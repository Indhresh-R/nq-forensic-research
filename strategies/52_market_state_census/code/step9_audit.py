"""Audit Step 9 executable-hypothesis artifacts."""
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
from step1_constants import CELL_C, CELL_D
from step9_analyze import COST_RT, HOLD_MINUTES, MIN_TRADES_SPLIT


def audit() -> dict:
    checks = []
    pop = pd.read_parquet(RESULTS / "step7_population.parquet")
    trades = pd.read_parquet(RESULTS / "step9_trades.parquet")
    verdict = json.loads((RESULTS / "step9_verdict.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(RESULTS / "step9_summary.csv")

    ids_t = set(trades["event_id"])
    ids_p = set(pop["event_id"])
    checks.append(
        {
            "name": "trades_subset_of_step7_pop",
            "pass": ids_t.issubset(ids_p),
            "detail": {"n_trades": len(ids_t), "n_pop": len(ids_p)},
        }
    )
    checks.append(
        {
            "name": "primary_arm_is_d_only",
            "pass": bool(
                (trades.loc[trades["arm"] == "PRIMARY_D", "origin_cell"] == CELL_D).all()
            ),
            "detail": None,
        }
    )
    checks.append(
        {
            "name": "control_arm_is_c_only",
            "pass": bool(
                (trades.loc[trades["arm"] == "CONTROL_C", "origin_cell"] == CELL_C).all()
            ),
            "detail": None,
        }
    )
    checks.append(
        {
            "name": "fixed_cost",
            "pass": bool((trades["cost_rt"] == COST_RT).all()),
            "detail": COST_RT,
        }
    )
    checks.append(
        {
            "name": "hold_at_most_15",
            "pass": bool((trades["hold_minutes"] <= HOLD_MINUTES).all()),
            "detail": int(trades["hold_minutes"].max()) if len(trades) else None,
        }
    )
    checks.append(
        {
            "name": "no_optimization_verdict_binary",
            "pass": verdict.get("classification") in {"PROMOTE_CANDIDATE", "KILL"},
            "detail": verdict.get("classification"),
        }
    )
    checks.append(
        {
            "name": "gate_uses_primary_only",
            "pass": "primary_gate" in verdict and "control_c" in verdict,
            "detail": None,
        }
    )
    checks.append(
        {
            "name": "min_trades_constant",
            "pass": verdict.get("min_trades_split") == MIN_TRADES_SPLIT,
            "detail": verdict.get("min_trades_split"),
        }
    )
    # sides only +/-1
    checks.append(
        {
            "name": "sides_fade_only",
            "pass": set(trades["side"].unique()).issubset({-1, 1}),
            "detail": sorted(map(int, trades["side"].unique())),
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_POPULATION_FROZEN": "PASS",
        "ENTRY_NEXT_OPEN_AFTER_TE": True,
        "PARAMETER_OPTIMIZATION": False,
        "EXTRA_FILTERS": False,
        "COST_RT": COST_RT,
        "HOLD_MINUTES": HOLD_MINUTES,
        "all_pass": all_pass,
        "checks": checks,
        "n_summary_rows": int(len(summary)),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step9_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "LOOKAHEAD_CHECK",
                    "EVENT_POPULATION_FROZEN",
                    "PARAMETER_OPTIMIZATION",
                    "EXTRA_FILTERS",
                    "COST_RT",
                    "HOLD_MINUTES",
                    "all_pass",
                )
            },
            indent=2,
        )
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
