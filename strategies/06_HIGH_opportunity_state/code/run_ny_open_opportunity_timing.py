"""
NQ Structural Opportunity Timing (09:30–11:00 ET)

Prior kills: direction, level confirmation, raw magnitude, year-stable path asymmetry.
Soft leftover from path-asym stage: quiet_wait cut structural resolution ~11–23pp.

This stage asks only:
  Can causal morning states reliably reprice P(structural move within H)
  vs same-TOD unconditional — across IS / Val / OOS / 2025 / 2026?

NO entries. NO targets. NO direction. NO strategy conversion. NO threshold mining.

Structural resolution (pre-specified, not fit on outcomes):
  From next-bar open after T, within horizon H:
    max(high_max - entry, entry - low_min) >= STRUCT_FRAC * ONR
  STRUCT_FRAC = 0.25 (a priori from prior stage). Sensitivity at 0.15 / 0.35 reported, not optimized.
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
)

warnings.filterwarnings("ignore", category=FutureWarning)

# Opportunity horizons (minutes)
OPP_HORIZONS = (10, 15, 20, 30, 45)
# Pre-specified structural fractions of ONR (primary = 0.25)
STRUCT_FRACS = (0.15, 0.25, 0.35)
PRIMARY_FRAC = 0.25

# Regime labels for discrimination
LOW_STATES = (
    "quiet_wait",
    "vol_expansion_low",
    "weak_dir_move",
    "low_local_vol",
    "slow_move",
    "wide_ON_quiet_open",
)
HIGH_STATES = (
    "vol_expansion_high",
    "strong_dir_move",
    "fast_move",
    "fast_and_expanded",
    "strong_and_persistent",
    "path_vs_ON_high",
    "high_local_vol",
    "compress_then_expand",
)


def structural_resolved(
    rth_full: pd.DataFrame,
    T_ny: int,
    onr: float,
    frac: float,
    horizons: tuple[int, ...],
) -> dict[str, float] | None:
    """Unsigned structural opportunity: either-side max excursion >= frac*ONR within H."""
    after = rth_full[rth_full["ny_min"] > T_ny].reset_index(drop=True)
    need = max(horizons)
    if len(after) < need or onr <= 0:
        return None
    entry = float(after.iloc[0]["open"])
    thr = frac * onr
    highs = after["high"].to_numpy(float)
    lows = after["low"].to_numpy(float)
    out: dict[str, float] = {"entry": entry, "thr_pts": thr}
    for H in horizons:
        mfe = float(highs[:H].max() - entry)
        mae = float(entry - lows[:H].min())
        mx = max(mfe, mae)
        out[f"max_exc_{H}"] = mx
        out[f"max_exc_onr_{H}"] = mx / onr
        out[f"resolved_f{frac:g}_{H}"] = 1.0 if mx >= thr else 0.0
        # time to structural resolution (first bar where running max excursion hits thr)
        t_hit = np.nan
        run_max = 0.0
        for i in range(H):
            run_max = max(run_max, highs[i] - entry, entry - lows[i])
            if run_max >= thr:
                t_hit = float(i + 1)
                break
        out[f"t_resolve_f{frac:g}_{H}"] = t_hit
    return out


def conditions_for(
    sub: pd.DataFrame,
    off: int,
    thresholds: dict[str, dict[int, dict[str, float]]],
) -> dict[str, pd.Series]:
    features = list(thresholds.keys())
    th = {feat: thresholds.get(feat, {}).get(off, {}) for feat in features}
    c: dict[str, pd.Series] = {}
    if th.get("rng_onr"):
        c["vol_expansion_high"] = sub["rng_onr"] >= th["rng_onr"]["p66"]
        c["vol_expansion_low"] = sub["rng_onr"] <= th["rng_onr"]["p33"]
    if th.get("onr_vs_med") and th.get("rng_onr"):
        c["compress_then_expand"] = (sub["onr_vs_med"] <= th["onr_vs_med"]["p33"]) & (
            sub["rng_onr"] >= th["rng_onr"]["p66"]
        )
        c["wide_ON_quiet_open"] = (sub["onr_vs_med"] >= th["onr_vs_med"]["p66"]) & (
            sub["rng_onr"] <= th["rng_onr"]["p33"]
        )
    if th.get("abs_move_onr"):
        c["strong_dir_move"] = (sub["abs_move_onr"] >= th["abs_move_onr"]["p66"]) & (
            sub["dir_sign"] != 0
        )
        c["weak_dir_move"] = sub["abs_move_onr"] <= th["abs_move_onr"]["p33"]
    if th.get("persist_frac"):
        c["high_persistence"] = (sub["persist_frac"] >= th["persist_frac"]["p66"]) & (
            sub["dir_sign"] != 0
        )
        c["low_persistence"] = (sub["persist_frac"] <= th["persist_frac"]["p33"]) & (
            sub["dir_sign"] != 0
        )
    if th.get("speed"):
        c["fast_move"] = (sub["speed"] >= th["speed"]["p66"]) & (sub["dir_sign"] != 0)
        c["slow_move"] = sub["speed"] <= th["speed"]["p33"]
    if th.get("open_loc"):
        c["open_near_ONH"] = sub["open_loc"] >= 0.80
        c["open_near_ONL"] = sub["open_loc"] <= 0.20
        c["open_mid"] = (sub["open_loc"] > 0.40) & (sub["open_loc"] < 0.60)
    c["price_near_ONH"] = sub["loc_now"] >= 0.90
    c["price_near_ONL"] = sub["loc_now"] <= 0.10
    if th.get("path_vs_onrv"):
        c["path_vs_ON_high"] = sub["path_vs_onrv"] >= th["path_vs_onrv"]["p66"]
    if th.get("vol_unit_onr"):
        c["high_local_vol"] = sub["vol_unit_onr"] >= th["vol_unit_onr"]["p66"]
        c["low_local_vol"] = sub["vol_unit_onr"] <= th["vol_unit_onr"]["p33"]
    if "strong_dir_move" in c and "high_persistence" in c:
        c["strong_and_persistent"] = c["strong_dir_move"] & c["high_persistence"]
    if "strong_dir_move" in c and "low_persistence" in c:
        c["strong_but_choppy"] = c["strong_dir_move"] & c["low_persistence"]
    if "fast_move" in c and "vol_expansion_high" in c:
        c["fast_and_expanded"] = c["fast_move"] & c["vol_expansion_high"]
    if "vol_expansion_low" in c and "weak_dir_move" in c:
        c["quiet_wait"] = c["vol_expansion_low"] & c["weak_dir_move"]
    return c


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pp(x: Any) -> str:
    return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== NQ Structural Opportunity Timing ===", flush=True)
    panel_path = art("ny_open_opp_timing_panel.parquet")

    # Always rebuild: horizons include 45m and multi-frac outcomes not in prior panel
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
        # need through 11:00 + 45m = 11:45; keep to noon
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
        if len(rth) >= 100:
            rth_map[sd] = rth
    print(f"RTH days: {len(rth_map)}", flush=True)

    rows: list[dict] = []
    n_days = 0
    for sd, ctx in ctx_map.items():
        rth = rth_map.get(sd)
        if rth is None:
            continue
        n_days += 1
        for off in DECISION_OFFSETS:
            T = NY_OPEN + off
            to_T = rth[rth["ny_min"] <= T]
            st = state_at_T(to_T, ctx, T)
            if st is None:
                continue
            # primary outcomes for all fracs
            packed: dict[str, float] = {}
            ok = True
            for frac in STRUCT_FRACS:
                out = structural_resolved(rth, T, st["onr"], frac, OPP_HORIZONS)
                if out is None:
                    ok = False
                    break
                packed.update(out)
            if not ok:
                continue
            rows.append(
                {
                    "session_date": str(sd),
                    "year": int(ctx["year"]),
                    "dow": int(ctx["dow"]),
                    "split": ctx["split"],
                    "T_offset": off,
                    "T_ny": T,
                    **st,
                    **packed,
                }
            )
        if n_days % 500 == 0:
            print(f"  processed {n_days} days, panel={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(panel_path, index=False)
    print(f"Panel rows: {len(panel)}  days: {n_days}  -> {panel_path}", flush=True)

    # IS terciles (state thresholds only — structural frac is pre-specified)
    features = [
        "rng_onr",
        "abs_move_onr",
        "path_onr",
        "speed",
        "onr_vs_med",
        "persist_frac",
        "open_loc",
        "loc_now",
        "path_vs_onrv",
        "gap_onr",
        "vol_unit_onr",
    ]
    thresholds: dict[str, dict[int, dict[str, float]]] = {}
    is_p = panel[panel["split"] == "IS"]
    for feat in features:
        thresholds[feat] = {}
        for off in DECISION_OFFSETS:
            s = is_p.loc[is_p["T_offset"] == off, feat].dropna()
            if len(s) < 100:
                continue
            thresholds[feat][off] = {
                "p33": float(s.quantile(0.33)),
                "p66": float(s.quantile(0.66)),
            }
    with open(art("ny_open_opp_timing_thresholds_IS.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "state_terciles": thresholds,
                "structural_frac_primary": PRIMARY_FRAC,
                "structural_fracs_sensitivity": list(STRUCT_FRACS),
                "note": "STRUCT_FRAC pre-specified; not fit on forward outcomes",
            },
            f,
            indent=2,
        )

    # --- Metrics: condition × T × H × frac × split ---
    results: list[dict[str, Any]] = []
    for off in DECISION_OFFSETS:
        sub = panel[panel["T_offset"] == off].copy()
        if len(sub) < 200:
            continue
        conds = conditions_for(sub, off, thresholds)
        conds = {"UNCONDITIONAL": pd.Series(True, index=sub.index), **conds}

        for cname, mask in conds.items():
            for split in ("IS", "Validation", "OOS", "ALL"):
                base = sub if split == "ALL" else sub[sub["split"] == split]
                m = mask.reindex(base.index).fillna(False)
                cond = base.loc[m.to_numpy()]
                unc = base
                if cname != "UNCONDITIONAL" and len(cond) < 40:
                    continue
                if len(cond) < 20:
                    continue
                for frac in STRUCT_FRACS:
                    for H in OPP_HORIZONS:
                        col = f"resolved_f{frac:g}_{H}"
                        cr = rate_of(cond[col])
                        ur = rate_of(unc[col])
                        if not cr["n"] or not ur["n"]:
                            continue
                        delta = cr["rate"] - ur["rate"]
                        tcol = f"t_resolve_f{frac:g}_{H}"
                        tt = cond[tcol].to_numpy(float)
                        tt = tt[np.isfinite(tt)]
                        results.append(
                            {
                                "condition": cname,
                                "regime": (
                                    "LOW"
                                    if cname in LOW_STATES
                                    else ("HIGH" if cname in HIGH_STATES else "OTHER")
                                ),
                                "T_offset": off,
                                "horizon": H,
                                "frac": frac,
                                "split": split,
                                "n": int(len(cond)),
                                "n_unc": int(len(unc)),
                                "rate": float(len(cond) / len(unc)),
                                "p_resolve": cr["rate"],
                                "unc_p_resolve": ur["rate"],
                                "delta": delta,
                                "mean_t_resolve_if_hit": float(np.mean(tt)) if len(tt) else np.nan,
                                "mean_max_exc_onr": float(
                                    np.nanmean(cond[f"max_exc_onr_{H}"].to_numpy(float))
                                ),
                            }
                        )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("ny_open_opp_timing_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

    def slice_metrics(cname: str, off: int, H: int, frac: float) -> dict[str, Any]:
        out: dict[str, Any] = {"condition": cname, "T_offset": off, "horizon": H, "frac": frac}
        for split in ("IS", "Validation", "OOS"):
            s = res_df[
                (res_df["condition"] == cname)
                & (res_df["T_offset"] == off)
                & (res_df["horizon"] == H)
                & (res_df["frac"] == frac)
                & (res_df["split"] == split)
            ]
            if len(s) == 0:
                out[f"{split}_n"] = 0
                out[f"{split}_p"] = np.nan
                out[f"{split}_delta"] = np.nan
                out[f"{split}_rate"] = np.nan
                continue
            r = s.iloc[0]
            out[f"{split}_n"] = int(r["n"])
            out[f"{split}_p"] = float(r["p_resolve"])
            out[f"{split}_delta"] = float(r["delta"])
            out[f"{split}_rate"] = float(r["rate"])
            out[f"{split}_unc"] = float(r["unc_p_resolve"])
        return out

    def year_rates(cname: str, off: int, H: int, frac: float) -> dict[str, Any]:
        sub = panel[(panel["T_offset"] == off) & (panel["year"].isin([2025, 2026]))].copy()
        out: dict[str, Any] = {}
        if len(sub) == 0:
            return {"y2025": np.nan, "y2025_n": 0, "y2026": np.nan, "y2026_n": 0, "y2025_delta": np.nan, "y2026_delta": np.nan}
        conds = conditions_for(sub, off, thresholds)
        col = f"resolved_f{frac:g}_{H}"
        unc25 = rate_of(sub.loc[sub["year"] == 2025, col])
        unc26 = rate_of(sub.loc[sub["year"] == 2026, col])
        if cname == "UNCONDITIONAL":
            out["y2025"] = unc25["rate"]
            out["y2025_n"] = unc25["n"]
            out["y2026"] = unc26["rate"]
            out["y2026_n"] = unc26["n"]
            out["y2025_delta"] = 0.0
            out["y2026_delta"] = 0.0
            return out
        if cname not in conds:
            return {"y2025": np.nan, "y2025_n": 0, "y2026": np.nan, "y2026_n": 0, "y2025_delta": np.nan, "y2026_delta": np.nan}
        mask = conds[cname]
        hit = sub.loc[mask.reindex(sub.index).fillna(False).to_numpy()]
        for y, unc in ((2025, unc25), (2026, unc26)):
            hy = hit[hit["year"] == y]
            rr = rate_of(hy[col])
            out[f"y{y}"] = rr["rate"]
            out[f"y{y}_n"] = rr["n"]
            out[f"y{y}_delta"] = (
                rr["rate"] - unc["rate"] if rr["n"] and unc["n"] else np.nan
            )
        return out

    # --- Candidate scoring (primary frac only for promotion) ---
    # LOW: delta negative (fewer opportunities). HIGH: delta positive.
    candidates: list[dict[str, Any]] = []
    is_rows = res_df[
        (res_df["split"] == "IS")
        & (res_df["condition"] != "UNCONDITIONAL")
        & (res_df["frac"] == PRIMARY_FRAC)
    ]
    for _, r in is_rows.iterrows():
        cname = str(r["condition"])
        off, H, frac = int(r["T_offset"]), int(r["horizon"]), float(r["frac"])
        regime = str(r["regime"])
        if regime not in ("LOW", "HIGH"):
            continue
        if int(r["n"]) < 80:
            continue
        met = slice_metrics(cname, off, H, frac)
        yrs = year_rates(cname, off, H, frac)
        is_d = met["IS_delta"]
        v_d, o_d = met["Validation_delta"], met["OOS_delta"]
        if not all(isinstance(x, (int, float)) and np.isfinite(x) for x in (is_d, v_d, o_d)):
            continue

        # Expected sign by regime
        if regime == "LOW":
            sign_ok_is = is_d <= -0.05
            sign_ok_vo = v_d < 0 and o_d < 0
            soft_is = is_d <= -0.03
        else:
            sign_ok_is = is_d >= 0.05
            sign_ok_vo = v_d > 0 and o_d > 0
            soft_is = is_d >= 0.03

        y25_d, y26_d = yrs.get("y2025_delta"), yrs.get("y2026_delta")
        y25_n, y26_n = yrs.get("y2025_n", 0), yrs.get("y2026_n", 0)
        year_sign_ok = (
            isinstance(y25_d, (int, float))
            and isinstance(y26_d, (int, float))
            and np.isfinite(y25_d)
            and np.isfinite(y26_d)
            and y25_n >= 20
            and y26_n >= 20
            and (
                (regime == "LOW" and y25_d < 0 and y26_d < 0)
                or (regime == "HIGH" and y25_d > 0 and y26_d > 0)
            )
        )
        # material year deltas (don't require full 5pp — years are smaller n)
        year_material = (
            isinstance(y25_d, (int, float))
            and isinstance(y26_d, (int, float))
            and abs(y25_d) >= 0.03
            and abs(y26_d) >= 0.03
        )

        strong = (
            sign_ok_is
            and sign_ok_vo
            and abs(is_d) >= 0.08
            and abs(v_d) >= 0.04
            and abs(o_d) >= 0.04
            and year_sign_ok
            and year_material
            and met["Validation_n"] >= 40
            and met["OOS_n"] >= 30
        )
        soft = (
            soft_is
            and sign_ok_vo
            and year_sign_ok
            and met["Validation_n"] >= 30
            and met["OOS_n"] >= 25
        )

        if strong or soft:
            candidates.append(
                {
                    **met,
                    **yrs,
                    "regime": regime,
                    "tier": "strong" if strong else "soft",
                    "IS_p": met["IS_p"],
                    "score": abs(is_d),
                }
            )

    candidates.sort(
        key=lambda x: (
            0 if x["tier"] == "strong" else 1,
            0 if x["regime"] == "LOW" else 1,  # prefer wait/gate signal
            -x["score"],
            -x["IS_n"],
        )
    )

    # --- Clock stability: count distinct T_offsets per (condition, H) that soft/strong ---
    stability: list[dict[str, Any]] = []
    if candidates:
        cand_df = pd.DataFrame(candidates)
        for (cname, H, regime), g in cand_df.groupby(["condition", "horizon", "regime"]):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            stability.append(
                {
                    "condition": cname,
                    "horizon": int(H),
                    "regime": regime,
                    "n_clocks_soft_or_strong": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "median_IS_delta": float(g["IS_delta"].median()),
                    "median_OOS_delta": float(g["OOS_delta"].median()),
                }
            )
        stability.sort(
            key=lambda x: (
                -x["n_clocks_strong"],
                -x["n_clocks_soft_or_strong"],
                -abs(x["median_IS_delta"]),
            )
        )

    # --- Discrimination: HIGH − LOW gap at each T,H (primary frac) ---
    # Use best-available paired states: quiet_wait vs fast_and_expanded / vol_expansion_high
    pair_defs = [
        ("quiet_wait", "fast_and_expanded"),
        ("quiet_wait", "vol_expansion_high"),
        ("quiet_wait", "strong_and_persistent"),
        ("vol_expansion_low", "vol_expansion_high"),
        ("low_local_vol", "high_local_vol"),
        ("weak_dir_move", "strong_dir_move"),
    ]
    discrimination: list[dict[str, Any]] = []
    for low_c, high_c in pair_defs:
        for off in DECISION_OFFSETS:
            for H in OPP_HORIZONS:
                low_m = slice_metrics(low_c, off, H, PRIMARY_FRAC)
                high_m = slice_metrics(high_c, off, H, PRIMARY_FRAC)
                if low_m["IS_n"] < 80 or high_m["IS_n"] < 80:
                    continue
                if low_m["Validation_n"] < 30 or high_m["Validation_n"] < 30:
                    continue
                if low_m["OOS_n"] < 25 or high_m["OOS_n"] < 25:
                    continue
                gaps = {}
                ok = True
                for split in ("IS", "Validation", "OOS"):
                    lp, hp = low_m[f"{split}_p"], high_m[f"{split}_p"]
                    if not (np.isfinite(lp) and np.isfinite(hp)):
                        ok = False
                        break
                    gaps[f"{split}_gap"] = hp - lp  # want HIGH > LOW
                if not ok:
                    continue
                # year gaps
                low_y = year_rates(low_c, off, H, PRIMARY_FRAC)
                high_y = year_rates(high_c, off, H, PRIMARY_FRAC)
                g25 = (
                    high_y["y2025"] - low_y["y2025"]
                    if np.isfinite(high_y.get("y2025", np.nan)) and np.isfinite(low_y.get("y2025", np.nan))
                    else np.nan
                )
                g26 = (
                    high_y["y2026"] - low_y["y2026"]
                    if np.isfinite(high_y.get("y2026", np.nan)) and np.isfinite(low_y.get("y2026", np.nan))
                    else np.nan
                )
                year_ok = (
                    np.isfinite(g25)
                    and np.isfinite(g26)
                    and g25 > 0
                    and g26 > 0
                    and low_y.get("y2025_n", 0) >= 20
                    and low_y.get("y2026_n", 0) >= 20
                    and high_y.get("y2025_n", 0) >= 20
                    and high_y.get("y2026_n", 0) >= 20
                )
                all_pos = gaps["IS_gap"] >= 0.08 and gaps["Validation_gap"] > 0 and gaps["OOS_gap"] > 0
                strong_disc = all_pos and year_ok and gaps["Validation_gap"] >= 0.04 and gaps["OOS_gap"] >= 0.04
                soft_disc = (
                    gaps["IS_gap"] >= 0.05
                    and gaps["Validation_gap"] > 0
                    and gaps["OOS_gap"] > 0
                    and year_ok
                )
                if strong_disc or soft_disc:
                    discrimination.append(
                        {
                            "low": low_c,
                            "high": high_c,
                            "T_offset": off,
                            "horizon": H,
                            "tier": "strong" if strong_disc else "soft",
                            "IS_gap": gaps["IS_gap"],
                            "Val_gap": gaps["Validation_gap"],
                            "OOS_gap": gaps["OOS_gap"],
                            "y2025_gap": g25,
                            "y2026_gap": g26,
                            "IS_low_p": low_m["IS_p"],
                            "IS_high_p": high_m["IS_p"],
                            "IS_low_n": low_m["IS_n"],
                            "IS_high_n": high_m["IS_n"],
                            "IS_unc": low_m.get("IS_unc"),
                        }
                    )

    discrimination.sort(
        key=lambda x: (0 if x["tier"] == "strong" else 1, -x["IS_gap"], x["T_offset"])
    )

    # Disc clock stability
    disc_stability: list[dict[str, Any]] = []
    if discrimination:
        dg = pd.DataFrame(discrimination)
        for (low_c, high_c, H), g in dg.groupby(["low", "high", "horizon"]):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            disc_stability.append(
                {
                    "pair": f"{low_c} vs {high_c}",
                    "horizon": int(H),
                    "n_clocks": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "median_IS_gap": float(g["IS_gap"].median()),
                    "median_OOS_gap": float(g["OOS_gap"].median()),
                }
            )
        disc_stability.sort(key=lambda x: (-x["n_clocks_strong"], -x["n_clocks"], -x["median_IS_gap"]))

    # Unconditional baselines
    unc_baselines = []
    for off in (5, 15, 30, 60, 90):
        for H in OPP_HORIZONS:
            s = res_df[
                (res_df["condition"] == "UNCONDITIONAL")
                & (res_df["T_offset"] == off)
                & (res_df["horizon"] == H)
                & (res_df["frac"] == PRIMARY_FRAC)
                & (res_df["split"] == "IS")
            ]
            if len(s):
                u = s.iloc[0]
                unc_baselines.append(
                    {
                        "T_offset": off,
                        "horizon": H,
                        "n": int(u["n"]),
                        "p_resolve": float(u["p_resolve"]),
                    }
                )

    # Sensitivity: quiet_wait deltas at 0.15/0.25/0.35 for a few clocks
    sensitivity = []
    for frac in STRUCT_FRACS:
        for off in (15, 30, 45, 60):
            for H in (15, 30):
                met = slice_metrics("quiet_wait", off, H, frac)
                yrs = year_rates("quiet_wait", off, H, frac)
                if met["IS_n"] >= 40:
                    sensitivity.append({**met, **yrs, "frac": frac})

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    strong_low = sum(1 for c in candidates if c["tier"] == "strong" and c["regime"] == "LOW")
    strong_high = sum(1 for c in candidates if c["tier"] == "strong" and c["regime"] == "HIGH")
    strong_disc_n = sum(1 for d in discrimination if d["tier"] == "strong")
    soft_disc_n = sum(1 for d in discrimination if d["tier"] == "soft")
    multi_clock = [s for s in stability if s["n_clocks_soft_or_strong"] >= 3]
    multi_clock_strong = [s for s in stability if s["n_clocks_strong"] >= 3]
    multi_disc = [s for s in disc_stability if s["n_clocks"] >= 3]

    # Verdict logic
    can_distinguish = strong_disc_n > 0 and len(multi_disc) > 0
    can_gate_wait = strong_low > 0 and any(
        s["regime"] == "LOW" and s["n_clocks_strong"] >= 2 for s in stability
    )
    if can_distinguish or (can_gate_wait and strong_disc_n > 0):
        verdict = "A_opportunity_timing_found"
        verdict_text = (
            "Causal states reliably reprice P(structural move within H) across "
            "IS→Val→OOS and 2025/2026, with multi-clock stability. "
            "This is a wait/arm gate candidate — not a directional edge."
        )
    elif strong_n > 0 or strong_disc_n > 0 or (soft_n > 0 and soft_disc_n > 0 and len(multi_clock) > 0):
        verdict = "B_weak_opportunity_timing"
        verdict_text = (
            "Some states shift structural-opportunity probability with partial year support, "
            "but discrimination is weak, clock-narrow, or not multi-year stable enough "
            "to treat as a reliable wait/arm gate."
        )
    else:
        verdict = "C_no_opportunity_timing"
        verdict_text = (
            "Cannot reliably distinguish low- vs high-opportunity morning regimes "
            "under the pre-specified 0.25·ONR structural definition."
        )

    # Answer the critical question explicitly
    if can_distinguish:
        critical_answer = "YES — with caveats: treat as a gate, not a trade."
    elif strong_disc_n > 0 or (soft_disc_n > 0 and any(s["n_clocks"] >= 2 for s in disc_stability)):
        critical_answer = "WEAK YES — discrimination exists but is not fully stable."
    else:
        critical_answer = "NO — cannot reliably separate low vs high opportunity periods."

    report = {
        "stage": "structural_opportunity_timing",
        "verdict": verdict,
        "verdict_text": verdict_text,
        "critical_question": "Can we reliably distinguish low- vs high-opportunity periods?",
        "critical_answer": critical_answer,
        "protocol": {
            "clocks": "every 5m 09:35–11:00",
            "entry_clock": "next bar open after T",
            "structural_definition": f"max(MFE,MAE) >= {PRIMARY_FRAC}*ONR within H",
            "structural_fracs_sensitivity": list(STRUCT_FRACS),
            "horizons_min": list(OPP_HORIZONS),
            "state_thresholds": "IS terciles only",
            "splits": "IS 2010-21 / Val 2022-24 / OOS 2025-26",
            "no_entries": True,
        },
        "panel": {"rows": int(len(panel)), "days": int(n_days)},
        "unc_baselines_IS_primary": unc_baselines,
        "n_candidates": len(candidates),
        "n_strong": strong_n,
        "n_soft": soft_n,
        "n_strong_LOW": strong_low,
        "n_strong_HIGH": strong_high,
        "n_disc_strong": strong_disc_n,
        "n_disc_soft": soft_disc_n,
        "top_candidates": candidates[:30],
        "stability": stability[:20],
        "discrimination": discrimination[:30],
        "disc_stability": disc_stability[:15],
        "quiet_wait_sensitivity": sensitivity,
        "kill_criteria": {
            "strong_state": (
                "IS |delta|>=8pp correct sign, Val&OOS same sign |delta|>=4pp, "
                "2025&2026 same-sign delta |d|>=3pp n>=20, samples adequate"
            ),
            "strong_discrimination": (
                "IS HIGH-LOW gap>=8pp, Val&OOS gaps>0 (>=4pp), both years gap>0 n>=20"
            ),
        },
    }
    with open(art("ny_open_opp_timing_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Markdown
    md: list[str] = []
    md.append("# NQ Structural Opportunity Timing")
    md.append("")
    md.append(f"**Verdict: `{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    md.append(f"**Critical question:** Can we reliably distinguish low- vs high-opportunity periods?")
    md.append("")
    md.append(f"**Answer: {critical_answer}**")
    md.append("")
    md.append(
        "This is a **wait/arm gate** research stage — not a directional edge and not a strategy."
    )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Protocol")
    md.append("")
    md.append("| Rule | Implementation |")
    md.append("|------|----------------|")
    md.append("| Clocks T | every 5m from 09:35–11:00 |")
    md.append("| State | bars with `ny_min <= T` only |")
    md.append("| Outcome start | **next bar open** after T |")
    md.append(
        f"| Structural resolve | `max(MFE, MAE) ≥ {PRIMARY_FRAC}·ONR` within H "
        "(frac pre-specified; sensitivity 0.15/0.35) |"
    )
    md.append("| Horizons | 10 / 15 / 20 / 30 / 45 min |")
    md.append("| Baseline | same-TOD unconditional |")
    md.append("| Strong gate | IS + Val + OOS + 2025 + 2026 same-sign; multi-clock preferred |")
    md.append("| Forbidden | entries, targets, direction, optimization, strategy conversion |")
    md.append("")
    md.append(f"Panel: **{len(panel):,}** rows · **{n_days:,}** days.")
    md.append("")
    md.append("## Unconditional IS P(structural resolve) @ 0.25·ONR")
    md.append("")
    md.append("| T+ | H10 | H15 | H20 | H30 | H45 |")
    md.append("|----|-----|-----|-----|-----|-----|")
    by_off: dict[int, dict[int, float]] = {}
    for u in unc_baselines:
        by_off.setdefault(u["T_offset"], {})[u["horizon"]] = u["p_resolve"]
    for off in (5, 15, 30, 60, 90):
        if off not in by_off:
            continue
        cells = [pct(by_off[off].get(H)) for H in OPP_HORIZONS]
        md.append(f"| +{off}m | " + " | ".join(cells) + " |")
    md.append("")
    md.append("## Candidates (primary 0.25·ONR)")
    md.append("")
    md.append(
        f"Strong: **{strong_n}** (LOW {strong_low} / HIGH {strong_high}) · Soft: **{soft_n}** · "
        f"Strong discrimination pairs: **{strong_disc_n}** · Soft disc: **{soft_disc_n}**"
    )
    md.append("")
    if not candidates:
        md.append("**None** cleared soft/strong bars.")
    else:
        md.append(
            "| Tier | Regime | State | T+ | H | IS n | IS P | Δ | Val Δ | OOS Δ | 2025 Δ | 2026 Δ |"
        )
        md.append(
            "|------|--------|-------|----|---|------|------|---|-------|-------|--------|--------|"
        )
        for c in candidates[:25]:
            md.append(
                f"| {c['tier']} | {c['regime']} | `{c['condition']}` | +{c['T_offset']}m | "
                f"{c['horizon']} | {c['IS_n']} | {pct(c['IS_p'])} | {pp(c['IS_delta'])} | "
                f"{pp(c['Validation_delta'])} | {pp(c['OOS_delta'])} | "
                f"{pp(c.get('y2025_delta'))} | {pp(c.get('y2026_delta'))} |"
            )
        md.append("")

    md.append("## Discrimination: HIGH − LOW opportunity gap")
    md.append("")
    md.append(
        "Can the same clock separate a low-opportunity state from a high-opportunity state?"
    )
    md.append("")
    if not discrimination:
        md.append("**No** pair cleared soft/strong discrimination bars.")
    else:
        md.append(
            "| Tier | Pair | T+ | H | IS gap | Val gap | OOS gap | 2025 | 2026 | IS P(low→high) |"
        )
        md.append(
            "|------|------|----|---|--------|---------|---------|------|------|----------------|"
        )
        for d in discrimination[:20]:
            md.append(
                f"| {d['tier']} | `{d['low']}` vs `{d['high']}` | +{d['T_offset']}m | "
                f"{d['horizon']} | {pp(d['IS_gap'])} | {pp(d['Val_gap'])} | {pp(d['OOS_gap'])} | "
                f"{pp(d['y2025_gap'])} | {pp(d['y2026_gap'])} | "
                f"{pct(d['IS_low_p'])}→{pct(d['IS_high_p'])} |"
            )
        md.append("")

    md.append("## Clock stability")
    md.append("")
    if stability:
        md.append("| State | Regime | H | soft+strong clocks | strong clocks | med IS Δ | med OOS Δ |")
        md.append("|-------|--------|---|--------------------|--------------|---------|-----------|")
        for s in stability[:15]:
            md.append(
                f"| `{s['condition']}` | {s['regime']} | {s['horizon']} | "
                f"{s['n_clocks_soft_or_strong']} | {s['n_clocks_strong']} | "
                f"{pp(s['median_IS_delta'])} | {pp(s['median_OOS_delta'])} |"
            )
        md.append("")
    if disc_stability:
        md.append("### Discrimination pair stability")
        md.append("")
        md.append("| Pair | H | clocks | strong clocks | med IS gap | med OOS gap |")
        md.append("|------|---|--------|---------------|------------|-------------|")
        for s in disc_stability[:10]:
            md.append(
                f"| `{s['pair']}` | {s['horizon']} | {s['n_clocks']} | {s['n_clocks_strong']} | "
                f"{pp(s['median_IS_gap'])} | {pp(s['median_OOS_gap'])} |"
            )
        md.append("")

    md.append("## Sensitivity: `quiet_wait` across structural fracs")
    md.append("")
    md.append("| Frac | T+ | H | IS Δ | Val Δ | OOS Δ | 2025 Δ | 2026 Δ |")
    md.append("|------|----|---|------|-------|-------|--------|--------|")
    for s in sensitivity:
        md.append(
            f"| {s['frac']} | +{s['T_offset']}m | {s['horizon']} | {pp(s['IS_delta'])} | "
            f"{pp(s['Validation_delta'])} | {pp(s['OOS_delta'])} | "
            f"{pp(s.get('y2025_delta'))} | {pp(s.get('y2026_delta'))} |"
        )
    md.append("")
    md.append("## Stage verdict")
    md.append("")
    md.append(f"**`{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    md.append(f"Critical answer: **{critical_answer}**")
    md.append("")
    md.append("### What this is / is not")
    md.append("")
    md.append("- **Is:** candidate information for a WAIT vs ARM gate on opportunity size")
    md.append("- **Is not:** a profitable strategy, a direction signal, or proof of edge")
    md.append("- Next (only if A or strong B): keep the gate frozen; search separately for entries")
    md.append("")
    md.append("### Explicit non-actions")
    md.append("")
    md.append("- Do not optimize STRUCT_FRAC, clocks, or terciles")
    md.append("- Do not convert timing into trades without a separate entry mechanism")
    md.append("- Do not reopen direction-prediction on these states")
    md.append("")
    md.append("## Artifacts")
    md.append("")
    md.append("- `artifacts/ny_open_opp_timing_panel.parquet`")
    md.append("- `artifacts/ny_open_opp_timing_results.csv`")
    md.append("- `artifacts/ny_open_opp_timing_report.json`")
    md.append("- `artifacts/ny_open_opp_timing_thresholds_IS.json`")
    md.append("- `run_ny_open_opportunity_timing.py`")
    md.append("")

    md_path = art("ny_open_opp_timing_report.md")
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {md_path}", flush=True)
    print(f"VERDICT: {verdict}", flush=True)
    print(f"critical: {critical_answer}", flush=True)
    print(
        f"strong/soft states: {strong_n}/{soft_n}  disc strong/soft: {strong_disc_n}/{soft_disc_n}",
        flush=True,
    )


if __name__ == "__main__":
    main()
