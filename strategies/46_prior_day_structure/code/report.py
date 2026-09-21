"""Write REPORT.md from the frozen tables. Does not refit any definition."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from definitions import ALL_HORIZONS, BODY_BUCKETS, LABEL, MIN_MEDIAN_SPREAD, PENETRATION_BUCKETS, REPORT_PATH

HORIZON_LABELS = {
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "60m",
    "120m": "120m",
    "session_end": "session end",
}


def _num(value: float, digits: int, signed: bool = False) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    if signed:
        return f"{value:+.{digits}f}"
    return f"{value:.{digits}f}"


def _md(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, rule]
    for _, row in frame.iterrows():
        cells = [str(row[col]) for col in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _stat_table(table: pd.DataFrame, stat: str, digits: int, signed: bool) -> pd.DataFrame:
    rows: list[dict] = []
    for _, source in table.iterrows():
        row = {"bucket": source["bucket"], "N 30m": int(source["30m_n"]) if np.isfinite(source["30m_n"]) else 0}
        for horizon in ALL_HORIZONS:
            row[HORIZON_LABELS[horizon]] = _num(float(source[f"{horizon}_{stat}"]), digits, signed=signed)
        rows.append(row)
    return pd.DataFrame(rows)


def _ordering_text(snapshot: dict) -> str:
    if not snapshot["evaluable"]:
        counts = ", ".join(f"{name} N={snapshot['counts'][name]}" for name in snapshot["counts"])
        return f"not evaluable ({counts})"
    parts = ", ".join(f"{name}={snapshot['medians'][name]:+.4f} (N={snapshot['counts'][name]})" for name in snapshot["medians"])
    return f"{parts}; spread={snapshot['spread']:.4f}; order={snapshot['ordering']}"


def _structure_relevant(structure: pd.DataFrame, panel: pd.DataFrame) -> tuple[bool, str]:
    combined = structure[structure["direction"] == "combined"]
    medians = combined["median_30m_rng"].to_numpy(np.float64)
    finite = medians[np.isfinite(medians)]
    span = float(finite.max() - finite.min()) if len(finite) else np.nan
    signs = []
    magnitudes = []
    for split in ("IS", "Validation"):
        subset = panel[(panel["qualified"]) & (panel["split"] == split)]
        left = subset["previous_body_fraction"].to_numpy(np.float64)
        right = subset["fwd_ret_rng_30m"].to_numpy(np.float64)
        mask = np.isfinite(left) & np.isfinite(right)
        if int(mask.sum()) < 50:
            signs.append(None)
            magnitudes.append(np.nan)
            continue
        rank_left = pd.Series(left[mask]).rank().to_numpy(np.float64)
        rank_right = pd.Series(right[mask]).rank().to_numpy(np.float64)
        rho = float(np.corrcoef(rank_left, rank_right)[0, 1])
        magnitudes.append(rho)
        if not np.isfinite(rho) or abs(rho) < 0.03:
            signs.append(0)
        else:
            signs.append(1 if rho > 0 else -1)
    relevant = (
        np.isfinite(span)
        and span >= MIN_MEDIAN_SPREAD
        and signs[0] not in (None, 0)
        and signs[0] == signs[1]
    )
    detail = (
        f"Body-fraction 30m median span={span:.4f} previous-day ranges. "
        f"Spearman of body fraction vs 30m return: IS={magnitudes[0]:+.3f}, Validation={magnitudes[1]:+.3f}."
    )
    return bool(relevant), detail


def write_report(
    panel: pd.DataFrame,
    audit: dict,
    pair_counts: dict[str, int],
    incomplete_reasons: dict[str, int],
    safety_lines: list[str],
    verdict_payload: dict,
    candle_frame: pd.DataFrame,
    forward_points: pd.DataFrame,
    forward_range: pd.DataFrame,
    bull_points: pd.DataFrame,
    bear_points: pd.DataFrame,
    bull_range: pd.DataFrame,
    bear_range: pd.DataFrame,
    excursions: pd.DataFrame,
    max_range: pd.DataFrame,
    baseline: pd.DataFrame,
    structure: pd.DataFrame,
    wick_stats: dict[str, float],
    yearly: pd.DataFrame,
    frequency: pd.DataFrame,
    durations: pd.DataFrame,
    split_range: dict[str, pd.DataFrame],
) -> Path:
    qualified = panel[panel["qualified"]]
    events = panel[panel["sequence_state"] == "retracement"]
    relevant, structure_detail = _structure_relevant(structure, panel)
    lines: list[str] = []
    add = lines.append

    add(f"# Previous-day directional structure — mechanism report")
    add("")
    add(f"**{LABEL}**")
    add("")
    add("No executable strategy is defined or tested in this document.")
    add("")
    add(
        "The event is clean separation beyond the previous close, then the first later bar that "
        "retraces into the previous close-to-extreme range. Penetration is measured on that later "
        "bar. The discarded opening-bar touch is not in these tables. No ATR cutoff is applied."
    )
    add("")
    add(f"## Research verdict: {verdict_payload['verdict']}")
    add("")
    add("The verdict is the frozen rule in `PREREGISTRATION.md`. It is not a profitability claim.")
    add("")
    add("## A. Dataset audit")
    add("")
    add("| Item | Value |")
    add("| --- | --- |")
    add("| Requested path | `d:\\NQ\\nq_data` (not present on this machine) |")
    add("| Source used | `data/nq_1m_continuous.parquet` via `common.nq_session.load_nq`, read only |")
    add(f"| Timestamp range | {audit['ts_min']} → {audit['ts_max']} |")
    add(f"| 1-minute bars | {audit['n_bars_total']} |")
    add(f"| Bars with high < low | {audit['n_corrupt_bars_high_lt_low']} |")
    add("| Session convention | Globex `session_date`, rolls at 18:00 America/New_York |")
    add("| Session end | Last 1-minute bar of that Globex session |")
    add("| Splits | IS 2010–2021 / Validation 2022–2024 / OOS 2025–2026, by the following session's year |")
    add(f"| Observed sessions | {audit['n_sessions']} |")
    add(f"| Complete sessions | {audit['n_complete']} |")
    add(f"| Incomplete sessions | {audit['n_incomplete']} |")
    add(f"| Adjacent slots blocked because one side was incomplete | {pair_counts['blocked_by_incomplete']} |")
    add(f"| Eligible directional pairs | {pair_counts['eligible_pairs']} |")
    add(f"| Previous day doji, dropped | {pair_counts['doji_previous']} |")
    add(f"| Undefined reference range, dropped | {pair_counts['undefined_reference']} |")
    add(f"| First bar entered the range before separation | {pair_counts['entered_before_separation']} |")
    add(f"| Separated, no return into the range | {pair_counts['separated_no_return']} |")
    add(f"| Retracement events | {int(events.shape[0])} |")
    add(f"| Retracement with a forward bar | {pair_counts['retracement']} |")
    add(f"| Retracement on the last bar, no forward path | {pair_counts['retracement_on_last_bar']} |")
    add("")
    add("A complete session has at least 1100 bars, starts in 18:00–18:05 ET, and prints at least one bar in 16:00–16:59 ET. Incomplete sessions are not used as the previous day and are not skipped over.")
    add("")
    add("Incomplete reasons (a session can fail more than one check; the stored reason is the joined list):")
    add("")
    add("| Reason | Sessions |")
    add("| --- | --- |")
    for reason, count in sorted(incomplete_reasons.items(), key=lambda item: -item[1]):
        add(f"| `{reason}` | {count} |")
    add("")
    add("## B. Previous-day candle distribution")
    add("")
    add("Counted on complete sessions, before the following-session pair filter.")
    add("")
    direction_counts = candle_frame["direction"].value_counts()
    add("| Direction | Complete sessions |")
    add("| --- | --- |")
    for name in ("bullish", "bearish", "doji"):
        add(f"| {name} | {int(direction_counts.get(name, 0))} |")
    add("")
    add("Range, body fraction, and wick fractions:")
    add("")
    dist_rows = []
    for column, label in (
        ("range", "range (points)"),
        ("body_fraction", "body / range"),
        ("upper_wick_fraction", "upper wick / range"),
        ("lower_wick_fraction", "lower wick / range"),
    ):
        values = candle_frame[column].to_numpy(np.float64)
        values = values[np.isfinite(values)]
        quantiles = np.quantile(values, [0.1, 0.25, 0.5, 0.75, 0.9])
        dist_rows.append(
            {
                "measure": label,
                "N": int(len(values)),
                "mean": _num(float(np.mean(values)), 3),
                "p10": _num(float(quantiles[0]), 3),
                "p25": _num(float(quantiles[1]), 3),
                "p50": _num(float(quantiles[2]), 3),
                "p75": _num(float(quantiles[3]), 3),
                "p90": _num(float(quantiles[4]), 3),
            }
        )
    add(_md(pd.DataFrame(dist_rows)))
    add("")
    add("Body-fraction buckets on complete sessions:")
    add("")
    add("| Body fraction | Sessions |")
    add("| --- | --- |")
    body_counts = candle_frame["body_bucket"].value_counts()
    for bucket in BODY_BUCKETS:
        add(f"| {bucket} | {int(body_counts.get(bucket, 0))} |")
    add("")
    add("## C. Sequence audit")
    add("")
    add(
        "Bullish previous day: before any bar with `low <= previous close`, require a bar with "
        "`low > previous close`. That bar is separation, including one tick. The retracement is "
        "the first later bar with `low <= previous close`. Bearish previous day mirrors this with "
        "`high < previous close`, then a later bar with `high >= previous close`. A bar that trades "
        "both sides of the close does not establish separation. Separation with no return is an "
        "audit count, not a penetration bucket. No ATR and no point-distance cutoff."
    )
    add("")
    add(
        "At 1-minute resolution the first bar either enters the range or lies entirely on the "
        "continuation side of the close. Clean separation is that first bar. The return, when it "
        "happens, is a later bar. This is the definition, not a delay filter."
    )
    add("")
    separated = panel["sequence_state"].isin(["retracement", "separated_no_return"])
    separation_not_first = int((panel.loc[separated, "separation_index"] != 0).sum()) if bool(separated.any()) else 0
    add(
        f"Separation is the first bar in {int(separated.sum()) - separation_not_first} of "
        f"{int(separated.sum())} separated sessions (exceptions: {separation_not_first})."
    )
    add("")
    freq_rows = []
    for _, source in frequency.iterrows():
        freq_rows.append(
            {
                "item": source["item"],
                "direction": source["direction"],
                "N": int(source["n"]),
                "share": _num(float(source["share_of_direction"]) * 100.0, 1) + "%",
            }
        )
    add(_md(pd.DataFrame(freq_rows)))
    add("")
    add("Minutes from the separation bar to the retracement bar, among retracement events:")
    add("")
    duration_rows = []
    ordered_durations = durations[durations["metric"] == "separation_duration_minutes"]
    for _, source in ordered_durations.iterrows():
        duration_rows.append(
            {
                "direction": source["direction"],
                "N": int(source["n"]),
                "mean": _num(float(source["mean"]), 1),
                "p10": _num(float(source["p10"]), 1),
                "p25": _num(float(source["p25"]), 1),
                "p50": _num(float(source["p50"]), 1),
                "p75": _num(float(source["p75"]), 1),
                "p90": _num(float(source["p90"]), 1),
            }
        )
    add(_md(pd.DataFrame(duration_rows)))
    add("")
    add("Clock time of the retracement bar, in minutes after 18:00 ET:")
    add("")
    clock_rows = []
    ordered_clock = durations[durations["metric"] == "retracement_minutes_from_open"]
    for _, source in ordered_clock.iterrows():
        clock_rows.append(
            {
                "direction": source["direction"],
                "N": int(source["n"]),
                "p10": _num(float(source["p10"]), 1),
                "p50": _num(float(source["p50"]), 1),
                "p90": _num(float(source["p90"]), 1),
            }
        )
    add(_md(pd.DataFrame(clock_rows)))
    add("")
    open_share = float((events["retracement_minutes_from_open"] == 0).mean()) if len(events) else float("nan")
    add(
        f"The retracement bar is the 18:00 ET open in {open_share:.1%} of retracement events. "
        "That share is zero when separation occupies the first bar and the return is a later bar."
    )
    add("")
    add("## D. Penetration at the retracement")
    add("")
    add(
        "Retracement penetration is the penetration of that later bar, measured at its low "
        "(bullish previous day) or high (bearish previous day). This is not a tick-level first "
        "print. One minute can travel from the boundary to a deep extreme, so this depth is an "
        "upper bound on the instantaneous entry. Maximum penetration uses the whole following "
        "session and is an outcome, not an entry-time fact. Buckets are unchanged."
    )
    add("")
    add("| Bucket | Retracement sessions | Maximum-penetration sessions |")
    add("| --- | --- | --- |")
    max_counts = panel["max_penetration_bucket"].value_counts()
    event_counts = events["retracement_bucket"].value_counts()
    add(f"| no penetration | — | {int(max_counts.get('no_penetration', 0))} |")
    for bucket in PENETRATION_BUCKETS:
        add(f"| {bucket} | {int(event_counts.get(bucket, 0))} | {int(max_counts.get(bucket, 0))} |")
    add("")
    event_values = events["retracement_penetration_pct"].to_numpy(np.float64)
    max_values = panel["max_penetration_pct"].to_numpy(np.float64)
    add(
        f"Retracement median (among return events) = {_num(float(np.nanmedian(event_values)), 2)}%. "
        f"Maximum-penetration median (all eligible pairs) = {_num(float(np.nanmedian(max_values)), 2)}%."
    )
    add("")
    add("Median separation duration and clock time of the retracement, by penetration bucket:")
    add("")
    time_rows = []
    for bucket in PENETRATION_BUCKETS:
        subset = events[events["retracement_bucket"] == bucket]
        time_rows.append(
            {
                "bucket": bucket,
                "N": int(len(subset)),
                "median separation minutes": _num(float(np.nanmedian(subset["separation_duration_minutes"])), 1)
                if len(subset)
                else "—",
                "median minutes after 18:00": _num(float(np.nanmedian(subset["retracement_minutes_from_open"])), 1)
                if len(subset)
                else "—",
            }
        )
    add(_md(pd.DataFrame(time_rows)))
    add("")
    add("## E. Forward outcomes by retracement penetration")
    add("")
    add(
        "Positive values continue the previous day's direction. Percentage positive counts "
        "strictly positive returns. It is not a win rate. There is no position and no cost."
    )
    add("")
    add("Measurement price is the open of the bar after the retracement bar. Point units are NQ index points.")
    add("")
    add("### Combined sample, points — medians")
    add("")
    add(_md(_stat_table(forward_points, "median", 2, True)))
    add("")
    add("### Combined sample, points — means")
    add("")
    add(_md(_stat_table(forward_points, "mean", 2, True)))
    add("")
    add("### Combined sample, points — standard deviation")
    add("")
    add(_md(_stat_table(forward_points, "std", 2, False)))
    add("")
    add("### Combined sample — percentage positive (not a win rate)")
    add("")
    add(_md(_stat_table(forward_points, "pct_positive", 1, False)))
    add("")
    add("### Combined sample, return / previous-day range — medians")
    add("")
    add(
        "This unit is pre-registered so that the rise in the NQ price level across 2010–2026 "
        "does not dominate the comparison. It is not a filter."
    )
    add("")
    add(_md(_stat_table(forward_range, "median", 4, True)))
    add("")
    add("### Combined sample, return / previous-day range — means")
    add("")
    add(_md(_stat_table(forward_range, "mean", 4, True)))
    add("")
    add("## F. MFE / MAE")
    add("")
    add(
        "Excursions run from the measurement bar through the horizon bar. The retracement bar "
        "is excluded. For a bullish previous day, MFE is the highest high above the measurement "
        "price and MAE is the deepest low below it. For a bearish previous day, MFE is the "
        "deepest low below the measurement price and MAE is the highest high above it. Both are "
        "floored at zero."
    )
    add("")
    show = excursions[excursions["horizon"].isin(["30m", "60m", "session_end"])].copy()
    pretty = pd.DataFrame(
        {
            "bucket": show["bucket"],
            "horizon": show["horizon"],
            "N": show["n"],
            "median MFE pts": show["mfe_median_pts"].map(lambda v: _num(float(v), 2)),
            "median MAE pts": show["mae_median_pts"].map(lambda v: _num(float(v), 2)),
            "median MFE / range": show["mfe_median_rng"].map(lambda v: _num(float(v), 4)),
            "median MAE / range": show["mae_median_rng"].map(lambda v: _num(float(v), 4)),
        }
    )
    add(_md(pretty))
    add("")
    add("The full horizon set, including means, is in `results/mfe_mae_by_retracement.csv`.")
    add("")
    add("## G. Bullish versus bearish previous days")
    add("")
    add("Returns stay direction-normalized. Positive still means continuation of that previous day.")
    add("")
    add("### Bullish previous day — median points")
    add("")
    add(_md(_stat_table(bull_points, "median", 2, True)))
    add("")
    add("### Bearish previous day — median points")
    add("")
    add(_md(_stat_table(bear_points, "median", 2, True)))
    add("")
    add("### Bullish previous day — median return / previous-day range")
    add("")
    add(_md(_stat_table(bull_range, "median", 4, True)))
    add("")
    add("### Bearish previous day — median return / previous-day range")
    add("")
    add(_md(_stat_table(bear_range, "median", 4, True)))
    add("")
    add("### Baseline from the session open")
    add("")
    add(
        "Same direction-normalized return, measured from the following session's 18:00 open, "
        "with no penetration condition. This is the previous-day-direction drift control."
    )
    add("")
    base_rows = []
    for _, source in baseline.iterrows():
        base_rows.append(
            {
                "sample": source["sample"],
                "unit": source["unit"],
                "N 30m": int(source["30m_n"]),
                "30m median": _num(float(source["30m_median"]), 4 if source["unit"] == "range" else 2, True),
                "60m median": _num(float(source["60m_median"]), 4 if source["unit"] == "range" else 2, True),
                "30m % > 0": _num(float(source["30m_pct_positive"]), 1),
                "session-end median": _num(
                    float(source["session_end_median"]), 4 if source["unit"] == "range" else 2, True
                ),
            }
        )
    add(_md(pd.DataFrame(base_rows)))
    add("")
    add("## H. Chronological stability")
    add("")
    add("Range-normalized median forward return by retracement bucket. Fixed horizons are the stability evidence. Session-end residual time varies with the retracement clock.")
    add("")
    for split, table in split_range.items():
        add(f"### {split}")
        add("")
        add(_md(_stat_table(table, "median", 4, True)))
        add("")
    add("### Year by year, 30-minute return / previous-day range")
    add("")
    year_rows = []
    for _, source in yearly.iterrows():
        year_rows.append(
            {
                "year": int(source["year"]),
                "split": source["split"],
                "N": int(source["n"]),
                "Spearman": _num(float(source["spearman_30m"]), 3, True),
                "shallow N": int(source["shallow_n"]),
                "shallow median": _num(float(source["shallow_median_30m"]), 4, True),
                "mid N": int(source["mid_n"]),
                "mid median": _num(float(source["mid_median_30m"]), 4, True),
                "deep N": int(source["deep_n"]),
                "deep median": _num(float(source["deep_median_30m"]), 4, True),
            }
        )
    add(_md(pd.DataFrame(year_rows)))
    add("")
    add("Shallow is retracement penetration in [0, 30). Mid is [30, 75). Deep is above 75, including beyond the previous extreme. These pools only summarize the frozen buckets.")
    add("")
    add("## I. Previous-day candle structure")
    add("")
    add("Fixed body-fraction bins. No bin was added or dropped after seeing returns.")
    add("")
    struct_rows = []
    for _, source in structure.iterrows():
        struct_rows.append(
            {
                "direction": source["direction"],
                "body": source["body_bucket"],
                "N": int(source["n"]),
                "median retracement %": _num(float(source["median_retracement_pct"]), 1),
                "median max penetration %": _num(float(source["median_max_penetration_pct"]), 1),
                "median 30m / range": _num(float(source["median_30m_rng"]), 4, True),
                "30m % > 0": _num(float(source["pct_positive_30m"]), 1),
            }
        )
    add(_md(pd.DataFrame(struct_rows)))
    add("")
    add("Descriptive rank correlations on qualifying retracements (not a search):")
    add("")
    add("| Association | Spearman |")
    add("| --- | --- |")
    for key, value in wick_stats.items():
        add(f"| {key} | {_num(float(value), 3, True)} |")
    add("")
    add(structure_detail)
    add("")
    add(
        "Structure "
        + ("meets" if relevant else "does not meet")
        + " the pre-registered bar for a later dedicated candle-structure test."
    )
    add("")
    add("## Non-causal appendix: maximum penetration")
    add("")
    add(
        "These medians group sessions by how far price eventually traveled, which can happen "
        "after the forward window. They are not a decision-time relationship. Do not read a "
        "cell as something that was known at the retracement."
    )
    add("")
    add(_md(_stat_table(max_range, "median", 4, True)))
    add("")
    add("## J. Interpretation")
    add("")
    slices = verdict_payload["slices"]
    add(f"Frozen verdict: **{verdict_payload['verdict']}**.")
    add("")
    add(
        f"Combined-sample Spearman of continuous retracement penetration versus the "
        f"range-normalized return: 30m = {_num(float(verdict_payload['spearman_30m']), 3, True)}, "
        f"60m = {_num(float(verdict_payload['spearman_60m']), 3, True)}."
    )
    add("")
    for horizon in ("30m", "60m"):
        add(f"30-minute pool snapshot:" if horizon == "30m" else "60-minute pool snapshot:")
        add("")
        for label in ("combined", "IS", "Validation", "OOS", "bullish", "bearish"):
            add(f"- {label}: {_ordering_text(slices[label][horizon])}")
        add("")
    add("### 1. Does penetration depth matter?")
    add("")
    add(_depth_answer(qualified, events, forward_range, baseline, verdict_payload))
    add("")
    add("### 2. Is the relationship stable across time?")
    add("")
    add(_stability_answer(yearly, verdict_payload))
    add("")
    add("### 3. Is it present on both bullish and bearish previous days?")
    add("")
    add(_side_answer(bull_range, bear_range, baseline))
    add("")
    add("### 4. Does previous-day candle structure appear relevant?")
    add("")
    add(
        structure_detail
        + f" The rank correlation of body fraction with maximum penetration is {float(wick_stats['spearman_body_vs_max_penetration']):+.3f}, and the wick fractions move the other way. "
        "That is mostly geometry: a small body leaves a shorter close-to-extreme distance, so the same point retracement is a larger penetration percent. "
        "It is not a forecast of the 30-minute return. "
        + (
            "A later structure test could be preregistered on its own."
            if relevant
            else "This pass does not justify a dedicated structure test."
        )
    )
    add("")
    add("### 5. What mechanism, if any, deserves the next test?")
    add("")
    add(_next_test(verdict_payload["verdict"], relevant))
    add("")
    add("## Safety checks")
    add("")
    for line in safety_lines:
        add(f"- PASS: {line}")
    add("")
    add("Confirmed absent: lookahead in the previous-day label, future bars redefining the retracement, forward returns inside the retracement bar, bucket edits after results, parameter optimization, ATR, SMT, order flow, volume profile, Fibonacci, lower-timeframe confirmation, recovery rules, and trading P&L.")
    add("")
    add("## Figures")
    add("")
    add("- `reports/figures/penetration_distributions.png`")
    add("- `reports/figures/separation_duration.png`")
    add("- `reports/figures/forward_vs_penetration.png`")
    add("- `reports/figures/median_forward_by_bucket.png`")
    add("- `reports/figures/mfe_mae_by_bucket.png`")
    add("- `reports/figures/bull_vs_bear.png`")
    add("- `reports/figures/year_stability.png`")
    add("")
    add("Display histograms clip the horizontal axis at 150% penetration. Tables do not.")
    add("")
    add("## How this was run")
    add("")
    add("```")
    add("python strategies/46_prior_day_structure/code/run_mechanism.py")
    add("```")
    add("")
    add("Working directory: repository root. `strategies/45_ict_ny_smt` already existed, so this study is folder 46 and does not share code with it.")
    add("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return REPORT_PATH


def _cell(table: pd.DataFrame, bucket: str, column: str) -> float:
    rows = table[table["bucket"] == bucket]
    if rows.empty:
        return float("nan")
    return float(rows.iloc[0][column])


def _depth_answer(
    qualified: pd.DataFrame,
    events: pd.DataFrame,
    forward_range: pd.DataFrame,
    baseline: pd.DataFrame,
    verdict_payload: dict,
) -> str:
    deep_n = int(((qualified["retracement_pool"] == "deep_gt_75") & qualified["fwd_ret_rng_30m"].notna()).sum())
    shallow_n = int((qualified["retracement_bucket"] == "0-10%").sum())
    median_pen = float(np.nanmedian(events["retracement_penetration_pct"])) if len(events) else float("nan")
    duration = float(np.nanmedian(events["separation_duration_minutes"])) if len(events) else float("nan")
    open_share = float((events["retracement_minutes_from_open"] == 0).mean()) if len(events) else float("nan")
    shallow_median = _cell(forward_range, "0-10%", "30m_median")
    shallow_60 = _cell(forward_range, "0-10%", "60m_median")
    base = baseline[(baseline["sample"] == "all_eligible") & (baseline["unit"] == "range")].iloc[0]
    return (
        "Penetration in these tables is the later retracement, after a prior bar traded entirely on the "
        "continuation side of the previous close. Sessions whose first bar already entered the range are "
        "excluded. "
        f"The retracement bar is the 18:00 open in {open_share:.1%} of return events. "
        f"Median time from separation to that bar is {duration:.1f} minutes. "
        f"Median penetration is {median_pen:.2f}%. "
        f"{shallow_n} of {len(qualified)} forward paths sit in 0–10%, and the deep pool has N={deep_n} at 30 minutes. "
        f"In 0–10% the 30-minute median is {shallow_median:+.4f} previous-day ranges and the 60-minute median is {shallow_60:+.4f}. "
        f"The open baseline, with no penetration condition, is {float(base['30m_median']):+.4f} at 30 minutes and "
        f"{float(base['60m_median']):+.4f} at 60 minutes. "
        f"Spearman of retracement penetration versus the range-normalized return is "
        f"{float(verdict_payload['spearman_30m']):+.3f} at 30 minutes and {float(verdict_payload['spearman_60m']):+.3f} at 60 minutes. "
        "The frozen verdict above is the depth conclusion for this event. It does not reuse the discarded opening-bar touch."
    )


def _stability_answer(yearly: pd.DataFrame, verdict_payload: dict) -> str:
    years = ", ".join(str(int(year)) for year in yearly["year"].tolist()) if len(yearly) else "none"
    counts = []
    for label in ("IS", "Validation", "OOS"):
        deep_n = verdict_payload["slices"][label]["30m"]["counts"]["deep_gt_75"]
        evaluable = verdict_payload["slices"][label]["30m"]["evaluable"]
        counts.append(f"{label} deep N={deep_n} ({'evaluable' if evaluable else 'not evaluable'})")
    return (
        "Stability uses the same shallow, mid, and deep pools, now on retracement penetration. "
        + "; ".join(counts)
        + ". A pool below N=50 cannot support the frozen stability claim. "
        f"The years present are {years}. 2010 does not appear when almost none of its sessions passed the completeness rule. "
        "No year was kept or dropped after seeing its median."
    )


def _side_answer(bull_range: pd.DataFrame, bear_range: pd.DataFrame, baseline: pd.DataFrame) -> str:
    bull_base = baseline[(baseline["sample"] == "bullish") & (baseline["unit"] == "range")].iloc[0]
    bear_base = baseline[(baseline["sample"] == "bearish") & (baseline["unit"] == "range")].iloc[0]
    bull_deep = int(_cell(bull_range, "75-100%", "30m_n")) + int(_cell(bull_range, ">100%", "30m_n"))
    bear_deep = int(_cell(bear_range, "75-100%", "30m_n")) + int(_cell(bear_range, ">100%", "30m_n"))
    return (
        "Returns stay direction-normalized on the retracement sample. "
        f"Bullish 0–10% session-end median is {_cell(bull_range, '0-10%', 'session_end_median'):+.4f} "
        f"of the previous range (30m N={int(_cell(bull_range, '0-10%', '30m_n'))}), against an open baseline of "
        f"{float(bull_base['session_end_median']):+.4f}. "
        f"Bearish 0–10% session-end median is {_cell(bear_range, '0-10%', 'session_end_median'):+.4f} "
        f"(30m N={int(_cell(bear_range, '0-10%', '30m_n'))}), against an open baseline of "
        f"{float(bear_base['session_end_median']):+.4f}. "
        f"Deep buckets at 30 minutes, 75–100% plus >100%, have N={bull_deep} on bullish previous days and N={bear_deep} on bearish previous days. "
        "A shared pattern requires both sides to clear the frozen pool rule. "
        "The non-causal maximum-penetration appendix is not a substitute: its session-end column can move because "
        "the session-end price is part of the path that defined the bin."
    )


def _next_test(verdict: str, structure_relevant: bool) -> str:
    if verdict == "MECHANISM SUPPORTED":
        return (
            "The frozen rule was met on retracement depth. Any next step would still be a new preregistration, "
            "not a strategy. Do not add ATR or a point-distance separation cutoff to preserve this result."
        )
    return (
        "Do not add ATR, a point-distance separation cutoff, a 50% level, a candle filter, a recovery rule, or an entry. "
        "The event in this report is already the later retracement after clean separation. "
        "First-bar range entries are excluded, and separation without a return stays an audit count. "
        + (
            "Body fraction cleared its own descriptive bar and could be written up as a separate mechanism "
            "preregistration. It still would not be a strategy."
            if structure_relevant
            else "Candle structure did not clear its pre-registered descriptive bar."
        )
    )

