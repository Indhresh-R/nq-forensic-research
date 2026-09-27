"""Verdict from the preregistered clauses. No threshold is added after the run."""
from __future__ import annotations

import math

import pandas as pd

from frozen import (
    FULL_MIN_N,
    NULL_FULL,
    NULL_OOS,
    OOS_MIN_N,
    P_GE_MAX,
    VERDICT_BUCKETS,
    YEAR_MIN_N,
    YEAR_MIN_POSITIVE,
)


def above_null(row: pd.Series) -> bool:
    if row.empty or pd.isna(row["p_ge"]) or pd.isna(row["null_mean"]):
        return False
    return float(row["observed"]) > float(row["null_mean"]) and float(row["p_ge"]) <= P_GE_MAX


def _null_row(table: pd.DataFrame, sample: str, statistic: str) -> pd.Series:
    chosen = table.loc[(table["sample"] == sample) & (table["statistic"] == statistic)]
    if chosen.empty:
        return pd.Series(dtype=object)
    return chosen.iloc[0]


def _cont_row(table: pd.DataFrame, sample: str, bucket: str) -> pd.Series:
    chosen = table.loc[
        (table["sample"] == sample) & (table["side"] == "pooled") & (table["bucket"] == bucket)
    ]
    if chosen.empty:
        return pd.Series(dtype=object)
    return chosen.iloc[0]


def _lift_holds(row: pd.Series, min_n: int) -> tuple[bool, str]:
    if row.empty or pd.isna(row.get("n", math.nan)):
        return False, "missing"
    n = int(row["n"])
    if n < min_n:
        return False, f"n={n} below {min_n}"
    lift = row["lift_pp"]
    if pd.isna(lift) or float(lift) <= 0.0:
        shown = "NA" if pd.isna(lift) else f"{float(lift):.2f}"
        return False, f"lift {shown} pp is not positive (n={n})"
    return True, f"lift {float(lift):.2f} pp (n={n})"


def judge(continuation: pd.DataFrame, nulls: pd.DataFrame, years: pd.DataFrame) -> dict[str, object]:
    full_flags = []
    for statistic in NULL_FULL:
        row = _null_row(nulls, "All", statistic)
        holds = above_null(row)
        detail = "missing" if row.empty else f"observed {int(row['observed'])}, null mean {float(row['null_mean']):.2f}, p_ge {float(row['p_ge']):.4f}"
        full_flags.append((statistic, holds, detail))
    clause_a_full = all(holds for _, holds, _ in full_flags)

    oos_row = _null_row(nulls, "OOS", NULL_OOS)
    clause_a_oos = above_null(oos_row)
    oos_detail = "missing" if oos_row.empty else (
        f"observed {int(oos_row['observed'])}, null mean {float(oos_row['null_mean']):.2f}, p_ge {float(oos_row['p_ge']):.4f}"
    )

    full_lifts = [_lift_holds(_cont_row(continuation, "All", bucket), FULL_MIN_N) for bucket in VERDICT_BUCKETS]
    clause_b = all(holds for holds, _ in full_lifts)

    oos_lifts = [_lift_holds(_cont_row(continuation, "OOS", bucket), OOS_MIN_N) for bucket in VERDICT_BUCKETS]
    oos_n_ok = all(not reason.startswith("n=") and reason != "missing" for _, reason in oos_lifts)
    clause_c = all(holds for holds, _ in oos_lifts)

    year_counts: list[tuple[str, int]] = []
    for bucket, column, n_column in (
        ("2", "pooled_lift_after_2", "n_pooled_after_2"),
        ("3", "pooled_lift_after_3", "n_pooled_after_3"),
    ):
        eligible = years.loc[years[n_column] >= YEAR_MIN_N]
        positives = int(np_positive(eligible[column]))
        year_counts.append((bucket, positives))
    clause_d = all(count >= YEAR_MIN_POSITIVE for _, count in year_counts)

    if clause_a_full and clause_a_oos and clause_b and clause_c and clause_d:
        verdict = "REAL MECHANISM"
        lead = "REAL MECHANISM. The preregistered null, continuation, OOS, and year clauses all hold."
    elif (not clause_a_full) or (not clause_b) or (oos_n_ok and not clause_c):
        verdict = "NOT REAL"
        lead = "NOT REAL. The preregistered null or matched-base continuation test does not show persistence."
    else:
        verdict = "INCONCLUSIVE"
        lead = "INCONCLUSIVE. The full-sample result is not confirmed under the remaining preregistered clauses."

    lines = [
        f"Clause A full null: {'pass' if clause_a_full else 'fail'}. "
        + "; ".join(f"{name} {detail}" for name, _, detail in full_flags),
        f"Clause A OOS null ({NULL_OOS}): {'pass' if clause_a_oos else 'fail'}. {oos_detail}",
        "Clause B All L=2 and L=3: "
        + ("pass. " if clause_b else "fail. ")
        + "; ".join(reason for _, reason in full_lifts),
        "Clause C OOS L=2 and L=3: "
        + ("pass. " if clause_c else "fail. ")
        + "; ".join(reason for _, reason in oos_lifts),
        "Clause D years: "
        + ("pass. " if clause_d else "fail. ")
        + "; ".join(f"L={bucket} positive years {count}" for bucket, count in year_counts),
    ]
    return {
        "verdict": verdict,
        "lead": lead,
        "lines": lines,
        "clause_a_full": clause_a_full,
        "clause_a_oos": clause_a_oos,
        "clause_b": clause_b,
        "clause_c": clause_c,
        "clause_d": clause_d,
    }


def np_positive(values: pd.Series) -> int:
    numeric = pd.to_numeric(values, errors="coerce")
    return int((numeric > 0).sum())
