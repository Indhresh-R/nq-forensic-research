"""
Strategy 38: Opening Auction Information Scan (2010-2026)
Evaluates whether the first 5, 10, or 15 minutes of RTH contain structural information
about remaining-session directional persistence, trendiness, and follow-through.
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

ARTIFACTS = ROOT / "artifacts" / "38_opening_auction_information"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30   # 570
RTH_CLOSE = 15 * 60 + 55 # 955

CHECKPOINTS = {
    "5m": {"close_min": 9 * 60 + 34, "next_open_min": 9 * 60 + 35},
    "10m": {"close_min": 9 * 60 + 39, "next_open_min": 9 * 60 + 40},
    "15m": {"close_min": 9 * 60 + 44, "next_open_min": 9 * 60 + 45},
}


def main():
    print("=" * 80)
    print("STRATEGY 38: OPENING AUCTION INFORMATION SCAN (2010-2026)")
    print("=" * 80)

    print("Loading continuous NQ 1-minute dataset...")
    nq = load_nq()
    rth = nq[(nq.ny_min >= RTH_OPEN) & (nq.ny_min <= RTH_CLOSE)].copy()
    print(f"Loaded {len(rth):,} RTH bars across {rth['session_date'].nunique():,} sessions.")

    # Pre-index by (session_date, ny_min)
    rth_indexed = rth.set_index(["session_date", "ny_min"]).sort_index()

    # Calculate full-day RTH metrics and trailing 20-day ATR per session
    sess_grouped = rth.groupby("session_date", sort=True)
    day_meta = sess_grouped.agg(
        rth_open=("open", "first"),
        rth_high=("high", "max"),
        rth_low=("low", "min"),
        rth_close=("close", "last"),
        rth_vol=("volume", "sum"),
        year=("year", "first"),
        n_bars=("ny_min", "count"),
    ).reset_index()

    # Filter complete sessions (386 bars)
    day_meta = day_meta[day_meta["n_bars"] >= 380].reset_index(drop=True)
    day_meta["rth_range"] = day_meta["rth_high"] - day_meta["rth_low"]
    day_meta["atr20"] = day_meta["rth_range"].shift(1).rolling(20, min_periods=10).mean()
    day_meta = day_meta.dropna(subset=["atr20"]).reset_index(drop=True)

    atr_map = day_meta.set_index("session_date")["atr20"].to_dict()
    valid_sessions = set(day_meta["session_date"].unique())

    all_records = []

    for cp_name, cp_info in CHECKPOINTS.items():
        c_min = cp_info["close_min"]
        n_min = cp_info["next_open_min"]

        print(f"\nProcessing Checkpoint {cp_name} (Close {c_min // 60:02d}:{c_min % 60:02d}, Remaining from {n_min // 60:02d}:{n_min % 60:02d})...")

        for sd in day_meta["session_date"]:
            if (sd, RTH_OPEN) not in rth_indexed.index or (sd, c_min) not in rth_indexed.index or (sd, n_min) not in rth_indexed.index or (sd, RTH_CLOSE) not in rth_indexed.index:
                continue

            day_bars = rth_indexed.loc[sd]
            atr = atr_map.get(sd)
            if atr is None or atr <= 0:
                continue

            # 1. Opening Window (570 to c_min)
            op_bars = day_bars.loc[RTH_OPEN:c_min]
            open_p = float(op_bars["open"].iloc[0])
            open_hi = float(op_bars["high"].max())
            open_lo = float(op_bars["low"].min())
            close_p = float(op_bars["close"].iloc[-1])
            vol_open = int(op_bars["volume"].sum())
            yr = int(op_bars["year"].iloc[0])

            or_pts = open_hi - open_lo
            or_ratio = or_pts / atr
            disp = close_p - open_p
            eff_open = abs(disp) / or_pts if or_pts > 0 else 0.0

            # 2. Remaining Session Window (n_min to 955)
            rem_bars = day_bars.loc[n_min:RTH_CLOSE]
            rem_open = float(rem_bars["open"].iloc[0])
            rem_hi = float(rem_bars["high"].max())
            rem_lo = float(rem_bars["low"].min())
            rem_close = float(rem_bars["close"].iloc[-1])
            rem_range = rem_hi - rem_lo
            rem_return = rem_close - rem_open

            eff_rem = abs(rem_return) / rem_range if rem_range > 0 else 0.0
            follow_through = 1 if (rem_return * disp) > 0 else (0 if (rem_return * disp) < 0 else np.nan)

            all_records.append({
                "checkpoint": cp_name,
                "session_date": str(sd),
                "year": yr,
                "split": split_of(yr),
                "atr20": atr,
                "or_pts": or_pts,
                "or_ratio": or_ratio,
                "displacement": disp,
                "eff_open": eff_open,
                "vol_open": vol_open,
                "rem_range": rem_range,
                "rem_return": rem_return,
                "eff_rem": eff_rem,
                "follow_through": follow_through,
            })

    df = pd.DataFrame(all_records)
    print(f"\nConstructed {len(df):,} total observation records across checkpoints.")

    # Calculate tertiles / thresholds on In-Sample
    panel_rows = []
    for cp_name in CHECKPOINTS.keys():
        cp_df = df[df["checkpoint"] == cp_name].copy()
        
        is_df = cp_df[cp_df["split"] == "IS"]
        p33_or = is_df["or_ratio"].quantile(0.333)
        p66_or = is_df["or_ratio"].quantile(0.666)
        med_rem_range = is_df["rem_range"].median()

        # Categorize
        cp_df["or_bin"] = np.where(
            cp_df["or_ratio"] < p33_or, "COMPRESSED_OR",
            np.where(cp_df["or_ratio"] > p66_or, "EXPANDED_OR", "NORMAL_OR")
        )

        cp_df["eff_bin"] = np.where(
            cp_df["eff_open"] >= 0.70, "HIGH_EFF",
            np.where(cp_df["eff_open"] < 0.35, "LOW_EFF", "MODERATE_EFF")
        )

        cp_df["drive_dir"] = np.where(
            cp_df["displacement"] > 0, "BULL_DRIVE",
            np.where(cp_df["displacement"] < 0, "BEAR_DRIVE", "NEUTRAL")
        )

        cp_df["is_trend_day_rem"] = np.where(
            (cp_df["rem_range"] >= med_rem_range) & (cp_df["eff_rem"] >= 0.60), 1, 0
        )

        panel_rows.append(cp_df)

    master_df = pd.concat(panel_rows, ignore_index=True)
    master_parquet = ARTIFACTS / "opening_auction_panel.parquet"
    master_df.to_parquet(master_parquet, index=False)
    print(f"Saved master scan panel to {master_parquet}")

    # Empirical Distribution Summaries
    print("\n" + "=" * 100)
    print("EMPIRICAL SCAN: OPENING AUCTION BEHAVIOR VS REMAINING-SESSION PERSISTENCE")
    print("=" * 100)

    # 1. Unconditional Baseline per Checkpoint
    for cp_name in CHECKPOINTS.keys():
        sub = master_df[master_df["checkpoint"] == cp_name]
        for sp in ["IS", "Validation", "OOS", "ALL"]:
            s_sub = sub if sp == "ALL" else sub[sub["split"] == sp]
            ft = s_sub["follow_through"].dropna()
            print(f"[{cp_name} | {sp}] Unconditional: N={len(s_sub):,} | Mean Eff_rem={s_sub['eff_rem'].mean():.3f} | TrendDay%={s_sub['is_trend_day_rem'].mean()*100:.1f}% | FollowThrough%={ft.mean()*100:.1f}% | Mean Rem Ret={s_sub['rem_return'].mean():+.2f} pts")

    # 2. Early Efficiency (F2) Conditioning Table
    print("\n--- 1. EARLY PATH EFFICIENCY (F2) VS REMAINING-SESSION PERSISTENCE ---")
    eff_rows = []
    for cp_name in CHECKPOINTS.keys():
        sub = master_df[master_df["checkpoint"] == cp_name]
        for sp in ["IS", "Validation", "OOS", "ALL"]:
            s_sub = sub if sp == "ALL" else sub[sub["split"] == sp]
            for ebin in ["HIGH_EFF", "MODERATE_EFF", "LOW_EFF"]:
                e_sub = s_sub[s_sub["eff_bin"] == ebin]
                n = len(e_sub)
                if n == 0: continue
                ft = e_sub["follow_through"].dropna()
                eff_rows.append({
                    "checkpoint": cp_name,
                    "split": sp,
                    "eff_bin": ebin,
                    "N": n,
                    "pct_of_days": round(n / len(s_sub) * 100, 1),
                    "mean_eff_rem": round(e_sub["eff_rem"].mean(), 3),
                    "trend_day_pct": round(e_sub["is_trend_day_rem"].mean() * 100, 1),
                    "follow_through_pct": round(ft.mean() * 100, 1) if len(ft) else np.nan,
                    "mean_rem_return": round(e_sub["rem_return"].mean(), 2),
                })
    df_eff_summary = pd.DataFrame(eff_rows)
    df_eff_summary.to_csv(ARTIFACTS / "audit_early_efficiency.csv", index=False)
    print(df_eff_summary[(df_eff_summary["checkpoint"] == "15m") & (df_eff_summary["split"].isin(["IS", "OOS"]))].to_string(index=False))

    # 3. Opening Range Ratio (F1) Conditioning Table
    print("\n--- 2. OPENING RANGE RATIO (F1) VS REMAINING-SESSION PERSISTENCE ---")
    or_rows = []
    for cp_name in CHECKPOINTS.keys():
        sub = master_df[master_df["checkpoint"] == cp_name]
        for sp in ["IS", "Validation", "OOS", "ALL"]:
            s_sub = sub if sp == "ALL" else sub[sub["split"] == sp]
            for obin in ["EXPANDED_OR", "NORMAL_OR", "COMPRESSED_OR"]:
                o_sub = s_sub[s_sub["or_bin"] == obin]
                n = len(o_sub)
                if n == 0: continue
                ft = o_sub["follow_through"].dropna()
                or_rows.append({
                    "checkpoint": cp_name,
                    "split": sp,
                    "or_bin": obin,
                    "N": n,
                    "pct_of_days": round(n / len(s_sub) * 100, 1),
                    "mean_eff_rem": round(o_sub["eff_rem"].mean(), 3),
                    "trend_day_pct": round(o_sub["is_trend_day_rem"].mean() * 100, 1),
                    "follow_through_pct": round(ft.mean() * 100, 1) if len(ft) else np.nan,
                    "mean_rem_return": round(o_sub["rem_return"].mean(), 2),
                })
    df_or_summary = pd.DataFrame(or_rows)
    df_or_summary.to_csv(ARTIFACTS / "audit_opening_range.csv", index=False)
    print(df_or_summary[(df_or_summary["checkpoint"] == "15m") & (df_or_summary["split"].isin(["IS", "OOS"]))].to_string(index=False))

    # 4. Early Drive Direction (F4) Conditioning Table
    print("\n--- 3. EARLY DRIVE DIRECTION (F4) VS REMAINING-SESSION RETURN ---")
    drive_rows = []
    for cp_name in CHECKPOINTS.keys():
        sub = master_df[master_df["checkpoint"] == cp_name]
        for sp in ["IS", "Validation", "OOS", "ALL"]:
            s_sub = sub if sp == "ALL" else sub[sub["split"] == sp]
            for ddir in ["BULL_DRIVE", "BEAR_DRIVE"]:
                d_sub = s_sub[s_sub["drive_dir"] == ddir]
                n = len(d_sub)
                if n == 0: continue
                ft = d_sub["follow_through"].dropna()
                drive_rows.append({
                    "checkpoint": cp_name,
                    "split": sp,
                    "drive_dir": ddir,
                    "N": n,
                    "mean_eff_rem": round(d_sub["eff_rem"].mean(), 3),
                    "trend_day_pct": round(d_sub["is_trend_day_rem"].mean() * 100, 1),
                    "follow_through_pct": round(ft.mean() * 100, 1) if len(ft) else np.nan,
                    "mean_rem_return": round(d_sub["rem_return"].mean(), 2),
                })
    df_drive_summary = pd.DataFrame(drive_rows)
    df_drive_summary.to_csv(ARTIFACTS / "audit_early_drive.csv", index=False)
    print(df_drive_summary[(df_drive_summary["checkpoint"] == "15m") & (df_drive_summary["split"].isin(["IS", "OOS"]))].to_string(index=False))


if __name__ == "__main__":
    main()
