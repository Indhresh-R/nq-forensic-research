"""Directional streaks and continuation rates. No market-data access."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from frozen import BEAR, BULL, BUCKETS, FLAT, SMALL_N, YEAR_DISPLAY_MIN_N


def direction_label(open_: float, close: float) -> int:
    """Body direction only. The prior close is not an input."""
    if close > open_:
        return BULL
    if close < open_:
        return BEAR
    return FLAT


def labels_from_ohlc(opens: np.ndarray, closes: np.ndarray) -> np.ndarray:
    labels = np.zeros(len(opens), dtype=np.int8)
    labels[closes > opens] = BULL
    labels[closes < opens] = BEAR
    return labels


def _bounds(labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(labels)
    if n == 0:
        empty = np.array([], dtype=np.int32)
        return empty, empty, np.array([], dtype=np.int8)
    change = np.ones(n, dtype=bool)
    change[1:] = labels[1:] != labels[:-1]
    starts = np.flatnonzero(change)
    ends = np.r_[starts[1:], n]
    return starts, ends, labels[starts]


def directional_runs(labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Bull and bear runs. A flat run is a break and is not returned."""
    starts, ends, directions = _bounds(labels)
    keep = directions != FLAT
    return directions[keep], (ends - starts)[keep], starts[keep], (ends - 1)[keep]


def base_rates(labels: np.ndarray) -> dict[str, float | int]:
    n = int(len(labels))
    n_bull = int(np.sum(labels == BULL))
    n_bear = int(np.sum(labels == BEAR))
    n_flat = int(np.sum(labels == FLAT))
    if n == 0:
        return {
            "n_sessions": 0,
            "n_bull": 0,
            "n_bear": 0,
            "n_flat": 0,
            "bull_rate": np.nan,
            "bear_rate": np.nan,
            "flat_rate": np.nan,
        }
    return {
        "n_sessions": n,
        "n_bull": n_bull,
        "n_bear": n_bear,
        "n_flat": n_flat,
        "bull_rate": n_bull / n,
        "bear_rate": n_bear / n,
        "flat_rate": n_flat / n,
    }


def count_stats(labels: np.ndarray) -> dict[str, int]:
    directions, lengths, _, _ = directional_runs(labels)

    def n_ge(side: int | None, minimum: int) -> int:
        if side is None:
            mask = lengths >= minimum
        else:
            mask = (directions == side) & (lengths >= minimum)
        return int(np.sum(mask))

    def longest(side: int) -> int:
        mask = directions == side
        if not np.any(mask):
            return 0
        return int(np.max(lengths[mask]))

    return {
        "max_bull": longest(BULL),
        "max_bear": longest(BEAR),
        "bull_ge_3": n_ge(BULL, 3),
        "bear_ge_3": n_ge(BEAR, 3),
        "bull_ge_4": n_ge(BULL, 4),
        "bear_ge_4": n_ge(BEAR, 4),
        "bull_ge_5": n_ge(BULL, 5),
        "bear_ge_5": n_ge(BEAR, 5),
        "pooled_ge_3": n_ge(None, 3),
        "pooled_ge_4": n_ge(None, 4),
        "pooled_ge_5": n_ge(None, 5),
    }


def _bucket_mask(lengths: np.ndarray, bucket: str) -> np.ndarray:
    if bucket == ">=7":
        return lengths >= 7
    return lengths == int(bucket)


def distribution_table(labels: np.ndarray, sample: str) -> pd.DataFrame:
    directions, lengths, _, _ = directional_runs(labels)
    total = int(len(lengths))
    rows: list[dict[str, object]] = []
    sides = (("pooled", None), ("bull", BULL), ("bear", BEAR))
    for side_name, side in sides:
        if side is None:
            side_mask = np.ones(total, dtype=bool)
        else:
            side_mask = directions == side
        side_n = int(np.sum(side_mask))
        for bucket in BUCKETS:
            chosen = side_mask & _bucket_mask(lengths, bucket) if total else np.array([], dtype=bool)
            n_streaks = int(np.sum(chosen)) if total else 0
            if n_streaks == 0:
                n_sessions = 0
            elif bucket == ">=7":
                n_sessions = int(np.sum(lengths[chosen]))
            else:
                n_sessions = n_streaks * int(bucket)
            rows.append(
                {
                    "sample": sample,
                    "side": side_name,
                    "bucket": bucket,
                    "n_streaks": n_streaks,
                    "pct_of_all_streaks": (n_streaks / total) if total else np.nan,
                    "pct_of_side_streaks": (n_streaks / side_n) if side_n else np.nan,
                    "n_sessions": n_sessions,
                }
            )
    return pd.DataFrame(rows)


def continuation_observations(labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Direction, length, and same-direction flag for every non-flat session with a next session."""
    n = len(labels)
    if n < 2:
        empty_i = np.array([], dtype=np.int8)
        empty_n = np.array([], dtype=np.int32)
        return empty_i, empty_n, empty_i
    change = np.ones(n, dtype=bool)
    change[1:] = labels[1:] != labels[:-1]
    run_start = np.maximum.accumulate(np.where(change, np.arange(n), 0))
    length_at = np.arange(n) - run_start + 1
    index = np.arange(n - 1)
    keep = labels[index] != FLAT
    direction = labels[index[keep]]
    length = length_at[index[keep]].astype(np.int32)
    continued = (labels[index[keep] + 1] == direction).astype(np.int8)
    return direction, length, continued


def continuation_table(labels: np.ndarray, sample: str) -> pd.DataFrame:
    rates = base_rates(labels)
    bull_rate = float(rates["bull_rate"])
    bear_rate = float(rates["bear_rate"])
    direction, length, continued = continuation_observations(labels)
    rows: list[dict[str, object]] = []
    sides = (("bull", BULL), ("bear", BEAR), ("pooled", None))
    for side_name, side in sides:
        for bucket in BUCKETS:
            chosen = _bucket_mask(length, bucket)
            if side is not None:
                chosen = chosen & (direction == side)
            n = int(np.sum(chosen))
            n_bull = int(np.sum(direction[chosen] == BULL)) if n else 0
            n_bear = int(np.sum(direction[chosen] == BEAR)) if n else 0
            if n == 0 or not np.isfinite(bull_rate):
                observed = np.nan
                matched = np.nan
                lift_pp = np.nan
            else:
                observed = float(np.mean(continued[chosen]))
                if side_name == "bull":
                    matched = bull_rate
                elif side_name == "bear":
                    matched = bear_rate
                else:
                    matched = (n_bull * bull_rate + n_bear * bear_rate) / n
                lift_pp = (observed - matched) * 100.0
            rows.append(
                {
                    "sample": sample,
                    "side": side_name,
                    "bucket": bucket,
                    "n": n,
                    "n_bull_observations": n_bull,
                    "n_bear_observations": n_bear,
                    "observed": observed,
                    "matched_base": matched,
                    "lift_pp": lift_pp,
                    "small_sample": n < SMALL_N,
                }
            )
    return pd.DataFrame(rows)


def asymmetry_table(labels: np.ndarray, sample: str) -> pd.DataFrame:
    directions, lengths, _, _ = directional_runs(labels)
    rows: list[dict[str, object]] = []
    for side_name, side in (("bull", BULL), ("bear", BEAR)):
        chosen = lengths[directions == side]
        if len(chosen) == 0:
            mean = np.nan
            median = np.nan
            maximum = 0
        else:
            mean = float(np.mean(chosen))
            median = float(np.median(chosen))
            maximum = int(np.max(chosen))
        rows.append(
            {
                "sample": sample,
                "side": side_name,
                "n_streaks": int(len(chosen)),
                "mean_length": mean,
                "median_length": median,
                "max_length": maximum,
            }
        )
    return pd.DataFrame(rows)


def streak_events(labels: np.ndarray, dates: list[date], sample: str) -> pd.DataFrame:
    directions, lengths, starts, ends = directional_runs(labels)
    columns = ["sample", "side", "length", "start_date", "end_date"]
    rows: list[dict[str, object]] = []
    for direction, length, start, end in zip(directions, lengths, starts, ends, strict=True):
        rows.append(
            {
                "sample": sample,
                "side": "bull" if int(direction) == BULL else "bear",
                "length": int(length),
                "start_date": dates[int(start)].isoformat(),
                "end_date": dates[int(end)].isoformat(),
            }
        )
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)


def _rate_or_na(n: int, observed: float) -> float:
    if n < YEAR_DISPLAY_MIN_N:
        return np.nan
    return observed


def year_row(labels: np.ndarray, year: int) -> dict[str, object]:
    rates = base_rates(labels)
    asymmetry = asymmetry_table(labels, str(year)).set_index("side")
    continuation = continuation_table(labels, str(year))

    def streak_stat(side: str, column: str) -> float:
        value = asymmetry.loc[side, column]
        if column != "max_length" and pd.isna(value):
            return np.nan
        return float(value)

    def continuation_rate(side: str, bucket: str) -> float:
        row = continuation.loc[(continuation["side"] == side) & (continuation["bucket"] == bucket)].iloc[0]
        return _rate_or_na(int(row["n"]), float(row["observed"]) if pd.notna(row["observed"]) else np.nan)

    def continuation_n(side: str, bucket: str) -> int:
        row = continuation.loc[(continuation["side"] == side) & (continuation["bucket"] == bucket)].iloc[0]
        return int(row["n"])

    return {
        "year": year,
        "n_sessions": int(rates["n_sessions"]),
        "bull_rate": rates["bull_rate"],
        "bear_rate": rates["bear_rate"],
        "avg_bull_streak": streak_stat("bull", "mean_length"),
        "median_bull_streak": streak_stat("bull", "median_length"),
        "max_bull_streak": int(asymmetry.loc["bull", "max_length"]),
        "avg_bear_streak": streak_stat("bear", "mean_length"),
        "median_bear_streak": streak_stat("bear", "median_length"),
        "max_bear_streak": int(asymmetry.loc["bear", "max_length"]),
        "bull_continuation_after_1": continuation_rate("bull", "1"),
        "bull_continuation_after_2": continuation_rate("bull", "2"),
        "bull_continuation_after_3": continuation_rate("bull", "3"),
        "bear_continuation_after_1": continuation_rate("bear", "1"),
        "bear_continuation_after_2": continuation_rate("bear", "2"),
        "bear_continuation_after_3": continuation_rate("bear", "3"),
        "n_bull_after_1": continuation_n("bull", "1"),
        "n_bull_after_2": continuation_n("bull", "2"),
        "n_bull_after_3": continuation_n("bull", "3"),
        "n_bear_after_1": continuation_n("bear", "1"),
        "n_bear_after_2": continuation_n("bear", "2"),
        "n_bear_after_3": continuation_n("bear", "3"),
        "pooled_lift_after_2": _pooled_lift(continuation, "2"),
        "pooled_lift_after_3": _pooled_lift(continuation, "3"),
        "n_pooled_after_2": continuation_n("pooled", "2"),
        "n_pooled_after_3": continuation_n("pooled", "3"),
    }


def _pooled_lift(table: pd.DataFrame, bucket: str) -> float:
    row = table.loc[(table["side"] == "pooled") & (table["bucket"] == bucket)].iloc[0]
    if pd.isna(row["lift_pp"]):
        return np.nan
    return float(row["lift_pp"])
