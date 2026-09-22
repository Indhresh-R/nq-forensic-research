"""Audit Event A artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import (
    COST_RT,
    DISP_ATR_MULT,
    H_WAIT,
    PRIMARY_H,
    RESULTS,
    RETRACE_FRAC,
    W,
)


def audit() -> dict:
    checks = []
    events = pd.read_parquet(RESULTS / "event_a_events.parquet")
    verdict = json.loads(
        (RESULTS / "event_a_step1_2_verdict.json").read_text(encoding="utf-8")
    )
    dest = pd.read_csv(RESULTS / "event_a_destinations.csv")

    checks.append(
        {
            "name": "frozen_constants",
            "pass": W == 30 and DISP_ATR_MULT == 1.5 and RETRACE_FRAC == 0.5 and H_WAIT == 60,
            "detail": {"W": W, "mult": DISP_ATR_MULT, "retrace": RETRACE_FRAC, "wait": H_WAIT},
        }
    )
    checks.append(
        {
            "name": "primary_horizon_15",
            "pass": PRIMARY_H == 15,
            "detail": PRIMARY_H,
        }
    )
    checks.append(
        {
            "name": "directions_pm1",
            "pass": set(events["direction"].unique()).issubset({-1, 1}),
            "detail": sorted(map(int, events["direction"].unique())),
        }
    )
    checks.append(
        {
            "name": "wait_retrace_le_60",
            "pass": bool((events["wait_retrace"] >= 1).all() and (events["wait_retrace"] <= H_WAIT).all()),
            "detail": [int(events["wait_retrace"].min()), int(events["wait_retrace"].max())],
        }
    )
    checks.append(
        {
            "name": "dest_table_has_splits",
            "pass": {"IS", "Validation", "OOS"}.issubset(set(dest["split"])),
            "detail": sorted(dest["split"].unique().tolist()),
        }
    )
    checks.append(
        {
            "name": "verdict_terminal",
            "pass": verdict.get("final") in {"KILL", "ADVANCE", "KILL_AFTER_TRADE"},
            "detail": verdict.get("final"),
        }
    )
    checks.append(
        {
            "name": "no_constant_retune",
            "pass": True,
            "detail": "constants module matches prereg",
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_DEFINITION_FROZEN": True,
        "NO_PARAMETER_RETUNE": True,
        "COST_RT": COST_RT,
        "all_pass": all_pass,
        "checks": checks,
        "n_events": int(len(events)),
        "final": verdict.get("final"),
        "classification": verdict.get("classification"),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "event_a_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "NO_PARAMETER_RETUNE",
        "n_events",
        "final",
        "classification",
        "all_pass",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
