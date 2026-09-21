"""State-machine tests on a hand-built session list. No market data."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE_DIR))

from candles import Candle  # noqa: E402
from score import metrics_table, summarize  # noqa: E402
from state_machine import build_forecasts, qualifying, update_state  # noqa: E402
from verdict import judge  # noqa: E402
from definitions import DOWN, NONE, PRIMARY, UP  # noqa: E402


def _candle(day: int, open_: float, high: float, low: float, close: float) -> Candle:
    return Candle(
        session_date=date(2020, 1, day),
        year=2020,
        split="IS",
        open=open_,
        high=high,
        low=low,
        close=close,
    )


def _hand_list() -> list[Candle]:
    return [
        _candle(1, 100, 110, 90, 100),
        _candle(2, 100, 101, 99, 100),
        _candle(3, 100, 120, 95, 115),
        _candle(6, 115, 130, 110, 125),
        _candle(7, 125, 140, 120, 135),
        _candle(8, 135, 136, 121, 122),
        _candle(9, 122, 123, 100, 105),
        _candle(10, 105, 122, 104, 118),
        _candle(13, 118, 140, 117, 130),
        _candle(14, 130, 131, 129, 130),
    ]


def _row(frame: pd.DataFrame, signal_day: int) -> pd.Series:
    return frame.loc[frame["signal_date"] == date(2020, 1, signal_day).isoformat()].iloc[0]


def test_three_bulls_stay_up() -> None:
    frame = build_forecasts(_hand_list())
    for day in (3, 6, 7):
        row = _row(frame, day)
        assert row["qualifying"] == "bull"
        assert row["test1_sign"] == 1
        assert row["test2_state"] == UP
        assert row["test2_sign"] == 1


def test_red_above_prior_low_stays_up() -> None:
    row = _row(build_forecasts(_hand_list()), 8)
    assert row["qualifying"] == "bear"
    assert row["test1_sign"] == -1
    assert row["test2_state"] == UP
    assert row["test2_sign"] == 1


def test_flip_down_forecasts_the_following_day() -> None:
    frame = build_forecasts(_hand_list())
    scored_as_prior = _row(frame, 8)
    assert scored_as_prior["target_date"] == date(2020, 1, 9).isoformat()
    assert scored_as_prior["test2_sign"] == 1
    flip = _row(frame, 9)
    assert flip["qualifying"] == "bear"
    assert flip["test2_state"] == DOWN
    assert flip["test2_sign"] == -1
    assert flip["target_date"] == date(2020, 1, 10).isoformat()
    candles = _hand_list()
    assert candles[6].close < candles[5].low
    assert qualifying(candles[6], candles[5]) == "bear"


def test_mirror_flip_up() -> None:
    frame = build_forecasts(_hand_list())
    stay = _row(frame, 10)
    assert stay["qualifying"] == "bull"
    assert stay["test1_sign"] == 1
    assert stay["test2_state"] == DOWN
    assert stay["test2_sign"] == -1
    before = _row(frame, 10)
    assert before["target_date"] == date(2020, 1, 13).isoformat()
    flip = _row(frame, 13)
    assert flip["test2_state"] == UP
    assert flip["test2_sign"] == 1
    assert flip["target_date"] == date(2020, 1, 14).isoformat()
    assert _row(frame, 10)["test2_sign"] == -1


def test_none_has_no_test2_forecast() -> None:
    frame = build_forecasts(_hand_list())
    for day in (1, 2):
        row = _row(frame, day)
        assert row["test2_state"] == NONE
        assert pd.isna(row["test2_sign"])
        assert row["qualifying"] == ""
        assert pd.isna(row["test1_sign"])


def test_rebuild_is_identical() -> None:
    candles = _hand_list()
    first = build_forecasts(candles)
    second = build_forecasts(candles)
    pd.testing.assert_frame_equal(first, second)


def test_qualifying_opposite_day_does_not_flip_without_breach() -> None:
    candles = _hand_list()
    assert update_state(UP, candles[5], candles[4]) == UP
    assert update_state(DOWN, candles[7], candles[6]) == DOWN
    assert update_state(UP, candles[6], candles[5]) == DOWN
    assert update_state(DOWN, candles[8], candles[7]) == UP
    assert update_state(NONE, candles[2], candles[1]) == UP


def test_matched_base_rate() -> None:
    summary = summarize(
        sign=pd.Series([1, 1, -1]).to_numpy(),
        outcome_sign=pd.Series([1, 1, -1]).to_numpy(),
        points=pd.Series([1.0, 1.0, 1.0]).to_numpy(),
        p_up=2.0 / 3.0,
        p_down=1.0 / 3.0,
        p_flat=0.0,
    )
    assert summary["n"] == 3
    assert summary["hit_rate"] == 1.0
    assert abs(summary["matched_base_rate"] - (5.0 / 9.0)) < 1e-12
    assert abs(summary["lift"] - (1.0 - 5.0 / 9.0)) < 1e-12


def test_flat_is_a_miss_in_the_denominator() -> None:
    summary = summarize(
        sign=pd.Series([1, 1, 1]).to_numpy(),
        outcome_sign=pd.Series([1, 0, -1]).to_numpy(),
        points=pd.Series([2.0, 0.0, -3.0]).to_numpy(),
        p_up=1.0 / 3.0,
        p_down=1.0 / 3.0,
        p_flat=1.0 / 3.0,
    )
    assert summary["n"] == 3
    assert summary["n_flat"] == 1
    assert abs(summary["hit_rate"] - (1.0 / 3.0)) < 1e-12


def test_verdict_requires_all_clauses() -> None:
    rows = []
    for model in ("test1_pooled", "test2_pooled", "test1_bear", "test2_down", "test2_up", "always_long"):
        for slice_name, lift in (("IS", 0.02), ("Validation", 0.01), ("OOS", 0.01), ("All", 0.01)):
            rows.append(
                {
                    "model": model,
                    "slice": slice_name,
                    "lift": lift,
                    "hit_rate": 0.60 if model != "always_long" else 0.55,
                    "n": 10,
                }
            )
    metrics = pd.DataFrame(rows)
    agreement = pd.DataFrame(
        [
            {"model": "test1", "slice": "All", "block": "disagree", "hit_rate": 0.40, "n": 10},
            {"model": "test2", "slice": "All", "block": "disagree", "hit_rate": 0.60, "n": 10},
        ]
    )
    passed = judge(metrics, agreement)
    assert passed["verdict"] == "REAL"
    assert passed["flip_adds"] is True
    assert passed["long_beats_bullish_state"] is False

    metrics.loc[(metrics["model"] == "test1_bear") & (metrics["slice"] == "OOS"), "lift"] = -0.01
    failed = judge(metrics, agreement)
    assert failed["verdict"] == "NOT REAL"
    assert any("test1_bear" in line and "OOS" in line for line in failed["failures"])


def test_metrics_always_long_matches_base_rate() -> None:
    frame = pd.DataFrame(
        {
            "year": [2020, 2020, 2020],
            "split": ["IS", "IS", "IS"],
            "test1_sign": [1, pd.NA, -1],
            "test2_sign": [1, 1, -1],
            "always_long_sign": [1, 1, 1],
            "primary_sign": [1, 0, -1],
            "secondary_sign": [1, -1, -1],
            "body": [2.0, 0.0, -4.0],
            "close_to_close": [3.0, -1.0, -2.0],
        }
    )
    table = metrics_table(frame, PRIMARY)
    always = table.loc[(table["model"] == "always_long") & (table["slice"] == "All")].iloc[0]
    assert always["n"] == 3
    assert always["n_flat"] == 1
    assert abs(always["hit_rate"] - always["p_up"]) < 1e-12
    assert abs(always["mean_signed_body"] - frame["body"].mean()) < 1e-12


def main() -> None:
    test_three_bulls_stay_up()
    test_red_above_prior_low_stays_up()
    test_flip_down_forecasts_the_following_day()
    test_mirror_flip_up()
    test_none_has_no_test2_forecast()
    test_rebuild_is_identical()
    test_qualifying_opposite_day_does_not_flip_without_breach()
    test_matched_base_rate()
    test_flat_is_a_miss_in_the_denominator()
    test_verdict_requires_all_clauses()
    test_metrics_always_long_matches_base_rate()
    print("ok")


if __name__ == "__main__":
    main()
