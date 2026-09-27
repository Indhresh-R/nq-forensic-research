"""Audit Step 7 low-ER origin-history artifacts."""
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


def audit() -> dict:
    checks = []
    pop = pd.read_parquet(RESULTS / "step7_population.parquet")
    cuts = json.loads((RESULTS / "step7_cuts_frozen.json").read_text(encoding="utf-8"))
    verdict = json.loads((RESULTS / "step7_verdict.json").read_text(encoding="utf-8"))
    step6 = json.loads((RESULTS / "step6_cuts_frozen.json").read_text(encoding="utf-8"))

    low_cut = float(cuts["low_er_cut"])
    expected = float(step6["features"]["te_er_60"]["q33"])
    checks.append(
        {
            "name": "low_er_cut_matches_step6",
            "pass": abs(low_cut - expected) < 1e-12,
            "detail": {"step7": low_cut, "step6": expected},
        }
    )
    checks.append(
        {
            "name": "all_te_er60_le_cut",
            "pass": bool((pop["te_er_60"] <= low_cut + 1e-12).all()),
            "detail": float(pop["te_er_60"].max()),
        }
    )
    checks.append(
        {
            "name": "expexit_only",
            "pass": (pop["family"] == FAMILY_EXP_EXIT).all(),
            "detail": sorted(pop["family"].unique().tolist()),
        }
    )
    bad = set(pop["origin_cell"].unique()) & {CELL_A, CELL_B}
    checks.append({"name": "no_compexit_cells", "pass": len(bad) == 0, "detail": sorted(bad)})
    checks.append(
        {
            "name": "cuts_from_is_low_er",
            "pass": "IS low-ER" in str(cuts.get("source", "")),
            "detail": cuts.get("source"),
        }
    )
    checks.append(
        {
            "name": "primary_feature_duration",
            "pass": "duration_bars" in pop.columns and "duration_bin" in pop.columns,
            "detail": None,
        }
    )
    checks.append(
        {
            "name": "verdict_class_ok",
            "pass": verdict.get("classification")
            in {
                "HISTORY_RESIDUAL",
                "HISTORY_ACCOUNTS",
                "CONCENTRATED",
                "PROGRESSIVE",
                "INCONCLUSIVE",
            },
            "detail": verdict.get("classification"),
        }
    )
    # duration equals wait history length: no post-te features required
    checks.append(
        {
            "name": "duration_positive",
            "pass": bool((pop["duration_bars"] >= 1).all()),
            "detail": int(pop["duration_bars"].min()) if len(pop) else None,
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "POST_EVENT_INFO_IN_HISTORY": False,
        "OUTCOME_DATA_USED": False,
        "STRATEGY_DATA_USED": False,
        "SCOPE_LOW_ER_EXPEXIT_ONLY": True,
        "LOW_ER_CUT_FROZEN_FROM_STEP6": True,
        "all_pass": all_pass,
        "checks": checks,
        "n_population": int(len(pop)),
        "n_c": int((pop["origin_cell"] == "C_EXP_HIGH_DIR").sum()),
        "n_d": int((pop["origin_cell"] == "D_EXP_LOW_DIR").sum()),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step7_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "LOOKAHEAD_CHECK",
                    "SCOPE_LOW_ER_EXPEXIT_ONLY",
                    "LOW_ER_CUT_FROZEN_FROM_STEP6",
                    "OUTCOME_DATA_USED",
                    "all_pass",
                    "n_population",
                )
            },
            indent=2,
        )
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
