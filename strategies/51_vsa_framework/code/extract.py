"""
Causal VSA No Demand sequence extraction (Step 2).

Produces event classes A / B / C under PREREGISTRATION.md freezes.
No forward returns. No mechanism outcomes.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from bars import build_15m, causal_atr20, mark_segments
from constants import (
    LOC_ATR_FRAC,
    LOC_K,
    MEDIAN_N,
    MIN_PRIOR_BARS,
    MIN_SEPARATION,
    ND_CLOSE_FRAC_MAX,
    SOW_L,
    W2_CLOSE_FRAC_MAX,
    WIDE_MULT,
)


def _rolling_median_prior(values: np.ndarray, seg: np.ndarray, window: int) -> np.ndarray:
    """Median of prior `window` bars within segment (excludes current bar)."""
    n = len(values)
    out = np.full(n, np.nan, dtype=np.float64)
    s = pd.Series(values)
    # shift so rolling window ends at t-1
    prior = s.groupby(seg, sort=False).shift(1)
    med = (
        prior.groupby(seg, sort=False)
        .transform(lambda x: x.rolling(window, min_periods=window).median())
        .to_numpy(np.float64)
    )
    out[:] = med
    return out


def _seg_position(seg: np.ndarray) -> np.ndarray:
    """0-based index within each segment."""
    pos = np.empty(len(seg), dtype=np.int64)
    if len(seg) == 0:
        return pos
    counts: dict[int, int] = {}
    for i, s in enumerate(seg):
        c = counts.get(int(s), 0)
        pos[i] = c
        counts[int(s)] = c + 1
    return pos


def prepare_bars(df_1m: pd.DataFrame) -> pd.DataFrame:
    bars = build_15m(df_1m)
    bars = mark_segments(bars)
    atr_at, atr_prior = causal_atr20(bars)
    bars["atr_at"] = atr_at
    bars["atr_prior"] = atr_prior

    high = bars["high"].to_numpy(np.float64)
    low = bars["low"].to_numpy(np.float64)
    close = bars["close"].to_numpy(np.float64)
    volume = bars["volume"].to_numpy(np.float64)
    seg = bars["segment_id"].to_numpy(np.int64)

    spread = high - low
    bars["spread"] = spread
    close_frac = np.full(len(bars), np.nan, dtype=np.float64)
    pos_spread = spread > 0.0
    close_frac[pos_spread] = (close[pos_spread] - low[pos_spread]) / spread[pos_spread]
    bars["close_frac"] = close_frac

    bars["med_spread"] = _rolling_median_prior(spread, seg, MEDIAN_N)
    bars["med_vol"] = _rolling_median_prior(volume, seg, MEDIAN_N)

    prev_close = np.roll(close, 1)
    prev_close[0] = np.nan
    breaks = np.zeros(len(bars), dtype=bool)
    breaks[0] = True
    breaks[1:] = seg[1:] != seg[:-1]
    prev_close = prev_close.copy()
    prev_close[breaks] = np.nan

    bars["up_bar"] = close > prev_close
    bars["down_bar"] = close < prev_close
    # first bar of segment: not up/down vs prior segment
    bars.loc[breaks, "up_bar"] = False
    bars.loc[breaks, "down_bar"] = False

    vol_prev1 = np.roll(volume, 1)
    vol_prev2 = np.roll(volume, 2)
    vol_prev1[0] = np.nan
    vol_prev2[:2] = np.nan
    # invalidate across segment boundaries
    for i in range(len(bars)):
        if breaks[i]:
            vol_prev1[i] = np.nan
            vol_prev2[i] = np.nan
        elif i >= 1 and breaks[i - 1]:
            vol_prev2[i] = np.nan
    bars["vol_lt_prior2"] = (volume < vol_prev1) & (volume < vol_prev2)

    bars["narrow"] = spread <= bars["med_spread"].to_numpy(np.float64)
    bars["wide"] = spread >= (WIDE_MULT * bars["med_spread"].to_numpy(np.float64))
    bars["high_vol"] = volume >= bars["med_vol"].to_numpy(np.float64)
    bars["not_narrow"] = spread >= bars["med_spread"].to_numpy(np.float64)

    pos = _seg_position(seg)
    bars["seg_pos"] = pos
    bars["warmup_ok"] = pos >= MIN_PRIOR_BARS

    return bars


def _build_sow_known(bars: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Return:
      sow_w1_known_at[t] = True if a W1 seed became known at bar t (close of s+1)
      sow_w2_known_at[t] = True if a W2 seed is known at bar t (close of s)
    """
    n = len(bars)
    w1 = np.zeros(n, dtype=bool)
    w2 = np.zeros(n, dtype=bool)
    if n < 3:
        return w1, w2

    up = bars["up_bar"].to_numpy(bool)
    high = bars["high"].to_numpy(np.float64)
    close = bars["close"].to_numpy(np.float64)
    high_vol = bars["high_vol"].to_numpy(bool)
    wide = bars["wide"].to_numpy(bool)
    not_narrow = bars["not_narrow"].to_numpy(bool)
    vol_lt = bars["vol_lt_prior2"].to_numpy(bool)
    close_frac = bars["close_frac"].to_numpy(np.float64)
    seg = bars["segment_id"].to_numpy(np.int64)
    med_ok = np.isfinite(bars["med_spread"].to_numpy(np.float64)) & np.isfinite(
        bars["med_vol"].to_numpy(np.float64)
    )

    prev_high = np.roll(high, 1)
    prev_high[0] = np.nan
    breaks = np.zeros(n, dtype=bool)
    breaks[0] = True
    breaks[1:] = seg[1:] != seg[:-1]
    prev_high = prev_high.copy()
    prev_high[breaks] = np.nan

    for s in range(n):
        if not med_ok[s]:
            continue
        # W2 known at s
        probe_up = bool(up[s]) or (np.isfinite(prev_high[s]) and high[s] > prev_high[s])
        if (
            probe_up
            and wide[s]
            and (high_vol[s] or vol_lt[s])
            and np.isfinite(close_frac[s])
            and close_frac[s] <= W2_CLOSE_FRAC_MAX
        ):
            w2[s] = True

        # W1: seed at s, known at s+1
        if s + 1 >= n:
            continue
        if seg[s + 1] != seg[s]:
            continue
        if not (up[s] and high_vol[s] and (wide[s] or not_narrow[s])):
            continue
        # no progress on next bar
        no_progress = (close[s + 1] <= close[s]) or (high[s + 1] <= high[s])
        if no_progress:
            w1[s + 1] = True

    return w1, w2


def _has_sow_in_lookback(
    t: int,
    seg: np.ndarray,
    w1_known: np.ndarray,
    w2_known: np.ndarray,
) -> tuple[bool, str]:
    """Any W1/W2 seed whose known-time is in [t-L, t-1] and same segment."""
    lo = t - SOW_L
    if lo < 0:
        lo = 0
    for k in range(lo, t):
        if seg[k] != seg[t]:
            continue
        if w1_known[k]:
            return True, "W1"
        if w2_known[k]:
            return True, "W2"
    return False, ""


def _rolling_hh_prior(high: np.ndarray, seg: np.ndarray, k: int) -> np.ndarray:
    """max(high[t-k…t-1]) within segment; NaN if fewer than k prior bars in segment."""
    n = len(high)
    out = np.full(n, np.nan, dtype=np.float64)
    s = pd.Series(high)
    prior = s.groupby(seg, sort=False).shift(1)
    hh = (
        prior.groupby(seg, sort=False)
        .transform(lambda x: x.rolling(k, min_periods=k).max())
        .to_numpy(np.float64)
    )
    out[:] = hh
    return out


def extract_events(df_1m: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    bars = prepare_bars(df_1m)
    n = len(bars)
    funnel: dict[str, int] = {
        "bars_15m": n,
        "warmup_ok": 0,
        "up_bars": 0,
        "location_near_high": 0,
        "sow_seed": 0,
        "bg_weak": 0,
        "nd_morphology": 0,
        "nd_and_bg_candidates": 0,
        "nd_without_bg_candidates": 0,
        "bg_up_without_nd_candidates": 0,
        "confirm_gap_abort": 0,
        "confirm_fail_not_down": 0,
        "confirm_ok_C": 0,
        "confirm_ok_A": 0,
        "confirm_ok_B": 0,
        "skipped_separation": 0,
        "skipped_overlap": 0,
    }

    if n == 0:
        meta = {
            "n_1m": int(len(df_1m)),
            "n_15m": 0,
            "n_segments": 0,
            "funnel": funnel,
            "n_events": 0,
        }
        return pd.DataFrame(), bars, meta

    w1_known, w2_known = _build_sow_known(bars)
    bars["sow_w1_known"] = w1_known
    bars["sow_w2_known"] = w2_known

    high = bars["high"].to_numpy(np.float64)
    close = bars["close"].to_numpy(np.float64)
    volume = bars["volume"].to_numpy(np.float64)
    spread = bars["spread"].to_numpy(np.float64)
    close_frac = bars["close_frac"].to_numpy(np.float64)
    seg = bars["segment_id"].to_numpy(np.int64)
    atr = bars["atr_at"].to_numpy(np.float64)
    up = bars["up_bar"].to_numpy(bool)
    down = bars["down_bar"].to_numpy(bool)
    narrow = bars["narrow"].to_numpy(bool)
    vol_lt = bars["vol_lt_prior2"].to_numpy(bool)
    warmup = bars["warmup_ok"].to_numpy(bool)
    med_spread = bars["med_spread"].to_numpy(np.float64)
    med_vol = bars["med_vol"].to_numpy(np.float64)

    hh = _rolling_hh_prior(high, seg, LOC_K)
    bars["hh_prior"] = hh

    events: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    next_eligible = 0
    last_event_t = -10**9
    last_confirm_t = -10**9

    for t in range(n):
        if not warmup[t]:
            continue
        if not (np.isfinite(med_spread[t]) and np.isfinite(med_vol[t]) and np.isfinite(atr[t])):
            continue
        funnel["warmup_ok"] += 1

        if not up[t]:
            continue
        funnel["up_bars"] += 1

        # Location A1
        loc_ok = False
        if np.isfinite(hh[t]) and np.isfinite(atr[t]) and atr[t] > 0:
            loc_ok = high[t] >= (hh[t] - LOC_ATR_FRAC * atr[t])
        if loc_ok:
            funnel["location_near_high"] += 1

        sow_ok, sow_kind = _has_sow_in_lookback(t, seg, w1_known, w2_known)
        if sow_ok:
            funnel["sow_seed"] += 1

        bg_weak = bool(loc_ok and sow_ok)
        if bg_weak:
            funnel["bg_weak"] += 1

        # ND morphology (requires positive spread for close_frac)
        nd_morph = False
        if (
            spread[t] > 0.0
            and narrow[t]
            and vol_lt[t]
            and np.isfinite(close_frac[t])
            and close_frac[t] <= ND_CLOSE_FRAC_MAX
        ):
            nd_morph = True
            funnel["nd_morphology"] += 1

        # Classify candidate path
        path: str | None = None
        if nd_morph and bg_weak:
            path = "C"
            funnel["nd_and_bg_candidates"] += 1
        elif nd_morph and not bg_weak:
            path = "A"
            funnel["nd_without_bg_candidates"] += 1
        elif bg_weak and not nd_morph:
            # Control B: ordinary up-bar in weak background (fails ≥1 ND component)
            path = "B"
            funnel["bg_up_without_nd_candidates"] += 1
        else:
            continue

        # Event dependence
        if t < next_eligible:
            funnel["skipped_separation"] += 1
            continue
        if last_event_t <= t <= last_confirm_t:
            funnel["skipped_overlap"] += 1
            continue

        u = t + 1
        # Confirmation requires next bar in same segment
        if u >= n or seg[u] != seg[t]:
            funnel["confirm_gap_abort"] += 1
            failed.append(
                {
                    "t_event": t,
                    "path": path,
                    "reason": "gap_or_missing_confirm_bar",
                    "bg_weak": bg_weak,
                    "nd_morph": nd_morph,
                    "sow_kind": sow_kind,
                }
            )
            last_event_t = t
            last_confirm_t = t  # no confirm bar
            next_eligible = t + MIN_SEPARATION
            continue

        if not down[u]:
            funnel["confirm_fail_not_down"] += 1
            failed.append(
                {
                    "t_event": t,
                    "t_attempt_confirm": u,
                    "path": path,
                    "reason": "confirm_not_down",
                    "bg_weak": bg_weak,
                    "nd_morph": nd_morph,
                    "sow_kind": sow_kind,
                }
            )
            last_event_t = t
            last_confirm_t = u
            next_eligible = t + MIN_SEPARATION
            continue

        # Confirmed observation
        funnel[f"confirm_ok_{path}"] += 1
        row = {
            "event_class": path,
            "kind": "no_demand_sequence" if path in ("A", "C") else "bg_up_control",
            "t_event": int(t),
            "t_confirmation": int(u),
            "t_sequence_complete": int(u),
            "session_date": bars["session_date"].iat[u],
            "year": int(bars["year"].iat[u]),
            "segment_id": int(seg[t]),
            "bg_weak": bool(bg_weak),
            "location_ok": bool(loc_ok),
            "sow_ok": bool(sow_ok),
            "sow_kind": sow_kind if sow_ok else "",
            "nd_morph": bool(nd_morph),
            "narrow": bool(narrow[t]),
            "vol_lt_prior2": bool(vol_lt[t]),
            "close_frac_event": float(close_frac[t]) if np.isfinite(close_frac[t]) else np.nan,
            "spread_event": float(spread[t]),
            "volume_event": float(volume[t]),
            "high_event": float(high[t]),
            "close_event": float(close[t]),
            "close_confirm": float(close[u]),
            "hh_prior": float(hh[t]) if np.isfinite(hh[t]) else np.nan,
            "atr_event": float(atr[t]),
            "start_event": bars["start"].iat[t],
            "end_event": bars["end"].iat[t],
            "start_confirm": bars["start"].iat[u],
            "end_confirm": bars["end"].iat[u],
            "confirm_ok": True,
        }
        events.append(row)
        last_event_t = t
        last_confirm_t = u
        next_eligible = t + MIN_SEPARATION

    ev = pd.DataFrame(events)
    fail_df = pd.DataFrame(failed)

    meta: dict[str, Any] = {
        "n_1m": int(len(df_1m)),
        "n_15m": int(n),
        "n_segments": int(bars["segment_id"].nunique()) if n else 0,
        "funnel": funnel,
        "n_events": int(len(ev)),
        "n_failed_confirm_attempts": int(len(fail_df)),
        "class_counts": (
            ev["event_class"].value_counts().to_dict() if len(ev) else {"A": 0, "B": 0, "C": 0}
        ),
    }
    # stash failed for runner
    meta["_failed_df"] = fail_df
    return ev, bars, meta
