"""Separation, then the first later retracement into the previous-day range.

The previous close is the boundary. A bar establishes separation only when it
trades entirely on the continuation side of that close. One tick is enough.
The retracement is the first later bar that enters the close-to-extreme range.
The same bar cannot do both. No distance cutoff is applied.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from definitions import minutes_from_globex_open, penetration_bucket
from daily_candles import SessionBars


def bar_is_clean_separation(bullish: bool, high: float, low: float, start: float) -> bool:
    """True when the whole bar is strictly beyond the previous close, away from the range."""
    if bullish:
        return low > start
    return high < start


def bar_is_range_entry(bullish: bool, high: float, low: float, start: float) -> bool:
    """True when the bar prints the previous close or trades into the close-to-extreme range."""
    if bullish:
        return low <= start
    return high >= start


def _timestamp(ns: int) -> str:
    return str(pd.Timestamp(int(ns), unit="ns", tz="UTC").tz_convert("America/New_York"))


def _empty_event() -> dict[str, float | str | bool]:
    return {
        "separation_index": -1,
        "separation_ts": "",
        "separation_minutes_from_open": np.nan,
        "retracement_index": -1,
        "retracement_ts": "",
        "retracement_minutes_from_open": np.nan,
        "separation_duration_minutes": np.nan,
        "retracement_penetration_pct": np.nan,
        "retracement_bucket": "no_retracement",
        "blocked_index": -1,
    }


def measure_sequence(bars: SessionBars, reference: dict[str, float | str]) -> dict[str, float | str | bool]:
    """Classify one following session. Maximum penetration remains a session outcome."""
    start = float(reference["reference_start"])
    ref_range = float(reference["reference_range"])
    bullish = int(reference["sign"]) == 1
    n_bars = len(bars.open)
    if n_bars == 0:
        raise RuntimeError("Session has no bars")
    if not np.isfinite(bars.high).all() or not np.isfinite(bars.low).all():
        raise RuntimeError("Session high/low is not finite")

    if bullish:
        session_depth = start - float(bars.low.min())
        max_index = int(np.argmin(bars.low))
    else:
        session_depth = float(bars.high.max()) - start
        max_index = int(np.argmax(bars.high))
    max_pct = session_depth / ref_range * 100.0
    max_ts = _timestamp(int(bars.ts_ns[max_index]))

    separated_at = -1
    retracement_at = -1
    blocked_at = -1
    for index in range(n_bars):
        high = float(bars.high[index])
        low = float(bars.low[index])
        entered = bar_is_range_entry(bullish, high, low, start)
        separated = bar_is_clean_separation(bullish, high, low, start)
        if separated_at < 0:
            if entered:
                blocked_at = index
                break
            if not separated:
                raise RuntimeError("Bar is neither clean separation nor a range entry")
            separated_at = index
            continue
        if entered:
            retracement_at = index
            break

    event = _empty_event()
    if blocked_at >= 0:
        state = "entered_before_separation"
        event["blocked_index"] = blocked_at
    elif retracement_at >= 0:
        state = "retracement"
        if bullish:
            bar_depth = start - float(bars.low[retracement_at])
        else:
            bar_depth = float(bars.high[retracement_at]) - start
        pct = bar_depth / ref_range * 100.0
        event["retracement_index"] = retracement_at
        event["retracement_ts"] = _timestamp(int(bars.ts_ns[retracement_at]))
        event["retracement_minutes_from_open"] = float(minutes_from_globex_open(int(bars.ny_min[retracement_at])))
        event["retracement_penetration_pct"] = float(pct)
        event["retracement_bucket"] = penetration_bucket(float(pct))
        event["separation_duration_minutes"] = float(
            (int(bars.ts_ns[retracement_at]) - int(bars.ts_ns[separated_at])) / 60_000_000_000
        )
    else:
        state = "separated_no_return"

    if separated_at >= 0:
        event["separation_index"] = separated_at
        event["separation_ts"] = _timestamp(int(bars.ts_ns[separated_at]))
        event["separation_minutes_from_open"] = float(minutes_from_globex_open(int(bars.ny_min[separated_at])))

    event["sequence_state"] = state
    event["max_penetration_pct"] = float(max_pct)
    event["max_penetration_bucket"] = penetration_bucket(float(max_pct))
    event["max_penetration_ts"] = max_ts
    event["max_penetration_index"] = max_index
    return event
