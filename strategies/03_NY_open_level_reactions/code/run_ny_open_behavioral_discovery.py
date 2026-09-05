"""
NQ NY Open — Behavioral Discovery & Strategy Research
Hostile / causal: facts first, then hypotheses, then optional strategy.

No lookahead. Thresholds frozen from IS (2010-2021) only.
No parameter search on Validation/OOS.
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
import warnings
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

from common.paths import art, ART, DATA, ROOT

# --- Frozen research constants (NOT optimized on OOS) ---
# Impulse "large" = top tercile of |impulse|/ONR on IS only (computed once).
# Pullback "controlled" = retrace between 25% and 62% of impulse size.
# Level "acceptance" = close beyond level by >= 0.15 * ONR within 10m after first touch.
# Level "rejection" = return through level within 10m after first touch.
ACCEPT_FRAC = 0.15
PULLBACK_LO = 0.25
PULLBACK_HI = 0.62
IMPULSE_WINDOW_M = 10  # minutes after 09:30 to measure first impulse
FORWARD_HORIZONS = (5, 10, 15, 20, 30)
SLIPPAGE = 0.50  # points per side (realistic NQ)
COMMISSION_RT = 0.50  # round-turn points equivalent (~$10 / NQ at $20/pt = 0.5pt)
TICK = 0.25
STOP_R = 1.0
TARGET_R = 1.5
MAX_HOLD_M = 60

IS_YEARS = set(range(2010, 2022))
VAL_YEARS = {2022, 2023, 2024}
OOS_YEARS = {2025, 2026}

NY_OPEN = 9 * 60 + 30  # 570
RTH_END = 16 * 60  # 960
SESSION_START = 18 * 60  # 1080


def assign_split(y: int) -> str:
    if y in IS_YEARS:
        return "IS"
    if y in VAL_YEARS:
        return "Validation"
    if y in OOS_YEARS:
        return "OOS"
    return "OTHER"


def load_nq() -> pd.DataFrame:
    df = pd.read_parquet(DATA / "nq_1m_continuous.parquet")
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
    out["dow"] = out["ts"].dt.dayofweek.astype(np.int8)  # Mon=0
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    cal = out["ts"].dt.date
    out["session_date"] = np.where(
        out["ny_min"].to_numpy() >= SESSION_START,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    return out


def build_session_frames(df: pd.DataFrame) -> dict[date, pd.DataFrame]:
    """Index bars by session_date for fast day lookup."""
    frames: dict[date, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=True):
        frames[sd] = g.reset_index(drop=True)
    return frames


@dataclass
class DayFacts:
    session_date: date
    year: int
    dow: int
    split: str
    # overnight
    onh: float
    onl: float
    onr: float
    on_bars: int
    open_930: float
    open_loc_onr: float  # (open-ONL)/ONR
    # prior day (completed session)
    pdh: float
    pdl: float
    pdc: float
    pdr: float
    gap_pts: float
    gap_onr: float
    # opening moves (causal at end of window)
    move_1m: float
    move_5m: float
    move_10m: float
    range_1m: float
    range_5m: float
    range_10m: float
    range_30m: float
    # first impulse in IMPULSE_WINDOW_M
    impulse_dir: int  # +1/-1 from net move to window end; 0 if flat
    impulse_ext: float  # max favorable excursion from open in impulse dir within window
    impulse_ext_onr: float
    impulse_end_min: int  # minute offset of extreme within window
    # pullback after impulse extreme (within next 20m after extreme, still before 11:00)
    pullback_depth: float
    pullback_frac: float
    pullback_end_min: int
    cont_after_pb: float  # move in impulse dir from pb extreme to +15m after pb
    # vol regime proxy known pre-open: median ONR of prior 20 sessions
    onr_med20: float
    onr_vs_med: float
    # ATR20 from prior completed day ranges
    atr20: float


def compute_day_facts(frames: dict[date, pd.DataFrame], sessions: list[date]) -> list[DayFacts]:
    results: list[DayFacts] = []
    onr_hist: list[float] = []
    day_range_hist: list[float] = []

    for i, sd in enumerate(sessions):
        g = frames[sd]
        # require 09:30 bar
        open_rows = g[g["ny_min"] == NY_OPEN]
        if len(open_rows) == 0:
            continue
        # overnight: bars with ny_min < 09:30 (includes 18:00-23:59 and 00:00-09:29)
        on = g[g["ny_min"] < NY_OPEN]
        if len(on) < 30:
            continue
        onh = float(on["high"].max())
        onl = float(on["low"].min())
        onr = onh - onl
        if onr < 1.0:
            continue

        o930 = float(open_rows.iloc[0]["open"])
        year = int(open_rows.iloc[0]["year"])
        dow = int(open_rows.iloc[0]["dow"])

        # prior completed session
        if i == 0:
            continue
        prev_sd = sessions[i - 1]
        # find previous session that exists in frames with enough bars
        j = i - 1
        prev_g = None
        while j >= 0:
            cand = frames.get(sessions[j])
            if cand is not None and len(cand) >= 200:
                prev_g = cand
                prev_sd = sessions[j]
                break
            j -= 1
        if prev_g is None:
            continue

        pdh = float(prev_g["high"].max())
        pdl = float(prev_g["low"].min())
        pdc = float(prev_g.iloc[-1]["close"])
        pdr = pdh - pdl
        if pdr < 1.0:
            continue

        gap = o930 - pdc

        # RTH window bars for opening measures
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 11 * 60)].reset_index(drop=True)
        if len(rth) < 60:
            continue

        def move_at(m: int) -> tuple[float, float]:
            sub = rth[rth["ny_min"] < NY_OPEN + m]
            if len(sub) == 0:
                return np.nan, np.nan
            last = float(sub.iloc[-1]["close"])
            rng = float(sub["high"].max() - sub["low"].min())
            return last - o930, rng

        m1, r1 = move_at(1)
        m5, r5 = move_at(5)
        m10, r10 = move_at(10)
        _, r30 = move_at(30)

        # First impulse: within first IMPULSE_WINDOW_M minutes
        win = rth[rth["ny_min"] < NY_OPEN + IMPULSE_WINDOW_M]
        if len(win) < IMPULSE_WINDOW_M // 2:
            continue
        net = float(win.iloc[-1]["close"] - o930)
        if abs(net) < TICK:
            impulse_dir = 0
        else:
            impulse_dir = 1 if net > 0 else -1

        if impulse_dir == 1:
            # max high relative to open
            ext_idx = int(win["high"].values.argmax())
            impulse_ext = float(win["high"].iloc[ext_idx] - o930)
        elif impulse_dir == -1:
            ext_idx = int(win["low"].values.argmin())
            impulse_ext = float(o930 - win["low"].iloc[ext_idx])
        else:
            ext_idx = len(win) - 1
            impulse_ext = 0.0

        impulse_end_min = int(win.iloc[ext_idx]["ny_min"] - NY_OPEN)

        # Pullback after impulse extreme: next 20 minutes
        after = rth[rth["ny_min"] > int(win.iloc[ext_idx]["ny_min"])].head(20)
        if len(after) < 5 or impulse_dir == 0 or impulse_ext < TICK:
            pullback_depth = np.nan
            pullback_frac = np.nan
            pullback_end_min = -1
            cont_after_pb = np.nan
        else:
            if impulse_dir == 1:
                pb_idx = int(after["low"].values.argmin())
                pb_price = float(after["low"].iloc[pb_idx])
                impulse_extreme = float(win["high"].iloc[ext_idx])
                pullback_depth = impulse_extreme - pb_price
            else:
                pb_idx = int(after["high"].values.argmax())
                pb_price = float(after["high"].iloc[pb_idx])
                impulse_extreme = float(win["low"].iloc[ext_idx])
                pullback_depth = pb_price - impulse_extreme
            pullback_frac = pullback_depth / impulse_ext if impulse_ext > 0 else np.nan
            pullback_end_min = int(after.iloc[pb_idx]["ny_min"] - NY_OPEN)
            # continuation: from pb extreme to +15m close after pb
            pb_ny = int(after.iloc[pb_idx]["ny_min"])
            fwd = rth[(rth["ny_min"] > pb_ny) & (rth["ny_min"] <= pb_ny + 15)]
            if len(fwd) == 0:
                cont_after_pb = np.nan
            else:
                end_px = float(fwd.iloc[-1]["close"])
                cont_after_pb = (end_px - pb_price) * impulse_dir

        # vol regime: median ONR prior 20 available
        onr_med20 = float(np.median(onr_hist[-20:])) if len(onr_hist) >= 5 else np.nan
        atr20 = float(np.mean(day_range_hist[-20:])) if len(day_range_hist) >= 5 else np.nan

        facts = DayFacts(
            session_date=sd,
            year=year,
            dow=dow,
            split=assign_split(year),
            onh=onh,
            onl=onl,
            onr=onr,
            on_bars=len(on),
            open_930=o930,
            open_loc_onr=(o930 - onl) / onr,
            pdh=pdh,
            pdl=pdl,
            pdc=pdc,
            pdr=pdr,
            gap_pts=gap,
            gap_onr=gap / onr,
            move_1m=m1,
            move_5m=m5,
            move_10m=m10,
            range_1m=r1,
            range_5m=r5,
            range_10m=r10,
            range_30m=r30,
            impulse_dir=impulse_dir,
            impulse_ext=impulse_ext,
            impulse_ext_onr=impulse_ext / onr,
            impulse_end_min=impulse_end_min,
            pullback_depth=pullback_depth,
            pullback_frac=pullback_frac,
            pullback_end_min=pullback_end_min,
            cont_after_pb=cont_after_pb,
            onr_med20=onr_med20,
            onr_vs_med=(onr / onr_med20) if onr_med20 and onr_med20 > 0 else np.nan,
            atr20=atr20,
        )
        results.append(facts)

        # update histories AFTER day completes conceptually — for next day we need
        # overnight of THIS day known at next open, and full day range after close.
        # ONR for today is known at 09:30, so we can append now for next day's med20.
        onr_hist.append(onr)
        # day range uses full session — append previous day's already done; for ATR
        # use prior completed session range (pdr already from prev). Append today's
        # full range only after we finish — for next iteration use prev day's range.
        day_range_hist.append(pdr)

    return results


def facts_to_df(facts: list[DayFacts]) -> pd.DataFrame:
    rows = [f.__dict__.copy() for f in facts]
    df = pd.DataFrame(rows)
    df["session_date"] = df["session_date"].astype(str)
    return df


# ---------------------------------------------------------------------------
# Level interaction events (causal)
# ---------------------------------------------------------------------------

@dataclass
class LevelEvent:
    session_date: str
    year: int
    dow: int
    split: str
    level_name: str
    level: float
    direction: int  # +1 crossed up through level, -1 crossed down
    signal_ny_min: int
    decision_ts_offset: int  # minutes after 09:30 when cross confirmed (bar close)
    onr: float
    atr20: float
    # outcome classification within 10m after touch (using only post-touch bars)
    outcome: str  # accept / reject / inconclusive
    # forward returns from NEXT bar open after signal bar (executable)
    fwd: dict[int, float]
    mfe_30: float
    mae_30: float
    t_mfe: int
    t_mae: int


def detect_level_events(
    frames: dict[date, pd.DataFrame],
    day_df: pd.DataFrame,
) -> list[LevelEvent]:
    """First touch of ONH/ONL/PDH/PDL after 09:30, confirmed on bar close beyond level."""
    meta = {row["session_date"]: row for _, row in day_df.iterrows()}
    events: list[LevelEvent] = []

    for sd_str, row in meta.items():
        sd = date.fromisoformat(sd_str)
        g = frames.get(sd)
        if g is None:
            continue
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 11 * 60)].reset_index(drop=True)
        if len(rth) < 35:
            continue

        levels = [
            ("ONH", float(row["onh"])),
            ("ONL", float(row["onl"])),
            ("PDH", float(row["pdh"])),
            ("PDL", float(row["pdl"])),
        ]
        onr = float(row["onr"])
        atr20 = float(row["atr20"]) if pd.notna(row["atr20"]) else onr

        for lname, lvl in levels:
            touched = False
            for i in range(len(rth)):
                bar = rth.iloc[i]
                # skip if open already beyond (gap through) — still valid event at first bar
                if lname in ("ONH", "PDH"):
                    # upward cross: close > level and prior close <= level (or first bar open<= and close>)
                    prev_c = float(rth.iloc[i - 1]["close"]) if i > 0 else float(bar["open"])
                    crossed = (float(bar["close"]) > lvl) and (prev_c <= lvl)
                    direction = 1
                else:
                    prev_c = float(rth.iloc[i - 1]["close"]) if i > 0 else float(bar["open"])
                    crossed = (float(bar["close"]) < lvl) and (prev_c >= lvl)
                    direction = -1

                if not crossed:
                    continue
                touched = True
                sig_min = int(bar["ny_min"])
                # classify accept/reject over next 10 bars AFTER signal bar
                post = rth.iloc[i + 1 : i + 11]
                outcome = "inconclusive"
                if len(post) >= 5:
                    if direction == 1:
                        # accept: any close >= level + ACCEPT_FRAC*ONR
                        # reject: any close < level
                        accept = (post["close"] >= lvl + ACCEPT_FRAC * onr).any()
                        reject = (post["close"] < lvl).any()
                    else:
                        accept = (post["close"] <= lvl - ACCEPT_FRAC * onr).any()
                        reject = (post["close"] > lvl).any()
                    if accept and not reject:
                        outcome = "accept"
                    elif reject and not accept:
                        outcome = "reject"
                    elif accept and reject:
                        # whichever first
                        for _, pb in post.iterrows():
                            if direction == 1:
                                if float(pb["close"]) < lvl:
                                    outcome = "reject"
                                    break
                                if float(pb["close"]) >= lvl + ACCEPT_FRAC * onr:
                                    outcome = "accept"
                                    break
                            else:
                                if float(pb["close"]) > lvl:
                                    outcome = "reject"
                                    break
                                if float(pb["close"]) <= lvl - ACCEPT_FRAC * onr:
                                    outcome = "accept"
                                    break

                # forward returns from NEXT bar open (executable, no lookahead)
                entry_i = i + 1
                fwd: dict[int, float] = {}
                mfe_30 = mae_30 = np.nan
                t_mfe = t_mae = -1
                if entry_i < len(rth):
                    entry = float(rth.iloc[entry_i]["open"])
                    for h in FORWARD_HORIZONS:
                        j = entry_i + h - 1
                        if j < len(rth):
                            fwd[h] = (float(rth.iloc[j]["close"]) - entry) * direction
                        else:
                            fwd[h] = np.nan
                    # MFE/MAE over 30m in trade direction
                    window = rth.iloc[entry_i : entry_i + 30]
                    if len(window):
                        if direction == 1:
                            fav = window["high"].to_numpy() - entry
                            adv = entry - window["low"].to_numpy()
                        else:
                            fav = entry - window["low"].to_numpy()
                            adv = window["high"].to_numpy() - entry
                        mfe_30 = float(np.max(fav))
                        mae_30 = float(np.max(adv))
                        t_mfe = int(np.argmax(fav)) + 1
                        t_mae = int(np.argmax(adv)) + 1

                events.append(
                    LevelEvent(
                        session_date=sd_str,
                        year=int(row["year"]),
                        dow=int(row["dow"]),
                        split=str(row["split"]),
                        level_name=lname,
                        level=lvl,
                        direction=direction,
                        signal_ny_min=sig_min,
                        decision_ts_offset=sig_min - NY_OPEN,
                        onr=onr,
                        atr20=atr20,
                        outcome=outcome,
                        fwd=fwd,
                        mfe_30=mfe_30,
                        mae_30=mae_30,
                        t_mfe=t_mfe,
                        t_mae=t_mae,
                    )
                )
                break  # first touch only per level per day
            _ = touched

    return events


# ---------------------------------------------------------------------------
# Impulse + pullback events
# ---------------------------------------------------------------------------

@dataclass
class ImpulseEvent:
    session_date: str
    year: int
    dow: int
    split: str
    impulse_dir: int
    impulse_ext: float
    impulse_ext_onr: float
    impulse_ext_atr: float
    pullback_frac: float
    pullback_end_min: int
    large: bool
    controlled_pb: bool
    # entry at next bar after pullback extreme confirmed (end of pb bar)
    entry_offset: int
    fwd: dict[int, float]  # in impulse direction (continuation)
    fwd_rev: dict[int, float]  # opposite (reversal)
    mfe_30: float
    mae_30: float
    onr: float
    atr20: float
    onr_vs_med: float


def detect_impulse_events(
    frames: dict[date, pd.DataFrame],
    day_df: pd.DataFrame,
    large_thresh_onr: float,
) -> list[ImpulseEvent]:
    """
    At pullback extreme bar close, we know impulse + pullback depth.
    Entry = next bar open. large_thresh_onr frozen from IS.
    """
    events: list[ImpulseEvent] = []
    for _, row in day_df.iterrows():
        if int(row["impulse_dir"]) == 0:
            continue
        if not np.isfinite(row["pullback_frac"]):
            continue
        sd = date.fromisoformat(row["session_date"])
        g = frames.get(sd)
        if g is None:
            continue
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
        pb_min = int(row["pullback_end_min"])
        if pb_min < 0:
            continue
        # find pb bar
        pb_rows = rth[rth["ny_min"] == NY_OPEN + pb_min]
        if len(pb_rows) == 0:
            continue
        pb_i = int(pb_rows.index[0]) if pb_rows.index[0] < len(rth) else -1
        # locate by position in rth
        matches = np.where(rth["ny_min"].to_numpy() == NY_OPEN + pb_min)[0]
        if len(matches) == 0:
            continue
        pb_i = int(matches[0])
        entry_i = pb_i + 1
        if entry_i >= len(rth):
            continue

        direction = int(row["impulse_dir"])
        onr = float(row["onr"])
        atr20 = float(row["atr20"]) if pd.notna(row["atr20"]) else onr
        ext_onr = float(row["impulse_ext_onr"])
        large = ext_onr >= large_thresh_onr
        pb_frac = float(row["pullback_frac"])
        controlled = PULLBACK_LO <= pb_frac <= PULLBACK_HI

        entry = float(rth.iloc[entry_i]["open"])
        fwd: dict[int, float] = {}
        fwd_rev: dict[int, float] = {}
        for h in FORWARD_HORIZONS:
            j = entry_i + h - 1
            if j < len(rth):
                ret = float(rth.iloc[j]["close"]) - entry
                fwd[h] = ret * direction
                fwd_rev[h] = -ret * direction
            else:
                fwd[h] = np.nan
                fwd_rev[h] = np.nan

        window = rth.iloc[entry_i : entry_i + 30]
        if len(window):
            if direction == 1:
                fav = window["high"].to_numpy() - entry
                adv = entry - window["low"].to_numpy()
            else:
                fav = entry - window["low"].to_numpy()
                adv = window["high"].to_numpy() - entry
            mfe_30 = float(np.max(fav))
            mae_30 = float(np.max(adv))
        else:
            mfe_30 = mae_30 = np.nan

        events.append(
            ImpulseEvent(
                session_date=row["session_date"],
                year=int(row["year"]),
                dow=int(row["dow"]),
                split=str(row["split"]),
                impulse_dir=direction,
                impulse_ext=float(row["impulse_ext"]),
                impulse_ext_onr=ext_onr,
                impulse_ext_atr=float(row["impulse_ext"]) / atr20 if atr20 > 0 else np.nan,
                pullback_frac=pb_frac,
                pullback_end_min=pb_min,
                large=large,
                controlled_pb=controlled,
                entry_offset=int(rth.iloc[entry_i]["ny_min"] - NY_OPEN),
                fwd=fwd,
                fwd_rev=fwd_rev,
                mfe_30=mfe_30,
                mae_30=mae_30,
                onr=onr,
                atr20=atr20,
                onr_vs_med=float(row["onr_vs_med"]) if pd.notna(row["onr_vs_med"]) else np.nan,
            )
        )
    return events


# ---------------------------------------------------------------------------
# Unconditional TOD baseline
# ---------------------------------------------------------------------------

def unconditional_forward(
    frames: dict[date, pd.DataFrame],
    day_df: pd.DataFrame,
    anchor_offset: int = 10,
) -> pd.DataFrame:
    """Forward returns from open of bar at 09:30+anchor_offset, signed by random? No — unsigned and abs.
    We store signed from long-only and also absolute for distribution comparison.
    """
    rows = []
    for _, row in day_df.iterrows():
        sd = date.fromisoformat(row["session_date"])
        g = frames.get(sd)
        if g is None:
            continue
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
        matches = np.where(rth["ny_min"].to_numpy() == NY_OPEN + anchor_offset)[0]
        if len(matches) == 0:
            continue
        i = int(matches[0])
        entry = float(rth.iloc[i]["open"])
        rec = {
            "session_date": row["session_date"],
            "year": int(row["year"]),
            "split": row["split"],
            "dow": int(row["dow"]),
        }
        for h in FORWARD_HORIZONS:
            j = i + h - 1
            if j < len(rth):
                rec[f"fwd_{h}"] = float(rth.iloc[j]["close"]) - entry
            else:
                rec[f"fwd_{h}"] = np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def dist_stats(x: np.ndarray, thresholds_pts: tuple[float, ...] = (5.0, 10.0, 15.0)) -> dict[str, Any]:
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return {"n": 0}
    out: dict[str, Any] = {
        "n": int(n),
        "mean": float(np.mean(x)),
        "median": float(np.median(x)),
        "std": float(np.std(x, ddof=1)) if n > 1 else 0.0,
        "win_p": float(np.mean(x > 0)),
        "p25": float(np.percentile(x, 25)),
        "p75": float(np.percentile(x, 75)),
    }
    for t in thresholds_pts:
        out[f"p_gt_{t}"] = float(np.mean(x >= t))
        out[f"p_lt_m{t}"] = float(np.mean(x <= -t))
    return out


def compare_to_base(cond: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    if cond.get("n", 0) == 0 or base.get("n", 0) == 0:
        return {"delta_mean": np.nan, "delta_win_p": np.nan}
    return {
        "delta_mean": cond["mean"] - base["mean"],
        "delta_win_p": cond["win_p"] - base["win_p"],
        "delta_median": cond["median"] - base["median"],
    }


# ---------------------------------------------------------------------------
# Strategy (only if phenomenon survives)
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    session_date: str
    year: int
    split: str
    dow: int
    direction: int
    entry: float
    stop: float
    target: float
    risk: float
    exit_price: float
    pnl_pts: float
    pnl_R: float
    exit_reason: str
    ambiguous: bool
    minutes_held: int
    mae: float
    mfe: float
    hypothesis: str


def simulate_trade(
    rth: pd.DataFrame,
    entry_i: int,
    direction: int,
    stop: float,
    target: float,
    entry: float,
) -> tuple[float, float, str, bool, int, float, float]:
    """Stop-first on ambiguous bars. Returns exit_px, pnl_pts_gross, reason, amb, held, mae, mfe."""
    risk = abs(entry - stop)
    if risk < TICK:
        return entry, 0.0, "invalid_risk", False, 0, 0.0, 0.0

    mae = 0.0
    mfe = 0.0
    end_i = min(len(rth), entry_i + MAX_HOLD_M)
    for j in range(entry_i, end_i):
        bar = rth.iloc[j]
        hi, lo = float(bar["high"]), float(bar["low"])
        if direction == 1:
            mae = max(mae, entry - lo)
            mfe = max(mfe, hi - entry)
            hit_stop = lo <= stop
            hit_tgt = hi >= target
        else:
            mae = max(mae, hi - entry)
            mfe = max(mfe, entry - lo)
            hit_stop = hi >= stop
            hit_tgt = lo <= target

        if hit_stop and hit_tgt:
            # stop first
            pnl = (stop - entry) * direction
            return stop, pnl, "stop_ambiguous", True, j - entry_i + 1, mae, mfe
        if hit_stop:
            pnl = (stop - entry) * direction
            return stop, pnl, "stop", False, j - entry_i + 1, mae, mfe
        if hit_tgt:
            pnl = (target - entry) * direction
            return target, pnl, "target", False, j - entry_i + 1, mae, mfe

    # time exit at last close
    last = float(rth.iloc[end_i - 1]["close"])
    pnl = (last - entry) * direction
    return last, pnl, "time", False, end_i - entry_i, mae, mfe


def run_strategy_failed_impulse_reversal(
    frames: dict[date, pd.DataFrame],
    day_df: pd.DataFrame,
    large_thresh_onr: float,
) -> list[Trade]:
    """
    Hypothesis B mechanical:
    Large opening impulse + pullback that exceeds 100% of impulse (failed)
    → enter reversal at next bar after pullback through open_930.
    Stop beyond impulse extreme + buffer; target 1.5R.
    Max 1 trade/day.
    """
    trades: list[Trade] = []
    for _, row in day_df.iterrows():
        if int(row["impulse_dir"]) == 0:
            continue
        if float(row["impulse_ext_onr"]) < large_thresh_onr:
            continue
        if not np.isfinite(row["pullback_frac"]):
            continue
        # failed = pullback > 100% of impulse (returned through open)
        if float(row["pullback_frac"]) < 1.0:
            continue

        sd = date.fromisoformat(row["session_date"])
        g = frames.get(sd)
        if g is None:
            continue
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
        o930 = float(row["open_930"])
        direction_impulse = int(row["impulse_dir"])
        # reversal direction
        direction = -direction_impulse

        # find when price first closes back through open after impulse extreme
        # use pullback_end_min bar; require close through open
        matches = np.where(rth["ny_min"].to_numpy() == NY_OPEN + int(row["pullback_end_min"]))[0]
        if len(matches) == 0:
            continue
        pb_i = int(matches[0])
        pb_close = float(rth.iloc[pb_i]["close"])
        # confirm failure through open
        if direction_impulse == 1 and pb_close >= o930:
            continue
        if direction_impulse == -1 and pb_close <= o930:
            continue

        entry_i = pb_i + 1
        if entry_i >= len(rth):
            continue
        # only trade if entry before 10:45
        if int(rth.iloc[entry_i]["ny_min"]) > 10 * 60 + 45:
            continue

        entry = float(rth.iloc[entry_i]["open"])
        # stop beyond impulse extreme
        impulse_ext = float(row["impulse_ext"])
        if direction_impulse == 1:
            impulse_extreme = o930 + impulse_ext
            stop = impulse_extreme + 2.0  # buffer
            # for short
            risk = stop - entry
            if risk < 2.0:
                continue
            target = entry - TARGET_R * risk
        else:
            impulse_extreme = o930 - impulse_ext
            stop = impulse_extreme - 2.0
            risk = entry - stop
            if risk < 2.0:
                continue
            target = entry + TARGET_R * risk

        exit_px, pnl_gross, reason, amb, held, mae, mfe = simulate_trade(
            rth, entry_i, direction, stop, target, entry
        )
        # costs
        pnl_net = pnl_gross - 2 * SLIPPAGE - COMMISSION_RT
        trades.append(
            Trade(
                session_date=row["session_date"],
                year=int(row["year"]),
                split=str(row["split"]),
                dow=int(row["dow"]),
                direction=direction,
                entry=entry,
                stop=stop,
                target=target,
                risk=risk,
                exit_price=exit_px,
                pnl_pts=pnl_net,
                pnl_R=pnl_net / risk if risk > 0 else np.nan,
                exit_reason=reason,
                ambiguous=amb,
                minutes_held=held,
                mae=mae,
                mfe=mfe,
                hypothesis="B_failed_impulse_reversal",
            )
        )
    return trades


def run_strategy_onh_reject(
    frames: dict[date, pd.DataFrame],
    events: list[LevelEvent],
) -> list[Trade]:
    """
    Hypothesis C mechanical (if reject survives):
    First ONH cross that REJECTS within 10m → short at rejection confirmation next bar.
    Stop = ONH + 0.15*ONR; target 1.5R; max 1/day.
    Symmetric for ONL reject → long.
    """
    trades: list[Trade] = []
    # rebuild quick access
    used_days: set[str] = set()
    # We need bar data — re-detect rejection confirmation bar
    by_day_events = {}
    for ev in events:
        if ev.level_name not in ("ONH", "ONL"):
            continue
        if ev.outcome != "reject":
            continue
        by_day_events.setdefault(ev.session_date, []).append(ev)

    for sd_str, evs in by_day_events.items():
        # earliest event only
        ev = sorted(evs, key=lambda e: e.signal_ny_min)[0]
        if sd_str in used_days:
            continue
        sd = date.fromisoformat(sd_str)
        g = frames.get(sd)
        if g is None:
            continue
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
        # find signal bar (cross), then find first reject bar in next 10
        matches = np.where(rth["ny_min"].to_numpy() == ev.signal_ny_min)[0]
        if len(matches) == 0:
            continue
        sig_i = int(matches[0])
        lvl = ev.level
        onr = ev.onr
        reject_i = None
        for j in range(sig_i + 1, min(len(rth), sig_i + 11)):
            c = float(rth.iloc[j]["close"])
            if ev.direction == 1 and c < lvl:
                reject_i = j
                break
            if ev.direction == -1 and c > lvl:
                reject_i = j
                break
        if reject_i is None:
            continue
        entry_i = reject_i + 1
        if entry_i >= len(rth):
            continue
        if int(rth.iloc[entry_i]["ny_min"]) > 10 * 60 + 45:
            continue

        # trade opposite to breakout direction
        direction = -ev.direction
        entry = float(rth.iloc[entry_i]["open"])
        if direction == -1:  # short after ONH reject
            stop = lvl + ACCEPT_FRAC * onr
            risk = stop - entry
            if risk < 2.0:
                continue
            target = entry - TARGET_R * risk
        else:
            stop = lvl - ACCEPT_FRAC * onr
            risk = entry - stop
            if risk < 2.0:
                continue
            target = entry + TARGET_R * risk

        exit_px, pnl_gross, reason, amb, held, mae, mfe = simulate_trade(
            rth, entry_i, direction, stop, target, entry
        )
        pnl_net = pnl_gross - 2 * SLIPPAGE - COMMISSION_RT
        trades.append(
            Trade(
                session_date=sd_str,
                year=ev.year,
                split=ev.split,
                dow=ev.dow,
                direction=direction,
                entry=entry,
                stop=stop,
                target=target,
                risk=risk,
                exit_price=exit_px,
                pnl_pts=pnl_net,
                pnl_R=pnl_net / risk if risk > 0 else np.nan,
                exit_reason=reason,
                ambiguous=amb,
                minutes_held=held,
                mae=mae,
                mfe=mfe,
                hypothesis="C_on_extreme_reject",
            )
        )
        used_days.add(sd_str)
    return trades


def trade_performance(trades: list[Trade]) -> dict[str, Any]:
    if not trades:
        return {"n": 0}
    df = pd.DataFrame([t.__dict__ for t in trades])
    r = df["pnl_R"].to_numpy(dtype=float)
    pts = df["pnl_pts"].to_numpy(dtype=float)
    wins = pts > 0
    gross_win = float(pts[wins].sum()) if wins.any() else 0.0
    gross_loss = float(-pts[~wins].sum()) if (~wins).any() else 0.0
    pf = gross_win / gross_loss if gross_loss > 0 else np.inf

    # max DD in R (cumulative)
    cum = np.cumsum(r)
    peak = np.maximum.accumulate(cum)
    dd = cum - peak
    max_dd = float(dd.min()) if len(dd) else 0.0

    n_days = df["session_date"].nunique()
    # approximate calendar span
    years = sorted(df["year"].unique())

    def by_split(name: str) -> dict[str, Any]:
        s = df[df["split"] == name]
        if len(s) == 0:
            return {"n": 0}
        rr = s["pnl_R"].to_numpy(float)
        pp = s["pnl_pts"].to_numpy(float)
        w = pp > 0
        gw = float(pp[w].sum()) if w.any() else 0.0
        gl = float(-pp[~w].sum()) if (~w).any() else 0.0
        return {
            "n": int(len(s)),
            "win_rate": float(np.mean(w)),
            "expectancy_R": float(np.mean(rr)),
            "total_R": float(np.sum(rr)),
            "avg_pts": float(np.mean(pp)),
            "pf": float(gw / gl) if gl > 0 else None,
            "median_R": float(np.median(rr)),
        }

    yearly = []
    for y, s in df.groupby("year"):
        pp = s["pnl_pts"].to_numpy(float)
        rr = s["pnl_R"].to_numpy(float)
        yearly.append(
            {
                "year": int(y),
                "n": int(len(s)),
                "total_R": float(rr.sum()),
                "avg_R": float(rr.mean()),
                "win_rate": float((pp > 0).mean()),
                "total_pts": float(pp.sum()),
            }
        )

    monthly = []
    df["ym"] = pd.to_datetime(df["session_date"]).dt.to_period("M").astype(str)
    for ym, s in df.groupby("ym"):
        rr = s["pnl_R"].to_numpy(float)
        monthly.append({"month": ym, "n": int(len(s)), "total_R": float(rr.sum()), "win_rate": float((s["pnl_pts"] > 0).mean())})

    # 2025 / 2026
    ybreak = {}
    for y in (2025, 2026):
        s = df[df["year"] == y]
        if len(s) == 0:
            ybreak[str(y)] = {"n": 0}
        else:
            ybreak[str(y)] = {
                "n": int(len(s)),
                "total_R": float(s["pnl_R"].sum()),
                "avg_R": float(s["pnl_R"].mean()),
                "win_rate": float((s["pnl_pts"] > 0).mean()),
            }

    return {
        "n": int(len(df)),
        "win_rate": float(wins.mean()),
        "profit_factor": float(pf) if np.isfinite(pf) else None,
        "expectancy_R": float(np.mean(r)),
        "total_R": float(np.sum(r)),
        "max_drawdown_R": max_dd,
        "median_R": float(np.median(r)),
        "avg_pts": float(np.mean(pts)),
        "trades_per_day": float(len(df) / max(n_days, 1)),
        "unique_days": int(n_days),
        "ambiguous_pct": float(df["ambiguous"].mean()),
        "avg_mae": float(df["mae"].mean()),
        "avg_mfe": float(df["mfe"].mean()),
        "costs": {"slippage_per_side": SLIPPAGE, "commission_rt_pts": COMMISSION_RT},
        "by_split": {k: by_split(k) for k in ("IS", "Validation", "OOS")},
        "yearly": yearly,
        "monthly_profitability_pct": float(np.mean([m["total_R"] > 0 for m in monthly])) if monthly else 0.0,
        "monthly": monthly[-24:],  # last 24 for report size
        "y2025_2026": ybreak,
        "hypothesis": df["hypothesis"].iloc[0],
    }


# ---------------------------------------------------------------------------
# Main research orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== NQ NY Open Behavioral Discovery ===", flush=True)
    print("Loading NQ...", flush=True)
    df = load_nq()
    print(f"Bars: {len(df):,}", flush=True)

    print("Building session frames...", flush=True)
    frames = build_session_frames(df)
    sessions = sorted(frames.keys())
    print(f"Sessions: {len(sessions)}", flush=True)

    print("Phase 1: day facts...", flush=True)
    facts = compute_day_facts(frames, sessions)
    day_df = facts_to_df(facts)
    day_df.to_parquet(art("ny_open_day_facts.parquet"), index=False)
    print(f"Days with facts: {len(day_df)}", flush=True)

    # --- Phase 1 summary ---
    phase1: dict[str, Any] = {}
    for col, label in [
        ("range_1m", "first_1m_range"),
        ("range_5m", "first_5m_range"),
        ("range_10m", "first_10m_range"),
        ("range_30m", "first_30m_range"),
        ("onr", "overnight_range"),
        ("move_1m", "move_1m"),
        ("move_5m", "move_5m"),
        ("move_10m", "move_10m"),
        ("open_loc_onr", "open_loc_in_ONR"),
        ("impulse_ext", "impulse_ext_pts"),
        ("impulse_ext_onr", "impulse_ext_onr"),
        ("pullback_frac", "pullback_frac"),
        ("gap_onr", "gap_vs_ONR"),
    ]:
        x = day_df[col].to_numpy(float)
        phase1[label] = dist_stats(x)

    # directional consistency: sign(move_5m) == sign(move_30 from open)?
    # measure P(continuation of 5m move over next 25m)
    cont5 = []
    for _, row in day_df.iterrows():
        if abs(row["move_5m"]) < TICK:
            continue
        sd = date.fromisoformat(row["session_date"])
        g = frames[sd]
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < NY_OPEN + 30)]
        if len(rth) < 25:
            continue
        o = float(row["open_930"])
        m5 = float(row["move_5m"])
        m30 = float(rth.iloc[-1]["close"] - o)
        cont5.append(1.0 if np.sign(m5) == np.sign(m30) and abs(m30) > abs(m5) else 0.0)
    phase1["p_5m_direction_extends_to_30m"] = {
        "n": len(cont5),
        "p": float(np.mean(cont5)) if cont5 else np.nan,
    }

    # ONH/ONL touch frequency during 09:30-11:00
    touch = {"ONH": 0, "ONL": 0, "PDH": 0, "PDL": 0, "both_ON": 0, "n": 0}
    for _, row in day_df.iterrows():
        sd = date.fromisoformat(row["session_date"])
        g = frames[sd]
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 11 * 60)]
        touch["n"] += 1
        hi, lo = float(rth["high"].max()), float(rth["low"].min())
        th = hi >= float(row["onh"])
        tl = lo <= float(row["onl"])
        if th:
            touch["ONH"] += 1
        if tl:
            touch["ONL"] += 1
        if th and tl:
            touch["both_ON"] += 1
        if hi >= float(row["pdh"]):
            touch["PDH"] += 1
        if lo <= float(row["pdl"]):
            touch["PDL"] += 1
    phase1["level_touch_0930_1100"] = {
        k: (v / touch["n"] if k != "n" else v) for k, v in touch.items()
    }

    # day of week opening range
    dow_stats = []
    for d, s in day_df.groupby("dow"):
        dow_stats.append(
            {
                "dow": int(d),
                "n": int(len(s)),
                "mean_range_30m": float(s["range_30m"].mean()),
                "mean_onr": float(s["onr"].mean()),
                "mean_abs_move_10m": float(s["move_10m"].abs().mean()),
            }
        )
    phase1["by_dow"] = dow_stats

    # year-by-year opening vol
    yearly_vol = []
    for y, s in day_df.groupby("year"):
        yearly_vol.append(
            {
                "year": int(y),
                "n": int(len(s)),
                "median_onr": float(s["onr"].median()),
                "median_range_30m": float(s["range_30m"].median()),
                "median_impulse_onr": float(s["impulse_ext_onr"].median()),
            }
        )
    phase1["yearly_vol"] = yearly_vol

    # open location buckets vs subsequent move
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    day_df["loc_bin"] = pd.cut(day_df["open_loc_onr"].clip(0, 1), bins=bins, include_lowest=True)
    loc_rows = []
    for b, s in day_df.groupby("loc_bin", observed=True):
        loc_rows.append(
            {
                "bin": str(b),
                "n": int(len(s)),
                "mean_move_30_proxy": float(s["move_10m"].mean()),  # known early; for fact board
                "mean_impulse_dir": float(s["impulse_dir"].mean()),
                "p_touch_ONH": float(
                    np.mean(
                        [
                            frames[date.fromisoformat(sd)][
                                (frames[date.fromisoformat(sd)]["ny_min"] >= NY_OPEN)
                                & (frames[date.fromisoformat(sd)]["ny_min"] < 11 * 60)
                            ]["high"].max()
                            >= onh
                            for sd, onh in zip(s["session_date"], s["onh"])
                        ]
                    )
                ),
            }
        )
    phase1["open_location_effects"] = loc_rows

    print("Phase 2-3: level events + impulse events...", flush=True)
    # Freeze large impulse threshold from IS only: 66th percentile of impulse_ext_onr
    is_mask = day_df["split"] == "IS"
    large_thresh = float(day_df.loc[is_mask, "impulse_ext_onr"].quantile(0.66))
    print(f"IS large-impulse threshold (P66 impulse/ONR): {large_thresh:.4f}", flush=True)

    level_events = detect_level_events(frames, day_df)
    impulse_events = detect_impulse_events(frames, day_df, large_thresh)

    # Unconditional baselines at typical decision times
    base10 = unconditional_forward(frames, day_df, anchor_offset=10)
    base20 = unconditional_forward(frames, day_df, anchor_offset=20)

    # --- Hypothesis evaluation ---
    hypotheses: dict[str, Any] = {}

    def event_fwd_matrix(evts: list, attr_fwd: str = "fwd", signed_from_long_base: bool = False) -> dict:
        """Aggregate conditional forward stats by split and horizon."""
        out = {}
        for split in ("IS", "Validation", "OOS", "ALL"):
            subset = [e for e in evts if split == "ALL" or e.split == split]
            out[split] = {}
            for h in FORWARD_HORIZONS:
                if attr_fwd == "fwd":
                    arr = np.array([e.fwd.get(h, np.nan) for e in subset], float)
                else:
                    arr = np.array([e.fwd_rev.get(h, np.nan) for e in subset], float)
                st = dist_stats(arr)
                # baseline: unconditional long from similar TOD — for directional events we compare
                # mean of signed-in-event-direction vs 0, and win_p vs 0.5
                st["vs_zero_mean"] = st.get("mean", np.nan)
                st["edge_vs_coin"] = st.get("win_p", np.nan) - 0.5 if st.get("n", 0) else np.nan
                out[split][f"h{h}"] = st
            # MFE/MAE
            mfe = np.array([e.mfe_30 for e in subset], float)
            mae = np.array([e.mae_30 for e in subset], float)
            out[split]["mfe_30"] = dist_stats(mfe)
            out[split]["mae_30"] = dist_stats(mae)
        return out

    # A: large + controlled pullback → continuation
    A = [e for e in impulse_events if e.large and e.controlled_pb]
    hypotheses["A_impulse_continuation"] = {
        "definition": "Large (IS P66+) opening impulse + pullback 25-62% of impulse → continuation",
        "n_total": len(A),
        "fwd_continuation": event_fwd_matrix(A, "fwd"),
        "n_by_split": {
            s: sum(1 for e in A if e.split == s) for s in ("IS", "Validation", "OOS")
        },
    }

    # A control: large without controlled pb
    A_ctrl = [e for e in impulse_events if e.large and not e.controlled_pb]
    hypotheses["A_control_large_not_controlled"] = {
        "n_total": len(A_ctrl),
        "fwd_continuation": event_fwd_matrix(A_ctrl, "fwd"),
    }

    # B: large + failed pullback (>100%) → reversal
    B = [e for e in impulse_events if e.large and e.pullback_frac >= 1.0]
    hypotheses["B_failed_impulse_reversal"] = {
        "definition": "Large impulse + pullback >=100% of impulse → reversal edge",
        "n_total": len(B),
        "fwd_reversal": event_fwd_matrix(B, "fwd_rev"),
        "n_by_split": {
            s: sum(1 for e in B if e.split == s) for s in ("IS", "Validation", "OOS")
        },
    }

    # C: ON extreme accept vs reject
    for lname in ("ONH", "ONL", "PDH", "PDL"):
        for outcome in ("accept", "reject"):
            sub = [e for e in level_events if e.level_name == lname and e.outcome == outcome]
            key = f"C_{lname}_{outcome}"
            # for accept: continuation in breakout dir; for reject: reversal (use fwd which is breakout dir — reject should be negative)
            hypotheses[key] = {
                "n_total": len(sub),
                "fwd_breakout_dir": event_fwd_matrix(sub, "fwd"),
                "n_by_split": {
                    s: sum(1 for e in sub if e.split == s) for s in ("IS", "Validation", "OOS")
                },
            }

    # D: open near ON extreme
    # Already in phase1; add conditional: open in top/bottom 20% of ONR
    near_high = day_df[day_df["open_loc_onr"] >= 0.8]
    near_low = day_df[day_df["open_loc_onr"] <= 0.2]
    # forward from 09:31 open — use move_10m as early proxy already in day facts;
    # build proper fwd from offset 1
    def days_fwd(sub_df: pd.DataFrame, offset: int = 1) -> dict:
        rows = []
        for _, row in sub_df.iterrows():
            sd = date.fromisoformat(row["session_date"])
            g = frames[sd]
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
            matches = np.where(rth["ny_min"].to_numpy() == NY_OPEN + offset)[0]
            if len(matches) == 0:
                continue
            i = int(matches[0])
            entry = float(rth.iloc[i]["open"])
            # fade: if near high, short; near low, long — store fade PnL
            fade_dir = -1 if row["open_loc_onr"] >= 0.8 else 1
            rec = {"split": row["split"], "year": int(row["year"])}
            for h in FORWARD_HORIZONS:
                j = i + h - 1
                if j < len(rth):
                    rec[f"h{h}"] = (float(rth.iloc[j]["close"]) - entry) * fade_dir
            rows.append(rec)
        rdf = pd.DataFrame(rows)
        out = {}
        for split in ("IS", "Validation", "OOS", "ALL"):
            s = rdf if split == "ALL" else rdf[rdf["split"] == split]
            out[split] = {f"h{h}": dist_stats(s[f"h{h}"].to_numpy(float)) for h in FORWARD_HORIZONS if f"h{h}" in s}
        return out

    hypotheses["D_fade_open_near_ON_extreme"] = {
        "definition": "Open in top/bottom 20% of overnight range → fade for 5-30m",
        "n_near_high": int(len(near_high)),
        "n_near_low": int(len(near_low)),
        "fade_stats": days_fwd(pd.concat([near_high, near_low], ignore_index=True)),
    }

    # E: gap through overnight extreme then reject (discovered)
    # gap above ONH at open, then within 30m close back below ONH
    gap_through = []
    for _, row in day_df.iterrows():
        o = float(row["open_930"])
        onh, onl = float(row["onh"]), float(row["onl"])
        sd = date.fromisoformat(row["session_date"])
        g = frames[sd]
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < NY_OPEN + 45)].reset_index(drop=True)
        if len(rth) < 20:
            continue
        if o > onh:
            # look for close back below ONH
            for i in range(1, min(30, len(rth))):
                if float(rth.iloc[i]["close"]) < onh:
                    entry_i = i + 1
                    if entry_i >= len(rth):
                        break
                    entry = float(rth.iloc[entry_i]["open"])
                    fwd = {}
                    for h in FORWARD_HORIZONS:
                        j = entry_i + h - 1
                        # need more bars — extend window
                        break
                    # use wider frame
                    rth2 = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
                    matches = np.where(rth2["ny_min"].to_numpy() == int(rth.iloc[entry_i]["ny_min"]))[0]
                    if len(matches) == 0:
                        break
                    ei = int(matches[0])
                    entry = float(rth2.iloc[ei]["open"])
                    fwd = {}
                    for h in FORWARD_HORIZONS:
                        j = ei + h - 1
                        if j < len(rth2):
                            fwd[h] = entry - float(rth2.iloc[j]["close"])  # short fade
                        else:
                            fwd[h] = np.nan
                    gap_through.append(
                        {
                            "split": row["split"],
                            "year": int(row["year"]),
                            "side": "above_ONH",
                            "fwd": fwd,
                        }
                    )
                    break
        elif o < onl:
            for i in range(1, min(30, len(rth))):
                if float(rth.iloc[i]["close"]) > onl:
                    rth2 = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
                    matches = np.where(rth2["ny_min"].to_numpy() == int(rth.iloc[i + 1]["ny_min"]) if i + 1 < len(rth) else -1)[0]
                    if len(matches) == 0:
                        break
                    ei = int(matches[0])
                    entry = float(rth2.iloc[ei]["open"])
                    fwd = {}
                    for h in FORWARD_HORIZONS:
                        j = ei + h - 1
                        if j < len(rth2):
                            fwd[h] = float(rth2.iloc[j]["close"]) - entry  # long fade
                        else:
                            fwd[h] = np.nan
                    gap_through.append(
                        {
                            "split": row["split"],
                            "year": int(row["year"]),
                            "side": "below_ONL",
                            "fwd": fwd,
                        }
                    )
                    break

    def gap_stats(items: list[dict]) -> dict:
        out = {}
        for split in ("IS", "Validation", "OOS", "ALL"):
            sub = items if split == "ALL" else [x for x in items if x["split"] == split]
            out[split] = {}
            for h in FORWARD_HORIZONS:
                arr = np.array([x["fwd"].get(h, np.nan) for x in sub], float)
                out[split][f"h{h}"] = dist_stats(arr)
        return out

    hypotheses["E_gap_through_ON_then_reclaim"] = {
        "definition": "Open beyond ONH/ONL then reclaim within 30m → fade continuation",
        "n_total": len(gap_through),
        "fwd_fade": gap_stats(gap_through),
        "n_by_split": {
            s: sum(1 for x in gap_through if x["split"] == s) for s in ("IS", "Validation", "OOS")
        },
    }

    # Unconditional baselines (long-only mean should be ~drift)
    baseline = {}
    for name, bdf in [("tod_plus10m", base10), ("tod_plus20m", base20)]:
        baseline[name] = {}
        for split in ("IS", "Validation", "OOS", "ALL"):
            s = bdf if split == "ALL" else bdf[bdf["split"] == split]
            baseline[name][split] = {
                f"h{h}": dist_stats(s[f"fwd_{h}"].to_numpy(float)) for h in FORWARD_HORIZONS
            }

    print("Scoring phenomena...", flush=True)

    def score_phenomenon(fwd_block: dict, direction_label: str) -> dict[str, Any]:
        """
        Require: IS edge (win_p>0.52 or mean materially >0), Validation same sign,
        OOS same sign at h15 or h20. Prefer larger n.
        """
        def edge(split: str, h: int = 15) -> dict:
            return fwd_block.get(split, {}).get(f"h{h}", {})

        is_e = edge("IS", 15)
        va_e = edge("Validation", 15)
        oo_e = edge("OOS", 15)
        # also check h20
        oo20 = edge("OOS", 20)

        def ok(e: dict) -> bool:
            if e.get("n", 0) < 40:
                return False
            return (e.get("win_p", 0) >= 0.53 and e.get("mean", 0) > 0) or (
                e.get("mean", 0) > 1.0 and e.get("win_p", 0) >= 0.51
            )

        survives = ok(is_e) and ok(va_e) and (ok(oo_e) or ok(oo20))
        # weaker: same sign means
        same_sign = (
            is_e.get("mean", 0) > 0
            and va_e.get("mean", 0) > 0
            and (oo_e.get("mean", 0) > 0 or oo20.get("mean", 0) > 0)
        )
        return {
            "direction": direction_label,
            "survives_strict": bool(survives),
            "same_sign_means": bool(same_sign),
            "IS_h15": is_e,
            "Val_h15": va_e,
            "OOS_h15": oo_e,
            "OOS_h20": oo20,
            "score": float(
                (is_e.get("win_p", 0.5) - 0.5) * 100
                + (va_e.get("win_p", 0.5) - 0.5) * 100
                + (oo_e.get("win_p", 0.5) - 0.5) * 100
            )
            if is_e.get("n", 0)
            else -999,
        }

    rankings = []
    # A continuation
    rankings.append(
        {
            "id": "A_impulse_continuation",
            **score_phenomenon(hypotheses["A_impulse_continuation"]["fwd_continuation"], "continuation"),
            "n": hypotheses["A_impulse_continuation"]["n_total"],
        }
    )
    rankings.append(
        {
            "id": "B_failed_impulse_reversal",
            **score_phenomenon(hypotheses["B_failed_impulse_reversal"]["fwd_reversal"], "reversal"),
            "n": hypotheses["B_failed_impulse_reversal"]["n_total"],
        }
    )
    for lname in ("ONH", "ONL", "PDH", "PDL"):
        # reject should show NEGATIVE fwd in breakout dir → flip: use mean < 0 as edge for fade
        for outcome, want_negative in (("accept", False), ("reject", True)):
            key = f"C_{lname}_{outcome}"
            block = hypotheses[key]["fwd_breakout_dir"]
            # If want_negative, negate means/win for scoring by transforming
            flipped = {}
            for split, horizons in block.items():
                flipped[split] = {}
                for hk, st in horizons.items():
                    if not isinstance(st, dict) or "mean" not in st:
                        flipped[split][hk] = st
                        continue
                    if want_negative:
                        # convert breakout-dir returns to fade returns
                        ns = dict(st)
                        if st.get("n", 0):
                            ns["mean"] = -st["mean"]
                            ns["median"] = -st.get("median", 0)
                            ns["win_p"] = 1.0 - st["win_p"]
                        flipped[split][hk] = ns
                    else:
                        flipped[split][hk] = st
            rankings.append(
                {
                    "id": key,
                    **score_phenomenon(flipped, "accept_cont" if not want_negative else "reject_fade"),
                    "n": hypotheses[key]["n_total"],
                }
            )

    rankings.append(
        {
            "id": "D_fade_open_near_ON_extreme",
            **score_phenomenon(hypotheses["D_fade_open_near_ON_extreme"]["fade_stats"], "fade"),
            "n": hypotheses["D_fade_open_near_ON_extreme"]["n_near_high"]
            + hypotheses["D_fade_open_near_ON_extreme"]["n_near_low"],
        }
    )
    rankings.append(
        {
            "id": "E_gap_through_ON_then_reclaim",
            **score_phenomenon(hypotheses["E_gap_through_ON_then_reclaim"]["fwd_fade"], "fade"),
            "n": hypotheses["E_gap_through_ON_then_reclaim"]["n_total"],
        }
    )

    rankings = sorted(rankings, key=lambda r: r.get("score", -999), reverse=True)

    survivors = [r for r in rankings if r.get("survives_strict")]
    soft = [r for r in rankings if r.get("same_sign_means") and not r.get("survives_strict")]

    print("Survivors (strict):", [r["id"] for r in survivors], flush=True)
    print("Soft same-sign:", [r["id"] for r in soft[:5]], flush=True)

    # --- Phase 7: strategy only for best survivor ---
    strategy_report: dict[str, Any] = {"built": False}
    trades: list[Trade] = []

    # Prefer ONH/ONL reject or B or E if survive
    preferred_order = [
        "C_ONH_reject",
        "C_ONL_reject",
        "B_failed_impulse_reversal",
        "E_gap_through_ON_then_reclaim",
        "A_impulse_continuation",
        "C_ONH_accept",
        "C_ONL_accept",
    ]
    chosen = None
    for pid in preferred_order:
        hit = next((r for r in survivors if r["id"] == pid), None)
        if hit:
            chosen = hit
            break
    if chosen is None and survivors:
        chosen = survivors[0]

    # If nothing strict, still build best soft candidate for diagnostic (labeled as insufficient)
    diagnostic_only = False
    if chosen is None:
        for pid in preferred_order:
            hit = next((r for r in soft if r["id"] == pid), None)
            if hit:
                chosen = hit
                diagnostic_only = True
                break
        if chosen is None and soft:
            chosen = soft[0]
            diagnostic_only = True

    if chosen is not None:
        cid = chosen["id"]
        print(f"Building strategy around: {cid} (diagnostic_only={diagnostic_only})", flush=True)
        if cid in ("C_ONH_reject", "C_ONL_reject") or cid.startswith("C_ON"):
            # use ON reject strategy (both ONH and ONL)
            trades = run_strategy_onh_reject(frames, level_events)
        elif cid == "B_failed_impulse_reversal":
            trades = run_strategy_failed_impulse_reversal(frames, day_df, large_thresh)
        elif cid == "A_impulse_continuation":
            # continuation strategy: large+controlled → enter with impulse dir
            trades = []
            for e in A:
                sd = date.fromisoformat(e.session_date)
                g = frames[sd]
                rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
                matches = np.where(rth["ny_min"].to_numpy() == NY_OPEN + e.pullback_end_min)[0]
                if len(matches) == 0:
                    continue
                entry_i = int(matches[0]) + 1
                if entry_i >= len(rth) or int(rth.iloc[entry_i]["ny_min"]) > 10 * 60 + 45:
                    continue
                entry = float(rth.iloc[entry_i]["open"])
                direction = e.impulse_dir
                # stop beyond pullback extreme approx: entry adverse by pullback remaining
                risk = max(e.impulse_ext * e.pullback_frac * 0.5, 0.25 * e.onr)
                risk = max(risk, 2.0)
                if direction == 1:
                    stop = entry - risk
                    target = entry + TARGET_R * risk
                else:
                    stop = entry + risk
                    target = entry - TARGET_R * risk
                exit_px, pnl_gross, reason, amb, held, mae, mfe = simulate_trade(
                    rth, entry_i, direction, stop, target, entry
                )
                pnl_net = pnl_gross - 2 * SLIPPAGE - COMMISSION_RT
                trades.append(
                    Trade(
                        session_date=e.session_date,
                        year=e.year,
                        split=e.split,
                        dow=e.dow,
                        direction=direction,
                        entry=entry,
                        stop=stop,
                        target=target,
                        risk=risk,
                        exit_price=exit_px,
                        pnl_pts=pnl_net,
                        pnl_R=pnl_net / risk,
                        exit_reason=reason,
                        ambiguous=amb,
                        minutes_held=held,
                        mae=mae,
                        mfe=mfe,
                        hypothesis="A_impulse_continuation",
                    )
                )
        elif cid == "E_gap_through_ON_then_reclaim":
            # mechanical gap-through reclaim
            trades = []
            for _, row in day_df.iterrows():
                o = float(row["open_930"])
                onh, onl = float(row["onh"]), float(row["onl"])
                onr = float(row["onr"])
                sd = date.fromisoformat(row["session_date"])
                g = frames[sd]
                rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
                direction = 0
                reclaim_i = None
                if o > onh:
                    for i in range(1, min(30, len(rth))):
                        if float(rth.iloc[i]["close"]) < onh:
                            reclaim_i = i
                            direction = -1
                            lvl = onh
                            break
                elif o < onl:
                    for i in range(1, min(30, len(rth))):
                        if float(rth.iloc[i]["close"]) > onl:
                            reclaim_i = i
                            direction = 1
                            lvl = onl
                            break
                if reclaim_i is None or direction == 0:
                    continue
                entry_i = reclaim_i + 1
                if entry_i >= len(rth):
                    continue
                entry = float(rth.iloc[entry_i]["open"])
                if direction == -1:
                    stop = max(o, lvl) + ACCEPT_FRAC * onr
                    risk = stop - entry
                    if risk < 2.0:
                        continue
                    target = entry - TARGET_R * risk
                else:
                    stop = min(o, lvl) - ACCEPT_FRAC * onr
                    risk = entry - stop
                    if risk < 2.0:
                        continue
                    target = entry + TARGET_R * risk
                exit_px, pnl_gross, reason, amb, held, mae, mfe = simulate_trade(
                    rth, entry_i, direction, stop, target, entry
                )
                pnl_net = pnl_gross - 2 * SLIPPAGE - COMMISSION_RT
                trades.append(
                    Trade(
                        session_date=row["session_date"],
                        year=int(row["year"]),
                        split=str(row["split"]),
                        dow=int(row["dow"]),
                        direction=direction,
                        entry=entry,
                        stop=stop,
                        target=target,
                        risk=risk,
                        exit_price=exit_px,
                        pnl_pts=pnl_net,
                        pnl_R=pnl_net / risk,
                        exit_reason=reason,
                        ambiguous=amb,
                        minutes_held=held,
                        mae=mae,
                        mfe=mfe,
                        hypothesis="E_gap_through_reclaim",
                    )
                )
        else:
            # D fade open — rarely survives; skip mechanical unless chosen
            trades = []

        if trades:
            strategy_report = {
                "built": True,
                "diagnostic_only": diagnostic_only,
                "based_on": cid,
                "performance": trade_performance(trades),
            }
            pd.DataFrame([t.__dict__ for t in trades]).to_csv(
                art("ny_open_strategy_trades.csv"), index=False
            )

    # OOS weekday / vol regime breakdown for top phenomenon conditional returns
    regime_breakdown = {}
    if chosen is not None:
        cid = chosen["id"]
        # attach onr_vs_med terciles from day_df for OOS events
        med = day_df["onr_vs_med"].median()
        day_df["vol_reg"] = np.where(
            day_df["onr_vs_med"] >= day_df["onr_vs_med"].quantile(0.66),
            "high",
            np.where(day_df["onr_vs_med"] <= day_df["onr_vs_med"].quantile(0.33), "low", "mid"),
        )

    # Final verdict
    if survivors:
        # check strategy OOS expectancy if built and not diagnostic
        if strategy_report.get("built") and not strategy_report.get("diagnostic_only"):
            oos = strategy_report["performance"]["by_split"].get("OOS", {})
            if oos.get("n", 0) >= 30 and oos.get("expectancy_R", -1) > 0.05 and oos.get("win_rate", 0) > 0.5:
                verdict = "A"
                verdict_text = "Demonstrated robust executable edge"
            else:
                verdict = "B"
                verdict_text = "Promising but insufficient evidence (phenomenon survives conditional test; strategy economics weak/thin)"
        else:
            verdict = "B"
            verdict_text = "Promising but insufficient evidence"
    elif soft:
        verdict = "C"
        verdict_text = "No demonstrated edge (same-sign soft effects only; fail strict survival)"
    else:
        verdict = "C"
        verdict_text = "No demonstrated edge"

    # Falsification summary
    falsified = []
    for r in rankings:
        if not r.get("survives_strict"):
            why = []
            if not r.get("same_sign_means"):
                why.append("mean forward return changes sign across IS/Val/OOS")
            else:
                why.append("effect too weak or sample too small for strict survival")
            is15 = r.get("IS_h15", {})
            if is15.get("n", 0) < 40:
                why.append(f"IS n={is15.get('n', 0)} too small")
            if is15.get("win_p", 0.5) < 0.52:
                why.append(f"IS win_p={is15.get('win_p', float('nan')):.3f} near coin-flip")
            falsified.append({"id": r["id"], "why": "; ".join(why), "score": r.get("score")})

    hyp_summaries: dict[str, Any] = {}
    for k, v in hypotheses.items():
        slim = {
            kk: vv
            for kk, vv in v.items()
            if kk
            not in (
                "fwd_continuation",
                "fwd_reversal",
                "fwd_breakout_dir",
                "fade_stats",
                "fwd_fade",
            )
        }
        block = v.get(
            "fwd_continuation",
            v.get(
                "fwd_reversal",
                v.get("fwd_breakout_dir", v.get("fade_stats", v.get("fwd_fade"))),
            ),
        )
        if block is not None:
            slim["fwd_summary"] = score_phenomenon(block, "summary")
        hyp_summaries[k] = slim

    report = {
        "meta": {
            "dataset": "nq_1m_continuous.parquet",
            "range": "2010-06 to 2026-08",
            "focus": "09:00-11:00 ET, emphasis 09:30-10:30",
            "splits": {"IS": "2010-2021", "Validation": "2022-2024", "OOS": "2025-2026"},
            "large_impulse_thresh_onr_IS_p66": large_thresh,
            "costs": {"slippage_per_side_pts": SLIPPAGE, "commission_rt_pts": COMMISSION_RT},
            "anti_overfit": [
                "Thresholds frozen from IS only",
                "No parameter search on Val/OOS",
                "Executable next-bar entries only",
                "Stop-first ambiguous bars",
            ],
        },
        "phase1_behavioral_facts": phase1,
        "n_days": int(len(day_df)),
        "n_level_events": len(level_events),
        "n_impulse_events": len(impulse_events),
        "baseline_tod": {
            "tod_plus10m_ALL_h15": baseline["tod_plus10m"]["ALL"]["h15"],
            "tod_plus20m_ALL_h15": baseline["tod_plus20m"]["ALL"]["h15"],
        },
        "hypotheses": hyp_summaries,
        "rankings": rankings,
        "survivors_strict": survivors,
        "soft_same_sign": soft,
        "falsified": falsified,
        "strategy": strategy_report,
        "verdict": {"code": verdict, "text": verdict_text},
    }

    # Store full hypothesis forward matrices separately (compact)
    hyp_full = {}
    for k, v in hypotheses.items():
        hyp_full[k] = v
    with open(art("ny_open_hypotheses_full.json"), "w", encoding="utf-8") as f:
        json.dump(hyp_full, f, indent=2, default=str)

    with open(art("ny_open_behavioral_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Also write a markdown research report
    md = render_markdown(report, rankings, survivors, soft, falsified, strategy_report, phase1, large_thresh)
    (art("ny_open_behavioral_report.md")).write_text(md, encoding="utf-8")
    print("Wrote artifacts/ny_open_behavioral_report.json/.md", flush=True)
    print("VERDICT:", verdict, verdict_text, flush=True)


def render_markdown(report, rankings, survivors, soft, falsified, strategy_report, phase1, large_thresh) -> str:
    v = report["verdict"]
    lines = []
    lines.append("# NQ NY Open — Behavioral Discovery Report")
    lines.append("")
    lines.append(f"**Verdict: {v['code']} — {v['text']}**")
    lines.append("")
    lines.append("Dataset: `nq_1m_continuous.parquet` (2010-06 → 2026-08). Splits: IS 2010–2021 / Val 2022–2024 / OOS 2025–2026.")
    lines.append(f"Days analyzed: {report['n_days']}. Large-impulse threshold frozen at IS P66 impulse/ONR = **{large_thresh:.4f}**.")
    lines.append("")
    lines.append("## 1. NQ Behavioral Facts")
    lines.append("")
    r1 = phase1.get("first_1m_range", {})
    r5 = phase1.get("first_5m_range", {})
    r10 = phase1.get("first_10m_range", {})
    r30 = phase1.get("first_30m_range", {})
    onr = phase1.get("overnight_range", {})
    lines.append(
        f"- Overnight range: median **{onr.get('median', float('nan')):.1f}** pts "
        f"(mean {onr.get('mean', float('nan')):.1f})."
    )
    lines.append(
        f"- Opening ranges: 1m median {r1.get('median', float('nan')):.1f}, "
        f"5m {r5.get('median', float('nan')):.1f}, "
        f"10m {r10.get('median', float('nan')):.1f}, "
        f"30m {r30.get('median', float('nan')):.1f} pts."
    )
    touch = phase1.get("level_touch_0930_1100", {})
    lines.append(
        f"- By 11:00 ET, price has touched ONH on **{100*touch.get('ONH', 0):.0f}%** of days, "
        f"ONL **{100*touch.get('ONL', 0):.0f}%**, both **{100*touch.get('both_ON', 0):.0f}%**; "
        f"PDH **{100*touch.get('PDH', 0):.0f}%**, PDL **{100*touch.get('PDL', 0):.0f}%**."
    )
    pext = phase1.get("p_5m_direction_extends_to_30m", {})
    lines.append(
        f"- P(5m direction extends through 30m): **{100*pext.get('p', float('nan')):.1f}%** "
        f"(n={pext.get('n')}) — modest continuation bias only."
    )
    pb = phase1.get("pullback_frac", {})
    lines.append(
        f"- After first impulse, pullback fraction median **{pb.get('median', float('nan')):.2f}** "
        f"(of impulse size)."
    )
    lines.append("")
    lines.append("Year-by-year overnight/opening vol (median pts):")
    lines.append("")
    lines.append("| Year | n | ONR | 30m range | impulse/ONR |")
    lines.append("|------|---|-----|-----------|-------------|")
    for y in phase1.get("yearly_vol", []):
        lines.append(
            f"| {y['year']} | {y['n']} | {y['median_onr']:.1f} | {y['median_range_30m']:.1f} | {y['median_impulse_onr']:.3f} |"
        )
    lines.append("")
    lines.append("## 2. Common-Sense Deductions")
    lines.append("")
    lines.append(
        "- Overnight extremes are frequently tested in the first 90 minutes — "
        "interaction with ONH/ONL is common enough to study, not rare."
    )
    lines.append(
        "- Opening impulse often partially retraces (~median pullback fraction above); "
        "blind continuation after any impulse is unlikely to be a strong edge."
    )
    lines.append(
        "- Absolute point thresholds are meaningless across 2010–2026; "
        "ONR- and ATR-normalized measures are required."
    )
    lines.append(
        "- Any exploitable asymmetry must shift the *conditional* forward distribution "
        "vs same-time-of-day unconditional returns, not merely print a positive mean."
    )
    lines.append("")
    lines.append("## 3. Candidate Phenomena (ranked)")
    lines.append("")
    lines.append("| Rank | ID | n | Score | Strict | Same-sign | IS h15 win | Val h15 win | OOS h15 win |")
    lines.append("|------|----|---|-------|--------|-----------|------------|-------------|-------------|")
    for i, r in enumerate(rankings[:12], 1):
        lines.append(
            f"| {i} | {r['id']} | {r.get('n')} | {r.get('score', float('nan')):.2f} | "
            f"{r.get('survives_strict')} | {r.get('same_sign_means')} | "
            f"{r.get('IS_h15', {}).get('win_p', float('nan')):.3f} | "
            f"{r.get('Val_h15', {}).get('win_p', float('nan')):.3f} | "
            f"{r.get('OOS_h15', {}).get('win_p', float('nan')):.3f} |"
        )
    lines.append("")
    lines.append("## 4. Falsification Results")
    lines.append("")
    for f in falsified[:15]:
        lines.append(f"- **{f['id']}**: {f['why']}")
    lines.append("")
    lines.append("## 5. Surviving Phenomena")
    lines.append("")
    if survivors:
        for s in survivors:
            lines.append(
                f"- **{s['id']}** — strict survival. "
                f"IS/Val/OOS h15 win_p = "
                f"{s.get('IS_h15', {}).get('win_p', float('nan')):.3f} / "
                f"{s.get('Val_h15', {}).get('win_p', float('nan')):.3f} / "
                f"{s.get('OOS_h15', {}).get('win_p', float('nan')):.3f}; "
                f"means = "
                f"{s.get('IS_h15', {}).get('mean', float('nan')):.2f} / "
                f"{s.get('Val_h15', {}).get('mean', float('nan')):.2f} / "
                f"{s.get('OOS_h15', {}).get('mean', float('nan')):.2f} pts."
            )
    else:
        lines.append("None under strict IS→Val→OOS criteria.")
        if soft:
            lines.append("Soft same-sign only: " + ", ".join(s["id"] for s in soft[:5]))
    lines.append("")
    lines.append("## 6–7. Strategy Candidate & Performance")
    lines.append("")
    if strategy_report.get("built"):
        perf = strategy_report["performance"]
        lines.append(
            f"Strategy based on `{strategy_report['based_on']}` "
            f"(diagnostic_only={strategy_report.get('diagnostic_only')})."
        )
        lines.append("")
        lines.append(
            f"- N={perf['n']}, win_rate={100*perf['win_rate']:.1f}%, "
            f"PF={perf['profit_factor']}, expectancy={perf['expectancy_R']:.3f}R, "
            f"total_R={perf['total_R']:.1f}, maxDD={perf['max_drawdown_R']:.1f}R, "
            f"median_R={perf['median_R']:.3f}, avg_pts={perf['avg_pts']:.2f}, "
            f"trades/day={perf['trades_per_day']:.2f}."
        )
        lines.append(f"- Ambiguous stop-first bars: {100*perf['ambiguous_pct']:.1f}%.")
        lines.append(f"- Costs: slippage {SLIPPAGE}pt/side, commission {COMMISSION_RT}pt RT.")
        lines.append("")
        lines.append("| Split | n | WR | Exp R | Total R | Avg pts | PF |")
        lines.append("|-------|---|----|-------|---------|---------|----|")
        for sp in ("IS", "Validation", "OOS"):
            s = perf["by_split"].get(sp, {})
            if s.get("n", 0) == 0:
                continue
            lines.append(
                f"| {sp} | {s['n']} | {100*s['win_rate']:.1f}% | {s['expectancy_R']:.3f} | "
                f"{s['total_R']:.1f} | {s['avg_pts']:.2f} | {s.get('pf')} |"
            )
        lines.append("")
        lines.append("Yearly:")
        lines.append("")
        lines.append("| Year | n | Total R | Avg R | WR |")
        lines.append("|------|---|---------|-------|----|")
        for y in perf.get("yearly", []):
            lines.append(
                f"| {y['year']} | {y['n']} | {y['total_R']:.1f} | {y['avg_R']:.3f} | {100*y['win_rate']:.1f}% |"
            )
        lines.append("")
        yb = perf.get("y2025_2026", {})
        lines.append(f"OOS breakdown: 2025={yb.get('2025')}, 2026={yb.get('2026')}.")
        lines.append(f"Monthly profitability rate: {100*perf.get('monthly_profitability_pct', 0):.0f}%.")
    else:
        lines.append("No strategy built — no phenomenon cleared the bar for mechanical conversion.")
    lines.append("")
    lines.append("## 8. Final Verdict")
    lines.append("")
    lines.append(f"**{v['code']} — {v['text']}**")
    lines.append("")
    lines.append(
        "Research outcome is successful if nothing survives: "
        "the NY open is structurally active, but a small persistent executable asymmetry "
        "was not established under hostile causal rules."
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
