"""Load OHLC, timezone/QC, and look-ahead-safe candle construction."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from config import BacktestConfig


@dataclass
class DataQuality:
    symbol: str
    path: str
    tz_detected: str
    date_range: tuple[str, str]
    bar_count: int
    duplicate_ts: int
    gaps_gt_5m: int
    gaps_gt_60m: int
    median_gap_min: float
    missing_rth_estimate: int

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "path": self.path,
            "tz_detected": self.tz_detected,
            "date_start": self.date_range[0],
            "date_end": self.date_range[1],
            "bar_count": self.bar_count,
            "duplicate_ts": self.duplicate_ts,
            "gaps_gt_5m": self.gaps_gt_5m,
            "gaps_gt_60m": self.gaps_gt_60m,
            "median_gap_min": self.median_gap_min,
            "missing_rth_estimate": self.missing_rth_estimate,
        }


def _detect_tz_label(series: pd.Series) -> str:
    if getattr(series.dt, "tz", None) is not None:
        return str(series.dt.tz)
    return "naive-assumed-UTC"


def load_ohlc(path: Path, symbol: str) -> tuple[pd.DataFrame, DataQuality]:
    """Load 1m OHLC, convert to America/New_York, drop duplicate timestamps."""
    raw = pd.read_parquet(path)
    colmap = {c.lower(): c for c in raw.columns}
    ts_col = colmap.get("ts_event") or colmap.get("timestamp") or colmap.get("ts")
    if ts_col is None:
        raise ValueError(f"{path}: need timestamp/ts_event column")

    ts = pd.to_datetime(raw[ts_col], utc=True)
    tz_detected = _detect_tz_label(ts)
    ts_et = ts.dt.tz_convert("America/New_York")

    out = pd.DataFrame(
        {
            "ts": ts_et,
            "open": raw[colmap["open"]].to_numpy(np.float64),
            "high": raw[colmap["high"]].to_numpy(np.float64),
            "low": raw[colmap["low"]].to_numpy(np.float64),
            "close": raw[colmap["close"]].to_numpy(np.float64),
        }
    )
    if "volume" in colmap:
        out["volume"] = raw[colmap["volume"]].to_numpy(np.float64)
    else:
        out["volume"] = np.nan

    dupes = int(out["ts"].duplicated().sum())
    out = out.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)

    gaps = out["ts"].diff().dt.total_seconds() / 60.0
    gaps_gt_5 = int((gaps > 5).sum())
    gaps_gt_60 = int((gaps > 60).sum())
    median_gap = float(gaps.median()) if len(gaps) else float("nan")

    # Rough missing-bar estimate inside weekdays 09:30-16:00
    ny_min = out["ts"].dt.hour * 60 + out["ts"].dt.minute
    rth = out[(ny_min >= 9 * 60 + 30) & (ny_min < 16 * 60) & (out["ts"].dt.dayofweek < 5)]
    expected_per_day = 6 * 60 + 30  # 09:30-16:00
    n_days = rth["ts"].dt.date.nunique()
    missing_rth = max(int(n_days * expected_per_day - len(rth)), 0)

    qc = DataQuality(
        symbol=symbol,
        path=str(path),
        tz_detected=tz_detected,
        date_range=(str(out["ts"].iloc[0]), str(out["ts"].iloc[-1])),
        bar_count=len(out),
        duplicate_ts=dupes,
        gaps_gt_5m=gaps_gt_5,
        gaps_gt_60m=gaps_gt_60,
        median_gap_min=median_gap,
        missing_rth_estimate=missing_rth,
    )
    return out, qc


def add_session_fields(df: pd.DataFrame, anchor_hour: int = 18) -> pd.DataFrame:
    """Attach session_date (CME: date of the 18:00 open's following calendar day label).

    Convention matching repo: bars from 18:00 ET belong to the *next* calendar date
    as session_date (the date when RTH of that Globex day occurs).
    """
    out = df.copy()
    ny_min = out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16)
    out["ny_min"] = ny_min
    cal = out["ts"].dt.date
    anchor_min = anchor_hour * 60
    out["session_date"] = np.where(
        ny_min.to_numpy() >= anchor_min,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    # Minutes since session open (18:00), wrapping past midnight
    out["mins_from_anchor"] = np.where(
        ny_min.to_numpy() >= anchor_min,
        ny_min.to_numpy() - anchor_min,
        ny_min.to_numpy() + (24 * 60 - anchor_min),
    )
    return out


def _ohlc_agg(g: pd.DataFrame) -> pd.Series:
    return pd.Series(
        {
            "open": g["open"].iloc[0],
            "high": g["high"].max(),
            "low": g["low"].min(),
            "close": g["close"].iloc[-1],
            "volume": g["volume"].sum(),
            "start_ts": g["ts"].iloc[0],
            "close_ts": g["ts"].iloc[-1] + pd.Timedelta(minutes=1),  # bar known after its end
            "n_bars": len(g),
        }
    )


def resample_fixed(df: pd.DataFrame, minutes: int, anchor_hour: int = 18) -> pd.DataFrame:
    """Resample to N-minute candles anchored to session open (mins_from_anchor).

    Bin [start, start+minutes) is emitted only if the last minute of the bin
    appears in data (fully closed). ``close_ts`` = scheduled bin end.
    """
    if df.empty:
        return pd.DataFrame()
    x = add_session_fields(df, anchor_hour).copy()
    x["bin"] = (x["mins_from_anchor"] // minutes).astype(np.int32)
    x["bin_end_mfa"] = (x["bin"] + 1) * minutes - 1
    # Keep groups that reached the last minute of the bin
    last = x.groupby(["session_date", "bin"], sort=False)["mins_from_anchor"].transform("max")
    x = x[last >= x["bin_end_mfa"]]
    if x.empty:
        return pd.DataFrame()

    g = x.groupby(["session_date", "bin"], sort=True)
    out = g.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        start_ts=("ts", "first"),
        n_bars=("ts", "count"),
        mfa0=("mins_from_anchor", "first"),
    ).reset_index()
    # Align start_ts to bin boundary and set close_ts
    adj = out["mfa0"] - out["bin"] * minutes
    out["start_ts"] = out["start_ts"] - pd.to_timedelta(adj, unit="m")
    out["close_ts"] = out["start_ts"] + pd.to_timedelta(minutes, unit="m")
    out = out.drop(columns=["mfa0"])
    out["tf_minutes"] = minutes
    return out


def resample_daily(df: pd.DataFrame, anchor_hour: int = 18) -> pd.DataFrame:
    """Daily candle: 18:00 → 17:00 ET (mins_from_anchor < 23*60)."""
    x = add_session_fields(df, anchor_hour)
    x = x[x["mins_from_anchor"] < 23 * 60]
    g = x.groupby("session_date", sort=True)
    out = g.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        start_ts=("ts", "first"),
        end_ts=("ts", "last"),
        n_bars=("ts", "count"),
    ).reset_index()
    out = out[out["n_bars"] >= 60]
    out["close_ts"] = out["end_ts"] + pd.Timedelta(minutes=1)
    out = out.drop(columns=["end_ts"])
    out["tf"] = "1D"
    return out


def resample_7h(df: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    """Custom 7H (and remainder) bins anchored at session open."""
    x = add_session_fields(df, cfg.session_anchor_hour).copy()
    edges = list(cfg.seven_h_edges_hours)
    edge_mins = np.array([e * 60 for e in edges], dtype=np.int64)
    mfa = x["mins_from_anchor"].to_numpy(np.int64)
    # Vectorized bin id
    bin_id = np.searchsorted(edge_mins, mfa, side="right") - 1
    bin_id = np.clip(bin_id, 0, len(edge_mins) - 2)
    x["bin"] = bin_id
    x["bin_end_mfa"] = edge_mins[bin_id + 1] - 1
    last = x.groupby(["session_date", "bin"], sort=False)["mins_from_anchor"].transform("max")
    x = x[last >= x["bin_end_mfa"]]
    if x.empty:
        return pd.DataFrame()
    g = x.groupby(["session_date", "bin"], sort=True)
    out = g.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        start_ts=("ts", "first"),
        end_ts=("ts", "last"),
        n_bars=("ts", "count"),
        mfa0=("mins_from_anchor", "first"),
    ).reset_index()
    # Scheduled close from bin edge
    start_edge = edge_mins[out["bin"].to_numpy()]
    adj = out["mfa0"].to_numpy() - start_edge
    out["start_ts"] = out["start_ts"] - pd.to_timedelta(adj, unit="m")
    dur = edge_mins[out["bin"].to_numpy() + 1] - start_edge
    out["close_ts"] = out["start_ts"] + pd.to_timedelta(dur, unit="m")
    out["bin_start_hour"] = [edges[int(b)] for b in out["bin"]]
    out["expected_minutes"] = dur
    out = out.drop(columns=["end_ts", "mfa0"])
    out["tf"] = "7H"
    return out


def print_qc(qc: DataQuality) -> None:
    print(f"=== Data quality: {qc.symbol} ===")
    for k, v in qc.to_dict().items():
        print(f"  {k}: {v}")


def load_markets(cfg: BacktestConfig) -> tuple[pd.DataFrame, pd.DataFrame, list[DataQuality]]:
    nq, nq_qc = load_ohlc(cfg.nq_path, "NQ")
    es, es_qc = load_ohlc(cfg.es_path, "ES")
    nq = add_session_fields(nq, cfg.session_anchor_hour)
    es = add_session_fields(es, cfg.session_anchor_hour)
    print_qc(nq_qc)
    print_qc(es_qc)
    return nq, es, [nq_qc, es_qc]
