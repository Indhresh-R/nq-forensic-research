"""
NQ HIGH + Multi-Scale Directional Discovery

FROZEN HIGH (untouched). Family: multi-scale only.
Each X independent vs HIGH alone. No combining. No rescue filters.

Kill rule: if only ~55% effects without stable multi-clock incremental
improvement over HIGH across Val/OOS/years -> kill family.
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
from run_ny_open_high_directional import ARM_OFFSETS, GATE, HORIZONS, fwd_from_next, is_high

warnings.filterwarnings("ignore", category=FutureWarning)


def scale_ret(rth: pd.DataFrame, T_ny: int, lookback: int) -> float:
    """Return from open of bar at T-lookback+1 through close at T (causal)."""
    sub = rth[(rth["ny_min"] > T_ny - lookback) & (rth["ny_min"] <= T_ny)]
    if len(sub) < max(1, lookback // 2):
        return np.nan
    o = float(sub.iloc[0]["open"])
    c = float(sub.iloc[-1]["close"])
    if o == 0 or not np.isfinite(o):
        return np.nan
    return (c - o) / o


def sgn(x: float) -> int:
    if not np.isfinite(x) or x == 0:
        return 0
    return 1 if x > 0 else -1


def main() -> None:
    print("=== HIGH + Multi-Scale Directional Discovery ===", flush=True)
    print(f"Frozen ARM: {GATE['primary_arm']} (untouched)", flush=True)

    panel_path = art("ny_open_high_multiscale_panel.parquet")
    rebuild = True
    if panel_path.exists():
        probe = pd.read_parquet(panel_path)
        need = {"x_align_1_5", "x_align_1_5_15", "x_rev_short_vs_med", "fwd_15", "r1", "r5", "r15"}
        if need.issubset(probe.columns) and len(probe) > 1000:
            panel = probe
            rebuild = False
            print(f"Reusing panel rows={len(panel)}", flush=True)

    if rebuild:
        df = load_nq()
        print("Building context...", flush=True)
        ctx_df = build_day_context(df)
        ctx_map = {r["session_date"]: r for _, r in ctx_df.iterrows()}

        print("Indexing RTH...", flush=True)
        rth_map: dict = {}
        for sd, g in df.groupby("session_date", sort=False):
            if sd not in ctx_map:
                continue
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
            if len(rth) >= 100:
                rth_map[sd] = rth

        rows: list[dict] = []
        n_days = 0
        for sd, ctx in ctx_map.items():
            rth = rth_map.get(sd)
            if rth is None:
                continue
            n_days += 1
            for off in ARM_OFFSETS:
                # Need at least 15m of path for 15m scale
                if off < 15:
                    continue
                T = NY_OPEN + off
                to_T = rth[rth["ny_min"] <= T].reset_index(drop=True)
                st = state_at_T(to_T, ctx, T)
                if st is None or not is_high(st["rng_onr"], off):
                    continue
                fwd = fwd_from_next(rth, T)
                if fwd is None:
                    continue

                r1 = scale_ret(rth, T, 1)
                r5 = scale_ret(rth, T, 5)
                r15 = scale_ret(rth, T, 15)
                # acceleration: short vs medium magnitude/sign
                # prior 5m ending at T-5
                r5_prev = scale_ret(rth, T - 5, 5) if off >= 20 else np.nan

                s1, s5, s15 = sgn(r1), sgn(r5), sgn(r15)
                s5p = sgn(r5_prev)

                # 1) 1m vs 5m alignment → that direction; else 0
                x_align_1_5 = s1 if (s1 != 0 and s1 == s5) else 0
                # 2) 1m vs 5m vs 15m full agreement
                x_align_1_5_15 = s1 if (s1 != 0 and s1 == s5 == s15) else 0
                # 3) 5m vs 15m trend agreement
                x_align_5_15 = s5 if (s5 != 0 and s5 == s15) else 0
                # 4) short-term acceleration vs medium direction:
                #    |r1| > |r5|/5 (faster short) and same sign as r15 → follow med
                if s15 != 0 and np.isfinite(r1) and np.isfinite(r5):
                    faster = abs(r1) > abs(r5) / 5.0
                    x_accel_with_med = s15 if (faster and s1 == s15) else 0
                else:
                    x_accel_with_med = 0
                # 5) short-term reversal against medium-scale trend
                #    s1 opposite s15 → fade short / follow medium
                x_rev_short_vs_med = s15 if (s1 != 0 and s15 != 0 and s1 != s15) else 0
                # 6) multi-scale disagreement → follow short
                x_disagree_follow_short = s1 if (s1 != 0 and s15 != 0 and s1 != s15) else 0
                # 7) 5m trend continuation (single medium scale — control / baseline-ish)
                x_follow_5 = s5
                # 8) 15m trend continuation
                x_follow_15 = s15
                # 9) acceleration of 5m blocks: current 5m same sign as prior 5m
                x_5m_persist = s5 if (s5 != 0 and s5 == s5p) else 0
                # 10) 5m flip vs prior 5m → follow new 5m
                x_5m_flip = s5 if (s5 != 0 and s5p != 0 and s5 != s5p) else 0

                rows.append(
                    {
                        "session_date": str(sd),
                        "year": int(ctx["year"]),
                        "dow": int(ctx["dow"]),
                        "split": str(ctx["split"]),
                        "T_offset": off,
                        "T_ny": T,
                        "dir_sign": int(st["dir_sign"]) if st["dir_sign"] != 0 else 0,
                        "r1": r1,
                        "r5": r5,
                        "r15": r15,
                        "x_align_1_5": x_align_1_5,
                        "x_align_1_5_15": x_align_1_5_15,
                        "x_align_5_15": x_align_5_15,
                        "x_accel_with_med": x_accel_with_med,
                        "x_rev_short_vs_med": x_rev_short_vs_med,
                        "x_disagree_follow_short": x_disagree_follow_short,
                        "x_follow_5": x_follow_5,
                        "x_follow_15": x_follow_15,
                        "x_5m_persist": x_5m_persist,
                        "x_5m_flip": x_5m_flip,
                        **{f"fwd_{H}": fwd[f"fwd_{H}"] for H in HORIZONS},
                    }
                )
            if n_days % 500 == 0:
                print(f"  days={n_days} rows={len(rows)}", flush=True)

        panel = pd.DataFrame(rows)
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)} days~{panel['session_date'].nunique()}", flush=True)

    mechanisms = [
        ("align_1_5", "x_align_1_5"),
        ("align_1_5_15", "x_align_1_5_15"),
        ("align_5_15", "x_align_5_15"),
        ("accel_with_med", "x_accel_with_med"),
        ("rev_short_vs_med", "x_rev_short_vs_med"),
        ("disagree_follow_short", "x_disagree_follow_short"),
        ("follow_5", "x_follow_5"),
        ("follow_15", "x_follow_15"),
        ("persist_5m", "x_5m_persist"),
        ("flip_5m", "x_5m_flip"),
    ]

    # Only clocks where off>=15 exist in panel
    offsets = sorted(panel["T_offset"].unique().tolist())

    results: list[dict[str, Any]] = []
    for off in offsets:
        sub = panel[panel["T_offset"] == off]
        if len(sub) < 50:
            continue
        for split in ("IS", "Validation", "OOS", "ALL"):
            base = sub if split == "ALL" else sub[sub["split"] == split]
            if len(base) < 30:
                continue
            for H in HORIZONS:
                follow = base[base["dir_sign"] != 0]
                fb = (follow[f"fwd_{H}"] * follow["dir_sign"]).to_numpy(float)
                fb = fb[np.isfinite(fb)]
                follow_win = float(np.mean(fb > 0)) if len(fb) else np.nan
                follow_mean = float(np.mean(fb)) if len(fb) else np.nan
                long_s = base[f"fwd_{H}"].to_numpy(float)
                long_win = float(np.nanmean(long_s > 0))
                long_mean = float(np.nanmean(long_s))

                results.append(
                    {
                        "mechanism": "HIGH_ALONE_FOLLOW",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(len(fb)),
                        "win": follow_win,
                        "mean": follow_mean,
                        "rate": float(len(follow) / len(base)) if len(base) else np.nan,
                    }
                )
                results.append(
                    {
                        "mechanism": "HIGH_ALONE_LONG",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(np.isfinite(long_s).sum()),
                        "win": long_win,
                        "mean": long_mean,
                        "rate": 1.0,
                    }
                )

                for mech, col in mechanisms:
                    s = base[base[col] != 0]
                    if len(s) < 25:
                        continue
                    signed = (s[f"fwd_{H}"] * s[col]).to_numpy(float)
                    signed = signed[np.isfinite(signed)]
                    if len(signed) < 25:
                        continue
                    win = float(np.mean(signed > 0))
                    mean = float(np.mean(signed))
                    results.append(
                        {
                            "mechanism": mech,
                            "T_offset": off,
                            "horizon": H,
                            "split": split,
                            "n": int(len(signed)),
                            "n_high": int(len(base)),
                            "rate": float(len(s) / len(base)),
                            "win": win,
                            "mean": mean,
                            "follow_win": follow_win,
                            "delta_win_vs_follow": win - follow_win if np.isfinite(follow_win) else np.nan,
                            "delta_mean_vs_follow": mean - follow_mean if np.isfinite(follow_mean) else np.nan,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("ny_open_high_multiscale_results.csv"), index=False)
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
    is_rows = res_df[(res_df["split"] == "IS") & (~res_df["mechanism"].str.startswith("HIGH_ALONE"))]
    for _, r in is_rows.iterrows():
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
        col = next(c for m, c in mechanisms if m == mech)
        yrs = year_stats(col, off, H)
        is_win, v_win, o_win = float(r["win"]), float(v["win"]), float(o["win"])
        is_d = float(r["delta_win_vs_follow"]) if np.isfinite(r["delta_win_vs_follow"]) else np.nan
        v_d = float(v["delta_win_vs_follow"]) if np.isfinite(v["delta_win_vs_follow"]) else np.nan
        o_d = float(o["delta_win_vs_follow"]) if np.isfinite(o["delta_win_vs_follow"]) else np.nan
        is_mean, v_mean, o_mean = float(r["mean"]), float(v["mean"]), float(o["mean"])
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
            and abs(y25 - y26) <= 0.15
        )
        # Incremental over HIGH: require material stable lift
        lift_ok = np.isfinite(is_d) and is_d >= 0.03 and np.isfinite(v_d) and v_d > 0 and np.isfinite(o_d) and o_d > 0
        abs_ok = is_win >= 0.53 and v_win >= 0.52 and o_win >= 0.52
        payoff_ok = is_mean > 0 and v_mean > 0 and o_mean > 0
        strong = lift_ok and abs_ok and year_ok and payoff_ok and is_d >= 0.05
        soft = (
            ((lift_ok and is_d >= 0.03) or (abs_ok and is_win >= 0.545))
            and year_ok
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
                    "IS_win": is_win,
                    "IS_mean": is_mean,
                    "IS_delta": is_d,
                    "Val_win": v_win,
                    "Val_delta": v_d,
                    "OOS_win": o_win,
                    "OOS_delta": o_d,
                    "y2025_win": y25,
                    "y2026_win": y26,
                    "y2025_n": y25n,
                    "y2026_n": y26n,
                }
            )

    candidates.sort(
        key=lambda x: (0 if x["tier"] == "strong" else 1, -(x["IS_delta"] if np.isfinite(x["IS_delta"]) else -1))
    )

    stability = []
    if candidates:
        cdf = pd.DataFrame(candidates)
        for (mech, H), g in cdf.groupby(["mechanism", "horizon"]):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            # median incremental lift
            stability.append(
                {
                    "mechanism": mech,
                    "horizon": int(H),
                    "n_clocks": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "median_IS_delta": float(g["IS_delta"].median()),
                    "median_IS_win": float(g["IS_win"].median()),
                }
            )

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    multi_strong = [s for s in stability if s["n_clocks_strong"] >= 3]
    # Extra kill: soft-only ~55% without multi-clock strong incremental
    multi_soft_incremental = [
        s
        for s in stability
        if s["n_clocks"] >= 3 and s["median_IS_delta"] >= 0.03 and s["n_clocks_strong"] == 0
    ]

    if multi_strong:
        verdict = "A"
        verdict_text = (
            "Multi-scale X provides multi-clock year-stable incremental directional lift inside HIGH."
        )
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Multi-scale leftovers exist (~soft/single-clock) without stable multi-clock "
            "incremental improvement over HIGH. Kill family for promotion."
        )
    else:
        verdict = "C"
        verdict_text = (
            "No directional information from multi-scale family inside HIGH beyond HIGH alone."
        )

    # Force kill emphasis if only weak ~55% without multi strong
    if verdict == "B" and not multi_strong:
        kill_family = True
    elif verdict == "C":
        kill_family = True
    else:
        kill_family = False

    mech_summary = []
    is_only = res_df[(res_df["split"] == "IS") & (~res_df["mechanism"].str.startswith("HIGH_ALONE"))]
    for mech, _ in mechanisms:
        g = is_only[is_only["mechanism"] == mech]
        if len(g) == 0:
            continue
        mech_summary.append(
            {
                "mechanism": mech,
                "IS_med_win": float(g["win"].median()),
                "IS_med_delta_vs_follow": float(g["delta_win_vs_follow"].median()),
                "IS_med_n": float(g["n"].median()),
            }
        )
    mech_summary.sort(key=lambda x: -x["IS_med_delta_vs_follow"])

    report = {
        "stage": "high_multiscale_directional",
        "family": "multi_scale",
        "verdict": verdict,
        "kill_family": kill_family,
        "verdict_text": verdict_text,
        "frozen_gate": GATE["primary_arm"],
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_clock_strong_mechs": len(multi_strong),
        "n_multi_clock_soft_only": len(multi_soft_incremental),
        "mechanism_IS_summary": mech_summary,
        "top_candidates": candidates[:20],
        "stability": stability,
        "pivot_if_killed": (
            "Stop manufacturing direction inside HIGH. "
            "Search directional mechanism independently; then test whether frozen HIGH improves its timing."
        ),
    }
    with open(art("ny_open_high_multiscale_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# HIGH + Multi-Scale Directional — Minimal Report")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(f"Frozen HIGH: `{GATE['primary_arm']}` (untouched). Kill family: **{kill_family}**.")
    md.append("")
    md.append(f"Strong cells: {strong_n} · Soft: {soft_n} · Multi-clock strong mechs: {len(multi_strong)}")
    md.append("")
    md.append("## Mechanism IS summary (median Δ vs HIGH-FOLLOW)")
    md.append("")
    md.append("| Mechanism | med n | med win | med Δ |")
    md.append("|-----------|-------|---------|-------|")
    for m in mech_summary:
        md.append(
            f"| `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | "
            f"{pp(m['IS_med_delta_vs_follow'])} |"
        )
    md.append("")
    md.append("## Surviving cells")
    md.append("")
    if not candidates:
        md.append("None.")
    else:
        md.append("| Tier | X | T+ | H | IS n | IS | Δ | Val | OOS | 2025 | 2026 |")
        md.append("|------|---|----|---|------|----|---|-----|-----|------|------|")
        for c in candidates[:15]:
            md.append(
                f"| {c['tier']} | `{c['mechanism']}` | +{c['T_offset']} | {c['horizon']} | "
                f"{c['IS_n']} | {pct(c['IS_win'])} | {pp(c['IS_delta'])} | "
                f"{pct(c['Val_win'])} | {pct(c['OOS_win'])} | "
                f"{pct(c.get('y2025_win'))} | {pct(c.get('y2026_win'))} |"
            )
    md.append("")
    md.append("## Stability")
    md.append("")
    if not stability:
        md.append("n/a")
    else:
        for s in stability:
            md.append(
                f"- `{s['mechanism']}` H{s['horizon']}: {s['n_clocks']} clocks "
                f"({s['n_clocks_strong']} strong) Δmed={pp(s['median_IS_delta'])} {s['clocks']}"
            )
    md.append("")
    md.append(f"## Final: **{verdict}**")
    md.append("")
    if kill_family:
        md.append(
            "Kill multi-scale family. Directional search **inside HIGH is exhausted** "
            "(price / levels / ES / volume / multi-scale)."
        )
        md.append("")
        md.append(
            "Pivot: find direction **independently**, then test whether frozen HIGH improves its timing."
        )
    md.append("")
    (art("ny_open_high_multiscale_report.md")).write_text("\n".join(md), encoding="utf-8")
    print(f"VERDICT: {verdict} kill_family={kill_family}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n} multi_strong: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
