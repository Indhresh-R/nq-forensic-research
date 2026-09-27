"""Mechanism plots. Display clipping is visual only and is not used in any table."""
from __future__ import annotations

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from definitions import FIGURES_DIR, PENETRATION_BUCKETS

DISPLAY_CAP = 150.0


def _events(panel: pd.DataFrame) -> pd.DataFrame:
    return panel[panel["sequence_state"] == "retracement"].copy()


def _qualified(panel: pd.DataFrame) -> pd.DataFrame:
    return panel[panel["qualified"]].copy()


def _save(figure: plt.Figure, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / name, dpi=140)
    plt.close(figure)


def plot_penetration_histograms(panel: pd.DataFrame) -> None:
    events = _events(panel)
    first = events["retracement_penetration_pct"].to_numpy(np.float64)
    maximum = panel["max_penetration_pct"].to_numpy(np.float64)
    first = first[np.isfinite(first)]
    maximum = maximum[np.isfinite(maximum)]

    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    axes[0].hist(np.clip(first, 0, DISPLAY_CAP), bins=30, color="#4C78A8", edgecolor="white")
    axes[0].set_title("Retracement penetration")
    axes[0].set_xlabel("Percent of close-to-extreme range (display capped at 150)")
    axes[0].set_ylabel("Sessions")
    axes[1].hist(np.clip(maximum, -20, DISPLAY_CAP), bins=30, color="#54A24B", edgecolor="white")
    axes[1].set_title("Maximum penetration")
    axes[1].set_xlabel("Percent of close-to-extreme range (display capped at 150)")
    _save(figure, "penetration_distributions.png")


def plot_separation_duration(panel: pd.DataFrame) -> None:
    events = _events(panel)
    minutes = events["separation_duration_minutes"].to_numpy(np.float64)
    minutes = minutes[np.isfinite(minutes)]
    figure, axis = plt.subplots(figsize=(8.2, 4.4))
    axis.hist(minutes, bins=40, color="#4C78A8", edgecolor="white")
    axis.set_xlabel("Minutes from clean separation to the retracement bar")
    axis.set_ylabel("Sessions")
    axis.set_title("How long separation lasts before the return")
    _save(figure, "separation_duration.png")


def plot_forward_vs_penetration(panel: pd.DataFrame) -> None:
    qualified = _qualified(panel)
    x = qualified["retracement_penetration_pct"].to_numpy(np.float64)
    y = qualified["fwd_ret_rng_30m"].to_numpy(np.float64)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    figure, axis = plt.subplots(figsize=(8.2, 4.6))
    axis.hexbin(np.clip(x, 0, DISPLAY_CAP), y, gridsize=35, cmap="Blues", mincnt=1)
    centers = []
    medians = []
    edges = (0, 10, 20, 30, 40, 50, 75, 100, 10_000)
    labels = PENETRATION_BUCKETS
    for left, right, _label in zip(edges[:-1], edges[1:], labels):
        if right == 100:
            inside = (x >= left) & (x <= right)
            center = 87.5
        elif right > 100:
            inside = x > 100
            center = 120
        else:
            inside = (x >= left) & (x < right)
            center = (left + right) / 2
        if int(inside.sum()) >= 20:
            centers.append(center)
            medians.append(float(np.median(y[inside])))
    axis.plot(centers, medians, color="#E45756", marker="o", linewidth=1.5, label="Bucket median")
    axis.axhline(0.0, color="#333333", linewidth=0.6)
    axis.set_xlabel("Retracement penetration % (display capped at 150)")
    axis.set_ylabel("30m forward return / previous-day range")
    axis.set_title("Forward return versus retracement penetration")
    axis.legend(frameon=False)
    _save(figure, "forward_vs_penetration.png")


def plot_median_by_bucket(normalized: pd.DataFrame) -> None:
    horizons = ("5m", "15m", "30m", "60m", "120m", "session_end")
    figure, axis = plt.subplots(figsize=(9.2, 4.8))
    x = np.arange(len(PENETRATION_BUCKETS))
    for horizon in horizons:
        medians = []
        for bucket in PENETRATION_BUCKETS:
            row = normalized[normalized["bucket"] == bucket]
            medians.append(float(row[f"{horizon}_median"].iloc[0]) if len(row) else np.nan)
        axis.plot(x, medians, marker="o", linewidth=1.2, label=horizon)
    axis.axhline(0.0, color="#333333", linewidth=0.6)
    axis.set_xticks(x)
    axis.set_xticklabels(PENETRATION_BUCKETS, rotation=30, ha="right")
    axis.set_ylabel("Median forward return / previous-day range")
    axis.set_title("Median forward return by retracement bucket")
    axis.legend(frameon=False, ncol=3, fontsize=8)
    _save(figure, "median_forward_by_bucket.png")


def plot_mfe_mae(excursions: pd.DataFrame) -> None:
    subset = excursions[excursions["horizon"] == "30m"]
    figure, axis = plt.subplots(figsize=(8.4, 4.6))
    x = np.arange(len(PENETRATION_BUCKETS))
    mfe = []
    mae = []
    for bucket in PENETRATION_BUCKETS:
        row = subset[subset["bucket"] == bucket]
        mfe.append(float(row["mfe_median_rng"].iloc[0]) if len(row) else np.nan)
        mae.append(float(row["mae_median_rng"].iloc[0]) if len(row) else np.nan)
    width = 0.38
    axis.bar(x - width / 2, mfe, width=width, color="#54A24B", label="Median MFE")
    axis.bar(x + width / 2, mae, width=width, color="#E45756", label="Median MAE")
    axis.set_xticks(x)
    axis.set_xticklabels(PENETRATION_BUCKETS, rotation=30, ha="right")
    axis.set_ylabel("30m excursion / previous-day range")
    axis.set_title("MFE and MAE by retracement bucket")
    axis.legend(frameon=False)
    _save(figure, "mfe_mae_by_bucket.png")


def plot_bull_bear(panel: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 4.6))
    x = np.arange(len(PENETRATION_BUCKETS))
    for direction, color in (("bullish", "#4C78A8"), ("bearish", "#E45756")):
        medians = []
        subset = panel[(panel["qualified"]) & (panel["direction"] == direction)]
        for bucket in PENETRATION_BUCKETS:
            values = subset.loc[subset["retracement_bucket"] == bucket, "fwd_ret_rng_30m"].to_numpy(np.float64)
            values = values[np.isfinite(values)]
            medians.append(float(np.median(values)) if len(values) else np.nan)
        axis.plot(x, medians, marker="o", color=color, label=direction)
    axis.axhline(0.0, color="#333333", linewidth=0.6)
    axis.set_xticks(x)
    axis.set_xticklabels(PENETRATION_BUCKETS, rotation=30, ha="right")
    axis.set_ylabel("Median 30m return / previous-day range")
    axis.set_title("Bullish versus bearish previous days")
    axis.legend(frameon=False)
    _save(figure, "bull_vs_bear.png")


def plot_year_stability(yearly: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(9.0, 4.6))
    axis.plot(yearly["year"], yearly["shallow_median_30m"], marker="o", color="#4C78A8", label="Shallow 0–30%")
    axis.plot(yearly["year"], yearly["deep_median_30m"], marker="o", color="#F58518", label="Deep >75%")
    axis.axhline(0.0, color="#333333", linewidth=0.6)
    axis.set_xlabel("Year of the following session")
    axis.set_ylabel("Median 30m return / previous-day range")
    axis.set_title("Year-by-year shallow versus deep retracement")
    axis.legend(frameon=False)
    _save(figure, "year_stability.png")
