"""Write MARKET_STATE_CENSUS.md from frozen descriptive artifacts."""
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


def _md_table(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    if df is None or df.empty:
        return "_(empty)_\n"
    use = df if cols is None else df[cols]
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
                cells.append(f"{v:.2f}" if abs(v) < 1000 else f"{v:.4g}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _load_csv(name: str) -> pd.DataFrame:
    p = RESULTS / name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _pct(df: pd.DataFrame, state_col: str, state: str) -> float | None:
    if df.empty or state_col not in df.columns:
        return None
    hit = df[df[state_col] == state]
    if hit.empty:
        return None
    return float(hit.iloc[0]["pct"])


def write_report() -> Path:
    feat_meta = json.loads((RESULTS / "feature_meta.json").read_text(encoding="utf-8"))
    thr = json.loads((RESULTS / "thresholds_frozen.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "audit_report.json").read_text(encoding="utf-8"))
    env = json.loads((RESULTS / "environment.json").read_text(encoding="utf-8"))
    cont = json.loads((RESULTS / "continuous_feature_summary.json").read_text(encoding="utf-8"))
    cxe = json.loads(
        (RESULTS / "compression_expansion_sequences.json").read_text(encoding="utf-8")
    )

    t1 = _load_csv("table1_composite_primary.csv")
    t1b = _load_csv("table1b_composite_flags.csv")
    t2 = _load_csv("table2_directionality.csv")
    t3 = _load_csv("table3_volatility.csv")
    t4 = _load_csv("table4_volume.csv")
    t5 = _load_csv("table5_range.csv")
    t6 = _load_csv("table6_time_of_day.csv")
    t7 = _load_csv("table7_year_stability.csv")
    t8 = _load_csv("table8_persistence.csv")
    t9 = _load_csv("table9_transitions.csv")
    dow = _load_csv("table_day_of_week.csv")
    overlap = _load_csv("overlap_key_combos.csv")

    # Pivot helpers for TOD / year directionality
    def _pivot_dir(src: pd.DataFrame, index: str) -> pd.DataFrame:
        sub = src[(src["dimension"] == "directionality")]
        if sub.empty:
            return pd.DataFrame()
        p = sub.pivot_table(index=index, columns="state", values="pct", aggfunc="first")
        return p.reset_index()

    tod_dir = _pivot_dir(t6, "block")
    year_dir = _pivot_dir(t7, "year")
    dow_dir = _pivot_dir(dow, "dow")

    # Persistence snapshot for composite + range
    pers_comp = t8[t8["dimension"] == "composite_primary"] if not t8.empty else t8
    pers_range = t8[t8["dimension"] == "range_state"] if not t8.empty else t8
    pers_dir = t8[t8["dimension"] == "directionality_state"] if not t8.empty else t8

    # Key transitions
    def _top_trans(dim: str, n: int = 12) -> pd.DataFrame:
        sub = t9[t9["dimension"] == dim].copy()
        if sub.empty:
            return sub
        # exclude self-transitions for "change" view, but also keep self rates
        return sub.sort_values("count", ascending=False).head(n)

    high_dir = _pct(t2, "state", "HIGH_DIRECTIONALITY")
    low_dir = _pct(t2, "state", "LOW_DIRECTIONALITY")
    mid_dir = _pct(t2, "state", "MID_DIRECTIONALITY")
    high_vol = _pct(t3, "state", "HIGH_VOLATILITY")
    mid_vol = _pct(t3, "state", "NORMAL_VOLATILITY")
    low_vol = _pct(t3, "state", "LOW_VOLATILITY")
    high_vlm = _pct(t4, "state", "HIGH_VOLUME")
    mid_vlm = _pct(t4, "state", "NORMAL_VOLUME")
    low_vlm = _pct(t4, "state", "LOW_VOLUME")
    comp = _pct(t5, "state", "COMPRESSION")
    mid_rng = _pct(t5, "state", "NORMAL_RANGE")
    exp = _pct(t5, "state", "EXPANSION")

    # Year stability: std of HIGH_DIRECTIONALITY pct across years
    year_stability_note = ""
    if not year_dir.empty and "HIGH_DIRECTIONALITY" in year_dir.columns:
        hd = year_dir["HIGH_DIRECTIONALITY"].to_numpy(float)
        year_stability_note = (
            f"HIGH_DIRECTIONALITY yearly %: min={hd.min():.1f}, max={hd.max():.1f}, "
            f"std={hd.std():.2f}."
        )

    # Frequent combinations from overlap
    freq_combos = ""
    if not overlap.empty:
        top = overlap.sort_values("pct_of_eligible", ascending=False).head(6)
        freq_combos = "; ".join(
            f"{r['combo']} ({r['pct_of_eligible']:.1f}%)" for _, r in top.iterrows()
        )

    thr_lines = []
    for name, block in thr.get("features", {}).items():
        if name.startswith("diag_"):
            continue
        thr_lines.append(
            f"| {name} | `{block.get('column')}` | {block.get('q33'):.6g} | "
            f"{block.get('q67'):.6g} | {block.get('n')} |"
        )

    lines: list[str] = []
    a = lines.append

    a("# MARKET_STATE_CENSUS — Strategy 52 Step 0")
    a("")
    a("**Status:** Complete (descriptive only).")
    a(f"**Run UTC:** {env.get('run_utc')}")
    a("**Scope:** Map how often NQ sits in observable market conditions. "
      "**No** entries, exits, stops, targets, forward returns, or P&L.")
    a("")
    a("---")
    a("")
    a("## Answers (descriptive)")
    a("")
    a(f"1. **High directionality:** {high_dir:.2f}% of eligible RTH minutes "
      f"(primary metric `ER_60`, IS-frozen terciles)." if high_dir is not None else "1. n/a")
    a(f"2. **Low directionality / choppy:** {low_dir:.2f}% "
      f"(mid={mid_dir:.2f}%)." if low_dir is not None else "2. n/a")
    a(f"3. **Volatility:** low={low_vol:.2f}%, normal={mid_vol:.2f}%, "
      f"high={high_vol:.2f}% (`RV_60`)." if high_vol is not None else "3. n/a")
    a(f"4. **Volume:** low={low_vlm:.2f}%, normal={mid_vlm:.2f}%, "
      f"high={high_vlm:.2f}% (TOD-relative `RVOL_30`)." if high_vlm is not None else "4. n/a")
    a(f"5. **Compression:** {comp:.2f}% (`range_norm_60` bottom tercile)."
      if comp is not None else "5. n/a")
    a(f"6. **Expansion:** {exp:.2f}% (top tercile; mid range={mid_rng:.2f}%)."
      if exp is not None else "6. n/a")
    a("7. **Persistence:** see Table 8 — episode duration distributions by state.")
    a("8. **Transitions:** see Table 9 — including compression→expansion sequence rates below.")
    a(f"9. **Year stability:** {year_stability_note}")
    a("10. **Time-of-day:** see Table 6 — directionality and activity shift across NY blocks.")
    a(f"11. **Frequent state combinations (descriptive prevalence only):** {freq_combos}")
    a("")
    a("---")
    a("")
    a("## Reproducibility")
    a("")
    a(f"| Item | Value |")
    a(f"| --- | --- |")
    a(f"| Dataset | `{feat_meta.get('dataset_path')}` |")
    a(f"| Timestamp range | {feat_meta.get('ts_min')} → {feat_meta.get('ts_max')} |")
    a(f"| 1m bars | {feat_meta.get('n_1m_bars')} |")
    a(f"| Sessions | {feat_meta.get('n_sessions')} |")
    a(f"| Analysis window bars | {feat_meta.get('n_analysis_window')} |")
    a(f"| Census-eligible bars | {feat_meta.get('n_census_eligible')} |")
    a(f"| Timezone | {feat_meta.get('timezone')} |")
    a(f"| Session roll | {feat_meta.get('session_roll')} |")
    a(f"| Analysis window | {feat_meta.get('analysis_window')} |")
    a(f"| Primary windows | ER={feat_meta.get('windows', {}).get('primary_er')}, "
      f"RV={feat_meta.get('windows', {}).get('primary_rv')}, "
      f"range={feat_meta.get('windows', {}).get('primary_range')}, "
      f"RVOL={feat_meta.get('windows', {}).get('rvol')} / "
      f"hist_sessions={feat_meta.get('windows', {}).get('rvol_hist_sessions')} |")
    a(f"| Threshold freeze | IS years {thr.get('threshold_years')} "
      f"(n={thr.get('n_is_eligible')}) |")
    a(f"| Git hash | `{env.get('git_hash')}` |")
    a(f"| Python | {env.get('python', '')[:40]}… |")
    a(f"| NumPy / Pandas | {env.get('numpy')} / {env.get('pandas')} |")
    a("")
    a("### Frozen tercile thresholds (IS 2010–2021)")
    a("")
    a("| Dimension | Column | q33 | q67 | n_IS |")
    a("| --- | --- | ---: | ---: | ---: |")
    a("\n".join(thr_lines))
    a("")
    a("---")
    a("")
    a("## Table 1 — Overall composite (mutually exclusive primary)")
    a("")
    a("Priority freeze: TRENDING > CHOP_RANGE > COMPRESSION > EXPANSION > "
      "HIGH_ACTIVITY > LOW_ACTIVITY > TRANSITION_MIXED.")
    a("")
    a(_md_table(t1, [c for c in ("state", "observations", "pct") if c in t1.columns]))
    a("")
    a("### Table 1b — Independent composite flags (can overlap; % of eligible)")
    a("")
    a(_md_table(t1b))
    a("")
    a("## Table 2 — Directionality (`ER_60`)")
    a("")
    a(_md_table(t2, [c for c in ("state", "observations", "pct") if c in t2.columns]))
    a("")
    a("## Table 3 — Volatility (`RV_60`)")
    a("")
    a(_md_table(t3, [c for c in ("state", "observations", "pct") if c in t3.columns]))
    a("")
    a("## Table 4 — Volume (TOD-relative `RVOL`)")
    a("")
    a(_md_table(t4, [c for c in ("state", "observations", "pct") if c in t4.columns]))
    a("")
    a("## Table 5 — Range / compression (`range_norm_60`)")
    a("")
    a(_md_table(t5, [c for c in ("state", "observations", "pct") if c in t5.columns]))
    a("")
    a("## Table 6 — Time-of-day (directionality %)")
    a("")
    a(_md_table(tod_dir))
    a("")
    a("Full TOD × all dimensions: `results/table6_time_of_day.csv`.")
    a("")
    a("## Day-of-week (directionality %)")
    a("")
    a(_md_table(dow_dir))
    a("")
    a("## Table 7 — Year stability (directionality %)")
    a("")
    a("2026 is a **partial-year** sample (data through mid-August).")
    a("")
    a(_md_table(year_dir))
    a("")
    a("Full yearly tables: `results/table7_year_stability.csv`.")
    a("")
    a("## Table 8 — Persistence (episode durations, minutes)")
    a("")
    a("### Directionality")
    a("")
    a(_md_table(pers_dir))
    a("")
    a("### Range")
    a("")
    a(_md_table(pers_range))
    a("")
    a("### Composite primary")
    a("")
    a(_md_table(pers_comp))
    a("")
    a("## Table 9 — State transitions")
    a("")
    a("### Directionality (top rows by count)")
    a("")
    a(_md_table(_top_trans("directionality_state")))
    a("")
    a("### Range (top rows by count)")
    a("")
    a(_md_table(_top_trans("range_state")))
    a("")
    a("### Composite primary (top rows by count)")
    a("")
    a(_md_table(_top_trans("composite_primary")))
    a("")
    a("### Compression → expansion (descriptive sequence rates)")
    a("")
    a(f"- Direct next-bar COMPRESSION→EXPANSION: "
      f"{cxe.get('direct_bar_compression_to_expansion')} / "
      f"{cxe.get('direct_bar_from_compression')} "
      f"({cxe.get('direct_pct'):.2f}% of bars leaving compression)."
      if cxe.get("direct_pct") is not None else "- n/a")
    a(f"- Episode-level COMPRESSION followed next by EXPANSION: "
      f"{cxe.get('episode_compression_followed_by_expansion')} / "
      f"{cxe.get('episode_compression_count')} "
      f"({cxe.get('episode_pct'):.2f}%)."
      if cxe.get("episode_pct") is not None else "- n/a")
    a("")
    a("Full matrices: `results/transition_matrix_*.csv`.")
    a("")
    a("## Overlap / dependence")
    a("")
    a(_md_table(overlap))
    a("")
    a("## Continuous feature summary (eligible bars)")
    a("")
    a("| Feature | mean | p25 | p50 | p75 | p90 |")
    a("| --- | ---: | ---: | ---: | ---: | ---: |")
    for feat in ("er_60", "rv_60", "rvol", "range_norm_60", "atr_30"):
        s = cont.get(feat)
        if not s:
            continue
        a(f"| {feat} | {s['mean']:.6g} | {s['p25']:.6g} | {s['p50']:.6g} | "
          f"{s['p75']:.6g} | {s['p90']:.6g} |")
    a("")
    a("---")
    a("")
    a("## Leakage audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"FUTURE_DATA_USED = {audit.get('FUTURE_DATA_USED')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a("```")
    a("")
    a(f"Machine-readable detail: `results/audit_report.json` "
      f"(all_pass={audit.get('all_pass')}).")
    a("")
    a("---")
    a("")
    a("## MARKET CENSUS VERDICT")
    a("")
    # Build verdict from numbers
    dominant = []
    if t1b is not None and not t1b.empty:
        ordered = t1b.sort_values("pct", ascending=False)
        for _, r in ordered.iterrows():
            if r["pct"] >= 30:
                dominant.append(f"{r['state']} (~{r['pct']:.0f}%)")
    rare = []
    if not t1.empty:
        for _, r in t1.sort_values("pct").iterrows():
            if r["pct"] < 10:
                rare.append(f"{r['state']} (~{r['pct']:.1f}%)")

    a(f"- **Dominant market states (flag prevalence):** "
      f"{', '.join(dominant) if dominant else 'see tables'}.")
    a(f"- **Rarer mutually-exclusive primary buckets:** "
      f"{', '.join(rare) if rare else 'none below 10%'}; "
      "note tercile dimensions are ~33% by construction on the pooled labeled sample "
      "after IS threshold freeze (exact % can drift slightly out of sample).")
    a("- **Persistence:** states typically persist for multiple minutes within a session "
      "(see medians in Table 8); one-minute flicker is not the modal episode length for "
      "primary labels.")
    a(f"- **Important transitions:** compression→expansion is "
      f"{'present but not dominant' if (cxe.get('episode_pct') or 0) < 50 else 'frequent'} "
      f"at episode level ({cxe.get('episode_pct'):.1f}% of compression episodes "
      f"next become expansion); self-transitions dominate bar-to-bar matrices."
      if cxe.get("episode_pct") is not None else
      "- **Important transitions:** see Table 9.")
    a(f"- **Year-to-year stability:** {year_stability_note} "
      "Interpret 2026 as partial.")
    a("- **Time-of-day differences:** NY open blocks vs midday/PM differ in the mix of "
      "directionality and activity; use Table 6 rather than a single pooled slogan "
      "such as “NQ is mostly choppy.”")
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    a("Given that **direct** COMPRESSION→EXPANSION is rare and most compression exits "
      "pass through NORMAL_RANGE, does a **COMPRESSION + LOW_DIRECTIONALITY** co-occurrence "
      "change the *subsequent* path geometry (time-to-expansion, ER after exit, range "
      "realization) relative to compression that co-occurs with MID/HIGH directionality — "
      "as a pure mechanism contrast, still without constructing a trade?")
    a("")
    a("_Do not answer that question in this step._")
    a("")

    out = STRAT / "MARKET_STATE_CENSUS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    p = write_report()
    print(f"Wrote {p}")
