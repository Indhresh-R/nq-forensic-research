"""
Strategy 40: Volatility Persistence -> Directional Distribution
Empirical scan testing whether high/low volatility regimes systematically condition
subsequent RTH direction, continuation, tail asymmetry, or excursion bias (2010-2026).
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

ARTIFACTS = ROOT / "artifacts" / "40_volatility_regime_direction"
RESULTS_DIR = ROOT / "strategies" / "40_volatility_regime_direction" / "results"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30   # 09:30
RTH_CLOSE = 15 * 60 + 55 # 15:55


def main():
    print("=" * 80)
    print("STRATEGY 40: VOLATILITY PERSISTENCE -> DIRECTIONAL SCAN (2010-2026)")
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
    df["prev_return"] = df["rth_return"].shift(1)

    # 20-day ATR and Median of Range (strictly lagged)
    df["atr20"] = df["prev_range"].rolling(20, min_periods=10).mean()
    df["med20"] = df["prev_range"].rolling(20, min_periods=10).median()

    # Normalized prior metrics
    df["norm_prev_range"] = df["prev_range"] / df["atr20"]
    df["norm_prev_return"] = df["prev_return"] / df["atr20"]
    df["ratio_med20"] = df["prev_range"] / df["med20"]

    # Drop warm-up rows
    clean_df = df.dropna(subset=["norm_prev_range", "norm_prev_return", "ratio_med20"]).copy().reset_index(drop=True)
    print(f"Clean analysis dataset contains {len(clean_df):,} sessions (from {clean_df['session_date'].iloc[0]} to {clean_df['session_date'].iloc[-1]}).")

    # 3. Categorize Conditioning States (t-1)
    # A. Volatility Scale Regimes
    clean_df["bin_vol_regime"] = pd.cut(
        clean_df["norm_prev_range"],
        bins=[-np.inf, 0.75, 1.25, 1.50, np.inf],
        labels=["LOW_VOL (<0.75)", "NORMAL_VOL (0.75-1.25)", "HIGH_VOL (1.25-1.50)", "EXTREME_VOL (>1.50)"]
    )

    clean_df["bin_range_to_med"] = pd.cut(
        clean_df["ratio_med20"],
        bins=[-np.inf, 0.65, 1.20, np.inf],
        labels=["COMPRESSED (<0.65)", "NORMAL (0.65-1.20)", "EXPANDED (>1.20)"]
    )

    # B. Prior Directional Displacement
    clean_df["bin_prev_dir"] = pd.cut(
        clean_df["norm_prev_return"],
        bins=[-np.inf, -0.75, -0.20, 0.20, 0.75, np.inf],
        labels=["LARGE_DOWN (<-0.75)", "MILD_DOWN (-0.75:-0.20)", "FLAT (-0.20:0.20)", "MILD_UP (0.20:0.75)", "LARGE_UP (>0.75)"]
    )

    # C. Interaction: Volatility x Direction
    def categorize_vol_x_dir(row):
        n_rng = row["norm_prev_range"]
        p_ret = row["prev_return"]
        if n_rng >= 1.25:
            return "HIGH_VOL_UP" if p_ret > 0 else "HIGH_VOL_DOWN"
        elif n_rng < 0.75:
            return "LOW_VOL_UP" if p_ret > 0 else "LOW_VOL_DOWN"
        else:
            return "NORMAL_VOL"

    clean_df["bin_vol_x_dir"] = clean_df.apply(categorize_vol_x_dir, axis=1)

    # 4. Compute Session t Directional Targets
    clean_df["norm_return"] = clean_df["rth_return"] / clean_df["atr20"]
    clean_df["is_up_day"] = clean_df["rth_return"] > 0
    clean_df["is_down_day"] = clean_df["rth_return"] < 0

    # Directional Continuation
    clean_df["continuation"] = np.where(
        (clean_df["prev_return"] > 0) & (clean_df["rth_return"] > 0), True,
        np.where((clean_df["prev_return"] < 0) & (clean_df["rth_return"] < 0), True, False)
    )
    clean_df["reversal"] = np.where(
        (clean_df["prev_return"] > 0) & (clean_df["rth_return"] < 0), True,
        np.where((clean_df["prev_return"] < 0) & (clean_df["rth_return"] > 0), True, False)
    )

    # Tail Moves
    clean_df["large_up_10"] = clean_df["norm_return"] >= 1.0
    clean_df["large_down_10"] = clean_df["norm_return"] <= -1.0
    clean_df["large_up_15"] = clean_df["norm_return"] >= 1.5
    clean_df["large_down_15"] = clean_df["norm_return"] <= -1.5

    # Excursions
    clean_df["upside_exc"] = (clean_df["rth_high"] - clean_df["rth_open"]) / clean_df["atr20"]
    clean_df["downside_exc"] = (clean_df["rth_open"] - clean_df["rth_low"]) / clean_df["atr20"]
    clean_df["exc_spread"] = clean_df["upside_exc"] - clean_df["downside_exc"]

    # Close Location
    clean_df["close_loc"] = (clean_df["rth_close"] - clean_df["rth_low"]) / clean_df["rth_range"]
    clean_df["bull_pin"] = clean_df["close_loc"] >= 0.80
    clean_df["bear_pin"] = clean_df["close_loc"] <= 0.20

    # Clean Trend Days
    clean_df["norm_range"] = clean_df["rth_range"] / clean_df["atr20"]
    clean_df["efficiency"] = clean_df["rth_return"].abs() / clean_df["rth_range"]
    clean_df["bull_trend"] = (clean_df["norm_range"] >= 1.0) & (clean_df["efficiency"] >= 0.60) & (clean_df["rth_return"] > 0)
    clean_df["bear_trend"] = (clean_df["norm_range"] >= 1.0) & (clean_df["efficiency"] >= 0.60) & (clean_df["rth_return"] < 0)

    # Save Parquet
    parquet_path = ARTIFACTS / "volatility_direction_panel.parquet"
    clean_df.to_parquet(parquet_path, index=False)
    print(f"Saved volatility direction panel to {parquet_path}")

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
                up_pct = float(g["is_up_day"].mean()) * 100
                cont_pct = float(g["continuation"].mean()) * 100
                l_up_pct = float(g["large_up_10"].mean()) * 100
                l_down_pct = float(g["large_down_10"].mean()) * 100
                tail_spread = l_up_pct - l_down_pct
                rows.append({
                    "split": split,
                    group_col: str(cat),
                    "n_sessions": n,
                    "pct_days": round(pct_days, 1),
                    "mean_ret_pts": round(float(g["rth_return"].mean()), 2),
                    "mean_norm_ret": round(float(g["norm_return"].mean()), 3),
                    "up_day_pct": round(up_pct, 1),
                    "continuation_pct": round(cont_pct, 1),
                    "large_up_pct": round(l_up_pct, 1),
                    "large_down_pct": round(l_down_pct, 1),
                    "tail_asym_pct": round(tail_spread, 1),
                    "mean_up_exc": round(float(g["upside_exc"].mean()), 3),
                    "mean_down_exc": round(float(g["downside_exc"].mean()), 3),
                    "exc_spread": round(float(g["exc_spread"].mean()), 3),
                    "bull_trend_pct": round(float(g["bull_trend"].mean()) * 100, 1),
                    "bear_trend_pct": round(float(g["bear_trend"].mean()) * 100, 1),
                })
        return pd.DataFrame(rows)

    # 5. Generate Audit Tables
    audit_vol_regime = build_summary_table(clean_df, "bin_vol_regime")
    audit_vol_x_dir = build_summary_table(clean_df, "bin_vol_x_dir")
    audit_prev_dir = build_summary_table(clean_df, "bin_prev_dir")
    audit_range_to_med = build_summary_table(clean_df, "bin_range_to_med")

    audit_vol_regime.to_csv(ARTIFACTS / "audit_vol_regime_direction.csv", index=False)
    audit_vol_x_dir.to_csv(ARTIFACTS / "audit_vol_x_dir_interaction.csv", index=False)
    audit_prev_dir.to_csv(ARTIFACTS / "audit_prev_return_to_next.csv", index=False)
    audit_range_to_med.to_csv(ARTIFACTS / "audit_range_to_med_direction.csv", index=False)

    print("\n--- TABLE 1: VOLATILITY REGIME VS NEXT RTH DIRECTIONAL DISTRIBUTION ---")
    print(audit_vol_regime.to_string(index=False))

    print("\n--- TABLE 2: VOLATILITY X DIRECTION INTERACTION VS NEXT RTH ---")
    print(audit_vol_x_dir.to_string(index=False))

    print("\n--- TABLE 3: PRIOR DAY RETURN (MOMENTUM / REVERSAL) VS NEXT RTH ---")
    print(audit_prev_dir.to_string(index=False))

    # Baselines across splits
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
        l_up = float(sub["large_up_10"].mean()) * 100
        l_down = float(sub["large_down_10"].mean()) * 100
        baselines[split] = {
            "n_sessions": len(sub),
            "mean_ret_pts": round(float(sub["rth_return"].mean()), 2),
            "mean_norm_ret": round(float(sub["norm_return"].mean()), 3),
            "up_day_pct": round(float(sub["is_up_day"].mean()) * 100, 1),
            "continuation_pct": round(float(sub["continuation"].mean()) * 100, 1),
            "large_up_pct": round(l_up, 1),
            "large_down_pct": round(l_down, 1),
            "tail_asym_pct": round(l_up - l_down, 1),
            "bull_trend_pct": round(float(sub["bull_trend"].mean()) * 100, 1),
            "bear_trend_pct": round(float(sub["bear_trend"].mean()) * 100, 1),
        }

    summary_metrics = {
        "total_sessions": len(clean_df),
        "baselines": baselines,
        "features_evaluated": ["bin_vol_regime", "bin_vol_x_dir", "bin_prev_dir", "bin_range_to_med"]
    }

    with open(RESULTS_DIR / "summary_metrics.json", "w") as f:
        json.dump(summary_metrics, f, indent=2)

    print("\nSummary metrics saved to:", RESULTS_DIR / "summary_metrics.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
