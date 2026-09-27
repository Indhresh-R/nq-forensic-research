"""Write STEP8_PATH_FEASIBILITY.md."""
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
from step1_constants import CELL_C, CELL_D
from step8_analyze import COST_MID_RT


def _md_table(df: pd.DataFrame, cols: list[str]) -> str:
    use = df[[c for c in cols if c in df.columns]].copy()
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
                if abs(v) < 1:
                    cells.append(f"{v:.4f}")
                else:
                    cells.append(f"{v:.2f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _pp(x) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{100 * float(x):+.1f} pp"


def _horizon_section(a, table: pd.DataFrame, h: int) -> None:
    a(f"## {h}m path results")
    a("")
    dest = table.loc[
        (table["metric_family"] == "destination_contrast")
        & (table["horizon"] == h)
        & (table["split"] == "ALL")
    ]
    if len(dest):
        d = dest.iloc[0]
        a(
            f"Destination (valid n_c={int(d['n_c'])}, n_d={int(d['n_d'])}, "
            f"eligible={d['eligible']}):"
        )
        a("")
        a(
            f"- Return to origin: C={100 * d['return_rate_c']:.1f}%, "
            f"D={100 * d['return_rate_d']:.1f}%, D−C={_pp(d['return_diff'])}"
        )
        a(
            f"- Reach opposite: C={100 * d['opposite_rate_c']:.1f}%, "
            f"D={100 * d['opposite_rate_d']:.1f}%, D−C={_pp(d['opposite_diff'])}"
        )
        a("")
    exc = table.loc[
        (table["metric_family"] == "excursion")
        & (table["horizon"] == h)
        & (table["origin_cell"].isin(["POOLED", CELL_C, CELL_D]))
    ]
    a("Raw excursion (NQ points; no trade side):")
    a("")
    a(
        _md_table(
            exc,
            [
                "origin_cell",
                "feature",
                "n",
                "mean",
                "p25",
                "p50",
                "p75",
                "p90",
                "frac_gt_5",
                "frac_gt_10",
            ],
        )
    )
    a("")


def write_report() -> Path:
    table = pd.read_csv(RESULTS / "step8_path_feasibility.csv")
    verdict = json.loads((RESULTS / "step8_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step8_audit.json").read_text(encoding="utf-8"))
    pop_check = json.loads(
        (RESULTS / "step8_population_check.json").read_text(encoding="utf-8")
    )
    detail = verdict.get("detail") or {}
    ref = detail.get("reference_30") or {}

    lines: list[str] = []
    a = lines.append

    a("# Step 8 — Path Feasibility Audit")
    a("")
    a("**Status:** Complete (path-feasibility audit).")
    a("**Scope:** Frozen low-transition-ER ExpExit C vs D. No trade. No optimization.")
    a("")
    a("## 1. Objective")
    a("")
    a(
        "Does the already-observed low-transition-ER ExpExit C/D destination asymmetry "
        "occur early enough and with sufficient raw price excursion to potentially "
        "support a simple executable hypothesis?"
    )
    a("")
    a("This step does **not** construct, optimize, or validate a strategy.")
    a("")
    a("## 2. Frozen population")
    a("")
    a(
        f"Step 7 population reused exactly: n={pop_check.get('n')} "
        f"(C={pop_check.get('n_c')}, D={pop_check.get('n_d')}). "
        f"Expected ≈ {pop_check.get('expected_n')} "
        f"(C≈{pop_check.get('expected_c')}, D≈{pop_check.get('expected_d')}). "
        f"Match OK={pop_check.get('ok')}."
    )
    a("")
    a("Low-ER cut remains the frozen Step 6 IS `te_er_60` q33. No redefinition of C/D.")
    a("")
    a("## 3. Leakage audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"EVENT_POPULATION_FROZEN = {audit.get('EVENT_POPULATION_FROZEN')}")
    a(f"FORWARD_PATH_STRICTLY_AFTER_TE = {audit.get('FORWARD_PATH_STRICTLY_AFTER_TE')}")
    a(f"OUTCOME_USED_FOR_SELECTION = {audit.get('OUTCOME_USED_FOR_SELECTION')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a(f"PARAMETER_OPTIMIZATION = {audit.get('PARAMETER_OPTIMIZATION')}")
    a("```")
    a("")
    a("## 4. Sample counts")
    a("")
    a(
        f"Pooled valid paths inherit Step 2 session/segment continuity. "
        f"Reference 30m destination: D−C return {_pp(ref.get('return_diff'))}, "
        f"opposite {_pp(ref.get('opposite_diff'))} "
        f"(n_c={ref.get('n_c')}, n_d={ref.get('n_d')})."
    )
    a("")

    for h in (5, 15, 30, 60):
        _horizon_section(a, table, h)

    a("## 9. Destination timing")
    a("")
    a("Among events that reach each destination within 60m (censored excluded from timing):")
    a("")
    tim = table.loc[table["metric_family"] == "timing"]
    a(
        _md_table(
            tim,
            [
                "origin_cell",
                "feature",
                "n_reached",
                "n_events",
                "frac_reached",
                "p25",
                "p50",
                "p75",
            ],
        )
    )
    a("")
    a("## 10. Competing-path analysis")
    a("")
    a("Which destination occurs first within 60m (path states only — not wins/losses):")
    a("")
    comp = table.loc[table["metric_family"] == "competing_path"]
    a(_md_table(comp, ["origin_cell", "feature", "n", "rate"]))
    a("")
    a("## 11. Raw NQ-point scale")
    a("")
    a(
        f"Event-time ATR (`atr_e`) distribution for scale context "
        f"(not an ATR-multiple trading rule):"
    )
    a("")
    atr = table.loc[table["metric_family"] == "atr_e"]
    a(_md_table(atr, ["origin_cell", "n", "mean", "p25", "p50", "p75", "p90"]))
    a("")
    a(
        f"Pooled median `hl_range`: 15m={detail.get('hl_range_p50_15')}, "
        f"30m={detail.get('hl_range_p50_30')} NQ points."
    )
    a(
        f"Pooled median time to first destination (among reached): "
        f"{detail.get('median_time_to_first_destination')} minutes."
    )
    a("")
    a("## 12. IS / Validation / OOS stability")
    a("")
    a("30m D−C destination contrasts by chronological split (same frozen population):")
    a("")
    stab = table.loc[
        (table["metric_family"] == "destination_contrast") & (table["horizon"] == 30)
    ].copy()
    stab["return"] = stab["return_diff"].map(_pp)
    stab["opposite"] = stab["opposite_diff"].map(_pp)
    a(_md_table(stab, ["split", "n_c", "n_d", "eligible", "return", "opposite"]))
    a("")
    a("## 13. Cost-scale context")
    a("")
    a(
        f"Project mid round-trip cost assumption: **{COST_MID_RT} NQ point** "
        f"(`research_framework/execution_assumptions.md`). "
        "Observed median post-event ranges at 15m/30m are compared to this scale "
        "**without** subtracting costs, computing P&L, or choosing stops/targets."
    )
    a("")
    a("## 14. Interpretation")
    a("")
    a(
        "Language remains destination / path-excursion / timing / feasibility. "
        "No continuation, reversal, long/short, expectancy, or profitability claims."
    )
    a("")
    a("Clause checklist (preregistered):")
    a("")
    a(f"- clause1_15 (assoc @15m): `{detail.get('clause1_15')}`")
    a(f"- clause1_30 (assoc @30m): `{detail.get('clause1_30')}`")
    a(f"- clause2 (median hl_range ≥ 5 @15 and @30): `{detail.get('clause2_hl_range')}`")
    a(
        f"- clause3 (median first destination ≤ 15m): "
        f"`{detail.get('clause3_median_first_dest')}`"
    )
    a(f"- clause4 (30m return D−C same sign IS/Val/OOS): `{detail.get('clause4_split_sign')}`")
    a("")
    a("## 15. Predeclared classification")
    a("")
    a(f"**Classification:** `{verdict.get('classification')}`")
    a("")
    a("## 16. Explicit stop/go decision")
    a("")
    a(f"**Decision:** `{verdict.get('decision')}`")
    a("")
    a(verdict.get("research_question_answer", ""))
    a("")
    if verdict.get("decision") == "GO_TO_STEP9":
        a(
            "A separate Step 9 may construct **one** simple, preregistered executable "
            "hypothesis. That hypothesis is **not** constructed in this step."
        )
    else:
        a("**STOP. Do not build a strategy.**")
    a("")

    out = STRAT / "STEP8_PATH_FEASIBILITY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
