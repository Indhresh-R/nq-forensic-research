"""Write STEP1_PATH_GEOMETRY.md from frozen Step 1 artifacts."""
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
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D, HORIZONS


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
                if abs(v) >= 100:
                    cells.append(f"{v:.2f}")
                elif abs(v) >= 1:
                    cells.append(f"{v:.3f}")
                else:
                    cells.append(f"{v:.4f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _fmt_pct(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "n/a"
    return f"{100.0 * float(x):.1f}%"


def _fmt_num(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "n/a"
    return f"{float(x):.3f}"


def write_report() -> Path:
    meta = json.loads((RESULTS / "step1_episode_meta.json").read_text(encoding="utf-8"))
    contrasts = json.loads((RESULTS / "step1_contrasts.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step1_audit.json").read_text(encoding="utf-8"))
    key = pd.read_csv(RESULTS / "step1_key_table.csv")
    episodes = pd.read_parquet(RESULTS / "step1_episodes.parquet")

    ep_counts = (
        episodes.groupby("cell").size().reindex([CELL_A, CELL_B, CELL_C, CELL_D]).fillna(0).astype(int)
    )

    lines: list[str] = []
    a = lines.append

    a("# Step 1 — State-transition / path-geometry mechanics")
    a("")
    a("**Status:** Complete (mechanism description only).")
    a("**Parent:** Strategy 52 Step 0 census labels (frozen).")
    a("**Forbidden here:** entries, exits, stops, targets, signed trade P&L, optimization.")
    a("")
    a("---")
    a("")
    a("## Question")
    a("")
    a("What path geometry tends to follow each of four observable state combinations?")
    a("")
    a("| Cell | Definition |")
    a("| --- | --- |")
    a("| **A** | Compression + Low directionality |")
    a("| **B** | Compression + Mid/High directionality |")
    a("| **C** | Expansion + High directionality |")
    a("| **D** | Expansion + Low directionality |")
    a("")
    a("Event unit: **episode onset** within a session (not every minute).")
    a("Horizons: 5 / 15 / 30 / 60 minutes of **subsequent** bars only.")
    a("")
    a("---")
    a("")
    a("## Sample")
    a("")
    a(f"| Item | Value |")
    a(f"| --- | --- |")
    a(f"| Eligible RTH bars | {meta.get('n_eligible_bars')} |")
    a(f"| Bars in four cells | {meta.get('n_bars_in_four_cells')} |")
    a(f"| Residual bars (e.g. expansion+mid) | {meta.get('n_bars_residual')} |")
    a(f"| Episodes total | {meta.get('n_episodes')} |")
    for cell, n in ep_counts.items():
        a(f"| Episodes {cell} | {n} |")
    a("")
    a("---")
    a("")
    a("## Key path table (valid horizons)")
    a("")
    a("Rates are proportions of valid episodes. Magnitudes are ATR-normalized medians at onset.")
    a("")

    show_cols = [
        "cell",
        "horizon",
        "n_valid",
        "rate_still_compressed",
        "rate_reached_normal",
        "rate_reached_expansion",
        "rate_still_expanded",
        "rate_left_expansion",
        "abs_net_atr_median",
        "max_range_atr_median",
        "er_forward_median",
        "max_up_atr_median",
        "max_down_atr_median",
        "time_to_leave_compression_median",
        "time_to_expansion_median",
        "time_to_leave_expansion_median",
        "expansion_is_directional_mean",
        "expansion_is_two_sided_mean",
    ]
    a(_md_table(key, show_cols))
    a("")
    a("Full detail: `results/step1_cell_summary.csv`, `results/step1_cell_summary_by_split.csv`.")
    a("")
    a("---")
    a("")
    a("## Primary contrasts")
    a("")

    for h in (15, 30, 60):
        block = contrasts.get("by_horizon", {}).get(str(h), {})
        ab = block.get("A_vs_B") or {}
        cd = block.get("C_vs_D") or {}
        a(f"### Horizon = {h} minutes")
        a("")
        if ab:
            d = ab.get("deltas_b_minus_a") or {}
            a(f"**A vs B (compression)** — n_A={ab.get('n_a')}, n_B={ab.get('n_b')}. "
              f"Deltas are B − A.")
            a("")
            a("| Metric | A | B | B−A |")
            a("| --- | ---: | ---: | ---: |")
            for name, key_m, fmt in (
                ("P(reached expansion)", "rate_reached_expansion", "pct"),
                ("P(reached normal)", "rate_reached_normal", "pct"),
                ("P(still compressed)", "rate_still_compressed", "pct"),
                ("median abs_net / ATR", "abs_net_atr_median", "num"),
                ("median max_range / ATR", "max_range_atr_median", "num"),
                ("median forward ER", "er_forward_median", "num"),
                ("median max_up / ATR", "max_up_atr_median", "num"),
                ("median max_down / ATR", "max_down_atr_median", "num"),
            ):
                va = (ab.get("a") or {}).get(key_m)
                vb = (ab.get("b") or {}).get(key_m)
                dd = d.get(key_m)
                if fmt == "pct":
                    delta_s = f"{(100 * dd):+.1f} pp" if dd is not None else "n/a"
                    a(f"| {name} | {_fmt_pct(va)} | {_fmt_pct(vb)} | {delta_s} |")
                else:
                    delta_s = f"{dd:+.3f}" if dd is not None else "n/a"
                    a(f"| {name} | {_fmt_num(va)} | {_fmt_num(vb)} | {delta_s} |")
            a("")

        if cd:
            d = cd.get("deltas_b_minus_a") or {}
            a(f"**C vs D (expansion)** — n_C={cd.get('n_a')}, n_D={cd.get('n_b')}. "
              f"Deltas are D − C.")
            a("")
            a("| Metric | C | D | D−C |")
            a("| --- | ---: | ---: | ---: |")
            for name, key_m, fmt in (
                ("P(still expanded)", "rate_still_expanded", "pct"),
                ("P(left expansion)", "rate_left_expansion", "pct"),
                ("median abs_net / ATR", "abs_net_atr_median", "num"),
                ("median max_range / ATR", "max_range_atr_median", "num"),
                ("median forward ER", "er_forward_median", "num"),
                ("median max_up / ATR", "max_up_atr_median", "num"),
                ("median max_down / ATR", "max_down_atr_median", "num"),
            ):
                va = (cd.get("a") or {}).get(key_m)
                vb = (cd.get("b") or {}).get(key_m)
                dd = d.get(key_m)
                if fmt == "pct":
                    if dd is not None:
                        a(f"| {name} | {_fmt_pct(va)} | {_fmt_pct(vb)} | {(100*dd):+.1f} pp |")
                    else:
                        a(f"| {name} | {_fmt_pct(va)} | {_fmt_pct(vb)} | n/a |")
                else:
                    if dd is not None:
                        a(f"| {name} | {_fmt_num(va)} | {_fmt_num(vb)} | {dd:+.3f} |")
                    else:
                        a(f"| {name} | {_fmt_num(va)} | {_fmt_num(vb)} | n/a |")
            a("")

    a("---")
    a("")
    a("## Leakage / scope audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"FUTURE_DATA_USED_IN_STATE_LABEL = {audit.get('FUTURE_DATA_USED_IN_STATE_LABEL')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a(f"FORWARD_PATH_USED = {audit.get('FORWARD_PATH_USED')}")
    a("```")
    a("")
    a(audit.get("FORWARD_PATH_NOTE", ""))
    a("")
    a("---")
    a("")
    a("## STEP 1 VERDICT")
    a("")
    a("- **Architecture:** four-cell state → subsequent path geometry is measurable at "
      "episode scale without constructing trades.")
    a("- **A vs B (compression):** over 15–60m, ATR-scaled move/range realization and "
      "forward ER are **largely similar**. B leaves compression slightly faster and is "
      "somewhat more likely to reach expansion by H=30 (~28% vs ~25%). Differences are "
      "modest — not a license to trade “directional compression.”")
    a("- **C vs D (expansion):** persistence of expansion and ATR-scaled path envelopes "
      "are also **similar**. The clear descriptive split is directional *character* at/after "
      "onset (high-dir vs low-dir expansion), which is partly built into the cell definition "
      "and should not be mistaken for an edge.")
    a("- **Compression path structure:** among compression onsets, reaching NORMAL is far "
      "more common than reaching EXPANSION at short horizons (e.g. H=15: ~45–49% reach "
      "normal vs ~8–11% reach expansion), consistent with Step 0’s finding that "
      "compression→expansion is usually indirect.")
    a("- **Sample sizes are adequate** for these descriptive contrasts (tens of thousands "
      "of episodes per cell).")
    a("- **Not done here:** no long/short rule; no claim that any cell is tradeable.")
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    a("Given that **magnitude path geometry is similar within compression (A vs B) and "
      "within expansion (C vs D)**, does a more specific **event** — e.g. the first "
      "COMPRESSION→NORMAL transition, or the first return to NORMAL from EXPANSION — "
      "produce distinguishable subsequent path geometry conditional on whether the "
      "pre-transition cell was A vs B (or C vs D)? Still mechanism-only; still no trade.")
    a("")
    a("_Do not answer that question by building a strategy in this step._")
    a("")

    out = STRAT / "STEP1_PATH_GEOMETRY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    p = write_report()
    print(f"Wrote {p}")
