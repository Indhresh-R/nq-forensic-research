"""Build CME-session volume profiles from Databento trade files.

Filename dates are UTC days, not CME sessions.
"""

from __future__ import annotations

import sys
import traceback
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd
import yaml
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
VP = Path(__file__).resolve().parents[1]
NY = ZoneInfo("America/New_York")


def load_config() -> dict:
    with (VP / "CONFIG.yaml").open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def assign_cme_sessions(ts_event_utc: pd.Series) -> pd.Series:
    """Vectorized CME session date. See assign_cme_session."""
    ny = pd.to_datetime(ts_event_utc, utc=True).dt.tz_convert(NY)
    day = ny.dt.floor("D")
    session = day.where(ny.dt.hour >= 18, day - pd.Timedelta(days=1))
    return session.dt.date


def assign_cme_session(ts_event_utc) -> date:
    """Map a UTC trade timestamp to the CME session date.

    New York time at or after 18:00 belongs to that New York calendar date.
    Any earlier New York time belongs to the previous calendar date.
    The session then runs until 17:00 New York on the following day.
    DST is handled by America/New_York. Offsets are not hardcoded.
    """
    return assign_cme_sessions(pd.Series([ts_event_utc])).iloc[0]


def session_bounds(session_date: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Assignment window: [18:00 New York, next 18:00 New York).

    This matches assign_cme_session. The economic close is 17:00; the
    17:00-18:00 maintenance break is inside the window and normally has no trades.
    """
    start = pd.Timestamp(datetime(session_date.year, session_date.month, session_date.day, 18, 0), tz=NY)
    nxt = session_date + timedelta(days=1)
    end = pd.Timestamp(datetime(nxt.year, nxt.month, nxt.day, 18, 0), tz=NY)
    return start, end


def epoch_ns(series: pd.Series) -> np.ndarray:
    """UTC nanoseconds. Databento and pandas may use ns or us; this forces ns."""
    utc = pd.to_datetime(series, utc=True)
    return utc.to_numpy(dtype="datetime64[ns]").view(np.int64)


def session_close(session_date: date) -> pd.Timestamp:
    nxt = session_date + timedelta(days=1)
    return pd.Timestamp(datetime(nxt.year, nxt.month, nxt.day, 17, 0), tz=NY)


def trades_dir(cfg: dict) -> Path:
    return REPO / cfg["trades_dir"]


def list_trade_files(cfg: dict) -> list[Path]:
    files = sorted(trades_dir(cfg).glob("trades_24h_*.dbn.zst"))
    return files


def file_date(path: Path) -> str:
    return path.stem.replace("trades_24h_", "").replace(".dbn", "")


def points_from_price(price: np.ndarray, scale: float) -> np.ndarray:
    values = np.asarray(price, dtype=np.float64)
    if values.size == 0:
        return values
    if np.nanmax(np.abs(values)) > 1_000_000:
        return values / scale
    return values


def to_ticks(points: np.ndarray, tick_size: float) -> np.ndarray:
    return np.rint(points / tick_size).astype(np.int64)


def read_trades(path: Path, cfg: dict) -> pd.DataFrame:
    store = db.DBNStore.from_file(path)
    symbols = list(getattr(store.metadata, "symbols", []) or [])
    frame = store.to_df()
    if "ts_event" not in frame.columns:
        frame = frame.reset_index()
    if "ts_event" not in frame.columns:
        raise ValueError("ts_event missing")
    for col in ("price", "size"):
        if col not in frame.columns:
            raise ValueError(f"{col} missing")
    ts = pd.to_datetime(frame["ts_event"], utc=True)
    points = points_from_price(frame["price"].to_numpy(), float(cfg["price_scale"]))
    ticks = to_ticks(points, float(cfg["tick_size"]))
    out = pd.DataFrame(
        {
            "ts_event": ts,
            "price_ticks": ticks,
            "size": frame["size"].to_numpy(dtype=np.int64),
            "sequence": frame["sequence"].to_numpy(dtype=np.int64) if "sequence" in frame.columns else np.zeros(len(frame), dtype=np.int64),
            "instrument_id": frame["instrument_id"].to_numpy(dtype=np.int64) if "instrument_id" in frame.columns else np.zeros(len(frame), dtype=np.int64),
        }
    )
    out["session_date"] = assign_cme_sessions(out["ts_event"])
    out.attrs["symbols"] = symbols
    out.attrs["max_tick_error"] = float(np.max(np.abs(points - ticks * float(cfg["tick_size"])))) if len(points) else 0.0
    return out


def audit_inputs(cfg: dict) -> pd.DataFrame:
    files = list_trade_files(cfg)
    rows = []
    names = [p.name for p in files]
    if len(files) != int(cfg["expected_file_count"]):
        rows.append(_audit_error("DIRECTORY", "", f"expected {cfg['expected_file_count']} files, found {len(files)}"))
    if names and names[0] != cfg["expected_first_file"]:
        rows.append(_audit_error(names[0] if names else "", "", f"first file is {names[:1]}, expected {cfg['expected_first_file']}"))
    if names and names[-1] != cfg["expected_last_file"]:
        rows.append(_audit_error(names[-1] if names else "", "", f"last file is {names[-1:]}, expected {cfg['expected_last_file']}"))
    if len(names) != len(set(names)):
        rows.append(_audit_error("DIRECTORY", "", "duplicate filenames"))
    dates = [file_date(p) for p in files]
    if len(dates) != len(set(dates)):
        rows.append(_audit_error("DIRECTORY", "", "duplicate file dates"))

    for path in files:
        row = {
            "filename": path.name,
            "file_date": file_date(path),
            "row_count": 0,
            "min_ts_event": "",
            "max_ts_event": "",
            "min_price": np.nan,
            "max_price": np.nan,
            "total_volume": 0,
            "status": "ok",
            "error": "",
        }
        try:
            frame = read_trades(path, cfg)
            symbols = frame.attrs.get("symbols", [])
            if cfg["expected_symbol"] not in symbols:
                raise ValueError(f"symbol {symbols} does not contain {cfg['expected_symbol']}")
            if frame["ts_event"].dt.tz is None:
                raise ValueError("ts_event is not timezone-aware")
            if (frame["size"] < 0).any():
                raise ValueError("negative size")
            tick = float(cfg["tick_size"])
            prices = frame["price_ticks"].to_numpy() * tick
            row.update(
                {
                    "row_count": int(len(frame)),
                    "min_ts_event": str(frame["ts_event"].min()),
                    "max_ts_event": str(frame["ts_event"].max()),
                    "min_price": float(prices.min()) if len(prices) else np.nan,
                    "max_price": float(prices.max()) if len(prices) else np.nan,
                    "total_volume": int(frame["size"].clip(lower=0).sum()),
                    "status": "ok" if frame.attrs["max_tick_error"] <= 1e-4 else "fail",
                    "error": "" if frame.attrs["max_tick_error"] <= 1e-4 else f"tick error {frame.attrs['max_tick_error']}",
                }
            )
        except Exception as exc:
            row["status"] = "fail"
            row["error"] = f"{exc.__class__.__name__}: {exc}"
        rows.append(row)
        print(f"[audit] {path.name} {row['status']} rows={row['row_count']}", flush=True)
    audit = pd.DataFrame(rows)
    out = VP / "data" / "input_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(out, index=False)
    if (audit["status"] != "ok").any():
        raise SystemExit(f"input audit failed, see {out}")
    return audit


def _audit_error(filename: str, file_date_value: str, message: str) -> dict:
    return {
        "filename": filename,
        "file_date": file_date_value,
        "row_count": 0,
        "min_ts_event": "",
        "max_ts_event": "",
        "min_price": np.nan,
        "max_price": np.nan,
        "total_volume": 0,
        "status": "fail",
        "error": message,
    }


def expand_value_area(volumes: dict[int, int], poc: int, target_pct: float) -> tuple[int, int, int]:
    """Expand from POC to the nearest traded prices until target_pct of volume is inside.

    If the two adjacent prices have equal volume, expand to the lower price.
    """
    prices = sorted(volumes)
    loc = {px: i for i, px in enumerate(prices)}
    lo = hi = loc[poc]
    included = int(volumes[poc])
    total = int(sum(volumes.values()))
    target = target_pct * total
    while included + 1e-9 < target and (lo > 0 or hi < len(prices) - 1):
        down_vol = volumes[prices[lo - 1]] if lo > 0 else -1
        up_vol = volumes[prices[hi + 1]] if hi < len(prices) - 1 else -1
        if lo > 0 and down_vol >= up_vol:
            lo -= 1
            included += int(volumes[prices[lo]])
        else:
            hi += 1
            included += int(volumes[prices[hi]])
    return prices[lo], prices[hi], included


def choose_poc(volumes: dict[int, int]) -> int:
    best = max(volumes.values())
    return min(px for px, vol in volumes.items() if vol == best)


def accumulate(files: list[Path], cfg: dict) -> tuple[dict, dict]:
    volumes: dict[date, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    meta: dict[date, dict] = {}
    for path in files:
        frame = read_trades(path, cfg)
        frame = frame[frame["size"] > 0]
        if frame.empty:
            print(f"[profile] {path.name} no positive size", flush=True)
            continue
        grouped = frame.groupby(["session_date", "price_ticks"], sort=False)["size"].sum()
        for (session, ticks), vol in grouped.items():
            volumes[session][int(ticks)] += int(vol)
        for session, part in frame.groupby("session_date", sort=False):
            order = part.sort_values(["ts_event", "sequence"], kind="mergesort")
            first = order.iloc[0]
            last = order.iloc[-1]
            slot = meta.get(session)
            first_key = (first["ts_event"].value, int(first["sequence"]))
            last_key = (last["ts_event"].value, int(last["sequence"]))
            ids = set(int(v) for v in order["instrument_id"].unique())
            if slot is None:
                meta[session] = {
                    "n_trades": int(len(order)),
                    "first_key": first_key,
                    "last_key": last_key,
                    "first_ts": first["ts_event"],
                    "last_ts": last["ts_event"],
                    "first_ticks": int(first["price_ticks"]),
                    "last_ticks": int(last["price_ticks"]),
                    "instrument_ids": ids,
                }
            else:
                slot["n_trades"] += int(len(order))
                slot["instrument_ids"].update(ids)
                if first_key < slot["first_key"]:
                    slot["first_key"] = first_key
                    slot["first_ts"] = first["ts_event"]
                    slot["first_ticks"] = int(first["price_ticks"])
                if last_key > slot["last_key"]:
                    slot["last_key"] = last_key
                    slot["last_ts"] = last["ts_event"]
                    slot["last_ticks"] = int(last["price_ticks"])
        print(f"[profile] {path.name} trades={len(frame)}", flush=True)
        del frame
    return volumes, meta


def build_tables(volumes: dict, meta: dict, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    tick = float(cfg["tick_size"])
    target = float(cfg["value_area_pct"])
    profile_rows = []
    vap_rows = []
    for session in sorted(volumes):
        volmap = dict(volumes[session])
        total = int(sum(volmap.values()))
        if total <= 0:
            continue
        poc = choose_poc(volmap)
        val, vah, va_vol = expand_value_area(volmap, poc, target)
        info = meta[session]
        start, _end = session_bounds(session)
        close = session_close(session)
        slack = pd.Timedelta(minutes=int(cfg["completeness_slack_minutes"]))
        complete = bool(info["first_ts"] <= start + slack and info["last_ts"] >= close - slack)
        ids = sorted(info["instrument_ids"])
        profile_rows.append(
            {
                "session_date": session.isoformat(),
                "total_volume": total,
                "poc": poc * tick,
                "vah": vah * tick,
                "val": val * tick,
                "poc_ticks": poc,
                "vah_ticks": vah,
                "val_ticks": val,
                "profile_high": max(volmap) * tick,
                "profile_low": min(volmap) * tick,
                "profile_high_ticks": max(volmap),
                "profile_low_ticks": min(volmap),
                "value_area_volume": va_vol,
                "value_area_pct": va_vol / total,
                "value_area_width": (vah - val) * tick,
                "profile_range": (max(volmap) - min(volmap)) * tick,
                "poc_volume": int(volmap[poc]),
                "poc_volume_pct": volmap[poc] / total,
                "n_price_levels": len(volmap),
                "first_trade_ts": info["first_ts"],
                "last_trade_ts": info["last_ts"],
                "n_trades": info["n_trades"],
                "first_ticks": info["first_ticks"],
                "last_ticks": info["last_ticks"],
                "instrument_id": ids[0] if len(ids) == 1 else -1,
                "n_instrument_ids": len(ids),
                "is_complete": complete,
            }
        )
        for px, vol in volmap.items():
            vap_rows.append(
                {
                    "session_date": session.isoformat(),
                    "price": px * tick,
                    "price_ticks": px,
                    "volume": int(vol),
                    "volume_pct": vol / total,
                }
            )
    profiles = pd.DataFrame(profile_rows).sort_values("session_date").reset_index(drop=True)
    profiles = mark_rolls(profiles, float(cfg["roll_gap_points"]), float(cfg["tick_size"]))
    vap = pd.DataFrame(vap_rows)
    return profiles, vap


def mark_rolls(profiles: pd.DataFrame, gap_points: float, tick_size: float) -> pd.DataFrame:
    out = profiles.copy()
    changed = out["instrument_id"].ne(out["instrument_id"].shift(1)) & out["instrument_id"].shift(1).notna()
    multi = out["n_instrument_ids"] > 1
    gap = (out["first_ticks"] - out["last_ticks"].shift(1)).abs() * tick_size
    gap_flag = gap.fillna(0) >= gap_points
    flag = (changed | multi | gap_flag).copy()
    if len(out):
        flag.iloc[0] = bool(out.iloc[0]["n_instrument_ids"] > 1)
    out["roll_id_change"] = (changed | multi).to_numpy()
    if len(out):
        out.loc[0, "roll_id_change"] = bool(out.iloc[0]["n_instrument_ids"] > 1)
    out["roll_gap"] = gap_flag.to_numpy()
    if len(out):
        out.loc[0, "roll_gap"] = False
    out["is_roll_transition"] = flag.to_numpy()
    return out


def write_outputs(profiles: pd.DataFrame, vap: pd.DataFrame) -> None:
    data = VP / "data"
    data.mkdir(parents=True, exist_ok=True)
    profiles.to_parquet(data / "session_profiles.parquet", index=False)
    vap.to_parquet(data / "session_volume_profile.parquet", index=False)
    print(f"[profile] sessions={len(profiles)} vap_rows={len(vap)}", flush=True)


def build_profiles(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    volumes, meta = accumulate(list_trade_files(cfg), cfg)
    profiles, vap = build_tables(volumes, meta, cfg)
    write_outputs(profiles, vap)
    return profiles, vap


def main() -> None:
    cfg = load_config()
    audit_only = "--audit-only" in sys.argv
    try:
        audit_inputs(cfg)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
    if audit_only:
        return
    build_profiles(cfg)


if __name__ == "__main__":
    main()
