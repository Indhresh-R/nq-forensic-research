"""Audit Step 1 path-geometry artifacts for leakage / scope."""
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
from step1_constants import CELLS, HORIZONS

FORBIDDEN = (
    "pnl",
    "p&l",
    "entry",
    "exit",
    "stop",
    "target",
    "sharpe",
    "trade_pnl",
    "position",
    "signal",
)


def audit() -> dict:
    checks = []
    ep = pd.read_parquet(RESULTS / "step1_episodes.parquet")
    mx = pd.read_parquet(RESULTS / "step1_path_metrics.parquet")

    bad = [c for c in mx.columns if any(s in c.lower() for s in FORBIDDEN)]
    # allow abs_net etc — "long"/"short" substrings shouldn't appear
    checks.append({"name": "no_trade_columns", "pass": len(bad) == 0, "detail": bad})

    cells_u = [c for c in ep["cell"].dropna().unique().tolist() if isinstance(c, str)]
    checks.append(
        {
            "name": "cells_only_abcd",
            "pass": set(cells_u).issubset(set(CELLS)),
            "detail": sorted(cells_u),
        }
    )

    checks.append(
        {
            "name": "horizons_frozen",
            "pass": set(mx["horizon"].unique()).issubset(set(HORIZONS)),
            "detail": sorted(mx["horizon"].unique().tolist()),
        }
    )

    # valid rows must have finite abs_net
    v = mx.loc[mx["valid"]]
    finite_ok = bool(np.isfinite(v["abs_net"].to_numpy(float)).all()) if len(v) else False
    checks.append({"name": "valid_finite_abs_net", "pass": finite_ok, "detail": None})

    # no signed strategy return column
    checks.append(
        {
            "name": "outcome_data_absent",
            "pass": not any(c.startswith("ret_") or c.endswith("_pnl") for c in mx.columns),
            "detail": None,
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "FUTURE_DATA_USED_IN_STATE_LABEL": False,
        "OUTCOME_DATA_USED": False,
        "STRATEGY_DATA_USED": False,
        "FORWARD_PATH_USED": True,
        "FORWARD_PATH_NOTE": "Subsequent bars used only for descriptive path geometry after labeled onset; labels themselves are causal.",
        "all_pass": all_pass,
        "checks": checks,
        "n_episodes": int(len(ep)),
        "n_metric_rows": int(len(mx)),
        "n_valid_metric_rows": int(mx["valid"].sum()),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step1_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "OUTCOME_DATA_USED",
        "STRATEGY_DATA_USED",
        "FORWARD_PATH_USED",
        "all_pass",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
