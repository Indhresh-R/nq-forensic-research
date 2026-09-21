"""Descriptive tables. No threshold search and no trade statistics."""
from __future__ import annotations

import numpy as np
import pandas as pd

from definitions import ALL_HORIZONS, BODY_BUCKETS, NO_PENETRATION, PENETRATION_BUCKETS
from verdict import spearman


def summarize(series: pd.Series) -> dict[str, float]:
    values = series.to_numpy(np.float64)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return {"n": 0, "mean": np.nan, "median": np.nan, "std": np.nan, "pct_positive": np.nan}
    std = float(np.std(values, ddof=1)) if len(values) > 1 else np.nan
    return {
        "n": int(len(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": std,
        "pct_positive": float(np.mean(values > 0.0) * 100.0),
    }


def _bucket_order(column: str) -> list[str]:
    if column == "max_penetration_bucket":
        return [NO_PENETRATION, *PENETRATION_BUCKETS]
    return list(PENETRATION_BUCKETS)


def forward_table(frame: pd.DataFrame, bucket_col: str, ret_prefix: str) -> pd.DataFrame:
    rows: list[dict] = []
    for bucket in _bucket_order(bucket_col):
        subset = frame[frame[bucket_col] == bucket]
        row: dict = {"bucket": bucket, "n_sessions": int(len(subset))}
        for horizon in ALL_HORIZONS:
            stats = summarize(subset[f"{ret_prefix}{horizon}"])
            row[f"{horizon}_n"] = stats["n"]
            row[f"{horizon}_median"] = stats["median"]
            row[f"{horizon}_mean"] = stats["mean"]
            row[f"{horizon}_std"] = stats["std"]
            row[f"{horizon}_pct_positive"] = stats["pct_positive"]
        if "retracement_minutes_from_open" in subset.columns and len(subset):
            minutes = subset["retracement_minutes_from_open"]
            row["median_minutes_from_open"] = float(np.nanmedian(minutes.to_numpy(np.float64)))
            remaining = subset["fwd_minutes_remaining"]
            row["median_minutes_remaining"] = float(np.nanmedian(remaining.to_numpy(np.float64)))
        rows.append(row)
    return pd.DataFrame(rows)


def excursion_table(frame: pd.DataFrame, bucket_col: str) -> pd.DataFrame:
    rows: list[dict] = []
    for bucket in _bucket_order(bucket_col):
        subset = frame[frame[bucket_col] == bucket]
        for horizon in ALL_HORIZONS:
            mfe = summarize(subset[f"fwd_mfe_{horizon}"])
            mae = summarize(subset[f"fwd_mae_{horizon}"])
            mfe_rng = summarize(subset[f"fwd_mfe_rng_{horizon}"])
            mae_rng = summarize(subset[f"fwd_mae_rng_{horizon}"])
            rows.append(
                {
                    "bucket": bucket,
                    "horizon": horizon,
                    "n": mfe["n"],
                    "mfe_median_pts": mfe["median"],
                    "mfe_mean_pts": mfe["mean"],
                    "mae_median_pts": mae["median"],
                    "mae_mean_pts": mae["mean"],
                    "mfe_median_rng": mfe_rng["median"],
                    "mae_median_rng": mae_rng["median"],
                }
            )
    return pd.DataFrame(rows)


def baseline_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    groups = {
        "all_eligible": frame,
        "retracement_only": frame[frame["qualified"]],
        "bullish": frame[frame["direction"] == "bullish"],
        "bearish": frame[frame["direction"] == "bearish"],
    }
    for name, subset in groups.items():
        for unit, prefix in (("points", "base_ret_"), ("range", "base_ret_rng_")):
            row: dict = {"sample": name, "unit": unit, "n_sessions": int(len(subset))}
            for horizon in ALL_HORIZONS:
                stats = summarize(subset[f"{prefix}{horizon}"])
                row[f"{horizon}_n"] = stats["n"]
                row[f"{horizon}_median"] = stats["median"]
                row[f"{horizon}_mean"] = stats["mean"]
                row[f"{horizon}_std"] = stats["std"]
                row[f"{horizon}_pct_positive"] = stats["pct_positive"]
            rows.append(row)
    return pd.DataFrame(rows)


def distribution_row(series: pd.Series) -> dict[str, float]:
    values = series.to_numpy(np.float64)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return {"n": 0}
    quantiles = np.quantile(values, [0.1, 0.25, 0.5, 0.75, 0.9])
    return {
        "n": int(len(values)),
        "mean": float(np.mean(values)),
        "p10": float(quantiles[0]),
        "p25": float(quantiles[1]),
        "p50": float(quantiles[2]),
        "p75": float(quantiles[3]),
        "p90": float(quantiles[4]),
    }


def structure_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Body-fraction buckets crossed with direction. Fixed bins only."""
    rows: list[dict] = []
    qualified = frame[frame["qualified"]]
    for direction in ("bullish", "bearish", "combined"):
        source = qualified if direction == "combined" else qualified[qualified["direction"] == direction]
        for bucket in BODY_BUCKETS:
            subset = source[source["body_bucket"] == bucket]
            ret = summarize(subset["fwd_ret_rng_30m"])
            rows.append(
                {
                    "direction": direction,
                    "body_bucket": bucket,
                    "n": ret["n"],
                    "median_retracement_pct": float(np.nanmedian(subset["retracement_penetration_pct"])) if len(subset) else np.nan,
                    "median_max_penetration_pct": float(np.nanmedian(subset["max_penetration_pct"])) if len(subset) else np.nan,
                    "median_30m_rng": ret["median"],
                    "mean_30m_rng": ret["mean"],
                    "pct_positive_30m": ret["pct_positive"],
                    "median_upper_wick_fraction": float(np.nanmedian(subset["previous_upper_wick_fraction"])) if len(subset) else np.nan,
                    "median_lower_wick_fraction": float(np.nanmedian(subset["previous_lower_wick_fraction"])) if len(subset) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def wick_associations(frame: pd.DataFrame) -> dict[str, float]:
    qualified = frame[frame["qualified"]]
    penetration = qualified["max_penetration_pct"].to_numpy(np.float64)
    forward = qualified["fwd_ret_rng_30m"].to_numpy(np.float64)
    upper = qualified["previous_upper_wick_fraction"].to_numpy(np.float64)
    lower = qualified["previous_lower_wick_fraction"].to_numpy(np.float64)
    body = qualified["previous_body_fraction"].to_numpy(np.float64)
    return {
        "spearman_body_vs_max_penetration": spearman(body, penetration),
        "spearman_upper_wick_vs_max_penetration": spearman(upper, penetration),
        "spearman_lower_wick_vs_max_penetration": spearman(lower, penetration),
        "spearman_body_vs_30m": spearman(body, forward),
        "spearman_upper_wick_vs_30m": spearman(upper, forward),
        "spearman_lower_wick_vs_30m": spearman(lower, forward),
    }


def year_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    qualified = frame[frame["qualified"]]
    for year, subset in qualified.groupby("year", sort=True):
        row: dict = {
            "year": int(year),
            "split": str(subset["split"].iloc[0]),
            "n": int(subset["fwd_ret_rng_30m"].notna().sum()),
            "spearman_30m": spearman(
                subset["retracement_penetration_pct"].to_numpy(np.float64),
                subset["fwd_ret_rng_30m"].to_numpy(np.float64),
            ),
        }
        for pool, label in (
            ("shallow_0_30", "shallow"),
            ("mid_30_75", "mid"),
            ("deep_gt_75", "deep"),
        ):
            stats = summarize(subset.loc[subset["retracement_pool"] == pool, "fwd_ret_rng_30m"])
            row[f"{label}_n"] = stats["n"]
            row[f"{label}_median_30m"] = stats["median"]
        rows.append(row)
    return pd.DataFrame(rows)


def sequence_frequency(frame: pd.DataFrame) -> pd.DataFrame:
    """How often the separation-then-retracement sequence occurs. Not a filter."""
    n_eligible = int(len(frame))
    rows: list[dict] = []
    for state in ("entered_before_separation", "separated_no_return", "retracement"):
        for direction in ("all", "bullish", "bearish"):
            subset = frame if direction == "all" else frame[frame["direction"] == direction]
            count = int((subset["sequence_state"] == state).sum())
            base = int(len(subset))
            rows.append(
                {
                    "item": state,
                    "direction": direction,
                    "n": count,
                    "share_of_direction": count / base if base else np.nan,
                }
            )
    usable = int(frame["qualified"].sum()) if n_eligible else 0
    rows.append(
        {
            "item": "retracement_with_forward_bar",
            "direction": "all",
            "n": usable,
            "share_of_direction": usable / n_eligible if n_eligible else np.nan,
        }
    )
    return pd.DataFrame(rows)


def duration_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Minutes from the separation bar to the later retracement bar."""
    rows: list[dict] = []
    events = frame[frame["sequence_state"] == "retracement"]
    for direction in ("all", "bullish", "bearish"):
        subset = events if direction == "all" else events[events["direction"] == direction]
        stats = distribution_row(subset["separation_duration_minutes"])
        for key in ("mean", "p10", "p25", "p50", "p75", "p90"):
            stats.setdefault(key, np.nan)
        stats["direction"] = direction
        stats["metric"] = "separation_duration_minutes"
        rows.append(stats)
        clock = distribution_row(subset["retracement_minutes_from_open"])
        for key in ("mean", "p10", "p25", "p50", "p75", "p90"):
            clock.setdefault(key, np.nan)
        clock["direction"] = direction
        clock["metric"] = "retracement_minutes_from_open"
        rows.append(clock)
    return pd.DataFrame(rows)

