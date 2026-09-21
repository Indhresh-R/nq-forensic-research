"""Globex daily candles from NQ 1-minute bars. Read-only."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from common.nq_session import load_nq
from common.splits import split_of
from definitions import (
    LATE_END_NY,
    LATE_START_NY,
    MIN_BARS,
    OPEN_NY_MIN,
    OPEN_TOLERANCE_MIN,
)


@dataclass(frozen=True)
class Candle:
    session_date: date
    year: int
    split: str
    open: float
    high: float
    low: float
    close: float


def is_complete(ny_min: np.ndarray, n_bars: int) -> tuple[bool, str]:
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


def candles_from_sessions(frame: pd.DataFrame) -> tuple[list[Candle], dict[str, object]]:
    """One OHLC per session_date. Incomplete sessions are dropped, not patched."""
    ordered = frame.sort_values("ts")
    corrupt = int((ordered["high"] < ordered["low"]).sum())
    kept: list[Candle] = []
    incomplete: Counter[str] = Counter()
    n_sessions = 0
    for session_date, group in ordered.groupby("session_date", sort=True):
        n_sessions += 1
        group = group.sort_values("ts")
        ny_min = group["ny_min"].to_numpy(np.int16)
        complete, reason = is_complete(ny_min, len(group))
        if not complete:
            incomplete[reason] += 1
            continue
        stamp = pd.Timestamp(session_date)
        session = stamp.date()
        year = int(stamp.year)
        kept.append(
            Candle(
                session_date=session,
                year=year,
                split=split_of(year),
                open=float(group["open"].iloc[0]),
                high=float(group["high"].max()),
                low=float(group["low"].min()),
                close=float(group["close"].iloc[-1]),
            )
        )
    audit: dict[str, object] = {
        "n_bars_total": int(len(ordered)),
        "n_sessions": n_sessions,
        "n_complete": len(kept),
        "n_incomplete": int(sum(incomplete.values())),
        "n_corrupt_bars_high_lt_low": corrupt,
        "incomplete_reasons": dict(incomplete),
        "ts_min": str(ordered["ts"].min()) if len(ordered) else "",
        "ts_max": str(ordered["ts"].max()) if len(ordered) else "",
        "first_session": str(kept[0].session_date) if kept else "",
        "last_session": str(kept[-1].session_date) if kept else "",
    }
    return kept, audit


def load_candles() -> tuple[list[Candle], dict[str, object]]:
    return candles_from_sessions(load_nq())
