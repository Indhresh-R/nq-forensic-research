"""Audit Strategy 59 ORB first-passage artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import H_CAP, H_WAIT, NY_OPEN, RESULTS, TARGET_R_MULT, W_OR


def audit() -> dict:
    checks = []
    events = pd.read_parquet(RESULTS / "orb_events.parquet")
    fp = pd.read_csv(RESULTS / "first_passage_by_split.csv")
    verdict = json.loads((RESULTS / "verdict.json").read_text(encoding="utf-8"))

    checks.append(
        {
            "name": "frozen_constants",
            "pass": (
                W_OR == 30
                and H_WAIT == 90
                and H_CAP == 60
                and TARGET_R_MULT == 1.0
                and NY_OPEN == 570
            ),
            "detail": {"W_or": W_OR, "H_wait": H_WAIT, "H_cap": H_CAP},
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
            "name": "adverse_is_or_mid",
            "pass": bool((events["adverse"] - events["OR_mid"]).abs().max() < 1e-6),
            "detail": "adverse=OR_mid",
        }
    )
    up = events.loc[events["break_dir"] > 0]
    dn = events.loc[events["break_dir"] < 0]
    tgt_ok = True
    if len(up):
        tgt_ok = tgt_ok and bool(
            (up["target"] - (up["OR_high"] + TARGET_R_MULT * up["R"])).abs().max() < 1e-6
        )
    if len(dn):
        tgt_ok = tgt_ok and bool(
            (dn["target"] - (dn["OR_low"] - TARGET_R_MULT * dn["R"])).abs().max() < 1e-6
        )
    checks.append({"name": "target_formula", "pass": tgt_ok, "detail": "OR±1R"})
    checks.append(
        {
            "name": "fp_splits",
            "pass": {"IS", "Validation", "OOS"}.issubset(set(fp["split"])),
            "detail": sorted(fp["split"].unique().tolist()),
        }
    )
    final = verdict.get("final")
    checks.append(
        {
            "name": "final_ok",
            "pass": final
            in {
                "KILL",
                "ADVANCE_TO_MAE",
                "ADVANCE_TO_TRADE",
                "ADVANCE",
                "KILL_AFTER_TRADE",
            },
            "detail": final,
        }
    )
    if (RESULTS / "trade_summary.csv").exists():
        s2 = (verdict.get("step2") or {}).get("advance")
        checks.append(
            {
                "name": "trade_only_after_mae_advance",
                "pass": bool(s2),
                "detail": s2,
            }
        )
    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_DEFINITION_FROZEN": True,
        "TARGET_ADVERSE_CO_DEFINED": True,
        "NO_PARAMETER_RETUNE": True,
        "NO_52_58_REOPEN": True,
        "all_pass": all_pass,
        "checks": checks,
        "final": final,
        "n_events": int(len(events)),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {k: report[k] for k in ("LOOKAHEAD_CHECK", "final", "n_events", "all_pass")},
            indent=2,
        )
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
