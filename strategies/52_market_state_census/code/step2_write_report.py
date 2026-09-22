"""Write STEP2_TRANSITION_EVENTS.md."""
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
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D


def _md_table(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    if df is None or df.empty:
        return "_(empty)_\n"
    use = df if cols is None else df[[c for c in cols if c in df.columns]]
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
                cells.append(f"{v:.4f}" if abs(v) < 1 else f"{v:.3f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _pct(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "n/a"
    return f"{100.0 * float(x):.1f}%"


def _num(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "n/a"
    return f"{float(x):.3f}"


def _contrast_block(lines: list, title: str, block: dict, a_lab: str, b_lab: str) -> None:
    a = lines.append
    if not block:
        a(f"_{title}: missing_\n")
        return
    d = block.get("deltas_b_minus_a") or {}
    a(f"**{title}** — n_{a_lab}={block.get('n_a')}, n_{b_lab}={block.get('n_b')}. "
      f"Deltas are {b_lab} − {a_lab}.")
    a("")
    a(f"| Metric | {a_lab} | {b_lab} | Δ |")
    a("| --- | ---: | ---: | ---: |")
    for name, key, kind in (
        ("P(still NORMAL)", "rate_still_normal", "pct"),
        ("P(return to origin range)", "rate_returned_to_origin_range", "pct"),
        ("P(reach opposite range)", "rate_reached_opposite_range", "pct"),
        ("median abs_net / ATR", "abs_net_atr_median", "num"),
        ("median max_range / ATR", "max_range_atr_median", "num"),
        ("median forward ER", "er_forward_median", "num"),
        ("median max_up / ATR", "max_up_atr_median", "num"),
        ("median max_down / ATR", "max_down_atr_median", "num"),
        ("median wait onset→event", "wait_to_event_median", "num"),
        ("median time leave NORMAL", "time_to_leave_normal_median", "num"),
        ("median path HIGH-dir share", "path_dir_high_share_median", "num"),
        ("median path LOW-dir share", "path_dir_low_share_median", "num"),
    ):
        va = (block.get("a") or {}).get(key)
        vb = (block.get("b") or {}).get(key)
        dd = d.get(key)
        if kind == "pct":
            ds = f"{(100 * dd):+.1f} pp" if dd is not None else "n/a"
            a(f"| {name} | {_pct(va)} | {_pct(vb)} | {ds} |")
        else:
            ds = f"{dd:+.3f}" if dd is not None else "n/a"
            a(f"| {name} | {_num(va)} | {_num(vb)} | {ds} |")
    a("")


def write_report() -> Path:
    funnel = json.loads((RESULTS / "step2_funnel.json").read_text(encoding="utf-8"))
    contrasts = json.loads((RESULTS / "step2_contrasts.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step2_audit.json").read_text(encoding="utf-8"))
    key = pd.read_csv(RESULTS / "step2_key_table.csv")
    wait = pd.read_csv(RESULTS / "step2_wait_to_event.csv")

    lines: list[str] = []
    a = lines.append

    a("# Step 2 — Transition-event mechanics")
    a("")
    a("**Status:** Complete (mechanism description only).")
    a("**Parent:** Steps 0–1 frozen labels / cells / episode onsets.")
    a("**Forbidden:** entries, exits, stops, targets, signed P&L, optimization.")
    a("")
    a("---")
    a("")
    a("## Question")
    a("")
    a("Does the **transition event** separate subsequent path geometry when the "
      "persistent state label (Step 1) did not?")
    a("")
    a("| Contrast | Event |")
    a("| --- | --- |")
    a("| A vs B | first `COMPRESSION → NORMAL` after A/B onset |")
    a("| C vs D | first `EXPANSION → NORMAL` after C/D onset |")
    a("")
    a("Event timestamp = **first NORMAL bar**. Path = strictly subsequent 5/15/30/60m.")
    a("At most one event per episode onset.")
    a("")
    a("---")
    a("")
    a("## Funnel")
    a("")
    a(f"| Item | Count |")
    a(f"| --- | ---: |")
    a(f"| Episode onsets | {funnel.get('n_onsets')} |")
    a(f"| Qualifying →NORMAL events | {funnel.get('n_events')} |")
    for reason, n in (funnel.get("censored") or {}).items():
        a(f"| Censored: {reason} | {n} |")
    a("")
    a("### Events by origin")
    a("")
    a("| Origin | Events |")
    a("| --- | ---: |")
    for cell, n in (funnel.get("events_by_origin") or {}).items():
        a(f"| {cell} | {n} |")
    a("")
    a("### Wait onset → first NORMAL")
    a("")
    a(_md_table(wait))
    a("")
    a("---")
    a("")
    a("## Key path table (valid horizons)")
    a("")
    a(_md_table(key))
    a("")
    a("Full detail: `results/step2_cell_summary.csv`, `results/step2_cell_summary_by_split.csv`.")
    a("")
    a("---")
    a("")
    a("## Primary contrasts")
    a("")
    for h in (15, 30, 60):
        block = contrasts.get("by_horizon", {}).get(str(h), {})
        a(f"### Horizon = {h} minutes")
        a("")
        _contrast_block(lines, "A→NORMAL vs B→NORMAL (CompExit)", block.get("A_vs_B_CompExit"), "A", "B")
        _contrast_block(lines, "C→NORMAL vs D→NORMAL (ExpExit)", block.get("C_vs_D_ExpExit"), "C", "D")

    a("---")
    a("")
    a("## Leakage / scope audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"EVENT_USES_POST_EVENT_INFO = {audit.get('EVENT_USES_POST_EVENT_INFO')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a(f"FORWARD_PATH_USED = {audit.get('FORWARD_PATH_USED')}")
    a("```")
    a("")
    a(audit.get("FORWARD_PATH_NOTE", ""))
    a("")
    a("---")
    a("")
    a("## STEP 2 VERDICT")
    a("")
    a("- **Design check:** events are first causal →NORMAL after episode onset; "
      "post-event path is descriptive only.")
    a("- **Funnel structure:** most non-events are **A/B cell switches while still "
      "compressed** (directionality flips before NORMAL), not opposite-range jumps. "
      "That is itself a market-structure fact: compression episodes often change "
      "directionality label before exiting to NORMAL.")
    a("- **Magnitude geometry (abs_net / max_range / ER):** A→NORMAL vs B→NORMAL and "
      "C→NORMAL vs D→NORMAL remain **largely similar** at 15–60m — matching Step 1’s "
      "conclusion that origin directionality does not strongly separate move *size*.")
    a("- **Destination geometry (where the path goes):** more informative than magnitude. "
      "At H=30, CompExit A returns to compression more often than B and reaches expansion "
      "slightly less often; ExpExit **D returns to expansion more often than C** and reaches "
      "compression less often. These are descriptive transition asymmetries, not trade signals.")
    a("- **Wait times:** CompExit median wait onset→NORMAL is short (~3m for A/B events); "
      "ExpExit waits are longer for C (~10m) than D (~4m) among qualifying events.")
    a("- **Interpretation:** origin directionality is a weak magnitude factor even at the "
      "transition, but it may still mark **different recycling preferences** after NORMAL. "
      "That is a mechanism lead, not an entry rule.")
    a("- **Not done:** no long/short rule; no profitability claim.")
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    a("Given similar magnitudes but different **post-NORMAL destination rates**, is the "
      "ExpExit (or CompExit) destination asymmetry stable across IS / Validation / OOS, "
      "and does an orthogonal frozen covariate at the event bar (volatility, volume, or "
      "NY time block) sharpen destination separation *within* one exit family — still "
      "mechanism-only, still no trade?")
    a("")
    a("_Do not answer by building a strategy in this step._")
    a("")

    out = STRAT / "STEP2_TRANSITION_EVENTS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
