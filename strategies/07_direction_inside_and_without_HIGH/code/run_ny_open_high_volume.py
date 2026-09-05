"""
NQ HIGH + Volume / Participation-Shock Directional Discovery

FROZEN gate (untouched): vol_expansion_high
Family: VOLUME only. No combinations. No ES/VWAP/ORB/SMT rescue.

Each X independent vs HIGH alone at same T/H.
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

# Fixed a priori (not swept): lookback windows for TOD volume history
TOD_LOOKBACK_DAYS = 20
ACCEL_WINDOW = 5  # minutes


def main() -> None:
    print("=== HIGH + Volume Directional Discovery ===", flush=True)
    print(f"Frozen ARM: {GATE['primary_arm']} (untouched)", flush=True)

    panel_path = art("ny_open_high_volume_panel.parquet")
    rebuild = True
    if panel_path.exists():
        probe = pd.read_parquet(panel_path)
        need = {"x_tod_high_vol_follow", "x_vol_accel_follow", "fwd_15", "vol_tod_pct"}
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

        # Causal same-TOD volume history: for each (session, T_offset), sum volume 09:30..T
        # Build chronologically so history uses only prior days.
        sessions = sorted(rth_map.keys())
        # hist[off] = list of prior-day vol_sum values (most recent last)
        hist: dict[int, list[float]] = {off: [] for off in ARM_OFFSETS}

        rows: list[dict] = []
        for i, sd in enumerate(sessions):
            ctx = ctx_map[sd]
            rth = rth_map[sd]
            o930 = float(ctx["open_930"])

            # Precompute cumulative volume from open
            vols = rth["volume"].to_numpy(np.float64)
            ny = rth["ny_min"].to_numpy(int)
            # map ny_min -> index
            idx_by_ny = {int(n): j for j, n in enumerate(ny)}

            day_vol_at_off: dict[int, float] = {}

            for off in ARM_OFFSETS:
                T = NY_OPEN + off
                if T not in idx_by_ny:
                    continue
                j = idx_by_ny[T]
                to_T = rth.iloc[: j + 1].reset_index(drop=True)
                st = state_at_T(to_T, ctx, T)
                if st is None:
                    continue

                vol_sum = float(vols[: j + 1].sum())
                day_vol_at_off[off] = vol_sum

                # TOD percentile vs prior days only (causal)
                prior = hist[off]
                if len(prior) >= 10:
                    vol_tod_pct = float(np.mean(np.asarray(prior, float) <= vol_sum))
                else:
                    vol_tod_pct = np.nan

                if not is_high(st["rng_onr"], off):
                    continue

                fwd = fwd_from_next(rth, T)
                if fwd is None:
                    continue

                last_c = float(to_T.iloc[-1]["close"])
                move = last_c - o930
                dir_sign = int(st["dir_sign"]) if st["dir_sign"] != 0 else 0
                abs_move = abs(move)

                # Short-term volume acceleration: last 5m vs prior 5m
                vol_last5 = float(vols[max(0, j - ACCEL_WINDOW + 1) : j + 1].sum())
                vol_prev5 = float(vols[max(0, j - 2 * ACCEL_WINDOW + 1) : max(0, j - ACCEL_WINDOW + 1)].sum())
                if vol_prev5 > 0:
                    vol_accel = vol_last5 / vol_prev5
                else:
                    vol_accel = np.nan

                # Displacement per unit volume (efficiency): |move| / vol_sum (pts per contract)
                # Higher = more price per volume (thin); lower = heavy participation for move
                disp_per_vol = abs_move / vol_sum if vol_sum > 0 else np.nan

                # Body efficiency on last bar
                bar = to_T.iloc[-1]
                rng = float(bar["high"] - bar["low"])
                body = abs(float(bar["close"] - bar["open"]))
                body_eff = body / rng if rng > 0 else np.nan
                bar_dir = 1 if float(bar["close"]) > float(bar["open"]) else (-1 if float(bar["close"]) < float(bar["open"]) else 0)

                rows.append(
                    {
                        "session_date": str(sd),
                        "year": int(ctx["year"]),
                        "dow": int(ctx["dow"]),
                        "split": str(ctx["split"]),
                        "T_offset": off,
                        "T_ny": T,
                        "dir_sign": dir_sign,
                        "vol_sum": vol_sum,
                        "vol_tod_pct": vol_tod_pct,
                        "vol_accel": vol_accel,
                        "disp_per_vol": disp_per_vol,
                        "body_eff": body_eff,
                        "bar_dir": bar_dir,
                        "abs_move": abs_move,
                        **{f"fwd_{H}": fwd[f"fwd_{H}"] for H in HORIZONS},
                    }
                )

            # After processing day: append today's vols to history (for future days)
            for off, vsum in day_vol_at_off.items():
                hist[off].append(vsum)
                if len(hist[off]) > TOD_LOOKBACK_DAYS:
                    hist[off] = hist[off][-TOD_LOOKBACK_DAYS:]

            if (i + 1) % 500 == 0:
                print(f"  days={i+1} HIGH rows={len(rows)}", flush=True)

        panel = pd.DataFrame(rows)
        if len(panel) == 0:
            raise RuntimeError("Empty HIGH+volume panel")

        # IS-only thresholds for volume features (per T_offset)
        thresholds: dict[str, dict[int, dict[str, float]]] = {}
        is_p = panel[panel["split"] == "IS"]
        for feat in ("vol_tod_pct", "vol_accel", "disp_per_vol", "body_eff", "abs_move"):
            thresholds[feat] = {}
            for off in ARM_OFFSETS:
                s = is_p.loc[is_p["T_offset"] == off, feat].dropna()
                if len(s) < 80:
                    continue
                thresholds[feat][off] = {
                    "p33": float(s.quantile(0.33)),
                    "p66": float(s.quantile(0.66)),
                }
        with open(art("ny_open_high_volume_thresholds_IS.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tod_lookback_days": TOD_LOOKBACK_DAYS,
                    "accel_window_min": ACCEL_WINDOW,
                    "features": thresholds,
                    "note": "IS terciles only; not optimized on Val/OOS",
                },
                f,
                indent=2,
            )

        # Attach X labels using frozen IS thresholds
        def lab(off: int, feat: str, side: str, val: float) -> bool:
            th = thresholds.get(feat, {}).get(off)
            if not th or not np.isfinite(val):
                return False
            if side == "high":
                return val >= th["p66"]
            return val <= th["p33"]

        x_rows = []
        for _, r in panel.iterrows():
            off = int(r["T_offset"])
            d = int(r["dir_sign"])
            bd = int(r["bar_dir"])
            vt = float(r["vol_tod_pct"]) if np.isfinite(r["vol_tod_pct"]) else np.nan
            va = float(r["vol_accel"]) if np.isfinite(r["vol_accel"]) else np.nan
            dp = float(r["disp_per_vol"]) if np.isfinite(r["disp_per_vol"]) else np.nan
            be = float(r["body_eff"]) if np.isfinite(r["body_eff"]) else np.nan

            high_tod = lab(off, "vol_tod_pct", "high", vt)
            low_tod = lab(off, "vol_tod_pct", "low", vt)
            high_accel = lab(off, "vol_accel", "high", va)
            low_accel = lab(off, "vol_accel", "low", va)
            # high disp_per_vol = thin participation for the move; low = heavy volume for move
            thin = lab(off, "disp_per_vol", "high", dp)
            heavy = lab(off, "disp_per_vol", "low", dp)
            high_body = lab(off, "body_eff", "high", be)

            # 1) Relative volume vs TOD → follow direction only if high/low TOD vol
            x_tod_high_vol_follow = d if (high_tod and d != 0) else 0
            x_tod_low_vol_follow = d if (low_tod and d != 0) else 0

            # 2) Volume percentile as participation regime + follow
            # (same as 1 operationally with p66/p33 — keep explicit alias labels)
            x_vol_pct_high_follow = x_tod_high_vol_follow
            x_vol_pct_low_follow = x_tod_low_vol_follow

            # 3) Volume acceleration
            x_vol_accel_follow = d if (high_accel and d != 0) else 0
            x_vol_decel_follow = d if (low_accel and d != 0) else 0

            # 4) Price displacement relative to volume
            # heavy participation + follow; thin + follow (test both independently)
            x_heavy_vol_follow = d if (heavy and d != 0) else 0
            x_thin_vol_follow = d if (thin and d != 0) else 0

            # 5) High-volume directional impulse vs low-volume movement
            # high TOD vol + directional move present
            x_hivol_impulse = d if (high_tod and d != 0) else 0
            x_lovol_move = d if (low_tod and d != 0) else 0

            # 6) Volume expansion + NQ direction (accel high + follow)
            x_vol_exp_dir = d if (high_accel and d != 0) else 0

            # 7) Volume expansion + body efficiency
            x_vol_exp_efficient = d if (high_accel and high_body and d != 0) else 0
            # also: high TOD vol + efficient body (independent of accel)
            x_hivol_efficient = bd if (high_tod and high_body and bd != 0) else 0

            x_rows.append(
                {
                    "x_tod_high_vol_follow": x_tod_high_vol_follow,
                    "x_tod_low_vol_follow": x_tod_low_vol_follow,
                    "x_vol_pct_high_follow": x_vol_pct_high_follow,
                    "x_vol_pct_low_follow": x_vol_pct_low_follow,
                    "x_vol_accel_follow": x_vol_accel_follow,
                    "x_vol_decel_follow": x_vol_decel_follow,
                    "x_heavy_vol_follow": x_heavy_vol_follow,
                    "x_thin_vol_follow": x_thin_vol_follow,
                    "x_hivol_impulse": x_hivol_impulse,
                    "x_lovol_move": x_lovol_move,
                    "x_vol_exp_dir": x_vol_exp_dir,
                    "x_vol_exp_efficient": x_vol_exp_efficient,
                    "x_hivol_efficient": x_hivol_efficient,
                }
            )

        panel = pd.concat([panel.reset_index(drop=True), pd.DataFrame(x_rows)], axis=1)
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)} days~{panel['session_date'].nunique()} -> {panel_path}", flush=True)

    mechanisms = [
        ("tod_high_vol_follow", "x_tod_high_vol_follow"),
        ("tod_low_vol_follow", "x_tod_low_vol_follow"),
        ("vol_pct_high_follow", "x_vol_pct_high_follow"),
        ("vol_pct_low_follow", "x_vol_pct_low_follow"),
        ("vol_accel_follow", "x_vol_accel_follow"),
        ("vol_decel_follow", "x_vol_decel_follow"),
        ("heavy_vol_follow", "x_heavy_vol_follow"),
        ("thin_vol_follow", "x_thin_vol_follow"),
        ("hivol_impulse", "x_hivol_impulse"),
        ("lovol_move", "x_lovol_move"),
        ("vol_exp_dir", "x_vol_exp_dir"),
        ("vol_exp_efficient", "x_vol_exp_efficient"),
        ("hivol_efficient", "x_hivol_efficient"),
    ]

    results: list[dict[str, Any]] = []
    for off in ARM_OFFSETS:
        sub = panel[panel["T_offset"] == off]
        if len(sub) < 50:
            continue
        for split in ("IS", "Validation", "OOS", "ALL"):
            base = sub if split == "ALL" else sub[sub["split"] == split]
            if len(base) < 30:
                continue
            for H in HORIZONS:
                long_s = base[f"fwd_{H}"].to_numpy(float)
                follow = base[base["dir_sign"] != 0]
                fb = (follow[f"fwd_{H}"] * follow["dir_sign"]).to_numpy(float)
                fb = fb[np.isfinite(fb)]
                follow_win = float(np.mean(fb > 0)) if len(fb) else np.nan
                follow_mean = float(np.mean(fb)) if len(fb) else np.nan
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
                        "rate": float(len(follow) / len(base)),
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
                            "delta_win_vs_long": win - long_win if np.isfinite(long_win) else np.nan,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("ny_open_high_volume_results.csv"), index=False)
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
            stability.append(
                {
                    "mechanism": mech,
                    "horizon": int(H),
                    "n_clocks": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                }
            )

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    multi_strong = [s for s in stability if s["n_clocks_strong"] >= 3]

    if multi_strong:
        verdict = "A"
        verdict_text = "Volume family provides multi-clock year-stable directional lift inside HIGH."
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Volume leftovers exist but fail multi-clock stability / consistency. "
            "Single-clock spikes ignored."
        )
    else:
        verdict = "C"
        verdict_text = "No directional information from volume/participation-shock family inside HIGH."

    # Compact per-mechanism IS median summary for report
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
        "stage": "high_volume_directional",
        "family": "volume_participation",
        "verdict": verdict,
        "verdict_full": f"{verdict}_volume_inside_HIGH",
        "verdict_text": verdict_text,
        "frozen_gate": GATE["primary_arm"],
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_clock_strong_mechs": len(multi_strong),
        "mechanism_IS_summary": mech_summary,
        "top_candidates": candidates[:20],
        "stability": stability,
        "next_if_C": "multi_scale_family",
    }
    with open(art("ny_open_high_volume_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# HIGH + Volume Directional — Minimal Report")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(f"Frozen HIGH: `{GATE['primary_arm']}` (untouched). Family: volume only.")
    md.append("")
    md.append(f"Strong cells: {strong_n} · Soft: {soft_n} · Multi-clock strong mechs: {len(multi_strong)}")
    md.append("")
    md.append("## Mechanism IS summary (median across clocks/horizons)")
    md.append("")
    md.append("| Mechanism | med n | med win | med Δ vs HIGH-FOLLOW |")
    md.append("|-----------|-------|---------|----------------------|")
    for m in mech_summary:
        md.append(
            f"| `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | "
            f"{pp(m['IS_med_delta_vs_follow'])} |"
        )
    md.append("")
    md.append("## Surviving cells (if any)")
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
        if not multi_strong and strong_n:
            md.append("")
            md.append("All strong cells fail multi-clock bar — not promotable.")
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
    if verdict == "C":
        md.append("Kill volume family. Next: multi-scale.")
    md.append("")
    (art("ny_open_high_volume_report.md")).write_text("\n".join(md), encoding="utf-8")
    print(f"VERDICT: {verdict}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n} multi_strong: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
