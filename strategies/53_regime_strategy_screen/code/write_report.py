"""Write results/REGIME_STRATEGY_SCREEN.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import COST_RT, HOLD_MINUTES, RESULTS


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
                cells.append(f"{v:.4f}" if abs(v) < 100 else f"{v:.2f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_report() -> Path:
    summary = pd.read_csv(RESULTS / "summary_by_split.csv")
    yearly = pd.read_csv(RESULTS / "summary_by_year.csv")
    baselines = pd.read_csv(RESULTS / "baselines.csv")
    pathm = pd.read_csv(RESULTS / "path_metrics.csv")
    verdict = json.loads((RESULTS / "verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    a = lines.append

    a("# Regime-Conditioned Strategy Family Screen")
    a("")
    a("**Strategy 53.** Screening study only. Market state is a routing variable.")
    a("")
    a("## 1. Objective")
    a("")
    a(
        "Determine whether simple strategy families show positive path/expectancy "
        "**when applied only inside** the frozen Strategy 52 market condition where "
        "their mechanism should plausibly operate."
    )
    a("")
    a("## 2. Frozen state definitions")
    a("")
    a(
        "Independent Strategy 52 flags (IS-frozen terciles; not re-fit): "
        "`flag_trending`, `flag_chop`, `flag_compression`, `flag_expansion` "
        "from `strategies/52_market_state_census/`."
    )
    a("")
    a("## 3. Four regime → strategy mappings")
    a("")
    a("| Cell | State | Family |")
    a("| --- | --- | --- |")
    a("| A | TRENDING | continuation |")
    a("| B | CHOP_RANGE (flag_chop) | mean reversion |")
    a("| C | COMPRESSION | breakout |")
    a("| D | EXPANSION | exhaustion / reversal |")
    a("")
    a("## 4–6. Signal and execution definitions")
    a("")
    a(
        f"As frozen in `PREREGISTRATION.md`. Common: entry `open[t+1]`, "
        f"exit `close[t+{HOLD_MINUTES}]`, cost **{COST_RT}** pt RT, no SL/TP."
    )
    a("")
    a("## 7. Cost assumption")
    a("")
    a(f"**{COST_RT} NQ point** round-trip (mid). Gross and net both reported.")
    a("")
    a("## 8. IS / Validation / OOS results")
    a("")
    a(
        _md_table(
            summary[summary["split"].isin(["IS", "Validation", "OOS"])],
            [
                "cell_id",
                "state_label",
                "family",
                "split",
                "n_trades",
                "signals_per_year",
                "mean_gross",
                "mean_net",
                "median_net",
                "win_rate",
                "profit_factor",
                "median_mfe_15",
                "median_mae_15",
            ],
        )
    )
    a("")
    a("## 9. Year-by-year results")
    a("")
    a(_md_table(yearly, ["cell_id", "session_year", "n_trades", "mean_net", "sum_net", "win_rate"]))
    a("")
    a("## 10. Baseline comparison")
    a("")
    a(
        _md_table(
            baselines[baselines["split"].isin(["IS", "Validation", "OOS"])],
            ["baseline", "cell_id", "split", "n_trades", "mean_net", "mean_gross"],
        )
    )
    a("")
    a("## 11. MFE / MAE path analysis")
    a("")
    a(_md_table(pathm, ["cell_id", "split", "n", "median_mfe_5", "median_mfe_15", "median_mae_5", "median_mae_15"]))
    a("")
    a("## 12. Leakage audit")
    a("")
    a("```text")
    for k in (
        "LOOKAHEAD_CHECK",
        "STATE_AT_T_ONLY",
        "SIGNAL_AT_T_ONLY",
        "ENTRY_OPEN_T_PLUS_1",
        "NO_SAME_BAR_EXECUTION",
        "NO_FUTURE_STATE",
        "NO_OUTCOME_FILTERING",
        "NO_PARAMETER_FIT_ON_VAL_OOS",
        "PARAMETER_OPTIMIZATION",
    ):
        a(f"{k} = {audit.get(k)}")
    a("```")
    a("")
    a("## 13. Multiple-testing statement")
    a("")
    a(
        "Exactly **four** primary hypotheses were preregistered. No additional variants, "
        "lookbacks, horizons, thresholds, or filters were added after seeing results."
    )
    a("")
    a("## 14. Independent classification of each cell")
    a("")
    for cid in ("A", "B", "C", "D"):
        v = verdict["cells"].get(cid, {})
        a(
            f"- **{cid} ({v.get('state_label')} → {v.get('family')}):** "
            f"`{v.get('classification')}`"
        )
        for sp, d in (v.get("detail") or {}).items():
            a(
                f"  - {sp}: n={d.get('n_trades')}, E_net={d.get('mean_net')}, "
                f"pass={d.get('pass')}"
            )
    a("")
    a(
        "A REJECTED or PATH-ONLY cell does **not** invalidate the market condition — "
        "only this representative rule inside that condition."
    )
    a("")
    a("## 15. Recommended next research direction")
    a("")
    promising = [
        v for v in verdict["cells"].values() if v.get("classification") == "PROMISING"
    ]
    path_only = [
        v for v in verdict["cells"].values() if v.get("classification") == "PATH-ONLY"
    ]
    if promising:
        a(
            "Deeper research is justified **only** for PROMISING cell(s): "
            + ", ".join(f"{v['cell_id']} ({v['state_label']}/{v['family']})" for v in promising)
            + ". Still one family at a time; no kitchen-sink filters."
        )
    elif path_only:
        a(
            "No PROMISING expectancy cells. PATH-ONLY cell(s) "
            + ", ".join(v["cell_id"] for v in path_only)
            + " may justify a **separate**, preregistered exit/path study — not silent retuning here."
        )
    else:
        a(
            "No cell cleared PROMISING. Do **not** deepen Strategy 52 mechanics to rescue these "
            "representatives. Consider a different research question or accept that these "
            "simple regime→family mappings lack evidence under the frozen screen."
        )
    a("")
    a("## Final research question")
    a("")
    a(
        "> Does routing simple, mechanically representative strategy families into the "
        "market conditions for which they are theoretically appropriate produce enough "
        "evidence to justify deeper research?"
    )
    a("")
    if promising:
        a(f"**Answer:** Yes, for {len(promising)} cell(s) classified PROMISING.")
    else:
        a(
            "**Answer:** Not under this frozen four-cell screen — no PROMISING cell. "
            "State remains useful as a map; these representative rules do not graduate."
        )
    a("")

    out = RESULTS / "REGIME_STRATEGY_SCREEN.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
