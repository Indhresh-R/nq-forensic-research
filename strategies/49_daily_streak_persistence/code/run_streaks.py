"""Run the streak-persistence information test. Read-only on market data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE_DIR))

from common.splits import IS_YEARS, OOS_YEARS, VAL_YEARS  # noqa: E402
from frozen import N_PERM, REPORT_PATH, RESULTS_DIR, SAMPLES, SEED  # noqa: E402
from load_sessions import load_complete_candles  # noqa: E402
from nulls import null_table  # noqa: E402
from report import write_report  # noqa: E402
from streaks import (  # noqa: E402
    asymmetry_table,
    base_rates,
    continuation_table,
    distribution_table,
    labels_from_ohlc,
    streak_events,
    year_row,
)
from verdict import judge  # noqa: E402


def _labels(candles: list) -> np.ndarray:
    opens = np.array([candle.open for candle in candles], dtype=np.float64)
    closes = np.array([candle.close for candle in candles], dtype=np.float64)
    return labels_from_ohlc(opens, closes)


def _dates(candles: list):
    return [candle.session_date for candle in candles]


def main() -> None:
    candles, audit = load_complete_candles()
    groups = {
        "All": candles,
        "IS": [candle for candle in candles if candle.year in IS_YEARS],
        "Validation": [candle for candle in candles if candle.year in VAL_YEARS],
        "OOS": [candle for candle in candles if candle.year in OOS_YEARS],
    }
    rates = {name: base_rates(_labels(group)) for name, group in groups.items()}
    distribution = pd.concat([distribution_table(_labels(groups[name]), name) for name in SAMPLES], ignore_index=True)
    continuation = pd.concat([continuation_table(_labels(groups[name]), name) for name in SAMPLES], ignore_index=True)
    asymmetry = pd.concat([asymmetry_table(_labels(groups[name]), name) for name in SAMPLES], ignore_index=True)
    events = pd.concat(
        [streak_events(_labels(groups[name]), _dates(groups[name]), name) for name in SAMPLES],
        ignore_index=True,
    )
    null_frames = []
    for name in SAMPLES:
        print(f"permutations {name}", flush=True)
        null_frames.append(null_table(_labels(groups[name]), name, n_perm=N_PERM, seed=SEED))
    nulls = pd.concat(null_frames, ignore_index=True)
    years = sorted({candle.year for candle in candles})
    year_table = pd.DataFrame(
        [year_row(_labels([candle for candle in candles if candle.year == year]), year) for year in years]
    )
    decision = judge(continuation, nulls, year_table)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    distribution.to_csv(RESULTS_DIR / "streak_distribution.csv", index=False)
    continuation.to_csv(RESULTS_DIR / "continuation.csv", index=False)
    nulls.to_csv(RESULTS_DIR / "null_comparison.csv", index=False)
    asymmetry.to_csv(RESULTS_DIR / "asymmetry.csv", index=False)
    events.to_csv(RESULTS_DIR / "streaks.csv", index=False)
    year_table.to_csv(RESULTS_DIR / "year_table.csv", index=False)
    write_report(
        REPORT_PATH,
        audit,
        rates,
        distribution,
        continuation,
        nulls,
        asymmetry,
        year_table,
        decision,
    )
    print(decision["verdict"])
    print(decision["lead"])
    for line in decision["lines"]:
        print(line)


if __name__ == "__main__":
    main()
