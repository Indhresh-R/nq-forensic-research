"""Step 5 — signed exit position diagnostic (ExpExit only)."""
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


def compute_signed_exit(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    atr = panel["atr_30"].to_numpy(np.float64)

    rows = []
    for ev in events.itertuples(index=False):
        if ev.family != FAMILY_EXP_EXIT:
            continue
        i0 = int(ev.onset_panel_idx)
        te = int(ev.event_panel_idx)
        if te <= i0:
            continue
        sl = slice(i0, te)
        hi = high[sl]
        lo = low[sl]
        if len(hi) == 0:
            continue
        p_high = float(hi.max())
        p_low = float(lo.min())
        r = p_high - p_low
        mid = 0.5 * (p_high + p_low)
        p_event = float(close[te])
        atr_ref = float(atr[te - 1])
        if r <= 0:
            s = np.nan
        else:
            s = (p_event - mid) / r
        s_atr = (p_event - mid) / atr_ref if atr_ref > 0 and np.isfinite(atr_ref) else np.nan
        rows.append(
            {
                "event_id": ev.event_id,
                "origin_cell": ev.origin_cell,
                "family": ev.family,
                "split": ev.split,
                "session_year": int(ev.session_year),
                "wait_to_event": int(ev.wait_to_event),
                "p_event": p_event,
                "p_mid": mid,
                "p_high": p_high,
                "p_low": p_low,
                "origin_range": r,
                "signed_exit_pos": s,
                "signed_exit_pos_atr": s_atr,
                "sign_bin": (
                    "BELOW"
                    if np.isfinite(s) and s < 0
                    else ("ABOVE_OR_AT" if np.isfinite(s) else "NA")
                ),
            }
        )
    return pd.DataFrame(rows)


def freeze_s_cuts(feat: pd.DataFrame) -> dict:
    is_s = feat.loc[
        (feat["split"] == "IS") & np.isfinite(feat["signed_exit_pos"]),
        "signed_exit_pos",
    ].to_numpy(float)
    q33 = float(np.quantile(is_s, 1.0 / 3.0)) if len(is_s) else np.nan
    q67 = float(np.quantile(is_s, 2.0 / 3.0)) if len(is_s) else np.nan
    return {
        "source": "IS ExpExit signed_exit_pos terciles",
        "n_is": int(len(is_s)),
        "q33": q33,
        "q67": q67,
        "S_T1": f"S <= {q33}",
        "S_T2": f"{q33} < S <= {q67}",
        "S_T3": f"S > {q67}",
    }


def assign_s_tercile(s: float, q33: float, q67: float) -> str:
    if not np.isfinite(s) or not np.isfinite(q33) or not np.isfinite(q67):
        return "NA"
    if s <= q33:
        return "S_T1"
    if s <= q67:
        return "S_T2"
    return "S_T3"


def within_bin_contrast(
    metrics: pd.DataFrame, feat: pd.DataFrame, bin_col: str, horizon: int
) -> pd.DataFrame:
    m = metrics.loc[
        (metrics["family"] == FAMILY_EXP_EXIT)
        & (metrics["horizon"] == horizon)
        & (metrics["valid"])
    ]
    df = feat.merge(
        m[
            [
                "event_id",
                "returned_to_origin_range",
                "reached_opposite_range",
            ]
        ],
        on="event_id",
        how="inner",
    )
    rows = []
    for bval, g in df.groupby(bin_col, sort=True):
        gc = g.loc[g["origin_cell"] == CELL_C]
        gd = g.loc[g["origin_cell"] == CELL_D]
        nc, nd = len(gc), len(gd)
        eligible = nc >= MIN_N_VALID and nd >= MIN_N_VALID
        row = {
            "bin_col": bin_col,
            "bin": bval,
            "horizon": horizon,
            "n_c": nc,
            "n_d": nd,
            "eligible": eligible,
            "share_c": nc / len(g) if len(g) else np.nan,
            "share_d": nd / len(g) if len(g) else np.nan,
            "mean_S_c": float(gc["signed_exit_pos"].mean()) if nc else np.nan,
            "mean_S_d": float(gd["signed_exit_pos"].mean()) if nd else np.nan,
        }
        for name, col in (
            ("return", "returned_to_origin_range"),
            ("opposite", "reached_opposite_range"),
        ):
            kc = int(gc[col].sum()) if nc else 0
            kd = int(gd[col].sum()) if nd else 0
            pc = kc / nc if nc else np.nan
            pd_ = kd / nd if nd else np.nan
            diff, lo, hi = newcombe_diff_ci(kc, nc, kd, nd)
            row[f"{name}_rate_c"] = pc
            row[f"{name}_rate_d"] = pd_
            row[f"{name}_diff"] = diff  # D - C
            row[f"{name}_diff_ci_lo"] = lo
            row[f"{name}_diff_ci_hi"] = hi
            row[f"{name}_sign"] = (
                0
                if not np.isfinite(diff) or abs(diff) < 1e-15
                else (1 if diff > 0 else -1)
            )
        rows.append(row)
    return pd.DataFrame(rows)


def composition_table(feat: pd.DataFrame, bin_col: str) -> pd.DataFrame:
    rows = []
    for cell in (CELL_C, CELL_D):
        g = feat.loc[feat["origin_cell"] == cell]
        n = len(g)
        for bval, gb in g.groupby(bin_col, sort=True):
            rows.append(
                {
                    "bin_col": bin_col,
                    "origin_cell": cell,
                    "bin": bval,
                    "n": int(len(gb)),
                    "pct_of_cell": 100.0 * len(gb) / n if n else np.nan,
                    "mean_S": float(gb["signed_exit_pos"].mean()),
                }
            )
    return pd.DataFrame(rows)


def classify_verdict(
    pooled_unmatched: dict, within: pd.DataFrame, horizon: int = PRIMARY_HORIZON
) -> dict:
    """
    Remain / disappear / conditional on eligible tercile bins at primary horizon.
    Reference signs from unmatched pooled ExpExit (Step 4 / Step 3).
    """
    u_ret = pooled_unmatched["return_diff"]
    u_opp = pooled_unmatched["opposite_diff"]
    ref_sign_ret = 1 if u_ret > 0 else (-1 if u_ret < 0 else 0)
    ref_sign_opp = 1 if u_opp > 0 else (-1 if u_opp < 0 else 0)

    elig = within.loc[
        (within["bin_col"] == "s_tercile")
        & (within["horizon"] == horizon)
        & (within["eligible"])
        & (within["bin"] != "NA")
    ]
    detail = []
    for _, r in elig.iterrows():
        detail.append(
            {
                "bin": r["bin"],
                "n_c": int(r["n_c"]),
                "n_d": int(r["n_d"]),
                "return_diff": float(r["return_diff"]),
                "opposite_diff": float(r["opposite_diff"]),
                "return_keeps_sign": int(r["return_sign"]) == ref_sign_ret,
                "opposite_keeps_sign": int(r["opposite_sign"]) == ref_sign_opp,
                "return_ge_half": abs(float(r["return_diff"])) >= 0.5 * abs(u_ret),
                "opposite_ge_half": abs(float(r["opposite_diff"])) >= 0.5 * abs(u_opp),
            }
        )

    if len(detail) == 0:
        return {
            "classification": "INCONCLUSIVE",
            "reason": "no_eligible_bins",
            "detail": detail,
            "reference": pooled_unmatched,
        }

    keep_both = [
        d
        for d in detail
        if d["return_keeps_sign"]
        and d["opposite_keeps_sign"]
        and d["return_ge_half"]
        and d["opposite_ge_half"]
    ]
    lose_both = [
        d
        for d in detail
        if (not d["return_keeps_sign"] or not d["return_ge_half"])
        and (not d["opposite_keeps_sign"] or not d["opposite_ge_half"])
    ]

    if len(keep_both) == len(detail):
        cls = "REMAIN"
    elif len(lose_both) == len(detail):
        cls = "DISAPPEAR"
    else:
        cls = "CONDITIONAL"

    return {
        "classification": cls,
        "n_eligible_bins": len(detail),
        "n_keep_both_endpoints": len(keep_both),
        "n_lose_both_endpoints": len(lose_both),
        "detail": detail,
        "reference_unmatched": pooled_unmatched,
    }


def main() -> None:
    print("Loading panel + ExpExit events…", flush=True)
    panel = build_panel()
    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    metrics = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    events = events.loc[events["family"] == FAMILY_EXP_EXIT].copy()

    print("Computing signed exit position…", flush=True)
    feat = compute_signed_exit(panel, events)
    cuts = freeze_s_cuts(feat)
    (RESULTS / "step5_s_cuts_frozen.json").write_text(
        json.dumps(cuts, indent=2), encoding="utf-8"
    )
    feat["s_tercile"] = [
        assign_s_tercile(float(s), cuts["q33"], cuts["q67"])
        for s in feat["signed_exit_pos"].to_numpy(float)
    ]
    feat.to_parquet(RESULTS / "step5_signed_features.parquet", index=False)
    print(
        f"events={len(feat):,} IS cuts q33={cuts['q33']:.4f} q67={cuts['q67']:.4f}",
        flush=True,
    )

    # composition
    comp = pd.concat(
        [
            composition_table(feat, "s_tercile"),
            composition_table(feat, "sign_bin"),
        ],
        ignore_index=True,
    )
    comp.to_csv(RESULTS / "step5_composition.csv", index=False)

    # within-bin contrasts
    parts = []
    for h in (PRIMARY_HORIZON, SECONDARY_HORIZON):
        parts.append(within_bin_contrast(metrics, feat, "s_tercile", h))
        parts.append(within_bin_contrast(metrics, feat, "sign_bin", h))
    within = pd.concat(parts, ignore_index=True)
    within.to_csv(RESULTS / "step5_within_bin_contrasts.csv", index=False)

    # pooled unmatched reference (ExpExit H=30)
    m30 = metrics.loc[
        (metrics["family"] == FAMILY_EXP_EXIT)
        & (metrics["horizon"] == PRIMARY_HORIZON)
        & (metrics["valid"])
    ]
    gc = m30.loc[m30["origin_cell"] == CELL_C]
    gd = m30.loc[m30["origin_cell"] == CELL_D]
    pooled = {}
    for name, col in (
        ("return", "returned_to_origin_range"),
        ("opposite", "reached_opposite_range"),
    ):
        kc, nc = int(gc[col].sum()), len(gc)
        kd, nd = int(gd[col].sum()), len(gd)
        diff, lo, hi = newcombe_diff_ci(kc, nc, kd, nd)
        pooled[f"{name}_diff"] = diff
        pooled[f"{name}_ci"] = [lo, hi]
        pooled[f"n_c"] = nc
        pooled[f"n_d"] = nd

    verdict = classify_verdict(pooled, within, PRIMARY_HORIZON)
    # also summarize sign_bin eligible rows
    sign_rows = within.loc[
        (within["bin_col"] == "sign_bin")
        & (within["horizon"] == PRIMARY_HORIZON)
        & (within["eligible"])
    ]
    verdict["sign_bin_primary"] = sign_rows[
        ["bin", "n_c", "n_d", "return_diff", "opposite_diff"]
    ].to_dict(orient="records")

    (RESULTS / "step5_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(f"Verdict: {verdict['classification']}", flush=True)


if __name__ == "__main__":
    main()
