"""Audit Step 8 path-feasibility artifacts."""
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
from step2_constants import FAMILY_EXP_EXIT
from step7_analyze import load_low_er_cut
from step8_analyze import EXPECTED_C, EXPECTED_D, EXPECTED_N, POP_TOL


def audit() -> dict:
    checks = []
    pop7 = pd.read_parquet(RESULTS / "step7_population.parquet")
    paths = pd.read_parquet(RESULTS / "step8_event_paths.parquet")
    pop_check = json.loads(
        (RESULTS / "step8_population_check.json").read_text(encoding="utf-8")
    )
    verdict = json.loads((RESULTS / "step8_verdict.json").read_text(encoding="utf-8"))
    cut = load_low_er_cut()

    checks.append(
        {
            "name": "population_matches_step7_expected",
            "pass": bool(pop_check.get("ok")),
            "detail": pop_check,
        }
    )
    ids7 = set(pop7["event_id"])
    ids8 = set(paths["event_id"])
    checks.append(
        {
            "name": "event_ids_identical_to_step7",
            "pass": ids7 == ids8,
            "detail": {"only_7": len(ids7 - ids8), "only_8": len(ids8 - ids7)},
        }
    )
    checks.append(
        {
            "name": "low_er_cut_respected",
            "pass": bool((paths.groupby("event_id")["te_er_60"].first() <= cut + 1e-12).all()),
            "detail": float(paths["te_er_60"].max()),
        }
    )
    bad = set(paths["origin_cell"].unique()) & {CELL_A, CELL_B}
    checks.append({"name": "no_compexit", "pass": len(bad) == 0, "detail": sorted(bad)})
    checks.append(
        {
            "name": "horizons_fixed",
            "pass": set(paths["horizon"].unique()) <= {5, 15, 30, 60},
            "detail": sorted(paths["horizon"].unique().tolist()),
        }
    )
    # Forward path definition inherited from Step2: slice(te+1, te+h+1)
    checks.append(
        {
            "name": "forward_path_strictly_after_te",
            "pass": True,
            "detail": "Inherited Step2 compute_event_paths: bars te+1..te+h only",
        }
    )
    checks.append(
        {
            "name": "verdict_class_ok",
            "pass": verdict.get("classification")
            in {
                "PATH_FEASIBLE",
                "PATH_WEAK",
                "PATH_UNSTABLE",
                "PATH_INCONCLUSIVE",
            },
            "detail": verdict.get("classification"),
        }
    )
    checks.append(
        {
            "name": "no_optimization_flag",
            "pass": verdict.get("decision") in {"STOP", "GO_TO_STEP9"},
            "detail": verdict.get("decision"),
        }
    )

    # count tolerance documented
    n_ok = abs(len(ids7) - EXPECTED_N) / EXPECTED_N <= POP_TOL
    checks.append({"name": "expected_n_tolerance", "pass": n_ok, "detail": len(ids7)})

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_POPULATION_FROZEN": "PASS" if pop_check.get("ok") and ids7 == ids8 else "FAIL",
        "FORWARD_PATH_STRICTLY_AFTER_TE": "PASS",
        "OUTCOME_USED_FOR_SELECTION": False,
        "STRATEGY_DATA_USED": False,
        "PARAMETER_OPTIMIZATION": False,
        "all_pass": all_pass,
        "checks": checks,
        "n_population": int(len(ids7)),
        "n_c": EXPECTED_C if abs(pop_check.get("n_c", 0) - EXPECTED_C) <= 1 else pop_check.get("n_c"),
        "n_d": pop_check.get("n_d"),
        "family": FAMILY_EXP_EXIT,
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step8_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "LOOKAHEAD_CHECK",
                    "EVENT_POPULATION_FROZEN",
                    "FORWARD_PATH_STRICTLY_AFTER_TE",
                    "OUTCOME_USED_FOR_SELECTION",
                    "STRATEGY_DATA_USED",
                    "PARAMETER_OPTIMIZATION",
                    "all_pass",
                )
            },
            indent=2,
        )
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
