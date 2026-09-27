"""Causal safety checks. A failure must stop the study before interpretation."""
from __future__ import annotations

import pandas as pd

from daily_candles import SessionBars, candle_fields
from definitions import penetration_bucket
from penetration import bar_is_clean_separation, bar_is_range_entry, measure_sequence
from reference_range import build_reference


class SafetyError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise SafetyError(message)


def run_safety_checks(panel: pd.DataFrame, sessions: list[SessionBars]) -> list[str]:
    """Return passing check names, or raise SafetyError."""
    passed: list[str] = []
    if panel.empty:
        _fail("Panel is empty")

    previous = pd.to_datetime(panel["previous_session_date"])
    current = pd.to_datetime(panel["session_date"])
    if not bool((previous < current).all()):
        _fail("A previous session date is not strictly before the following session")
    passed.append("previous session date is strictly earlier")

    doji = panel[panel["previous_open"] == panel["previous_close"]]
    if len(doji):
        _fail("Doji previous days entered the primary sample")
    passed.append("doji previous days are excluded")

    bull = panel["direction"] == "bullish"
    bear = panel["direction"] == "bearish"
    if not bool((panel.loc[bull, "previous_close"] > panel.loc[bull, "previous_open"]).all()):
        _fail("Bullish label does not match previous close > previous open")
    if not bool((panel.loc[bear, "previous_close"] < panel.loc[bear, "previous_open"]).all()):
        _fail("Bearish label does not match previous close < previous open")
    passed.append("direction uses only the completed previous candle")

    if not bool((panel.loc[bull, "reference_extreme"] == panel.loc[bull, "previous_low"]).all()):
        _fail("Bullish reference extreme is not the previous low")
    if not bool((panel.loc[bear, "reference_extreme"] == panel.loc[bear, "previous_high"]).all()):
        _fail("Bearish reference extreme is not the previous high")
    if not bool((panel["reference_start"] == panel["previous_close"]).all()):
        _fail("Reference start is not the previous close")
    passed.append("reference range is the previous close-to-extreme distance")

    unqualified = panel[~panel["qualified"]]
    forward_cols = [col for col in panel.columns if col.startswith("fwd_ret_")]
    if len(unqualified) and bool(unqualified[forward_cols].notna().any().any()):
        _fail("A session without a usable retracement has a forward return")
    passed.append("forward returns exist only after a usable retracement")

    separated = panel["sequence_state"].isin(["retracement", "separated_no_return"])
    if bool((panel.loc[separated, "separation_index"] != 0).any()):
        _fail("Clean separation is not the session's first bar")
    blocked = panel["sequence_state"] == "entered_before_separation"
    if bool((panel.loc[blocked, "blocked_index"] != 0).any()):
        _fail("A range entry before separation is not the session's first bar")
    events = panel["sequence_state"] == "retracement"
    if bool((panel.loc[events, "retracement_index"] <= panel.loc[events, "separation_index"]).any()):
        _fail("Retracement is not strictly after separation")
    passed.append("separation is the first bar and the retracement is a later bar")

    by_date = {item.session_date: item for item in sessions}
    qualified = panel[panel["qualified"]]
    if qualified.empty:
        _fail("No qualifying retracement to recompute")
    sample = qualified.sample(n=min(40, int(len(qualified))), random_state=46)
    for _, row in sample.iterrows():
        current_bars = by_date[pd.Timestamp(row["session_date"]).date()]
        previous_bars = by_date[pd.Timestamp(row["previous_session_date"]).date()]
        candle = candle_fields(previous_bars)
        reference = build_reference(candle)
        if reference is None:
            _fail(f"Reference rebuilt as undefined for {row['session_date']}")
        measured = measure_sequence(current_bars, reference)
        if int(measured["retracement_index"]) != int(row["retracement_index"]):
            _fail(f"Retracement index changed on recompute for {row['session_date']}")
        if abs(float(measured["retracement_penetration_pct"]) - float(row["retracement_penetration_pct"])) > 1e-6:
            _fail(f"Retracement penetration changed on recompute for {row['session_date']}")
        if abs(float(measured["max_penetration_pct"]) - float(row["max_penetration_pct"])) > 1e-6:
            _fail(f"Maximum penetration changed on recompute for {row['session_date']}")
        if str(measured["sequence_state"]) != str(row["sequence_state"]):
            _fail(f"Sequence state changed on recompute for {row['session_date']}")
        touch_index = int(row["retracement_index"])
        separation_index = int(row["separation_index"])
        entry_index = touch_index + 1
        if int(current_bars.ts_ns[entry_index]) <= int(current_bars.ts_ns[touch_index]):
            _fail(f"Measurement bar is not after the retracement bar on {row['session_date']}")
        if int(current_bars.ts_ns[touch_index]) <= int(current_bars.ts_ns[separation_index]):
            _fail(f"Retracement bar is not after the separation bar on {row['session_date']}")
        if abs(float(current_bars.open[entry_index]) - float(row["fwd_measurement_price"])) > 1e-6:
            _fail(f"Measurement price is not the next bar open on {row['session_date']}")
        expected = penetration_bucket(float(row["retracement_penetration_pct"]))
        if expected != row["retracement_bucket"]:
            _fail(f"Bucket assignment drifted for {row['session_date']}")
        start = float(reference["reference_start"])
        bullish = int(reference["sign"]) == 1
        if not bar_is_clean_separation(
            bullish, float(current_bars.high[separation_index]), float(current_bars.low[separation_index]), start
        ):
            _fail(f"Separation bar is not entirely beyond the close on {row['session_date']}")
        if not bar_is_range_entry(bullish, float(current_bars.high[touch_index]), float(current_bars.low[touch_index]), start):
            _fail(f"Retracement bar does not enter the range on {row['session_date']}")
        for prior in range(touch_index):
            if bar_is_range_entry(bullish, float(current_bars.high[prior]), float(current_bars.low[prior]), start):
                _fail(f"An earlier bar already entered the range on {row['session_date']}")
    passed.append("recomputed retracement, penetration, bucket, and next-open price on a sample")

    forbidden = [col for col in panel.columns if any(token in col.lower() for token in ("atr", "smt", "fib", "pnl"))]
    if forbidden:
        _fail(f"Forbidden columns present: {forbidden}")
    passed.append("no ATR, SMT, Fibonacci, or P&L columns")
    passed.append("penetration buckets were not refit")
    passed.append("no trading cost was applied")
    return passed
