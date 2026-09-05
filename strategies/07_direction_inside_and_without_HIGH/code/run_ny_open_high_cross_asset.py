"""
NQ HIGH + Cross-Asset (ES) Directional Discovery

FROZEN gate (do not touch):
  HIGH/ARM = vol_expansion_high  (artifacts/frozen_opportunity_gate.md)

Family: CROSS-ASSET only (this pass).
  Volume and multi-scale are OUT OF SCOPE until this family is finished.

Question:
  Inside HIGH, does contemporaneous ES / NQ–ES relative information
  materially change NQ's forward directional distribution vs HIGH alone?

Each X tested independently. No combinations. No optimization.
No reopening of dead NQ price-pattern features.
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
from datetime import date as date_cls
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common.nq_session import (
    art,
    ART,
    NY_OPEN,
    SESSION_START,
    build_day_context,
    load_es,
    load_nq,
    state_at_T,
)
from run_ny_open_high_directional import (
    ARM_OFFSETS,
    GATE,
    HORIZONS,
    STATE_TH,
    fwd_from_next,
    is_high,
    th_get,
)

warnings.filterwarnings("ignore", category=FutureWarning)



def es_slice_to_T(es_rth: pd.DataFrame, T_ny: int) -> pd.DataFrame | None:
    sub = es_rth[es_rth["ny_min"] <= T_ny]
    if len(sub) < 3:
        return None
    if T_ny not in set(sub["ny_min"].tolist()):
        return None
    return sub.reset_index(drop=True)


def pct_ret(o: float, c: float) -> float:
    if not np.isfinite(o) or o == 0:
        return np.nan
    return (c - o) / o


def main() -> None:
    print("=== HIGH + Cross-Asset (ES) Directional Discovery ===", flush=True)
    print(f"Frozen ARM: {GATE['primary_arm']} (untouched)", flush=True)
    print("Family: CROSS-ASSET only. Volume/multi-scale deferred.", flush=True)

    panel_path = art("ny_open_high_xasset_panel.parquet")
    rebuild = True
    if panel_path.exists():
        probe = pd.read_parquet(panel_path)
        if {"x_follow_es", "x_rs_continue", "fwd_15", "es_ret"}.issubset(probe.columns) and len(probe) > 1000:
            panel = probe
            rebuild = False
            print(f"Reusing panel {panel_path} rows={len(panel)}", flush=True)

    if rebuild:
        print("Loading NQ + ES...", flush=True)
        nq = load_nq()
        es = load_es()
        print("Building NQ day context...", flush=True)
        ctx_df = build_day_context(nq)
        ctx_map = {r["session_date"]: r for _, r in ctx_df.iterrows()}

        print("Indexing RTH...", flush=True)
        nq_rth: dict = {}
        for sd, g in nq.groupby("session_date", sort=False):
            if sd not in ctx_map:
                continue
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
            if len(rth) >= 100:
                nq_rth[sd] = rth

        es_rth: dict = {}
        for sd, g in es.groupby("session_date", sort=False):
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
            if len(rth) >= 50:
                es_rth[sd] = rth
        print(f"NQ RTH days: {len(nq_rth)}  ES RTH days: {len(es_rth)}", flush=True)

        rows: list[dict] = []
        n_days = 0
        n_skip_es = 0
        for sd, ctx in ctx_map.items():
            nqr = nq_rth.get(sd)
            esr = es_rth.get(sd)
            if nqr is None:
                continue
            n_days += 1
            if esr is None:
                n_skip_es += 1
                continue

            # ES open at 09:30
            es_open_bars = esr[esr["ny_min"] == NY_OPEN]
            if len(es_open_bars) == 0:
                n_skip_es += 1
                continue
            es_o930 = float(es_open_bars.iloc[0]["open"])
            nq_o930 = float(ctx["open_930"])

            for off in ARM_OFFSETS:
                T = NY_OPEN + off
                to_T = nqr[nqr["ny_min"] <= T].reset_index(drop=True)
                st = state_at_T(to_T, ctx, T)
                if st is None or not is_high(st["rng_onr"], off):
                    continue

                es_to = es_slice_to_T(esr, T)
                if es_to is None:
                    continue

                fwd = fwd_from_next(nqr, T)
                if fwd is None:
                    continue

                nq_c = float(to_T.iloc[-1]["close"])
                es_c = float(es_to.iloc[-1]["close"])
                nq_ret = pct_ret(nq_o930, nq_c)
                es_ret = pct_ret(es_o930, es_c)
                if not np.isfinite(nq_ret) or not np.isfinite(es_ret):
                    continue

                # last 5m ES return (causal bars within last 5 minutes)
                es_5 = es_to[es_to["ny_min"] > T - 5]
                if len(es_5) >= 2:
                    es_ret5 = pct_ret(float(es_5.iloc[0]["open"]), float(es_5.iloc[-1]["close"]))
                else:
                    es_ret5 = np.nan

                nq_sign = 1 if nq_ret > 0 else (-1 if nq_ret < 0 else 0)
                es_sign = 1 if es_ret > 0 else (-1 if es_ret < 0 else 0)
                rs = nq_ret - es_ret
                rs_sign = 1 if rs > 0 else (-1 if rs < 0 else 0)

                # Independent X directions
                x_follow_es = es_sign
                x_rs_continue = rs_sign  # NQ outperforming → long
                x_rs_fade = -rs_sign if rs_sign != 0 else 0
                x_es_last5 = (
                    1 if np.isfinite(es_ret5) and es_ret5 > 0 else (-1 if np.isfinite(es_ret5) and es_ret5 < 0 else 0)
                )
                if nq_sign != 0 and es_sign != 0 and nq_sign == es_sign:
                    x_agree = nq_sign
                else:
                    x_agree = 0
                if nq_sign != 0 and es_sign != 0 and nq_sign != es_sign:
                    x_disagree_follow_es = es_sign
                    x_disagree_follow_nq = nq_sign
                else:
                    x_disagree_follow_es = 0
                    x_disagree_follow_nq = 0

                rows.append(
                    {
                        "session_date": str(sd),
                        "year": int(ctx["year"]),
                        "dow": int(ctx["dow"]),
                        "split": str(ctx["split"]),
                        "T_offset": off,
                        "T_ny": T,
                        "onr": float(ctx["onr"]),
                        "rng_onr": float(st["rng_onr"]),
                        "dir_sign": int(st["dir_sign"]) if st["dir_sign"] != 0 else 0,
                        "nq_ret": nq_ret,
                        "es_ret": es_ret,
                        "rs": rs,
                        "es_ret5": es_ret5 if np.isfinite(es_ret5) else np.nan,
                        "x_follow_es": x_follow_es,
                        "x_rs_continue": x_rs_continue,
                        "x_rs_fade": x_rs_fade,
                        "x_es_last5": x_es_last5,
                        "x_agree": x_agree,
                        "x_disagree_follow_es": x_disagree_follow_es,
                        "x_disagree_follow_nq": x_disagree_follow_nq,
                        **{f"fwd_{H}": fwd[f"fwd_{H}"] for H in HORIZONS},
                        **{f"mfe_{H}": fwd[f"mfe_{H}"] for H in HORIZONS},
                        **{f"mae_{H}": fwd[f"mae_{H}"] for H in HORIZONS},
                    }
                )
            if n_days % 500 == 0:
                print(f"  days={n_days} rows={len(rows)} skip_es_days~{n_skip_es}", flush=True)

        panel = pd.DataFrame(rows)
        panel.to_parquet(panel_path, index=False)
        print(
            f"Panel rows: {len(panel)}  HIGH+ES days~{panel['session_date'].nunique()}  "
            f"ES-missing days~{n_skip_es} -> {panel_path}",
            flush=True,
        )

    mechanisms = [
        ("follow_es", "x_follow_es"),
        ("rs_continue", "x_rs_continue"),
        ("rs_fade", "x_rs_fade"),
        ("es_last5", "x_es_last5"),
        ("agree_nq_es", "x_agree"),
        ("disagree_follow_es", "x_disagree_follow_es"),
        ("disagree_follow_nq", "x_disagree_follow_nq"),
    ]

    results: list[dict[str, Any]] = []

    def append_baseline(off: int, split: str, base: pd.DataFrame) -> None:
        for H in HORIZONS:
            long_s = base[f"fwd_{H}"].to_numpy(float)
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
                }
            )

    for off in ARM_OFFSETS:
        sub = panel[panel["T_offset"] == off]
        if len(sub) < 50:
            continue
        for split in ("IS", "Validation", "OOS", "ALL"):
            base = sub if split == "ALL" else sub[sub["split"] == split]
            if len(base) < 30:
                continue
            append_baseline(off, split, base)

            for mech, col in mechanisms:
                s = base[base[col] != 0]
                if len(s) < 25:
                    continue
                for H in HORIZONS:
                    signed = (s[f"fwd_{H}"] * s[col]).to_numpy(float)
                    signed = signed[np.isfinite(signed)]
                    if len(signed) < 25:
                        continue
                    win = float(np.mean(signed > 0))
                    mean = float(np.mean(signed))
                    # lookup follow baseline already in results — compute directly
                    follow = base[base["dir_sign"] != 0]
                    fb = (follow[f"fwd_{H}"] * follow["dir_sign"]).to_numpy(float)
                    fb = fb[np.isfinite(fb)]
                    follow_win = float(np.mean(fb > 0)) if len(fb) else np.nan
                    follow_mean = float(np.mean(fb)) if len(fb) else np.nan
                    long_s = base[f"fwd_{H}"].to_numpy(float)
                    long_win = float(np.nanmean(long_s > 0))
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
                            "follow_mean": follow_mean,
                            "long_win": long_win,
                            "delta_win_vs_follow": win - follow_win if np.isfinite(follow_win) else np.nan,
                            "delta_mean_vs_follow": mean - follow_mean if np.isfinite(follow_mean) else np.nan,
                            "delta_win_vs_long": win - long_win if np.isfinite(long_win) else np.nan,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("ny_open_high_xasset_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

    def year_stats(mech: str, col: str, off: int, H: int) -> dict[str, Any]:
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
        yrs = year_stats(mech, col, off, H)
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
            and (is_mean >= 0 or payoff_ok)
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
                    "IS_follow_win": float(r["follow_win"]) if np.isfinite(r["follow_win"]) else None,
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
                }
            )

    candidates.sort(
        key=lambda x: (
            0 if x["tier"] == "strong" else 1,
            -(x["IS_delta_vs_follow"] if np.isfinite(x["IS_delta_vs_follow"]) else -1),
            -x["IS_n"],
        )
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
                    "median_IS_win": float(g["IS_win"].median()),
                    "median_IS_delta": float(g["IS_delta_vs_follow"].median()),
                    "median_OOS_win": float(g["OOS_win"].median()),
                }
            )
        stability.sort(key=lambda x: (-x["n_clocks_strong"], -x["n_clocks"], -x["median_IS_delta"]))

    # HIGH alone snapshot
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
    # Promotable = strong AND multi-clock (>=3)
    multi_strong = [s for s in stability if s["n_clocks_strong"] >= 3]
    multi_any = [s for s in stability if s["n_clocks"] >= 3]
    single_clock_strong = strong_n > 0 and not multi_strong

    if multi_strong:
        verdict = "A_cross_asset_direction_inside_HIGH"
        verdict_text = (
            "ES/cross-asset X creates multi-clock year-stable directional lift inside frozen HIGH."
        )
    elif strong_n > 0 or (soft_n > 0 and multi_any):
        verdict = "B_weak_cross_asset_inside_HIGH"
        verdict_text = (
            "Cross-asset leftovers exist inside HIGH but fail multi-clock stability "
            "and/or are too weak to promote. Family not cleared."
        )
        if single_clock_strong:
            verdict_text += " Apparent strong cells are single-clock — not promotable."
    else:
        verdict = "C_no_cross_asset_direction_inside_HIGH"
        verdict_text = (
            "Inside frozen HIGH, contemporaneous ES / NQ–ES relative signals do not "
            "reliably reprice NQ direction beyond HIGH alone."
        )

    report = {
        "stage": "high_cross_asset_directional",
        "family": "cross_asset_ES",
        "verdict": verdict,
        "verdict_text": verdict_text,
        "frozen_gate": GATE,
        "deferred": ["volume_participation", "multi_scale"],
        "unavailable_this_pass": ["QQQ", "SPY", "VIX", "DXY", "yields"],
        "panel": {"rows": int(len(panel)), "days": int(panel["session_date"].nunique())},
        "n_strong": strong_n,
        "n_soft": soft_n,
        "n_multi_clock_strong_mechs": len(multi_strong),
        "high_alone_baselines": high_alone,
        "top_candidates": candidates[:30],
        "stability": stability[:20],
        "mechanisms_tested": [m for m, _ in mechanisms],
    }
    with open(art("ny_open_high_xasset_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pts(x: Any) -> str:
        return f"{x:+.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md: list[str] = []
    md.append("# NQ HIGH + Cross-Asset (ES) Directional Discovery")
    md.append("")
    md.append(f"**Verdict: `{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    md.append(
        f"Frozen ARM: **`{GATE['primary_arm']}`** — untouched. "
        "Family: **cross-asset (ES only)**. Volume / multi-scale deferred."
    )
    md.append("")
    md.append("Unavailable this pass: QQQ, SPY, VIX, DXY, yields.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Question")
    md.append("")
    md.append(
        "> Inside HIGH, does contemporaneous ES / NQ–ES relative information "
        "change NQ's next directional probabilities vs HIGH alone?"
    )
    md.append("")
    md.append("Each X independent. No combining. No gate retuning.")
    md.append("")
    md.append("## Protocol")
    md.append("")
    md.append("| Rule | Implementation |")
    md.append("|------|----------------|")
    md.append("| Universe | HIGH (`vol_expansion_high`) at T with aligned ES bar |")
    md.append("| Cross-asset | ES 1m continuous, same NY session clock |")
    md.append("| Returns | %-returns from 09:30 open → T (NQ and ES) |")
    md.append("| Outcome | NQ next-bar open → H∈{10,15,30}, signed by X |")
    md.append("| Baseline | HIGH alone LONG + FOLLOW |")
    md.append("| Splits | IS / Val / OOS + 2025 / 2026 |")
    md.append("")
    md.append(
        f"Panel: **{len(panel):,}** rows · **{panel['session_date'].nunique():,}** days."
    )
    md.append("")
    md.append("## HIGH-alone baselines (sanity)")
    md.append("")
    md.append("| Mech | T+ | H | IS win/mean | Val | OOS |")
    md.append("|------|----|---|-------------|-----|-----|")
    for row in high_alone:
        md.append(
            f"| `{row['mechanism']}` | +{row['T_offset']}m | {row['horizon']} | "
            f"{pct(row.get('IS_win'))}/{pts(row.get('IS_mean'))} | "
            f"{pct(row.get('Validation_win'))}/{pts(row.get('Validation_mean'))} | "
            f"{pct(row.get('OOS_win'))}/{pts(row.get('OOS_mean'))} |"
        )
    md.append("")
    md.append("## Mechanisms (independent)")
    md.append("")
    md.append("| ID | Rule |")
    md.append("|----|------|")
    md.append("| `follow_es` | Trade NQ in direction of ES open→T % return |")
    md.append("| `rs_continue` | NQ % − ES % > 0 → long (relative-strength continuation) |")
    md.append("| `rs_fade` | Opposite of `rs_continue` |")
    md.append("| `es_last5` | Trade NQ in direction of ES last-5m return |")
    md.append("| `agree_nq_es` | Only when NQ and ES same sign; that direction |")
    md.append("| `disagree_follow_es` | Only when signs disagree; follow ES |")
    md.append("| `disagree_follow_nq` | Only when signs disagree; follow NQ |")
    md.append("")
    md.append("## Candidates")
    md.append("")
    md.append(
        f"Strong cells: **{strong_n}** · Soft: **{soft_n}** · "
        f"Multi-clock strong mechanisms: **{len(multi_strong)}**"
    )
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
        if single_clock_strong:
            md.append(
                "> **Hostile:** any strong cells with only 1 clock are **not promotable**."
            )
            md.append("")

    md.append("## Clock stability")
    md.append("")
    if not stability:
        md.append("No candidate mechanisms.")
    else:
        md.append("| X | H | clocks | strong clocks | med IS win | med Δ | med OOS |")
        md.append("|---|---|--------|---------------|------------|-------|---------|")
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
    md.append("### Research tree status")
    md.append("")
    md.append("```")
    md.append("FROZEN HIGH GATE")
    md.append("   ├── Cross-asset (ES)  → this stage")
    md.append("   ├── Volume shock      → next (only if needed)")
    md.append("   └── Multi-scale       → next (only if needed)")
    md.append("```")
    md.append("")
    md.append("### Explicit non-actions")
    md.append("")
    md.append("- Do not unfreeze HIGH")
    md.append("- Do not combine cross-asset X with dead NQ price patterns")
    md.append("- Do not start volume/multi-scale until this family is closed")
    md.append("- Do not promote single-clock leftovers")
    md.append("")
    md.append("## Artifacts")
    md.append("")
    md.append("- `artifacts/frozen_opportunity_gate.md`")
    md.append("- `artifacts/ny_open_high_xasset_panel.parquet`")
    md.append("- `artifacts/ny_open_high_xasset_results.csv`")
    md.append("- `artifacts/ny_open_high_xasset_report.json`")
    md.append("- `run_ny_open_high_cross_asset.py`")
    md.append("")

    md_path = art("ny_open_high_xasset_report.md")
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {md_path}", flush=True)
    print(f"VERDICT: {verdict}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n}  multi_strong_mechs: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
