"""Write EVENT_B_REPORT.md."""
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

from constants import COST_RT, PRIMARY_H, RESULTS


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


def _pp(x) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{100 * float(x):+.1f} pp"


def write_report() -> Path:
    summary = pd.read_csv(RESULTS / "event_b_destinations.csv")
    funnel = json.loads((RESULTS / "event_b_funnel.json").read_text(encoding="utf-8"))
    verdict = json.loads((RESULTS / "event_b_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "event_b_audit.json").read_text(encoding="utf-8"))
    feas = pd.read_csv(RESULTS / "event_b_path_feasibility.csv")

    lines: list[str] = []
    a = lines.append
    a("# Event B Report — Range Break → Failed Return")
    a("")
    a("**Family 2 only.** Frozen definitions. No retuning. Not Event A.")
    a("")
    a("## Funnel")
    a("")
    a(f"- Break onsets: {funnel.get('n_break_onsets')} (up={funnel.get('n_up')}, down={funnel.get('n_down')})")
    a(f"- Events (failed return): {funnel.get('n_events')}")
    a(f"- Censored: {funnel.get('n_censored_no_return')}")
    a("")
    a("## Leakage / freeze audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"EVENT_DEFINITION_FROZEN = {audit.get('EVENT_DEFINITION_FROZEN')}")
    a(f"NO_PARAMETER_RETUNE = {audit.get('NO_PARAMETER_RETUNE')}")
    a(f"NO_EVENT_A_COMBINE = {audit.get('NO_EVENT_A_COMBINE')}")
    a(f"COST_RT = {audit.get('COST_RT')}")
    a("```")
    a("")
    a("## Destination asymmetry")
    a("")
    a(
        _md_table(
            summary,
            [
                "horizon",
                "split",
                "n_valid",
                "p_opposite",
                "p_mid",
                "p_rebreak",
                "delta_opp_minus_rebreak",
            ],
        )
    )
    a("")
    a(f"Primary Δ = P(opposite) − P(rebreak) at {PRIMARY_H}m.")
    a("")
    a("## Step 1 / 2 verdict")
    a("")
    a(f"- **Classification:** `{verdict.get('classification')}`")
    a(f"- **Stage:** `{verdict.get('stage')}`")
    a(f"- **Reason:** `{verdict.get('reason')}`")
    a(f"- **Final:** `{verdict.get('final')}`")
    a("")
    for sp, d in (verdict.get("detail") or {}).items():
        if isinstance(d, dict) and "delta" in d:
            a(
                f"- {sp}: n={d.get('n_valid')}, "
                f"P(opp)={d.get('p_opposite')}, P(rebreak)={d.get('p_rebreak')}, "
                f"Δ={_pp(d.get('delta'))}"
            )
    a("")
    a("## Path feasibility (descriptive)")
    a("")
    a(_md_table(feas, ["horizon", "n", "median_hl_range", "p25", "p75", "cost_rt"]))
    a("")
    trade = verdict.get("trade")
    if trade:
        a("## Trade test")
        a("")
        a(f"Side rule: `{verdict.get('trade_side_rule')}` (from IS sign of Δ).")
        a(f"Entry open[t+1], exit close[t+15], cost {COST_RT} pt RT.")
        a("")
        tsum_path = RESULTS / "event_b_trade_summary.csv"
        if tsum_path.exists():
            tsum = pd.read_csv(tsum_path)
            a(
                _md_table(
                    tsum,
                    [
                        "split",
                        "n_trades",
                        "mean_gross",
                        "mean_net",
                        "median_net",
                        "hit_rate",
                        "eligible",
                    ],
                )
            )
        a("")
        a(f"**Trade classification:** `{trade.get('classification')}`")
        a("")
    else:
        a("## Trade test")
        a("")
        a("_Not run — Event B did not ADVANCE from Steps 1–2._")
        a("")
    a("## EVENT B FINAL")
    a("")
    final = verdict.get("final")
    if final == "ADVANCE":
        a("**ADVANCE** — destination asymmetry stable and trade gate passed.")
    else:
        a(
            f"**KILL** (`{final}`). Do not retune W / H_wait / 0.25R. "
            "Do not fix Event A. Do not start Family 3/4 in this run."
        )
    a("")
    out = RESULTS / "EVENT_B_REPORT.md"
    text = "\n".join(lines)
    out.write_text(text, encoding="utf-8")
    (STRAT / "EVENT_B_REPORT.md").write_text(text, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
