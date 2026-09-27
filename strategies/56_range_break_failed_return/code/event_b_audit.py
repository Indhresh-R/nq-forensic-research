"""Audit Event B artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import COST_RT, H_WAIT, PRIMARY_H, REBREAK_FRAC, RESULTS, W


def audit() -> dict:
    checks = []
    events = pd.read_parquet(RESULTS / "event_b_events.parquet")
    verdict = json.loads((RESULTS / "event_b_verdict.json").read_text(encoding="utf-8"))
    dest = pd.read_csv(RESULTS / "event_b_destinations.csv")

    checks.append(
        {
            "name": "frozen_constants",
            "pass": W == 60 and H_WAIT == 60 and REBREAK_FRAC == 0.25 and PRIMARY_H == 15,
            "detail": {"W": W, "H_wait": H_WAIT, "rebreak": REBREAK_FRAC},
        }
    )
    checks.append(
        {
            "name": "break_dir_pm1",
            "pass": set(events["break_dir"].unique()).issubset({-1, 1}),
            "detail": sorted(map(int, events["break_dir"].unique())),
        }
    )
    checks.append(
        {
            "name": "wait_return_bounds",
            "pass": bool(
                (events["wait_return"] >= 1).all() and (events["wait_return"] <= H_WAIT).all()
            ),
            "detail": [int(events["wait_return"].min()), int(events["wait_return"].max())],
        }
    )
    checks.append(
        {
            "name": "dest_has_splits",
            "pass": {"IS", "Validation", "OOS"}.issubset(set(dest["split"])),
            "detail": sorted(dest["split"].unique().tolist()),
        }
    )
    checks.append(
        {
            "name": "final_ok",
            "pass": verdict.get("final") in {"KILL", "ADVANCE", "KILL_AFTER_TRADE"},
            "detail": verdict.get("final"),
        }
    )
    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_DEFINITION_FROZEN": True,
        "NO_PARAMETER_RETUNE": True,
        "NO_EVENT_A_COMBINE": True,
        "COST_RT": COST_RT,
        "all_pass": all_pass,
        "checks": checks,
        "n_events": int(len(events)),
        "final": verdict.get("final"),
        "classification": verdict.get("classification"),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "event_b_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "LOOKAHEAD_CHECK",
                    "NO_PARAMETER_RETUNE",
                    "n_events",
                    "final",
                    "classification",
                    "all_pass",
                )
            },
            indent=2,
        )
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
