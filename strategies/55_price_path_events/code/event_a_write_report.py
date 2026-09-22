"""Write EVENT_A_REPORT.md."""
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
    summary = pd.read_csv(RESULTS / "event_a_destinations.csv")
    funnel = json.loads((RESULTS / "event_a_funnel.json").read_text(encoding="utf-8"))
    verdict = json.loads(
        (RESULTS / "event_a_step1_2_verdict.json").read_text(encoding="utf-8")
    )
    audit = json.loads((RESULTS / "event_a_audit.json").read_text(encoding="utf-8"))
    feas = pd.read_csv(RESULTS / "event_a_path_feasibility.csv")

    lines: list[str] = []
    a = lines.append

    a("# Event A Report — Displacement → Retracement")
    a("")
    a("**Family 1 only.** Frozen definitions. No retuning.")
    a("")
    a("## Funnel")
    a("")
    a(f"- Onset displacements: {funnel.get('n_onset_displacements')}")
    a(f"- Events (retracement confirmed): {funnel.get('n_events')}")
    a(f"- Censored (no retrace / event not eligible): {funnel.get('n_censored_no_retrace')}")
    a("")
    a("## Leakage / freeze audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"EVENT_DEFINITION_FROZEN = {audit.get('EVENT_DEFINITION_FROZEN')}")
    a(f"NO_PARAMETER_RETUNE = {audit.get('NO_PARAMETER_RETUNE')}")
    a(f"COST_RT = {audit.get('COST_RT')}")
    a("```")
    a("")
    a("## Destination asymmetry")
    a("")
    a(_md_table(
        summary,
        [
            "horizon",
            "split",
            "n_valid",
            "p_origin",
            "p_impulse_end",
            "p_extension",
            "delta_ext_minus_origin",
        ],
    ))
    a("")
    a(f"Primary contrast Δ = P(extension) − P(origin) at {PRIMARY_H}m.")
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
                f"P(origin)={d.get('p_origin')}, P(extension)={d.get('p_extension')}, "
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
        tsum_path = RESULTS / "event_a_trade_summary.csv"
        if tsum_path.exists():
            tsum = pd.read_csv(tsum_path)
            a(_md_table(
                tsum,
                ["split", "n_trades", "mean_gross", "mean_net", "median_net", "hit_rate", "eligible"],
            ))
        a("")
        a(f"**Trade classification:** `{trade.get('classification')}`")
        a("")
    else:
        a("## Trade test")
        a("")
        a("_Not run — Event A did not ADVANCE from Steps 1–2._")
        a("")

    a("## EVENT A FINAL")
    a("")
    final = verdict.get("final")
    if final == "ADVANCE":
        a("**ADVANCE** — destination asymmetry stable and trade gate passed.")
    else:
        a(
            f"**KILL** (`{final}`). Do not retune W / 1.5 / 0.5 / H_wait. "
            "Do not switch to Family 2–4 in this run. "
            "Do not add filters."
        )
    a("")

    out = RESULTS / "EVENT_A_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    # also copy convenience path at strategy root
    (STRAT / "EVENT_A_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
