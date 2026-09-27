"""
Step 4 — matched transition experiment (CEM on pre-event geometry).

No trades. Matching uses only information at/before the →NORMAL event bar.
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
from step1_extract_paths import R_COMP, R_EXP, _range_code, build_panel
from step2_constants import FAMILY_COMP_EXIT, FAMILY_EXP_EXIT
from step3_analyze import (
    assign_tod_block,
    assign_wait_stratum,
    newcombe_diff_ci,
    wilson_ci,
)
from step3_constants import PRIMARY_HORIZON, SECONDARY_HORIZON
from step4_constants import CEM_MIN_CELL


def _tercile_cuts(x: np.ndarray) -> tuple[float, float]:
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return (np.nan, np.nan)
    return float(np.quantile(x, 1.0 / 3.0)), float(np.quantile(x, 2.0 / 3.0))


def _tercile_label(v: float, q33: float, q67: float) -> str:
    if not np.isfinite(v) or not np.isfinite(q33) or not np.isfinite(q67):
        return "NA"
    if v <= q33:
        return "T1"
    if v <= q67:
        return "T2"
    return "T3"


def compute_pre_event_features(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    atr = panel["atr_30"].to_numpy(np.float64)
    ny = panel["ny_min"].to_numpy(np.int16)
    seg = panel["segment_id"].to_numpy(np.int64)
    session = panel["session_date"].to_numpy()
    range_c = _range_code(panel["range_state"].to_numpy(dtype=object))
    n = len(panel)

    rows = []
    for ev in events.itertuples(index=False):
        i0 = int(ev.onset_panel_idx)
        te = int(ev.event_panel_idx)
        if te <= i0:
            continue
        # pre-event window [i0, te)
        sl = slice(i0, te)
        hi = high[sl]
        lo = low[sl]
        cl = close[sl]
        atr_ref = atr[te - 1]
        atr_ok = np.isfinite(atr_ref) and atr_ref > 0

        # ER over pre window
        if len(cl) >= 2:
            abs_path = float(np.sum(np.abs(np.diff(cl))))
            pre_er = abs(float(cl[-1] - cl[0])) / abs_path if abs_path > 0 else np.nan
        else:
            pre_er = np.nan

        pre_range = float(hi.max() - lo.min()) if len(hi) else np.nan
        mid = 0.5 * (float(hi.max()) + float(lo.min())) if len(hi) else np.nan
        c_last = float(cl[-1])
        dist_mid = abs(c_last - mid) / atr_ref if atr_ok and np.isfinite(mid) else np.nan
        dist_edge = (
            min(abs(c_last - float(hi.max())), abs(c_last - float(lo.min()))) / atr_ref
            if atr_ok
            else np.nan
        )
        pre_range_atr = pre_range / atr_ref if atr_ok else np.nan

        # contiguous origin-range run ending at te-1
        origin_r = R_COMP if ev.family == FAMILY_COMP_EXIT else R_EXP
        run = 0
        j = te - 1
        while j >= 0:
            if session[j] != session[te] or seg[j] != seg[te]:
                break
            if j < te - 1 and ny[j + 1] != ny[j] + 1:
                break
            if int(range_c[j]) != origin_r:
                break
            run += 1
            j -= 1

        rows.append(
            {
                "event_id": ev.event_id,
                "origin_cell": ev.origin_cell,
                "family": ev.family,
                "split": ev.split,
                "wait_to_event": int(ev.wait_to_event),
                "pre_er": pre_er,
                "pre_range_atr": pre_range_atr,
                "dist_mid_atr": dist_mid,
                "dist_edge_atr": dist_edge,
                "origin_run_bars": int(run),
                "pre_bars": int(te - i0),
            }
        )
    return pd.DataFrame(rows)


def freeze_geometry_terciles(feat: pd.DataFrame, events: pd.DataFrame) -> dict:
    """IS-only terciles by family for continuous pre-event geometry."""
    merged = feat.merge(
        events[["event_id", "split"]], on="event_id", how="left", suffixes=("", "_e")
    )
    # split already on feat if present
    if "split" not in merged.columns:
        merged = feat.merge(events[["event_id", "split"]], on="event_id", how="left")
    out = {"source": "IS pre-event geometry terciles by family", "families": {}}
    cols = ("origin_run_bars", "pre_range_atr", "pre_er", "dist_mid_atr")
    for fam in (FAMILY_COMP_EXIT, FAMILY_EXP_EXIT):
        is_m = merged.loc[(merged["family"] == fam) & (merged["split"] == "IS")]
        block = {}
        for c in cols:
            q33, q67 = _tercile_cuts(is_m[c].to_numpy(float))
            block[c] = {"q33": q33, "q67": q67, "n_is": int(np.isfinite(is_m[c]).sum())}
        out["families"][fam] = block
    return out


def enrich_for_matching(
    events: pd.DataFrame,
    feat: pd.DataFrame,
    wait_cuts: dict,
    geom_cuts: dict,
    panel: pd.DataFrame,
) -> pd.DataFrame:
    # feat may already include split/family from upstream merge
    keep_feat = [
        c
        for c in feat.columns
        if c
        in {
            "event_id",
            "pre_er",
            "pre_range_atr",
            "dist_mid_atr",
            "dist_edge_atr",
            "origin_run_bars",
            "pre_bars",
        }
    ]
    out = events.merge(feat[keep_feat], on="event_id", how="inner")

    eidx = out["event_panel_idx"].to_numpy(np.int64)
    out["volatility_state"] = panel["volatility_state"].to_numpy(dtype=object)[eidx]
    out["volume_state"] = panel["volume_state"].to_numpy(dtype=object)[eidx]
    out["tod_block"] = [
        assign_tod_block(int(m)) for m in panel["ny_min"].to_numpy(np.int16)[eidx]
    ]

    wait_s = []
    for r in out.itertuples(index=False):
        fam = r.family
        q33 = wait_cuts["families"][fam]["q33"]
        q67 = wait_cuts["families"][fam]["q67"]
        wait_s.append(assign_wait_stratum(float(r.wait_to_event), q33, q67))
    out["wait_stratum"] = wait_s

    for c in ("origin_run_bars", "pre_range_atr", "pre_er", "dist_mid_atr"):
        labels = []
        for r in out.itertuples(index=False):
            q = geom_cuts["families"][r.family][c]
            labels.append(_tercile_label(float(getattr(r, c)), q["q33"], q["q67"]))
        out[f"{c}_tercile"] = labels

    out["cem_key"] = (
        out["wait_stratum"].astype(str)
        + "|"
        + out["volatility_state"].astype(str)
        + "|"
        + out["volume_state"].astype(str)
        + "|"
        + out["tod_block"].astype(str)
        + "|"
        + out["origin_run_bars_tercile"].astype(str)
        + "|"
        + out["pre_range_atr_tercile"].astype(str)
        + "|"
        + out["pre_er_tercile"].astype(str)
        + "|"
        + out["dist_mid_atr_tercile"].astype(str)
    )
    return out


def _destination_rates(flags: np.ndarray) -> tuple[int, int, float]:
    n = int(len(flags))
    k = int(np.sum(flags)) if n else 0
    p = k / n if n else np.nan
    return n, k, float(p)


def unmatched_estimate(metrics: pd.DataFrame, cell_a: str, cell_b: str, horizon: int) -> dict:
    a = metrics[
        (metrics["origin_cell"] == cell_a)
        & (metrics["horizon"] == horizon)
        & (metrics["valid"])
    ]
    b = metrics[
        (metrics["origin_cell"] == cell_b)
        & (metrics["horizon"] == horizon)
        & (metrics["valid"])
    ]
    out = {"n_a": int(len(a)), "n_b": int(len(b)), "horizon": horizon}
    for name, col in (
        ("return", "returned_to_origin_range"),
        ("opposite", "reached_opposite_range"),
    ):
        na, ka, pa = _destination_rates(a[col].to_numpy(bool))
        nb, kb, pb = _destination_rates(b[col].to_numpy(bool))
        diff, lo, hi = newcombe_diff_ci(ka, na, kb, nb)
        out[f"{name}_rate_a"] = pa
        out[f"{name}_rate_b"] = pb
        out[f"{name}_diff"] = diff
        out[f"{name}_diff_ci_lo"] = lo
        out[f"{name}_diff_ci_hi"] = hi
    return out


def cem_estimate(
    enriched: pd.DataFrame,
    metrics: pd.DataFrame,
    cell_a: str,
    cell_b: str,
    horizon: int,
    key_col: str = "cem_key",
) -> dict:
    """Weighted within-stratum B−A / D−C destination differences."""
    m = metrics.loc[(metrics["horizon"] == horizon) & (metrics["valid"])]
    df = enriched.merge(
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
    df = df.loc[df["origin_cell"].isin([cell_a, cell_b])]

    strata = []
    for key, g in df.groupby(key_col, sort=False):
        ga = g.loc[g["origin_cell"] == cell_a]
        gb = g.loc[g["origin_cell"] == cell_b]
        na, nb = len(ga), len(gb)
        if na < CEM_MIN_CELL or nb < CEM_MIN_CELL:
            continue
        w = float(na + nb)
        row = {"key": key, "n_a": na, "n_b": nb, "w": w}
        for name, col in (
            ("return", "returned_to_origin_range"),
            ("opposite", "reached_opposite_range"),
        ):
            pa = float(ga[col].mean())
            pb = float(gb[col].mean())
            row[f"{name}_diff"] = pb - pa
            row[f"{name}_rate_a"] = pa
            row[f"{name}_rate_b"] = pb
        strata.append(row)

    if not strata:
        return {
            "horizon": horizon,
            "n_strata": 0,
            "n_a_matched": 0,
            "n_b_matched": 0,
            "n_a_total": int((enriched["origin_cell"] == cell_a).sum()),
            "n_b_total": int((enriched["origin_cell"] == cell_b).sum()),
            "retained_frac": 0.0,
            "return_diff": np.nan,
            "opposite_diff": np.nan,
        }

    sdf = pd.DataFrame(strata)
    wsum = float(sdf["w"].sum())
    out = {
        "horizon": horizon,
        "n_strata": int(len(sdf)),
        "n_a_matched": int(sdf["n_a"].sum()),
        "n_b_matched": int(sdf["n_b"].sum()),
        "n_a_total": int((enriched["origin_cell"] == cell_a).sum()),
        "n_b_total": int((enriched["origin_cell"] == cell_b).sum()),
        "return_diff": float(np.average(sdf["return_diff"], weights=sdf["w"])),
        "opposite_diff": float(np.average(sdf["opposite_diff"], weights=sdf["w"])),
        "return_rate_a": float(np.average(sdf["return_rate_a"], weights=sdf["w"])),
        "return_rate_b": float(np.average(sdf["return_rate_b"], weights=sdf["w"])),
        "opposite_rate_a": float(np.average(sdf["opposite_rate_a"], weights=sdf["w"])),
        "opposite_rate_b": float(np.average(sdf["opposite_rate_b"], weights=sdf["w"])),
    }
    tot = out["n_a_total"] + out["n_b_total"]
    out["retained_frac"] = (
        (out["n_a_matched"] + out["n_b_matched"]) / tot if tot else 0.0
    )
    return out


def standardized_mean_diff(x_t: np.ndarray, x_c: np.ndarray) -> float:
    x_t = x_t[np.isfinite(x_t)]
    x_c = x_c[np.isfinite(x_c)]
    if len(x_t) < 2 or len(x_c) < 2:
        return np.nan
    mt, mc = float(np.mean(x_t)), float(np.mean(x_c))
    vt, vc = float(np.var(x_t, ddof=1)), float(np.var(x_c, ddof=1))
    denom = np.sqrt(0.5 * (vt + vc))
    if denom <= 0:
        return 0.0
    return (mt - mc) / denom


def balance_table(
    enriched: pd.DataFrame, cell_a: str, cell_b: str, key_col: str = "cem_key"
) -> pd.DataFrame:
    """SMD before matching and after (matched subpopulation only)."""
    cols = (
        "wait_to_event",
        "origin_run_bars",
        "pre_range_atr",
        "pre_er",
        "dist_mid_atr",
        "dist_edge_atr",
    )
    # matched events = those in retained strata
    retained_keys = set()
    for key, g in enriched.groupby(key_col, sort=False):
        na = int((g["origin_cell"] == cell_a).sum())
        nb = int((g["origin_cell"] == cell_b).sum())
        if na >= CEM_MIN_CELL and nb >= CEM_MIN_CELL:
            retained_keys.add(key)
    matched = enriched.loc[enriched[key_col].isin(retained_keys)]

    rows = []
    for c in cols:
        a0 = enriched.loc[enriched["origin_cell"] == cell_a, c].to_numpy(float)
        b0 = enriched.loc[enriched["origin_cell"] == cell_b, c].to_numpy(float)
        a1 = matched.loc[matched["origin_cell"] == cell_a, c].to_numpy(float)
        b1 = matched.loc[matched["origin_cell"] == cell_b, c].to_numpy(float)
        rows.append(
            {
                "covariate": c,
                "smd_before": standardized_mean_diff(b0, a0),
                "smd_after": standardized_mean_diff(b1, a1),
                "mean_a_before": float(np.nanmean(a0)) if len(a0) else np.nan,
                "mean_b_before": float(np.nanmean(b0)) if len(b0) else np.nan,
                "mean_a_after": float(np.nanmean(a1)) if len(a1) else np.nan,
                "mean_b_after": float(np.nanmean(b1)) if len(b1) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def classify_outcome(unmatched: dict, matched: dict) -> dict:
    """Apply predeclared A/B rules per endpoint; overall uses stricter joint view."""
    endpoints = {}
    for ep in ("return", "opposite"):
        u = unmatched.get(f"{ep}_diff")
        m = matched.get(f"{ep}_diff")
        if not np.isfinite(u) or not np.isfinite(m) or abs(u) < 1e-15:
            endpoints[ep] = {"class": "INCONCLUSIVE", "unmatched": u, "matched": m}
            continue
        same_sign = np.sign(m) == np.sign(u)
        survives = same_sign and abs(m) >= 0.5 * abs(u)
        shrinks = (not same_sign) or abs(m) < 0.5 * abs(u)
        if survives:
            cls = "A_SURVIVES"
        elif shrinks:
            cls = "B_COMPOSITIONAL"
        else:
            cls = "INCONCLUSIVE"
        endpoints[ep] = {
            "class": cls,
            "unmatched": float(u),
            "matched": float(m),
            "ratio_abs_matched_over_unmatched": float(abs(m) / abs(u)),
            "same_sign": bool(same_sign),
        }

    classes = {endpoints[e]["class"] for e in endpoints}
    if classes == {"A_SURVIVES"}:
        overall = "A_SURVIVES"
    elif classes == {"B_COMPOSITIONAL"}:
        overall = "B_COMPOSITIONAL"
    elif "A_SURVIVES" in classes and "B_COMPOSITIONAL" in classes:
        overall = "MIXED"
    else:
        overall = "INCONCLUSIVE"
    return {"overall": overall, "endpoints": endpoints}


def main() -> None:
    print("Loading panel + Step2/3 artifacts…", flush=True)
    panel = build_panel()
    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    metrics = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    wait_cuts = json.loads((RESULTS / "step3_wait_cuts_frozen.json").read_text(encoding="utf-8"))
    events = events.loc[
        events["origin_cell"].isin([CELL_A, CELL_B, CELL_C, CELL_D])
    ].copy()

    print("Computing pre-event geometry…", flush=True)
    feat = compute_pre_event_features(panel, events)
    feat.to_parquet(RESULTS / "step4_pre_event_features.parquet", index=False)

    feat = feat.merge(events[["event_id", "split"]], on="event_id", how="left")
    geom_cuts = freeze_geometry_terciles(feat, events)
    (RESULTS / "step4_tercile_cuts_frozen.json").write_text(
        json.dumps(geom_cuts, indent=2), encoding="utf-8"
    )

    print("Building CEM keys…", flush=True)
    enriched = enrich_for_matching(events, feat, wait_cuts, geom_cuts, panel)
    enriched.to_parquet(RESULTS / "step4_events_matched_ready.parquet", index=False)

    estimates = []
    balances = []
    leave_rows = []
    verdict = {"contrasts": {}}

    specs = (
        ("ExpExit_C_vs_D", FAMILY_EXP_EXIT, CELL_C, CELL_D, "D_minus_C", True),
        ("CompExit_A_vs_B", FAMILY_COMP_EXIT, CELL_A, CELL_B, "B_minus_A", False),
    )

    continuous_terciles = (
        "origin_run_bars_tercile",
        "pre_range_atr_tercile",
        "pre_er_tercile",
        "dist_mid_atr_tercile",
    )

    for tag, fam, ca, cb, lab, primary in specs:
        sub_en = enriched.loc[enriched["family"] == fam].copy()
        sub_m = metrics.loc[metrics["family"] == fam]
        for h in (PRIMARY_HORIZON, SECONDARY_HORIZON):
            u = unmatched_estimate(sub_m, ca, cb, h)
            m = cem_estimate(sub_en, sub_m, ca, cb, h, "cem_key")
            estimates.append(
                {
                    "contrast_tag": tag,
                    "label": lab,
                    "primary_contrast": primary,
                    "design": "unmatched",
                    **{f"u_{k}": v for k, v in u.items()},
                    "horizon": h,
                    "return_diff": u["return_diff"],
                    "opposite_diff": u["opposite_diff"],
                    "n_a": u["n_a"],
                    "n_b": u["n_b"],
                    "retained_frac": 1.0,
                    "n_strata": np.nan,
                }
            )
            estimates.append(
                {
                    "contrast_tag": tag,
                    "label": lab,
                    "primary_contrast": primary,
                    "design": "CEM",
                    "horizon": h,
                    "return_diff": m["return_diff"],
                    "opposite_diff": m["opposite_diff"],
                    "return_rate_a": m.get("return_rate_a"),
                    "return_rate_b": m.get("return_rate_b"),
                    "opposite_rate_a": m.get("opposite_rate_a"),
                    "opposite_rate_b": m.get("opposite_rate_b"),
                    "n_a": m["n_a_matched"],
                    "n_b": m["n_b_matched"],
                    "n_a_total": m["n_a_total"],
                    "n_b_total": m["n_b_total"],
                    "retained_frac": m["retained_frac"],
                    "n_strata": m["n_strata"],
                }
            )

            if h == PRIMARY_HORIZON:
                bal = balance_table(sub_en, ca, cb)
                bal.insert(0, "contrast_tag", tag)
                balances.append(bal)
                outcome = classify_outcome(u, m)
                verdict["contrasts"][tag] = {
                    "primary": primary,
                    "unmatched": {
                        "return_diff": u["return_diff"],
                        "opposite_diff": u["opposite_diff"],
                    },
                    "matched": {
                        "return_diff": m["return_diff"],
                        "opposite_diff": m["opposite_diff"],
                        "retained_frac": m["retained_frac"],
                        "n_strata": m["n_strata"],
                    },
                    "classification": outcome,
                }

                # leave-one-in diagnostics: drop one continuous tercile from key
                base_parts = [
                    "wait_stratum",
                    "volatility_state",
                    "volume_state",
                    "tod_block",
                ]
                for drop in continuous_terciles:
                    keep = base_parts + [c for c in continuous_terciles if c != drop]
                    key = sub_en[keep[0]].astype(str)
                    for c in keep[1:]:
                        key = key + "|" + sub_en[c].astype(str)
                    tmp = sub_en.copy()
                    tmp["cem_key_alt"] = key
                    alt = cem_estimate(tmp, sub_m, ca, cb, h, "cem_key_alt")
                    leave_rows.append(
                        {
                            "contrast_tag": tag,
                            "dropped_factor": drop,
                            "horizon": h,
                            "return_diff": alt["return_diff"],
                            "opposite_diff": alt["opposite_diff"],
                            "retained_frac": alt["retained_frac"],
                            "n_strata": alt["n_strata"],
                        }
                    )

    est_df = pd.DataFrame(estimates)
    est_df.to_csv(RESULTS / "step4_matched_estimates.csv", index=False)
    bal_df = pd.concat(balances, ignore_index=True) if balances else pd.DataFrame()
    bal_df.to_csv(RESULTS / "step4_balance.csv", index=False)
    pd.DataFrame(leave_rows).to_csv(RESULTS / "step4_leave_one_in.csv", index=False)

    # Outcome C diagnostic: if full CEM is A but dropping one factor yields B
    for tag, block in verdict["contrasts"].items():
        full_cls = block["classification"]["overall"]
        leave = [r for r in leave_rows if r["contrast_tag"] == tag]
        c_hits = []
        if full_cls == "A_SURVIVES":
            u_ret = block["unmatched"]["return_diff"]
            u_opp = block["unmatched"]["opposite_diff"]
            for r in leave:
                # if dropping this factor makes effect shrink below half on both endpoints
                shrink_ret = (
                    np.isfinite(r["return_diff"])
                    and abs(r["return_diff"]) < 0.5 * abs(u_ret)
                )
                shrink_opp = (
                    np.isfinite(r["opposite_diff"])
                    and abs(r["opposite_diff"]) < 0.5 * abs(u_opp)
                )
                if shrink_ret and shrink_opp:
                    c_hits.append(r["dropped_factor"])
        block["outcome_C_candidate_factors"] = c_hits
        if c_hits and full_cls == "A_SURVIVES":
            block["interpretation_hint"] = "C_POSSIBLE_SINGLE_FACTOR"
        else:
            block["interpretation_hint"] = full_cls

    (RESULTS / "step4_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print("Step 4 estimates written.", flush=True)
    print(json.dumps(verdict, indent=2, default=str)[:2000], flush=True)


if __name__ == "__main__":
    main()
