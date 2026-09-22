"""
Step 8 — Path feasibility audit for frozen low-ER ExpExit population.

No trades. No optimization. No new filters.
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
from step1_constants import CELL_C, CELL_D, HORIZONS
from step2_constants import FAMILY_EXP_EXIT
from step3_analyze import newcombe_diff_ci
from step3_constants import MIN_N_VALID
from step7_analyze import load_low_er_cut

EXPECTED_N = 9442
EXPECTED_C = 4529
EXPECTED_D = 4913
POP_TOL = 0.01  # 1% relative

# Descriptive point levels only (not stops/targets)
POINT_LEVELS = (5, 10, 15, 20)
COST_MID_RT = 1.0  # NQ points; research_framework/execution_assumptions.md

EXCURSION_COLS = (
    "max_up",
    "max_down",
    "abs_max_excursion",
    "net_displacement",
    "hl_range",
    "abs_net",
)


def _qstats(x: np.ndarray) -> dict:
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {
            "n": 0,
            "mean": np.nan,
            "p10": np.nan,
            "p25": np.nan,
            "p50": np.nan,
            "p75": np.nan,
            "p90": np.nan,
        }
    qs = np.quantile(x, [0.10, 0.25, 0.50, 0.75, 0.90])
    return {
        "n": int(len(x)),
        "mean": float(np.mean(x)),
        "p10": float(qs[0]),
        "p25": float(qs[1]),
        "p50": float(qs[2]),
        "p75": float(qs[3]),
        "p90": float(qs[4]),
    }


def verify_population(pop: pd.DataFrame) -> dict:
    n = len(pop)
    nc = int((pop["origin_cell"] == CELL_C).sum())
    nd = int((pop["origin_cell"] == CELL_D).sum())
    ok = (
        abs(n - EXPECTED_N) / EXPECTED_N <= POP_TOL
        and abs(nc - EXPECTED_C) / EXPECTED_C <= POP_TOL
        and abs(nd - EXPECTED_D) / EXPECTED_D <= POP_TOL
    )
    return {
        "ok": ok,
        "n": n,
        "n_c": nc,
        "n_d": nd,
        "expected_n": EXPECTED_N,
        "expected_c": EXPECTED_C,
        "expected_d": EXPECTED_D,
    }


def load_population_events() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    pop = pd.read_parquet(RESULTS / "step7_population.parquet")
    check = verify_population(pop)
    if not check["ok"]:
        raise RuntimeError(f"Step7 population count mismatch: {check}")

    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    events = events.loc[events["event_id"].isin(pop["event_id"])].copy()
    if len(events) != len(pop):
        raise RuntimeError(
            f"Event join mismatch: pop={len(pop)} events={len(events)}"
        )
    # confirm low-ER cut still holds via step7 column
    cut = load_low_er_cut()
    if not (pop["te_er_60"] <= cut + 1e-12).all():
        raise RuntimeError("Population contains te_er_60 above frozen cut")
    return pop, events, check


def attach_paths(pop: pd.DataFrame) -> pd.DataFrame:
    """Reuse Step 2 path metrics (strictly after te) for frozen event_ids."""
    m = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    m = m.loc[
        (m["family"] == FAMILY_EXP_EXIT) & (m["event_id"].isin(pop["event_id"]))
    ].copy()
    # enrich excursion aliases
    m["abs_max_excursion"] = np.fmax(m["max_up"], m["max_down"])
    m["net_displacement"] = m["net_move"]
    m["hl_range"] = m["max_range"]
    m["abs_net"] = m["abs_net"]
    meta = pop[["event_id", "te_er_60", "duration_bars"]]
    return m.merge(meta, on="event_id", how="inner")


def competing_path_60(paths: pd.DataFrame) -> pd.DataFrame:
    h60 = paths.loc[(paths["horizon"] == 60) & (paths["valid"])].copy()
    rows = []
    for r in h60.itertuples(index=False):
        t_ret = r.time_to_origin_range
        t_opp = r.time_to_opposite_range
        ret_ok = np.isfinite(t_ret)
        opp_ok = np.isfinite(t_opp)
        if ret_ok and opp_ok:
            if t_ret < t_opp:
                first = "return_to_origin"
                t_first = float(t_ret)
            elif t_opp < t_ret:
                first = "reach_opposite"
                t_first = float(t_opp)
            else:
                first = "same_bar_both"
                t_first = float(t_ret)
        elif ret_ok:
            first = "return_to_origin"
            t_first = float(t_ret)
        elif opp_ok:
            first = "reach_opposite"
            t_first = float(t_opp)
        else:
            first = "neither_within_60m"
            t_first = np.nan
        rows.append(
            {
                "event_id": r.event_id,
                "origin_cell": r.origin_cell,
                "split": r.split,
                "first_destination": first,
                "time_to_first_destination": t_first,
                "time_to_origin_range": float(t_ret) if ret_ok else np.nan,
                "time_to_opposite_range": float(t_opp) if opp_ok else np.nan,
            }
        )
    return pd.DataFrame(rows)


def destination_contrast(paths: pd.DataFrame, horizon: int, split: str | None = None) -> dict:
    g = paths.loc[(paths["horizon"] == horizon) & (paths["valid"])]
    if split is not None:
        g = g.loc[g["split"] == split]
    gc = g.loc[g["origin_cell"] == CELL_C]
    gd = g.loc[g["origin_cell"] == CELL_D]
    nc, nd = len(gc), len(gd)
    out: dict = {
        "horizon": horizon,
        "split": split or "ALL",
        "n_c": nc,
        "n_d": nd,
        "eligible": nc >= MIN_N_VALID and nd >= MIN_N_VALID,
    }
    for name, col in (
        ("return", "returned_to_origin_range"),
        ("opposite", "reached_opposite_range"),
    ):
        kc = int(gc[col].sum()) if nc else 0
        kd = int(gd[col].sum()) if nd else 0
        diff, lo, hi = newcombe_diff_ci(kc, nc, kd, nd)
        out[f"{name}_rate_c"] = kc / nc if nc else np.nan
        out[f"{name}_rate_d"] = kd / nd if nd else np.nan
        out[f"{name}_diff"] = diff
        out[f"{name}_diff_ci_lo"] = lo
        out[f"{name}_diff_ci_hi"] = hi
    return out


def excursion_block(paths: pd.DataFrame, horizon: int, cell: str | None = None) -> list[dict]:
    g = paths.loc[(paths["horizon"] == horizon) & (paths["valid"])]
    if cell is not None:
        g = g.loc[g["origin_cell"] == cell]
    rows = []
    label = cell or "POOLED"
    for col in EXCURSION_COLS:
        st = _qstats(g[col].to_numpy(float))
        row = {
            "metric_family": "excursion",
            "horizon": horizon,
            "origin_cell": label,
            "feature": col,
            **st,
        }
        x = g[col].to_numpy(float)
        x = x[np.isfinite(x)]
        row["frac_gt_0"] = float(np.mean(x > 0)) if len(x) else np.nan
        for thr in POINT_LEVELS:
            row[f"frac_gt_{thr}"] = float(np.mean(x > thr)) if len(x) else np.nan
        rows.append(row)
    return rows


def timing_block(comp: pd.DataFrame) -> list[dict]:
    rows = []
    for cell in (CELL_C, CELL_D, None):
        g = comp if cell is None else comp.loc[comp["origin_cell"] == cell]
        label = cell or "POOLED"
        for feat, mask_col in (
            ("time_to_origin_range", "time_to_origin_range"),
            ("time_to_opposite_range", "time_to_opposite_range"),
            ("time_to_first_destination", "time_to_first_destination"),
        ):
            x = g[mask_col].to_numpy(float)
            # only reached (finite) — censored excluded
            st = _qstats(x)
            rows.append(
                {
                    "metric_family": "timing",
                    "horizon": 60,
                    "origin_cell": label,
                    "feature": feat,
                    "n_reached": st["n"],
                    "n_events": int(len(g)),
                    "frac_reached": st["n"] / len(g) if len(g) else np.nan,
                    "mean": st["mean"],
                    "p25": st["p25"],
                    "p50": st["p50"],
                    "p75": st["p75"],
                    "p90": st["p90"],
                }
            )
    return rows


def competing_freq(comp: pd.DataFrame) -> list[dict]:
    rows = []
    for cell in (CELL_C, CELL_D):
        g = comp.loc[comp["origin_cell"] == cell]
        n = len(g)
        for first, cnt in g["first_destination"].value_counts().items():
            rows.append(
                {
                    "metric_family": "competing_path",
                    "horizon": 60,
                    "origin_cell": cell,
                    "feature": str(first),
                    "n": int(cnt),
                    "rate": float(cnt) / n if n else np.nan,
                }
            )
    return rows


def atr_block(events: pd.DataFrame) -> list[dict]:
    rows = []
    for cell in (CELL_C, CELL_D, None):
        g = events if cell is None else events.loc[events["origin_cell"] == cell]
        st = _qstats(g["atr_e"].to_numpy(float))
        rows.append(
            {
                "metric_family": "atr_e",
                "horizon": 0,
                "origin_cell": cell or "POOLED",
                "feature": "atr_e",
                **st,
            }
        )
    return rows


def build_feasibility_table(
    paths: pd.DataFrame, comp: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict] = []

    # destination contrasts all horizons + by split at 30
    for h in HORIZONS:
        d = destination_contrast(paths, h)
        rows.append({"metric_family": "destination_contrast", **d})
    for sp in ("IS", "Validation", "OOS"):
        d = destination_contrast(paths, 30, split=sp)
        rows.append({"metric_family": "destination_contrast", **d})

    for h in HORIZONS:
        rows.extend(excursion_block(paths, h, None))
        rows.extend(excursion_block(paths, h, CELL_C))
        rows.extend(excursion_block(paths, h, CELL_D))

    rows.extend(timing_block(comp))
    rows.extend(competing_freq(comp))
    rows.extend(atr_block(events))

    # cost context row
    rows.append(
        {
            "metric_family": "cost_context",
            "horizon": 0,
            "origin_cell": "POOLED",
            "feature": "mid_round_trip_nq_points",
            "p50": COST_MID_RT,
            "note": "research_framework/execution_assumptions.md mid=1.0; not subtracted",
        }
    )
    return pd.DataFrame(rows)


def classify(table: pd.DataFrame, comp: pd.DataFrame, ref30: dict) -> dict:
    def _dest(h: int, split: str = "ALL") -> dict | None:
        m = table.loc[
            (table["metric_family"] == "destination_contrast")
            & (table["horizon"] == h)
            & (table["split"] == split)
        ]
        if m.empty:
            return None
        return m.iloc[0].to_dict()

    def _hl_median(h: int) -> float:
        m = table.loc[
            (table["metric_family"] == "excursion")
            & (table["horizon"] == h)
            & (table["origin_cell"] == "POOLED")
            & (table["feature"] == "hl_range")
        ]
        if m.empty:
            return np.nan
        return float(m.iloc[0]["p50"])

    ref_ret_sign = 1 if ref30["return_diff"] > 0 else -1
    ref_opp_sign = 1 if ref30["opposite_diff"] > 0 else -1

    def _assoc_ok(d: dict | None, min_abs: float = 0.05) -> bool:
        if d is None or not d.get("eligible"):
            return False
        rd, od = float(d["return_diff"]), float(d["opposite_diff"])
        if not (np.isfinite(rd) and np.isfinite(od)):
            return False
        rs = 1 if rd > 0 else (-1 if rd < 0 else 0)
        os_ = 1 if od > 0 else (-1 if od < 0 else 0)
        return (
            rs == ref_ret_sign
            and os_ == ref_opp_sign
            and abs(rd) >= min_abs
            and abs(od) >= min_abs
        )

    d15 = _dest(15)
    d30 = _dest(30)
    d30_is = _dest(30, "IS")
    d30_val = _dest(30, "Validation")
    d30_oos = _dest(30, "OOS")

    # timing: median first destination among reached
    tmed = table.loc[
        (table["metric_family"] == "timing")
        & (table["origin_cell"] == "POOLED")
        & (table["feature"] == "time_to_first_destination")
    ]
    median_first = float(tmed.iloc[0]["p50"]) if len(tmed) else np.nan
    n_reached = int(tmed.iloc[0]["n_reached"]) if len(tmed) else 0

    clause1_15 = _assoc_ok(d15)
    clause1_30 = _assoc_ok(d30)
    clause2 = (
        np.isfinite(_hl_median(15))
        and np.isfinite(_hl_median(30))
        and _hl_median(15) >= 5.0
        and _hl_median(30) >= 5.0
    )
    clause3 = np.isfinite(median_first) and median_first <= 15.0 and n_reached >= 200

    def _sign(d: dict | None) -> int:
        if d is None or not d.get("eligible"):
            return 0
        rd = float(d["return_diff"])
        if not np.isfinite(rd) or abs(rd) < 1e-15:
            return 0
        return 1 if rd > 0 else -1

    signs = [_sign(d30_is), _sign(d30_val), _sign(d30_oos)]
    splits_eligible = all(
        d is not None and d.get("eligible") for d in (d30_is, d30_val, d30_oos)
    )
    clause4 = (
        splits_eligible
        and all(s == ref_ret_sign for s in signs)
        and all(s != 0 for s in signs)
    )

    detail = {
        "clause1_15": clause1_15,
        "clause1_30": clause1_30,
        "clause2_hl_range": clause2,
        "hl_range_p50_15": _hl_median(15),
        "hl_range_p50_30": _hl_median(30),
        "clause3_median_first_dest": clause3,
        "median_time_to_first_destination": median_first,
        "n_reached_first_dest": n_reached,
        "clause4_split_sign": clause4,
        "return_diff_30_IS": None if d30_is is None else d30_is.get("return_diff"),
        "return_diff_30_Validation": None if d30_val is None else d30_val.get("return_diff"),
        "return_diff_30_OOS": None if d30_oos is None else d30_oos.get("return_diff"),
        "reference_30": ref30,
    }

    # classification priority
    if not clause1_30 and not (d30 and d30.get("eligible")):
        cls = "PATH_INCONCLUSIVE"
        decision = "STOP"
    elif not splits_eligible and clause1_30:
        # cannot evaluate stability
        cls = "PATH_INCONCLUSIVE"
        decision = "STOP"
    elif clause1_30 and not clause4:
        cls = "PATH_UNSTABLE"
        decision = "STOP"
    elif clause1_30 and (not clause2 or not clause3):
        cls = "PATH_WEAK"
        decision = "STOP"
    elif clause1_15 and clause1_30 and clause2 and clause3 and clause4:
        cls = "PATH_FEASIBLE"
        decision = "GO_TO_STEP9"
    elif clause1_30:
        # association at 30 but 15 failed while other clauses ok → weak
        cls = "PATH_WEAK"
        decision = "STOP"
    else:
        cls = "PATH_INCONCLUSIVE"
        decision = "STOP"

    return {
        "classification": cls,
        "decision": decision,
        "research_question_answer": (
            "Yes — enough stable path geometry to justify constructing one simple "
            "executable hypothesis in a separate Step 9."
            if decision == "GO_TO_STEP9"
            else "No — do not build a strategy; stop after this feasibility audit."
        ),
        "detail": detail,
        "cost_mid_rt_nq_points": COST_MID_RT,
    }


def main() -> None:
    print("Loading frozen Step7 population…", flush=True)
    pop, events, pop_check = load_population_events()
    print(f"Population OK: {pop_check}", flush=True)

    print("Attaching Step2 forward paths…", flush=True)
    paths = attach_paths(pop)
    # keep lean event-path artifact
    keep_cols = [
        "event_id",
        "origin_cell",
        "split",
        "horizon",
        "valid",
        "te_er_60",
        "duration_bars",
        "max_up",
        "max_down",
        "abs_max_excursion",
        "net_displacement",
        "hl_range",
        "abs_net",
        "returned_to_origin_range",
        "reached_opposite_range",
        "time_to_origin_range",
        "time_to_opposite_range",
    ]
    paths[keep_cols].to_parquet(RESULTS / "step8_event_paths.parquet", index=False)

    comp = competing_path_60(paths)
    comp.to_parquet(RESULTS / "step8_competing_paths.parquet", index=False)

    table = build_feasibility_table(paths, comp, events)
    table.to_csv(RESULTS / "step8_path_feasibility.csv", index=False)

    ref30 = destination_contrast(paths, 30)
    verdict = classify(table, comp, ref30)
    (RESULTS / "step8_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    (RESULTS / "step8_population_check.json").write_text(
        json.dumps(pop_check, indent=2), encoding="utf-8"
    )
    print(f"Verdict: {verdict['classification']} / {verdict['decision']}", flush=True)
    d = verdict["detail"]
    print(
        f"hl_range p50 15/30={d['hl_range_p50_15']:.2f}/{d['hl_range_p50_30']:.2f}; "
        f"median first dest={d['median_time_to_first_destination']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
