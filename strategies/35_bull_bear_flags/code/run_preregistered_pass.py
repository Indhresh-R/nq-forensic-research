"""
Strategy 35: Bull Flags and Bear Flags -- Frozen Pre-Registered Backtest Pass
Evaluates continuous NQ and ES futures (2010-2026).
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

from common.nq_session import load_es, load_nq
from common.splits import split_of

ARTIFACTS = ROOT / "artifacts" / "35_bull_bear_flags"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30   # 09:30
RTH_CLOSE = 15 * 60 + 55 # 15:55
MIN_SIGNAL_MIN = 9 * 60 + 45 # 09:45
MAX_SIGNAL_MIN = 15 * 60 + 0 # 15:00

COST_PTS = {"nq": 1.0, "es": 0.5}
POINT_VAL = {"nq": 20.0, "es": 50.0}
TICK_SIZE = {"nq": 0.25, "es": 0.25}


def aggregate_5m_bars(rth_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate 1-minute RTH data into 5-minute completed bars."""
    # 5m bar index: 09:30-09:34 closes at 09:34 (or represented by 09:35 open)
    # Standard: bins of 5 minutes: [570, 575), [575, 580), ...
    rth_df = rth_df.copy()
    rth_df["bar_5m_idx"] = (rth_df["ny_min"] - RTH_OPEN) // 5
    
    grouped = rth_df.groupby(["session_date", "bar_5m_idx"], sort=True)
    bars_5m = grouped.agg(
        ts=("ts", "last"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        close_ny_min=("ny_min", "last"),
        year=("year", "first"),
    ).reset_index()
    
    # Calculate ATR 20 on 5-minute bars
    tr1 = bars_5m["high"] - bars_5m["low"]
    prev_close = bars_5m["close"].shift(1)
    tr2 = (bars_5m["high"] - prev_close).abs()
    tr3 = (bars_5m["low"] - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    bars_5m["atr20"] = tr.rolling(20, min_periods=5).mean()
    
    return bars_5m


def scan_flag_signals(bars_5m: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Detect causal bull and bear flag breakout signals on completed 5m bars.
    Pole: 4 completed 5m bars.
    Flag: k in [3..8] completed 5m bars.
    Breakout: current completed 5m bar.
    """
    signals = []
    
    for sd, g in bars_5m.groupby("session_date", sort=True):
        g = g.reset_index(drop=True)
        n_bars = len(g)
        if n_bars < 15:
            continue
            
        opens = g["open"].to_numpy(float)
        highs = g["high"].to_numpy(float)
        lows = g["low"].to_numpy(float)
        closes = g["close"].to_numpy(float)
        vols = g["volume"].to_numpy(float)
        atrs = g["atr20"].to_numpy(float)
        close_mins = g["close_ny_min"].to_numpy(int)
        years = g["year"].to_numpy(int)
        
        # We search for breakout at bar i
        # First breakout signal of the session wins per side
        found_bull = False
        found_bear = False
        
        for i in range(7, n_bars):
            cur_min = close_mins[i]
            if cur_min < MIN_SIGNAL_MIN or cur_min > MAX_SIGNAL_MIN:
                continue
            
            c_close = closes[i]
            year = years[i]
            
            # Test candidate flag lengths k from 3 to 8
            # Pole is bars [p-3 .. p], Flag is bars [p+1 .. i-1]
            # where p = i - 1 - k + 1 = i - k
            # So flag has k-1 consolidation bars prior to breakout bar i, OR k consolidation bars.
            # Let flag consolidation be k completed bars before bar i: bars [i - k .. i - 1].
            # Then pole is 4 bars preceding the flag: [i - k - 4 .. i - k - 1].
            
            # --- Bull Flag Check ---
            if not found_bull:
                for k in range(3, 9):
                    pole_start_idx = i - k - 4
                    pole_end_idx = i - k - 1
                    flag_start_idx = i - k
                    flag_end_idx = i - 1
                    
                    if pole_start_idx < 0:
                        continue
                        
                    p_open = opens[pole_start_idx]
                    p_close = closes[pole_end_idx]
                    p_disp = p_close - p_open
                    
                    atr = atrs[pole_end_idx]
                    if np.isnan(atr) or atr <= 0:
                        continue
                        
                    # Pole height >= 1.5 * ATR
                    if p_disp < 1.5 * atr:
                        continue
                        
                    # Pole directional efficiency >= 0.65
                    pole_high = np.max(highs[pole_start_idx : pole_end_idx + 1])
                    pole_low = np.min(lows[pole_start_idx : pole_end_idx + 1])
                    pole_sum_range = np.sum(highs[pole_start_idx : pole_end_idx + 1] - lows[pole_start_idx : pole_end_idx + 1])
                    if pole_sum_range <= 0 or (p_disp / pole_sum_range) < 0.65:
                        continue
                        
                    p_height = pole_high - pole_low
                    if p_height <= 0:
                        continue
                        
                    # Flag consolidation checks
                    f_high = np.max(highs[flag_start_idx : flag_end_idx + 1])
                    f_low = np.min(lows[flag_start_idx : flag_end_idx + 1])
                    f_range = f_high - f_low
                    
                    # 1) Max retracement <= 50% of pole
                    if f_low < (pole_high - 0.50 * p_height):
                        continue
                    # 2) Flag tightness <= 50% of pole height
                    if f_range > 0.50 * p_height:
                        continue
                    # 3) Volume contraction: mean flag vol <= mean pole vol
                    mean_pole_vol = np.mean(vols[pole_start_idx : pole_end_idx + 1])
                    mean_flag_vol = np.mean(vols[flag_start_idx : flag_end_idx + 1])
                    if mean_flag_vol > mean_pole_vol:
                        continue
                        
                    # 4) Breakout trigger at bar i: close > f_high
                    if c_close > f_high:
                        signals.append({
                            "session_date": sd,
                            "year": year,
                            "signal_5m_idx": i,
                            "signal_ny_min": cur_min,
                            "entry_ny_min": cur_min + 1,
                            "side": 1,
                            "pattern": "BULL_FLAG",
                            "pole_height": p_height,
                            "flag_high": f_high,
                            "flag_low": f_low,
                            "stop_price": f_low,
                            "k_flag": k,
                        })
                        found_bull = True
                        break # shortest qualifying k wins
                        
            # --- Bear Flag Check ---
            if not found_bear:
                for k in range(3, 9):
                    pole_start_idx = i - k - 4
                    pole_end_idx = i - k - 1
                    flag_start_idx = i - k
                    flag_end_idx = i - 1
                    
                    if pole_start_idx < 0:
                        continue
                        
                    p_open = opens[pole_start_idx]
                    p_close = closes[pole_end_idx]
                    p_disp = p_open - p_close # downward displacement
                    
                    atr = atrs[pole_end_idx]
                    if np.isnan(atr) or atr <= 0:
                        continue
                        
                    # Pole height >= 1.5 * ATR
                    if p_disp < 1.5 * atr:
                        continue
                        
                    # Pole directional efficiency >= 0.65
                    pole_high = np.max(highs[pole_start_idx : pole_end_idx + 1])
                    pole_low = np.min(lows[pole_start_idx : pole_end_idx + 1])
                    pole_sum_range = np.sum(highs[pole_start_idx : pole_end_idx + 1] - lows[pole_start_idx : pole_end_idx + 1])
                    if pole_sum_range <= 0 or (p_disp / pole_sum_range) < 0.65:
                        continue
                        
                    p_height = pole_high - pole_low
                    if p_height <= 0:
                        continue
                        
                    # Flag consolidation checks
                    f_high = np.max(highs[flag_start_idx : flag_end_idx + 1])
                    f_low = np.min(lows[flag_start_idx : flag_end_idx + 1])
                    f_range = f_high - f_low
                    
                    # 1) Max retracement <= 50% of pole
                    if f_high > (pole_low + 0.50 * p_height):
                        continue
                    # 2) Flag tightness <= 50% of pole height
                    if f_range > 0.50 * p_height:
                        continue
                    # 3) Volume contraction
                    mean_pole_vol = np.mean(vols[pole_start_idx : pole_end_idx + 1])
                    mean_flag_vol = np.mean(vols[flag_start_idx : flag_end_idx + 1])
                    if mean_flag_vol > mean_pole_vol:
                        continue
                        
                    # 4) Breakout trigger at bar i: close < f_low
                    if c_close < f_low:
                        signals.append({
                            "session_date": sd,
                            "year": year,
                            "signal_5m_idx": i,
                            "signal_ny_min": cur_min,
                            "entry_ny_min": cur_min + 1,
                            "side": -1,
                            "pattern": "BEAR_FLAG",
                            "pole_height": p_height,
                            "flag_high": f_high,
                            "flag_low": f_low,
                            "stop_price": f_high,
                            "k_flag": k,
                        })
                        found_bear = True
                        break
                        
            if found_bull and found_bear:
                break
                
    return signals


def simulate_trade_outcomes(
    signals: list[dict[str, Any]], 
    rth_1m: pd.DataFrame, 
    market: str
) -> pd.DataFrame:
    """
    Simulate minute-by-minute execution for each signal and candidate rule.
    C1: Measured Move (Target = 1.0 * Pole Height)
    C2: 1.0R
    C3: 1.5R
    C4: 2.0R
    C5: Session Close (flat at 15:55 ET)
    """
    cost_pts = COST_PTS[market]
    pt_val = POINT_VAL[market]
    
    # Pre-index 1m data by (session_date, ny_min)
    rth_indexed = rth_1m.set_index(["session_date", "ny_min"]).sort_index()
    
    trades = []
    
    for sig in signals:
        sd = sig["session_date"]
        entry_min = sig["entry_ny_min"]
        side = sig["side"]
        stop_price = sig["stop_price"]
        pole_height = sig["pole_height"]
        
        # Check if entry minute exists
        if (sd, entry_min) not in rth_indexed.index:
            continue
            
        entry_bar = rth_indexed.loc[(sd, entry_min)]
        entry_price = float(entry_bar["open"])
        
        # Invalidation risk R
        if side == 1:
            initial_risk = entry_price - stop_price
        else:
            initial_risk = stop_price - entry_price
            
        if initial_risk <= 0:
            continue
            
        # Get remaining minutes of session
        try:
            day_path = rth_indexed.loc[sd].loc[entry_min:RTH_CLOSE]
        except KeyError:
            continue
            
        hi_arr = day_path["high"].to_numpy(float)
        lo_arr = day_path["low"].to_numpy(float)
        cl_arr = day_path["close"].to_numpy(float)
        min_arr = day_path.index.to_numpy(int)
        n_path = len(hi_arr)
        if n_path == 0:
            continue
            
        # Define candidate targets
        targets = {
            "C1_measured_move": entry_price + side * pole_height,
            "C2_1.0R": entry_price + side * (1.0 * initial_risk),
            "C3_1.5R": entry_price + side * (1.5 * initial_risk),
            "C4_2.0R": entry_price + side * (2.0 * initial_risk),
            "C5_session_close": None,
        }
        
        for cand_name, target_price in targets.items():
            exit_price = None
            exit_reason = None
            exit_min = None
            
            for m in range(n_path):
                cur_hi = hi_arr[m]
                cur_lo = lo_arr[m]
                cur_m_min = min_arr[m]
                
                # Check stop and target collision
                hit_stop = False
                hit_target = False
                
                if side == 1:
                    if cur_lo <= stop_price:
                        hit_stop = True
                    if target_price is not None and cur_hi >= target_price:
                        hit_target = True
                else:
                    if cur_hi >= stop_price:
                        hit_stop = True
                    if target_price is not None and cur_lo <= target_price:
                        hit_target = True
                        
                # Hostile ambiguity: Stop first
                if hit_stop and hit_target:
                    exit_price = stop_price
                    exit_reason = "stop_collision"
                    exit_min = cur_m_min
                    break
                elif hit_stop:
                    exit_price = stop_price
                    exit_reason = "stop"
                    exit_min = cur_m_min
                    break
                elif hit_target:
                    exit_price = target_price
                    exit_reason = "target"
                    exit_min = cur_m_min
                    break
                    
            if exit_price is None:
                # EOD flat at 15:55 close
                exit_price = cl_arr[-1]
                exit_reason = "time_flat"
                exit_min = min_arr[-1]
                
            gross_pts = (exit_price - entry_price) * side
            net_pts = gross_pts - cost_pts
            net_dollars = net_pts * pt_val
            
            trades.append({
                "market": market,
                "candidate": cand_name,
                "session_date": str(sd),
                "year": sig["year"],
                "split": split_of(sig["year"]),
                "pattern": sig["pattern"],
                "side": side,
                "entry_ny_min": entry_min,
                "exit_ny_min": exit_min,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "stop_price": stop_price,
                "target_price": target_price,
                "initial_risk_pts": initial_risk,
                "exit_reason": exit_reason,
                "gross_pts": gross_pts,
                "net_pts": net_pts,
                "net_dollars": net_dollars,
            })
            
    return pd.DataFrame(trades)


def compute_metrics(trades: pd.DataFrame) -> dict[str, Any]:
    n = len(trades)
    if n == 0:
        return {
            "n": 0, "win_rate": 0.0, "profit_factor": 0.0, "payoff": 0.0,
            "net_pts": 0.0, "net_dollars": 0.0, "expectancy_pts": 0.0, "expectancy_dollars": 0.0,
        }
        
    wins = trades[trades["net_dollars"] > 0]
    losses = trades[trades["net_dollars"] <= 0]
    
    n_wins = len(wins)
    n_losses = len(losses)
    win_rate = n_wins / n if n > 0 else 0.0
    
    gross_win_dollars = wins["net_dollars"].sum() if n_wins > 0 else 0.0
    gross_loss_dollars = abs(losses["net_dollars"].sum()) if n_losses > 0 else 0.0
    
    pf = gross_win_dollars / gross_loss_dollars if gross_loss_dollars > 0 else (99.0 if gross_win_dollars > 0 else 0.0)
    payoff = (gross_win_dollars / n_wins) / (gross_loss_dollars / n_losses) if (n_wins > 0 and n_losses > 0 and gross_loss_dollars > 0) else 0.0
    
    net_pts = trades["net_pts"].sum()
    net_dollars = trades["net_dollars"].sum()
    
    return {
        "n": n,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(pf, 3),
        "payoff": round(payoff, 3),
        "net_pts": round(net_pts, 2),
        "net_dollars": round(net_dollars, 2),
        "expectancy_pts": round(net_pts / n, 2),
        "expectancy_dollars": round(net_dollars / n, 2),
    }


def main():
    print("=" * 70)
    print("Strategy 35: Bull Flags and Bear Flags Forensic Pass")
    print("=" * 70)
    
    all_trades = []
    
    for market in ["nq", "es"]:
        print(f"\nLoading {market.upper()} continuous 1-minute data...")
        raw_df = load_nq() if market == "nq" else load_es()
        
        # Filter to RTH
        rth_df = raw_df[(raw_df["ny_min"] >= RTH_OPEN) & (raw_df["ny_min"] <= RTH_CLOSE)].copy()
        print(f"Aggregating {len(rth_df):,} RTH 1-minute bars into 5-minute bars...")
        bars_5m = aggregate_5m_bars(rth_df)
        print(f"Built {len(bars_5m):,} 5-minute bars across {bars_5m['session_date'].nunique():,} sessions.")
        
        print("Scanning for Bull and Bear Flag setups...")
        signals = scan_flag_signals(bars_5m)
        print(f"Identified {len(signals):,} qualifying flag signals.")
        
        print("Simulating candidate trade executions against 1-minute paths...")
        trades = simulate_trade_outcomes(signals, rth_df, market)
        print(f"Generated {len(trades):,} trade records across candidate variants.")
        all_trades.append(trades)
        
    combined_trades = pd.concat(all_trades, ignore_index=True)
    
    # Save raw trades artifact
    trades_path = ARTIFACTS / "flag_trades_master.parquet"
    combined_trades.to_parquet(trades_path, index=False)
    print(f"\nSaved trade ledger to {trades_path}")
    
    # Compile summary table across Splits and Candidates
    summary_rows = []
    splits = ["IS", "Validation", "OOS"]
    
    for market in ["nq", "es"]:
        m_trades = combined_trades[combined_trades["market"] == market]
        for cand in sorted(m_trades["candidate"].unique()):
            c_trades = m_trades[m_trades["candidate"] == cand]
            
            # Overall
            tot_m = compute_metrics(c_trades)
            # IS
            is_m = compute_metrics(c_trades[c_trades["split"] == "IS"])
            # Val
            val_m = compute_metrics(c_trades[c_trades["split"] == "Validation"])
            # OOS
            oos_m = compute_metrics(c_trades[c_trades["split"] == "OOS"])
            # 2025 separate
            oos25_m = compute_metrics(c_trades[c_trades["year"] == 2025])
            # 2026 separate
            oos26_m = compute_metrics(c_trades[c_trades["year"] == 2026])
            
            summary_rows.append({
                "market": market.upper(),
                "candidate": cand,
                "IS_n": is_m["n"],
                "IS_WR": is_m["win_rate"],
                "IS_PF": is_m["profit_factor"],
                "IS_E_pts": is_m["expectancy_pts"],
                "Val_n": val_m["n"],
                "Val_WR": val_m["win_rate"],
                "Val_PF": val_m["profit_factor"],
                "Val_E_pts": val_m["expectancy_pts"],
                "OOS_n": oos_m["n"],
                "OOS_WR": oos_m["win_rate"],
                "OOS_PF": oos_m["profit_factor"],
                "OOS_E_pts": oos_m["expectancy_pts"],
                "2025_E_pts": oos25_m["expectancy_pts"],
                "2026_E_pts": oos26_m["expectancy_pts"],
            })
            
    summary_df = pd.DataFrame(summary_rows)
    summary_csv = ARTIFACTS / "candidate_performance_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    print(f"Saved performance summary to {summary_csv}")
    
    # Print formatted summary table
    print("\n" + "=" * 100)
    print("PRE-REGISTERED CANDIDATE PERFORMANCE MATRIX")
    print("=" * 100)
    print(summary_df.to_string(index=False))
    print("=" * 100)


if __name__ == "__main__":
    main()
