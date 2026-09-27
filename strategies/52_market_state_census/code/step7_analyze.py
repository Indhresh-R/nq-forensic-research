"""
Step 7 — Low-transition-ER ExpExit origin-history decomposition.

Primary feature: expansion duration before exit. No trades. No new CEM.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import RESULTS
from step1_constants import CELL_C, CELL_D
from step1_extract_paths import build_panel
from step2_constants import FAMILY_EXP_EXIT
from step3_analyze import newcombe_diff_ci
from step3_constants import MIN_N_VALID, PRIMARY_HORIZON, SECONDARY_HORIZON
from step4_analyze import standardized_mean_diff


def load_low_er_cut() -> float:
    cuts = json.loads((RESULTS / "step6_cuts_frozen.json").read_text(encoding="utf-8"))
    return float(cuts["features"]["te_er_60"]["q33"])


def compute_history(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    atr = panel["atr_30"].to_numpy(np.float64)

    rows = []
    for ev in events.itertuples(index=False):
        i0 = int(ev.onset_panel_idx)
        te = int(ev.event_panel_idx)
        if te <= i0:
            continue
        sl = slice(i0, te)
        hi = high[sl]
        lo = low[sl]
        cl = close[sl]
        atr_ref = float(atr[te - 1])
        atr_ok = np.isfinite(atr_ref) and atr_ref > 0

        duration = int(te - i0)
        if duration != int(ev.wait_to_event):
            continue

        if len(cl) >= 2:
            path = float(np.sum(np.abs(np.diff(cl))))
            net = abs(float(cl[-1] - cl[0]))
            pre_er = net / path if path > 0 else np.nan
        else:
            pre_er = np.nan

        if len(hi):
            excursion = float(hi.max() - lo.min())
            excursion_atr = excursion / atr_ref if atr_ok else np.nan
            c0 = float(close[i0])
            max_ext = float(np.max(np.abs(cl - c0)))
            max_ext_atr = max_ext / atr_ref if atr_ok else np.nan
        else:
            excursion_atr = np.nan
            max_ext_atr = np.nan

        # early vs late displacement share (path-length halves of the pre window)
        late_share = np.nan
        n_pre = len(cl)
        if n_pre >= 4:
            mid = n_pre // 2
            early_net = abs(float(cl[mid] - cl[0]))
            late_net = abs(float(cl[-1] - cl[mid]))
            denom = early_net + late_net
            late_share = late_net / denom if denom > 0 else np.nan

        rows.append(
            {
                "event_id": ev.event_id,
                "origin_cell": ev.origin_cell,
                "family": ev.family,
                "split": ev.split,
                "session_year": int(ev.session_year),
                "duration_bars": duration,
                "te_er_60": float(ev.te_er_60),
                "excursion_atr": excursion_atr,
                "pre_er": pre_er,
                "max_ext_atr": max_ext_atr,
                "late_share": late_share,
            }
        )
    return pd.DataFrame(rows)


def freeze_duration_cuts(pop: pd.DataFrame, low_er_cut: float) -> dict:
    is_m = pop.loc[pop["split"] == "IS", "duration_bars"].to_numpy(float)
    is_m = is_m[np.isfinite(is_m)]
    q33 = float(np.quantile(is_m, 1.0 / 3.0)) if len(is_m) else np.nan
    q67 = float(np.quantile(is_m, 2.0 / 3.0)) if len(is_m) else np.nan
    return {
        "source": "IS low-ER ExpExit duration_bars terciles",
        "low_er_cut_source": "step6_cuts_frozen.json features.te_er_60.q33",
        "low_er_cut": low_er_cut,
        "n_is": int(len(is_m)),
        "q33": q33,
        "q67": q67,
        "DUR_T1": f"duration_bars <= {q33}",
        "DUR_T2": f"{q33} < duration_bars <= {q67}",
        "DUR_T3": f"duration_bars > {q67}",
    }


def assign_duration_bin(v: float, q33: float, q67: float) -> str:
    if not np.isfinite(v) or not np.isfinite(q33) or not np.isfinite(q67):
        return "NA"
    if v <= q33:
        return "DUR_T1"
    if v <= q67:
        return "DUR_T2"
    return "DUR_T3"


def balance_table(pop: pd.DataFrame) -> pd.DataFrame:
    cols = (
        "duration_bars",
        "te_er_60",
        "excursion_atr",
        "pre_er",
        "max_ext_atr",
        "late_share",
    )
    c = pop.loc[pop["origin_cell"] == CELL_C]
    d = pop.loc[pop["origin_cell"] == CELL_D]
    rows = []
    for col in cols:
        xc = c[col].to_numpy(float)
        xd = d[col].to_numpy(float)
        rows.append(
            {
                "feature": col,
                "mean_c": float(np.nanmean(xc)),
                "mean_d": float(np.nanmean(xd)),
                "smd_d_minus_c": standardized_mean_diff(xd, xc),
                "n_c_finite": int(np.isfinite(xc).sum()),
                "n_d_finite": int(np.isfinite(xd).sum()),
            }
        )
    return pd.DataFrame(rows)


def composition_table(pop: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cell in (CELL_C, CELL_D):
        g = pop.loc[pop["origin_cell"] == cell]
        n = len(g)
        for bval, gb in g.groupby("duration_bin", sort=True):
            rows.append(
                {
                    "origin_cell": cell,
                    "bin": bval,
                    "n": int(len(gb)),
                    "pct_of_cell": 100.0 * len(gb) / n if n else np.nan,
                    "mean_duration": float(gb["duration_bars"].mean()),
                    "mean_te_er_60": float(gb["te_er_60"].mean()),
                }
            )
    return pd.DataFrame(rows)


def within_bin_contrasts(pop: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h in (PRIMARY_HORIZON, SECONDARY_HORIZON):
        m = metrics.loc[
            (metrics["family"] == FAMILY_EXP_EXIT)
            & (metrics["horizon"] == h)
            & (metrics["valid"])
        ]
        df = pop.merge(
            m[["event_id", "returned_to_origin_range", "reached_opposite_range"]],
            on="event_id",
            how="inner",
        )
        for bval, g in df.groupby("duration_bin", sort=True):
            gc = g.loc[g["origin_cell"] == CELL_C]
            gd = g.loc[g["origin_cell"] == CELL_D]
            nc, nd = len(gc), len(gd)
            row = {
                "bin": bval,
                "horizon": h,
                "n_c": nc,
                "n_d": nd,
                "eligible": nc >= MIN_N_VALID and nd >= MIN_N_VALID,
                "mean_duration_c": float(gc["duration_bars"].mean()) if nc else np.nan,
                "mean_duration_d": float(gd["duration_bars"].mean()) if nd else np.nan,
            }
            for name, col in (
                ("return", "returned_to_origin_range"),
                ("opposite", "reached_opposite_range"),
            ):
                kc = int(gc[col].sum()) if nc else 0
                kd = int(gd[col].sum()) if nd else 0
                diff, lo, hi = newcombe_diff_ci(kc, nc, kd, nd)
                row[f"{name}_rate_c"] = kc / nc if nc else np.nan
                row[f"{name}_rate_d"] = kd / nd if nd else np.nan
                row[f"{name}_diff"] = diff
                row[f"{name}_diff_ci_lo"] = lo
                row[f"{name}_diff_ci_hi"] = hi
                row[f"{name}_sign"] = (
                    0
                    if not np.isfinite(diff) or abs(diff) < 1e-15
                    else (1 if diff > 0 else -1)
                )
            rows.append(row)
    return pd.DataFrame(rows)


def _is_monotonic(vals: list[float], increasing: bool | None = None) -> bool:
    """True if strictly mono-inc or mono-dec (or constant)."""
    if len(vals) < 2 or any(not np.isfinite(v) for v in vals):
        return False
    diffs = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    if all(abs(d) < 1e-15 for d in diffs):
        return False  # constant is not "progressive"
    if increasing is True:
        return all(d >= -1e-15 for d in diffs) and any(d > 1e-15 for d in diffs)
    if increasing is False:
        return all(d <= 1e-15 for d in diffs) and any(d < -1e-15 for d in diffs)
    return (all(d >= -1e-15 for d in diffs) and any(d > 1e-15 for d in diffs)) or (
        all(d <= 1e-15 for d in diffs) and any(d < -1e-15 for d in diffs)
    )


def classify(within: pd.DataFrame, pooled: dict) -> dict:
    u_ret = pooled["return_diff"]
    u_opp = pooled["opposite_diff"]
    ref_ret = 1 if u_ret > 0 else -1
    ref_opp = 1 if u_opp > 0 else -1

    elig = within.loc[
        (within["horizon"] == PRIMARY_HORIZON)
        & (within["eligible"])
        & (within["bin"] != "NA")
    ].copy()
    # order duration bins
    order = {"DUR_T1": 0, "DUR_T2": 1, "DUR_T3": 2}
    elig["_ord"] = elig["bin"].map(order)
    elig = elig.sort_values("_ord")

    detail = []
    for _, r in elig.iterrows():
        detail.append(
            {
                "bin": r["bin"],
                "n_c": int(r["n_c"]),
                "n_d": int(r["n_d"]),
                "return_diff": float(r["return_diff"]),
                "opposite_diff": float(r["opposite_diff"]),
                "return_keeps": int(r["return_sign"]) == ref_ret
                and abs(float(r["return_diff"])) >= 0.5 * abs(u_ret),
                "opposite_keeps": int(r["opposite_sign"]) == ref_opp
                and abs(float(r["opposite_diff"])) >= 0.5 * abs(u_opp),
            }
        )

    if not detail:
        return {
            "classification": "INCONCLUSIVE",
            "reason": "no_eligible_bins",
            "detail": detail,
            "reference_low_er_pooled": pooled,
        }

    keep = [d for d in detail if d["return_keeps"] and d["opposite_keeps"]]
    lose = [
        d
        for d in detail
        if (not d["return_keeps"]) and (not d["opposite_keeps"])
    ]

    if len(keep) == len(detail):
        primary = "HISTORY_RESIDUAL"
    elif len(lose) == len(detail):
        primary = "HISTORY_ACCOUNTS"
    else:
        primary = "CONCENTRATED"

    ret_diffs = [d["return_diff"] for d in detail]
    opp_diffs = [d["opposite_diff"] for d in detail]
    progressive = (
        primary in {"CONCENTRATED", "HISTORY_RESIDUAL"}
        and len(detail) >= 3
        and _is_monotonic(ret_diffs)
        and _is_monotonic(opp_diffs)
    )
    # For residual, require progressive magnitude change still countable as PROGRESSIVE
    # only when not all-keep identical — if HISTORY_RESIDUAL and monotonic, upgrade.
    if progressive and primary != "HISTORY_ACCOUNTS":
        classification = "PROGRESSIVE"
    else:
        classification = primary

    return {
        "classification": classification,
        "base_class": primary,
        "progressive_upgrade": bool(progressive and primary != "HISTORY_ACCOUNTS"),
        "detail": detail,
        "reference_low_er_pooled": pooled,
    }


def main() -> None:
    print("Loading Step6 components + events + metrics…", flush=True)
    low_er_cut = load_low_er_cut()
    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    metrics = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    comps = pd.read_parquet(RESULTS / "step6_components.parquet")

    events = events.loc[events["family"] == FAMILY_EXP_EXIT].copy()
    comps = comps[["event_id", "te_er_60"]].copy()
    ev = events.merge(comps, on="event_id", how="inner")
    low = ev.loc[np.isfinite(ev["te_er_60"]) & (ev["te_er_60"] <= low_er_cut)].copy()
    print(
        f"Low-ER cut={low_er_cut:.6f}; ExpExit={len(ev):,} low-ER={len(low):,}",
        flush=True,
    )

    print("Computing pre-event history features…", flush=True)
    panel = build_panel()
    pop = compute_history(panel, low)
    cuts = freeze_duration_cuts(pop, low_er_cut)
    pop["duration_bin"] = [
        assign_duration_bin(float(v), cuts["q33"], cuts["q67"])
        for v in pop["duration_bars"].to_numpy(float)
    ]
    pop.to_parquet(RESULTS / "step7_population.parquet", index=False)
    (RESULTS / "step7_cuts_frozen.json").write_text(
        json.dumps(cuts, indent=2), encoding="utf-8"
    )

    bal = balance_table(pop)
    bal.to_csv(RESULTS / "step7_balance.csv", index=False)
    composition_table(pop).to_csv(RESULTS / "step7_composition.csv", index=False)

    within = within_bin_contrasts(pop, metrics)
    within.to_csv(RESULTS / "step7_within_bin_contrasts.csv", index=False)

    # pooled low-ER unmatched reference
    m30 = metrics.loc[
        (metrics["family"] == FAMILY_EXP_EXIT)
        & (metrics["horizon"] == PRIMARY_HORIZON)
        & (metrics["valid"])
    ]
    dfp = pop.merge(
        m30[["event_id", "returned_to_origin_range", "reached_opposite_range"]],
        on="event_id",
        how="inner",
    )
    gc = dfp.loc[dfp["origin_cell"] == CELL_C]
    gd = dfp.loc[dfp["origin_cell"] == CELL_D]
    pooled = {"n_c": len(gc), "n_d": len(gd), "n_total": len(dfp)}
    for name, col in (
        ("return", "returned_to_origin_range"),
        ("opposite", "reached_opposite_range"),
    ):
        diff, lo, hi = newcombe_diff_ci(
            int(gc[col].sum()), len(gc), int(gd[col].sum()), len(gd)
        )
        pooled[f"{name}_diff"] = diff
        pooled[f"{name}_ci"] = [lo, hi]
        pooled[f"{name}_rate_c"] = float(gc[col].mean()) if len(gc) else np.nan
        pooled[f"{name}_rate_d"] = float(gd[col].mean()) if len(gd) else np.nan

    verdict = classify(within, pooled)
    (RESULTS / "step7_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(f"Verdict: {verdict['classification']}", flush=True)
    print(
        f"Low-ER pooled return D-C={100 * pooled['return_diff']:+.1f} pp "
        f"(n_c={pooled['n_c']}, n_d={pooled['n_d']})",
        flush=True,
    )


if __name__ == "__main__":
    main()
