"""
Shared NQ session primitives for forensic strategy research.

Canonical import:
  from common.nq_session import ART, NY_OPEN, load_nq, state_at_T, build_day_context
"""
from __future__ import annotations

from datetime import date as date_cls
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common.paths import ART, DATA, ROOT, art
from common.splits import IS_YEARS as IS_Y
from common.splits import OOS_YEARS as OOS_Y
from common.splits import VAL_YEARS as VAL_Y
from common.splits import split_of

NY_OPEN = 9 * 60 + 30
SESSION_START = 18 * 60
DECISION_OFFSETS = tuple(range(5, 91, 5))


def load_nq(path: Path | None = None) -> pd.DataFrame:
    candidates = []
    if path is not None:
        candidates.append(path)
    candidates.extend(
        [
            DATA / "nq_1m_continuous.parquet",
            ROOT / "nq_1m_continuous.parquet",
            ROOT / "data" / "nq_1m_continuous.parquet",
        ]
    )
    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        raise FileNotFoundError("nq_1m_continuous.parquet not found under data/ or repo root")
    df = pd.read_parquet(src)
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert("America/New_York")
    out = pd.DataFrame(
        {
            "ts": ts,
            "open": df["open"].to_numpy(np.float64),
            "high": df["high"].to_numpy(np.float64),
            "low": df["low"].to_numpy(np.float64),
            "close": df["close"].to_numpy(np.float64),
            "volume": df["volume"].to_numpy(np.int64),
        }
    )
    out["year"] = out["ts"].dt.year.astype(np.int16)
    out["dow"] = out["ts"].dt.dayofweek.astype(np.int8)
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    cal = out["ts"].dt.date
    out["session_date"] = np.where(
        out["ny_min"].to_numpy() >= SESSION_START,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    return out


def load_es(path: Path | None = None) -> pd.DataFrame:
    candidates = []
    if path is not None:
        candidates.append(path)
    candidates.extend(
        [
            DATA / "es_1m_continuous.parquet",
            ROOT / "es_1m_continuous.parquet",
        ]
    )
    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        raise FileNotFoundError("es_1m_continuous.parquet not found")
    df = pd.read_parquet(src)
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert("America/New_York")
    out = pd.DataFrame(
        {
            "ts": ts,
            "open": df["open"].to_numpy(np.float64),
            "high": df["high"].to_numpy(np.float64),
            "low": df["low"].to_numpy(np.float64),
            "close": df["close"].to_numpy(np.float64),
            "volume": df["volume"].to_numpy(np.int64),
        }
    )
    out["year"] = out["ts"].dt.year.astype(np.int16)
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    cal = out["ts"].dt.date
    out["session_date"] = np.where(
        out["ny_min"].to_numpy() >= SESSION_START,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    return out


def build_day_context(df: pd.DataFrame) -> pd.DataFrame:
    facts = pd.read_parquet(art("ny_open_day_facts.parquet"))
    rows = []
    onr_hist: list[float] = []
    frames = {sd: g for sd, g in df.groupby("session_date", sort=True)}
    for _, fr in facts.iterrows():
        sd = fr["session_date"]
        sd_key = date_cls.fromisoformat(sd) if isinstance(sd, str) else sd
        g = frames.get(sd_key)
        if g is None:
            continue
        on = g[g["ny_min"] < NY_OPEN]
        on_c = on["close"].to_numpy(float)
        on_rv = float(np.sum(np.abs(np.diff(on_c)))) if len(on_c) > 1 else float(fr["onr"])
        onr = float(fr["onr"])
        onr_med20 = (
            float(np.median(onr_hist[-20:]))
            if len(onr_hist) >= 5
            else (float(fr["onr_med20"]) if np.isfinite(fr.get("onr_med20", np.nan)) else np.nan)
        )
        rows.append(
            {
                "session_date": sd_key,
                "year": int(fr["year"]),
                "dow": int(fr["dow"]),
                "split": str(fr["split"]),
                "onh": float(fr["onh"]),
                "onl": float(fr["onl"]),
                "onr": onr,
                "on_rv": on_rv,
                "open_930": float(fr["open_930"]),
                "open_loc": float(fr["open_loc_onr"]),
                "gap_onr": float(fr["gap_onr"]),
                "pdh": float(fr["pdh"]),
                "pdl": float(fr["pdl"]),
                "pdc": float(fr["pdc"]),
                "pdr": float(fr["pdr"]),
                "onr_med20": onr_med20,
                "onr_vs_med": (onr / onr_med20) if onr_med20 and onr_med20 > 0 else np.nan,
            }
        )
        onr_hist.append(onr)
    return pd.DataFrame(rows)


def state_at_T(rth_to_T: pd.DataFrame, ctx: dict, T_ny: int) -> dict[str, float] | None:
    """Causal state + current vol unit using only bars with ny_min <= T."""
    if len(rth_to_T) < 3:
        return None
    if T_ny not in set(rth_to_T["ny_min"].tolist()):
        return None
    rth_to_T = rth_to_T[rth_to_T["ny_min"] <= T_ny].reset_index(drop=True)
    o930 = float(ctx["open_930"])
    onr = float(ctx["onr"])
    if onr <= 0:
        return None
    c = rth_to_T["close"].to_numpy(float)
    h = rth_to_T["high"].to_numpy(float)
    l = rth_to_T["low"].to_numpy(float)
    o = rth_to_T["open"].to_numpy(float)
    last_c = float(c[-1])
    elapsed = max(int(T_ny - NY_OPEN), 1)

    rng = float(h.max() - l.min())
    rng_onr = rng / onr
    move = last_c - o930
    move_onr = move / onr
    path = float(np.sum(np.abs(np.diff(c)))) if len(c) > 1 else abs(move)
    path_onr = path / onr
    speed = abs(move_onr) / elapsed

    prev_c = np.concatenate([[o[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    atr = float(np.mean(tr)) if len(tr) else float(rng / max(elapsed, 1))
    vol_unit = max(atr, 0.05 * onr, 1.0)

    onr_vs_med = float(ctx["onr_vs_med"]) if np.isfinite(ctx["onr_vs_med"]) else np.nan
    if abs(move) < 0.25:
        persist_frac = np.nan
        dir_sign = 0.0
    else:
        dir_sign = 1.0 if move > 0 else -1.0
        deltas = np.diff(c)
        persist_frac = float(np.mean(np.sign(deltas) == dir_sign)) if len(deltas) else np.nan

    loc_now = (last_c - float(ctx["onl"])) / onr
    on_rv = float(ctx["on_rv"])
    path_vs_onrv = path / on_rv if on_rv > 0 else np.nan

    return {
        "elapsed": float(elapsed),
        "rng_onr": rng_onr,
        "move_onr": move_onr,
        "abs_move_onr": abs(move_onr),
        "path_onr": path_onr,
        "speed": speed,
        "vol_exp": rng_onr,
        "onr_vs_med": onr_vs_med,
        "persist_frac": persist_frac,
        "dir_sign": dir_sign,
        "loc_now": loc_now,
        "open_loc": float(ctx["open_loc"]),
        "path_vs_onrv": path_vs_onrv,
        "gap_onr": float(ctx["gap_onr"]),
        "onr": onr,
        "atr": atr,
        "vol_unit": vol_unit,
        "vol_unit_onr": vol_unit / onr,
    }


def rate_of(series: pd.Series) -> dict[str, float]:
    x = series.to_numpy(float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return {"n": 0, "rate": np.nan}
    return {"n": int(n), "rate": float(np.mean(x))}


def win_rate(series: pd.Series) -> dict[str, float]:
    """P(x > 0) for signed returns."""
    x = series.to_numpy(float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return {"n": 0, "rate": np.nan}
    return {"n": int(n), "rate": float(np.mean(x > 0))}


# Re-export multi-session clock helpers
from common.sessions import (  # noqa: E402
    PRIOR_SESSION,
    RTH_END,
    SESSION_BY_NAME,
    SESSION_DECISION_OFFSETS,
    SESSION_ORDER,
    SESSIONS,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    session_of,
    state_at_T_session,
)

__all__ = [
    "ART",
    "DATA",
    "ROOT",
    "art",
    "NY_OPEN",
    "SESSION_START",
    "DECISION_OFFSETS",
    "IS_Y",
    "VAL_Y",
    "OOS_Y",
    "split_of",
    "load_nq",
    "load_es",
    "build_day_context",
    "state_at_T",
    "win_rate",
    "rate_of",
    "RTH_END",
    "SESSIONS",
    "SESSION_BY_NAME",
    "SESSION_ORDER",
    "SESSION_DECISION_OFFSETS",
    "PRIOR_SESSION",
    "session_of",
    "bars_in_session",
    "build_session_facts",
    "decision_ny_min",
    "state_at_T_session",
]
