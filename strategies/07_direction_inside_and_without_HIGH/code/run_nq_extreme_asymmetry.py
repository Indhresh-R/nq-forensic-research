"""
NQ Intrinsic Directional Discovery — Family 2: Vol-Standardized Extremes

NO HIGH. Liquid RTH 09:30-15:30.
Question: After an unusually large standardized displacement at T,
does the forward return distribution become asymmetric?

Test independently:
  - continuation of extreme
  - fade of extreme

Full forward distribution (not win-rate only):
  mean/median, P(dir), z-return, MFE/MAE, P(+thr before -thr), clock/year stability.

Hostile: causal, next-bar outcomes, IS thresholds only, no sweep, no rescue.
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
from typing import Any

import numpy as np
import pandas as pd

from common.nq_session import art, ART, NY_OPEN, load_nq

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_END = 15 * 60 + 30
DECISION_OFFSETS = tuple(range(0, SESSION_END - NY_OPEN + 1, 5))
EVAL_OFFSETS = tuple(range(0, SESSION_END - NY_OPEN + 1, 15))
LOOKBACKS = (5, 15, 30)
FWD_HORIZONS = (5, 10, 15, 30, 45, 60)
IS_Y = set(range(2010, 2022))
VAL_Y = {2022, 2023, 2024}
OOS_Y = {2025, 2026}
# Path threshold in units of vol at T (pre-specified, not swept)
PATH_R = 1.0


def split_of(y: int) -> str:
    if y in IS_Y:
        return "IS"
    if y in VAL_Y:
        return "Validation"
    if y in OOS_Y:
        return "OOS"
    return "OTHER"


def first_hit(highs: np.ndarray, lows: np.ndarray, entry: float, thr: float) -> float:
    """1 if +thr before -thr, 0 if -thr before +thr, nan if neither/ambiguous same bar."""
    t_up = t_dn = None
    for i in range(len(highs)):
        up = highs[i] >= entry + thr
        dn = lows[i] <= entry - thr
        if up and dn:
            return np.nan
        if up and t_up is None:
            t_up = i
        if dn and t_dn is None:
            t_dn = i
        if t_up is not None and t_dn is not None:
            break
    if t_up is not None and (t_dn is None or t_up < t_dn):
        return 1.0
    if t_dn is not None and (t_up is None or t_dn < t_up):
        return 0.0
    return np.nan


def main() -> None:
    print("=== Vol-Standardized Extreme Asymmetry (NO HIGH) ===", flush=True)
    panel_path = art("nq_extreme_asym_panel.parquet")
    rebuild = True
    if panel_path.exists():
        probe = pd.read_parquet(panel_path)
        need = {"z_15", "x_cont_15", "x_fade_15", "fwd_15", "hit1R_dir_15", "mfe_dir_15"}
        if need.issubset(probe.columns) and len(probe) > 50000:
            panel = probe
            rebuild = False
            print(f"Reusing panel rows={len(panel)}", flush=True)

    if rebuild:
        df = load_nq()
        print("Indexing RTH...", flush=True)
        rows: list[dict] = []
        n_days = 0
        atr_hist: list[float] = []

        for sd, g in df.groupby("session_date", sort=True):
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 16 * 60)].reset_index(drop=True)
            if len(rth) < 220:
                continue
            n_days += 1
            year = int(rth.iloc[0]["year"])
            dow = int(rth.iloc[0]["dow"])
            split = split_of(year)

            o = rth["open"].to_numpy(float)
            h = rth["high"].to_numpy(float)
            l = rth["low"].to_numpy(float)
            c = rth["close"].to_numpy(float)
            ny = rth["ny_min"].to_numpy(int)
            idx = {int(n): i for i, n in enumerate(ny)}

            prev_c = np.concatenate([[o[0]], c[:-1]])
            tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
            prior_atr = float(np.median(atr_hist[-20:])) if len(atr_hist) >= 5 else float(np.mean(tr[:30]))

            day_trs = []
            for off in DECISION_OFFSETS:
                T = NY_OPEN + off
                if T not in idx:
                    continue
                j = idx[T]
                after = np.where(ny > T)[0]
                if len(after) < max(FWD_HORIZONS):
                    continue

                atr_so_far = float(np.mean(tr[max(0, j - 29) : j + 1]))  # recent 30m TR mean
                vol = max(atr_so_far, 0.25 * prior_atr, 0.25)

                entry_i = int(after[0])
                entry = float(o[entry_i])

                # lookback displacements ending at T
                zs = {}
                rets = {}
                for L in LOOKBACKS:
                    if j + 1 < L:
                        zs[L] = np.nan
                        rets[L] = np.nan
                        continue
                    i0 = j - L + 1
                    ret = float(c[j] - o[i0])
                    rets[L] = ret
                    zs[L] = ret / vol

                row: dict[str, Any] = {
                    "session_date": str(sd),
                    "year": year,
                    "dow": dow,
                    "split": split,
                    "T_offset": off,
                    "T_ny": T,
                    "vol": vol,
                    **{f"ret_{L}": rets[L] for L in LOOKBACKS},
                    **{f"z_{L}": zs[L] for L in LOOKBACKS},
                }

                # Forward path metrics from next open, for each H, both raw and direction-ready
                for H in FWD_HORIZONS:
                    # bars from entry_i inclusive for H minutes
                    end_i = entry_i + H - 1
                    if end_i >= len(c):
                        for key in (
                            f"fwd_{H}",
                            f"fwd_z_{H}",
                            f"mfe_{H}",
                            f"mae_{H}",
                            f"hit1R_long_{H}",
                        ):
                            row[key] = np.nan
                        continue
                    hh = h[entry_i : end_i + 1]
                    ll = l[entry_i : end_i + 1]
                    fwd = float(c[end_i] - entry)
                    mfe = float(hh.max() - entry)
                    mae = float(entry - ll.min())
                    row[f"fwd_{H}"] = fwd
                    row[f"fwd_z_{H}"] = fwd / vol
                    row[f"mfe_{H}"] = mfe
                    row[f"mae_{H}"] = mae
                    row[f"hit1R_long_{H}"] = first_hit(hh, ll, entry, PATH_R * vol)

                rows.append(row)
                day_trs.append(float(tr[j]))

            if day_trs:
                atr_hist.append(float(np.mean(day_trs)))
            if n_days % 500 == 0:
                print(f"  days={n_days} rows={len(rows)}", flush=True)

        panel = pd.DataFrame(rows)

        # IS |z| thresholds per (L, T_offset) — extreme = |z| >= p80 (pre-specified quantile, not swept grid)
        EXT_Q = 0.80
        thresholds: dict[str, dict[int, float]] = {}
        is_p = panel[panel["split"] == "IS"]
        for L in LOOKBACKS:
            thresholds[f"z_{L}"] = {}
            for off in DECISION_OFFSETS:
                s = is_p.loc[is_p["T_offset"] == off, f"z_{L}"].abs().dropna()
                if len(s) < 100:
                    continue
                thresholds[f"z_{L}"][off] = float(s.quantile(EXT_Q))
        with open(art("nq_extreme_asym_thresholds_IS.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "extreme_abs_z_quantile": EXT_Q,
                    "path_R_vol_units": PATH_R,
                    "vol_def": "max(mean TR last 30m to T, 0.25*prior_day_ATR, 0.25)",
                    "thresholds": thresholds,
                },
                f,
                indent=2,
            )

        # Labels + direction-aligned path metrics
        labs = []
        for _, r in panel.iterrows():
            off = int(r["T_offset"])
            lab: dict[str, Any] = {}
            for L in LOOKBACKS:
                z = float(r[f"z_{L}"])
                th = thresholds.get(f"z_{L}", {}).get(off)
                d = 1 if z > 0 else (-1 if z < 0 else 0)
                is_ext = th is not None and np.isfinite(z) and abs(z) >= th
                lab[f"x_cont_{L}"] = d if is_ext and d != 0 else 0
                lab[f"x_fade_{L}"] = -d if is_ext and d != 0 else 0
                lab[f"is_ext_{L}"] = 1 if is_ext else 0

            # Direction-aligned MFE/MAE/hit for each H using continuation direction of z_15 when extreme
            # Store generic long metrics; align at eval time by x direction
            labs.append(lab)

        panel = pd.concat([panel.reset_index(drop=True), pd.DataFrame(labs)], axis=1)

        # Precompute dir-aligned path columns for each L mechanism at eval — done in scoring
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)} days~{panel['session_date'].nunique()}", flush=True)
    else:
        thresholds = json.loads((art("nq_extreme_asym_thresholds_IS.json")).read_text(encoding="utf-8"))[
            "thresholds"
        ]

    mechanisms = []
    for L in LOOKBACKS:
        mechanisms.append((f"cont_{L}", f"x_cont_{L}"))
        mechanisms.append((f"fade_{L}", f"x_fade_{L}"))

    results: list[dict[str, Any]] = []

    def dist_stats(signed: np.ndarray, mfe_d: np.ndarray, mae_d: np.ndarray, hit_d: np.ndarray) -> dict[str, float]:
        signed = signed[np.isfinite(signed)]
        if len(signed) == 0:
            return {"n": 0}
        out = {
            "n": int(len(signed)),
            "win": float(np.mean(signed > 0)),
            "mean": float(np.mean(signed)),
            "median": float(np.median(signed)),
            "mean_z": float(np.mean(signed)),  # caller passes z-signed
        }
        mfe_d = mfe_d[np.isfinite(mfe_d)]
        mae_d = mae_d[np.isfinite(mae_d)]
        if len(mfe_d) and len(mae_d) and len(mfe_d) == len(mae_d):
            out["mean_mfe"] = float(np.mean(mfe_d))
            out["mean_mae"] = float(np.mean(mae_d))
            out["mfe_gt_mae"] = float(np.mean(mfe_d > mae_d))
        hit = hit_d[np.isfinite(hit_d)]
        if len(hit):
            out["p_hit_plus_first"] = float(np.mean(hit))
            out["hit_n"] = int(len(hit))
        return out

    for off in EVAL_OFFSETS:
        sub = panel[panel["T_offset"] == off]
        if len(sub) < 200:
            continue
        for split in ("IS", "Validation", "OOS"):
            base = sub[sub["split"] == split]
            if len(base) < 80:
                continue
            for H in FWD_HORIZONS:
                # unconditional long baseline
                fwd = base[f"fwd_{H}"].to_numpy(float)
                fz = base[f"fwd_z_{H}"].to_numpy(float)
                results.append(
                    {
                        "mechanism": "UNCOND_LONG",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(np.isfinite(fwd).sum()),
                        "rate": 1.0,
                        "win": float(np.nanmean(fwd > 0)),
                        "mean": float(np.nanmean(fwd)),
                        "median": float(np.nanmedian(fwd)),
                        "mean_z": float(np.nanmean(fz)),
                        "mean_mfe": float(np.nanmean(base[f"mfe_{H}"])),
                        "mean_mae": float(np.nanmean(base[f"mae_{H}"])),
                        "mfe_gt_mae": float(np.nanmean(base[f"mfe_{H}"] > base[f"mae_{H}"])),
                        "p_hit_plus_first": float(np.nanmean(base[f"hit1R_long_{H}"])),
                        "delta_win_vs_unc": 0.0,
                        "delta_mean_vs_unc": 0.0,
                    }
                )
                unc_win = float(np.nanmean(fwd > 0))
                unc_mean = float(np.nanmean(fwd))

                for mech, col in mechanisms:
                    s = base[base[col] != 0].copy()
                    if len(s) < 40:
                        continue
                    dirc = s[col].to_numpy(float)
                    signed = (s[f"fwd_{H}"] * s[col]).to_numpy(float)
                    signed_z = (s[f"fwd_z_{H}"] * s[col]).to_numpy(float)
                    # align MFE/MAE
                    mfe = s[f"mfe_{H}"].to_numpy(float)
                    mae = s[f"mae_{H}"].to_numpy(float)
                    mfe_d = np.where(dirc > 0, mfe, mae)
                    mae_d = np.where(dirc > 0, mae, mfe)
                    # hit +1R first in trade direction: long uses hit1R_long; short = 1 - hit if resolved
                    hit_long = s[f"hit1R_long_{H}"].to_numpy(float)
                    hit_d = np.where(dirc > 0, hit_long, 1.0 - hit_long)
                    # if hit_long nan, keep nan
                    hit_d = np.where(np.isfinite(hit_long), hit_d, np.nan)

                    st = dist_stats(signed, mfe_d, mae_d, hit_d)
                    if st.get("n", 0) < 40:
                        continue
                    # overwrite mean_z properly
                    sz = signed_z[np.isfinite(signed_z)]
                    st["mean_z"] = float(np.mean(sz)) if len(sz) else np.nan

                    results.append(
                        {
                            "mechanism": mech,
                            "T_offset": off,
                            "horizon": H,
                            "split": split,
                            "n": st["n"],
                            "n_base": int(len(base)),
                            "rate": float(len(s) / len(base)),
                            "win": st["win"],
                            "mean": st["mean"],
                            "median": st["median"],
                            "mean_z": st["mean_z"],
                            "mean_mfe": st.get("mean_mfe", np.nan),
                            "mean_mae": st.get("mean_mae", np.nan),
                            "mfe_gt_mae": st.get("mfe_gt_mae", np.nan),
                            "p_hit_plus_first": st.get("p_hit_plus_first", np.nan),
                            "hit_n": st.get("hit_n", 0),
                            "unc_win": unc_win,
                            "unc_mean": unc_mean,
                            "delta_win_vs_unc": st["win"] - unc_win,
                            "delta_mean_vs_unc": st["mean"] - unc_mean,
                            "delta_win_vs_50": st["win"] - 0.5,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_extreme_asym_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

    def year_stats(col: str, off: int, H: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for y in (2025, 2026):
            s = panel[(panel["T_offset"] == off) & (panel["year"] == y) & (panel[col] != 0)]
            signed = (s[f"fwd_{H}"] * s[col]).to_numpy(float)
            signed = signed[np.isfinite(signed)]
            out[f"y{y}_n"] = int(len(signed))
            out[f"y{y}_win"] = float(np.mean(signed > 0)) if len(signed) else np.nan
            out[f"y{y}_mean"] = float(np.mean(signed)) if len(signed) else np.nan
        return out

    candidates: list[dict[str, Any]] = []
    is_rows = res_df[(res_df["split"] == "IS") & (res_df["mechanism"] != "UNCOND_LONG")]
    for _, r in is_rows.iterrows():
        mech = str(r["mechanism"])
        off, H = int(r["T_offset"]), int(r["horizon"])
        if int(r["n"]) < 100:
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
        if int(v["n"]) < 50 or int(o["n"]) < 40:
            continue

        col = next(c for m, c in mechanisms if m == mech)
        yrs = year_stats(col, off, H)
        is_win, v_win, o_win = float(r["win"]), float(v["win"]), float(o["win"])
        is_d = float(r["delta_win_vs_50"])
        v_d = float(v["delta_win_vs_50"])
        o_d = float(o["delta_win_vs_50"])
        # also require lift vs same-TOD unc in same direction as edge
        is_du = float(r["delta_win_vs_unc"])
        v_du = float(v["delta_win_vs_unc"])
        o_du = float(o["delta_win_vs_unc"])
        is_mean, v_mean, o_mean = float(r["mean"]), float(v["mean"]), float(o["mean"])
        is_mz = float(r["mean_z"]) if np.isfinite(r["mean_z"]) else np.nan
        y25, y26 = yrs.get("y2025_win"), yrs.get("y2026_win")
        y25n, y26n = yrs.get("y2025_n", 0), yrs.get("y2026_n", 0)

        year_ok = (
            isinstance(y25, (int, float))
            and isinstance(y26, (int, float))
            and np.isfinite(y25)
            and np.isfinite(y26)
            and y25n >= 25
            and y26n >= 25
            and y25 >= 0.50
            and y26 >= 0.50
            and abs(y25 - y26) <= 0.12
        )
        # Material asymmetry: win lift AND mean/z supportive
        lift_ok = is_d >= 0.03 and v_d > 0 and o_d > 0 and is_du > 0 and v_du > 0 and o_du > 0
        abs_ok = is_win >= 0.53 and v_win >= 0.52 and o_win >= 0.52
        payoff_ok = is_mean > 0 and v_mean > 0 and o_mean > 0 and (not np.isfinite(is_mz) or is_mz > 0)
        path_ok = (
            np.isfinite(r.get("mfe_gt_mae", np.nan))
            and float(r["mfe_gt_mae"]) >= 0.52
            and np.isfinite(r.get("p_hit_plus_first", np.nan))
            and float(r["p_hit_plus_first"]) >= 0.52
        )
        strong = lift_ok and abs_ok and year_ok and payoff_ok and is_d >= 0.04 and path_ok
        soft = (
            ((lift_ok and is_d >= 0.025) or (abs_ok and is_win >= 0.54))
            and year_ok
            and v_win >= 0.50
            and o_win >= 0.50
            and (payoff_ok or path_ok)
        )
        if strong or soft:
            candidates.append(
                {
                    "mechanism": mech,
                    "T_offset": off,
                    "horizon": H,
                    "tier": "strong" if strong else "soft",
                    "IS_n": int(r["n"]),
                    "IS_win": is_win,
                    "IS_mean": is_mean,
                    "IS_mean_z": is_mz,
                    "IS_d50": is_d,
                    "IS_d_unc": is_du,
                    "IS_mfe_gt_mae": float(r["mfe_gt_mae"]) if np.isfinite(r.get("mfe_gt_mae", np.nan)) else None,
                    "IS_p_hit": float(r["p_hit_plus_first"]) if np.isfinite(r.get("p_hit_plus_first", np.nan)) else None,
                    "Val_win": v_win,
                    "Val_d50": v_d,
                    "Val_mean": v_mean,
                    "OOS_win": o_win,
                    "OOS_d50": o_d,
                    "OOS_mean": o_mean,
                    "y2025_win": y25,
                    "y2026_win": y26,
                    "y2025_n": y25n,
                    "y2026_n": y26n,
                }
            )

    candidates.sort(
        key=lambda x: (0 if x["tier"] == "strong" else 1, -(x["IS_d50"] if np.isfinite(x["IS_d50"]) else 0))
    )

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
                    "median_IS_d50": float(g["IS_d50"].median()),
                    "median_IS_win": float(g["IS_win"].median()),
                }
            )

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    multi_strong = [s for s in stability if s["n_clocks_strong"] >= 3]

    if multi_strong:
        verdict = "A"
        verdict_text = (
            "Vol-standardized extremes produce multi-clock year-stable forward asymmetry "
            "(continuation and/or fade)."
        )
        kill = False
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Weak/inconsistent extreme-asymmetry leftovers; no multi-clock strong effect. Kill for promotion."
        )
        kill = True
    else:
        verdict = "C"
        verdict_text = (
            "No forward distribution asymmetry after vol-standardized extremes "
            "(continuation and fade both fail hostile gates)."
        )
        kill = True

    mech_summary = []
    is_only = res_df[(res_df["split"] == "IS") & (res_df["mechanism"] != "UNCOND_LONG")]
    for mech, _ in mechanisms:
        g = is_only[is_only["mechanism"] == mech]
        if len(g) == 0:
            continue
        mech_summary.append(
            {
                "mechanism": mech,
                "IS_med_n": float(g["n"].median()),
                "IS_med_win": float(g["win"].median()),
                "IS_med_d50": float(g["delta_win_vs_50"].median()),
                "IS_med_mean_z": float(g["mean_z"].median()),
                "IS_med_mfe_gt_mae": float(g["mfe_gt_mae"].median()),
                "IS_med_p_hit": float(g["p_hit_plus_first"].median()),
            }
        )
    mech_summary.sort(key=lambda x: -abs(x["IS_med_d50"]))

    report = {
        "stage": "vol_standardized_extreme_asymmetry",
        "family": "return_imbalance_asymmetry",
        "verdict": verdict,
        "kill_family": kill,
        "verdict_text": verdict_text,
        "scope": "RTH 09:30-15:30; NO HIGH; extreme=|z|>=IS_p80; PATH_R=1 vol",
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_clock_strong": len(multi_strong),
        "mechanism_IS_summary": mech_summary,
        "top_candidates": candidates[:20],
        "stability": stability,
        "next_if_killed": "failed_movement_exhaustion family",
        "pivot_doc": "artifacts/research_pivot_independent_direction.md",
    }
    with open(art("nq_extreme_asym_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# NQ Vol-Standardized Extremes — Minimal Report (NO HIGH)")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(f"Kill family: **{kill}**. Extreme = `|z| ≥ IS p80` at T. Cont vs fade tested separately.")
    md.append("")
    md.append(f"Strong: {strong_n} · Soft: {soft_n} · Multi-clock strong: {len(multi_strong)}")
    md.append("")
    md.append("## Mechanism IS summary (median across clocks/horizons)")
    md.append("")
    md.append("| Mechanism | med n | win | Δ50 | mean z | MFE>MAE | P(+1R≺) |")
    md.append("|-----------|-------|-----|-----|--------|---------|---------|")
    for m in mech_summary:
        md.append(
            f"| `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | "
            f"{pp(m['IS_med_d50'])} | {m['IS_med_mean_z']:+.3f} | "
            f"{pct(m['IS_med_mfe_gt_mae'])} | {pct(m['IS_med_p_hit'])} |"
        )
    md.append("")
    md.append("## Surviving cells")
    md.append("")
    if not candidates:
        md.append("None.")
    else:
        md.append("| Tier | X | T+ | H | n | IS | Δ50 | mean z | Val | OOS | 2025 | 2026 |")
        md.append("|------|---|----|---|---|----|-----|--------|-----|-----|------|------|")
        for c in candidates[:15]:
            md.append(
                f"| {c['tier']} | `{c['mechanism']}` | +{c['T_offset']} | {c['horizon']} | "
                f"{c['IS_n']} | {pct(c['IS_win'])} | {pp(c['IS_d50'])} | "
                f"{c['IS_mean_z']:+.3f} | {pct(c['Val_win'])} | {pct(c['OOS_win'])} | "
                f"{pct(c.get('y2025_win'))} | {pct(c.get('y2026_win'))} |"
            )
        if not multi_strong:
            md.append("")
            md.append("No multi-clock strong mechanism — not promotable.")
    md.append("")
    md.append("## Stability")
    md.append("")
    if not stability:
        md.append("n/a")
    else:
        for s in stability:
            md.append(
                f"- `{s['mechanism']}` H{s['horizon']}: {s['n_clocks']} clocks "
                f"({s['n_clocks_strong']} strong) {s['clocks']}"
            )
    md.append("")
    md.append(f"## Final: **{verdict}**")
    md.append("")
    if kill:
        md.append("Kill vol-standardized extreme family.")
        md.append("Next: **failed movement / exhaustion** (still no HIGH).")
        md.append("HIGH remains frozen for later timing-only tests.")
    else:
        md.append("Only after this: test whether frozen HIGH improves timing of the surviving phenomenon.")
    md.append("")
    (art("nq_extreme_asym_report.md")).write_text("\n".join(md), encoding="utf-8")
    print(f"VERDICT: {verdict} kill={kill}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n} multi_strong: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
