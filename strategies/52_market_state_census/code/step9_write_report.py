"""Write STEP9_EXECUTABLE_HYPOTHESIS.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
STRAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import RESULTS
from step9_analyze import COST_RT, HOLD_MINUTES


def _md_table(df: pd.DataFrame, cols: list[str]) -> str:
    use = df[[c for c in cols if c in df.columns]]
    if use.empty:
        return "_(empty)_\n"
    headers = list(use.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in use.iterrows():
        cells = []
        for h in headers:
            v = row[h]
            if isinstance(v, float):
                cells.append(f"{v:.4f}" if abs(v) < 10 else f"{v:.2f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_report() -> Path:
    summary = pd.read_csv(RESULTS / "step9_summary.csv")
    verdict = json.loads((RESULTS / "step9_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step9_audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    a = lines.append

    a("# Step 9 — Executable hypothesis test")
    a("")
    a("**Status:** Complete (single frozen trade test).")
    a("**Scope:** One hypothesis. No optimization. No extra filters.")
    a("")
    a("## Research question")
    a("")
    a(
        "Can the observed low-transition-ER ExpExit destination asymmetry be converted "
        "into positive net expectancy under a simple, fixed entry/exit rule and "
        f"realistic NQ costs ({COST_RT} pt RT)?"
    )
    a("")
    a("## Frozen hypothesis H1")
    a("")
    a(verdict.get("hypothesis", ""))
    a("")
    a(
        f"- Primary arm: **D only** (promotion gate)."
    )
    a(
        f"- Control arm: **C** with the identical fade-to-mid / {HOLD_MINUTES}m rule "
        "(diagnostic only)."
    )
    a("- Population: frozen Step 7 low-ER ExpExit event ids.")
    a("")
    a("## Leakage / freeze audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"EVENT_POPULATION_FROZEN = {audit.get('EVENT_POPULATION_FROZEN')}")
    a(f"ENTRY_NEXT_OPEN_AFTER_TE = {audit.get('ENTRY_NEXT_OPEN_AFTER_TE')}")
    a(f"PARAMETER_OPTIMIZATION = {audit.get('PARAMETER_OPTIMIZATION')}")
    a(f"EXTRA_FILTERS = {audit.get('EXTRA_FILTERS')}")
    a(f"COST_RT = {audit.get('COST_RT')}")
    a(f"HOLD_MINUTES = {audit.get('HOLD_MINUTES')}")
    a("```")
    a("")
    a("## Results — primary D arm")
    a("")
    prim = summary.loc[summary["arm"] == "PRIMARY_D"]
    a(
        _md_table(
            prim,
            [
                "split",
                "n_trades",
                "n_long",
                "n_short",
                "mean_gross",
                "mean_net",
                "median_net",
                "hit_rate_net_gt_0",
                "eligible_gate",
            ],
        )
    )
    a("")
    a("## Results — control C arm (not used for promotion)")
    a("")
    ctrl = summary.loc[summary["arm"] == "CONTROL_C"]
    a(
        _md_table(
            ctrl,
            [
                "split",
                "n_trades",
                "mean_gross",
                "mean_net",
                "median_net",
                "hit_rate_net_gt_0",
            ],
        )
    )
    a("")
    a("## Gate detail")
    a("")
    for sp, d in (verdict.get("primary_gate") or {}).items():
        a(
            f"- **{sp}:** n={d.get('n_trades')}, E_net={d.get('mean_net')}, "
            f"eligible={d.get('eligible')}, pass={d.get('pass')}"
        )
    a("")
    a("## STEP 9 VERDICT")
    a("")
    a(f"**Classification:** `{verdict.get('classification')}`")
    a("")
    a(f"**Decision:** `{verdict.get('decision')}`")
    a("")
    a(verdict.get("research_question_answer", ""))
    a("")
    if verdict.get("classification") == "KILL":
        a(
            "Mechanism interest does not override this gate. "
            "**Stop. Do not build a strategy** from this hypothesis."
        )
    else:
        a(
            "Only now is a separate prop-risk / serious OOS evaluation justified. "
            "Do not add filters to rescue other variants."
        )
    a("")

    out = STRAT / "STEP9_EXECUTABLE_HYPOTHESIS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
