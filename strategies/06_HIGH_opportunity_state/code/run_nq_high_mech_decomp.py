"""
HIGH Mechanism Decomposition — What does vol_expansion_high actually detect?

NO strategy. NO entries. NO direction. NO threshold retuning.

Questions:
  1) Is HIGH predictive of *incremental* post-T opportunity, or mostly labeling
     an already-started move?
  2) Which pre-T mechanism best characterizes HIGH vs matched LOW:
       - volatility clustering (recent TR elevated)
       - range expansion trajectory
       - acceleration (speed rising)
       - compression → expansion transition

Frozen ARM: vol_expansion_high (rng_onr >= IS p66[T]). Never recompute.
Structural opportunity (context): max excursion from next-bar open >= 0.25*ONR within H.
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
OPP_H = (15, 30)
STRUCT_FRAC = 0.25
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


def post_opportunity(
    h: np.ndarray,
    l: np.ndarray,
    o: np.ndarray,
    ny: np.ndarray,
    T: int,
    onr: float,
    horizons: tuple[int, ...],
) -> dict[str, float]:
    after = np.where(ny > T)[0]
    out: dict[str, float] = {}
    if len(after) < max(horizons) or onr <= 0:
        for H in horizons:
            out[f"post_max_onr_{H}"] = np.nan
            out[f"post_resolved_{H}"] = np.nan
            out[f"t_resolve_{H}"] = np.nan
        return out
    entry_i = int(after[0])
    entry = float(o[entry_i])
    thr = STRUCT_FRAC * onr
    for H in horizons:
        end = entry_i + H - 1
        if end >= len(h):
            out[f"post_max_onr_{H}"] = np.nan
            out[f"post_resolved_{H}"] = np.nan
            out[f"t_resolve_{H}"] = np.nan
            continue
        hh = h[entry_i : end + 1]
        ll = l[entry_i : end + 1]
        mfe = float(hh.max() - entry)
        mae = float(entry - ll.min())
        mx = max(mfe, mae)
        out[f"post_max_onr_{H}"] = mx / onr
        out[f"post_resolved_{H}"] = 1.0 if mx >= thr else 0.0
        t_hit = np.nan
        run = 0.0
        for i in range(H):
            run = max(run, hh[i] - entry, entry - ll[i])
            if run >= thr:
                t_hit = float(i + 1)
                break
        out[f"t_resolve_{H}"] = t_hit
    return out


def pre_window_stats(
    h: np.ndarray,
    l: np.ndarray,
    o: np.ndarray,
    c: np.ndarray,
    j: int,
    onr: float,
    o930: float,
    open_i: int,
) -> dict[str, float]:
    """Causal pre-T diagnostics using bars [open_i, j]."""
    if j <= open_i or onr <= 0:
        return {k: np.nan for k in (
            "pre_rng_onr", "pre_move_onr", "pre_exc_onr",
            "tr5", "tr15", "tr_early", "vol_cluster",
            "speed_now", "speed_lag5", "accel",
            "rng_early", "rng_late", "expand_ratio",
            "compress_then_expand", "already_frac_proxy",
        )}

    seg_h = h[open_i : j + 1]
    seg_l = l[open_i : j + 1]
    seg_c = c[open_i : j + 1]
    pre_rng = float(seg_h.max() - seg_l.min())
    pre_move = float(c[j] - o930)
    pre_exc = max(abs(float(seg_h.max() - o930)), abs(float(o930 - seg_l.min())))

    prev_c = np.concatenate([[o[open_i]], c[open_i:j]])
    # align tr length to bars open_i..j
    hh = h[open_i : j + 1]
    ll = l[open_i : j + 1]
    cc = c[open_i : j + 1]
    oo = o[open_i : j + 1]
    pc = np.concatenate([[oo[0]], cc[:-1]])
    tr = np.maximum(hh - ll, np.maximum(np.abs(hh - pc), np.abs(ll - pc)))

    n = len(tr)
    tr5 = float(np.mean(tr[-5:])) if n >= 1 else np.nan
    tr15 = float(np.mean(tr[-15:])) if n >= 1 else np.nan
    early_n = max(min(10, n // 3), 1)
    tr_early = float(np.mean(tr[:early_n]))
    vol_cluster = tr5 / tr_early if tr_early > 1e-9 else np.nan

    elapsed = max(j - open_i, 1)
    speed_now = abs(pre_move) / onr / elapsed
    # speed as of 5 bars earlier
    if j - 5 > open_i:
        move_lag = float(c[j - 5] - o930)
        elapsed_lag = max(j - 5 - open_i, 1)
        speed_lag5 = abs(move_lag) / onr / elapsed_lag
    else:
        speed_lag5 = np.nan
    accel = speed_now - speed_lag5 if np.isfinite(speed_lag5) else np.nan

    # early vs late range (first third vs full)
    cut = open_i + max(early_n - 1, 0)
    rng_early = float(h[open_i : cut + 1].max() - l[open_i : cut + 1].min()) / onr
    rng_late = pre_rng / onr
    expand_ratio = rng_late / rng_early if rng_early > 1e-9 else np.nan
    # compression then expand: early range small relative to ONR, late large
    compress_then_expand = 1.0 if (rng_early <= 0.35 and rng_late >= 0.66) else 0.0

    return {
        "pre_rng_onr": pre_rng / onr,
        "pre_move_onr": pre_move / onr,
        "pre_exc_onr": pre_exc / onr,
        "tr5": tr5,
        "tr15": tr15,
        "tr_early": tr_early,
        "vol_cluster": vol_cluster,
        "speed_now": speed_now,
        "speed_lag5": speed_lag5,
        "accel": accel,
        "rng_early": rng_early,
        "rng_late": rng_late,
        "expand_ratio": expand_ratio,
        "compress_then_expand": compress_then_expand,
    }


def main() -> None:
    print("=== HIGH Mechanism Decomposition (no strategy) ===", flush=True)
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
        o930 = float(ctx["open_930"])

        o = rth["open"].to_numpy(float)
        h = rth["high"].to_numpy(float)
        l = rth["low"].to_numpy(float)
        c = rth["close"].to_numpy(float)
        ny = rth["ny_min"].to_numpy(int)
        idx = {int(m): i for i, m in enumerate(ny)}
        open_i = idx.get(NY_OPEN, 0)

        for off in ARM_OFFSETS:
            T = NY_OPEN + off
            if T not in idx:
                continue
            j = idx[T]
            st = state_at_T(rth[rth["ny_min"] <= T], ctx, T)
            if st is None:
                continue
            rng_onr = float(st["rng_onr"])
            if is_high(rng_onr, off):
                regime = "HIGH"
            elif is_low(rng_onr, off):
                regime = "LOW"
            else:
                regime = "MID"

            pre = pre_window_stats(h, l, o, c, j, onr, o930, open_i)
            post = post_opportunity(h, l, o, ny, T, onr, OPP_H)

            # Total excursion open→T+H (eventual path size from open)
            row: dict[str, Any] = {
                "session_date": str(sd),
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": regime,
                "rng_onr": rng_onr,
                "abs_move_onr": float(st["abs_move_onr"]),
                "speed": float(st["speed"]),
                "vol_unit_onr": float(st["vol_unit_onr"]),
                "onr": onr,
                **pre,
                **post,
            }

            for H in OPP_H:
                # eventual max excursion from open through T+H
                after = np.where(ny > T)[0]
                if len(after) < H:
                    row[f"total_exc_onr_{H}"] = np.nan
                    row[f"share_pre_{H}"] = np.nan
                    row[f"share_post_{H}"] = np.nan
                    row[f"incremental_onr_{H}"] = np.nan
                    continue
                end_i = int(after[0]) + H - 1
                if end_i >= len(h):
                    row[f"total_exc_onr_{H}"] = np.nan
                    row[f"share_pre_{H}"] = np.nan
                    row[f"share_post_{H}"] = np.nan
                    row[f"incremental_onr_{H}"] = np.nan
                    continue
                tot_hi = float(h[open_i : end_i + 1].max())
                tot_lo = float(l[open_i : end_i + 1].min())
                total_exc = max(abs(tot_hi - o930), abs(o930 - tot_lo))
                pre_exc = float(pre["pre_exc_onr"]) * onr
                # incremental from T close over next H (not from entry — raw remaining range growth)
                post_from_ref = float(post[f"post_max_onr_{H}"]) * onr
                row[f"total_exc_onr_{H}"] = total_exc / onr
                row[f"incremental_onr_{H}"] = post_from_ref / onr
                # share of total open-based excursion already present by T
                if total_exc > 1e-9:
                    row[f"share_pre_{H}"] = min(pre_exc / total_exc, 1.0)
                    row[f"share_post_growth_{H}"] = max(0.0, (total_exc - pre_exc) / total_exc)
                else:
                    row[f"share_pre_{H}"] = np.nan
                    row[f"share_post_growth_{H}"] = np.nan

                # Classifier proxies (frozen cuts, descriptive not optimized)
                # already_moving: >=60% of eventual open-excursion done by T
                # early: <40% done by T AND post resolves
                sp = row[f"share_pre_{H}"]
                resolved = row[f"post_resolved_{H}"]
                if np.isfinite(sp):
                    row[f"class_{H}"] = (
                        "already_moving"
                        if sp >= 0.60
                        else ("early_transition" if sp <= 0.40 else "mixed")
                    )
                else:
                    row[f"class_{H}"] = "unknown"
                row[f"early_and_resolves_{H}"] = (
                    1.0
                    if np.isfinite(sp) and sp <= 0.40 and resolved == 1.0
                    else 0.0
                )

            rows.append(row)

        if n_days % 500 == 0:
            print(f"  days={n_days} rows={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_high_mech_panel.parquet"), index=False)
    print(f"Panel rows={len(panel)} days~{panel['session_date'].nunique()}", flush=True)

    # ——— Analysis ———
    def med(s: pd.Series) -> float:
        s = s.dropna()
        return float(s.median()) if len(s) else np.nan

    def mean(s: pd.Series) -> float:
        s = s.dropna()
        return float(s.mean()) if len(s) else np.nan

    reports: dict[str, Any] = {
        "stage": "high_mechanism_decomposition",
        "frozen_arm": "vol_expansion_high",
        "struct_frac": STRUCT_FRAC,
        "horizons": list(OPP_H),
        "n_rows": int(len(panel)),
    }

    # 1) HIGH vs LOW pre-T profiles (IS)
    is_p = panel[panel["split"] == "IS"]
    profile_rows = []
    feats = [
        "pre_rng_onr",
        "pre_exc_onr",
        "abs_move_onr",
        "vol_cluster",
        "accel",
        "expand_ratio",
        "compress_then_expand",
        "speed",
        "tr5",
        "rng_early",
    ]
    for off in (15, 30, 60):
        for reg in ("HIGH", "LOW", "MID"):
            s = is_p[(is_p["T_offset"] == off) & (is_p["regime"] == reg)]
            if len(s) < 50:
                continue
            rec = {"T_offset": off, "regime": reg, "n": int(len(s))}
            for f in feats:
                rec[f"med_{f}"] = med(s[f])
            for H in OPP_H:
                rec[f"p_resolve_{H}"] = mean(s[f"post_resolved_{H}"])
                rec[f"med_share_pre_{H}"] = med(s[f"share_pre_{H}"])
                rec[f"med_post_max_{H}"] = med(s[f"post_max_onr_{H}"])
                rec[f"p_already_{H}"] = mean((s[f"class_{H}"] == "already_moving").astype(float))
                rec[f"p_early_{H}"] = mean((s[f"class_{H}"] == "early_transition").astype(float))
                rec[f"p_early_resolves_{H}"] = mean(s[f"early_and_resolves_{H}"])
            profile_rows.append(rec)
    profiles = pd.DataFrame(profile_rows)
    profiles.to_csv(art("nq_high_mech_profiles.csv"), index=False)
    reports["profiles_IS"] = profile_rows

    # 2) Within HIGH: does post-resolve depend on how much already moved?
    within = []
    for H in OPP_H:
        for split in ("IS", "Validation", "OOS"):
            s = panel[(panel["split"] == split) & (panel["regime"] == "HIGH")].copy()
            s = s[np.isfinite(s["pre_exc_onr"]) & np.isfinite(s[f"post_resolved_{H}"])]
            if len(s) < 100:
                continue
            # terciles of pre_exc within HIGH (IS cuts frozen from IS only)
            if split == "IS":
                q33, q66 = s["pre_exc_onr"].quantile([0.33, 0.66])
            else:
                is_h = panel[(panel["split"] == "IS") & (panel["regime"] == "HIGH")]
                q33, q66 = is_h["pre_exc_onr"].quantile([0.33, 0.66])
            s["pre_bucket"] = np.where(
                s["pre_exc_onr"] <= q33, "low_pre", np.where(s["pre_exc_onr"] >= q66, "high_pre", "mid_pre")
            )
            for b, g in s.groupby("pre_bucket"):
                within.append(
                    {
                        "split": split,
                        "horizon": H,
                        "pre_bucket": b,
                        "n": int(len(g)),
                        "med_pre_exc": med(g["pre_exc_onr"]),
                        "p_resolve": mean(g[f"post_resolved_{H}"]),
                        "med_post_max": med(g[f"post_max_onr_{H}"]),
                        "med_share_pre": med(g[f"share_pre_{H}"]),
                    }
                )
    within_df = pd.DataFrame(within)
    within_df.to_csv(art("nq_high_mech_within_high.csv"), index=False)
    reports["within_HIGH_by_pre_excursion"] = within

    # 3) Mechanism prevalence: HIGH vs LOW gaps on diagnostics (IS, pool clocks)
    mech_gap = []
    sH = is_p[is_p["regime"] == "HIGH"]
    sL = is_p[is_p["regime"] == "LOW"]
    for f, label in [
        ("vol_cluster", "volatility_clustering"),
        ("expand_ratio", "range_expansion_ratio"),
        ("accel", "acceleration"),
        ("compress_then_expand", "compression_to_expansion"),
        ("pre_exc_onr", "already_excursed_by_T"),
        ("abs_move_onr", "directional_move_by_T"),
    ]:
        mech_gap.append(
            {
                "mechanism": label,
                "feature": f,
                "HIGH_med": med(sH[f]),
                "LOW_med": med(sL[f]),
                "gap_med": med(sH[f]) - med(sL[f]),
                "HIGH_mean": mean(sH[f]),
                "LOW_mean": mean(sL[f]),
            }
        )
    reports["mechanism_gaps_IS"] = mech_gap

    # 4) Share-pre distribution for HIGH that resolve vs not
    share_rows = []
    for H in OPP_H:
        for split in ("IS", "Validation", "OOS"):
            s = panel[(panel["split"] == split) & (panel["regime"] == "HIGH")]
            for res_flag, name in ((1.0, "resolves"), (0.0, "no_resolve")):
                g = s[s[f"post_resolved_{H}"] == res_flag]
                share_rows.append(
                    {
                        "split": split,
                        "horizon": H,
                        "outcome": name,
                        "n": int(len(g)),
                        "med_share_pre": med(g[f"share_pre_{H}"]),
                        "med_pre_exc": med(g["pre_exc_onr"]),
                        "med_post_max": med(g[f"post_max_onr_{H}"]),
                        "p_already": mean((g[f"class_{H}"] == "already_moving").astype(float)),
                        "p_early": mean((g[f"class_{H}"] == "early_transition").astype(float)),
                    }
                )
    reports["share_pre_by_resolve"] = share_rows

    # 5) Classification summary + stability
    class_sum = []
    for H in OPP_H:
        for split in ("IS", "Validation", "OOS"):
            s = panel[(panel["split"] == split) & (panel["regime"] == "HIGH")]
            n = len(s)
            class_sum.append(
                {
                    "split": split,
                    "horizon": H,
                    "n_HIGH": n,
                    "p_already_moving": mean((s[f"class_{H}"] == "already_moving").astype(float)),
                    "p_early_transition": mean((s[f"class_{H}"] == "early_transition").astype(float)),
                    "p_mixed": mean((s[f"class_{H}"] == "mixed").astype(float)),
                    "med_share_pre": med(s[f"share_pre_{H}"]),
                    "p_resolve": mean(s[f"post_resolved_{H}"]),
                    "p_early_and_resolves": mean(s[f"early_and_resolves_{H}"]),
                    # Among early: resolve rate
                    "early_resolve_rate": mean(
                        s.loc[s[f"class_{H}"] == "early_transition", f"post_resolved_{H}"]
                    ),
                    "already_resolve_rate": mean(
                        s.loc[s[f"class_{H}"] == "already_moving", f"post_resolved_{H}"]
                    ),
                }
            )
    reports["classification"] = class_sum

    # 6) Year check 2025/2026 on share_pre and class mix
    year_rows = []
    for y in (2025, 2026):
        for H in OPP_H:
            s = panel[(panel["year"] == y) & (panel["regime"] == "HIGH")]
            year_rows.append(
                {
                    "year": y,
                    "horizon": H,
                    "n": int(len(s)),
                    "med_share_pre": med(s[f"share_pre_{H}"]),
                    "p_already": mean((s[f"class_{H}"] == "already_moving").astype(float)),
                    "p_early": mean((s[f"class_{H}"] == "early_transition").astype(float)),
                    "p_resolve": mean(s[f"post_resolved_{H}"]),
                }
            )
    reports["year_stability"] = year_rows

    # Verdict logic (descriptive classification of HIGH's nature)
    # Use IS H30 as primary
    is_h30 = next(c for c in class_sum if c["split"] == "IS" and c["horizon"] == 30)
    val_h30 = next(c for c in class_sum if c["split"] == "Validation" and c["horizon"] == 30)
    oos_h30 = next(c for c in class_sum if c["split"] == "OOS" and c["horizon"] == 30)

    # Within-HIGH: low_pre vs high_pre resolve gap on IS H30
    wh_is = [
        w
        for w in within
        if w["split"] == "IS" and w["horizon"] == 30
    ]
    p_low = next((w["p_resolve"] for w in wh_is if w["pre_bucket"] == "low_pre"), np.nan)
    p_high = next((w["p_resolve"] for w in wh_is if w["pre_bucket"] == "high_pre"), np.nan)
    pre_gradient = (
        p_high - p_low if np.isfinite(p_high) and np.isfinite(p_low) else np.nan
    )

    already_dom = is_h30["p_already_moving"] >= 0.55 and is_h30["med_share_pre"] >= 0.70
    early_meaningful = is_h30["p_early_transition"] >= 0.25 and is_h30["early_resolve_rate"] >= 0.55
    # share_pre dominates the nature call; resolve gradient is secondary evidence
    if already_dom:
        nature = "persistence_already_moving"
        nature_text = (
            "HIGH primarily labels an already-active / already-excursed state "
            "(activity/range persistence). Median share of eventual open-based excursion "
            "already present at T is very high; the early state-transition subset is rare. "
            "HIGH is not mainly an early compression-to-expansion detector."
        )
    elif early_meaningful and is_h30["p_already_moving"] < 0.45:
        nature = "early_state_transition"
        nature_text = (
            "HIGH often fires with a minority of eventual excursion already done, "
            "and those early cases still show elevated post-T resolution — "
            "consistent with a state-transition / early opportunity detector."
        )
    else:
        nature = "mixed_persistence_and_transition"
        nature_text = (
            "HIGH is a mixture: substantial already-moving mass plus a non-trivial "
            "early-transition subset. Not a pure early detector; treat as activity-state "
            "recognition with partial incremental opportunity remaining."
        )

    # Stability of nature across Val/OOS
    stable = (
        abs(is_h30["p_already_moving"] - val_h30["p_already_moving"]) <= 0.12
        and abs(is_h30["p_already_moving"] - oos_h30["p_already_moving"]) <= 0.12
    )

    reports["nature"] = nature
    reports["nature_text"] = nature_text
    reports["nature_stable_across_splits"] = stable
    reports["IS_H30"] = is_h30
    reports["pre_excursion_resolve_gradient_IS_H30"] = pre_gradient
    reports["mechanism_ranking_note"] = (
        "Rank mechanisms by |HIGH−LOW| median gap on IS; "
        "interpret share_pre for predictive vs contemporaneous."
    )

    with open(art("nq_high_mech_report.json"), "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def num(x: Any) -> str:
        return f"{x:.3f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# HIGH Mechanism Decomposition — What Does HIGH Detect?")
    md.append("")
    md.append(f"**Nature: `{nature}`**")
    md.append("")
    md.append(nature_text)
    md.append("")
    md.append(
        f"Split-stability of already-moving share: **{'yes' if stable else 'no'}**. "
        "No strategy. Frozen `vol_expansion_high` only."
    )
    md.append("")
    md.append("## 1. Predictive vs contemporaneous (share of eventual excursion already in by T)")
    md.append("")
    md.append(
        "For each HIGH at T: `share_pre = (open→T max excursion) / (open→T+H max excursion)`. "
        "`already_moving` if share_pre≥60%; `early_transition` if ≤40%."
    )
    md.append("")
    md.append("| Split | H | n | med share_pre | % already | % early | P(resolve) | early→resolve | already→resolve |")
    md.append("|-------|---|---|---------------|-----------|---------|------------|---------------|-----------------|")
    for c in class_sum:
        md.append(
            f"| {c['split']} | {c['horizon']} | {c['n_HIGH']} | {pct(c['med_share_pre'])} | "
            f"{pct(c['p_already_moving'])} | {pct(c['p_early_transition'])} | "
            f"{pct(c['p_resolve'])} | {pct(c['early_resolve_rate'])} | "
            f"{pct(c['already_resolve_rate'])} |"
        )
    md.append("")
    md.append("## 2. Within HIGH: does more pre-excursion mean more post opportunity?")
    md.append("")
    md.append(
        f"IS H30 resolve gradient (high_pre − low_pre pre-excursion tercile): "
        f"**{pct(pre_gradient)}**"
    )
    md.append("")
    md.append("| Split | H | bucket | n | med pre_exc | P(resolve) | med post_max | med share_pre |")
    md.append("|-------|---|--------|---|-------------|------------|--------------|---------------|")
    for w in within:
        if w["horizon"] != 30:
            continue
        md.append(
            f"| {w['split']} | {w['horizon']} | `{w['pre_bucket']}` | {w['n']} | "
            f"{num(w['med_pre_exc'])} | {pct(w['p_resolve'])} | {num(w['med_post_max'])} | "
            f"{pct(w['med_share_pre'])} |"
        )
    md.append("")
    md.append("## 3. HIGH vs LOW pre-T mechanism gaps (IS medians)")
    md.append("")
    md.append("| Mechanism | Feature | HIGH med | LOW med | Gap |")
    md.append("|-----------|---------|----------|---------|-----|")
    for m in sorted(mech_gap, key=lambda x: -abs(x["gap_med"] if np.isfinite(x["gap_med"]) else 0)):
        md.append(
            f"| {m['mechanism']} | `{m['feature']}` | {num(m['HIGH_med'])} | "
            f"{num(m['LOW_med'])} | {num(m['gap_med'])} |"
        )
    md.append("")
    md.append("## 4. Profile snapshot @ T+30 (IS)")
    md.append("")
    snap = profiles[profiles["T_offset"] == 30]
    if len(snap):
        md.append("| Regime | n | med pre_exc | vol_cluster | expand_ratio | accel | %compress→exp | P(res H30) | med share_pre |")
        md.append("|--------|---|-------------|-------------|--------------|-------|---------------|------------|---------------|")
        for _, r in snap.iterrows():
            md.append(
                f"| `{r['regime']}` | {int(r['n'])} | {num(r['med_pre_exc_onr'])} | "
                f"{num(r['med_vol_cluster'])} | {num(r['med_expand_ratio'])} | "
                f"{num(r['med_accel'])} | {pct(r['med_compress_then_expand'])} | "
                f"{pct(r['p_resolve_30'])} | {pct(r['med_share_pre_30'])} |"
            )
    md.append("")
    md.append("## 5. Year check")
    md.append("")
    md.append("| Year | H | n | med share_pre | % already | % early | P(resolve) |")
    md.append("|------|---|---|---------------|-----------|---------|------------|")
    for y in year_rows:
        md.append(
            f"| {y['year']} | {y['horizon']} | {y['n']} | {pct(y['med_share_pre'])} | "
            f"{pct(y['p_already'])} | {pct(y['p_early'])} | {pct(y['p_resolve'])} |"
        )
    md.append("")
    md.append("## Interpretation")
    md.append("")
    md.append("```text")
    md.append("                 HIGH")
    md.append("                  │")
    md.append("      ┌───────────┴───────────┐")
    md.append("      │                       │")
    md.append(" Already-moving state    State-transition")
    md.append(" (persistence)           (early detector)")
    md.append("```")
    md.append("")
    if nature == "persistence_already_moving":
        md.append(
            "**This decomposition favors the left branch:** HIGH is largely recognizing "
            "that the morning is already in a high-activity / expanded-range state. "
            "Incremental post-T opportunity exists, but a large share of the day's "
            "open-based excursion is typically already present at activation."
        )
        md.append("")
        md.append(
            "Implication for trading ideas: do **not** treat HIGH as an early 'compression→go' "
            "signal without further proof. Any reactive scheme must assume detection is often late."
        )
    elif nature == "early_state_transition":
        md.append(
            "**This decomposition favors the right branch:** HIGH often fires early enough "
            "that most of the eventual excursion is still ahead — worth studying "
            "compression→transition pathways carefully (still no strategy yet)."
        )
    else:
        md.append(
            "**Mixed:** HIGH is not a clean early detector. Separate the early-transition "
            "subset from the already-moving majority before any trade design — "
            "and do not blur them with new filters yet."
        )
    md.append("")
    md.append("## Forbidden next steps")
    md.append("")
    md.append("- Do not invent another directional family")
    md.append("- Do not retune HIGH terciles")
    md.append("- Do not build entries until the nature conclusion is accepted")
    md.append("")
    (art("nq_high_mech_report.md")).write_text("\n".join(md), encoding="utf-8")

    print(f"NATURE: {nature} stable={stable}", flush=True)
    print(
        f"IS H30: already={is_h30['p_already_moving']:.1%} early={is_h30['p_early_transition']:.1%} "
        f"share_pre_med={is_h30['med_share_pre']:.1%} pre_grad={pre_gradient}",
        flush=True,
    )


if __name__ == "__main__":
    main()
