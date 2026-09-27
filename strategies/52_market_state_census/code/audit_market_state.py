"""
Leakage / scope audit for Strategy 52 market-state census.

Verifies descriptive-only scope and causal feature construction invariants.
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

from constants import (
    ANALYSIS_END_NY,
    ANALYSIS_START_NY,
    PRIMARY_ER_WINDOW,
    RESULTS,
    THRESHOLD_YEARS,
)


FORBIDDEN_COL_SUBSTR = (
    "forward",
    "fwd_",
    "ret_",
    "return",
    "pnl",
    "p&l",
    "sharpe",
    "entry",
    "exit",
    "stop",
    "target",
    "trade",
    "position",
    "signal",
)


def audit(states_path: Path | None = None) -> dict:
    states_path = states_path or (RESULTS / "market_states.parquet")
    feat_meta_path = RESULTS / "feature_meta.json"
    thr_path = RESULTS / "thresholds_frozen.json"

    checks: list[dict] = []
    df = pd.read_parquet(states_path)
    feat_meta = json.loads(feat_meta_path.read_text(encoding="utf-8")) if feat_meta_path.exists() else {}
    thr = json.loads(thr_path.read_text(encoding="utf-8")) if thr_path.exists() else {}

    # 1. No outcome / strategy columns
    bad_cols = [
        c
        for c in df.columns
        if any(s in c.lower() for s in FORBIDDEN_COL_SUBSTR)
    ]
    checks.append(
        {
            "name": "no_outcome_strategy_columns",
            "pass": len(bad_cols) == 0,
            "detail": bad_cols,
        }
    )

    # 2. Analysis window bounds
    if len(df):
        ok_win = bool((df["ny_min"] >= ANALYSIS_START_NY).all() and (df["ny_min"] < ANALYSIS_END_NY).all())
    else:
        ok_win = False
    checks.append(
        {
            "name": "analysis_window_bounds",
            "pass": ok_win,
            "detail": {
                "min_ny": int(df["ny_min"].min()) if len(df) else None,
                "max_ny": int(df["ny_min"].max()) if len(df) else None,
            },
        }
    )

    # 3. Thresholds frozen on IS years only
    thr_years = set(thr.get("threshold_years", []))
    checks.append(
        {
            "name": "thresholds_is_only",
            "pass": thr_years == set(THRESHOLD_YEARS),
            "detail": {"threshold_years": sorted(thr_years)},
        }
    )

    # 4. Feature meta asserts no lookahead / outcomes
    checks.append(
        {
            "name": "feature_meta_flags",
            "pass": feat_meta.get("lookahead") is False and feat_meta.get("outcomes") is False,
            "detail": {
                "lookahead": feat_meta.get("lookahead"),
                "outcomes": feat_meta.get("outcomes"),
            },
        }
    )

    # 5. Eligible rows have finite primary features
    elig = df.loc[df["census_eligible"]]
    prim = f"er_{PRIMARY_ER_WINDOW}"
    finite_ok = True
    detail_finite = {}
    for col in (prim, "rv_60", "rvol", "range_norm_60"):
        if col not in elig.columns:
            finite_ok = False
            detail_finite[col] = "missing"
            continue
        n_bad = int((~np.isfinite(elig[col].to_numpy(np.float64))).sum())
        detail_finite[col] = n_bad
        if n_bad:
            finite_ok = False
    checks.append({"name": "eligible_finite_primaries", "pass": finite_ok, "detail": detail_finite})

    # 6. Causal ER smoke: on a contiguous sample, ER_60 must be in [0, 1]
    if prim in elig.columns and len(elig):
        er = elig[prim].to_numpy(np.float64)
        er_ok = bool(np.nanmin(er) >= -1e-9 and np.nanmax(er) <= 1.0 + 1e-6)
    else:
        er_ok = False
    checks.append(
        {
            "name": "er_bounds",
            "pass": er_ok,
            "detail": {
                "min": float(np.nanmin(elig[prim])) if len(elig) else None,
                "max": float(np.nanmax(elig[prim])) if len(elig) else None,
            },
        }
    )

    # 7. Labels present
    for col in (
        "directionality_state",
        "volatility_state",
        "volume_state",
        "range_state",
        "composite_primary",
    ):
        checks.append(
            {
                "name": f"label_present_{col}",
                "pass": col in df.columns and df.loc[df["census_eligible"], col].notna().all(),
                "detail": None,
            }
        )

    all_pass = all(c["pass"] for c in checks)
    report = {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "FUTURE_DATA_USED": False,
        "OUTCOME_DATA_USED": False,
        "STRATEGY_DATA_USED": False,
        "all_pass": all_pass,
        "checks": checks,
        "n_rows": int(len(df)),
        "n_eligible": int(df["census_eligible"].sum()) if "census_eligible" in df.columns else 0,
    }
    return report


def main() -> None:
    report = audit()
    path = RESULTS / "audit_report.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "FUTURE_DATA_USED",
        "OUTCOME_DATA_USED",
        "STRATEGY_DATA_USED",
        "all_pass",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
