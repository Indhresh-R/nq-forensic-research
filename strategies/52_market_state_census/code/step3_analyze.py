"""
Step 3 — destination asymmetry stability, wait stratification, orthogonal conditioning.

No trades. Covariates and wait cuts frozen before destination claims.
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
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D
from step1_extract_paths import build_panel
from step2_constants import FAMILY_COMP_EXIT, FAMILY_EXP_EXIT
from step3_constants import (
    MIN_N_VALID,
    PRIMARY_HORIZON,
    SECONDARY_HORIZON,
    STEP3_TOD_BLOCKS,
    WAIT_LONG,
    WAIT_MED,
    WAIT_SHORT,
    WAIT_STRATA,
)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Return (p_hat, lo, hi) Wilson score interval."""
    if n <= 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return float(p), float(max(0.0, center - half)), float(min(1.0, center + half))


def newcombe_diff_ci(
    k1: int, n1: int, k2: int, n2: int, z: float = 1.96
) -> tuple[float, float, float]:
    """
    Difference p2 - p1 with Newcombe–Wilson unpaired CI.
    Returns (diff, lo, hi).
    """
    p1, l1, u1 = wilson_ci(k1, n1, z)
    p2, l2, u2 = wilson_ci(k2, n2, z)
    if not np.isfinite(p1) or not np.isfinite(p2):
        return (np.nan, np.nan, np.nan)
    diff = p2 - p1
    # Newcombe (1998) method 10-style
    lo = diff - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = diff + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return float(diff), float(lo), float(hi)


def freeze_wait_cuts(events: pd.DataFrame) -> dict:
    """IS-only wait terciles by family — frozen before destination stratification."""
    out: dict = {"source": "IS wait_to_event terciles by family", "families": {}}
    is_ev = events.loc[events["split"] == "IS"]
    for fam in (FAMILY_COMP_EXIT, FAMILY_EXP_EXIT):
        w = is_ev.loc[is_ev["family"] == fam, "wait_to_event"].to_numpy(float)
        w = w[np.isfinite(w)]
        if len(w) == 0:
            q33 = q67 = np.nan
        else:
            q33 = float(np.quantile(w, 1.0 / 3.0))
            q67 = float(np.quantile(w, 2.0 / 3.0))
        out["families"][fam] = {
            "n_is": int(len(w)),
            "q33": q33,
            "q67": q67,
            "SHORT": f"wait <= {q33}",
            "MEDIUM": f"{q33} < wait <= {q67}",
            "LONG": f"wait > {q67}",
        }
    return out


def assign_wait_stratum(wait: float, q33: float, q67: float) -> str:
    if not np.isfinite(wait) or not np.isfinite(q33) or not np.isfinite(q67):
        return "NA"
    if wait <= q33:
        return WAIT_SHORT
    if wait <= q67:
        return WAIT_MED
    return WAIT_LONG


def assign_tod_block(ny_min: int) -> str:
    for name, (lo, hi) in STEP3_TOD_BLOCKS.items():
        if lo <= ny_min < hi:
            return name
    return "OTHER"


def attach_event_covariates(events: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    idx = events["event_panel_idx"].to_numpy(np.int64)
    out = events.copy()
    out["volatility_state"] = panel["volatility_state"].to_numpy(dtype=object)[idx]
    out["volume_state"] = panel["volume_state"].to_numpy(dtype=object)[idx]
    out["event_ny_min"] = panel["ny_min"].to_numpy(np.int16)[idx]
    out["tod_block"] = [assign_tod_block(int(m)) for m in out["event_ny_min"]]
    return out


def _rate_block(flags: np.ndarray) -> dict:
    flags = flags[np.isfinite(flags.astype(float))]
    n = int(len(flags))
    k = int(np.sum(flags.astype(bool))) if n else 0
    p, lo, hi = wilson_ci(k, n)
    return {"n": n, "k": k, "rate": p, "ci_lo": lo, "ci_hi": hi}


def contrast_destination(
    metrics: pd.DataFrame,
    cell_a: str,
    cell_b: str,
    horizon: int,
    label: str,
) -> dict:
    """cell_b minus cell_a on destination endpoints."""
    def _sub(cell: str) -> pd.DataFrame:
        return metrics[
            (metrics["origin_cell"] == cell)
            & (metrics["horizon"] == horizon)
            & (metrics["valid"])
        ]

    a = _sub(cell_a)
    b = _sub(cell_b)
    out: dict = {
        "contrast": label,
        "horizon": horizon,
        "cell_a": cell_a,
        "cell_b": cell_b,
        "n_a": int(len(a)),
        "n_b": int(len(b)),
        "eligible": bool(len(a) >= MIN_N_VALID and len(b) >= MIN_N_VALID),
    }
    for endpoint, col in (
        ("return_to_origin", "returned_to_origin_range"),
        ("reach_opposite", "reached_opposite_range"),
    ):
        fa = a[col].to_numpy(dtype=bool) if len(a) else np.array([], dtype=bool)
        fb = b[col].to_numpy(dtype=bool) if len(b) else np.array([], dtype=bool)
        ra = _rate_block(fa.astype(float))
        rb = _rate_block(fb.astype(float))
        diff, dlo, dhi = newcombe_diff_ci(ra["k"], ra["n"], rb["k"], rb["n"])
        out[endpoint] = {
            "a": ra,
            "b": rb,
            "diff_b_minus_a": diff,
            "diff_ci_lo": dlo,
            "diff_ci_hi": dhi,
            "sign": (
                0
                if not np.isfinite(diff) or abs(diff) < 1e-15
                else (1 if diff > 0 else -1)
            ),
        }
    return out


def flatten_contrast(row_meta: dict, c: dict) -> dict:
    flat = {**row_meta}
    flat.update(
        {
            "contrast": c["contrast"],
            "horizon": c["horizon"],
            "n_a": c["n_a"],
            "n_b": c["n_b"],
            "eligible": c["eligible"],
            "return_rate_a": c["return_to_origin"]["a"]["rate"],
            "return_rate_b": c["return_to_origin"]["b"]["rate"],
            "return_diff": c["return_to_origin"]["diff_b_minus_a"],
            "return_diff_ci_lo": c["return_to_origin"]["diff_ci_lo"],
            "return_diff_ci_hi": c["return_to_origin"]["diff_ci_hi"],
            "return_sign": c["return_to_origin"]["sign"],
            "opposite_rate_a": c["reach_opposite"]["a"]["rate"],
            "opposite_rate_b": c["reach_opposite"]["b"]["rate"],
            "opposite_diff": c["reach_opposite"]["diff_b_minus_a"],
            "opposite_diff_ci_lo": c["reach_opposite"]["diff_ci_lo"],
            "opposite_diff_ci_hi": c["reach_opposite"]["diff_ci_hi"],
            "opposite_sign": c["reach_opposite"]["sign"],
        }
    )
    return flat


def evaluate_criteria(split_df: pd.DataFrame, wait_df: pd.DataFrame) -> dict:
    """Apply predeclared interestingness criteria on primary horizon."""
    verdict: dict = {"primary_horizon": PRIMARY_HORIZON, "contrasts": {}}

    for family, cell_a, cell_b, tag in (
        (FAMILY_COMP_EXIT, CELL_A, CELL_B, "CompExit_A_vs_B"),
        (FAMILY_EXP_EXIT, CELL_C, CELL_D, "ExpExit_C_vs_D"),
    ):
        pooled = split_df[
            (split_df["slice"] == "POOLED")
            & (split_df["contrast_tag"] == tag)
            & (split_df["horizon"] == PRIMARY_HORIZON)
        ]
        splits = split_df[
            (split_df["slice"].isin(["IS", "Validation", "OOS"]))
            & (split_df["contrast_tag"] == tag)
            & (split_df["horizon"] == PRIMARY_HORIZON)
        ]
        waits = wait_df[
            (wait_df["contrast_tag"] == tag) & (wait_df["horizon"] == PRIMARY_HORIZON)
        ]

        def _endpoint_eval(prefix: str) -> dict:
            if pooled.empty:
                return {"pass": False, "reason": "missing_pooled"}
            prow = pooled.iloc[0]
            pooled_diff = float(prow[f"{prefix}_diff"])
            pooled_sign = int(prow[f"{prefix}_sign"])
            present = bool(prow["eligible"] and abs(pooled_diff) >= 0.02)

            eligible_splits = splits.loc[splits["eligible"]]
            if len(eligible_splits) == 0:
                same_sign = False
                split_detail = "no_eligible_splits"
            else:
                signs = eligible_splits[f"{prefix}_sign"].to_numpy(int)
                # ignore exact zeros for persistence
                nonzero = signs[signs != 0]
                same_sign = (
                    len(nonzero) >= 2 and bool(np.all(nonzero == pooled_sign))
                    if pooled_sign != 0
                    else False
                )
                # require all three splits eligible and same sign when possible
                if len(eligible_splits) >= 3 and pooled_sign != 0:
                    same_sign = bool(np.all(signs == pooled_sign))
                split_detail = {
                    r["slice"]: {
                        "diff": float(r[f"{prefix}_diff"]),
                        "sign": int(r[f"{prefix}_sign"]),
                        "eligible": bool(r["eligible"]),
                        "n_a": int(r["n_a"]),
                        "n_b": int(r["n_b"]),
                    }
                    for _, r in splits.iterrows()
                }

            # wait confound: separation vanishes uniformly across strata?
            elig_w = waits.loc[waits["eligible"]]
            if len(elig_w) == 0:
                wait_ok = False
                wait_detail = "no_eligible_wait_strata"
            else:
                w_diffs = elig_w[f"{prefix}_diff"].to_numpy(float)
                w_signs = elig_w[f"{prefix}_sign"].to_numpy(int)
                # vanishes if all |diff| < 0.02 or mixed with near-zero
                vanished = bool(np.all(np.abs(w_diffs) < 0.02))
                # also vanished if no stratum keeps pooled sign with |diff|>=0.02
                keeps = [
                    abs(float(d)) >= 0.02 and int(s) == pooled_sign
                    for d, s in zip(w_diffs, w_signs)
                ]
                wait_ok = (not vanished) and any(keeps)
                wait_detail = {
                    r["wait_stratum"]: {
                        "diff": float(r[f"{prefix}_diff"]),
                        "sign": int(r[f"{prefix}_sign"]),
                        "eligible": bool(r["eligible"]),
                    }
                    for _, r in waits.iterrows()
                }

            # not confined to one tiny subgroup: need >=2 eligible wait strata with same sign
            # OR split persistence already requires multi-period — use wait breadth
            breadth = False
            if len(elig_w):
                keeps_n = sum(
                    1
                    for d, s in zip(
                        elig_w[f"{prefix}_diff"].to_numpy(float),
                        elig_w[f"{prefix}_sign"].to_numpy(int),
                    )
                    if abs(float(d)) >= 0.02 and int(s) == pooled_sign
                )
                breadth = keeps_n >= 2 or (keeps_n >= 1 and same_sign)

            passed = bool(present and same_sign and wait_ok and breadth)
            return {
                "pass": passed,
                "present_pooled": present,
                "pooled_diff": pooled_diff,
                "same_sign_across_splits": same_sign,
                "not_wait_confound_only": wait_ok,
                "not_tiny_subgroup_only": breadth,
                "split_detail": split_detail,
                "wait_detail": wait_detail,
            }

        verdict["contrasts"][tag] = {
            "return_to_origin": _endpoint_eval("return"),
            "reach_opposite": _endpoint_eval("opposite"),
        }
        # overall interesting if either endpoint survives
        verdict["contrasts"][tag]["interesting"] = bool(
            verdict["contrasts"][tag]["return_to_origin"]["pass"]
            or verdict["contrasts"][tag]["reach_opposite"]["pass"]
        )

    return verdict


def main() -> None:
    print("Loading Step 2 artifacts + panel covariates…", flush=True)
    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    metrics = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    events = events.loc[
        events["origin_cell"].isin([CELL_A, CELL_B, CELL_C, CELL_D])
    ].copy()

    wait_cuts = freeze_wait_cuts(events)
    (RESULTS / "step3_wait_cuts_frozen.json").write_text(
        json.dumps(wait_cuts, indent=2), encoding="utf-8"
    )
    print(f"Frozen wait cuts: {wait_cuts}", flush=True)

    # assign wait strata
    qmap = wait_cuts["families"]
    strata = []
    for r in events.itertuples(index=False):
        fam = r.family
        q33 = qmap[fam]["q33"]
        q67 = qmap[fam]["q67"]
        strata.append(assign_wait_stratum(float(r.wait_to_event), q33, q67))
    events["wait_stratum"] = strata

    panel = build_panel()
    events = attach_event_covariates(events, panel)

    # join stratum + covariates onto metrics via event_id
    meta_cols = [
        "event_id",
        "wait_stratum",
        "volatility_state",
        "volume_state",
        "tod_block",
    ]
    metrics = metrics.merge(events[meta_cols], on="event_id", how="left")

    horizons = (PRIMARY_HORIZON, SECONDARY_HORIZON)
    contrasts_spec = (
        (FAMILY_COMP_EXIT, CELL_A, CELL_B, "CompExit_A_vs_B", "B_minus_A"),
        (FAMILY_EXP_EXIT, CELL_C, CELL_D, "ExpExit_C_vs_D", "D_minus_C"),
    )

    # --- split stability ---
    split_rows = []
    for tag_fam, ca, cb, tag, lab in contrasts_spec:
        for h in horizons:
            # pooled
            c = contrast_destination(metrics, ca, cb, h, lab)
            split_rows.append(
                flatten_contrast(
                    {"slice": "POOLED", "family": tag_fam, "contrast_tag": tag}, c
                )
            )
            for spl in ("IS", "Validation", "OOS"):
                sub = metrics.loc[metrics["split"] == spl]
                c = contrast_destination(sub, ca, cb, h, lab)
                split_rows.append(
                    flatten_contrast(
                        {"slice": spl, "family": tag_fam, "contrast_tag": tag}, c
                    )
                )
    split_df = pd.DataFrame(split_rows)
    split_df.to_csv(RESULTS / "step3_split_stability.csv", index=False)

    # --- wait strata ---
    wait_rows = []
    for tag_fam, ca, cb, tag, lab in contrasts_spec:
        for h in horizons:
            for ws in WAIT_STRATA:
                sub = metrics.loc[metrics["wait_stratum"] == ws]
                c = contrast_destination(sub, ca, cb, h, lab)
                wait_rows.append(
                    flatten_contrast(
                        {
                            "wait_stratum": ws,
                            "family": tag_fam,
                            "contrast_tag": tag,
                        },
                        c,
                    )
                )
    wait_df = pd.DataFrame(wait_rows)
    wait_df.to_csv(RESULTS / "step3_wait_strata.csv", index=False)

    # --- orthogonal one-at-a-time ---
    orth_rows = []
    covariate_specs = (
        ("volatility_state", sorted(events["volatility_state"].dropna().unique().tolist())),
        ("volume_state", sorted(events["volume_state"].dropna().unique().tolist())),
        ("tod_block", list(STEP3_TOD_BLOCKS.keys())),
    )
    for tag_fam, ca, cb, tag, lab in contrasts_spec:
        for h in horizons:
            for cov_name, levels in covariate_specs:
                for level in levels:
                    sub = metrics.loc[metrics[cov_name] == level]
                    c = contrast_destination(sub, ca, cb, h, lab)
                    orth_rows.append(
                        flatten_contrast(
                            {
                                "covariate": cov_name,
                                "level": level,
                                "family": tag_fam,
                                "contrast_tag": tag,
                            },
                            c,
                        )
                    )
    orth_df = pd.DataFrame(orth_rows)
    orth_df.to_csv(RESULTS / "step3_orthogonal.csv", index=False)

    verdict = evaluate_criteria(split_df, wait_df)
    # attach orthogonal summary: same-sign persistence within eligible levels
    for tag in ("CompExit_A_vs_B", "ExpExit_C_vs_D"):
        orth_summary = {}
        for cov in ("volatility_state", "volume_state", "tod_block"):
            sub = orth_df[
                (orth_df["contrast_tag"] == tag)
                & (orth_df["covariate"] == cov)
                & (orth_df["horizon"] == PRIMARY_HORIZON)
            ]
            pooled_sign_ret = int(
                split_df.loc[
                    (split_df["contrast_tag"] == tag)
                    & (split_df["slice"] == "POOLED")
                    & (split_df["horizon"] == PRIMARY_HORIZON),
                    "return_sign",
                ].iloc[0]
            )
            pooled_sign_opp = int(
                split_df.loc[
                    (split_df["contrast_tag"] == tag)
                    & (split_df["slice"] == "POOLED")
                    & (split_df["horizon"] == PRIMARY_HORIZON),
                    "opposite_sign",
                ].iloc[0]
            )
            elig = sub.loc[sub["eligible"]]
            orth_summary[cov] = {
                "n_levels_eligible": int(len(elig)),
                "return_same_sign_levels": int(
                    ((elig["return_sign"] == pooled_sign_ret) & (elig["return_sign"] != 0)).sum()
                )
                if len(elig)
                else 0,
                "opposite_same_sign_levels": int(
                    ((elig["opposite_sign"] == pooled_sign_opp) & (elig["opposite_sign"] != 0)).sum()
                )
                if len(elig)
                else 0,
            }
        verdict["contrasts"][tag]["orthogonal_summary"] = orth_summary

    (RESULTS / "step3_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    events[
        [
            "event_id",
            "origin_cell",
            "family",
            "split",
            "wait_to_event",
            "wait_stratum",
            "volatility_state",
            "volume_state",
            "tod_block",
            "event_ny_min",
        ]
    ].to_parquet(RESULTS / "step3_events_enriched.parquet", index=False)
    print("Step 3 tables written.", flush=True)


if __name__ == "__main__":
    main()
