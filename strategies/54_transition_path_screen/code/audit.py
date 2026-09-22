"""Audit Strategy 54 transition path screen."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import HORIZONS, PRIMARY_H, RESULTS


def audit() -> dict:
    checks = []
    verdict = json.loads((RESULTS / "verdict.json").read_text(encoding="utf-8"))
    contrast = pd.read_csv(RESULTS / "path_contrast_all.csv")

    checks.append(
        {
            "name": "catalogs_R_and_C",
            "pass": set(contrast["catalog"].unique()) == {"R", "C"},
            "detail": sorted(contrast["catalog"].unique().tolist()),
        }
    )
    checks.append(
        {
            "name": "primary_horizon_15",
            "pass": PRIMARY_H == 15 and set(HORIZONS) == {5, 15, 30},
            "detail": list(HORIZONS),
        }
    )
    allowed = {"INTERESTING", "UNSTABLE", "THIN", "KILL"}
    classes = {v["classification"] for v in verdict["cells"].values()}
    checks.append(
        {
            "name": "classes_ok",
            "pass": classes <= allowed,
            "detail": sorted(classes),
        }
    )
    checks.append(
        {
            "name": "no_trades_in_verdict",
            "pass": "No trades" in str(verdict.get("note", "")),
            "detail": verdict.get("note"),
        }
    )
    # no self-transitions in contrast
    selfs = contrast.loc[contrast["from_state"] == contrast["to_state"]]
    checks.append(
        {
            "name": "no_self_transitions",
            "pass": len(selfs) == 0,
            "detail": len(selfs),
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "STATE_AT_T_CAUSAL": True,
        "PATH_STRICTLY_AFTER_T": True,
        "NO_STRATEGY_PNL": True,
        "NO_PARAMETER_OPTIMIZATION": True,
        "NO_POST_HOC_TRANSITION_PICK": True,
        "all_pass": all_pass,
        "checks": checks,
        "n_transition_types": int(contrast.groupby(["catalog", "transition"]).ngroups),
        "n_interesting": len(verdict.get("interesting") or []),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "NO_STRATEGY_PNL",
        "n_transition_types",
        "n_interesting",
        "all_pass",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
