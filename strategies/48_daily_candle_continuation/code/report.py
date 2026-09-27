"""Write the frozen-rule report from scored tables. No plot, no reinterpretation."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

METRIC_COLUMNS = (
    "model",
    "slice",
    "n",
    "n_flat",
    "hit_rate",
    "matched_base_rate",
    "lift",
    "mean_signed_body",
    "median_signed_body",
)

AGREEMENT_COLUMNS = (
    "block",
    "model",
    "slice",
    "n",
    "n_flat",
    "hit_rate",
    "mean_signed_body",
    "median_signed_body",
)


def _fmt(value: object, digits: int) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.{digits}f}"
    return str(value)


def _table(frame: pd.DataFrame, columns: tuple[str, ...], digits: dict[str, int]) -> str:
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, rule]
    for _, row in frame.iterrows():
        cells = []
        for column in columns:
            places = digits.get(column, 0)
            if column in {"model", "slice", "block"}:
                cells.append(str(row[column]))
            elif column in {"n", "n_flat"}:
                cells.append(str(int(row[column])))
            else:
                cells.append(_fmt(row[column], places))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _metric_digits() -> dict[str, int]:
    return {
        "hit_rate": 4,
        "matched_base_rate": 4,
        "lift": 4,
        "mean_signed_body": 2,
        "median_signed_body": 2,
    }


def write_report(
    path: Path,
    audit: dict[str, object],
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    agreement_primary: pd.DataFrame,
    agreement_secondary: pd.DataFrame,
    verdict: dict[str, object],
) -> None:
    failures = verdict["failures"]
    failure_text = "\n".join(f"- {line}" for line in failures) if failures else "- None."
    reasons = audit.get("incomplete_reasons", {})
    reason_text = ", ".join(f"{key}={value}" for key, value in reasons.items()) or "none"
    parts = [
        "# 48 Daily candle continuation",
        "",
        f"**Verdict: {verdict['verdict']}**",
        "",
        str(verdict["lead"]),
        "",
        failure_text,
        "",
        str(verdict["flip_line"]),
        "",
        str(verdict["long_line"]),
        "",
        "This is an information test. It is not an entry, a stop, or a P&L backtest. "
        "No threshold was chosen after seeing these numbers. The secondary close-to-close "
        "table is a diagnostic and is not used to pick a winner.",
        "",
        "## Frozen rules",
        "",
        "Instrument: NQ Globex `session_date`, roll at 18:00 America/New_York. "
        "Not the NAS100 cash CFD daily chart.",
        "",
        "Candle: open = first bar, high = max high, low = min low, close = last bar. "
        f"Complete sessions only: n_bars >= 1100, first bar in 18:00–18:05, at least one bar in 16:00–17:00. "
        "t−1 is the previous kept session.",
        "",
        "Qualifying bull: Close[t] > Open[t] and Close[t] > Close[t−1]. "
        "Qualifying bear: Close[t] < Open[t] and Close[t] < Close[t−1]. Otherwise no Test 1 forecast.",
        "",
        "Primary outcome: Up if Close[t+1] > Open[t+1], Down if Close[t+1] < Open[t+1], "
        "flat otherwise. A flat is a miss and stays in the denominator. "
        "Signed body = forecast sign × (Close[t+1] − Open[t+1]).",
        "",
        "Test 2 starts at NONE. A qualifying day sets UP or DOWN only from NONE. "
        "From UP, flip to DOWN only if Close[t] < Low[t−1] and Close[t] < Open[t]. "
        "From DOWN, flip to UP only if Close[t] > High[t−1] and Close[t] > Open[t]. "
        "The state after day t forecasts day t+1 only.",
        "",
        "Lift = hit rate − matched base rate. "
        "Matched base rate = (n_up forecasts × P(Up) + n_down forecasts × P(Down)) / n, "
        "using the unconditional outcome rate inside that slice. "
        "P(Up) is not subtracted from a pooled long-and-short hit rate. "
        "Split is the year of the signal day (the close that issues the forecast).",
        "",
        "Real only if Test 1 pooled lift and Test 2 pooled lift are positive on IS, Validation, and OOS, "
        "and the Test 1 bear and Test 2 down lifts are also positive on those three splits. "
        "Bear lifts use P(Down), so a failed bear lift is not excused as the bull base rate.",
        "",
        "## Sample",
        "",
        f"- Bars: {audit['n_bars_total']}",
        f"- Sessions: {audit['n_sessions']}",
        f"- Complete: {audit['n_complete']}",
        f"- Incomplete: {audit['n_incomplete']} ({reason_text})",
        f"- Bars with high < low: {audit['n_corrupt_bars_high_lt_low']}",
        f"- First kept session: {audit['first_session']}",
        f"- Last kept session: {audit['last_session']}",
        f"- Bar range: {audit['ts_min']} → {audit['ts_max']}",
        "",
        "The unconditional sample is every kept session that has a next kept session. "
        "Always Long forecasts Up on that sample, so its hit rate equals P(Up) and its mean signed body equals the mean body.",
        "",
        "## Primary",
        "",
        _table(primary, METRIC_COLUMNS, _metric_digits()),
        "",
        "## Primary agreement",
        "",
        "Agree, disagree, and all Test 1 days that also have a Test 2 state. "
        "Disagreement is the incremental-state test. Hit rate and signed body are reported for each forecast.",
        "",
        _table(agreement_primary, AGREEMENT_COLUMNS, _metric_digits()),
        "",
        "## Secondary (close to close)",
        "",
        "Diagnostic only. Up means Close[t+1] > Close[t]. Not used for the verdict.",
        "",
        _table(secondary, METRIC_COLUMNS, _metric_digits()),
        "",
        "## Secondary agreement",
        "",
        _table(agreement_secondary, AGREEMENT_COLUMNS, _metric_digits()),
        "",
    ]
    path.write_text("\n".join(parts), encoding="utf-8")
