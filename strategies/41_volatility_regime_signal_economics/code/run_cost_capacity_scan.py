"""
Strategy 41 - Layer 1: Signal-Agnostic Cost Capacity Scan
Measures available price excursions vs fixed 1.0 pt round-trip friction across
pre-market volatility regimes in continuous NQ futures (2010-2026).
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

ARTIFACTS = ROOT / "artifacts" / "41_volatility_regime_signal_economics"
RESULTS_DIR = ROOT / "strategies" / "41_volatility_regime_signal_economics" / "results"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30    # 09:30
RTH_CLOSE = 15 * 60 + 55  # 15:55
M60_END = 10 * 60 + 35    # 10:35
M180_END = 12 * 60 + 35   # 12:35


def main():
    print("=" * 80)
    print("STRATEGY 41 - LAYER 1: SIGNAL-AGNOSTIC COST CAPACITY SCAN (2010-2026)")
    print("=" * 80)

    print("Loading continuous NQ 1-minute dataset...")
    nq = load_nq()
    sessions = sorted(nq["session_date"].unique())
    grouped = {sd: g for sd, g in nq.groupby("session_date", sort=True)}

    raw_summaries = []
    for sd in sessions:
        g = grouped[sd]
        rth_g = g[(g.ny_min >= RTH_OPEN) & (g.ny_min <= RTH_CLOSE)]
        if len(rth_g) < 300:
            continue

        o930 = float(rth_g["open"].iloc[0])
        h_rth = float(rth_g["high"].max())
        l_rth = float(rth_g["low"].min())
        c_rth = float(rth_g["close"].iloc[-1])
        yr = int(rth_g["year"].iloc[0])

        # 60m window (09:35 to 10:35)
        g_60m = rth_g[(rth_g.ny_min >= 9 * 60 + 35) & (rth_g.ny_min <= M60_END)]
        if len(g_60m) > 0:
            o935 = float(g_60m["open"].iloc[0])
            h_60m = float(g_60m["high"].max())
            l_60m = float(g_60m["low"].min())
            exc_60m = max(h_60m - o935, o935 - l_60m)
            rng_60m = h_60m - l_60m
        else:
            exc_60m, rng_60m = np.nan, np.nan

        # Full day open excursion
        exc_open = max(h_rth - o930, o930 - l_rth)
        rng_rth = h_rth - l_rth

        raw_summaries.append({
            "session_date": sd,
            "year": yr,
            "split": split_of(yr),
            "rth_range": rng_rth,
            "exc_open": exc_open,
            "exc_60m": exc_60m,
            "rng_60m": rng_60m,
        })

    df = pd.DataFrame(raw_summaries).sort_values("session_date").reset_index(drop=True)
    print(f"Aggregated {len(df):,} valid complete RTH sessions.")

    # Prior day metrics (known strictly at t-1)
    df["prev_range"] = df["rth_range"].shift(1)
    df["atr20"] = df["prev_range"].rolling(20, min_periods=10).mean()
    df["med20"] = df["prev_range"].rolling(20, min_periods=10).median()
    df["norm_prev_range"] = df["prev_range"] / df["atr20"]
    df["ratio_med20"] = df["prev_range"] / df["med20"]

    clean_df = df.dropna(subset=["norm_prev_range", "ratio_med20", "exc_60m"]).copy().reset_index(drop=True)
    print(f"Clean analysis dataset contains {len(clean_df):,} sessions.")

    # Volatility Regimes
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

    # Friction drag (fixed 1.0 pt round-trip)
    clean_df["drag_open_pct"] = (1.0 / clean_df["exc_open"]) * 100
    clean_df["drag_60m_pct"] = (1.0 / clean_df["exc_60m"]) * 100

    # Excursion thresholds
    for pt in [20, 40, 60, 80, 100, 150]:
        clean_df[f"reach_open_{pt}"] = clean_df["exc_open"] >= pt
        clean_df[f"reach_60m_{pt}"] = clean_df["exc_60m"] >= pt

    # Save Parquet
    parquet_path = ARTIFACTS / "cost_capacity_panel.parquet"
    clean_df.to_parquet(parquet_path, index=False)
    print(f"Saved cost capacity panel to {parquet_path}")

    # Build Summary Table
    def build_capacity_table(df_sub: pd.DataFrame, group_col: str) -> pd.DataFrame:
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
                    "mean_rth_range": round(float(g["rth_range"].mean()), 1),
                    "mean_exc_open": round(float(g["exc_open"].mean()), 1),
                    "mean_exc_60m": round(float(g["exc_60m"].mean()), 1),
                    "drag_open_pct": round(float(g["drag_open_pct"].mean()), 2),
                    "drag_60m_pct": round(float(g["drag_60m_pct"].mean()), 2),
                    "reach_60m_20pt_pct": round(float(g["reach_60m_20"].mean()) * 100, 1),
                    "reach_60m_40pt_pct": round(float(g["reach_60m_40"].mean()) * 100, 1),
                    "reach_60m_80pt_pct": round(float(g["reach_60m_80"].mean()) * 100, 1),
                    "reach_open_40pt_pct": round(float(g["reach_open_40"].mean()) * 100, 1),
                    "reach_open_80pt_pct": round(float(g["reach_open_80"].mean()) * 100, 1),
                    "reach_open_150pt_pct": round(float(g["reach_open_150"].mean()) * 100, 1),
                })
        return pd.DataFrame(rows)

    audit_capacity = build_capacity_table(clean_df, "bin_vol_regime")
    audit_capacity.to_csv(ARTIFACTS / "audit_cost_capacity_by_regime.csv", index=False)

    print("\n--- TABLE 1: SIGNAL-AGNOSTIC COST CAPACITY & FRICTION DRAG BY VOLATILITY REGIME ---")
    print(audit_capacity.to_string(index=False))


if __name__ == "__main__":
    main()
