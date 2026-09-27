"""Write REPORT.md from scored tables. The verdict text comes from the frozen clauses."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def _num(value: object, digits: int) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "NA"
    return f"{float(value):.{digits}f}"


def _pct(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "NA"
    return f"{float(value) * 100:.2f}%"


def _pp(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "NA"
    return f"{float(value):+.2f}"


def _int(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "NA"
    return str(int(value))


def _markdown(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(cells) + " |" for cells in rows]
    return "\n".join([head, rule, *body])


def _distribution_section(table: pd.DataFrame, sample: str) -> str:
    chosen = table.loc[table["sample"] == sample]
    rows: list[list[str]] = []
    for _, row in chosen.iterrows():
        rows.append(
            [
                str(row["side"]),
                str(row["bucket"]),
                _int(row["n_streaks"]),
                _pct(row["pct_of_all_streaks"]),
                _pct(row["pct_of_side_streaks"]),
                _int(row["n_sessions"]),
            ]
        )
    return _markdown(
        ["side", "length", "streaks", "pct of all streaks", "pct of this side", "sessions inside"],
        rows,
    )


def _continuation_section(table: pd.DataFrame, sample: str) -> str:
    chosen = table.loc[table["sample"] == sample]
    rows: list[list[str]] = []
    for _, row in chosen.iterrows():
        flag = "yes" if bool(row["small_sample"]) else ""
        rows.append(
            [
                str(row["side"]),
                str(row["bucket"]),
                _int(row["n"]),
                _pct(row["observed"]),
                _pct(row["matched_base"]),
                _pp(row["lift_pp"]),
                flag,
            ]
        )
    return _markdown(
        ["side", "length", "n", "observed", "matched base", "lift pp", "n<30"],
        rows,
    )


def _null_section(table: pd.DataFrame, sample: str) -> str:
    chosen = table.loc[table["sample"] == sample]
    rows: list[list[str]] = []
    for _, row in chosen.iterrows():
        rows.append(
            [
                str(row["statistic"]),
                _int(row["observed"]),
                _num(row["null_mean"], 2),
                _num(row["null_p50"], 1),
                _num(row["null_p95"], 1),
                _num(row["percentile_rank"], 1),
                f"{int(row['n_null_ge_observed'])}/{int(row['n_perm'])}",
                _num(row["p_ge"], 4),
            ]
        )
    return _markdown(
        ["statistic", "observed", "null mean", "null p50", "null p95", "percentile", "null >= observed", "p_ge"],
        rows,
    )


def _asymmetry_section(table: pd.DataFrame, sample: str) -> str:
    chosen = table.loc[table["sample"] == sample]
    rows: list[list[str]] = []
    for _, row in chosen.iterrows():
        rows.append(
            [
                str(row["side"]),
                _int(row["n_streaks"]),
                _num(row["mean_length"], 2),
                _num(row["median_length"], 2),
                _int(row["max_length"]),
            ]
        )
    return _markdown(["side", "streaks", "mean", "median", "max"], rows)


def _base_line(rates: dict[str, object]) -> str:
    return (
        f"Sessions {int(rates['n_sessions'])}. "
        f"Bull {_int(rates['n_bull'])} ({_pct(rates['bull_rate'])}). "
        f"Bear {_int(rates['n_bear'])} ({_pct(rates['bear_rate'])}). "
        f"Flat {_int(rates['n_flat'])} ({_pct(rates['flat_rate'])})."
    )


def _year_table(years: pd.DataFrame) -> str:
    rows: list[list[str]] = []
    for _, row in years.iterrows():
        rows.append(
            [
                str(int(row["year"])),
                _int(row["n_sessions"]),
                _pct(row["bull_rate"]),
                _pct(row["bear_rate"]),
                _num(row["avg_bull_streak"], 2),
                _num(row["median_bull_streak"], 1),
                _int(row["max_bull_streak"]),
                _num(row["avg_bear_streak"], 2),
                _num(row["median_bear_streak"], 1),
                _int(row["max_bear_streak"]),
                _pct(row["bull_continuation_after_1"]),
                _pct(row["bull_continuation_after_2"]),
                _pct(row["bull_continuation_after_3"]),
                _pct(row["bear_continuation_after_1"]),
                _pct(row["bear_continuation_after_2"]),
                _pct(row["bear_continuation_after_3"]),
            ]
        )
    return _markdown(
        [
            "year",
            "n",
            "bull rate",
            "bear rate",
            "avg bull",
            "med bull",
            "max bull",
            "avg bear",
            "med bear",
            "max bear",
            "bull after 1",
            "bull after 2",
            "bull after 3",
            "bear after 1",
            "bear after 2",
            "bear after 3",
        ],
        rows,
    )


def write_report(
    path: Path,
    audit: dict[str, object],
    rates: dict[str, dict[str, object]],
    distribution: pd.DataFrame,
    continuation: pd.DataFrame,
    nulls: pd.DataFrame,
    asymmetry: pd.DataFrame,
    years: pd.DataFrame,
    verdict: dict[str, object],
) -> None:
    reasons = audit.get("incomplete_reasons", {})
    reason_text = ", ".join(f"{key}={value}" for key, value in reasons.items()) or "none"
    clause_lines = "\n".join(f"- {line}" for line in verdict["lines"])
    sample_blocks = []
    for sample in ("All", "IS", "Validation", "OOS"):
        sample_blocks.append(
            "\n".join(
                [
                    f"### {sample}",
                    "",
                    _base_line(rates[sample]),
                    "",
                    "Streak distribution",
                    "",
                    _distribution_section(distribution, sample),
                    "",
                    "Continuation and matched-base lift. Survival given current length is this same rate.",
                    "",
                    _continuation_section(continuation, sample),
                    "",
                    "Randomized null",
                    "",
                    _null_section(nulls, sample),
                    "",
                    "Bull versus bear streak lengths",
                    "",
                    _asymmetry_section(asymmetry, sample),
                    "",
                ]
            )
        )
    text = "\n".join(
        [
            "# 49 Daily directional streak persistence",
            "",
            f"**Verdict: {verdict['verdict']}**",
            "",
            str(verdict["lead"]),
            "",
            clause_lines,
            "",
            "No streak length was selected after seeing the tables. "
            "The continuation clause uses only pooled lengths 2 and 3. "
            "Length 1 is the one-day transition and is not a verdict input. "
            "Buckets with n < 30 are descriptive. "
            "A result that looks large against 50% is not evidence.",
            "",
            "## 1. Hypothesis",
            "",
            "Same-direction Globex sessions may form streaks that are longer, or that continue more often, "
            "than the unconditional bull and bear rates already imply. "
            "The test is not whether one bull or bear day predicts the next day.",
            "",
            "## 2. Session definition",
            "",
            "NQ continuous futures. One candle per complete Globex session from Strategy 48 `load_candles()`, unmodified. "
            "The session rolls at 18:00 America/New_York. "
            "Open is the first price, high the session high, low the session low, close the last price. "
            "This is not a NAS100 cash CFD candle and not an RTH-only candle.",
            "",
            "Bull means close above open. Bear means close below open. Flat means close equal to open. "
            "A flat day ends a streak and is not a bull or bear streak. "
            "Inside each sample, the next day is the next kept session in that sample.",
            "",
            "## 3. Sample",
            "",
            f"- Bars: {audit['n_bars_total']}",
            f"- Sessions before the completeness filter: {audit['n_sessions']}",
            f"- Complete sessions: {audit['n_complete']}",
            f"- Incomplete sessions dropped: {audit['n_incomplete']} ({reason_text})",
            f"- Bars with high < low: {audit['n_corrupt_bars_high_lt_low']}",
            f"- First kept session: {audit['first_session']}",
            f"- Last kept session: {audit['last_session']}",
            "",
            "IS is 2010–2021, Validation is 2022–2024, OOS is 2025–2026, by the session year. "
            "Each sample is sequenced on its own. A streak does not continue across a sample boundary.",
            "",
            "## 4. Bull and bear base rates",
            "",
            "Rates use every session in the sample, including flats, as the denominator.",
            "",
            _base_line(rates["All"]),
            "",
            f"IS: {_base_line(rates['IS'])}",
            "",
            f"Validation: {_base_line(rates['Validation'])}",
            "",
            f"OOS: {_base_line(rates['OOS'])}",
            "",
            "## 5–10. Distribution, continuation, null, and asymmetry",
            "",
            "Lift is observed continuation minus the matched base, in percentage points. "
            "The bull matched base is the sample bull rate. The bear matched base is the sample bear rate. "
            "The pooled matched base weights those two rates by the bull and bear observations inside the bucket. "
            "The permutation shuffles labels and keeps the bull, bear, and flat counts. "
            "10,000 draws, seed 49, one-sided p_ge = share of draws at least as large as the observed count.",
            "",
            *sample_blocks,
            "## 11. Year by year",
            "",
            "Each year is its own sequence. A continuation cell is NA when that cell has fewer than 5 observations. "
            "The year clause in the verdict uses pooled lengths 2 and 3 and ignores a year cell with n < 20.",
            "",
            _year_table(years),
            "",
            "## 12. Interpretation",
            "",
            "Long runs of green or red days are expected once the base rate is above one half. "
            "The permutation asks whether the observed run counts still stand out after that base rate is locked in. "
            "The continuation table asks whether a streak that has already reached length 2 or 3 is more likely to extend "
            "than the base rate. Length 1 answers a different question and is not used to pass the test.",
            "",
            "## 13. Verdict",
            "",
            str(verdict["verdict"]),
            "",
            str(verdict["lead"]),
            "",
            "This file does not contain an entry, a stop, or a P&L.",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
