"""
Strategy 41 - Layer 2: Frozen Benchmark Signals Stratification across Volatility Regimes
Executes pre-existing frozen benchmark signals (Strategy 30 IB Breakout, Strategy 38
Opening Drive, Strategy 36 Intraday) and stratifies economics across Strategy-39 volatility tiers (2010-2026).
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
FRICTION = 1.0            # 1.0 point round-trip


def main():
    print("=" * 80)
    print("STRATEGY 41 - LAYER 2: BENCHMARK SIGNALS STRATIFICATION (2010-2026)")
    print("=" * 80)

    print("Loading continuous NQ 1-minute dataset...")
    nq = load_nq()
    sessions = sorted(nq["session_date"].unique())
    grouped = {sd: g for sd, g in nq.groupby("session_date", sort=True)}

    # 1. First pass: extract per-session RTH summary and volatility state
    session_metas = []
    for sd in sessions:
        g = grouped[sd]
        rth_g = g[(g.ny_min >= RTH_OPEN) & (g.ny_min <= RTH_CLOSE)]
        if len(rth_g) < 300:
            continue
        h = float(rth_g["high"].max())
        l = float(rth_g["low"].min())
        o = float(rth_g["open"].iloc[0])
        c = float(rth_g["close"].iloc[-1])
        yr = int(rth_g["year"].iloc[0])
        session_metas.append({
            "session_date": sd,
            "year": yr,
            "split": split_of(yr),
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "range": h - l,
            "return": c - o,
        })

    df_meta = pd.DataFrame(session_metas).sort_values("session_date").reset_index(drop=True)
    df_meta["prev_range"] = df_meta["range"].shift(1)
    df_meta["prev_return"] = df_meta["return"].shift(1)
    df_meta["atr20"] = df_meta["prev_range"].rolling(20, min_periods=10).mean()
    df_meta["norm_prev_range"] = df_meta["prev_range"] / df_meta["atr20"]

    # Assign Volatility Regime (strictly known at t-1)
    df_meta["bin_vol_regime"] = pd.cut(
        df_meta["norm_prev_range"],
        bins=[-np.inf, 0.75, 1.25, 1.50, np.inf],
        labels=["LOW_VOL (<0.75)", "NORMAL_VOL (0.75-1.25)", "HIGH_VOL (1.25-1.50)", "EXTREME_VOL (>1.50)"]
    )

    clean_meta = df_meta.dropna(subset=["norm_prev_range", "bin_vol_regime"]).copy()
    meta_dict = {row["session_date"]: row for _, row in clean_meta.iterrows()}
    print(f"Prepared volatility metadata for {len(meta_dict):,} valid sessions.")

    # 2. Execute Benchmark Signals across all sessions
    trades = []

    for sd, meta in meta_dict.items():
        g = grouped[sd]
        rth_g = g[(g.ny_min >= RTH_OPEN) & (g.ny_min <= RTH_CLOSE)].reset_index(drop=True)
        if len(rth_g) < 300:
            continue

        yr = meta["year"]
        spl = meta["split"]
        vol_tier = str(meta["bin_vol_regime"])
        atr = meta["atr20"]

        # ----------------------------------------------------
        # Benchmark A: Strategy 30 Initial Balance (30m OR) Breakout
        # ----------------------------------------------------
        # 30m window: 09:30 to 09:59 inclusive
        ib_bars = rth_g[rth_g.ny_min < 10 * 60]
        if len(ib_bars) >= 25:
            ib_high = float(ib_bars["high"].max())
            ib_low = float(ib_bars["low"].min())

            # Post-IB bars: 10:00 to 15:54
            post_ib = rth_g[rth_g.ny_min >= 10 * 60].reset_index(drop=True)
            entry_side = 0
            entry_idx = -1
            entry_price = np.nan

            for i in range(len(post_ib) - 1):
                c_bar = float(post_ib["close"].iloc[i])
                if c_bar > ib_high:
                    entry_side = 1 # Long
                    entry_idx = i + 1
                    entry_price = float(post_ib["open"].iloc[i + 1])
                    break
                elif c_bar < ib_low:
                    entry_side = -1 # Short
                    entry_idx = i + 1
                    entry_price = float(post_ib["open"].iloc[i + 1])
                    break

            if entry_side != 0 and entry_idx < len(post_ib):
                trade_bars = post_ib.iloc[entry_idx:]
                exit_price = float(trade_bars["close"].iloc[-1])
                gross_ret = (exit_price - entry_price) * entry_side
                net_ret = gross_ret - FRICTION

                # MFE / MAE
                if entry_side == 1:
                    mfe = float(trade_bars["high"].max()) - entry_price
                    mae = entry_price - float(trade_bars["low"].min())
                else:
                    mfe = entry_price - float(trade_bars["low"].min())
                    mae = float(trade_bars["high"].max()) - entry_price

                trades.append({
                    "strategy": "BENCHMARK_A_IB_BREAKOUT",
                    "session_date": sd,
                    "year": yr,
                    "split": spl,
                    "vol_regime": vol_tier,
                    "atr20": atr,
                    "side": entry_side,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_return": gross_ret,
                    "net_return": net_ret,
                    "mfe": mfe,
                    "mae": mae,
                })

        # ----------------------------------------------------
        # Benchmark B: Strategy 38 15m Opening Drive Momentum
        # ----------------------------------------------------
        drive_bars = rth_g[rth_g.ny_min < 9 * 60 + 45]
        if len(drive_bars) >= 14:
            o930 = float(drive_bars["open"].iloc[0])
            c944 = float(drive_bars["close"].iloc[-1])
            disp = c944 - o930
            if disp != 0:
                side = 1 if disp > 0 else -1
                post_15m = rth_g[rth_g.ny_min >= 9 * 60 + 45].reset_index(drop=True)
                if len(post_15m) > 60:
                    entry_price = float(post_15m["open"].iloc[0])

                    # Variant B1: 60m hold (exit at 10:45)
                    g_60m = post_15m[post_15m.ny_min <= 10 * 60 + 45]
                    exit_60m = float(g_60m["close"].iloc[-1])
                    gross_60m = (exit_60m - entry_price) * side
                    net_60m = gross_60m - FRICTION
                    if side == 1:
                        mfe_60 = float(g_60m["high"].max()) - entry_price
                        mae_60 = entry_price - float(g_60m["low"].min())
                    else:
                        mfe_60 = entry_price - float(g_60m["low"].min())
                        mae_60 = float(g_60m["high"].max()) - entry_price

                    trades.append({
                        "strategy": "BENCHMARK_B1_DRIVE_60M",
                        "session_date": sd,
                        "year": yr,
                        "split": spl,
                        "vol_regime": vol_tier,
                        "atr20": atr,
                        "side": side,
                        "entry_price": entry_price,
                        "exit_price": exit_60m,
                        "gross_return": gross_60m,
                        "net_return": net_60m,
                        "mfe": mfe_60,
                        "mae": mae_60,
                    })

                    # Variant B2: Session close hold (15:55)
                    exit_eod = float(post_15m["close"].iloc[-1])
                    gross_eod = (exit_eod - entry_price) * side
                    net_eod = gross_eod - FRICTION
                    if side == 1:
                        mfe_eod = float(post_15m["high"].max()) - entry_price
                        mae_eod = entry_price - float(post_15m["low"].min())
                    else:
                        mfe_eod = entry_price - float(post_15m["low"].min())
                        mae_eod = float(post_15m["high"].max()) - entry_price

                    trades.append({
                        "strategy": "BENCHMARK_B2_DRIVE_EOD",
                        "session_date": sd,
                        "year": yr,
                        "split": spl,
                        "vol_regime": vol_tier,
                        "atr20": atr,
                        "side": side,
                        "entry_price": entry_price,
                        "exit_price": exit_eod,
                        "gross_return": gross_eod,
                        "net_return": net_eod,
                        "mfe": mfe_eod,
                        "mae": mae_eod,
                    })

        # ----------------------------------------------------
        # Benchmark C: Strategy 36 Fixed-Clock Momentum (09:35 -> 10:35)
        # ----------------------------------------------------
        p_ret = meta["prev_return"]
        if p_ret != 0:
            side = 1 if p_ret > 0 else -1
            post_0935 = rth_g[(rth_g.ny_min >= 9 * 60 + 35) & (rth_g.ny_min <= 10 * 60 + 35)].reset_index(drop=True)
            if len(post_0935) >= 50:
                entry_price = float(post_0935["open"].iloc[0])
                exit_price = float(post_0935["close"].iloc[-1])
                gross_ret = (exit_price - entry_price) * side
                net_ret = gross_ret - FRICTION
                if side == 1:
                    mfe = float(post_0935["high"].max()) - entry_price
                    mae = entry_price - float(post_0935["low"].min())
                else:
                    mfe = entry_price - float(post_0935["low"].min())
                    mae = float(post_0935["high"].max()) - entry_price

                trades.append({
                    "strategy": "BENCHMARK_C_FIXED_CLOCK_60M",
                    "session_date": sd,
                    "year": yr,
                    "split": spl,
                    "vol_regime": vol_tier,
                    "atr20": atr,
                    "side": side,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_return": gross_ret,
                    "net_return": net_ret,
                    "mfe": mfe,
                    "mae": mae,
                })

    df_trades = pd.DataFrame(trades)
    parquet_path = ARTIFACTS / "benchmark_trades_panel.parquet"
    df_trades.to_parquet(parquet_path, index=False)
    print(f"Generated {len(df_trades):,} total benchmark trade records across {df_trades['strategy'].nunique()} strategies.")
    print(f"Saved trades panel to {parquet_path}")

    # 3. Generate Stratified Performance Summaries
    def summarize_strategy(df_strat: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for split in ["IS", "Validation", "OOS", "OOS_2025", "OOS_2026", "ALL"]:
            if split == "ALL":
                sub = df_strat
            elif split == "OOS_2025":
                sub = df_strat[df_strat["year"] == 2025]
            elif split == "OOS_2026":
                sub = df_strat[df_strat["year"] == 2026]
            else:
                sub = df_strat[df_strat["split"] == split]
            total_n = len(sub)
            if total_n == 0:
                continue
            for vol_cat, g in sub.groupby("vol_regime", observed=True):
                n = len(g)
                pct_trades = (n / total_n) * 100
                gross_rets = g["gross_return"].to_numpy()
                net_rets = g["net_return"].to_numpy()

                wins_gross = gross_rets[gross_rets > 0]
                losses_gross = gross_rets[gross_rets < 0]
                wins_net = net_rets[net_rets > 0]
                losses_net = net_rets[net_rets < 0]

                pf_gross = (wins_gross.sum() / abs(losses_gross.sum())) if len(losses_gross) > 0 and abs(losses_gross.sum()) > 0 else np.nan
                pf_net = (wins_net.sum() / abs(losses_net.sum())) if len(losses_net) > 0 and abs(losses_net.sum()) > 0 else np.nan

                e_gross = float(gross_rets.mean())
                e_net = float(net_rets.mean())
                drag_pct = (FRICTION / abs(e_gross)) * 100 if abs(e_gross) > 0.05 else np.nan

                rows.append({
                    "split": split,
                    "vol_regime": str(vol_cat),
                    "n_trades": n,
                    "pct_trades": round(pct_trades, 1),
                    "e_gross_pts": round(e_gross, 2),
                    "e_net_pts": round(e_net, 2),
                    "total_net_pts": round(float(net_rets.sum()), 1),
                    "wr_gross_pct": round((len(wins_gross) / n) * 100, 1),
                    "wr_net_pct": round((len(wins_net) / n) * 100, 1),
                    "pf_gross": round(float(pf_gross), 3) if np.isfinite(pf_gross) else np.nan,
                    "pf_net": round(float(pf_net), 3) if np.isfinite(pf_net) else np.nan,
                    "mean_mfe": round(float(g["mfe"].mean()), 1),
                    "mean_mae": round(float(g["mae"].mean()), 1),
                    "mfe_mae_ratio": round(float(g["mfe"].mean() / g["mae"].mean()), 2) if float(g["mae"].mean()) > 0 else np.nan,
                    "drag_pct": round(float(drag_pct), 1) if np.isfinite(drag_pct) else np.nan,
                })
        return pd.DataFrame(rows)

    # Export Audits for each Strategy
    for strat_name, filename in [
        ("BENCHMARK_A_IB_BREAKOUT", "audit_ib_breakout_by_regime.csv"),
        ("BENCHMARK_B1_DRIVE_60M", "audit_drive_60m_by_regime.csv"),
        ("BENCHMARK_B2_DRIVE_EOD", "audit_drive_eod_by_regime.csv"),
        ("BENCHMARK_C_FIXED_CLOCK_60M", "audit_fixed_clock_by_regime.csv"),
    ]:
        sub_strat = df_trades[df_trades["strategy"] == strat_name].copy()
        audit_table = summarize_strategy(sub_strat)
        audit_table.to_csv(ARTIFACTS / filename, index=False)
        print(f"\n--- {strat_name} STRATIFIED BY VOLATILITY REGIME ---")
        print(audit_table.to_string(index=False))


if __name__ == "__main__":
    main()
