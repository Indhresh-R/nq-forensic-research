"""Hand-built streak tests. No market data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE_DIR))

from frozen import N_PERM, SEED  # noqa: E402
from nulls import null_table  # noqa: E402
from streaks import (  # noqa: E402
    base_rates,
    continuation_table,
    count_stats,
    direction_label,
    directional_runs,
    distribution_table,
)
from verdict import above_null, judge  # noqa: E402


EXAMPLE = np.array([1, 1, 1, -1, -1, 1, 1, 1, 1, -1], dtype=np.int8)


def test_direction_ignores_prior_close() -> None:
    assert direction_label(100, 101) == 1
    assert direction_label(100, 99) == -1
    assert direction_label(100, 100) == 0


def test_example_runs() -> None:
    directions, lengths, _, _ = directional_runs(EXAMPLE)
    assert list(directions) == [1, -1, 1, -1]
    assert list(lengths) == [3, 2, 4, 1]
    stats = count_stats(EXAMPLE)
    assert stats["max_bull"] == 4
    assert stats["max_bear"] == 2
    assert stats["pooled_ge_3"] == 2
    assert stats["pooled_ge_4"] == 1
    assert stats["pooled_ge_5"] == 0
    assert stats["bull_ge_3"] == 2
    assert stats["bear_ge_3"] == 0
    assert stats["bear_ge_5"] == 0


def test_flat_breaks_the_streak() -> None:
    labels = np.array([1, 1, 0, 1, -1], dtype=np.int8)
    directions, lengths, _, _ = directional_runs(labels)
    assert list(directions) == [1, 1, -1]
    assert list(lengths) == [2, 1, 1]
    table = continuation_table(labels, "toy")
    bull_l1 = table.loc[(table["side"] == "bull") & (table["bucket"] == "1")].iloc[0]
    bull_l2 = table.loc[(table["side"] == "bull") & (table["bucket"] == "2")].iloc[0]
    assert int(bull_l1["n"]) == 2
    assert abs(float(bull_l1["observed"]) - 0.5) < 1e-12
    assert int(bull_l2["n"]) == 1
    assert float(bull_l2["observed"]) == 0.0


def test_example_continuation_lift() -> None:
    table = continuation_table(EXAMPLE, "toy")
    bull_l3 = table.loc[(table["side"] == "bull") & (table["bucket"] == "3")].iloc[0]
    assert int(bull_l3["n"]) == 2
    assert abs(float(bull_l3["observed"]) - 0.5) < 1e-12
    assert abs(float(bull_l3["matched_base"]) - 0.7) < 1e-12
    assert abs(float(bull_l3["lift_pp"]) - (-20.0)) < 1e-9
    rates = base_rates(EXAMPLE)
    assert rates["n_bull"] == 7
    assert rates["n_bear"] == 3
    assert rates["n_flat"] == 0
    pooled = distribution_table(EXAMPLE, "toy")
    all_streaks = int(pooled.loc[pooled["side"] == "pooled", "n_streaks"].sum())
    assert all_streaks == 4
    sessions = int(pooled.loc[(pooled["side"] == "bull") & (pooled["bucket"] == "4"), "n_sessions"].iloc[0])
    assert sessions == 4


def test_permutation_preserves_counts_and_seed() -> None:
    labels = EXAMPLE.copy()
    first = null_table(labels, "toy", n_perm=30, seed=SEED)
    second = null_table(labels, "toy", n_perm=30, seed=SEED)
    pd.testing.assert_frame_equal(first, second)
    assert list(labels) == list(EXAMPLE)
    row = first.loc[first["statistic"] == "pooled_ge_3"].iloc[0]
    assert int(row["observed"]) == 2
    assert int(row["n_perm"]) == 30
    assert N_PERM == 10_000
    assert SEED == 49


def _null_row(sample: str, statistic: str, observed: int, null_mean: float, p_ge: float) -> dict[str, object]:
    return {
        "sample": sample,
        "statistic": statistic,
        "observed": observed,
        "null_mean": null_mean,
        "p_ge": p_ge,
    }


def _lift_row(sample: str, bucket: str, n: int, lift: float) -> dict[str, object]:
    return {"sample": sample, "side": "pooled", "bucket": bucket, "n": n, "lift_pp": lift}


def _years(l2: list[tuple[int, float]], l3: list[tuple[int, float]]) -> pd.DataFrame:
    rows = []
    for index, ((n2, lift2), (n3, lift3)) in enumerate(zip(l2, l3, strict=True)):
        rows.append(
            {
                "year": 2010 + index,
                "n_pooled_after_2": n2,
                "pooled_lift_after_2": lift2,
                "n_pooled_after_3": n3,
                "pooled_lift_after_3": lift3,
            }
        )
    return pd.DataFrame(rows)


def _passing_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nulls = pd.DataFrame(
        [
            _null_row("All", "pooled_ge_3", 20, 10, 0.01),
            _null_row("All", "pooled_ge_4", 12, 6, 0.02),
            _null_row("OOS", "pooled_ge_3", 8, 4, 0.03),
        ]
    )
    continuation = pd.DataFrame(
        [
            _lift_row("All", "2", 200, 1.5),
            _lift_row("All", "3", 150, 0.4),
            _lift_row("OOS", "2", 40, 1.0),
            _lift_row("OOS", "3", 35, 0.2),
        ]
    )
    years = _years([(25, 1.0), (22, 0.5), (21, 0.2), (10, 5.0)], [(30, 0.4), (24, 0.1), (20, 0.3), (5, 9.0)])
    return continuation, nulls, years


def test_verdict_real_not_real_and_inconclusive() -> None:
    continuation, nulls, years = _passing_inputs()
    assert judge(continuation, nulls, years)["verdict"] == "REAL MECHANISM"

    nulls.loc[nulls["statistic"] == "pooled_ge_3", "p_ge"] = 0.40
    failed_null = judge(continuation, nulls, years)
    assert failed_null["verdict"] == "NOT REAL"

    continuation, nulls, years = _passing_inputs()
    continuation.loc[(continuation["sample"] == "All") & (continuation["bucket"] == "2"), "lift_pp"] = -0.2
    assert judge(continuation, nulls, years)["verdict"] == "NOT REAL"

    continuation, nulls, years = _passing_inputs()
    continuation.loc[continuation["sample"] == "OOS", "lift_pp"] = -1.0
    assert judge(continuation, nulls, years)["verdict"] == "NOT REAL"

    continuation, nulls, years = _passing_inputs()
    continuation.loc[continuation["sample"] == "OOS", "n"] = 10
    assert judge(continuation, nulls, years)["verdict"] == "INCONCLUSIVE"

    continuation, nulls, years = _passing_inputs()
    years["pooled_lift_after_2"] = -1.0
    assert judge(continuation, nulls, years)["verdict"] == "INCONCLUSIVE"


def test_above_null_requires_both_conditions() -> None:
    assert above_null(pd.Series({"observed": 5, "null_mean": 4, "p_ge": 0.05}))
    assert not above_null(pd.Series({"observed": 5, "null_mean": 5, "p_ge": 0.01}))
    assert not above_null(pd.Series({"observed": 5, "null_mean": 4, "p_ge": 0.06}))


def main() -> None:
    test_direction_ignores_prior_close()
    test_example_runs()
    test_flat_breaks_the_streak()
    test_example_continuation_lift()
    test_permutation_preserves_counts_and_seed()
    test_verdict_real_not_real_and_inconclusive()
    test_above_null_requires_both_conditions()
    print("ok")


if __name__ == "__main__":
    main()
