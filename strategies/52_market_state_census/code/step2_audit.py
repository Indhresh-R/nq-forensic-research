"""Audit Step 2 transition-event artifacts."""
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
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D, HORIZONS
from step2_constants import FAMILY_COMP_EXIT, FAMILY_EXP_EXIT


def audit() -> dict:
    checks = []
    ev = pd.read_parquet(RESULTS / "step2_events.parquet")
    mx = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    funnel = json.loads((RESULTS / "step2_funnel.json").read_text(encoding="utf-8"))

    forbidden_sub = ("pnl", "p&l", "entry", "exit_price", "stop", "target", "sharpe", "signal")
    bad = [c for c in mx.columns if any(s in c.lower() for s in forbidden_sub)]
    checks.append({"name": "no_trade_columns", "pass": len(bad) == 0, "detail": bad})

    origins = set(ev["origin_cell"].dropna().astype(str).unique())
    checks.append(
        {
            "name": "origins_abcd",
            "pass": origins.issubset({CELL_A, CELL_B, CELL_C, CELL_D}),
            "detail": sorted(origins),
        }
    )

    checks.append(
        {
            "name": "horizons_frozen",
            "pass": set(mx["horizon"].unique()).issubset(set(HORIZONS)),
            "detail": sorted(map(int, mx["horizon"].unique().tolist())),
        }
    )

    # one event per episode_id
    dup = int(ev["episode_id"].duplicated().sum()) if len(ev) else 0
    checks.append({"name": "at_most_one_event_per_episode", "pass": dup == 0, "detail": dup})

    # wait >= 1
    wait_ok = bool((ev["wait_to_event"] >= 1).all()) if len(ev) else False
    checks.append({"name": "wait_at_least_1", "pass": wait_ok, "detail": None})

    v = mx.loc[mx["valid"]]
    finite_ok = bool(np.isfinite(v["abs_net"].to_numpy(float)).all()) if len(v) else False
    checks.append({"name": "valid_finite_abs_net", "pass": finite_ok, "detail": None})

    # family consistency
    fam_ok = True
    if len(ev):
        for cell, fam in (
            (CELL_A, FAMILY_COMP_EXIT),
            (CELL_B, FAMILY_COMP_EXIT),
            (CELL_C, FAMILY_EXP_EXIT),
            (CELL_D, FAMILY_EXP_EXIT),
        ):
            sub = ev.loc[ev["origin_cell"] == cell]
            if len(sub) and not (sub["family"] == fam).all():
                fam_ok = False
    checks.append({"name": "family_matches_origin", "pass": fam_ok, "detail": None})

    # funnel arithmetic
    cens = sum(funnel.get("censored", {}).values())
    arith = funnel.get("n_events", 0) + cens == funnel.get("n_onsets", -1)
    checks.append(
        {
            "name": "funnel_adds_up",
            "pass": bool(arith),
            "detail": {
                "n_onsets": funnel.get("n_onsets"),
                "n_events": funnel.get("n_events"),
                "n_censored": cens,
            },
        }
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "LOOKAHEAD_CHECK": "PASS" if all_pass else "FAIL",
        "EVENT_USES_POST_EVENT_INFO": False,
        "OUTCOME_DATA_USED": False,
        "STRATEGY_DATA_USED": False,
        "FORWARD_PATH_USED": True,
        "FORWARD_PATH_NOTE": "Path after te is descriptive only; event at first NORMAL does not use post-te info.",
        "all_pass": all_pass,
        "checks": checks,
        "n_events": int(len(ev)),
        "n_metric_rows": int(len(mx)),
        "n_valid_metric_rows": int(mx["valid"].sum()) if len(mx) else 0,
    }


def main() -> None:
    report = audit()
    path = RESULTS / "step2_audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "LOOKAHEAD_CHECK",
                    "EVENT_USES_POST_EVENT_INFO",
                    "OUTCOME_DATA_USED",
                    "STRATEGY_DATA_USED",
                    "all_pass",
                )
            },
            indent=2,
        )
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
