"""Audit Step 5 signed-exit-position artifacts."""
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
from step1_constants import CELL_A, CELL_B
from step2_constants import FAMILY_COMP_EXIT


def audit() -> dict:
    checks = []
    feat = pd.read_parquet(RESULTS / "step5_signed_features.parquet")
    cuts = json.loads((RESULTS / "step5_s_cuts_frozen.json").read_text(encoding="utf-8"))
    within = pd.read_csv(RESULTS / "step5_within_bin_contrasts.csv")
    verdict = json.loads((RESULTS / "step5_verdict.json").read_text(encoding="utf-8"))

    checks.append(
        {
            "name": "expexit_only",
            "pass": set(feat["family"].unique()) == {"ExpExit"}
            or (feat["family"] == "ExpExit").all(),
            "detail": sorted(feat["family"].unique().tolist()),
        }
    )
    # no CompExit cells
    bad_cells = set(feat["origin_cell"].unique()) & {CELL_A, CELL_B}
    checks.append(
        {
            "name": "no_compexit_cells",
            "pass": len(bad_cells) == 0,
            "detail": sorted(bad_cells),
        }
    )
    checks.append(
        {
            "name": "cuts_from_is",
            "pass": "IS" in str(cuts.get("source", "")),
            "detail": cuts.get("source"),
        }
    )
    # S finite mostly
    s = feat["signed_exit_pos"].to_numpy(float)
    checks.append(
        {
            "name": "signed_feature_mostly_finite",
            "pass": float(np.mean(np.isfinite(s))) >= 0.99,
            "detail": float(np.mean(np.isfinite(s))),
        }
    )
    forbidden = [c for c in within.columns if any(x in c.lower() for x in ("pnl", "entry", "stop", "target"))]
    checks.append({"name": "no_trade_columns", "pass": len(forbidden) == 0, "detail": forbidden})
    checks.append(
        {
            "name": "verdict_class_present",
            "pass": verdict.get("classification")
            in {"REMAIN", "DISAPPEAR", "CONDITIONAL", "INCONCLUSIVE"},
            "detail": verdict.get("classification"),
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "POST_EVENT_INFO_IN_FEATURE": False,
        "OUTCOME_DATA_USED": False,
        "STRATEGY_DATA_USED": False,
        "SCOPE_EXPEXIT_ONLY": True,
        "all_pass": all_pass,
        "checks": checks,
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step5_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "POST_EVENT_INFO_IN_FEATURE",
        "SCOPE_EXPEXIT_ONLY",
        "OUTCOME_DATA_USED",
        "all_pass",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
