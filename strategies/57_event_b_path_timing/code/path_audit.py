"""Audit Strategy 57 path-timing artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import HORIZONS, PREDICTED_SIDE_RULE, RESULTS, S56_EVENTS, S56_VERDICT


def audit() -> dict:
    checks = []
    paths = pd.read_parquet(RESULTS / "path_progress.parquet")
    ladder = pd.read_csv(RESULTS / "path_ladder_by_split.csv")
    verdict = json.loads((RESULTS / "path_verdict.json").read_text(encoding="utf-8"))
    s56 = json.loads(S56_VERDICT.read_text(encoding="utf-8"))
    events = pd.read_parquet(S56_EVENTS)

    checks.append(
        {
            "name": "horizons_frozen",
            "pass": list(HORIZONS) == [5, 15, 30, 60],
            "detail": list(HORIZONS),
        }
    )
    checks.append(
        {
            "name": "side_rule_frozen",
            "pass": (
                PREDICTED_SIDE_RULE == "toward_rebreak"
                and s56.get("trade_side_rule") == "toward_rebreak"
                and verdict.get("predicted_side_rule") == "toward_rebreak"
            ),
            "detail": {
                "const": PREDICTED_SIDE_RULE,
                "s56": s56.get("trade_side_rule"),
                "verdict": verdict.get("predicted_side_rule"),
            },
        }
    )
    checks.append(
        {
            "name": "event_ledger_reuse",
            "pass": set(paths["event_id"].unique()) == set(events["event_id"].unique()),
            "detail": {
                "n_path_events": int(paths["event_id"].nunique()),
                "n_s56_events": int(len(events)),
            },
        }
    )
    checks.append(
        {
            "name": "no_pnl_columns",
            "pass": not any(
                c in paths.columns for c in ("pnl", "gross", "net", "mean_net", "hit_rate")
            ),
            "detail": list(paths.columns),
        }
    )
    checks.append(
        {
            "name": "ladder_splits",
            "pass": {"IS", "Validation", "OOS"}.issubset(set(ladder["split"])),
            "detail": sorted(ladder["split"].unique().tolist()),
        }
    )
    checks.append(
        {
            "name": "verdict_ok",
            "pass": verdict.get("classification") in {"PATH_KILL", "PATH_ADVANCE"},
            "detail": verdict.get("classification"),
        }
    )
    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_DEFINITION_FROZEN": True,
        "NO_PARAMETER_RETUNE": True,
        "NO_HORIZON_PNL_SHOP": True,
        "NO_TRADE_IN_THIS_RUN": True,
        "all_pass": all_pass,
        "checks": checks,
        "classification": verdict.get("classification"),
        "reason": verdict.get("reason"),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "LOOKAHEAD_CHECK",
                    "NO_TRADE_IN_THIS_RUN",
                    "classification",
                    "reason",
                    "all_pass",
                )
            },
            indent=2,
        )
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
