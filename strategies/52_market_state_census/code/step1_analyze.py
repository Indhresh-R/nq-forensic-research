"""Aggregate Step 1 path metrics and A/B, C/D contrasts (descriptive only)."""
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
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D, CELLS, HORIZONS


RATE_COLS = (
    "still_compressed",
    "still_expanded",
    "reached_normal",
    "reached_expansion",
    "left_expansion",
    "p_terminal_normal",
    "p_terminal_expansion",
    "p_terminal_compression",
)

CONT_COLS = (
    "abs_net",
    "abs_net_atr",
    "max_up",
    "max_down",
    "max_up_atr",
    "max_down_atr",
    "max_range",
    "max_range_atr",
    "er_forward",
    "time_to_normal",
    "time_to_expansion",
    "time_to_leave_compression",
    "time_to_leave_expansion",
    "expansion_is_directional",
    "expansion_is_two_sided",
)


def _summarize_block(df: pd.DataFrame) -> dict:
    out: dict = {"n": int(len(df)), "n_valid": int(df["valid"].sum()) if "valid" in df else int(len(df))}
    v = df.loc[df["valid"]] if "valid" in df.columns else df
    out["n_valid"] = int(len(v))
    if len(v) == 0:
        return out
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


def cell_horizon_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cell in CELLS:
        for h in HORIZONS:
            sub = metrics[(metrics["cell"] == cell) & (metrics["horizon"] == h)]
            s = _summarize_block(sub)
            s["cell"] = cell
            s["horizon"] = h
            rows.append(s)
    return pd.DataFrame(rows)


def contrast(a_sum: dict, b_sum: dict, label: str) -> dict:
    """Descriptive delta of key rates/medians (B−A or D−C style)."""
    keys = [
        "rate_reached_expansion",
        "rate_reached_normal",
        "rate_still_compressed",
        "rate_still_expanded",
        "rate_left_expansion",
        "abs_net_atr_median",
        "max_range_atr_median",
        "er_forward_median",
        "max_up_atr_median",
        "max_down_atr_median",
        "time_to_expansion_median",
        "time_to_leave_compression_median",
        "time_to_leave_expansion_median",
        "expansion_is_directional_mean",
        "expansion_is_two_sided_mean",
    ]
    deltas = {}
    for k in keys:
        va = a_sum.get(k)
        vb = b_sum.get(k)
        if va is None or vb is None:
            deltas[k] = None
        else:
            deltas[k] = float(vb) - float(va)
    return {
        "contrast": label,
        "n_a": a_sum.get("n_valid"),
        "n_b": b_sum.get("n_valid"),
        "deltas_b_minus_a": deltas,
        "a": {k: a_sum.get(k) for k in keys if k in a_sum},
        "b": {k: b_sum.get(k) for k in keys if k in b_sum},
    }


def build_contrasts(summary: pd.DataFrame) -> dict:
    out = {"by_horizon": {}}
    for h in HORIZONS:
        sh = summary[summary["horizon"] == h].set_index("cell")
        if CELL_A not in sh.index or CELL_B not in sh.index:
            continue
        a = sh.loc[CELL_A].to_dict()
        b = sh.loc[CELL_B].to_dict()
        c = sh.loc[CELL_C].to_dict() if CELL_C in sh.index else {}
        d = sh.loc[CELL_D].to_dict() if CELL_D in sh.index else {}
        out["by_horizon"][str(h)] = {
            "A_vs_B": contrast(a, b, "B_minus_A_compression"),
            "C_vs_D": contrast(c, d, "D_minus_C_expansion") if c and d else None,
        }
    return out


def split_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, g in metrics.groupby("split", sort=False):
        for cell in CELLS:
            for h in HORIZONS:
                sub = g[(g["cell"] == cell) & (g["horizon"] == h)]
                s = _summarize_block(sub)
                s["split"] = split
                s["cell"] = cell
                s["horizon"] = h
                rows.append(s)
    return pd.DataFrame(rows)


def main() -> None:
    metrics = pd.read_parquet(RESULTS / "step1_path_metrics.parquet")
    print(f"metrics={len(metrics):,}", flush=True)

    summary = cell_horizon_summary(metrics)
    summary.to_csv(RESULTS / "step1_cell_summary.csv", index=False)

    by_split = split_summary(metrics)
    by_split.to_csv(RESULTS / "step1_cell_summary_by_split.csv", index=False)

    contrasts = build_contrasts(summary)
    (RESULTS / "step1_contrasts.json").write_text(
        json.dumps(contrasts, indent=2, default=str), encoding="utf-8"
    )

    # Compact key table for report
    key_cols = [
        "cell",
        "horizon",
        "n_valid",
        "rate_still_compressed",
        "rate_reached_normal",
        "rate_reached_expansion",
        "rate_still_expanded",
        "rate_left_expansion",
        "abs_net_atr_median",
        "max_range_atr_median",
        "er_forward_median",
        "max_up_atr_median",
        "max_down_atr_median",
        "time_to_expansion_median",
        "time_to_leave_compression_median",
        "time_to_leave_expansion_median",
        "expansion_is_directional_mean",
        "expansion_is_two_sided_mean",
    ]
    present = [c for c in key_cols if c in summary.columns]
    summary[present].to_csv(RESULTS / "step1_key_table.csv", index=False)
    print("Step 1 summaries written.", flush=True)


if __name__ == "__main__":
    main()
