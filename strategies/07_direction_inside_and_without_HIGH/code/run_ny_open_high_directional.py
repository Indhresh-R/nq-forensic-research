"""
NQ HIGH-conditional Directional Discovery

Prerequisite (FROZEN — do not optimize):
  HIGH/ARM = vol_expansion_high  (rng_onr >= IS p66 at T)
  See artifacts/frozen_opportunity_gate.md

Question:
  Inside HIGH only, does independent mechanism X create directional asymmetry
  beyond the HIGH-alone baseline?

Test each X independently (no combinations):
  1) Opening impulse / follow-through
  2) VWAP side (above/below session VWAP to T)
  3) Opening-range accept / reject
  4) Short-term HH/HL vs LH/LL structure
  5) Overnight positioning (mid / ONH / ONL)
  6) Impulse + first pullback reaction

Protocol:
  - State + X from bars with ny_min <= T only (pullback confirm may be later but causal)
  - Outcomes from NEXT bar open after signal clock
  - Compare HIGH+X vs HIGH alone (same T / same horizon)
  - Splits: IS 2010-21 / Val 2022-24 / OOS 2025-26 + year break
  - Success: causal, year-stable, modest lift OK; not max win-rate mining

NO entries optimization, NO stops/targets fitting, NO gate retuning.
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
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common.nq_session import (
    art,
    ART,
    DECISION_OFFSETS,
    NY_OPEN,
    build_day_context,
    load_nq,
    rate_of,
    state_at_T,
    win_rate,
)

warnings.filterwarnings("ignore", category=FutureWarning)

HORIZONS = (10, 15, 30)
# Primary ARM clocks denser early morning where gate was strongest for opportunity
ARM_OFFSETS = tuple(range(10, 91, 5))  # need some path for structure / OR

GATE = json.loads((art("frozen_opportunity_gate.json")).read_text(encoding="utf-8"))
THRESH = json.loads((art("ny_open_opp_timing_thresholds_IS.json")).read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]


def th_get(feat: str, off: int) -> dict[str, float]:
    d = STATE_TH[feat]
    return d.get(str(off)) or d.get(off) or {}


def is_high(row_or_rng: float, off: int) -> bool:
    t = th_get("rng_onr", off)
    if not t:
        return False
    return float(row_or_rng) >= float(t["p66"])


def fwd_from_next(rth: pd.DataFrame, clock_ny: int, horizons: tuple[int, ...] = HORIZONS) -> dict[str, float] | None:
    after = rth[rth["ny_min"] > clock_ny].reset_index(drop=True)
    if len(after) < max(horizons):
        return None
    entry = float(after.iloc[0]["open"])
    out = {"entry": entry, "clock_ny": float(clock_ny)}
    highs = after["high"].to_numpy(float)
    lows = after["low"].to_numpy(float)
    closes = after["close"].to_numpy(float)
    for H in horizons:
        out[f"fwd_{H}"] = float(closes[H - 1] - entry)
        out[f"mfe_{H}"] = float(highs[:H].max() - entry)
        out[f"mae_{H}"] = float(entry - lows[:H].min())
    return out


def session_vwap(rth_to_T: pd.DataFrame) -> float | None:
    if len(rth_to_T) == 0:
        return None
    tp = (rth_to_T["high"].to_numpy(float) + rth_to_T["low"].to_numpy(float) + rth_to_T["close"].to_numpy(float)) / 3.0
    vol = rth_to_T["volume"].to_numpy(float)
    if np.nansum(vol) <= 0:
        return float(np.nanmean(tp))
    return float(np.nansum(tp * vol) / np.nansum(vol))


def opening_range(rth: pd.DataFrame, or_minutes: int = 5) -> tuple[float, float] | None:
    or_bars = rth[(rth["ny_min"] >= NY_OPEN) & (rth["ny_min"] < NY_OPEN + or_minutes)]
    if len(or_bars) < max(1, or_minutes - 1):
        return None
    return float(or_bars["high"].max()), float(or_bars["low"].min())


def structure_bias(closes: np.ndarray) -> int:
    """
    Simple causal structure from close path:
      +1 if last half makes higher high and higher low than first half
      -1 if lower high and lower low
       0 otherwise / flat
    """
    if len(closes) < 6:
        return 0
    mid = len(closes) // 2
    a, b = closes[:mid], closes[mid:]
    hh = b.max() > a.max()
    hl = b.min() > a.min()
    lh = b.max() < a.max()
    ll = b.min() < a.min()
    if hh and hl:
        return 1
    if lh and ll:
        return -1
    return 0


def find_impulse_pullback(
    rth: pd.DataFrame,
    onr: float,
    T_ny: int,
    impulse_window: int = 10,
    pullback_frac: float = 0.382,
    max_wait: int = 20,
) -> dict[str, Any] | None:
    """
    Causal impulse+pullback using only bars <= T for impulse definition when T>=impulse_window,
    then pullback confirmation in bars after impulse extreme up to T (must confirm by T).
    Signal clock = confirmation bar ny_min; outcome from next open.
    """
    if onr <= 0 or T_ny < NY_OPEN + impulse_window:
        return None
    win = rth[(rth["ny_min"] >= NY_OPEN) & (rth["ny_min"] < NY_OPEN + impulse_window)].reset_index(drop=True)
    if len(win) < impulse_window - 1:
        return None
    o0 = float(win.iloc[0]["open"])
    # impulse extreme: max displacement from open in window
    c = win["close"].to_numpy(float)
    h = win["high"].to_numpy(float)
    l = win["low"].to_numpy(float)
    up_ext = float(h.max() - o0)
    dn_ext = float(o0 - l.min())
    if max(up_ext, dn_ext) < 0.15 * onr:
        return None
    if up_ext >= dn_ext:
        direction = 1
        extreme = float(h.max())
        impulse = up_ext
        ext_i = int(np.argmax(h))
    else:
        direction = -1
        extreme = float(l.min())
        impulse = dn_ext
        ext_i = int(np.argmin(l))
    ext_ny = int(win.iloc[ext_i]["ny_min"])
    # pullback after extreme, must confirm by T
    after = rth[(rth["ny_min"] > ext_ny) & (rth["ny_min"] <= T_ny)].reset_index(drop=True)
    if len(after) == 0 or len(after) > max_wait:
        # allow shorter; reject if too long wait beyond max from extreme
        if len(after) == 0:
            return None
    pb_need = pullback_frac * impulse
    confirmed = False
    conf_ny = None
    for i in range(min(len(after), max_wait)):
        bar = after.iloc[i]
        if direction == 1:
            pb = extreme - float(bar["low"])
            # reject if closes through open (failed impulse) before pullback confirm
            if float(bar["close"]) < o0:
                return None
            if pb >= pb_need:
                confirmed = True
                conf_ny = int(bar["ny_min"])
                break
        else:
            pb = float(bar["high"]) - extreme
            if float(bar["close"]) > o0:
                return None
            if pb >= pb_need:
                confirmed = True
                conf_ny = int(bar["ny_min"])
                break
    if not confirmed or conf_ny is None:
        return None
    return {"direction": direction, "signal_ny": conf_ny, "impulse_onr": impulse / onr}


def main() -> None:
    print("=== HIGH-conditional Directional Discovery ===", flush=True)
    print(f"Frozen ARM: {GATE['primary_arm']}", flush=True)

    panel_path = art("ny_open_high_dir_panel.parquet")
    if panel_path.exists():
        panel = pd.read_parquet(panel_path)
        need_cols = {"x_impulse", "x_vwap", "x_pullback", "fwd_15", "dir_sign", "T_offset"}
        if need_cols.issubset(panel.columns) and len(panel) > 1000:
            print(f"Reusing HIGH panel {panel_path} rows={len(panel)}", flush=True)
        else:
            panel = None
    else:
        panel = None

    if panel is None:
        df = load_nq()
        print("Building day context...", flush=True)
        ctx_df = build_day_context(df)
        ctx_map = {r["session_date"]: r for _, r in ctx_df.iterrows()}
        print(f"Days: {len(ctx_df)}", flush=True)

        print("Indexing RTH...", flush=True)
        rth_map: dict = {}
        for sd, g in df.groupby("session_date", sort=False):
            if sd not in ctx_map:
                continue
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
            if len(rth) >= 100:
                rth_map[sd] = rth
        print(f"RTH days: {len(rth_map)}", flush=True)

        # Panel: one row per (day, T) where HIGH is true, plus mechanism labels + forwards
        rows: list[dict] = []
        n_days = 0
        for sd, ctx in ctx_map.items():
            rth = rth_map.get(sd)
            if rth is None:
                continue
            n_days += 1
            onr = float(ctx["onr"])
            o930 = float(ctx["open_930"])
            onh, onl = float(ctx["onh"]), float(ctx["onl"])
            open_loc = float(ctx["open_loc"])

            for off in ARM_OFFSETS:
                T = NY_OPEN + off
                to_T = rth[rth["ny_min"] <= T].reset_index(drop=True)
                st = state_at_T(to_T, ctx, T)
                if st is None:
                    continue
                if not is_high(st["rng_onr"], off):
                    continue

                fwd = fwd_from_next(rth, T)
                if fwd is None:
                    continue

                last_c = float(to_T.iloc[-1]["close"])
                closes = to_T["close"].to_numpy(float)
                dir_sign = int(st["dir_sign"]) if st["dir_sign"] != 0 else 0

                # --- Mechanism labels (direction in {-1,0,+1}; 0 = no signal) ---
                # 1) Impulse follow-through: follow open→T displacement
                x_impulse = dir_sign

                # 2) VWAP side
                vwap = session_vwap(to_T)
                if vwap is None or not np.isfinite(vwap):
                    x_vwap = 0
                else:
                    x_vwap = 1 if last_c > vwap else (-1 if last_c < vwap else 0)

                # 3) Opening-range accept/reject (5m OR; only for T >= 09:40)
                x_or_accept = 0
                x_or_reject = 0
                or_hl = opening_range(rth, 5)
                if or_hl is not None and off >= 10:
                    orh, orl = or_hl
                    # accept: close beyond OR in direction of break
                    if last_c > orh:
                        x_or_accept = 1
                    elif last_c < orl:
                        x_or_accept = -1
                    # reject: traded beyond OR earlier then closed back inside
                    touched_hi = bool((to_T["high"] > orh).any())
                    touched_lo = bool((to_T["low"] < orl).any())
                    inside = orl <= last_c <= orh
                    if inside and touched_hi and not touched_lo:
                        x_or_reject = -1  # fade failed upside
                    elif inside and touched_lo and not touched_hi:
                        x_or_reject = 1  # fade failed downside
                    elif inside and touched_hi and touched_lo:
                        x_or_reject = 0  # ambiguous both sides

                # 4) Structure
                x_structure = structure_bias(closes)

                # 5) Overnight positioning
                x_on_continue = 0
                x_on_fade = 0
                if open_loc >= 0.80:
                    x_on_continue = 1
                    x_on_fade = -1
                elif open_loc <= 0.20:
                    x_on_continue = -1
                    x_on_fade = 1
                x_loc_continue = 0
                x_loc_fade = 0
                loc_now = float(st["loc_now"])
                if loc_now >= 0.90:
                    x_loc_continue = 1
                    x_loc_fade = -1
                elif loc_now <= 0.10:
                    x_loc_continue = -1
                    x_loc_fade = 1

                # 6) Impulse + pullback
                pb = find_impulse_pullback(rth, onr, T)
                x_pullback = 0
                pb_clock = T
                pb_fwd = None
                if pb is not None:
                    x_pullback = int(pb["direction"])
                    pb_clock = int(pb["signal_ny"])
                    pb_fwd = fwd_from_next(rth, pb_clock)

                base = {
                    "session_date": str(sd),
                    "year": int(ctx["year"]),
                    "dow": int(ctx["dow"]),
                    "split": str(ctx["split"]),
                    "T_offset": off,
                    "T_ny": T,
                    "onr": onr,
                    "rng_onr": float(st["rng_onr"]),
                    "dir_sign": dir_sign,
                    "open_loc": open_loc,
                    "loc_now": float(st["loc_now"]),
                    "x_impulse": x_impulse,
                    "x_vwap": x_vwap,
                    "x_or_accept": x_or_accept,
                    "x_or_reject": x_or_reject,
                    "x_structure": x_structure,
                    "x_on_continue": x_on_continue,
                    "x_on_fade": x_on_fade,
                    "x_loc_continue": x_loc_continue,
                    "x_loc_fade": x_loc_fade,
                    "x_pullback": x_pullback,
                    "pb_clock_ny": float(pb_clock),
                    **{f"fwd_{H}": fwd[f"fwd_{H}"] for H in HORIZONS},
                    **{f"mfe_{H}": fwd[f"mfe_{H}"] for H in HORIZONS},
                    **{f"mae_{H}": fwd[f"mae_{H}"] for H in HORIZONS},
                }
                for H in HORIZONS:
                    if pb_fwd is None:
                        base[f"pb_fwd_{H}"] = np.nan
                        base[f"pb_mfe_{H}"] = np.nan
                        base[f"pb_mae_{H}"] = np.nan
                    else:
                        base[f"pb_fwd_{H}"] = pb_fwd[f"fwd_{H}"]
                        base[f"pb_mfe_{H}"] = pb_fwd[f"mfe_{H}"]
                        base[f"pb_mae_{H}"] = pb_fwd[f"mae_{H}"]

                rows.append(base)

            if n_days % 500 == 0:
                print(f"  processed {n_days} days, HIGH rows={len(rows)}", flush=True)

        panel = pd.DataFrame(rows)
        panel.to_parquet(panel_path, index=False)
        print(
            f"HIGH panel rows: {len(panel)}  days_touched~{panel['session_date'].nunique()}  -> {panel_path}",
            flush=True,
        )

    mechanisms = [
        ("impulse_follow", "x_impulse", False),
        ("vwap_side", "x_vwap", False),
        ("or5_accept", "x_or_accept", False),
        ("or5_reject", "x_or_reject", False),
        ("structure_hhhl", "x_structure", False),
        ("on_open_continue", "x_on_continue", False),
        ("on_open_fade", "x_on_fade", False),
        ("loc_now_continue", "x_loc_continue", False),
        ("loc_now_fade", "x_loc_fade", False),
        ("impulse_pullback", "x_pullback", True),
    ]

    def signed_series(df: pd.DataFrame, direction_col: str, H: int, pullback: bool) -> pd.Series:
        if pullback:
            return df[f"pb_fwd_{H}"] * df[direction_col]
        return df[f"fwd_{H}"] * df[direction_col]

    def payoff_stats(signed: np.ndarray, mfe: np.ndarray, mae: np.ndarray) -> dict[str, float]:
        signed = signed[np.isfinite(signed)]
        if len(signed) == 0:
            return {"n": 0}
        # path: did MFE exceed MAE in trade direction proxy via signed excursion ratio
        # use mfe/mae arrays aligned — caller passes direction-adjusted
        out = {
            "n": int(len(signed)),
            "win": float(np.mean(signed > 0)),
            "mean": float(np.mean(signed)),
            "median": float(np.median(signed)),
            "p_abs_gt_10": float(np.mean(np.abs(signed) >= 10)),
        }
        mfe = mfe[np.isfinite(mfe)]
        mae = mae[np.isfinite(mae)]
        if len(mfe) and len(mae) and len(mfe) == len(mae):
            out["mean_mfe"] = float(np.mean(mfe))
            out["mean_mae"] = float(np.mean(mae))
            out["mfe_gt_mae"] = float(np.mean(mfe > mae))
        return out

    results: list[dict[str, Any]] = []

    # HIGH-alone baselines at each (T,H,split)
    for off in ARM_OFFSETS:
        sub = panel[panel["T_offset"] == off]
        if len(sub) < 50:
            continue
        for split in ("IS", "Validation", "OOS", "ALL"):
            base = sub if split == "ALL" else sub[sub["split"] == split]
            if len(base) < 30:
                continue
            for H in HORIZONS:
                # long baseline
                long_s = base[f"fwd_{H}"].to_numpy(float)
                # follow baseline (dir_sign)
                follow = base[base["dir_sign"] != 0]
                follow_s = (follow[f"fwd_{H}"] * follow["dir_sign"]).to_numpy(float)
                results.append(
                    {
                        "mechanism": "HIGH_ALONE_LONG",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(np.isfinite(long_s).sum()),
                        "rate": 1.0,
                        "win": float(np.nanmean(long_s > 0)),
                        "mean": float(np.nanmean(long_s)),
                        "median": float(np.nanmedian(long_s)),
                        "mean_mfe": float(np.nanmean(base[f"mfe_{H}"])),
                        "mean_mae": float(np.nanmean(base[f"mae_{H}"])),
                        "mfe_gt_mae": float(np.nanmean(base[f"mfe_{H}"] > base[f"mae_{H}"])),
                    }
                )
                results.append(
                    {
                        "mechanism": "HIGH_ALONE_FOLLOW",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(np.isfinite(follow_s).sum()),
                        "rate": float(len(follow) / len(base)) if len(base) else np.nan,
                        "win": float(np.nanmean(follow_s > 0)) if len(follow_s) else np.nan,
                        "mean": float(np.nanmean(follow_s)) if len(follow_s) else np.nan,
                        "median": float(np.nanmedian(follow_s)) if len(follow_s) else np.nan,
                        "mean_mfe": float(np.nanmean(follow[f"mfe_{H}"])) if len(follow) else np.nan,
                        "mean_mae": float(np.nanmean(follow[f"mae_{H}"])) if len(follow) else np.nan,
                        "mfe_gt_mae": float(np.nanmean(follow[f"mfe_{H}"] > follow[f"mae_{H}"])) if len(follow) else np.nan,
                    }
                )

    # HIGH + X
    for mech, col, is_pb in mechanisms:
        for off in ARM_OFFSETS:
            sub = panel[panel["T_offset"] == off]
            if len(sub) < 50:
                continue
            sig = sub[sub[col] != 0]
            if len(sig) < 30:
                continue
            for split in ("IS", "Validation", "OOS", "ALL"):
                base_all = sub if split == "ALL" else sub[sub["split"] == split]
                s = sig if split == "ALL" else sig[sig["split"] == split]
                if len(s) < 25:
                    continue
                for H in HORIZONS:
                    signed = signed_series(s, col, H, is_pb).to_numpy(float)
                    # MFE/MAE in trade direction
                    if is_pb:
                        mfe_raw = s[f"pb_mfe_{H}"].to_numpy(float)
                        mae_raw = s[f"pb_mae_{H}"].to_numpy(float)
                    else:
                        mfe_raw = s[f"mfe_{H}"].to_numpy(float)
                        mae_raw = s[f"mae_{H}"].to_numpy(float)
                    dirc = s[col].to_numpy(float)
                    # when short, swap mfe/mae
                    mfe_dir = np.where(dirc > 0, mfe_raw, mae_raw)
                    mae_dir = np.where(dirc > 0, mae_raw, mfe_raw)
                    stt = payoff_stats(signed, mfe_dir, mae_dir)

                    # baselines at same T/H/split
                    follow_base = [
                        r
                        for r in results
                        if r["mechanism"] == "HIGH_ALONE_FOLLOW"
                        and r["T_offset"] == off
                        and r["horizon"] == H
                        and r["split"] == split
                    ]
                    long_base = [
                        r
                        for r in results
                        if r["mechanism"] == "HIGH_ALONE_LONG"
                        and r["T_offset"] == off
                        and r["horizon"] == H
                        and r["split"] == split
                    ]
                    fb = follow_base[0] if follow_base else {}
                    lb = long_base[0] if long_base else {}
                    d_follow = (
                        stt["win"] - float(fb["win"])
                        if stt.get("n") and isinstance(fb.get("win"), (int, float)) and np.isfinite(fb["win"])
                        else np.nan
                    )
                    d_follow_mean = (
                        stt["mean"] - float(fb["mean"])
                        if stt.get("n")
                        and isinstance(fb.get("mean"), (int, float))
                        and np.isfinite(fb["mean"])
                        else np.nan
                    )
                    d_long = (
                        stt["win"] - float(lb["win"])
                        if stt.get("n") and isinstance(lb.get("win"), (int, float)) and np.isfinite(lb["win"])
                        else np.nan
                    )

                    results.append(
                        {
                            "mechanism": mech,
                            "T_offset": off,
                            "horizon": H,
                            "split": split,
                            "n": stt.get("n", 0),
                            "n_high": int(len(base_all)),
                            "rate": float(len(s) / len(base_all)) if len(base_all) else np.nan,
                            "win": stt.get("win", np.nan),
                            "mean": stt.get("mean", np.nan),
                            "median": stt.get("median", np.nan),
                            "mean_mfe": stt.get("mean_mfe", np.nan),
                            "mean_mae": stt.get("mean_mae", np.nan),
                            "mfe_gt_mae": stt.get("mfe_gt_mae", np.nan),
                            "delta_win_vs_follow": d_follow,
                            "delta_mean_vs_follow": d_follow_mean,
                            "delta_win_vs_long": d_long,
                            "follow_win": fb.get("win"),
                            "follow_mean": fb.get("mean"),
                            "long_win": lb.get("win"),
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("ny_open_high_dir_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

    # --- Year breaks + scoring ---
    def year_mech(mech: str, off: int, H: int, col: str, is_pb: bool) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for y in (2025, 2026):
            s = panel[(panel["T_offset"] == off) & (panel["year"] == y) & (panel[col] != 0)]
            if len(s) < 15:
                out[f"y{y}_n"] = len(s)
                out[f"y{y}_win"] = np.nan
                out[f"y{y}_mean"] = np.nan
                continue
            signed = signed_series(s, col, H, is_pb).to_numpy(float)
            signed = signed[np.isfinite(signed)]
            out[f"y{y}_n"] = int(len(signed))
            out[f"y{y}_win"] = float(np.mean(signed > 0)) if len(signed) else np.nan
            out[f"y{y}_mean"] = float(np.mean(signed)) if len(signed) else np.nan
        return out

    def year_follow(off: int, H: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for y in (2025, 2026):
            s = panel[(panel["T_offset"] == off) & (panel["year"] == y) & (panel["dir_sign"] != 0)]
            signed = (s[f"fwd_{H}"] * s["dir_sign"]).to_numpy(float)
            signed = signed[np.isfinite(signed)]
            out[f"y{y}_follow_win"] = float(np.mean(signed > 0)) if len(signed) else np.nan
            out[f"y{y}_follow_n"] = int(len(signed))
        return out

    candidates: list[dict[str, Any]] = []
    is_mech = res_df[(res_df["split"] == "IS") & (~res_df["mechanism"].str.startswith("HIGH_ALONE"))]
    for _, r in is_mech.iterrows():
        mech = str(r["mechanism"])
        off, H = int(r["T_offset"]), int(r["horizon"])
        if int(r["n"]) < 80:
            continue
        val = res_df[
            (res_df["mechanism"] == mech)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "Validation")
        ]
        oos = res_df[
            (res_df["mechanism"] == mech)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "OOS")
        ]
        if len(val) == 0 or len(oos) == 0:
            continue
        v, o = val.iloc[0], oos.iloc[0]
        if int(v["n"]) < 40 or int(o["n"]) < 30:
            continue

        col = next(c for m, c, _ in mechanisms if m == mech)
        is_pb = next(pb for m, _, pb in mechanisms if m == mech)
        yrs = year_mech(mech, off, H, col, is_pb)
        yf = year_follow(off, H)

        is_win, v_win, o_win = float(r["win"]), float(v["win"]), float(o["win"])
        is_d = float(r["delta_win_vs_follow"]) if np.isfinite(r.get("delta_win_vs_follow", np.nan)) else np.nan
        v_d = float(v["delta_win_vs_follow"]) if np.isfinite(v.get("delta_win_vs_follow", np.nan)) else np.nan
        o_d = float(o["delta_win_vs_follow"]) if np.isfinite(o.get("delta_win_vs_follow", np.nan)) else np.nan
        is_mean = float(r["mean"])
        v_mean, o_mean = float(v["mean"]), float(o["mean"])

        y25, y26 = yrs.get("y2025_win"), yrs.get("y2026_win")
        y25n, y26n = yrs.get("y2025_n", 0), yrs.get("y2026_n", 0)
        year_ok = (
            isinstance(y25, (int, float))
            and isinstance(y26, (int, float))
            and np.isfinite(y25)
            and np.isfinite(y26)
            and y25n >= 20
            and y26n >= 20
            and y25 >= 0.50
            and y26 >= 0.50
            and abs(y25 - y26) <= 0.15  # no violent flip
        )

        # Lift vs HIGH follow baseline
        lift_ok = (
            np.isfinite(is_d)
            and is_d >= 0.03
            and np.isfinite(v_d)
            and v_d > 0
            and np.isfinite(o_d)
            and o_d > 0
        )
        # Absolute directional quality
        abs_ok = is_win >= 0.53 and v_win >= 0.52 and o_win >= 0.52
        # Payoff: mean should not be wrong-signed if win > 50
        payoff_ok = is_mean > 0 and v_mean > 0 and o_mean > 0

        strong = lift_ok and abs_ok and year_ok and payoff_ok and is_d >= 0.05
        soft = (
            ((lift_ok and is_d >= 0.03) or (abs_ok and is_win >= 0.545))
            and year_ok
            and (is_mean >= 0 or (np.isfinite(r.get("mfe_gt_mae", np.nan)) and r["mfe_gt_mae"] >= 0.52))
            and v_win >= 0.50
            and o_win >= 0.50
        )

        if strong or soft:
            candidates.append(
                {
                    "mechanism": mech,
                    "T_offset": off,
                    "horizon": H,
                    "tier": "strong" if strong else "soft",
                    "IS_n": int(r["n"]),
                    "IS_rate": float(r["rate"]),
                    "IS_win": is_win,
                    "IS_mean": is_mean,
                    "IS_delta_vs_follow": is_d,
                    "IS_follow_win": float(r["follow_win"]) if np.isfinite(r.get("follow_win", np.nan)) else None,
                    "Val_win": v_win,
                    "Val_mean": v_mean,
                    "Val_delta": v_d,
                    "OOS_win": o_win,
                    "OOS_mean": o_mean,
                    "OOS_delta": o_d,
                    "y2025_win": y25,
                    "y2026_win": y26,
                    "y2025_n": y25n,
                    "y2026_n": y26n,
                    "IS_mfe_gt_mae": float(r["mfe_gt_mae"]) if np.isfinite(r.get("mfe_gt_mae", np.nan)) else None,
                    "year_ok": year_ok,
                }
            )

    candidates.sort(
        key=lambda x: (
            0 if x["tier"] == "strong" else 1,
            -(x["IS_delta_vs_follow"] if np.isfinite(x["IS_delta_vs_follow"]) else -1),
            -x["IS_n"],
        )
    )

    # Clock stability per mechanism
    stability = []
    if candidates:
        cdf = pd.DataFrame(candidates)
        for (mech, H), g in cdf.groupby(["mechanism", "horizon"]):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            stability.append(
                {
                    "mechanism": mech,
                    "horizon": int(H),
                    "n_clocks": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "median_IS_win": float(g["IS_win"].median()),
                    "median_IS_delta": float(g["IS_delta_vs_follow"].median()),
                    "median_OOS_win": float(g["OOS_win"].median()),
                }
            )
        stability.sort(key=lambda x: (-x["n_clocks_strong"], -x["n_clocks"], -x["median_IS_delta"]))

    # HIGH alone summary table
    high_alone = []
    for off in (15, 30, 45, 60):
        for H in (15, 30):
            for mech in ("HIGH_ALONE_FOLLOW", "HIGH_ALONE_LONG"):
                row = {"mechanism": mech, "T_offset": off, "horizon": H}
                for split in ("IS", "Validation", "OOS"):
                    s = res_df[
                        (res_df["mechanism"] == mech)
                        & (res_df["T_offset"] == off)
                        & (res_df["horizon"] == H)
                        & (res_df["split"] == split)
                    ]
                    if len(s):
                        row[f"{split}_n"] = int(s.iloc[0]["n"])
                        row[f"{split}_win"] = float(s.iloc[0]["win"])
                        row[f"{split}_mean"] = float(s.iloc[0]["mean"])
                high_alone.append(row)

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    multi = [s for s in stability if s["n_clocks"] >= 3]

    if strong_n > 0 and multi:
        verdict = "A_directional_inside_HIGH"
        verdict_text = (
            "At least one independent X creates stable directional lift inside frozen HIGH "
            "vs HIGH-alone follow baseline."
        )
    elif strong_n > 0 or (soft_n > 0 and multi):
        verdict = "B_weak_directional_inside_HIGH"
        verdict_text = (
            "Soft / narrow directional leftovers exist inside HIGH, but nothing clears a "
            "strong multi-clock year-stable bar. Gate remains; direction still missing."
        )
    else:
        verdict = "C_no_directional_inside_HIGH"
        verdict_text = (
            "Inside frozen HIGH, no tested independent X reliably reprices direction "
            "beyond HIGH-alone. Opportunity gate stands; directional layer not found."
        )

    report = {
        "stage": "high_conditional_directional_discovery",
        "verdict": verdict,
        "verdict_text": verdict_text,
        "frozen_gate": GATE,
        "hierarchy": "causal → stable → economically meaningful → executable → profitable",
        "panel": {
            "rows": int(len(panel)),
            "high_days": int(panel["session_date"].nunique()),
        },
        "n_strong": strong_n,
        "n_soft": soft_n,
        "high_alone_baselines": high_alone,
        "top_candidates": candidates[:30],
        "stability": stability[:20],
        "mechanisms_tested": [m[0] for m in mechanisms],
        "kill_criteria": {
            "strong": (
                "IS win>=53%, delta_vs_HIGH_follow>=5pp, Val&OOS delta>0 & win>=52%, "
                "means>0, 2025&2026 win>=50% n>=20 |Δyear|<=15pp"
            ),
            "soft": "weaker lift/absolute with year stability",
        },
    }
    with open(art("ny_open_high_dir_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pts(x: Any) -> str:
        return f"{x:+.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md: list[str] = []
    md.append("# NQ HIGH-conditional Directional Discovery")
    md.append("")
    md.append(f"**Verdict: `{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    md.append(
        f"Frozen ARM: **`{GATE['primary_arm']}`** "
        f"(see `artifacts/frozen_opportunity_gate.md`). Gate was **not** re-tuned."
    )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Question")
    md.append("")
    md.append("> Inside HIGH only, does independent X create directional asymmetry beyond HIGH alone?")
    md.append("")
    md.append("Each X tested separately. No combinations. Hierarchy: causal → stable → meaningful.")
    md.append("")
    md.append("## Protocol")
    md.append("")
    md.append("| Rule | Implementation |")
    md.append("|------|----------------|")
    md.append("| Universe | rows where `vol_expansion_high` at T |")
    md.append("| Clocks | every 5m from 09:40–11:00 |")
    md.append("| Baseline | HIGH alone LONG + HIGH alone FOLLOW (`dir_sign`) |")
    md.append("| Outcome | next-bar open → H∈{10,15,30} signed by X direction |")
    md.append("| Compare | HIGH+X win/mean vs HIGH FOLLOW at same T,H |")
    md.append("| Splits | IS / Val / OOS + 2025 / 2026 |")
    md.append("")
    md.append(
        f"HIGH panel: **{len(panel):,}** rows · **{panel['session_date'].nunique():,}** days with ≥1 HIGH clock."
    )
    md.append("")
    md.append("## HIGH-alone baselines")
    md.append("")
    md.append("| Mech | T+ | H | IS win / mean | Val | OOS |")
    md.append("|------|----|---|---------------|-----|-----|")
    for row in high_alone:
        md.append(
            f"| `{row['mechanism']}` | +{row['T_offset']}m | {row['horizon']} | "
            f"{pct(row.get('IS_win'))} / {pts(row.get('IS_mean'))} | "
            f"{pct(row.get('Validation_win'))} / {pts(row.get('Validation_mean'))} | "
            f"{pct(row.get('OOS_win'))} / {pts(row.get('OOS_mean'))} |"
        )
    md.append("")
    md.append("## Mechanisms tested (independent)")
    md.append("")
    for m, _, _ in mechanisms:
        md.append(f"- `{m}`")
    md.append("")
    md.append("## Candidates")
    md.append("")
    md.append(f"Strong: **{strong_n}** · Soft: **{soft_n}**")
    md.append("")
    if not candidates:
        md.append("**None** cleared soft/strong bars.")
    else:
        md.append(
            "| Tier | X | T+ | H | IS n | IS win | Δfollow | Val | OOS | 2025 | 2026 |"
        )
        md.append(
            "|------|---|----|---|------|--------|---------|-----|-----|------|------|"
        )
        for c in candidates[:25]:
            md.append(
                f"| {c['tier']} | `{c['mechanism']}` | +{c['T_offset']}m | {c['horizon']} | "
                f"{c['IS_n']} | {pct(c['IS_win'])} | {pp(c['IS_delta_vs_follow'])} | "
                f"{pct(c['Val_win'])} | {pct(c['OOS_win'])} | "
                f"{pct(c.get('y2025_win'))} | {pct(c.get('y2026_win'))} |"
            )
        md.append("")

    md.append("## Clock stability")
    md.append("")
    if not stability:
        md.append("No candidate mechanisms with multi-cell presence.")
    else:
        md.append("| X | H | clocks | strong clocks | med IS win | med Δfollow | med OOS win |")
        md.append("|---|---|--------|---------------|------------|-------------|-------------|")
        for s in stability[:15]:
            md.append(
                f"| `{s['mechanism']}` | {s['horizon']} | {s['n_clocks']} | {s['n_clocks_strong']} | "
                f"{pct(s['median_IS_win'])} | {pp(s['median_IS_delta'])} | {pct(s['median_OOS_win'])} |"
            )
        md.append("")

    md.append("## Stage verdict")
    md.append("")
    md.append(f"**`{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    md.append("### Architecture status")
    md.append("")
    md.append("```")
    md.append("09:30–11:00 → HIGH? → NO: WAIT / YES: ARM")
    md.append("             → independent X? → (this stage)")
    md.append("             → mechanical execution → (not yet)")
    md.append("```")
    md.append("")
    md.append("### Explicit non-actions")
    md.append("")
    md.append("- Do not unfreeze or re-optimize the HIGH gate")
    md.append("- Do not combine X mechanisms until each clears alone")
    md.append("- Do not convert soft leftovers into a strategy")
    md.append("- Do not demand 60%+ win rate; demand stability first")
    md.append("")
    md.append("## Artifacts")
    md.append("")
    md.append("- `artifacts/frozen_opportunity_gate.md`")
    md.append("- `artifacts/frozen_opportunity_gate.json`")
    md.append("- `artifacts/ny_open_high_dir_panel.parquet`")
    md.append("- `artifacts/ny_open_high_dir_results.csv`")
    md.append("- `artifacts/ny_open_high_dir_report.json`")
    md.append("- `run_ny_open_high_directional.py`")
    md.append("")

    md_path = art("ny_open_high_dir_report.md")
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {md_path}", flush=True)
    print(f"VERDICT: {verdict}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n}", flush=True)


if __name__ == "__main__":
    main()
