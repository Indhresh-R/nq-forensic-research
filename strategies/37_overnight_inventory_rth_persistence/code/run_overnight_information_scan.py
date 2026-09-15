"""
Strategy 37: Overnight Inventory -> RTH Directional Persistence Information Scan
Evaluates whether pre-market Globex states contain conditioning information over RTH session behavior.
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

ARTIFACTS = ROOT / "artifacts" / "37_overnight_inventory_rth_persistence"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30   # 09:30
RTH_CLOSE = 15 * 60 + 55 # 15:55


def main():
    print("=" * 80)
    print("STRATEGY 37: OVERNIGHT INVENTORY INFORMATION SCAN (2010-2026)")
    print("=" * 80)

    print("Loading continuous NQ 1-minute dataset...")
    nq = load_nq()
    print(f"Loaded {len(nq):,} bars across {nq['session_date'].nunique():,} sessions.")

    # 1. Separate RTH and Overnight data per session_date
    sessions = sorted(nq["session_date"].unique())
    
    session_stats = []
    
    # Pre-group by session_date
    grouped = {sd: g for sd, g in nq.groupby("session_date", sort=True)}
    
    # Calculate per-session RTH summary and Overnight summary
    raw_summaries = []
    for sd in sessions:
        g = grouped[sd]
        
        # RTH: 09:30 to 15:55
        rth_g = g[(g.ny_min >= RTH_OPEN) & (g.ny_min <= RTH_CLOSE)]
        if len(rth_g) < 300: # incomplete RTH session
            continue
            
        rth_open = float(rth_g["open"].iloc[0])
        rth_high = float(rth_g["high"].max())
        rth_low = float(rth_g["low"].min())
        rth_close = float(rth_g["close"].iloc[-1])
        rth_vol = int(rth_g["volume"].sum())
        yr = int(rth_g["year"].iloc[0])
        
        # Overnight: ny_min >= 18:00 (prior night) OR ny_min < 09:30 (morning)
        on_g = g[(g.ny_min >= 18 * 60) | (g.ny_min < RTH_OPEN)]
        if len(on_g) < 60: # insufficient overnight prints
            continue
            
        on_open = float(on_g["open"].iloc[0])
        on_high = float(on_g["high"].max())
        on_low = float(on_g["low"].min())
        on_close = float(on_g["close"].iloc[-1])
        on_vol = int(on_g["volume"].sum())
        
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
            "on_open": on_open,
            "on_high": on_high,
            "on_low": on_low,
            "on_close": on_close,
            "on_range": on_high - on_low,
            "on_vol": on_vol,
        })
        
    df_sess = pd.DataFrame(raw_summaries).sort_values("session_date").reset_index(drop=True)
    print(f"Processed {len(df_sess):,} complete sessions with both Overnight and RTH data.")

    # 2. Compute Lagged Features (Prior Day RTH & Trailing 20-day ATR)
    df_sess["prev_rth_high"] = df_sess["rth_high"].shift(1)
    df_sess["prev_rth_low"] = df_sess["rth_low"].shift(1)
    df_sess["prev_rth_close"] = df_sess["rth_close"].shift(1)
    df_sess["prev_rth_return"] = df_sess["rth_return"].shift(1)
    df_sess["atr20"] = df_sess["rth_range"].shift(1).rolling(20, min_periods=10).mean()

    # Drop warm-up sessions
    df = df_sess.dropna(subset=["prev_rth_high", "atr20"]).copy().reset_index(drop=True)

    # 3. Engineer Pre-Market Features (Strictly Known at t <= 09:29 ET)
    # G1: Gap
    df["gap_pts"] = df["rth_open"] - df["prev_rth_close"]
    df["gap_norm"] = df["gap_pts"] / df["atr20"]
    df["gap_bin"] = pd.cut(
        df["gap_norm"], 
        bins=[-np.inf, -0.50, -0.15, 0.15, 0.50, np.inf],
        labels=["LARGE_GAP_DOWN", "MOD_GAP_DOWN", "NEUTRAL_GAP", "MOD_GAP_UP", "LARGE_GAP_UP"]
    )

    # G2: Overnight Range Ratio
    df["onr_ratio"] = df["on_range"] / df["atr20"]
    df["onr_regime"] = pd.cut(
        df["onr_ratio"],
        bins=[-np.inf, 0.40, 0.80, np.inf],
        labels=["COMPRESSED_ONR", "NORMAL_ONR", "EXPANDED_ONR"]
    )

    # G3: Inventory Location
    df["inv_location"] = np.where(
        df["on_range"] > 0,
        (df["on_close"] - df["on_low"]) / df["on_range"],
        0.5
    )
    df["inv_location_bin"] = pd.cut(
        df["inv_location"],
        bins=[-np.inf, 0.20, 0.40, 0.60, 0.80, np.inf],
        labels=["PINNED_SHORT", "LOWER_MID", "BALANCED", "UPPER_MID", "PINNED_LONG"]
    )

    # G4: Overnight Extension Regime
    def get_extension(row):
        on_hi, on_lo = row["on_high"], row["on_low"]
        pr_hi, pr_lo = row["prev_rth_high"], row["prev_rth_low"]
        if on_lo > pr_hi:
            return "TRUE_GAP_UP"
        elif on_hi > pr_hi and on_lo <= pr_hi:
            return "EXTENSION_UP"
        elif on_hi <= pr_hi and on_lo >= pr_lo:
            return "INSIDE_BALANCED"
        elif on_lo < pr_lo and on_hi >= pr_lo:
            return "EXTENSION_DOWN"
        elif on_hi < pr_lo:
            return "TRUE_GAP_DOWN"
        return "OTHER"

    df["extension_regime"] = df.apply(get_extension, axis=1)

    # G5: Confluence
    df["confluence"] = np.where(
        (df["prev_rth_return"] * df["gap_pts"]) > 0, "PRO_TREND",
        np.where((df["prev_rth_return"] * df["gap_pts"]) < 0, "COUNTER_TREND", "NEUTRAL")
    )

    # 4. Compute RTH Persistence Dependent Targets (Y1-Y5)
    # Y1: RTH Return (already computed)
    # Y2: Directional Efficiency
    df["rth_efficiency"] = np.where(
        df["rth_range"] > 0,
        df["rth_return"].abs() / df["rth_range"],
        0.0
    )

    # Y3: Gap Continuation (Did RTH move in gap direction?)
    df["gap_continuation"] = np.where(
        df["gap_pts"] > 0,
        (df["rth_return"] > 0).astype(int),
        np.where(df["gap_pts"] < 0, (df["rth_return"] < 0).astype(int), np.nan)
    )

    # Y4: Clean Trend Day Indicator
    median_range = df["rth_range"].median()
    df["is_trend_day"] = (
        (df["rth_range"] >= median_range) & (df["rth_efficiency"] >= 0.60)
    ).astype(int)

    # Save master panel
    master_panel_path = ARTIFACTS / "overnight_information_panel.parquet"
    df.to_parquet(master_panel_path, index=False)
    print(f"Saved master scan panel to {master_panel_path}")

    # 5. Compile Empirical Distribution Analysis
    print("\n" + "=" * 100)
    print("EMPIRICAL DISTRIBUTION SCAN ACROSS OVERNIGHT REGIMES")
    print("=" * 100)

    # Baseline Unconditional Distribution
    for sp in ["IS", "Validation", "OOS", "ALL"]:
        sub = df if sp == "ALL" else df[df["split"] == sp]
        cont = sub["gap_continuation"].dropna()
        print(f"[{sp}] Unconditional: N={len(sub):,} | Mean Eff={sub['rth_efficiency'].mean():.3f} | TrendDay%={sub['is_trend_day'].mean()*100:.1f}% | GapCont%={cont.mean()*100:.1f}% | Mean RTH Ret={sub['rth_return'].mean():+.2f} pts")

    # Table 1: Extension Regime Analysis
    print("\n--- 1. OVERNIGHT EXTENSION REGIME (G4) VS RTH PERSISTENCE ---")
    ext_rows = []
    for sp in ["IS", "Validation", "OOS", "ALL"]:
        sub = df if sp == "ALL" else df[df["split"] == sp]
        for reg in ["TRUE_GAP_UP", "EXTENSION_UP", "INSIDE_BALANCED", "EXTENSION_DOWN", "TRUE_GAP_DOWN"]:
            r_df = sub[sub["extension_regime"] == reg]
            n = len(r_df)
            if n == 0: continue
            cont = r_df["gap_continuation"].dropna()
            ext_rows.append({
                "split": sp,
                "regime": reg,
                "N": n,
                "pct_of_days": round(n / len(sub) * 100, 1),
                "mean_eff": round(r_df["rth_efficiency"].mean(), 3),
                "trend_day_pct": round(r_df["is_trend_day"].mean() * 100, 1),
                "gap_cont_pct": round(cont.mean() * 100, 1) if len(cont) else np.nan,
                "mean_rth_return": round(r_df["rth_return"].mean(), 2),
            })
    df_ext = pd.DataFrame(ext_rows)
    df_ext.to_csv(ARTIFACTS / "audit_extension_regime.csv", index=False)
    print(df_ext[df_ext["split"] == "IS"].to_string(index=False))

    # Table 2: Inventory Location Pinning Analysis
    print("\n--- 2. INVENTORY LOCATION PINNING (G3) VS RTH PERSISTENCE ---")
    loc_rows = []
    for sp in ["IS", "Validation", "OOS", "ALL"]:
        sub = df if sp == "ALL" else df[df["split"] == sp]
        for lbin in ["PINNED_SHORT", "LOWER_MID", "BALANCED", "UPPER_MID", "PINNED_LONG"]:
            l_df = sub[sub["inv_location_bin"] == lbin]
            n = len(l_df)
            if n == 0: continue
            cont = l_df["gap_continuation"].dropna()
            loc_rows.append({
                "split": sp,
                "location_bin": lbin,
                "N": n,
                "mean_eff": round(l_df["rth_efficiency"].mean(), 3),
                "trend_day_pct": round(l_df["is_trend_day"].mean() * 100, 1),
                "mean_rth_return": round(l_df["rth_return"].mean(), 2),
            })
    df_loc = pd.DataFrame(loc_rows)
    df_loc.to_csv(ARTIFACTS / "audit_inventory_location.csv", index=False)
    print(df_loc[df_loc["split"] == "IS"].to_string(index=False))

    # Table 3: Gap Size Norm Analysis
    print("\n--- 3. GAP SIZE NORM (G1) VS RTH PERSISTENCE ---")
    gap_rows = []
    for sp in ["IS", "Validation", "OOS", "ALL"]:
        sub = df if sp == "ALL" else df[df["split"] == sp]
        for gbin in ["LARGE_GAP_DOWN", "MOD_GAP_DOWN", "NEUTRAL_GAP", "MOD_GAP_UP", "LARGE_GAP_UP"]:
            g_df = sub[sub["gap_bin"] == gbin]
            n = len(g_df)
            if n == 0: continue
            cont = g_df["gap_continuation"].dropna()
            gap_rows.append({
                "split": sp,
                "gap_bin": gbin,
                "N": n,
                "mean_eff": round(g_df["rth_efficiency"].mean(), 3),
                "trend_day_pct": round(g_df["is_trend_day"].mean() * 100, 1),
                "gap_cont_pct": round(cont.mean() * 100, 1) if len(cont) else np.nan,
                "mean_rth_return": round(g_df["rth_return"].mean(), 2),
            })
    df_gap = pd.DataFrame(gap_rows)
    df_gap.to_csv(ARTIFACTS / "audit_gap_size.csv", index=False)
    print(df_gap[df_gap["split"] == "IS"].to_string(index=False))

    # Table 4: Directional Confluence Analysis
    print("\n--- 4. DIRECTIONAL CONFLUENCE (G5) VS RTH PERSISTENCE ---")
    conf_rows = []
    for sp in ["IS", "Validation", "OOS", "ALL"]:
        sub = df if sp == "ALL" else df[df["split"] == sp]
        for cbin in ["PRO_TREND", "COUNTER_TREND"]:
            c_df = sub[sub["confluence"] == cbin]
            n = len(c_df)
            if n == 0: continue
            conf_rows.append({
                "split": sp,
                "confluence": cbin,
                "N": n,
                "mean_eff": round(c_df["rth_efficiency"].mean(), 3),
                "trend_day_pct": round(c_df["is_trend_day"].mean() * 100, 1),
                "mean_rth_return": round(c_df["rth_return"].mean(), 2),
            })
    df_conf = pd.DataFrame(conf_rows)
    df_conf.to_csv(ARTIFACTS / "audit_directional_confluence.csv", index=False)
    print(df_conf[df_conf["split"] == "IS"].to_string(index=False))


if __name__ == "__main__":
    main()
