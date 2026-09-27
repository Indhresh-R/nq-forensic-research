"""Run the daily-candle continuation information test. Read-only on market data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE_DIR))

from candles import load_candles  # noqa: E402
from definitions import PRIMARY, RESULTS_DIR, SECONDARY  # noqa: E402
from report import write_report  # noqa: E402
from score import agreement_table, metrics_table  # noqa: E402
from state_machine import build_forecasts  # noqa: E402
from verdict import judge  # noqa: E402


def _check_always_long(frame: pd.DataFrame) -> None:
    body = frame["body"].to_numpy(dtype=np.float64)
    primary = frame["primary_sign"].to_numpy(dtype=np.int8)
    hit = float(np.mean((primary == 1)))
    always_hit = float(np.mean(frame["always_long_sign"].to_numpy() == primary))
    # Flats are misses, so Always Long hit rate equals P(Up), not P(not Down).
    if abs(always_hit - hit) > 1e-12:
        raise RuntimeError("Always Long hit rate does not equal P(Up)")
    signed = frame["always_long_sign"].to_numpy(dtype=np.float64) * body
    if abs(float(np.mean(signed)) - float(np.mean(body))) > 1e-9:
        raise RuntimeError("Always Long mean signed body does not equal mean body")


def main() -> None:
    candles, audit = load_candles()
    first = build_forecasts(candles)
    second = build_forecasts(candles)
    if not first.equals(second):
        raise RuntimeError("forecast rebuild was not identical")
    _check_always_long(first)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    first.to_csv(RESULTS_DIR / "forecasts.csv", index=False)
    primary = metrics_table(first, PRIMARY)
    secondary = metrics_table(first, SECONDARY)
    agree_primary = agreement_table(first, PRIMARY)
    agree_secondary = agreement_table(first, SECONDARY)
    primary.to_csv(RESULTS_DIR / "metrics_primary.csv", index=False)
    secondary.to_csv(RESULTS_DIR / "metrics_secondary.csv", index=False)
    agree_primary.to_csv(RESULTS_DIR / "agreement_primary.csv", index=False)
    agree_secondary.to_csv(RESULTS_DIR / "agreement_secondary.csv", index=False)
    decision = judge(primary, agree_primary)
    write_report(
        RESULTS_DIR / "full_report.md",
        audit,
        primary,
        secondary,
        agree_primary,
        agree_secondary,
        decision,
    )
    print(decision["verdict"])
    print(decision["lead"])
    print(decision["flip_line"])
    print(decision["long_line"])
    print(f"sessions={audit['n_complete']} forecasts={len(first)}")


if __name__ == "__main__":
    main()
