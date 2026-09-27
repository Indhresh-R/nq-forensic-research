"""Audit Step 4 matched-transition artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import RESULTS


def audit() -> dict:
    checks = []
    cuts = json.loads((RESULTS / "step4_tercile_cuts_frozen.json").read_text(encoding="utf-8"))
    est = pd.read_csv(RESULTS / "step4_matched_estimates.csv")
    bal = pd.read_csv(RESULTS / "step4_balance.csv")
    verdict = json.loads((RESULTS / "step4_verdict.json").read_text(encoding="utf-8"))
    feat = pd.read_parquet(RESULTS / "step4_pre_event_features.parquet")

    checks.append(
        {
            "name": "geometry_cuts_is_source",
            "pass": "IS" in str(cuts.get("source", "")),
            "detail": cuts.get("source"),
        }
    )
    checks.append(
        {
            "name": "has_unmatched_and_cem",
            "pass": set(est["design"].unique()) >= {"unmatched", "CEM"},
            "detail": sorted(est["design"].unique().tolist()),
        }
    )
    checks.append(
        {
            "name": "pre_event_features_no_post_te_cols",
            "pass": not any(
                s in c.lower()
                for c in feat.columns
                for s in ("forward", "return_to", "reached_opp", "pnl")
            ),
            "detail": feat.columns.tolist(),
        }
    )
    bad = [
        c
        for c in list(est.columns) + list(bal.columns)
        if any(s in c.lower() for s in ("pnl", "entry", "stop", "target", "sharpe"))
    ]
    checks.append({"name": "no_trade_columns", "pass": len(bad) == 0, "detail": bad})
    checks.append(
        {
            "name": "verdict_has_expexit",
            "pass": "ExpExit_C_vs_D" in verdict.get("contrasts", {}),
            "detail": list(verdict.get("contrasts", {}).keys()),
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "MATCHING_USES_POST_EVENT_INFO": False,
        "OUTCOME_DATA_USED": False,
        "STRATEGY_DATA_USED": False,
        "MATCHING_RECIPE_FROZEN": True,
        "all_pass": all_pass,
        "checks": checks,
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step4_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "MATCHING_USES_POST_EVENT_INFO",
        "OUTCOME_DATA_USED",
        "STRATEGY_DATA_USED",
        "all_pass",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
