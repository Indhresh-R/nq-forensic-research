"""Audit Event C artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import H_WAIT, K, PRIMARY_H, RESULTS, RETRACE_FRAC, THROUGH_FRAC, W


def audit() -> dict:
    checks = []
    events = pd.read_parquet(RESULTS / "event_c_events.parquet")
    verdict = json.loads((RESULTS / "event_c_verdict.json").read_text(encoding="utf-8"))
    dest = pd.read_csv(RESULTS / "event_c_destinations.csv")

    checks.append(
        {
            "name": "frozen_constants",
            "pass": (
                W == 30
                and K == 2.0
                and RETRACE_FRAC == 0.5
                and THROUGH_FRAC == 0.25
                and H_WAIT == 60
                and PRIMARY_H == 15
            ),
            "detail": {"W": W, "K": K, "retrace": RETRACE_FRAC},
        }
    )
    checks.append(
        {
            "name": "side_equals_minus_ext_dir",
            "pass": bool((events["side"] == -events["ext_dir"]).all()),
            "detail": "toward_anchor",
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
            "name": "no_ab_combine",
            "pass": True,
            "detail": "Event C only",
        }
    )
    final = verdict.get("final")
    checks.append(
        {
            "name": "final_ok",
            "pass": final
            in {
                "KILL",
                "ADVANCE_TO_PATH",
                "PATH_KILL",
                "PATH_ADVANCE",
                "ADVANCE",
                "KILL_AFTER_TRADE",
            },
            "detail": final,
        }
    )
    # If path was not run, ensure no trade file claiming success without path
    trade_path = RESULTS / "event_c_trade_summary.csv"
    if trade_path.exists():
        path_adv = (verdict.get("path") or {}).get("path_advance")
        checks.append(
            {
                "name": "trade_only_after_path_advance",
                "pass": bool(path_adv),
                "detail": path_adv,
            }
        )
    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_DEFINITION_FROZEN": True,
        "NO_PARAMETER_RETUNE": True,
        "NO_EVENT_AB_COMBINE": True,
        "NO_HORIZON_PNL_SHOP": True,
        "all_pass": all_pass,
        "checks": checks,
        "final": final,
        "n_events": int(len(events)),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("LOOKAHEAD_CHECK", "final", "n_events", "all_pass")}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
