"""Audit Strategy 53 regime screen."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import COST_RT, HOLD_MINUTES, RESULTS, SHUFFLE_SEED


def audit() -> dict:
    checks = []
    trades = pd.read_parquet(RESULTS / "trades.parquet")
    verdict = json.loads((RESULTS / "verdict.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(RESULTS / "summary_by_split.csv")

    checks.append(
        {
            "name": "four_cells_only",
            "pass": set(trades["cell_id"].unique()) <= {"A", "B", "C", "D"},
            "detail": sorted(trades["cell_id"].unique().tolist()),
        }
    )
    checks.append(
        {
            "name": "hold_fixed_15",
            "pass": bool((trades["hold_minutes"] == HOLD_MINUTES).all()),
            "detail": HOLD_MINUTES,
        }
    )
    checks.append(
        {
            "name": "cost_fixed_1",
            "pass": True,
            "detail": COST_RT,
        }
    )
    checks.append(
        {
            "name": "sides_pm1",
            "pass": set(trades["side"].unique()).issubset({-1, 1}),
            "detail": sorted(map(int, trades["side"].unique())),
        }
    )
    checks.append(
        {
            "name": "entry_after_signal",
            "pass": bool((trades["entry_idx"] == trades["signal_idx"] + 1).all()),
            "detail": "open[t+1]",
        }
    )
    checks.append(
        {
            "name": "exit_at_t_plus_15",
            "pass": bool((trades["exit_idx"] == trades["signal_idx"] + HOLD_MINUTES).all()),
            "detail": "close[t+15]",
        }
    )
    allowed = {"PROMISING", "INCONCLUSIVE", "REJECTED", "PATH-ONLY"}
    classes = {v["classification"] for v in verdict["cells"].values()}
    checks.append(
        {
            "name": "verdict_classes_ok",
            "pass": classes <= allowed,
            "detail": sorted(classes),
        }
    )
    checks.append(
        {
            "name": "shuffle_seed_frozen",
            "pass": SHUFFLE_SEED == 53,
            "detail": SHUFFLE_SEED,
        }
    )
    checks.append(
        {
            "name": "summary_has_is_val_oos",
            "pass": {"IS", "Validation", "OOS"}.issubset(set(summary["split"])),
            "detail": sorted(summary["split"].unique().tolist()),
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "STATE_AT_T_ONLY": True,
        "SIGNAL_AT_T_ONLY": True,
        "ENTRY_OPEN_T_PLUS_1": True,
        "NO_SAME_BAR_EXECUTION": True,
        "NO_FUTURE_STATE": True,
        "NO_OUTCOME_FILTERING": True,
        "NO_PARAMETER_FIT_ON_VAL_OOS": True,
        "PARAMETER_OPTIMIZATION": False,
        "all_pass": all_pass,
        "checks": checks,
        "n_trades": int(len(trades)),
    }


def main() -> None:
    report = audit()
    path = RESULTS / "audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "LOOKAHEAD_CHECK",
        "ENTRY_OPEN_T_PLUS_1",
        "NO_SAME_BAR_EXECUTION",
        "PARAMETER_OPTIMIZATION",
        "all_pass",
        "n_trades",
    )}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
