"""Aggregate Step 2 transition-event path metrics and contrasts."""
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
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D, HORIZONS
from step2_constants import FAMILY_COMP_EXIT, FAMILY_EXP_EXIT


RATE_COLS = (
    "still_normal",
    "returned_to_origin_range",
    "reached_opposite_range",
    "terminal_dir_high",
    "terminal_dir_low",
    "p_terminal_normal",
    "p_terminal_origin",
    "p_terminal_opposite",
)

CONT_COLS = (
    "wait_to_event",
    "abs_net_atr",
    "max_up_atr",
    "max_down_atr",
    "max_range_atr",
    "er_forward",
    "time_to_leave_normal",
    "time_to_origin_range",
    "time_to_opposite_range",
    "path_dir_high_share",
    "path_dir_low_share",
)


def _summarize(df: pd.DataFrame) -> dict:
    out: dict = {"n": int(len(df))}
    v = df.loc[df["valid"]] if "valid" in df.columns else df
    out["n_valid"] = int(len(v))
    if len(v) == 0:
        return out
    # wait is constant across horizons for an event — use once from valid rows
    for c in RATE_COLS:
        if c not in v.columns:
            continue
        x = v[c].to_numpy(dtype=float)
        x = x[np.isfinite(x)]
        out[f"rate_{c}"] = float(np.mean(x)) if len(x) else None
    for c in CONT_COLS:
        if c not in v.columns:
            continue
        x = v[c].to_numpy(dtype=float)
        x = x[np.isfinite(x)]
        if len(x) == 0:
            out[f"{c}_n"] = 0
            continue
        out[f"{c}_n"] = int(len(x))
        out[f"{c}_mean"] = float(np.mean(x))
        out[f"{c}_median"] = float(np.median(x))
        out[f"{c}_p25"] = float(np.quantile(x, 0.25))
        out[f"{c}_p75"] = float(np.quantile(x, 0.75))
    return out


def _contrast(a: dict, b: dict, label: str) -> dict:
    keys = [
        "rate_still_normal",
        "rate_returned_to_origin_range",
        "rate_reached_opposite_range",
        "rate_terminal_dir_high",
        "rate_terminal_dir_low",
        "abs_net_atr_median",
        "max_range_atr_median",
        "er_forward_median",
        "max_up_atr_median",
        "max_down_atr_median",
        "wait_to_event_median",
        "time_to_leave_normal_median",
        "path_dir_high_share_median",
        "path_dir_low_share_median",
    ]
    deltas = {}
    for k in keys:
        va, vb = a.get(k), b.get(k)
        deltas[k] = None if va is None or vb is None else float(vb) - float(va)
    return {
        "contrast": label,
        "n_a": a.get("n_valid"),
        "n_b": b.get("n_valid"),
        "deltas_b_minus_a": deltas,
        "a": {k: a.get(k) for k in keys},
        "b": {k: b.get(k) for k in keys},
    }


def main() -> None:
    metrics = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    print(f"events={len(events):,} metrics={len(metrics):,}", flush=True)

    # Wait distribution once per event (not per horizon)
    wait_rows = []
    for cell, g in events.groupby("origin_cell"):
        w = g["wait_to_event"].to_numpy(float)
        wait_rows.append(
            {
                "origin_cell": cell,
                "n_events": int(len(g)),
                "wait_median": float(np.median(w)),
                "wait_mean": float(np.mean(w)),
                "wait_p25": float(np.quantile(w, 0.25)),
                "wait_p75": float(np.quantile(w, 0.75)),
            }
        )
    pd.DataFrame(wait_rows).to_csv(RESULTS / "step2_wait_to_event.csv", index=False)

    rows = []
    for cell in (CELL_A, CELL_B, CELL_C, CELL_D):
        for h in HORIZONS:
            sub = metrics[(metrics["origin_cell"] == cell) & (metrics["horizon"] == h)]
            s = _summarize(sub)
            s["origin_cell"] = cell
            s["family"] = (
                FAMILY_COMP_EXIT if cell in (CELL_A, CELL_B) else FAMILY_EXP_EXIT
            )
            s["horizon"] = h
            rows.append(s)
    summary = pd.DataFrame(rows)
    summary.to_csv(RESULTS / "step2_cell_summary.csv", index=False)

    # splits
    split_rows = []
    for split, g in metrics.groupby("split", sort=False):
        for cell in (CELL_A, CELL_B, CELL_C, CELL_D):
            for h in HORIZONS:
                sub = g[(g["origin_cell"] == cell) & (g["horizon"] == h)]
                s = _summarize(sub)
                s["split"] = split
                s["origin_cell"] = cell
                s["horizon"] = h
                split_rows.append(s)
    pd.DataFrame(split_rows).to_csv(
        RESULTS / "step2_cell_summary_by_split.csv", index=False
    )

    contrasts: dict = {"by_horizon": {}}
    for h in HORIZONS:
        sh = summary[summary["horizon"] == h].set_index("origin_cell")
        contrasts["by_horizon"][str(h)] = {
            "A_vs_B_CompExit": _contrast(
                sh.loc[CELL_A].to_dict(),
                sh.loc[CELL_B].to_dict(),
                "B_minus_A_CompExit_to_NORMAL",
            ),
            "C_vs_D_ExpExit": _contrast(
                sh.loc[CELL_C].to_dict(),
                sh.loc[CELL_D].to_dict(),
                "D_minus_C_ExpExit_to_NORMAL",
            ),
        }

    (RESULTS / "step2_contrasts.json").write_text(
        json.dumps(contrasts, indent=2, default=str), encoding="utf-8"
    )

    key_cols = [
        "origin_cell",
        "family",
        "horizon",
        "n_valid",
        "rate_still_normal",
        "rate_returned_to_origin_range",
        "rate_reached_opposite_range",
        "abs_net_atr_median",
        "max_range_atr_median",
        "er_forward_median",
        "max_up_atr_median",
        "max_down_atr_median",
        "wait_to_event_median",
        "time_to_leave_normal_median",
        "path_dir_high_share_median",
        "path_dir_low_share_median",
    ]
    present = [c for c in key_cols if c in summary.columns]
    summary[present].to_csv(RESULTS / "step2_key_table.csv", index=False)
    print("Step 2 summaries written.", flush=True)


if __name__ == "__main__":
    main()
