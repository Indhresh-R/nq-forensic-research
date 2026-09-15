"""
Strategy 39: Multi-Day Volatility Compression -> RTH Expansion & Persistence
Systematic Information Scan across continuous NQ 1-minute futures (2010-2026).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from common.nq_session import load_nq
from common.splits import split_of

ARTIFACTS = ROOT / "artifacts" / "39_multi_day_volatility_compression"
RESULTS_DIR = ROOT / "strategies" / "39_multi_day_volatility_compression" / "results"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30   # 09:30
RTH_CLOSE = 15 * 60 + 55 # 15:55


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Computes rolling percentile rank (0.0 to 1.0) strictly using historical window."""
    vals = series.to_numpy()
    n = len(vals)
    pctls = np.full(n, np.nan)
    for i in range(window, n):
        w = vals[i - window : i] # strictly prior window
        curr = vals[i]
        valid_w = w[np.isfinite(w)]
        if len(valid_w) >= 50 and np.isfinite(curr):
            pctls[i] = (valid_w <= curr).mean()
    return pd.Series(pctls, index=series.index)


def count_consecutive_contracting(ranges: np.ndarray) -> np.ndarray:
    """Counts consecutive days of strictly decreasing daily range prior to today."""
    n = len(ranges)
    counts = np.zeros(n, dtype=int)
    for i in range(1, n):
        c = 0
        j = i - 1
        while j >= 1 and ranges[j] < ranges[j - 1]:
            c += 1
            j -= 1
        counts[i] = c
    return counts


def count_compression_duration(ranges: np.ndarray, medians: np.ndarray) -> np.ndarray:
    """Counts consecutive prior days where range < median."""
    n = len(ranges)
    counts = np.zeros(n, dtype=int)
    for i in range(1, n):
        c = 0
        j = i - 1
        while j >= 0 and np.isfinite(medians[j]) and ranges[j] < medians[j]:
            c += 1
            j -= 1
        counts[i] = c
    return counts


def main():
    print("=" * 80)
    print("STRATEGY 39: MULTI-DAY VOLATILITY COMPRESSION INFORMATION SCAN (2010-2026)")
    print("=" * 80)

    print("Loading continuous NQ 1-minute dataset...")
    nq = load_nq()
    print(f"Loaded {len(nq):,} bars across {nq['session_date'].nunique():,} sessions.")

    # 1. Separate RTH data per session_date
    sessions = sorted(nq["session_date"].unique())
    grouped = {sd: g for sd, g in nq.groupby("session_date", sort=True)}

    raw_summaries = []
    for sd in sessions:
        g = grouped[sd]
        rth_g = g[(g.ny_min >= RTH_OPEN) & (g.ny_min <= RTH_CLOSE)]
        if len(rth_g) < 300: # incomplete session
            continue

        rth_open = float(rth_g["open"].iloc[0])
        rth_high = float(rth_g["high"].max())
        rth_low = float(rth_g["low"].min())
        rth_close = float(rth_g["close"].iloc[-1])
        rth_vol = int(rth_g["volume"].sum())
        yr = int(rth_g["year"].iloc[0])

        raw_summaries.append({
            "session_date": sd,
            "year": yr,
            "split": split_of(yr),
            "rth_open": rth_open,
            "rth_high": rth_high,
            "rth_low": rth_low,
            "rth_close": rth_close,
            "rth_range": rth_high - rth_low,
            "rth_return": rth_close - rth_open,
            "rth_volume": rth_vol,
        })

    df = pd.DataFrame(raw_summaries).sort_values("session_date").reset_index(drop=True)
    print(f"Aggregated {len(df):,} valid complete RTH sessions.")

    # 2. Historical metrics strictly known at t <= 09:29 ET
    df["prev_high"] = df["rth_high"].shift(1)
    df["prev_low"] = df["rth_low"].shift(1)
    df["prev_range"] = df["rth_range"].shift(1)
    df["prev2_high"] = df["rth_high"].shift(2)
    df["prev2_low"] = df["rth_low"].shift(2)
    df["prev2_range"] = df["rth_range"].shift(2)

    # Moving averages and medians of range (strictly lagged)
    df["atr20"] = df["prev_range"].rolling(20, min_periods=10).mean()
    df["med20"] = df["prev_range"].rolling(20, min_periods=10).median()
    df["range_3d"] = df["prev_range"].rolling(3, min_periods=3).mean()
    df["range_5d"] = df["prev_range"].rolling(5, min_periods=5).mean()
    df["range_10d"] = df["prev_range"].rolling(10, min_periods=10).mean()

    # 3. Rolling 252-day percentiles
    print("Computing trailing 252-day percentiles (strictly causal)...")
    df["pctl_range3d"] = rolling_percentile(df["range_3d"], window=252)
    df["pctl_range5d"] = rolling_percentile(df["range_5d"], window=252)
    df["pctl_range10d"] = rolling_percentile(df["range_10d"], window=252)
    df["pctl_atr20"] = rolling_percentile(df["atr20"], window=252)

    # 4. Narrow Range structural patterns
    # NR4: prev_range < min of 3 prior ranges
    r = df["rth_range"].to_numpy()
    n_sess = len(df)
    is_nr4 = np.zeros(n_sess, dtype=bool)
    is_nr7 = np.zeros(n_sess, dtype=bool)
    is_inside_day = np.zeros(n_sess, dtype=bool)

    h = df["rth_high"].to_numpy()
    l = df["rth_low"].to_numpy()

    for i in range(7, n_sess):
        # session t: prev day is i-1
        p_r = r[i - 1]
        # NR4: r[i-1] < min(r[i-2], r[i-3], r[i-4])
        if p_r < np.min(r[i - 4 : i - 1]):
            is_nr4[i] = True
        # NR7: r[i-1] < min(r[i-7 : i-1])
        if p_r < np.min(r[i - 7 : i - 1]):
            is_nr7[i] = True
        # Inside day: h[i-1] <= h[i-2] and l[i-1] >= l[i-2]
        if h[i - 1] <= h[i - 2] and l[i - 1] >= l[i - 2]:
            is_inside_day[i] = True

    df["is_nr4"] = is_nr4
    df["is_nr7"] = is_nr7
    df["is_inside_day"] = is_inside_day
    df["is_id_nr4"] = is_inside_day & is_nr4
    df["is_id_nr7"] = is_inside_day & is_nr7

    # 5. Consecutive Contracting Days & Compression Duration
    df["contracting_days"] = count_consecutive_contracting(r)
    df["compression_duration"] = count_compression_duration(r, df["med20"].to_numpy())

    # 6. Current Range to 20-Day Median Ratio
    df["range_to_med20"] = df["prev_range"] / df["med20"]

    # 7. Dependent Target Metrics (Session t)
    df["norm_range"] = df["rth_range"] / df["atr20"]
    df["norm_abs_return"] = df["rth_return"].abs() / df["atr20"]
    df["efficiency"] = df["rth_return"].abs() / df["rth_range"]
    df["trend_day"] = (df["norm_range"] >= 1.0) & (df["efficiency"] >= 0.60)
    df["high_trend_day"] = (df["norm_range"] >= 1.25) & (df["efficiency"] >= 0.70)
    df["exp_125"] = df["norm_range"] >= 1.25
    df["exp_150"] = df["norm_range"] >= 1.50
    df["upside_exc"] = (df["rth_high"] - df["rth_open"]) / df["atr20"]
    df["downside_exc"] = (df["rth_open"] - df["rth_low"]) / df["atr20"]
    df["max_exc"] = np.maximum(df["upside_exc"], df["downside_exc"])
    df["close_loc"] = (df["rth_close"] - df["rth_low"]) / df["rth_range"]
    df["pinned_close"] = (df["close_loc"] <= 0.20) | (df["close_loc"] >= 0.80)

    # Drop warm-up rows (first 252 sessions for valid percentile ranks)
    clean_df = df.dropna(subset=["pctl_range3d", "pctl_range5d", "pctl_range10d", "pctl_atr20", "range_to_med20"]).copy().reset_index(drop=True)
    print(f"Clean analysis dataset contains {len(clean_df):,} sessions (from {clean_df['session_date'].iloc[0]} to {clean_df['session_date'].iloc[-1]}).")

    # 8. Quantile Binnings
    clean_df["bin_range3d"] = pd.cut(
        clean_df["pctl_range3d"],
        bins=[-0.01, 0.20, 0.40, 0.60, 0.80, 1.01],
        labels=["Q1_DEEP_COMP", "Q2_MILD_COMP", "Q3_NORMAL", "Q4_MILD_EXP", "Q5_DEEP_EXP"]
    )
    clean_df["bin_range5d"] = pd.cut(
        clean_df["pctl_range5d"],
        bins=[-0.01, 0.20, 0.40, 0.60, 0.80, 1.01],
        labels=["Q1_DEEP_COMP", "Q2_MILD_COMP", "Q3_NORMAL", "Q4_MILD_EXP", "Q5_DEEP_EXP"]
    )
    clean_df["bin_range10d"] = pd.cut(
        clean_df["pctl_range10d"],
        bins=[-0.01, 0.20, 0.40, 0.60, 0.80, 1.01],
        labels=["Q1_DEEP_COMP", "Q2_MILD_COMP", "Q3_NORMAL", "Q4_MILD_EXP", "Q5_DEEP_EXP"]
    )
    clean_df["bin_atr20"] = pd.cut(
        clean_df["pctl_atr20"],
        bins=[-0.01, 0.20, 0.40, 0.60, 0.80, 1.01],
        labels=["Q1_DEEP_COMP", "Q2_MILD_COMP", "Q3_NORMAL", "Q4_MILD_EXP", "Q5_DEEP_EXP"]
    )
    clean_df["bin_range_to_med"] = pd.cut(
        clean_df["range_to_med20"],
        bins=[-np.inf, 0.65, 1.20, np.inf],
        labels=["COMPRESSED (<0.65)", "NORMAL (0.65-1.20)", "EXPANDED (>1.20)"]
    )
    clean_df["bin_contracting"] = pd.cut(
        clean_df["contracting_days"],
        bins=[-1, 0, 1, 2, 3, 100],
        labels=["0_DAYS", "1_DAY", "2_DAYS", "3_DAYS", "4+_DAYS"]
    )
    clean_df["bin_duration"] = pd.cut(
        clean_df["compression_duration"],
        bins=[-1, 0, 1, 2, 3, 100],
        labels=["0_DAYS", "1_DAY", "2_DAYS", "3_DAYS", "4+_DAYS"]
    )

    # Categorical structural pattern
    def categorize_nr(row):
        if row["is_id_nr7"]:
            return "ID_NR7"
        if row["is_id_nr4"]:
            return "ID_NR4"
        if row["is_nr7"]:
            return "NR7"
        if row["is_nr4"]:
            return "NR4"
        if row["is_inside_day"]:
            return "INSIDE_DAY"
        return "NORMAL"

    clean_df["pattern_nr"] = clean_df.apply(categorize_nr, axis=1)

    # Save Parquet
    parquet_path = ARTIFACTS / "volatility_compression_panel.parquet"
    clean_df.to_parquet(parquet_path, index=False)
    print(f"Saved complete volatility compression panel to {parquet_path}")

    # Helper function for generating summary tables
    def build_summary_table(df_sub: pd.DataFrame, group_col: str) -> pd.DataFrame:
        rows = []
        for split in ["IS", "Validation", "OOS", "OOS_2025", "OOS_2026", "ALL"]:
            if split == "ALL":
                sub = df_sub
            elif split == "OOS_2025":
                sub = df_sub[df_sub["year"] == 2025]
            elif split == "OOS_2026":
                sub = df_sub[df_sub["year"] == 2026]
            else:
                sub = df_sub[df_sub["split"] == split]
            total_n = len(sub)
            if total_n == 0:
                continue
            for cat, g in sub.groupby(group_col, observed=True):
                n = len(g)
                pct_days = (n / total_n) * 100
                rows.append({
                    "split": split,
                    group_col: str(cat),
                    "n_sessions": n,
                    "pct_days": round(pct_days, 1),
                    "mean_norm_range": round(float(g["norm_range"].mean()), 3),
                    "mean_norm_abs_ret": round(float(g["norm_abs_return"].mean()), 3),
                    "mean_efficiency": round(float(g["efficiency"].mean()), 3),
                    "trend_day_pct": round(float(g["trend_day"].mean()) * 100, 1),
                    "high_trend_pct": round(float(g["high_trend_day"].mean()) * 100, 1),
                    "exp_125_pct": round(float(g["exp_125"].mean()) * 100, 1),
                    "exp_150_pct": round(float(g["exp_150"].mean()) * 100, 1),
                    "mean_max_exc": round(float(g["max_exc"].mean()), 3),
                    "pinned_close_pct": round(float(g["pinned_close"].mean()) * 100, 1),
                })
        return pd.DataFrame(rows)

    # 9. Generate Audit Tables
    audit_range3d = build_summary_table(clean_df, "bin_range3d")
    audit_range5d = build_summary_table(clean_df, "bin_range5d")
    audit_range10d = build_summary_table(clean_df, "bin_range10d")
    audit_atr20 = build_summary_table(clean_df, "bin_atr20")
    audit_nr = build_summary_table(clean_df, "pattern_nr")
    audit_contracting = build_summary_table(clean_df, "bin_contracting")
    audit_duration = build_summary_table(clean_df, "bin_duration")
    audit_ratio = build_summary_table(clean_df, "bin_range_to_med")

    audit_range3d.to_csv(ARTIFACTS / "audit_range3d.csv", index=False)
    audit_range5d.to_csv(ARTIFACTS / "audit_range5d.csv", index=False)
    audit_range10d.to_csv(ARTIFACTS / "audit_range10d.csv", index=False)
    audit_atr20.to_csv(ARTIFACTS / "audit_atr20.csv", index=False)
    audit_nr.to_csv(ARTIFACTS / "audit_nr4_nr7.csv", index=False)
    audit_contracting.to_csv(ARTIFACTS / "audit_contracting_days.csv", index=False)
    audit_duration.to_csv(ARTIFACTS / "audit_compression_duration.csv", index=False)
    audit_ratio.to_csv(ARTIFACTS / "audit_range_to_median.csv", index=False)

    print("\n--- TABLE 1: 5-DAY RANGE PERCENTILE VS NEXT RTH EXPANSION & PERSISTENCE ---")
    print(audit_range5d.to_string(index=False))

    print("\n--- TABLE 2: NARROW RANGE PATTERNS (NR4 / NR7 / ID) VS NEXT RTH ---")
    print(audit_nr.to_string(index=False))

    print("\n--- TABLE 3: CONSECUTIVE CONTRACTING DAYS VS NEXT RTH ---")
    print(audit_contracting.to_string(index=False))

    print("\n--- TABLE 4: RANGE TO 20-DAY MEDIAN RATIO VS NEXT RTH ---")
    print(audit_ratio.to_string(index=False))

    # Baseline metrics across splits
    baselines = {}
    for split in ["IS", "Validation", "OOS", "OOS_2025", "OOS_2026", "ALL"]:
        if split == "ALL":
            sub = clean_df
        elif split == "OOS_2025":
            sub = clean_df[clean_df["year"] == 2025]
        elif split == "OOS_2026":
            sub = clean_df[clean_df["year"] == 2026]
        else:
            sub = clean_df[clean_df["split"] == split]
        if len(sub) == 0:
            continue
        baselines[split] = {
            "n_sessions": len(sub),
            "mean_norm_range": round(float(sub["norm_range"].mean()), 3),
            "mean_efficiency": round(float(sub["efficiency"].mean()), 3),
            "trend_day_pct": round(float(sub["trend_day"].mean()) * 100, 1),
            "high_trend_pct": round(float(sub["high_trend_day"].mean()) * 100, 1),
            "exp_125_pct": round(float(sub["exp_125"].mean()) * 100, 1),
            "exp_150_pct": round(float(sub["exp_150"].mean()) * 100, 1),
            "mean_max_exc": round(float(sub["max_exc"].mean()), 3),
        }

    summary_metrics = {
        "total_sessions": len(clean_df),
        "splits": baselines,
        "features_evaluated": [
            "bin_range3d", "bin_range5d", "bin_range10d", "bin_atr20",
            "pattern_nr", "bin_contracting", "bin_duration", "bin_range_to_med"
        ]
    }

    with open(RESULTS_DIR / "summary_metrics.json", "w") as f:
        json.dump(summary_metrics, f, indent=2)

    print("\nSummary metrics saved to:", RESULTS_DIR / "summary_metrics.json")
    print("=" * 80)


if __name__ == "__main__":
    main()

