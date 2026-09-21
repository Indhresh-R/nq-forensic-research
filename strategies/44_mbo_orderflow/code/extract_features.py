"""
Feature Engineering Engine for Strategy 44: Hypothesis H02
Transforms 1-second continuous order flow and MBO samples into rigorous, causal hypothesis features:
  - H02-A: Generic CVD, NFR, TCD (1s, 5s, 15s, 60s)
  - H02-B: Causal 15-minute Range Location & Volatility Context
  - H02-C: Price-Flow Divergence Indicators (Bullish & Bearish)
  - H02-D: Passive Absorption (Trade-Only vs. L3 MBO Replenishment)
  - Event De-duplication with 30s Cooldown Flag
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INPUT_DIR = PROJECT_ROOT / "strategies" / "44_mbo_orderflow" / "results" / "sampled_features"
OUTPUT_DIR = PROJECT_ROOT / "strategies" / "44_mbo_orderflow" / "results" / "engineered_features"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IS_SESSIONS = [
    "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15",
    "2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23",
    "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31",
    "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10",
    "2026-08-11", "2026-08-12"
]


def apply_event_cooldown(events_series: pd.Series, cooldown_s: int = 30) -> pd.Series:
    """
    Applies a refractory cooldown period to discrete event triggers.
    If an event triggers at t, any subsequent event within cooldown_s is filtered out.
    """
    arr = events_series.values
    n = len(arr)
    dedup = np.zeros(n, dtype=bool)
    last_trigger_idx = -cooldown_s - 1

    for i in range(n):
        if arr[i] != 0:
            if (i - last_trigger_idx) >= cooldown_s:
                dedup[i] = True
                last_trigger_idx = i

    return pd.Series(dedup, index=events_series.index)


def compute_h02_features(df: pd.DataFrame) -> pd.DataFrame:
    eps = 1e-6
    feat = df.copy()

    # --- H02-A: GENERIC AGGRESSIVE ORDER FLOW DELTA ---
    tb = feat["trade_b_1s"]
    ta = feat["trade_a_1s"]
    tcb = feat["trade_cnt_b_1s"]
    tca = feat["trade_cnt_a_1s"]

    # 1s window
    feat["cvd_1s"] = tb - ta
    feat["vol_1s"] = tb + ta
    feat["nfr_1s"] = feat["cvd_1s"] / (feat["vol_1s"] + eps)
    feat["tcd_1s"] = tcb - tca

    # 5s window
    tb_5s = tb.rolling(5).sum()
    ta_5s = ta.rolling(5).sum()
    feat["cvd_5s"] = tb_5s - ta_5s
    feat["vol_5s"] = tb_5s + ta_5s
    feat["nfr_5s"] = feat["cvd_5s"] / (feat["vol_5s"] + eps)
    feat["tcd_5s"] = tcb.rolling(5).sum() - tca.rolling(5).sum()

    # 15s window
    tb_15s = tb.rolling(15).sum()
    ta_15s = ta.rolling(15).sum()
    feat["cvd_15s"] = tb_15s - ta_15s
    feat["vol_15s"] = tb_15s + ta_15s
    feat["nfr_15s"] = feat["cvd_15s"] / (feat["vol_15s"] + eps)
    feat["tcd_15s"] = tcb.rolling(15).sum() - tca.rolling(15).sum()

    # 60s window
    tb_60s = tb.rolling(60).sum()
    ta_60s = ta.rolling(60).sum()
    feat["cvd_60s"] = tb_60s - ta_60s
    feat["vol_60s"] = tb_60s + ta_60s
    feat["nfr_60s"] = feat["cvd_60s"] / (feat["vol_60s"] + eps)
    feat["tcd_60s"] = tcb.rolling(60).sum() - tca.rolling(60).sum()

    # --- H02-B: CAUSAL RANGE & VOLATILITY CONTEXT ---
    # 15-minute rolling range (900 seconds)
    low_15m = feat["mid_px"].rolling(900, min_periods=60).min()
    high_15m = feat["mid_px"].rolling(900, min_periods=60).max()
    feat["range_loc_15m"] = (feat["mid_px"] - low_15m) / (high_15m - low_15m + eps)

    # Range regime flags
    feat["range_extreme_high"] = (feat["range_loc_15m"] >= 0.90).astype(int)
    feat["range_extreme_low"] = (feat["range_loc_15m"] <= 0.10).astype(int)
    feat["range_value_area"] = ((feat["range_loc_15m"] >= 0.30) & (feat["range_loc_15m"] <= 0.70)).astype(int)

    # 15-minute rolling volatility of 5s mid-price changes
    dp_5s = feat["mid_px"] - feat["mid_px"].shift(5)
    dp_15s = feat["mid_px"] - feat["mid_px"].shift(15)
    dp_60s = feat["mid_px"] - feat["mid_px"].shift(60)

    feat["dp_5s"] = dp_5s
    feat["dp_15s"] = dp_15s
    feat["dp_60s"] = dp_60s
    feat["vol_15m"] = dp_5s.rolling(900, min_periods=60).std().bfill()

    # --- H02-C: PRICE-FLOW DIVERGENCE ---
    # Divergence 15s
    div_bear_15s = (feat["dp_15s"] >= 1.5 * feat["vol_15m"]) & (feat["cvd_15s"] <= 0)
    div_bull_15s = (feat["dp_15s"] <= -1.5 * feat["vol_15m"]) & (feat["cvd_15s"] >= 0)
    feat["div_sig_15s"] = np.where(div_bull_15s, 1, np.where(div_bear_15s, -1, 0))
    feat["div_dedup_15s"] = apply_event_cooldown(feat["div_sig_15s"], cooldown_s=30)

    # Divergence 60s
    div_bear_60s = (feat["dp_60s"] >= 1.5 * feat["vol_15m"]) & (feat["cvd_60s"] <= 0)
    div_bull_60s = (feat["dp_60s"] <= -1.5 * feat["vol_15m"]) & (feat["cvd_60s"] >= 0)
    feat["div_sig_60s"] = np.where(div_bull_60s, 1, np.where(div_bear_60s, -1, 0))
    feat["div_dedup_60s"] = apply_event_cooldown(feat["div_sig_60s"], cooldown_s=30)

    # --- H02-D: PASSIVE ABSORPTION (TRADE-ONLY VS L3 MBO) ---
    # Causal rolling 1800s (30-min) 90th percentile of total volume
    vol_p90_causal_5s = feat["vol_5s"].rolling(1800, min_periods=300).quantile(0.90).bfill()
    vol_p90_causal_15s = feat["vol_15s"].rolling(1800, min_periods=300).quantile(0.90).bfill()

    # Stagnation: |dp| <= 1 tick (0.25 pts)
    stagnant_5s = feat["dp_5s"].abs() <= 0.25
    stagnant_15s = feat["dp_15s"].abs() <= 0.25

    # 1. Trade-Only Absorption (5s and 15s)
    trade_bear_5s = (tb_5s >= vol_p90_causal_5s) & (feat["dp_5s"] <= 0)
    trade_bull_5s = (ta_5s >= vol_p90_causal_5s) & (feat["dp_5s"] >= 0)
    feat["absorb_trade_sig_5s"] = np.where(trade_bull_5s, 1, np.where(trade_bear_5s, -1, 0))
    feat["absorb_trade_dedup_5s"] = apply_event_cooldown(feat["absorb_trade_sig_5s"], cooldown_s=30)

    trade_bear_15s = (tb_15s >= vol_p90_causal_15s) & (feat["dp_15s"] <= 0)
    trade_bull_15s = (ta_15s >= vol_p90_causal_15s) & (feat["dp_15s"] >= 0)
    feat["absorb_trade_sig_15s"] = np.where(trade_bull_15s, 1, np.where(trade_bear_15s, -1, 0))
    feat["absorb_trade_dedup_15s"] = apply_event_cooldown(feat["absorb_trade_sig_15s"], cooldown_s=30)

    # 2. L3 MBO-Confirmed Absorption (Replenishment at BBO)
    # Bearish: buyers absorbed by passive asks, with resting replenishment (adds >= fills or depth stable)
    add_a_5s = feat["add_a_1s"].rolling(5).sum()
    fill_a_5s = feat["fill_a_1s"].rolling(5).sum()
    add_b_5s = feat["add_b_1s"].rolling(5).sum()
    fill_b_5s = feat["fill_b_1s"].rolling(5).sum()

    replenish_ask_5s = (add_a_5s >= fill_a_5s) | (feat["q_a1"] >= feat["q_a1"].shift(5))
    replenish_bid_5s = (add_b_5s >= fill_b_5s) | (feat["q_b1"] >= feat["q_b1"].shift(5))

    l3_bear_5s = trade_bear_5s & replenish_ask_5s
    l3_bull_5s = trade_bull_5s & replenish_bid_5s
    feat["absorb_l3_sig_5s"] = np.where(l3_bull_5s, 1, np.where(l3_bear_5s, -1, 0))
    feat["absorb_l3_dedup_5s"] = apply_event_cooldown(feat["absorb_l3_sig_5s"], cooldown_s=30)

    add_a_15s = feat["add_a_1s"].rolling(15).sum()
    fill_a_15s = feat["fill_a_1s"].rolling(15).sum()
    add_b_15s = feat["add_b_1s"].rolling(15).sum()
    fill_b_15s = feat["fill_b_1s"].rolling(15).sum()

    replenish_ask_15s = (add_a_15s >= fill_a_15s) | (feat["q_a1"] >= feat["q_a1"].shift(15))
    replenish_bid_15s = (add_b_15s >= fill_b_15s) | (feat["q_b1"] >= feat["q_b1"].shift(15))

    l3_bear_15s = trade_bear_15s & replenish_ask_15s
    l3_bull_15s = trade_bull_15s & replenish_bid_15s
    feat["absorb_l3_sig_15s"] = np.where(l3_bull_15s, 1, np.where(l3_bear_15s, -1, 0))
    feat["absorb_l3_dedup_15s"] = apply_event_cooldown(feat["absorb_l3_sig_15s"], cooldown_s=30)

    return feat


def process_features_batch():
    for date_str in IS_SESSIONS:
        in_file = INPUT_DIR / f"h02_samples_{date_str}.parquet"
        out_file = OUTPUT_DIR / f"h02_features_{date_str}.parquet"
        if out_file.exists():
            continue
        if not in_file.exists():
            continue

        df = pd.read_parquet(in_file)
        feat = compute_h02_features(df)
        feat.to_parquet(out_file, index=False)
        print(f"[{date_str}] Engineered H02 features -> {out_file.name}", flush=True)


if __name__ == "__main__":
    process_features_batch()
