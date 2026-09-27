"""Frozen Test 1 qualifier and Test 2 state machine.

The forecast for day t+1 is the state after day t is processed.
Day t is never scored under the state that day t itself just created.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from candles import Candle
from definitions import DOWN, NONE, UP


def qualifying(curr: Candle, prev: Candle) -> str | None:
    """Bull and bear require both body color and a close beyond the prior close."""
    if curr.close > curr.open and curr.close > prev.close:
        return "bull"
    if curr.close < curr.open and curr.close < prev.close:
        return "bear"
    return None


def update_state(state: str, curr: Candle, prev: Candle) -> str:
    """Update only from a completed day and the previous kept session.

    From UP, a qualifying bear day does not flip unless the close is also
    below the prior session low. From DOWN, a qualifying bull day does not
    flip unless the close is also above the prior session high.
    """
    if state == NONE:
        kind = qualifying(curr, prev)
        if kind == "bull":
            return UP
        if kind == "bear":
            return DOWN
        return NONE
    if state == UP:
        if curr.close < prev.low and curr.close < curr.open:
            return DOWN
        return UP
    if state == DOWN:
        if curr.close > prev.high and curr.close > curr.open:
            return UP
        return DOWN
    raise ValueError(f"unknown state {state}")


def _sign_from_qualifying(kind: str | None) -> int | None:
    if kind == "bull":
        return 1
    if kind == "bear":
        return -1
    return None


def _sign_from_state(state: str) -> int | None:
    if state == UP:
        return 1
    if state == DOWN:
        return -1
    return None


def _outcome_sign(left: float, right: float) -> int:
    if left > right:
        return 1
    if left < right:
        return -1
    return 0


def build_forecasts(candles: list[Candle]) -> pd.DataFrame:
    """One row per kept session that has a next kept session.

    t-1 is the previous kept session, not the previous calendar date.
    The first session has no t-1, so it cannot qualify and cannot set state.
    """
    rows: list[dict[str, object]] = []
    state = NONE
    for i in range(len(candles) - 1):
        curr = candles[i]
        target = candles[i + 1]
        if i == 0:
            kind = None
            test2_state = NONE
        else:
            prev = candles[i - 1]
            kind = qualifying(curr, prev)
            state = update_state(state, curr, prev)
            test2_state = state
        rows.append(
            {
                "signal_date": curr.session_date.isoformat(),
                "target_date": target.session_date.isoformat(),
                "year": curr.year,
                "split": curr.split,
                "qualifying": kind if kind is not None else "",
                "test1_sign": _sign_from_qualifying(kind),
                "test2_state": test2_state,
                "test2_sign": _sign_from_state(test2_state),
                "always_long_sign": 1,
                "primary_sign": _outcome_sign(target.close, target.open),
                "secondary_sign": _outcome_sign(target.close, curr.close),
                "body": target.close - target.open,
                "close_to_close": target.close - curr.close,
            }
        )
    return pd.DataFrame(rows)


def signal_date(value: str) -> date:
    return date.fromisoformat(value)
