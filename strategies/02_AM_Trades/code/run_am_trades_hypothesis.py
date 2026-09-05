"""
AM Trades NY Continuation — fresh hypothesis test (no ORB/VWAP/SMT reuse).
Definitions frozen in artifacts/am_trades_definitions.md BEFORE any metrics.
"""
from __future__ import annotations

import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))


import json
import math
import warnings
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

from common.paths import ART, DATA, ROOT, art

# --- Frozen primary parameters (see definitions.md) ---
LOOKBACK_DAYS = 30
SWING_SEP = 40.0
SLIPPAGE = 1.0
COMMISSION_RT = 0.25
STOP_BUFFER = 0.25
TARGET_R = 2.0
MIN_RISK = 1.0
TICK = 0.25

IS_YEARS = set(range(2010, 2022))
VAL_YEARS = {2022, 2023, 2024}
OOS_YEARS = {2025, 2026}


@dataclass
class Trade:
    session_date: str
    year: int
    split: str
    direction: int  # +1 long, -1 short
    bias: str
    profile: str
    signal_ts: str
    entry_ts: str
    exit_ts: str
    entry: float
    stop: float
    target: float
    risk: float
    exit_price: float
    pnl_points: float
    pnl_R: float
    exit_reason: str
    ambiguous_bar: bool
    gap_through_stop: bool
    blocked: bool
    open_930: float
    entry_vs_930: float
    mae: float
    mfe: float
    mae_R: float
    mfe_R: float
    minutes_held: int
    sweep_level: float
    sweep_extreme: float
    ref_high: float
    ref_low: float
    sep_param: float
    target_R_param: float
    conf_tf: str
    close_tol: float


def session_date_for_ny(ts: pd.Timestamp) -> date:
    d = ts.date()
    if ts.hour >= 18:
        return d + timedelta(days=1)
    return d


def assign_split(y: int) -> str:
    if y in IS_YEARS:
        return "IS"
    if y in VAL_YEARS:
        return "Validation"
    if y in OOS_YEARS:
        return "OOS"
    return "OTHER"


def load_instrument(symbol: str = "NQ") -> pd.DataFrame:
    symbol = symbol.upper()
    path = {
        "NQ": DATA / "nq_1m_continuous.parquet",
        "ES": DATA / "es_1m_continuous.parquet",
    }.get(symbol)
    if path is None or not path.exists():
        raise FileNotFoundError(f"No continuous parquet for {symbol}: {path}")
    df = pd.read_parquet(path)
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert("America/New_York")
    out = pd.DataFrame(
        {
            "ts": ts,
            "open": df["open"].to_numpy(np.float64),
            "high": df["high"].to_numpy(np.float64),
            "low": df["low"].to_numpy(np.float64),
            "close": df["close"].to_numpy(np.float64),
            "volume": df["volume"].to_numpy(np.int64),
        }
    )
    out["year"] = out["ts"].dt.year.astype(np.int16)
    out["hour"] = out["ts"].dt.hour.astype(np.int8)
    out["minute"] = out["ts"].dt.minute.astype(np.int8)
    out["ny_min"] = (out["hour"].astype(np.int16) * 60 + out["minute"].astype(np.int16))
    cal = out["ts"].dt.date
    # session date: if hour>=18 -> next calendar day
    out["session_date"] = np.where(
        out["hour"].to_numpy() >= 18,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    return out


def load_nq() -> pd.DataFrame:
    return load_instrument("NQ")


def build_daily(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("session_date", sort=True)
    daily = g.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        n_bars=("close", "size"),
        year=("year", "last"),
    ).reset_index()
    daily = daily[daily["n_bars"] >= 200].reset_index(drop=True)
    return daily


def build_relevant_swings(daily: pd.DataFrame, sep: float) -> dict[date, dict[str, Any]]:
    """
    For each session date S, return active relevant high/low and manipulation state
    using only information available BEFORE S opens (completed days < S).
    """
    dates = daily["session_date"].tolist()
    H = daily["high"].to_numpy(np.float64)
    L = daily["low"].to_numpy(np.float64)
    C = daily["close"].to_numpy(np.float64)
    n = len(daily)

    # Confirmed pivots at index i when i+1 exists
    pivot_hi = []  # (idx, price, is_failure)
    pivot_lo = []
    last_hi_price = None
    last_lo_price = None
    retained_hi = []  # list of dicts
    retained_lo = []

    for i in range(1, n - 1):
        is_ph = H[i] > H[i - 1] and H[i] > H[i + 1]
        is_pl = L[i] < L[i - 1] and L[i] < L[i + 1]
        # Confirmation time = close of day i+1 → available starting day i+2
        confirm_available_from = dates[i + 1]  # after day i+1 completes, known at start of next
        # We will attach pivots with available_from = dates[i+2] if exists else None
        avail = dates[i + 2] if (i + 2) < n else None

        if is_ph and avail is not None:
            fail = last_hi_price is not None and H[i] < last_hi_price
            if last_hi_price is None or abs(H[i] - last_hi_price) >= sep:
                retained_hi.append(
                    {
                        "idx": i,
                        "date": dates[i],
                        "price": float(H[i]),
                        "failure": bool(fail),
                        "available_from": avail,
                        "invalidated_on": None,
                        "manipulated_on": None,
                    }
                )
                last_hi_price = float(H[i])
                pivot_hi.append(i)
        if is_pl and avail is not None:
            fail = last_lo_price is not None and L[i] > last_lo_price
            if last_lo_price is None or abs(L[i] - last_lo_price) >= sep:
                retained_lo.append(
                    {
                        "idx": i,
                        "date": dates[i],
                        "price": float(L[i]),
                        "failure": bool(fail),
                        "available_from": avail,
                        "invalidated_on": None,
                        "manipulated_on": None,
                    }
                )
                last_lo_price = float(L[i])
                pivot_lo.append(i)

    # Also treat lookback window extremes as candidate levels if not already retained:
    # Per definitions: pivots within 30-day lookback. Retained list already chronological.

    # Process day-by-day manipulations / deep closes for causal state
    # Map: for each day index j, update swing invalidation/manipulation using day j's OHLC
    # State snapshot at start of day k uses updates through day k-1.

    state_at: dict[date, dict[str, Any]] = {}

    # Working copies
    highs = [dict(x) for x in retained_hi]
    lows = [dict(x) for x in retained_lo]

    date_to_i = {d: i for i, d in enumerate(dates)}

    for k, S in enumerate(dates):
        # Apply previous day's (k-1) OHLC effects before snapshot? 
        # Snapshot at start of S=dates[k] uses completed days < S, i.e. indices < k.
        # Pivot availability: swing available_from <= S
        # Manipulation/deep-close events on days m with m < S

        def active_levels(swings, side: str):
            # side 'high' or 'low'
            active = []
            for sw in swings:
                if sw["available_from"] is None or sw["available_from"] > S:
                    continue
                if sw["date"] >= S:
                    continue
                # deep-close invalidation on days after swing and before S
                inv = sw.get("invalidated_on")
                if inv is not None and inv < S:
                    continue
                # lookback 30 completed days
                si = date_to_i.get(sw["date"])
                if si is None or (k - 1 - si) > LOOKBACK_DAYS:
                    continue
                active.append(sw)
            return active

        # First, if k>=1, apply day k-1 events onto swings (mutate) — but we need
        # snapshots without mutating future. Better: recompute invalidation from scratch
        # for each S from raw OHLC (O(n^2) ok for ~4000 days).

        def compute_active(swings_src, is_high: bool):
            out = []
            for sw in swings_src:
                if sw["available_from"] is None or sw["available_from"] > S:
                    continue
                if sw["date"] >= S:
                    continue
                si = date_to_i[sw["date"]]
                if (k - 1 - si) > LOOKBACK_DAYS or (k - 1 - si) < 0:
                    continue
                price = sw["price"]
                manipulated_on = None
                invalidated_on = None
                for m in range(si + 1, k):  # days after swing, before S
                    if is_high:
                        if C[m] > price:
                            invalidated_on = dates[m]
                            break
                        if H[m] > price and C[m] < price:
                            manipulated_on = dates[m]  # keep latest
                    else:
                        if C[m] < price:
                            invalidated_on = dates[m]
                            break
                        if L[m] < price and C[m] > price:
                            manipulated_on = dates[m]
                if invalidated_on is not None:
                    continue
                out.append(
                    {
                        "date": sw["date"],
                        "price": price,
                        "failure": sw["failure"],
                        "manipulated_on": manipulated_on,
                    }
                )
            return out

        act_hi = compute_active(highs, True)
        act_lo = compute_active(lows, False)

        # Bias
        bull = False
        bear = False
        bull_m = None
        bear_m = None
        bull_L = None
        bear_H = None
        draw_H = None
        draw_L = None

        prior_close = float(C[k - 1]) if k >= 1 else None

        # Most recent manipulated active low
        cand_lo = [x for x in act_lo if x["manipulated_on"] is not None]
        cand_hi = [x for x in act_hi if x["manipulated_on"] is not None]
        if cand_lo and act_hi and prior_close is not None:
            # pick most recently manipulated low
            best = max(cand_lo, key=lambda x: x["manipulated_on"])
            # opposing draw high above prior close
            opp = [h for h in act_hi if h["price"] > prior_close]
            if opp:
                bull = True
                bull_m = best["manipulated_on"]
                bull_L = best["price"]
                draw_H = max(opp, key=lambda x: x["date"])["price"]

        if cand_hi and act_lo and prior_close is not None:
            best = max(cand_hi, key=lambda x: x["manipulated_on"])
            opp = [lo for lo in act_lo if lo["price"] < prior_close]
            if opp:
                bear = True
                bear_m = best["manipulated_on"]
                bear_H = best["price"]
                draw_L = min(opp, key=lambda x: x["date"])["price"]

        bias = "none"
        if bull and bear:
            if bull_m > bear_m:
                bias = "bull"
            elif bear_m > bull_m:
                bias = "bear"
            else:
                bias = "none"
        elif bull:
            bias = "bull"
        elif bear:
            bias = "bear"

        state_at[S] = {
            "bias": bias,
            "bull_L": bull_L,
            "bear_H": bear_H,
            "draw_H": draw_H,
            "draw_L": draw_L,
            "prior_close": prior_close,
            "prior_day_low": float(L[k - 1]) if k >= 1 else None,
            "prior_day_high": float(H[k - 1]) if k >= 1 else None,
            "n_act_hi": len(act_hi),
            "n_act_lo": len(act_lo),
        }

    return state_at


def window_mask(ny_min: np.ndarray, start_m: int, end_m: int, crosses_midnight: bool) -> np.ndarray:
    if crosses_midnight:
        return (ny_min >= start_m) | (ny_min < end_m)
    return (ny_min >= start_m) & (ny_min < end_m)


def simulate_trade(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    ts: np.ndarray,
    ny_min: np.ndarray,
    entry_i: int,
    direction: int,
    stop: float,
    target: float,
    fill: float,
    risk: float,
) -> dict[str, Any]:
    """Walk forward from entry bar; stop-first on ambiguous bars."""
    mae = 0.0
    mfe = 0.0
    gap_through = False
    ambiguous = False
    exit_i = entry_i
    exit_price = fill
    reason = "time_exit"

    n = len(o)
    for i in range(entry_i, n):
        if ny_min[i] >= 16 * 60:
            # time exit at open of 16:00 bar if we reach it without prior exit
            exit_i = i
            exit_price = float(o[i])
            reason = "time_exit"
            break

        # gap through stop at open
        if direction == 1:
            if o[i] <= stop:
                exit_i = i
                exit_price = float(o[i])
                gap_through = True
                reason = "gap_through_stop"
                break
            # intrabar
            hit_stop = l[i] <= stop
            hit_tgt = h[i] >= target
            mae = max(mae, fill - l[i])
            mfe = max(mfe, h[i] - fill)
            if hit_stop and hit_tgt:
                ambiguous = True
                exit_i = i
                exit_price = stop
                reason = "stop"
                break
            if hit_stop:
                exit_i = i
                exit_price = stop
                reason = "stop"
                break
            if hit_tgt:
                exit_i = i
                exit_price = target
                reason = "target"
                break
        else:
            if o[i] >= stop:
                exit_i = i
                exit_price = float(o[i])
                gap_through = True
                reason = "gap_through_stop"
                break
            hit_stop = h[i] >= stop
            hit_tgt = l[i] <= target
            mae = max(mae, h[i] - fill)
            mfe = max(mfe, fill - l[i])
            if hit_stop and hit_tgt:
                ambiguous = True
                exit_i = i
                exit_price = stop
                reason = "stop"
                break
            if hit_stop:
                exit_i = i
                exit_price = stop
                reason = "stop"
                break
            if hit_tgt:
                exit_i = i
                exit_price = target
                reason = "target"
                break
    else:
        exit_i = n - 1
        exit_price = float(c[n - 1])
        reason = "time_exit"

    raw = direction * (exit_price - fill)
    pnl = raw - COMMISSION_RT
    held = int((pd.Timestamp(ts[exit_i]) - pd.Timestamp(ts[entry_i])).total_seconds() // 60)
    return {
        "exit_i": exit_i,
        "exit_price": float(exit_price),
        "exit_ts": str(pd.Timestamp(ts[exit_i])),
        "pnl_points": float(pnl),
        "pnl_R": float(pnl / risk) if risk > 0 else 0.0,
        "exit_reason": reason,
        "ambiguous_bar": ambiguous,
        "gap_through_stop": gap_through,
        "mae": float(mae),
        "mfe": float(mfe),
        "mae_R": float(mae / risk) if risk > 0 else 0.0,
        "mfe_R": float(mfe / risk) if risk > 0 else 0.0,
        "minutes_held": held,
    }


def find_reference(o, h, l, c, start_i, end_i, direction: int):
    """Last opposing close candle in [start_i, end_i]; else sweep bar."""
    ref_i = start_i
    found = False
    for i in range(start_i, end_i + 1):
        if direction == 1 and c[i] < o[i]:
            ref_i = i
            found = True
        elif direction == -1 and c[i] > o[i]:
            ref_i = i
            found = True
    if not found:
        ref_i = start_i
    return ref_i


def run_backtest(
    df: pd.DataFrame,
    state_at: dict,
    sep: float = SWING_SEP,
    target_R: float = TARGET_R,
    conf_tf: str = "1m",
    close_tol: float = 0.0,
    years_filter: Optional[set[int]] = None,
) -> tuple[list[Trade], dict[str, Any]]:
    trades: list[Trade] = []
    forensics = {
        "blocked_gap_through_entry": 0,
        "skipped_tight_risk": 0,
        "skipped_no_bias": 0,
        "skipped_invalid_profile": 0,
        "skipped_no_trigger": 0,
        "days_total": 0,
        "days_with_bias": 0,
        "profile_counts": {"A": 0, "B": 0, "C": 0, "D": 0},
    }

    # Group indices by session_date
    sd = df["session_date"].to_numpy()
    # Build mapping date -> slice
    unique_dates = pd.unique(df["session_date"])
    # precompute start/end indices
    starts = {}
    ends = {}
    i0 = 0
    n = len(df)
    cur = sd[0]
    for i in range(1, n):
        if sd[i] != cur:
            starts[cur] = i0
            ends[cur] = i
            i0 = i
            cur = sd[i]
    starts[cur] = i0
    ends[cur] = n

    o_all = df["open"].to_numpy(np.float64)
    h_all = df["high"].to_numpy(np.float64)
    l_all = df["low"].to_numpy(np.float64)
    c_all = df["close"].to_numpy(np.float64)
    ts_all = df["ts"].to_numpy()
    ny_all = df["ny_min"].to_numpy(np.int16)
    yr_all = df["year"].to_numpy(np.int16)

    for S in unique_dates:
        if S not in state_at:
            continue
        st = state_at[S]
        y = S.year
        if years_filter is not None and y not in years_filter:
            continue
        forensics["days_total"] += 1
        bias = st["bias"]
        if bias == "none":
            forensics["skipped_no_bias"] += 1
            forensics["profile_counts"]["D"] += 1
            continue
        forensics["days_with_bias"] += 1

        a0, a1 = starts[S], ends[S]
        o = o_all[a0:a1]
        h = h_all[a0:a1]
        l = l_all[a0:a1]
        c = c_all[a0:a1]
        ts = ts_all[a0:a1]
        ny = ny_all[a0:a1]
        m = len(o)
        if m < 200:
            continue

        asia = (ny >= 18 * 60) | (ny < 1 * 60)
        lon = (ny >= 1 * 60) & (ny < 8 * 60)
        ny_sess = (ny >= 8 * 60) & (ny < 16 * 60)

        if asia.sum() < 30 or lon.sum() < 30:
            forensics["skipped_invalid_profile"] += 1
            forensics["profile_counts"]["D"] += 1
            continue

        asia_low = float(l[asia].min())
        asia_high = float(h[asia].max())
        asia_close = float(c[np.where(asia)[0][-1]])
        asia_idx = np.where(asia)[0]
        lon_low = float(l[lon].min())
        lon_high = float(h[lon].max())
        lon_close = float(c[np.where(lon)[0][-1]])
        lon_idx = np.where(lon)[0]

        pdl = st["prior_day_low"]
        pdh = st["prior_day_high"]
        if pdl is None or pdh is None:
            continue

        direction = 1 if bias == "bull" else -1
        profile = "D"
        sweep_level = None
        sweep_extreme = None
        confirm_i = None
        extreme_i = None

        if bias == "bull":
            # A: Asia reverses PDL
            if asia_low < (pdl - close_tol) and asia_close > (pdl + close_tol):
                profile = "A"
                sweep_level = pdl
                # extreme among asia bars that traded below pdl
                cand = asia_idx[l[asia_idx] < pdl]
                if len(cand) == 0:
                    cand = asia_idx
                extreme_i = int(cand[np.argmin(l[cand])])
                sweep_extreme = float(l[extreme_i])
                confirm_i = int(asia_idx[-1])
            # B: London reverses Asia low
            elif lon_low < (asia_low - close_tol) and lon_close > (asia_low + close_tol):
                profile = "B"
                sweep_level = asia_low
                cand = lon_idx[l[lon_idx] < asia_low]
                if len(cand) == 0:
                    cand = lon_idx
                extreme_i = int(cand[np.argmin(l[cand])])
                sweep_extreme = float(l[extreme_i])
                confirm_i = int(lon_idx[-1])
            else:
                # C: NY reverses overnight low
                onl = min(asia_low, lon_low)
                ny_idx = np.where(ny_sess)[0]
                confirmed = False
                for j in ny_idx:
                    if ny[j] > 15 * 60:
                        break
                    if l[j] < (onl - close_tol):
                        # track running extreme until confirm
                        pass
                # find first close back above after having taken onl
                taken = False
                run_ext_i = None
                run_ext = None
                for j in ny_idx:
                    if ny[j] > 15 * 60:
                        break
                    if l[j] < (onl - close_tol):
                        taken = True
                        if run_ext is None or l[j] < run_ext:
                            run_ext = float(l[j])
                            run_ext_i = j
                    if taken and c[j] > (onl + close_tol):
                        profile = "C"
                        sweep_level = onl
                        sweep_extreme = run_ext
                        extreme_i = int(run_ext_i)
                        confirm_i = int(j)
                        confirmed = True
                        break
                if not confirmed:
                    profile = "D"
        else:
            # bear
            if asia_high > (pdh + close_tol) and asia_close < (pdh - close_tol):
                profile = "A"
                sweep_level = pdh
                cand = asia_idx[h[asia_idx] > pdh]
                if len(cand) == 0:
                    cand = asia_idx
                extreme_i = int(cand[np.argmax(h[cand])])
                sweep_extreme = float(h[extreme_i])
                confirm_i = int(asia_idx[-1])
            elif lon_high > (asia_high + close_tol) and lon_close < (asia_high - close_tol):
                profile = "B"
                sweep_level = asia_high
                cand = lon_idx[h[lon_idx] > asia_high]
                if len(cand) == 0:
                    cand = lon_idx
                extreme_i = int(cand[np.argmax(h[cand])])
                sweep_extreme = float(h[extreme_i])
                confirm_i = int(lon_idx[-1])
            else:
                onh = max(asia_high, lon_high)
                ny_idx = np.where(ny_sess)[0]
                taken = False
                run_ext_i = None
                run_ext = None
                for j in ny_idx:
                    if ny[j] > 15 * 60:
                        break
                    if h[j] > (onh + close_tol):
                        taken = True
                        if run_ext is None or h[j] > run_ext:
                            run_ext = float(h[j])
                            run_ext_i = j
                    if taken and c[j] < (onh - close_tol):
                        profile = "C"
                        sweep_level = onh
                        sweep_extreme = run_ext
                        extreme_i = int(run_ext_i)
                        confirm_i = int(j)
                        break
                else:
                    profile = "D"

        forensics["profile_counts"][profile] += 1
        if profile == "D" or confirm_i is None or extreme_i is None:
            forensics["skipped_invalid_profile"] += 1
            continue

        # Reference candle
        lo_i = min(extreme_i, confirm_i)
        hi_i = max(extreme_i, confirm_i)
        ref_i = find_reference(o, h, l, c, lo_i, hi_i, direction)
        ref_high = float(h[ref_i])
        ref_low = float(l[ref_i])

        # 09:30 open feature
        m930 = np.where(ny == 9 * 60 + 30)[0]
        open_930 = float(o[m930[0]]) if len(m930) else float("nan")

        # Trigger search after confirm_i
        signal_i = None
        if conf_tf == "1m":
            for j in range(confirm_i + 1, m):
                if ny[j] > 14 * 60 + 59:
                    break
                if not ((ny[j] >= 8 * 60) or profile in ("A", "B")):
                    # entries only in NY cash hours for continuation; allow from confirm onward if confirm in NY
                    if ny[j] < 8 * 60:
                        continue
                if ny[j] < 8 * 60:
                    continue
                if direction == 1 and c[j] > ref_high:
                    signal_i = j
                    break
                if direction == -1 and c[j] < ref_low:
                    signal_i = j
                    break
        else:
            # 5m confirmation: aggregate closes
            # Build 5m buckets from confirm
            j = confirm_i + 1
            while j < m:
                if ny[j] > 14 * 60 + 59:
                    break
                if ny[j] < 8 * 60:
                    j += 1
                    continue
                # end of 5m bucket
                bucket_end = j
                base = ny[j] // 5 * 5
                while bucket_end + 1 < m and (ny[bucket_end + 1] // 5 * 5) == base and ny[bucket_end + 1] < 16 * 60:
                    bucket_end += 1
                # 5m OHLC
                c5 = c[bucket_end]
                if direction == 1 and c5 > ref_high:
                    signal_i = bucket_end
                    break
                if direction == -1 and c5 < ref_low:
                    signal_i = bucket_end
                    break
                j = bucket_end + 1

        if signal_i is None or signal_i + 1 >= m:
            forensics["skipped_no_trigger"] += 1
            continue

        entry_i = signal_i + 1
        if ny[entry_i] > 15 * 60:
            forensics["skipped_no_trigger"] += 1
            continue

        raw_open = float(o[entry_i])
        if direction == 1:
            fill = raw_open + SLIPPAGE
            stop = float(sweep_extreme) - STOP_BUFFER
            if fill <= stop:
                forensics["blocked_gap_through_entry"] += 1
                continue
            risk = fill - stop
            target = fill + target_R * risk
        else:
            fill = raw_open - SLIPPAGE
            stop = float(sweep_extreme) + STOP_BUFFER
            if fill >= stop:
                forensics["blocked_gap_through_entry"] += 1
                continue
            risk = stop - fill
            target = fill - target_R * risk

        if risk < MIN_RISK:
            forensics["skipped_tight_risk"] += 1
            continue

        sim = simulate_trade(o, h, l, c, ts, ny, entry_i, direction, stop, target, fill, risk)

        entry_vs_930 = (fill - open_930) * direction if not math.isnan(open_930) else float("nan")

        trades.append(
            Trade(
                session_date=str(S),
                year=int(y),
                split=assign_split(int(y)),
                direction=direction,
                bias=bias,
                profile=profile,
                signal_ts=str(pd.Timestamp(ts[signal_i])),
                entry_ts=str(pd.Timestamp(ts[entry_i])),
                exit_ts=sim["exit_ts"],
                entry=float(fill),
                stop=float(stop),
                target=float(target),
                risk=float(risk),
                exit_price=sim["exit_price"],
                pnl_points=sim["pnl_points"],
                pnl_R=sim["pnl_R"],
                exit_reason=sim["exit_reason"],
                ambiguous_bar=sim["ambiguous_bar"],
                gap_through_stop=sim["gap_through_stop"],
                blocked=False,
                open_930=open_930,
                entry_vs_930=entry_vs_930,
                mae=sim["mae"],
                mfe=sim["mfe"],
                mae_R=sim["mae_R"],
                mfe_R=sim["mfe_R"],
                minutes_held=sim["minutes_held"],
                sweep_level=float(sweep_level),
                sweep_extreme=float(sweep_extreme),
                ref_high=ref_high,
                ref_low=ref_low,
                sep_param=float(sep),
                target_R_param=float(target_R),
                conf_tf=conf_tf,
                close_tol=float(close_tol),
            )
        )

    return trades, forensics


def max_losing_streak(pnls: np.ndarray) -> int:
    streak = 0
    mx = 0
    for x in pnls:
        if x < 0:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
    return mx


def max_drawdown(pnls: np.ndarray) -> float:
    if len(pnls) == 0:
        return 0.0
    eq = np.cumsum(pnls)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    return float(dd.min()) if len(dd) else 0.0


def summarize_trades(trades: list[Trade], label: str) -> dict[str, Any]:
    if not trades:
        return {
            "split": label,
            "N": 0,
            "win_rate": None,
            "profit_factor": None,
            "expectancy": None,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "avg_win": None,
            "avg_loss": None,
            "median_R": None,
            "largest_win": None,
            "largest_loss": None,
            "max_losing_streak": 0,
            "ambiguous_bars": 0,
            "gap_through_stops": 0,
            "avg_risk": None,
            "median_risk": None,
            "p90_risk": None,
            "avg_mae_R": None,
            "avg_mfe_R": None,
            "avg_minutes_held": None,
            "exit_reasons": {},
            "profile_counts": {},
        }

    pnls = np.array([t.pnl_points for t in trades], dtype=np.float64)
    Rs = np.array([t.pnl_R for t in trades], dtype=np.float64)
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]
    gp = float(wins.sum()) if len(wins) else 0.0
    gl = float(-losses.sum()) if len(losses) else 0.0
    pf = (gp / gl) if gl > 1e-12 else (999.0 if gp > 0 else 0.0)
    risks = np.array([t.risk for t in trades], dtype=np.float64)
    exit_reasons: dict[str, int] = {}
    profiles: dict[str, int] = {}
    for t in trades:
        exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1
        profiles[t.profile] = profiles.get(t.profile, 0) + 1

    return {
        "split": label,
        "N": len(trades),
        "win_rate": float((pnls > 0).mean()),
        "profit_factor": float(pf),
        "expectancy": float(pnls.mean()),
        "total_pnl": float(pnls.sum()),
        "max_drawdown": max_drawdown(pnls),
        "avg_win": float(wins.mean()) if len(wins) else None,
        "avg_loss": float(losses.mean()) if len(losses) else None,
        "median_R": float(np.median(Rs)),
        "largest_win": float(pnls.max()),
        "largest_loss": float(pnls.min()),
        "max_losing_streak": max_losing_streak(pnls),
        "ambiguous_bars": int(sum(1 for t in trades if t.ambiguous_bar)),
        "gap_through_stops": int(sum(1 for t in trades if t.gap_through_stop)),
        "avg_risk": float(risks.mean()),
        "median_risk": float(np.median(risks)),
        "p90_risk": float(np.percentile(risks, 90)),
        "avg_mae_R": float(np.mean([t.mae_R for t in trades])),
        "avg_mfe_R": float(np.mean([t.mfe_R for t in trades])),
        "avg_minutes_to_target": float(
            np.mean([t.minutes_held for t in trades if t.exit_reason == "target"])
        )
        if any(t.exit_reason == "target" for t in trades)
        else None,
        "avg_minutes_to_stop": float(
            np.mean([t.minutes_held for t in trades if t.exit_reason == "stop"])
        )
        if any(t.exit_reason == "stop" for t in trades)
        else None,
        "avg_minutes_held": float(np.mean([t.minutes_held for t in trades])),
        "exit_reasons": exit_reasons,
        "profile_counts": profiles,
    }


def yearly_table(trades: list[Trade]) -> pd.DataFrame:
    rows = []
    by = {}
    for t in trades:
        by.setdefault(t.year, []).append(t)
    for y in sorted(by):
        s = summarize_trades(by[y], str(y))
        rows.append(
            {
                "year": y,
                "split": assign_split(y),
                "N": s["N"],
                "win_rate": s["win_rate"],
                "profit_factor": s["profit_factor"],
                "expectancy": s["expectancy"],
                "total_pnl": s["total_pnl"],
                "max_drawdown": s["max_drawdown"],
                "median_R": s["median_R"],
            }
        )
    return pd.DataFrame(rows)


def monthly_table(trades: list[Trade]) -> pd.DataFrame:
    rows = []
    by = {}
    for t in trades:
        key = t.session_date[:7]
        by.setdefault(key, []).append(t)
    for k in sorted(by):
        s = summarize_trades(by[k], k)
        pnls = np.array([t.pnl_points for t in by[k]])
        rows.append(
            {
                "month": k,
                "N": s["N"],
                "win_rate": s["win_rate"],
                "profit_factor": s["profit_factor"],
                "expectancy": s["expectancy"],
                "total_pnl": s["total_pnl"],
                "profitable": bool(pnls.sum() > 0),
            }
        )
    return pd.DataFrame(rows)


def positive_edge(summary: dict) -> bool:
    if summary["N"] == 0:
        return False
    pf = summary["profit_factor"]
    exp = summary["expectancy"]
    return pf is not None and exp is not None and pf > 1.0 and exp > 0


def main(symbol: str = "NQ", out_prefix: str | None = None):
    symbol = symbol.upper()
    prefix = out_prefix or ("am_trades" if symbol == "NQ" else f"am_trades_{symbol.lower()}")
    print(f"Loading {symbol} 1m...", flush=True)
    df = load_instrument(symbol)
    print(f"Bars: {len(df):,}  {df['ts'].min()} -> {df['ts'].max()}", flush=True)

    print("Building daily candles...", flush=True)
    daily = build_daily(df)
    print(f"Daily bars: {len(daily)}", flush=True)

    print("Building causal relevant swings / bias (sep=40)...", flush=True)
    state_at = build_relevant_swings(daily, SWING_SEP)
    bias_counts = pd.Series([state_at[d]["bias"] for d in state_at]).value_counts().to_dict()
    print(f"Bias counts: {bias_counts}", flush=True)

    print("Running PRIMARY backtest (2R, 1m, sep=40, tol=0)...", flush=True)
    trades, forensics = run_backtest(df, state_at, SWING_SEP, TARGET_R, "1m", 0.0)
    print(f"Trades: {len(trades)}  forensics: {forensics}", flush=True)

    # Split summaries
    by_split = {"IS": [], "Validation": [], "OOS": []}
    for t in trades:
        if t.split in by_split:
            by_split[t.split].append(t)

    summaries = {
        "IS": summarize_trades(by_split["IS"], "IS"),
        "Validation": summarize_trades(by_split["Validation"], "Validation"),
        "OOS": summarize_trades(by_split["OOS"], "OOS"),
        "ALL": summarize_trades(trades, "ALL"),
    }
    for k, s in summaries.items():
        print(
            f"{k}: N={s['N']} WR={s['win_rate']} PF={s['profit_factor']} "
            f"E={s['expectancy']} PnL={s['total_pnl']} DD={s['max_drawdown']}",
            flush=True,
        )

    # Robustness only if IS and Validation positive
    robustness = []
    run_robustness = positive_edge(summaries["IS"]) and positive_edge(summaries["Validation"])
    print(f"IS+Val positive? {run_robustness} -> robustness={'YES' if run_robustness else 'SKIP'}", flush=True)

    if run_robustness:
        for sep in (30.0, 40.0, 50.0):
            st = state_at if sep == SWING_SEP else build_relevant_swings(daily, sep)
            for conf in ("1m", "5m"):
                for tr in (1.5, 2.0, 2.5, 3.0):
                    for tol in (0.0, 0.25):
                        if sep == SWING_SEP and conf == "1m" and tr == TARGET_R and tol == 0.0:
                            # reuse primary split metrics for this cell
                            pass
                        t2, _ = run_backtest(df, st, sep, tr, conf, tol)
                        for split_name in ("IS", "Validation", "OOS"):
                            sub = [x for x in t2 if x.split == split_name]
                            s = summarize_trades(sub, split_name)
                            robustness.append(
                                {
                                    "sep": sep,
                                    "conf_tf": conf,
                                    "target_R": tr,
                                    "close_tol": tol,
                                    "split": split_name,
                                    "N": s["N"],
                                    "win_rate": s["win_rate"],
                                    "profit_factor": s["profit_factor"],
                                    "expectancy": s["expectancy"],
                                    "total_pnl": s["total_pnl"],
                                }
                            )
                        print(
                            f"  rob sep={sep} conf={conf} R={tr} tol={tol} "
                            f"IS_PF={summarize_trades([x for x in t2 if x.split=='IS'],'IS')['profit_factor']} "
                            f"Val_PF={summarize_trades([x for x in t2 if x.split=='Validation'],'V')['profit_factor']} "
                            f"OOS_PF={summarize_trades([x for x in t2 if x.split=='OOS'],'O')['profit_factor']}",
                            flush=True,
                        )

    # 09:30 feature analysis (not a filter) on primary
    open930_analysis = {}
    for split_name, subset in by_split.items():
        if not subset:
            open930_analysis[split_name] = {}
            continue
        aligned = [t for t in subset if not math.isnan(t.entry_vs_930) and t.entry_vs_930 > 0]
        opposed = [t for t in subset if not math.isnan(t.entry_vs_930) and t.entry_vs_930 <= 0]
        open930_analysis[split_name] = {
            "aligned_with_930": summarize_trades(aligned, "aligned"),
            "opposed_to_930": summarize_trades(opposed, "opposed"),
        }

    # SMT secondary ONLY if core demonstrates edge on IS + Validation + OOS
    smt_result = {
        "ran": False,
        "reason": "Core failed IS and/or Validation — SMT not permitted to rescue",
    }
    if (
        positive_edge(summaries["IS"])
        and positive_edge(summaries["Validation"])
        and positive_edge(summaries["OOS"])
    ):
        try:
            smt_result = run_smt_secondary(df, state_at, trades)
        except Exception as e:
            smt_result = {"ran": False, "error": str(e)}
    elif positive_edge(summaries["OOS"]) and not (
        positive_edge(summaries["IS"]) and positive_edge(summaries["Validation"])
    ):
        smt_result = {
            "ran": False,
            "reason": (
                "OOS alone not sufficient: IS/Validation failed under frozen rules; "
                "SMT secondary blocked per no-rescue protocol"
            ),
        }

    # Verdict
    verdict, why = classify_verdict(summaries, forensics, run_robustness, robustness)

    # Persist
    trades_df = pd.DataFrame([asdict(t) for t in trades])
    trades_df.to_csv(art(f"{prefix}_trades.csv"), index=False)
    yearly_table(trades).to_csv(art(f"{prefix}_yearly.csv"), index=False)
    monthly_table(trades).to_csv(art(f"{prefix}_monthly.csv"), index=False)

    summary_rows = [summaries["IS"], summaries["Validation"], summaries["OOS"], summaries["ALL"]]
    pd.DataFrame(summary_rows).to_csv(art(f"{prefix}_summary.csv"), index=False)

    report = {
        "hypothesis": f"AM Trades NY continuation on {symbol} (no SMT/VWAP/ORB)",
        "symbol": symbol,
        "definitions": "artifacts/am_trades_definitions.md",
        "frozen_params": {
            "lookback_days": LOOKBACK_DAYS,
            "swing_sep": SWING_SEP,
            "slippage": SLIPPAGE,
            "commission_rt": COMMISSION_RT,
            "stop_buffer": STOP_BUFFER,
            "target_R": TARGET_R,
            "min_risk": MIN_RISK,
            "conf_tf": "1m",
            "close_tol": 0.0,
            "note": "Identical absolute point params as NQ freeze (not volatility-scaled)",
        },
        "bias_counts": bias_counts,
        "forensics": forensics,
        "summaries": summaries,
        "open930_analysis": {
            k: {
                "aligned": {kk: vv for kk, vv in v.get("aligned_with_930", {}).items() if kk in ("N", "win_rate", "profit_factor", "expectancy", "total_pnl")},
                "opposed": {kk: vv for kk, vv in v.get("opposed_to_930", {}).items() if kk in ("N", "win_rate", "profit_factor", "expectancy", "total_pnl")},
            }
            for k, v in open930_analysis.items()
        },
        "robustness_ran": run_robustness,
        "robustness": robustness,
        "smt": smt_result,
        "verdict": verdict,
        "verdict_reason": why,
        "failure_checks": {
            "oos_pf_lt_1": (summaries["OOS"]["profit_factor"] or 0) < 1.0,
            "oos_expectancy_le_0": (summaries["OOS"]["expectancy"] or 0) <= 0,
            "is_val_positive": run_robustness,
        },
    }

    with open(art(f"{prefix}_forensic_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n=== VERDICT ===", flush=True)
    print(verdict, flush=True)
    print(why, flush=True)
    print(f"Saved artifacts/{prefix}_*", flush=True)
    return report


def classify_verdict(summaries, forensics, ran_rob, robustness):
    is_ok = positive_edge(summaries["IS"])
    val_ok = positive_edge(summaries["Validation"])
    oos = summaries["OOS"]
    oos_ok = positive_edge(oos)

    # Artifact check: tiny N or extreme gap dominance
    if oos["N"] and oos["N"] < 20:
        return "B", (
            f"Sample too small on OOS (N={oos['N']}). "
            f"IS_ok={is_ok} Val_ok={val_ok} OOS_PF={oos['profit_factor']} OOS_E={oos['expectancy']}."
        )

    if forensics.get("blocked_gap_through_entry", 0) > max(1, int(0.5 * (summaries["ALL"]["N"] or 1))):
        return "D", "Majority of signals blocked by gap-through at entry — results dominated by execution/data artifacts."

    if not is_ok and not val_ok:
        return "C", (
            f"No edge on IS or Validation under frozen execution rules. "
            f"IS PF={summaries['IS']['profit_factor']} E={summaries['IS']['expectancy']}; "
            f"Val PF={summaries['Validation']['profit_factor']} E={summaries['Validation']['expectancy']}. "
            f"Hypothesis FAILED — no optimization attempted."
        )

    if is_ok and val_ok and not oos_ok:
        return "C", (
            f"IS and Validation looked positive but OOS failed "
            f"(PF={oos['profit_factor']}, E={oos['expectancy']}, N={oos['N']}). "
            f"Per failure conditions: FAILED — do not optimize."
        )

    if is_ok and val_ok and oos_ok:
        # Check broad region if robustness ran
        if ran_rob and robustness:
            cells = [r for r in robustness if r["split"] == "OOS"]
            good = [r for r in cells if r["profit_factor"] and r["expectancy"] and r["profit_factor"] > 1 and r["expectancy"] > 0]
            frac = len(good) / max(len(cells), 1)
            if frac >= 0.5:
                return "A", (
                    f"Positive IS, Validation, and OOS with broad robustness "
                    f"({len(good)}/{len(cells)} OOS cells profitable). "
                    f"OOS PF={oos['profit_factor']} E={oos['expectancy']} N={oos['N']}."
                )
            return "B", (
                f"Primary OOS positive but robustness region not broad "
                f"({len(good)}/{len(cells)} OOS cells). "
                f"OOS PF={oos['profit_factor']} E={oos['expectancy']}."
            )
        return "B", (
            f"Primary IS/Val/OOS positive but robustness not established. "
            f"OOS PF={oos['profit_factor']} E={oos['expectancy']} N={oos['N']}."
        )

    # Mixed: e.g. IS ok Val fail
    return "C", (
        f"No consistent edge across IS and Validation. "
        f"IS_ok={is_ok} Val_ok={val_ok} OOS_ok={oos_ok}. "
        f"IS PF={summaries['IS']['profit_factor']} Val PF={summaries['Validation']['profit_factor']} "
        f"OOS PF={oos['profit_factor']}."
    )


def run_smt_secondary(df_nq, state_at, core_trades):
    """NQ/ES SMT filter at sweep — only called if OOS core is positive."""
    es = pd.read_parquet(DATA / "es_1m_continuous.parquet")
    ts = pd.to_datetime(es["ts_event"], utc=True).dt.tz_convert("America/New_York")
    es = pd.DataFrame({"ts": ts, "high": es["high"], "low": es["low"]})
    # Align on timestamp
    nq = df_nq[["ts", "high", "low"]].rename(columns={"high": "high_nq", "low": "low_nq"})
    m = pd.merge(nq, es, on="ts", how="inner")
    m["session_date"] = [session_date_for_ny(t) for t in m["ts"]]

    # For each core trade, check SMT at sweep window: bullish SMT = ES fails to make lower low vs its prior session extreme proxy
    # Pre-committed: within the 60 minutes ending at entry, NQ makes the sweep extreme while ES low > ES rolling 60m prior low (divergence)
    smt_keep = []
    core_keep_idx = []
    for i, t in enumerate(core_trades):
        S = date.fromisoformat(t.session_date)
        day = m[m["session_date"] == S]
        if day.empty:
            continue
        entry_ts = pd.Timestamp(t.entry_ts)
        if entry_ts.tzinfo is None:
            entry_ts = entry_ts.tz_localize("America/New_York")
        window = day[(day["ts"] <= entry_ts) & (day["ts"] >= entry_ts - pd.Timedelta(minutes=120))]
        if len(window) < 30:
            continue
        if t.direction == 1:
            # SMT long: NQ took a lower low vs first half; ES did not
            mid = len(window) // 2
            nq1 = window["low_nq"].iloc[:mid].min()
            nq2 = window["low_nq"].iloc[mid:].min()
            es1 = window["low"].iloc[:mid].min()
            es2 = window["low"].iloc[mid:].min()
            smt = (nq2 < nq1) and (es2 >= es1)
        else:
            mid = len(window) // 2
            nq1 = window["high_nq"].iloc[:mid].max()
            nq2 = window["high_nq"].iloc[mid:].max()
            es1 = window["high"].iloc[:mid].max()
            es2 = window["high"].iloc[mid:].max()
            smt = (nq2 > nq1) and (es2 <= es1)
        if smt:
            smt_keep.append(t)
            core_keep_idx.append(i)

    core_oos = [t for t in core_trades if t.split == "OOS"]
    smt_oos = [t for t in smt_keep if t.split == "OOS"]
    return {
        "ran": True,
        "definition": "120m pre-entry half-split: NQ makes new extreme in 2nd half, ES does not",
        "core": {
            "ALL": summarize_trades(core_trades, "core"),
            "OOS": summarize_trades(core_oos, "core_oos"),
        },
        "core_plus_smt": {
            "ALL": summarize_trades(smt_keep, "smt"),
            "OOS": summarize_trades(smt_oos, "smt_oos"),
            "N_filtered": len(smt_keep),
        },
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NQ", choices=["NQ", "ES", "nq", "es"])
    ap.add_argument("--out-prefix", default=None)
    args = ap.parse_args()
    main(symbol=args.symbol, out_prefix=args.out_prefix)
