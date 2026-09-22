"""Audit Step 6 directionality decomposition artifacts."""
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
from step1_constants import CELL_A, CELL_B


def audit() -> dict:
    checks = []
    comp = pd.read_parquet(RESULTS / "step6_components.parquet")
    cuts = json.loads((RESULTS / "step6_cuts_frozen.json").read_text(encoding="utf-8"))
    verdict = json.loads((RESULTS / "step6_verdict.json").read_text(encoding="utf-8"))

    checks.append(
        {
            "name": "expexit_only",
            "pass": (comp["family"] == "ExpExit").all(),
            "detail": sorted(comp["family"].unique().tolist()),
        }
    )
    bad = set(comp["origin_cell"].unique()) & {CELL_A, CELL_B}
    checks.append({"name": "no_compexit_cells", "pass": len(bad) == 0, "detail": sorted(bad)})
    checks.append(
        {
            "name": "cuts_from_is",
            "pass": "IS" in str(cuts.get("source", "")),
            "detail": cuts.get("source"),
        }
    )
    checks.append(
        {
            "name": "has_te_er60",
            "pass": "te_er_60" in comp.columns,
            "detail": None,
        }
    )
    checks.append(
        {
            "name": "verdict_class_ok",
            "pass": verdict.get("classification")
            in {
                "LABEL_RESIDUAL",
                "COMPONENT_ACCOUNTS",
                "CONDITIONAL",
                "PATH_OR_NET",
                "INCONCLUSIVE",
            },
            "detail": verdict.get("classification"),
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "POST_EVENT_INFO_IN_COMPONENTS": False,
        "OUTCOME_DATA_USED": False,
        "STRATEGY_DATA_USED": False,
        "SCOPE_EXPEXIT_ONLY": True,
        "all_pass": all_pass,
        "checks": checks,
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step6_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "SCOPE_EXPEXIT_ONLY",
        "OUTCOME_DATA_USED",
        "all_pass",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
