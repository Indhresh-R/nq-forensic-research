"""Build one Globex daily candle per session_date from 1-minute bars."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from common.nq_session import SESSION_START, load_nq
from common.splits import split_of

from definitions import (
    LATE_END_NY,
    LATE_START_NY,
    MIN_BARS,
    OPEN_NY_MIN,
    OPEN_TOLERANCE_MIN,
)


@dataclass
class SessionBars:
    session_date: object
    year: int
    split: str
    ts_ns: np.ndarray
    ny_min: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    complete: bool
    incomplete_reason: str


def candle_fields(bars: SessionBars) -> dict[str, float | str]:
    """OHLC and candle geometry from this session only."""
    open_px = float(bars.open[0])
    high_px = float(bars.high.max())
    low_px = float(bars.low.min())
    close_px = float(bars.close[-1])
    full_range = high_px - low_px
    body = abs(close_px - open_px)
    upper = high_px - max(open_px, close_px)
    lower = min(open_px, close_px) - low_px
    if close_px > open_px:
        direction = "bullish"
    elif close_px < open_px:
        direction = "bearish"
    else:
        direction = "doji"
    body_fraction = body / full_range if full_range > 0.0 else np.nan
    return {
        "open": open_px,
        "high": high_px,
        "low": low_px,
        "close": close_px,
        "range": full_range,
        "body": body,
        "body_fraction": float(body_fraction) if np.isfinite(body_fraction) else np.nan,
        "upper_wick": upper,
        "lower_wick": lower,
        "upper_wick_fraction": upper / full_range if full_range > 0.0 else np.nan,
        "lower_wick_fraction": lower / full_range if full_range > 0.0 else np.nan,
        "direction": direction,
        "n_bars": int(len(bars.open)),
    }


def _completeness(ny_min: np.ndarray, n_bars: int) -> tuple[bool, str]:
    reasons: list[str] = []
    if n_bars < MIN_BARS:
        reasons.append(f"n_bars<{MIN_BARS}")
    first = int(ny_min[0])
    if first < OPEN_NY_MIN or first > OPEN_NY_MIN + OPEN_TOLERANCE_MIN:
        reasons.append("open_not_in_1800_1805")
    late = (ny_min >= LATE_START_NY) & (ny_min < LATE_END_NY)
    if not bool(np.any(late)):
        reasons.append("no_1600_hour")
    if reasons:
        return False, ",".join(reasons)
    return True, "ok"


def load_sessions() -> tuple[list[SessionBars], dict[str, int]]:
    """Load frozen NQ bars and split them into Globex sessions. Read-only."""
    frame = load_nq()
    frame = frame.sort_values("ts")
    corrupt = int((frame["high"] < frame["low"]).sum())
    sessions: list[SessionBars] = []
    for session_date, group in frame.groupby("session_date", sort=True):
        group = group.sort_values("ts")
        stamp = pd.Timestamp(session_date)
        year = int(stamp.year)
        ny_min = group["ny_min"].to_numpy(np.int16)
        ts_ns = group["ts"].astype("int64").to_numpy()
        complete, reason = _completeness(ny_min, len(group))
        sessions.append(
            SessionBars(
                session_date=stamp.date(),
                year=year,
                split=split_of(year),
                ts_ns=ts_ns,
                ny_min=ny_min,
                open=group["open"].to_numpy(np.float64),
                high=group["high"].to_numpy(np.float64),
                low=group["low"].to_numpy(np.float64),
                close=group["close"].to_numpy(np.float64),
                complete=complete,
                incomplete_reason=reason,
            )
        )
    audit = {
        "n_bars_total": int(len(frame)),
        "n_sessions": len(sessions),
        "n_complete": int(sum(1 for s in sessions if s.complete)),
        "n_incomplete": int(sum(1 for s in sessions if not s.complete)),
        "n_corrupt_bars_high_lt_low": corrupt,
        "ts_min": str(frame["ts"].min()),
        "ts_max": str(frame["ts"].max()),
        "session_start_ny": int(SESSION_START),
    }
    return sessions, audit
