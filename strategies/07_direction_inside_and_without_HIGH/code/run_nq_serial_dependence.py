"""
NQ Intrinsic Directional Discovery — Family 1: Serial Dependence

NO HIGH gate. Broader liquid RTH (09:30–15:30 ET).
Question: Is there genuine short-horizon directional memory in NQ?

Each mechanism independent. IS thresholds only. No optimization.
Compare continuation/fade vs 50% (and vs same-TOD unconditional long).
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

from common.nq_session import art, ART, NY_OPEN, SESSION_START, load_nq

warnings.filterwarnings("ignore", category=FutureWarning)

# Liquid session decision clocks (minutes after midnight ET)
SESSION_END = 15 * 60 + 30  # 15:30 — leave room for 60m forward
DECISION_OFFSETS = tuple(range(0, SESSION_END - NY_OPEN + 1, 5))  # 09:30..15:30 every 5m
LOOKBACKS = (1, 5, 15, 30)
FWD_HORIZONS = (5, 15, 30, 60)
IS_Y = set(range(2010, 2022))
VAL_Y = {2022, 2023, 2024}
OOS_Y = {2025, 2026}


def split_of(y: int) -> str:
    if y in IS_Y:
        return "IS"
    if y in VAL_Y:
        return "Validation"
    if y in OOS_Y:
        return "OOS"
    return "OTHER"


def main() -> None:
    print("=== Serial Dependence Discovery (NO HIGH) ===", flush=True)
    panel_path = art("nq_serial_dep_panel.parquet")
    rebuild = True
    if panel_path.exists():
        probe = pd.read_parquet(panel_path)
        if {"x_follow_5", "x_fade_5_ext", "fwd_15", "z_5"}.issubset(probe.columns) and len(probe) > 50000:
            panel = probe
            rebuild = False
            print(f"Reusing panel rows={len(panel)}", flush=True)

    if rebuild:
        df = load_nq()
        print("Indexing RTH...", flush=True)
        rows: list[dict] = []
        n_days = 0
        # ATR history for vol norm: rolling mean TR of prior session RTH (causal across days)
        atr_hist: list[float] = []

        for sd, g in df.groupby("session_date", sort=True):
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 16 * 60)].reset_index(drop=True)
            if len(rth) < 200:
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

            # session ATR so far proxy: mean TR of bars so far; also use prior-day ATR floor
            prev_c = np.concatenate([[o[0]], c[:-1]])
            tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
            prior_atr = float(np.median(atr_hist[-20:])) if len(atr_hist) >= 5 else float(np.mean(tr[:30]))

            # signed 1m returns for run length
            r1m = np.concatenate([[0.0], np.diff(c)])

            day_trs = []
            for off in DECISION_OFFSETS:
                T = NY_OPEN + off
                if T not in idx:
                    continue
                j = idx[T]
                # need forward 60m
                if T + max(FWD_HORIZONS) not in idx and (T + max(FWD_HORIZONS)) > ny[-1]:
                    # check enough bars after
                    after = np.where(ny > T)[0]
                    if len(after) < max(FWD_HORIZONS):
                        continue
                after_idx = np.where(ny > T)[0]
                if len(after_idx) < max(FWD_HORIZONS):
                    continue

                # vol unit at T
                atr_so_far = float(np.mean(tr[: j + 1])) if j >= 5 else prior_atr
                vol = max(atr_so_far, 0.05 * prior_atr, 0.25)

                entry_i = int(after_idx[0])
                entry = float(o[entry_i])  # next bar open after T

                fwds = {}
                for H in FWD_HORIZONS:
                    # H minutes later close relative to entry open
                    # find bar with ny_min == T+H or entry_i + H - 1
                    target_ny = T + H
                    if target_ny in idx:
                        fwds[H] = float(c[idx[target_ny]] - entry)
                    else:
                        k = entry_i + H - 1
                        if k >= len(c):
                            fwds[H] = np.nan
                        else:
                            fwds[H] = float(c[k] - entry)

                if not all(np.isfinite(fwds[H]) for H in FWD_HORIZONS):
                    continue

                # lookback returns ending at T close
                lb = {}
                zb = {}
                for L in LOOKBACKS:
                    start_ny = T - L + 1
                    if start_ny < NY_OPEN or start_ny not in idx:
                        # use earliest available
                        if j + 1 < L:
                            lb[L] = np.nan
                            zb[L] = np.nan
                            continue
                        i0 = j - L + 1
                    else:
                        i0 = idx[start_ny]
                    ret = float(c[j] - o[i0])
                    lb[L] = ret
                    zb[L] = ret / vol

                # signed run length of 1m closes ending at j
                run = 0
                if j >= 1:
                    s0 = np.sign(r1m[j])
                    if s0 != 0:
                        run = 1
                        for t in range(j - 1, max(0, j - 20) - 1, -1):
                            if np.sign(r1m[t]) == s0:
                                run += 1
                            else:
                                break
                        run = int(run * s0)  # signed

                rows.append(
                    {
                        "session_date": str(sd),
                        "year": year,
                        "dow": dow,
                        "split": split,
                        "T_offset": off,
                        "T_ny": T,
                        "vol": vol,
                        "run": run,
                        **{f"ret_{L}": lb.get(L, np.nan) for L in LOOKBACKS},
                        **{f"z_{L}": zb.get(L, np.nan) for L in LOOKBACKS},
                        **{f"fwd_{H}": fwds[H] for H in FWD_HORIZONS},
                    }
                )
                day_trs.append(float(tr[j]))

            if day_trs:
                atr_hist.append(float(np.mean(day_trs)))
            if n_days % 500 == 0:
                print(f"  days={n_days} rows={len(rows)}", flush=True)

        panel = pd.DataFrame(rows)
        # IS thresholds for |z_L|
        thresholds: dict[str, dict[int, float]] = {}
        is_p = panel[panel["split"] == "IS"]
        for L in LOOKBACKS:
            thresholds[f"z_{L}"] = {}
            for off in DECISION_OFFSETS:
                s = is_p.loc[is_p["T_offset"] == off, f"z_{L}"].abs().dropna()
                if len(s) < 100:
                    continue
                thresholds[f"z_{L}"][off] = float(s.quantile(0.66))
        with open(art("nq_serial_dep_thresholds_IS.json"), "w", encoding="utf-8") as f:
            json.dump({"z_abs_p66": thresholds, "note": "IS only; extreme = |z|>=p66"}, f, indent=2)

        # Labels
        def extreme(off: int, L: int, z: float) -> bool:
            th = thresholds.get(f"z_{L}", {}).get(off)
            if th is None or not np.isfinite(z):
                return False
            return abs(z) >= th

        xl = []
        for _, r in panel.iterrows():
            off = int(r["T_offset"])
            lab = {}
            for L in LOOKBACKS:
                ret = float(r[f"ret_{L}"])
                z = float(r[f"z_{L}"])
                d = 1 if ret > 0 else (-1 if ret < 0 else 0)
                lab[f"x_follow_{L}"] = d
                lab[f"x_fade_{L}"] = -d if d != 0 else 0
                ext = extreme(off, L, z)
                lab[f"x_follow_{L}_ext"] = d if ext and d != 0 else 0
                lab[f"x_fade_{L}_ext"] = -d if ext and d != 0 else 0
            run = int(r["run"])
            # continue signed run if |run|>=3
            if abs(run) >= 3:
                lab["x_run_continue"] = 1 if run > 0 else -1
                lab["x_run_fade"] = -lab["x_run_continue"]
            else:
                lab["x_run_continue"] = 0
                lab["x_run_fade"] = 0
            # alternating: last two 1m moves opposite of prior? use run==+/-1 after opposite — simple fade after run>=2
            if abs(run) == 2:
                lab["x_alt_fade"] = -1 if run > 0 else 1
            else:
                lab["x_alt_fade"] = 0
            xl.append(lab)

        panel = pd.concat([panel.reset_index(drop=True), pd.DataFrame(xl)], axis=1)
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)} days~{panel['session_date'].nunique()}", flush=True)

    mechanisms = []
    for L in LOOKBACKS:
        mechanisms += [
            (f"follow_{L}", f"x_follow_{L}"),
            (f"fade_{L}", f"x_fade_{L}"),
            (f"follow_{L}_ext", f"x_follow_{L}_ext"),
            (f"fade_{L}_ext", f"x_fade_{L}_ext"),
        ]
    mechanisms += [
        ("run_continue", "x_run_continue"),
        ("run_fade", "x_run_fade"),
        ("alt_fade", "x_alt_fade"),
    ]

    # Evaluate on a subset of clocks for tractability + stability: every 15m + key opens
    EVAL_OFFSETS = tuple(range(0, SESSION_END - NY_OPEN + 1, 15))  # 09:30, 09:45, ...
    results: list[dict[str, Any]] = []

    for off in EVAL_OFFSETS:
        sub = panel[panel["T_offset"] == off]
        if len(sub) < 200:
            continue
        for split in ("IS", "Validation", "OOS"):
            base = sub[sub["split"] == split]
            if len(base) < 80:
                continue
            for H in FWD_HORIZONS:
                long_s = base[f"fwd_{H}"].to_numpy(float)
                long_win = float(np.nanmean(long_s > 0))
                long_mean = float(np.nanmean(long_s))
                results.append(
                    {
                        "mechanism": "UNCOND_LONG",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(np.isfinite(long_s).sum()),
                        "win": long_win,
                        "mean": long_mean,
                        "rate": 1.0,
                        "delta_vs_50": long_win - 0.5,
                    }
                )
                for mech, col in mechanisms:
                    s = base[base[col] != 0]
                    if len(s) < 40:
                        continue
                    signed = (s[f"fwd_{H}"] * s[col]).to_numpy(float)
                    signed = signed[np.isfinite(signed)]
                    if len(signed) < 40:
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
                            "n_base": int(len(base)),
                            "rate": float(len(s) / len(base)),
                            "win": win,
                            "mean": mean,
                            "delta_vs_50": win - 0.5,
                            "delta_vs_long": win - long_win,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_serial_dep_results.csv"), index=False)
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
        if int(r["n"]) < 120:
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
        if int(v["n"]) < 60 or int(o["n"]) < 40:
            continue
        col = next(c for m, c in mechanisms if m == mech)
        yrs = year_stats(col, off, H)
        is_win, v_win, o_win = float(r["win"]), float(v["win"]), float(o["win"])
        is_d50 = float(r["delta_vs_50"])
        v_d50, o_d50 = float(v["delta_vs_50"]), float(o["delta_vs_50"])
        is_mean, v_mean, o_mean = float(r["mean"]), float(v["mean"]), float(o["mean"])
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
        # Material vs coin: need lift and same sign across splits
        lift_ok = is_d50 >= 0.03 and v_d50 > 0 and o_d50 > 0
        abs_ok = is_win >= 0.53 and v_win >= 0.52 and o_win >= 0.52
        payoff_ok = is_mean > 0 and v_mean > 0 and o_mean > 0
        strong = lift_ok and abs_ok and year_ok and payoff_ok and is_d50 >= 0.04
        soft = (
            ((lift_ok and is_d50 >= 0.025) or (abs_ok and is_win >= 0.54))
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
                    "IS_d50": is_d50,
                    "Val_win": v_win,
                    "Val_d50": v_d50,
                    "OOS_win": o_win,
                    "OOS_d50": o_d50,
                    "y2025_win": y25,
                    "y2026_win": y26,
                    "y2025_n": y25n,
                    "y2026_n": y26n,
                }
            )

    candidates.sort(
        key=lambda x: (0 if x["tier"] == "strong" else 1, -x["IS_d50"] if np.isfinite(x["IS_d50"]) else 0)
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
        verdict_text = "NQ shows multi-clock year-stable short-horizon serial dependence."
        kill = False
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Weak/inconsistent serial dependence leftovers; no multi-clock strong memory. "
            "Do not promote."
        )
        kill = True
    else:
        verdict = "C"
        verdict_text = (
            "No genuine short-horizon directional memory detected under hostile gates "
            "(continuation/fade/extreme/runs)."
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
                "IS_med_win": float(g["win"].median()),
                "IS_med_d50": float(g["delta_vs_50"].median()),
                "IS_med_n": float(g["n"].median()),
            }
        )
    mech_summary.sort(key=lambda x: -abs(x["IS_med_d50"]))

    # Uncond long snapshot
    unc = []
    for off in (0, 30, 60, 120, 180):
        for H in (15, 30):
            s = res_df[
                (res_df["mechanism"] == "UNCOND_LONG")
                & (res_df["T_offset"] == off)
                & (res_df["horizon"] == H)
                & (res_df["split"] == "IS")
            ]
            if len(s):
                unc.append(
                    {
                        "T_offset": off,
                        "horizon": H,
                        "IS_win": float(s.iloc[0]["win"]),
                        "IS_mean": float(s.iloc[0]["mean"]),
                    }
                )

    report = {
        "stage": "serial_dependence_no_HIGH",
        "family": "serial_dependence",
        "verdict": verdict,
        "kill_family": kill,
        "verdict_text": verdict_text,
        "scope": "RTH 09:30-15:30 every 5m build / eval every 15m; NO HIGH",
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_clock_strong": len(multi_strong),
        "unc_long_IS": unc,
        "mechanism_IS_summary": mech_summary,
        "top_candidates": candidates[:20],
        "stability": stability,
        "next_if_killed": "return_imbalance_asymmetry family",
        "pivot_doc": "artifacts/research_pivot_independent_direction.md",
    }
    with open(art("nq_serial_dep_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# NQ Serial Dependence — Minimal Report (NO HIGH)")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(f"Kill family: **{kill}**. Scope: liquid RTH, independent of frozen HIGH.")
    md.append("")
    md.append(f"Strong: {strong_n} · Soft: {soft_n} · Multi-clock strong mechs: {len(multi_strong)}")
    md.append("")
    md.append("## Uncond long IS (sanity)")
    md.append("")
    md.append("| T+ | H | win | mean |")
    md.append("|----|---|-----|------|")
    for u in unc:
        md.append(f"| +{u['T_offset']}m | {u['horizon']} | {pct(u['IS_win'])} | {u['IS_mean']:+.2f} |")
    md.append("")
    md.append("## Mechanism IS summary (|Δ| vs 50%)")
    md.append("")
    md.append("| Mechanism | med n | med win | med Δ50 |")
    md.append("|-----------|-------|---------|---------|")
    for m in mech_summary[:12]:
        md.append(
            f"| `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | {pp(m['IS_med_d50'])} |"
        )
    md.append("")
    md.append("## Surviving cells")
    md.append("")
    if not candidates:
        md.append("None.")
    else:
        md.append("| Tier | X | T+ | H | IS n | IS | Δ50 | Val | OOS | 2025 | 2026 |")
        md.append("|------|---|----|---|------|----|-----|-----|-----|------|------|")
        for c in candidates[:15]:
            md.append(
                f"| {c['tier']} | `{c['mechanism']}` | +{c['T_offset']} | {c['horizon']} | "
                f"{c['IS_n']} | {pct(c['IS_win'])} | {pp(c['IS_d50'])} | "
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
                f"({s['n_clocks_strong']} strong) {s['clocks']}"
            )
    md.append("")
    md.append(f"## Final: **{verdict}**")
    md.append("")
    if kill:
        md.append("Kill serial-dependence family for promotion.")
        md.append("Next independent family: **return / imbalance asymmetry** (vol-standardized).")
        md.append("HIGH remains frozen for later timing tests only.")
    md.append("")
    (art("nq_serial_dep_report.md")).write_text("\n".join(md), encoding="utf-8")
    print(f"VERDICT: {verdict} kill={kill}", flush=True)


if __name__ == "__main__":
    main()
