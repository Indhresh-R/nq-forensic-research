"""1m → 15m aggregation, gap segments, causal ATR (Step 2 freezes)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from constants import ATR_N, GAP_TOLERANCE_MINUTES, TICK, TICK_INV


def to_ticks(price: float | np.ndarray) -> np.ndarray | int:
    arr = np.asarray(price, dtype=np.float64)
    ticks = np.rint(arr * TICK_INV).astype(np.int64)
    if arr.ndim == 0:
        return int(ticks)
    return ticks


def from_ticks(ticks: int | np.ndarray) -> float | np.ndarray:
    arr = np.asarray(ticks, dtype=np.float64)
    out = arr * TICK
    if arr.ndim == 0:
        return float(out)
    return out


def build_15m(df_1m: pd.DataFrame) -> pd.DataFrame:
    """
    Globex-aligned 15m bars from 18:00 NY.

    Incomplete buckets (n != 15) are dropped. No OHLC forward-fill.
    """
    x = df_1m.sort_values("ts").reset_index(drop=True).copy()
    x["offset"] = (x["ny_min"].to_numpy(np.int16) - 18 * 60) % (24 * 60)
    x["bucket"] = x["offset"] // 15
    g = x.groupby(["session_date", "bucket"], sort=True)
    b = g.agg(
        start=("ts", "first"),
        end=("ts", "last"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        n=("close", "size"),
        year=("year", "last"),
        session_date=("session_date", "last"),
    ).reset_index(drop=True)
    b = b.loc[b["n"] == 15].reset_index(drop=True)
    b["i"] = np.arange(len(b), dtype=np.int64)
    b["open_ticks"] = to_ticks(b["open"].to_numpy())
    b["high_ticks"] = to_ticks(b["high"].to_numpy())
    b["low_ticks"] = to_ticks(b["low"].to_numpy())
    b["close_ticks"] = to_ticks(b["close"].to_numpy())
    return b


def mark_segments(bars: pd.DataFrame) -> pd.DataFrame:
    """Assign contiguous segment ids; break when gap > GAP_TOLERANCE_MINUTES."""
    out = bars.copy()
    if len(out) == 0:
        out["gap_minutes_before"] = np.array([], dtype=np.float64)
        out["segment_id"] = np.array([], dtype=np.int64)
        out["segment_break"] = np.array([], dtype=bool)
        return out
    start = pd.to_datetime(out["start"], utc=True)
    end = pd.to_datetime(out["end"], utc=True)
    gap_min = np.empty(len(out), dtype=np.float64)
    gap_min[0] = np.inf
    if len(out) > 1:
        delta_ns = start.iloc[1:].to_numpy(dtype="datetime64[ns]") - end.iloc[:-1].to_numpy(
            dtype="datetime64[ns]"
        )
        gap_min[1:] = delta_ns.astype("timedelta64[ns]").astype(np.float64) / 60e9
    break_mask = gap_min > GAP_TOLERANCE_MINUTES
    seg = np.cumsum(break_mask.astype(np.int64))
    out["gap_minutes_before"] = gap_min
    out["segment_id"] = seg
    out["segment_break"] = break_mask
    return out


def causal_atr20(bars: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Per-segment simple-mean ATR(20).

    atr_at[t] = mean TR over bars [t-19..t] within segment.
    atr_prior[t] = atr_at[t-1] (NaN at segment starts / warm-up).
    """
    n = len(bars)
    high = bars["high"].to_numpy(np.float64)
    low = bars["low"].to_numpy(np.float64)
    close = bars["close"].to_numpy(np.float64)
    seg = bars["segment_id"].to_numpy(np.int64)

    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    breaks = np.zeros(n, dtype=bool)
    breaks[0] = True
    breaks[1:] = seg[1:] != seg[:-1]
    prev_close = prev_close.copy()
    prev_close[breaks] = close[breaks]

    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    tr[breaks] = high[breaks] - low[breaks]

    s = pd.Series(tr)
    atr_at = (
        s.groupby(seg, sort=False)
        .transform(lambda x: x.rolling(ATR_N, min_periods=ATR_N).mean())
        .to_numpy(np.float64)
    )

    atr_prior = np.full(n, np.nan, dtype=np.float64)
    atr_prior[1:] = atr_at[:-1]
    atr_prior[breaks] = np.nan
    return atr_at, atr_prior
