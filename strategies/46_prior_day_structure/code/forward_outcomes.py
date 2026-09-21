"""Direction-normalized forward returns, MFE, and MAE after a causal measurement bar."""
from __future__ import annotations

import numpy as np

from definitions import HORIZON_TOLERANCE_NS, HORIZONS, SESSION_END
from daily_candles import SessionBars


def _horizon_index(ts_ns: np.ndarray, entry_index: int, minutes: int) -> int:
    """Index of the bar whose close is `minutes` after the entry open, or -1."""
    target = int(ts_ns[entry_index]) + (minutes - 1) * 60 * 1_000_000_000
    position = int(np.searchsorted(ts_ns, target, side="right") - 1)
    if position < entry_index:
        return -1
    if int(ts_ns[position]) < target - HORIZON_TOLERANCE_NS:
        return -1
    return position


def _path_stats(
    bars: SessionBars,
    entry_index: int,
    end_index: int,
    sign: int,
) -> tuple[float, float, float]:
    entry = float(bars.open[entry_index])
    future = float(bars.close[end_index])
    highs = bars.high[entry_index : end_index + 1]
    lows = bars.low[entry_index : end_index + 1]
    if sign == 1:
        forward = future - entry
        mfe = float(max(0.0, highs.max() - entry))
        mae = float(max(0.0, entry - lows.min()))
    else:
        forward = entry - future
        mfe = float(max(0.0, entry - lows.min()))
        mae = float(max(0.0, highs.max() - entry))
    return forward, mfe, mae


def outcomes_from_entry(
    bars: SessionBars,
    entry_index: int,
    sign: int,
    previous_range: float,
    prefix: str,
) -> dict[str, float]:
    """Forward path starting at `entry_index` open. `prefix` is `fwd` or `base`."""
    out: dict[str, float] = {}
    scale = previous_range if previous_range > 0.0 else np.nan
    horizon_names = tuple(name for name, _minutes in HORIZONS) + (SESSION_END,)
    if entry_index < 0 or entry_index >= len(bars.open):
        for name in horizon_names:
            out[f"{prefix}_ret_{name}"] = np.nan
            out[f"{prefix}_mfe_{name}"] = np.nan
            out[f"{prefix}_mae_{name}"] = np.nan
            out[f"{prefix}_ret_rng_{name}"] = np.nan
            out[f"{prefix}_mfe_rng_{name}"] = np.nan
            out[f"{prefix}_mae_rng_{name}"] = np.nan
        out[f"{prefix}_minutes_remaining"] = np.nan
        out[f"{prefix}_measurement_price"] = np.nan
        return out

    out[f"{prefix}_measurement_price"] = float(bars.open[entry_index])
    last = len(bars.open) - 1
    out[f"{prefix}_minutes_remaining"] = float((int(bars.ts_ns[last]) - int(bars.ts_ns[entry_index])) / 60_000_000_000)

    ends: list[tuple[str, int]] = []
    for name, minutes in HORIZONS:
        ends.append((name, _horizon_index(bars.ts_ns, entry_index, minutes)))
    ends.append((SESSION_END, last if last >= entry_index else -1))

    for name, end_index in ends:
        if end_index < 0:
            forward = mfe = mae = np.nan
        else:
            forward, mfe, mae = _path_stats(bars, entry_index, end_index, sign)
        out[f"{prefix}_ret_{name}"] = forward
        out[f"{prefix}_mfe_{name}"] = mfe
        out[f"{prefix}_mae_{name}"] = mae
        out[f"{prefix}_ret_rng_{name}"] = forward / scale if np.isfinite(forward) else np.nan
        out[f"{prefix}_mfe_rng_{name}"] = mfe / scale if np.isfinite(mfe) else np.nan
        out[f"{prefix}_mae_rng_{name}"] = mae / scale if np.isfinite(mae) else np.nan
    return out
