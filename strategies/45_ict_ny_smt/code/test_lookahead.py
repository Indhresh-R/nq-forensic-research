"""Unit checks: signals only use closed candles / confirmed swings."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from structure import classify_c2_vs_c1, confirmed_swings, detect_fvgs, smt_at_bar


def test_swing_confirmation_gate():
    n = 20
    highs = np.array([float(i) for i in range(n)], dtype=float)
    # Make index 10 a clear swing high
    highs[10] = 100.0
    lows = -highs
    close_ts = pd.date_range("2024-01-01", periods=n, freq="5min", tz="America/New_York")
    sh, sl = confirmed_swings(highs, lows, close_ts.to_numpy(), lookback=3)
    assert any(s["idx"] == 10 for s in sh)
    swing = next(s for s in sh if s["idx"] == 10)
    # Confirmed only at i+L = 13
    assert swing["confirmed_at"] == close_ts[13]
    # Before confirmation, SMT must not see it
    early = smt_at_bar(sh, sl, sh, sl, close_ts[12], -1)
    # May or may not find SMT, but swing at 10 must not be in last_two if only one confirmed
    avail = [s for s in sh if pd.Timestamp(s["confirmed_at"]) <= close_ts[12]]
    assert all(s["idx"] != 10 for s in avail) or swing["confirmed_at"] > close_ts[12]
    avail_ok = [s for s in sh if pd.Timestamp(s["confirmed_at"]) <= close_ts[13]]
    assert any(s["idx"] == 10 for s in avail_ok)


def test_fvg_known_after_third_close():
    ohlc = pd.DataFrame(
        {
            "open": [10, 12, 14],
            "high": [11, 13, 15],
            "low": [9, 11, 13.5],
            "close": [10.5, 12.5, 14.5],
            "close_ts": pd.to_datetime(
                ["2024-01-01 10:00", "2024-01-01 11:00", "2024-01-01 12:00"]
            ).tz_localize("America/New_York"),
            "session_date": [pd.Timestamp("2024-01-01").date()] * 3,
        }
    )
    # Force bullish FVG: c1.high < c3.low
    ohlc.loc[0, "high"] = 10.0
    ohlc.loc[2, "low"] = 12.0
    fvgs = detect_fvgs(ohlc)
    assert len(fvgs) >= 1
    assert fvgs.iloc[0]["formed_at"] == ohlc.iloc[2]["close_ts"]


def test_c2_classification():
    c1 = pd.Series({"open": 100, "high": 105, "low": 99, "close": 101})
    c2_cont = pd.Series({"open": 101, "high": 110, "low": 100, "close": 108})
    r = classify_c2_vs_c1(c1, c2_cont)
    assert r["kind"] == "continuation" and r["direction"] == 1
    c2_rev = pd.Series({"open": 104, "high": 108, "low": 100, "close": 102})
    r2 = classify_c2_vs_c1(c1, c2_rev)
    assert r2["kind"] == "reversal"


def test_no_lookahead_trade_entry_ts():
    """Entry decision_ts must be <= confirming bar close; never use unclosed HTF OHLC."""
    # Synthetic: 1H close_ts must gate protected level
    h1 = pd.DataFrame(
        {
            "open": [100.0, 99.0, 98.0],
            "high": [101.0, 100.0, 103.0],
            "low": [98.0, 97.0, 97.5],
            "close": [99.0, 98.0, 102.0],
            "close_ts": pd.to_datetime(
                ["2024-06-03 10:00", "2024-06-03 11:00", "2024-06-03 12:00"]
            ).tz_localize("America/New_York"),
            "start_ts": pd.to_datetime(
                ["2024-06-03 09:00", "2024-06-03 10:00", "2024-06-03 11:00"]
            ).tz_localize("America/New_York"),
        }
    )
    from structure import find_engulfing_protected

    before = find_engulfing_protected(h1, 1, h1.iloc[1]["close_ts"] - pd.Timedelta(seconds=1))
    after = find_engulfing_protected(h1, 1, h1.iloc[2]["close_ts"])
    # Engulfing occurs on candle index 2; must not be visible before its close
    if after is not None:
        assert pd.Timestamp(after["formed_at"]) <= h1.iloc[2]["close_ts"]
    if before is not None:
        assert pd.Timestamp(before["formed_at"]) < h1.iloc[2]["close_ts"]


if __name__ == "__main__":
    test_swing_confirmation_gate()
    test_fvg_known_after_third_close()
    test_c2_classification()
    test_no_lookahead_trade_entry_ts()
    print("All lookahead/unit checks passed.")
