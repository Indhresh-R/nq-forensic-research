"""Lightweight unit checks for VSA bar helpers (no market scan)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from bars import causal_atr20, mark_segments, to_ticks
from constants import TICK


def test_ticks() -> None:
    assert to_ticks(100.0) == 400
    assert abs(float(to_ticks(100.13)) * TICK - 100.25) < 1e-9 or to_ticks(100.13) in (400, 401)


def test_segment_gap() -> None:
    # two bars 15m apart, then a large gap
    rows = []
    t0 = pd.Timestamp("2020-01-02 18:00:00", tz="UTC")
    for i in range(5):
        rows.append(
            {
                "start": t0 + pd.Timedelta(minutes=15 * i),
                "end": t0 + pd.Timedelta(minutes=15 * i + 14),
                "open": 1.0,
                "high": 2.0,
                "low": 0.5,
                "close": 1.5,
                "volume": 10,
                "n": 15,
                "year": 2020,
                "session_date": "2020-01-02",
                "i": i,
            }
        )
    # gap > 20m before next bar
    t1 = t0 + pd.Timedelta(minutes=15 * 5 + 60)
    rows.append(
        {
            "start": t1,
            "end": t1 + pd.Timedelta(minutes=14),
            "open": 1.0,
            "high": 2.0,
            "low": 0.5,
            "close": 1.5,
            "volume": 10,
            "n": 15,
            "year": 2020,
            "session_date": "2020-01-02",
            "i": 5,
        }
    )
    bars = mark_segments(pd.DataFrame(rows))
    assert bars["segment_id"].nunique() == 2
    atr_at, atr_prior = causal_atr20(bars)
    assert np.isnan(atr_prior[5])  # new segment


if __name__ == "__main__":
    test_ticks()
    test_segment_gap()
    print("ok")
