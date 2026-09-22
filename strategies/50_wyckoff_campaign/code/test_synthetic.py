"""Synthetic grammar checks for Step 2 (no market outcomes)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))

from bars import build_15m, mark_segments, to_ticks
from constants import PIVOT_L
from extract import detect_pivots


def test_tick_grid_equality() -> None:
    assert to_ticks(18900.0) == to_ticks(18900.0000001)
    assert to_ticks(18900.25) == 75601
    assert to_ticks(100.00) == 400
    assert to_ticks(100.12) != to_ticks(100.25)


def test_pivot_requires_full_window() -> None:
    n = 20
    low = np.full(n, 100, dtype=np.int64)
    high = np.full(n, 110, dtype=np.int64)
    low[10] = 90
    high[10] = 110
    seg = np.zeros(n, dtype=np.int64)
    lows, highs = detect_pivots(low, high, seg)
    # pivot at 10 confirms at 12
    assert any(p == 10 and c == 10 + PIVOT_L for p, c in lows)


def test_gap_breaks_segment() -> None:
    # minimal fake 1m frame spanning a gap
    rows = []
    ts0 = pd.Timestamp("2024-01-02 18:00:00", tz="America/New_York")
    for m in range(15):
        t = ts0 + pd.Timedelta(minutes=m)
        rows.append(
            {
                "ts": t,
                "open": 100.0,
                "high": 100.25,
                "low": 99.75,
                "close": 100.0,
                "volume": 1,
                "year": 2024,
                "ny_min": t.hour * 60 + t.minute,
                "session_date": t.date() if t.hour < 18 else (t + pd.Timedelta(days=1)).date(),
            }
        )
    # skip 40 minutes then another full 15m
    ts1 = ts0 + pd.Timedelta(minutes=60)
    for m in range(15):
        t = ts1 + pd.Timedelta(minutes=m)
        rows.append(
            {
                "ts": t,
                "open": 100.0,
                "high": 100.25,
                "low": 99.75,
                "close": 100.0,
                "volume": 1,
                "year": 2024,
                "ny_min": t.hour * 60 + t.minute,
                "session_date": t.date() if t.hour < 18 else (t + pd.Timedelta(days=1)).date(),
            }
        )
    df = pd.DataFrame(rows)
    # fix session_date like load_nq
    df["session_date"] = pd.to_datetime("2024-01-03").date()
    bars = build_15m(df)
    bars = mark_segments(bars)
    assert len(bars) == 2
    assert bars["segment_id"].nunique() == 2


if __name__ == "__main__":
    test_tick_grid_equality()
    test_pivot_requires_full_window()
    test_gap_breaks_segment()
    print("synthetic checks OK")
