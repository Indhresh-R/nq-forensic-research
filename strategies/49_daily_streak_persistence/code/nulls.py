"""Permutation null that keeps the observed bull, bear, and flat counts."""
from __future__ import annotations

import numpy as np
import pandas as pd

from frozen import N_PERM, SEED
from streaks import count_stats


STAT_ORDER = (
    "max_bull",
    "max_bear",
    "bull_ge_3",
    "bear_ge_3",
    "bull_ge_4",
    "bear_ge_4",
    "bull_ge_5",
    "bear_ge_5",
    "pooled_ge_3",
    "pooled_ge_4",
    "pooled_ge_5",
)


def null_table(labels: np.ndarray, sample: str, n_perm: int = N_PERM, seed: int = SEED) -> pd.DataFrame:
    observed = count_stats(labels)
    draws = {name: np.empty(n_perm, dtype=np.int32) for name in STAT_ORDER}
    rng = np.random.default_rng(seed)
    for i in range(n_perm):
        permuted = count_stats(rng.permutation(labels))
        for name in STAT_ORDER:
            draws[name][i] = permuted[name]
    rows: list[dict[str, object]] = []
    for name in STAT_ORDER:
        null = draws[name]
        obs = int(observed[name])
        p_ge = float(np.sum(null >= obs) / n_perm)
        percentile_rank = float(np.sum(null <= obs) / n_perm * 100.0)
        rows.append(
            {
                "sample": sample,
                "statistic": name,
                "observed": obs,
                "null_mean": float(np.mean(null)),
                "null_p50": float(np.median(null)),
                "null_p95": float(np.quantile(null, 0.95)),
                "percentile_rank": percentile_rank,
                "p_ge": p_ge,
                "n_perm": n_perm,
                "n_null_ge_observed": int(np.sum(null >= obs)),
            }
        )
    return pd.DataFrame(rows)
