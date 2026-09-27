"""Definition tests that do not read the market data."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from daily_candles import SessionBars
from definitions import (
    NO_PENETRATION,
    body_fraction_bucket,
    depth_pool,
    penetration_bucket,
)
from forward_outcomes import outcomes_from_entry
from penetration import measure_sequence
from reference_range import build_reference
from verdict import decide


def _bars(n: int, start: str = "2020-01-06 18:00") -> tuple[SessionBars, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ts = pd.date_range(start, periods=n, freq="min", tz="America/New_York")
    open_px = np.full(n, 101.0)
    high = np.full(n, 101.5)
    low = np.full(n, 100.5)
    close = np.full(n, 101.0)
    bars = SessionBars(
        session_date=date(2020, 1, 7),
        year=2020,
        split="IS",
        ts_ns=ts.as_unit("ns").asi8.copy(),
        ny_min=(ts.hour * 60 + ts.minute).to_numpy(np.int16),
        open=open_px,
        high=high,
        low=low,
        close=close,
        complete=True,
        incomplete_reason="ok",
    )
    return bars, open_px, high, low, close


def _check_buckets() -> None:
    assert penetration_bucket(-1) == NO_PENETRATION
    assert penetration_bucket(0) == "0-10%"
    assert penetration_bucket(9.999) == "0-10%"
    assert penetration_bucket(10) == "10-20%"
    assert penetration_bucket(50) == "50-75%"
    assert penetration_bucket(75) == "75-100%"
    assert penetration_bucket(100) == "75-100%"
    assert penetration_bucket(100.01) == ">100%"
    assert body_fraction_bucket(0.0) == "<25%"
    assert body_fraction_bucket(0.25) == "25-50%"
    assert body_fraction_bucket(0.50) == "50-75%"
    assert body_fraction_bucket(0.75) == ">75%"
    assert depth_pool(29.9) == "shallow_0_30"
    assert depth_pool(30) == "mid_30_75"
    assert depth_pool(75) == "deep_gt_75"


def _check_reference() -> None:
    bull = build_reference(
        {"direction": "bullish", "range": 5.0, "close": 10.0, "low": 7.0, "high": 12.0, "open": 8.0}
    )
    assert bull is not None
    assert bull["reference_start"] == 10.0
    assert bull["reference_extreme"] == 7.0
    assert bull["reference_range"] == 3.0
    bear = build_reference(
        {"direction": "bearish", "range": 5.0, "close": 8.0, "low": 7.0, "high": 12.0, "open": 10.0}
    )
    assert bear is not None
    assert bear["reference_extreme"] == 12.0
    assert bear["reference_range"] == 4.0
    assert build_reference({"direction": "doji", "range": 5.0, "close": 10.0, "low": 7.0, "high": 12.0, "open": 10.0}) is None
    assert (
        build_reference({"direction": "bullish", "range": 2.0, "close": 7.0, "low": 7.0, "high": 9.0, "open": 8.0})
        is None
    )


def _check_sequence_and_forward() -> None:
    bars, open_px, high, low, close = _bars(40)
    # Bars 0-4 sit entirely above 100. Bar 5 is the later retracement.
    low[5] = 97.0
    high[5] = 100.25
    low[20] = 88.0
    reference = {
        "direction": "bullish",
        "sign": 1,
        "reference_start": 100.0,
        "reference_extreme": 90.0,
        "reference_range": 10.0,
    }
    measured = measure_sequence(bars, reference)
    assert measured["sequence_state"] == "retracement"
    assert measured["separation_index"] == 0
    assert measured["retracement_index"] == 5
    assert int(measured["retracement_index"]) > int(measured["separation_index"])
    assert abs(float(measured["separation_duration_minutes"]) - 5.0) < 1e-9
    assert abs(float(measured["retracement_penetration_pct"]) - 30.0) < 1e-9
    assert abs(float(measured["max_penetration_pct"]) - 120.0) < 1e-9
    assert measured["retracement_bucket"] == "30-40%"
    assert measured["max_penetration_bucket"] == ">100%"

    open_px[6] = 99.0
    close[10] = 101.0
    high[6:11] = 102.0
    low[6:11] = 98.0
    path = outcomes_from_entry(bars, 6, 1, previous_range=20.0, prefix="fwd")
    assert abs(path["fwd_measurement_price"] - 99.0) < 1e-9
    assert abs(path["fwd_ret_5m"] - (101.0 - 99.0)) < 1e-9
    assert abs(path["fwd_mfe_5m"] - 3.0) < 1e-9
    assert abs(path["fwd_mae_5m"] - 1.0) < 1e-9
    bear_path = outcomes_from_entry(bars, 6, -1, previous_range=20.0, prefix="fwd")
    assert abs(bear_path["fwd_ret_5m"] - (99.0 - 101.0)) < 1e-9
    assert abs(bear_path["fwd_mfe_5m"] - 1.0) < 1e-9
    assert abs(bear_path["fwd_mae_5m"] - 3.0) < 1e-9

    # A shallower non-crossing bar must not move the retracement.
    low[4] = 100.25
    again = measure_sequence(bars, reference)
    assert again["retracement_index"] == 5

    # One tick above the close is separation. An exact later touch is 0% penetration.
    tick_bars, _open, tick_high, tick_low, _close = _bars(8)
    tick_low[:] = 100.25
    tick_high[:] = 100.50
    tick_low[3] = 100.0
    tick_high[3] = 100.25
    one_tick = measure_sequence(tick_bars, reference)
    assert one_tick["sequence_state"] == "retracement"
    assert one_tick["separation_index"] == 0
    assert one_tick["retracement_index"] == 3
    assert abs(float(one_tick["retracement_penetration_pct"]) - 0.0) < 1e-9
    assert one_tick["retracement_bucket"] == "0-10%"

    # A bar that trades both sides of the close does not establish separation.
    cross_bars, _open, cross_high, cross_low, _close = _bars(6)
    cross_low[0] = 99.0
    cross_high[0] = 101.0
    cross_low[1:] = 101.0
    cross_high[1:] = 102.0
    crossed = measure_sequence(cross_bars, reference)
    assert crossed["sequence_state"] == "entered_before_separation"
    assert crossed["blocked_index"] == 0
    assert crossed["retracement_index"] == -1
    assert crossed["retracement_bucket"] == "no_retracement"

    # Separation with no later return is an audit state, not a penetration bucket.
    held_bars, _open, held_high, held_low, _close = _bars(6)
    held_low[:] = 100.25
    held_high[:] = 101.0
    held = measure_sequence(held_bars, reference)
    assert held["sequence_state"] == "separated_no_return"
    assert held["separation_index"] == 0
    assert held["retracement_index"] == -1
    assert held["retracement_bucket"] == "no_retracement"

    # Opening gap through the range is not a retracement event.
    gap_bars, _open, _gap_high, gap_low, _close = _bars(6)
    gap_low[0] = 80.0
    gapped = measure_sequence(gap_bars, reference)
    assert gapped["sequence_state"] == "entered_before_separation"
    assert gapped["retracement_index"] == -1

    # Bearish mirror: bars entirely below the close, then a later bar trades back up.
    bear_bars, _open, bear_high, bear_low, _close = _bars(8)
    bear_high[:] = 99.0
    bear_low[:] = 98.0
    bear_high[4] = 103.0
    bear_low[4] = 99.5
    bear_reference = {
        "direction": "bearish",
        "sign": -1,
        "reference_start": 100.0,
        "reference_extreme": 110.0,
        "reference_range": 10.0,
    }
    bear = measure_sequence(bear_bars, bear_reference)
    assert bear["sequence_state"] == "retracement"
    assert bear["separation_index"] == 0
    assert bear["retracement_index"] == 4
    assert abs(float(bear["retracement_penetration_pct"]) - 30.0) < 1e-9
    assert bear["retracement_bucket"] == "30-40%"


def _frame_from_pools(mapping: dict[tuple[str, str, str], float], noise: float = 0.0) -> pd.DataFrame:
    rows = []
    pen = {"shallow_0_30": 10.0, "mid_30_75": 50.0, "deep_gt_75": 90.0}
    rng = np.random.default_rng(1)
    for (split, direction, pool), median in mapping.items():
        for _ in range(60):
            shock = float(rng.normal(0.0, noise))
            rows.append(
                {
                    "split": split,
                    "direction": direction,
                    "retracement_pool": pool,
                    "retracement_penetration_pct": pen[pool] + shock,
                    "fwd_ret_rng_30m": median + shock * 0.01,
                    "fwd_ret_rng_60m": median + shock * 0.01,
                }
            )
    return pd.DataFrame(rows)


def _check_verdict_rule() -> None:
    pools = ("shallow_0_30", "mid_30_75", "deep_gt_75")
    levels = {"shallow_0_30": 0.00, "mid_30_75": 0.03, "deep_gt_75": 0.06}
    supported_map = {
        (split, direction, pool): levels[pool]
        for split in ("IS", "Validation", "OOS")
        for direction in ("bullish", "bearish")
        for pool in pools
    }
    assert decide(_frame_from_pools(supported_map))["verdict"] == "MECHANISM SUPPORTED"

    opposed = {}
    for direction in ("bullish", "bearish"):
        for pool in pools:
            opposed[("IS", direction, pool)] = levels[pool]
            opposed[("Validation", direction, pool)] = -levels[pool]
            opposed[("OOS", direction, pool)] = 0.0
    # Equal-and-opposite IS/Validation plus a flat combined correlation.
    mixed = _frame_from_pools(opposed, noise=0.0)
    mixed["retracement_penetration_pct"] = np.tile(np.linspace(0, 100, 60), len(mixed) // 60)
    assert decide(mixed)["verdict"] == "MECHANISM NOT SUPPORTED"

    flat = {
        (split, direction, pool): 0.01
        for split in ("IS", "Validation", "OOS")
        for direction in ("bullish", "bearish")
        for pool in pools
    }
    assert decide(_frame_from_pools(flat))["verdict"] == "MECHANISM UNCLEAR"


def run_definition_tests() -> None:
    _check_buckets()
    _check_reference()
    _check_sequence_and_forward()
    _check_verdict_rule()
    print("definition tests passed", flush=True)


if __name__ == "__main__":
    run_definition_tests()
