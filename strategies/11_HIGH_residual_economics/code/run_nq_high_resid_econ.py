"""
HIGH Residual Opportunity Economics — direction-neutral

Question:
  Does HIGH reliably leave enough remaining TWO-SIDED movement after activation
  to have economic value vs LOW — without predicting direction?

NO direction. NO entries. NO strategy. Frozen HIGH only.

For each HIGH/LOW at T:
  residual = max(high-entry, entry-low) from next-bar open over H in {5,10,15,30,60}
  Compare distributions HIGH vs LOW
  Cover frozen round-trip cost scenarios (pts and ONR-normalized)
  Frequency + clustering of HIGH events

Frozen costs (pre-specified, not optimized) in NQ points:
  tight=0.50, mid=1.00, wide=2.00  (fees+slippage round-trip ballparks)
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

from common.nq_session import art, ART, NY_OPEN, build_day_context, load_nq, state_at_T

warnings.filterwarnings("ignore", category=FutureWarning)

ARM_OFFSETS = tuple(range(5, 91, 5))
HORIZONS = (5, 10, 15, 30, 60)
STRUCT_FRAC = 0.25
COST_PTS = {"tight": 0.50, "mid": 1.00, "wide": 2.00}
IS_Y = set(range(2010, 2022))
VAL_Y = {2022, 2023, 2024}
OOS_Y = {2025, 2026}

THRESH = json.loads((art("ny_open_opp_timing_thresholds_IS.json")).read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]


def split_of(y: int) -> str:
    if y in IS_Y:
        return "IS"
    if y in VAL_Y:
        return "Validation"
    if y in OOS_Y:
        return "OOS"
    return "OTHER"


def th_get(feat: str, off: int) -> dict[str, float]:
    d = STATE_TH[feat]
    return d.get(str(off)) or d.get(off) or {}


def is_high(rng_onr: float, off: int) -> bool:
    t = th_get("rng_onr", off)
    return bool(t) and float(rng_onr) >= float(t["p66"])


def is_low(rng_onr: float, off: int) -> bool:
    t = th_get("rng_onr", off)
    return bool(t) and float(rng_onr) <= float(t["p33"])


def residual_abs(
    h: np.ndarray,
    l: np.ndarray,
    o: np.ndarray,
    ny: np.ndarray,
    T: int,
    horizons: tuple[int, ...],
) -> dict[str, float]:
    after = np.where(ny > T)[0]
    out: dict[str, float] = {}
    if len(after) < max(horizons):
        for H in horizons:
            out[f"resid_pts_{H}"] = np.nan
            out[f"t_half_{H}"] = np.nan
        return out
    entry_i = int(after[0])
    entry = float(o[entry_i])
    for H in horizons:
        end = entry_i + H - 1
        if end >= len(h):
            out[f"resid_pts_{H}"] = np.nan
            out[f"t_half_{H}"] = np.nan
            continue
        hh = h[entry_i : end + 1]
        ll = l[entry_i : end + 1]
        mx = max(float(hh.max() - entry), float(entry - ll.min()))
        out[f"resid_pts_{H}"] = mx
        # time to reach half of final residual (path timing)
        half = 0.5 * mx
        t_half = np.nan
        if mx > 0:
            run = 0.0
            for i in range(H):
                run = max(run, hh[i] - entry, entry - ll[i])
                if run >= half:
                    t_half = float(i + 1)
                    break
        out[f"t_half_{H}"] = t_half
    return out


def main() -> None:
    print("=== HIGH Residual Opportunity Economics (direction-neutral) ===", flush=True)
    print(f"FROZEN costs pts={COST_PTS}; H={HORIZONS}; ARM=vol_expansion_high", flush=True)

    panel_path = art("nq_high_resid_econ_panel.parquet")
    if panel_path.exists():
        panel = pd.read_parquet(panel_path)
        print(f"Reusing panel rows={len(panel)}", flush=True)
    else:
        df = load_nq()
        print("Building day context...", flush=True)
        ctx_df = build_day_context(df)
        ctx_map = {r["session_date"]: r for _, r in ctx_df.iterrows()}

        rows: list[dict] = []
        n_days = 0
        for sd, g in df.groupby("session_date", sort=True):
            ctx = ctx_map.get(sd)
            if ctx is None:
                continue
            onr = float(ctx["onr"])
            if onr <= 0:
                continue
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 16 * 60)].reset_index(drop=True)
            if len(rth) < 120:
                continue
            n_days += 1
            year = int(rth.iloc[0]["year"])
            split = split_of(year)
            o = rth["open"].to_numpy(float)
            h = rth["high"].to_numpy(float)
            l = rth["low"].to_numpy(float)
            ny = rth["ny_min"].to_numpy(int)
            idx = {int(m): i for i, m in enumerate(ny)}

            for off in ARM_OFFSETS:
                T = NY_OPEN + off
                if T not in idx:
                    continue
                st = state_at_T(rth[rth["ny_min"] <= T], ctx, T)
                if st is None:
                    continue
                rng = float(st["rng_onr"])
                if is_high(rng, off):
                    regime = "HIGH"
                elif is_low(rng, off):
                    regime = "LOW"
                else:
                    regime = "MID"

                res = residual_abs(h, l, o, ny, T, HORIZONS)
                row: dict[str, Any] = {
                    "session_date": str(sd),
                    "year": year,
                    "split": split,
                    "T_offset": off,
                    "regime": regime,
                    "onr": onr,
                    "rng_onr": rng,
                }
                o930 = float(ctx["open_930"])
                j = idx[T]
                open_i = idx.get(NY_OPEN, 0)
                pre_exc = max(
                    abs(float(h[open_i : j + 1].max() - o930)),
                    abs(float(o930 - l[open_i : j + 1].min())),
                )
                row["pre_exc_pts"] = pre_exc
                row["pre_exc_onr"] = pre_exc / onr
                for H in HORIZONS:
                    pts = res[f"resid_pts_{H}"]
                    row[f"resid_pts_{H}"] = pts
                    row[f"resid_onr_{H}"] = pts / onr if np.isfinite(pts) and onr > 0 else np.nan
                    row[f"t_half_{H}"] = res[f"t_half_{H}"]
                    row[f"struct_{H}"] = (
                        1.0 if np.isfinite(pts) and pts >= STRUCT_FRAC * onr else (0.0 if np.isfinite(pts) else np.nan)
                    )
                    for cname, cpts in COST_PTS.items():
                        row[f"cover_{cname}_{H}"] = (
                            1.0 if np.isfinite(pts) and pts >= cpts else (0.0 if np.isfinite(pts) else np.nan)
                        )
                        crow = cpts / onr
                        row[f"cover_{cname}_onr_{H}"] = (
                            1.0
                            if np.isfinite(pts) and onr > 0 and (pts / onr) >= crow
                            else (0.0 if np.isfinite(pts) else np.nan)
                        )
                rows.append(row)

            if n_days % 500 == 0:
                print(f"  days={n_days} rows={len(rows)}", flush=True)

        panel = pd.DataFrame(rows)
        panel["is_first_high"] = False
        high_mask = panel["regime"] == "HIGH"
        first_idx = panel[high_mask].groupby("session_date")["T_offset"].idxmin()
        panel.loc[first_idx, "is_first_high"] = True
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)}", flush=True)

    if "is_first_high" not in panel.columns:
        panel["is_first_high"] = False
        high_mask = panel["regime"] == "HIGH"
        first_idx = panel[high_mask].groupby("session_date")["T_offset"].idxmin()
        panel.loc[first_idx, "is_first_high"] = True
        panel.to_parquet(panel_path, index=False)

    def dist(s: pd.Series) -> dict[str, float]:
        x = s.to_numpy(float)
        x = x[np.isfinite(x)]
        if len(x) == 0:
            return {"n": 0}
        return {
            "n": int(len(x)),
            "mean": float(np.mean(x)),
            "median": float(np.median(x)),
            "p25": float(np.percentile(x, 25)),
            "p75": float(np.percentile(x, 75)),
            "p90": float(np.percentile(x, 90)),
        }

    # ——— Residual distributions HIGH vs LOW ———
    dist_rows = []
    for split in ("IS", "Validation", "OOS"):
        for H in HORIZONS:
            for reg in ("HIGH", "LOW"):
                s = panel[(panel["split"] == split) & (panel["regime"] == reg)]
                d_pts = dist(s[f"resid_pts_{H}"])
                d_onr = dist(s[f"resid_onr_{H}"])
                rec = {
                    "split": split,
                    "horizon": H,
                    "regime": reg,
                    "n": d_pts.get("n", 0),
                    "med_pts": d_pts.get("median", np.nan),
                    "mean_pts": d_pts.get("mean", np.nan),
                    "p25_pts": d_pts.get("p25", np.nan),
                    "p75_pts": d_pts.get("p75", np.nan),
                    "p90_pts": d_pts.get("p90", np.nan),
                    "med_onr": d_onr.get("median", np.nan),
                    "mean_onr": d_onr.get("mean", np.nan),
                    "p_struct": float(np.nanmean(s[f"struct_{H}"])) if len(s) else np.nan,
                }
                for cname in COST_PTS:
                    rec[f"p_cover_{cname}"] = float(np.nanmean(s[f"cover_{cname}_{H}"])) if len(s) else np.nan
                dist_rows.append(rec)
    dist_df = pd.DataFrame(dist_rows)
    dist_df.to_csv(art("nq_high_resid_econ_dist.csv"), index=False)

    # Lift HIGH - LOW
    lift_rows = []
    for split in ("IS", "Validation", "OOS"):
        for H in HORIZONS:
            hi = dist_df[(dist_df["split"] == split) & (dist_df["horizon"] == H) & (dist_df["regime"] == "HIGH")]
            lo = dist_df[(dist_df["split"] == split) & (dist_df["horizon"] == H) & (dist_df["regime"] == "LOW")]
            if len(hi) == 0 or len(lo) == 0:
                continue
            h, l = hi.iloc[0], lo.iloc[0]
            lift_rows.append(
                {
                    "split": split,
                    "horizon": H,
                    "lift_med_pts": float(h["med_pts"] - l["med_pts"]),
                    "lift_med_onr": float(h["med_onr"] - l["med_onr"]),
                    "lift_p_struct": float(h["p_struct"] - l["p_struct"]),
                    "HIGH_med_pts": float(h["med_pts"]),
                    "LOW_med_pts": float(l["med_pts"]),
                    "HIGH_med_onr": float(h["med_onr"]),
                    "LOW_med_onr": float(l["med_onr"]),
                    "HIGH_p_struct": float(h["p_struct"]),
                    "LOW_p_struct": float(l["p_struct"]),
                    **{f"HIGH_p_cover_{c}": float(h[f"p_cover_{c}"]) for c in COST_PTS},
                    **{f"LOW_p_cover_{c}": float(l[f"p_cover_{c}"]) for c in COST_PTS},
                    **{
                        f"lift_p_cover_{c}": float(h[f"p_cover_{c}"] - l[f"p_cover_{c}"])
                        for c in COST_PTS
                    },
                }
            )
    lift_df = pd.DataFrame(lift_rows)
    lift_df.to_csv(art("nq_high_resid_econ_lift.csv"), index=False)

    # ——— Frequency & clustering ———
    freq_rows = []
    for split in ("IS", "Validation", "OOS"):
        days = panel[panel["split"] == split]["session_date"].nunique()
        high_rows = panel[(panel["split"] == split) & (panel["regime"] == "HIGH")]
        high_days = high_rows["session_date"].nunique()
        first = high_rows[high_rows["is_first_high"]]
        # clocks per high-day
        cpg = high_rows.groupby("session_date").size()
        # independence proxy: gap between consecutive HIGH offs within day
        gaps = []
        for _, g in high_rows.groupby("session_date"):
            offs = sorted(g["T_offset"].unique())
            if len(offs) >= 2:
                gaps.extend(np.diff(offs).tolist())
        freq_rows.append(
            {
                "split": split,
                "n_days": int(days),
                "n_high_days": int(high_days),
                "frac_days_with_high": high_days / days if days else np.nan,
                "high_events_per_day_all_clocks": len(high_rows) / days if days else np.nan,
                "first_high_per_day": len(first) / days if days else np.nan,
                "med_high_clocks_given_high_day": float(cpg.median()) if len(cpg) else np.nan,
                "mean_high_clocks_given_high_day": float(cpg.mean()) if len(cpg) else np.nan,
                "med_gap_min_between_high_clocks": float(np.median(gaps)) if gaps else np.nan,
                "p_gap_eq_5": float(np.mean(np.array(gaps) == 5)) if gaps else np.nan,
            }
        )
    # year frequency
    for y in (2025, 2026):
        days = panel[panel["year"] == y]["session_date"].nunique()
        high_rows = panel[(panel["year"] == y) & (panel["regime"] == "HIGH")]
        first = high_rows[high_rows["is_first_high"]]
        freq_rows.append(
            {
                "split": f"y{y}",
                "n_days": int(days),
                "n_high_days": int(high_rows["session_date"].nunique()),
                "frac_days_with_high": high_rows["session_date"].nunique() / days if days else np.nan,
                "high_events_per_day_all_clocks": len(high_rows) / days if days else np.nan,
                "first_high_per_day": len(first) / days if days else np.nan,
                "med_high_clocks_given_high_day": float(
                    high_rows.groupby("session_date").size().median()
                )
                if len(high_rows)
                else np.nan,
                "mean_high_clocks_given_high_day": float(
                    high_rows.groupby("session_date").size().mean()
                )
                if len(high_rows)
                else np.nan,
                "med_gap_min_between_high_clocks": np.nan,
                "p_gap_eq_5": np.nan,
            }
        )
    freq_df = pd.DataFrame(freq_rows)
    freq_df.to_csv(art("nq_high_resid_econ_freq.csv"), index=False)

    # First-HIGH only economics (closer to 1/day scarcity)
    first_econ = []
    for split in ("IS", "Validation", "OOS"):
        for H in HORIZONS:
            s = panel[(panel["split"] == split) & (panel["is_first_high"])]
            first_econ.append(
                {
                    "split": split,
                    "horizon": H,
                    "n": int(len(s)),
                    "med_pts": float(np.nanmedian(s[f"resid_pts_{H}"])),
                    "mean_pts": float(np.nanmean(s[f"resid_pts_{H}"])),
                    "med_onr": float(np.nanmedian(s[f"resid_onr_{H}"])),
                    "p_struct": float(np.nanmean(s[f"struct_{H}"])),
                    **{
                        f"p_cover_{c}": float(np.nanmean(s[f"cover_{c}_{H}"]))
                        for c in COST_PTS
                    },
                }
            )
    first_df = pd.DataFrame(first_econ)

    # ——— Verdict ———
    # Economic if across IS/Val/OOS at H15 and H30:
    # 1) HIGH med residual >> cost mid
    # 2) HIGH p_cover_mid materially > LOW
    # 3) first_high frequency in usable band (~0.3–1.5 / day)
    # 4) year 2025/2026 not collapsing
    def cell(split: str, H: int) -> pd.Series:
        return lift_df[(lift_df["split"] == split) & (lift_df["horizon"] == H)].iloc[0]

    checks = []
    for H in (15, 30):
        for split in ("IS", "Validation", "OOS"):
            r = cell(split, H)
            ok_med = float(r["HIGH_med_pts"]) >= COST_PTS["mid"]
            ok_cover = float(r["HIGH_p_cover_mid"]) >= 0.70
            ok_lift = float(r["lift_p_cover_mid"]) >= 0.10
            checks.append(
                {
                    "split": split,
                    "H": H,
                    "ok_med_ge_midcost": ok_med,
                    "ok_cover70": ok_cover,
                    "ok_lift_cover": ok_lift,
                    "HIGH_med_pts": float(r["HIGH_med_pts"]),
                    "HIGH_p_cover_mid": float(r["HIGH_p_cover_mid"]),
                    "lift_p_cover_mid": float(r["lift_p_cover_mid"]),
                }
            )
    chk = pd.DataFrame(checks)
    all_strong = bool(
        chk["ok_med_ge_midcost"].all() and chk["ok_cover70"].all() and chk["ok_lift_cover"].all()
    )
    # wide cost harder
    wide_ok = True
    for H in (15, 30):
        for split in ("IS", "Validation", "OOS"):
            r = cell(split, H)
            if float(r["HIGH_p_cover_wide"]) < 0.55 or float(r["lift_p_cover_wide"]) < 0.08:
                wide_ok = False

    is_freq = freq_df[freq_df["split"] == "IS"].iloc[0]
    freq_ok = 0.25 <= float(is_freq["frac_days_with_high"]) <= 1.0
    cluster_heavy = float(is_freq["p_gap_eq_5"]) >= 0.60 if np.isfinite(is_freq["p_gap_eq_5"]) else True

    # First-high cover mid IS/Val/OOS H30
    fh_ok = True
    for split in ("IS", "Validation", "OOS"):
        r = first_df[(first_df["split"] == split) & (first_df["horizon"] == 30)].iloc[0]
        if float(r["p_cover_mid"]) < 0.65 or float(r["med_pts"]) < COST_PTS["mid"]:
            fh_ok = False

    # Economic differentiation requires HIGH to beat LOW on cost coverage, not merely
    # that absolute residuals are large (modern NQ residuals often cover 1–2pts even on LOW).
    cover_lift_mean = float(chk["ok_lift_cover"].mean()) if len(chk) else 0.0
    # Recompute lift cover strength directly
    lift_cover_ok = True
    for H in (15, 30):
        for split in ("IS", "Validation", "OOS"):
            r = cell(split, H)
            if float(r["lift_p_cover_mid"]) < 0.05:  # need meaningful coverage edge vs LOW
                lift_cover_ok = False

    if all_strong and freq_ok and fh_ok and lift_cover_ok and wide_ok and not cluster_heavy:
        verdict = "A_residual_economic"
        verdict_text = (
            "Residual absolute movement after HIGH clears costs AND lifts coverage vs LOW, "
            "with usable non-clustered first-HIGH frequency — direction-neutral residue is economic."
        )
        economic = True
    elif all_strong and freq_ok and fh_ok and not lift_cover_ok:
        verdict = "C_not_economically_exploitable_as_standalone"
        verdict_text = (
            "Residual absolute movement after HIGH covers frozen costs — but so does LOW "
            "(coverage lift ~0). HIGH's edge is ONR-normalized structural opportunity, not an "
            "absolute-points economic moat. With heavy clock clustering, HIGH is not a "
            "standalone direction-neutral exploitable signal."
        )
        economic = False
    elif chk["ok_med_ge_midcost"].mean() >= 0.5 and cover_lift_mean >= 0.5:
        verdict = "B_residual_marginal"
        verdict_text = (
            "Residual opportunity is statistically elevated vs LOW but only inconsistently "
            "clears / differentiates realistic round-trip costs across splits/horizons."
        )
        economic = False
    else:
        # Default: check if costs covered but no lift (common modern-NQ case)
        if float(chk["ok_cover70"].mean()) >= 0.8 and not lift_cover_ok:
            verdict = "C_not_economically_exploitable_as_standalone"
            verdict_text = (
                "Residual absolute movement after HIGH covers frozen costs — but so does LOW "
                "(coverage lift ~0). HIGH's edge is ONR-normalized structural opportunity, not an "
                "absolute-points economic moat. With heavy clock clustering, HIGH is not a "
                "standalone direction-neutral exploitable signal."
            )
            economic = False
        else:
            verdict = "C_not_economically_exploitable_as_standalone"
            verdict_text = (
                "HIGH residual movement is statistically real vs LOW in ONR units but not "
                "economically usable as a standalone direction-neutral opportunity after costs, "
                "independence, and LOW baselines are accounted for."
            )
            economic = False

    report = {
        "stage": "high_residual_opportunity_economics",
        "verdict": verdict,
        "economically_interesting": economic,
        "verdict_text": verdict_text,
        "frozen": {
            "arm": "vol_expansion_high",
            "costs_pts": COST_PTS,
            "struct_frac": STRUCT_FRAC,
            "horizons": list(HORIZONS),
            "no_direction": True,
        },
        "checks": checks,
        "frequency": freq_rows,
        "first_high_econ": first_econ,
        "lift_primary": lift_rows,
        "cluster_heavy_IS": cluster_heavy,
        "implication": (
            "If A/B: residual two-sided movement has economic content — later explore "
            "direction-neutral realization carefully (still no predictive directional engine). "
            "If C: HIGH is statistically real but not standalone-exploitable; terminal for "
            "this branch as a trade signal."
        ),
    }
    with open(art("nq_high_resid_econ_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def num(x: Any) -> str:
        return f"{x:.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# HIGH Residual Opportunity Economics (Direction-Neutral)")
    md.append("")
    md.append(f"**Verdict: `{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    md.append(
        f"Frozen round-trip costs (NQ pts): tight={COST_PTS['tight']}, "
        f"mid={COST_PTS['mid']}, wide={COST_PTS['wide']}. No direction. No strategy."
    )
    md.append("")
    md.append("## 1. Residual absolute movement — HIGH vs LOW")
    md.append("")
    md.append("| Split | H | HIGH med pts | LOW med pts | Δpts | HIGH med ONR | ΔONR | HIGH P(struct) | Δstruct |")
    md.append("|-------|---|--------------|-------------|------|--------------|------|----------------|---------|")
    for _, r in lift_df.iterrows():
        md.append(
            f"| {r['split']} | {int(r['horizon'])} | {num(r['HIGH_med_pts'])} | {num(r['LOW_med_pts'])} | "
            f"{num(r['lift_med_pts'])} | {num(r['HIGH_med_onr'])} | {num(r['lift_med_onr'])} | "
            f"{pct(r['HIGH_p_struct'])} | {pct(r['lift_p_struct'])} |"
        )
    md.append("")
    md.append("## 2. Cost coverage — P(residual ≥ round-trip cost)")
    md.append("")
    md.append("| Split | H | HIGH mid | LOW mid | Δ mid | HIGH wide | LOW wide | Δ wide |")
    md.append("|-------|---|----------|---------|-------|-----------|----------|--------|")
    for _, r in lift_df.iterrows():
        md.append(
            f"| {r['split']} | {int(r['horizon'])} | {pct(r['HIGH_p_cover_mid'])} | "
            f"{pct(r['LOW_p_cover_mid'])} | {pct(r['lift_p_cover_mid'])} | "
            f"{pct(r['HIGH_p_cover_wide'])} | {pct(r['LOW_p_cover_wide'])} | "
            f"{pct(r['lift_p_cover_wide'])} |"
        )
    md.append("")
    md.append("## 3. First HIGH only (scarcity / ~1 event path)")
    md.append("")
    md.append("| Split | H | n | med pts | med ONR | P≥mid cost | P≥wide | P(struct) |")
    md.append("|-------|---|---|---------|---------|------------|--------|-----------|")
    for _, r in first_df.iterrows():
        md.append(
            f"| {r['split']} | {int(r['horizon'])} | {int(r['n'])} | {num(r['med_pts'])} | "
            f"{num(r['med_onr'])} | {pct(r['p_cover_mid'])} | {pct(r['p_cover_wide'])} | "
            f"{pct(r['p_struct'])} |"
        )
    md.append("")
    md.append("## 4. Frequency & clustering")
    md.append("")
    md.append(
        "| Split | days | % days w/ HIGH | first-HIGH / day | all HIGH clocks / day | "
        "med clocks/high-day | % adjacent (5m gap) |"
    )
    md.append(
        "|-------|------|----------------|------------------|----------------------|"
        "---------------------|---------------------|"
    )
    for _, r in freq_df.iterrows():
        md.append(
            f"| {r['split']} | {int(r['n_days'])} | {pct(r['frac_days_with_high'])} | "
            f"{num(r['first_high_per_day'])} | {num(r['high_events_per_day_all_clocks'])} | "
            f"{num(r['med_high_clocks_given_high_day'])} | {pct(r['p_gap_eq_5'])} |"
        )
    md.append("")
    md.append("## 5. Residual distribution detail (IS HIGH)")
    md.append("")
    md.append("| H | n | p25 | median | p75 | p90 | mean |")
    md.append("|---|---|-----|--------|-----|-----|------|")
    for H in HORIZONS:
        r = dist_df[(dist_df["split"] == "IS") & (dist_df["horizon"] == H) & (dist_df["regime"] == "HIGH")]
        if len(r) == 0:
            continue
        r = r.iloc[0]
        md.append(
            f"| {H} | {int(r['n'])} | {num(r['p25_pts'])} | {num(r['med_pts'])} | "
            f"{num(r['p75_pts'])} | {num(r['p90_pts'])} | {num(r['mean_pts'])} |"
        )
    md.append("")
    md.append(f"## Final: **{verdict}**")
    md.append("")
    if verdict.startswith("A"):
        md.append(
            "Direction-neutral residual movement after HIGH has economic content. "
            "Next (only if pursued): how to realize two-sided movement without a directional engine — "
            "still not another predictive filter stack."
        )
    elif verdict.startswith("B"):
        md.append(
            "Borderline. Residual is real vs LOW but clustering / wide-cost fragility means "
            "HIGH is not a clean standalone money printer. Do not force a strategy."
        )
    else:
        md.append(
            "**Terminal for HIGH as a standalone exploitable signal:** statistically real "
            "activity persistence with residual movement, but not economically usable without "
            "direction (which we already failed to predict)."
        )
    md.append("")
    md.append("Forbidden: directional families, HIGH retune, pretending consecutive HIGH clocks are independent trades.")
    md.append("")
    (art("nq_high_resid_econ_report.md")).write_text("\n".join(md), encoding="utf-8")

    print(f"VERDICT: {verdict} economic={economic}", flush=True)
    is15 = cell("IS", 15)
    print(
        f"IS H15 HIGH med={is15['HIGH_med_pts']:.2f}pts cover_mid={is15['HIGH_p_cover_mid']:.1%} "
        f"lift_cover={is15['lift_p_cover_mid']:.1%}",
        flush=True,
    )
    print(
        f"IS freq: frac_high_days={is_freq['frac_days_with_high']:.1%} "
        f"first/day={is_freq['first_high_per_day']:.2f} cluster5={is_freq['p_gap_eq_5']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
