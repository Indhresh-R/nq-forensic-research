"""
Strategy 36: Pure Horizon Drift Backtest Pass
Evaluates unconditional Long vs Short forward returns across 5m, 15m, 30m, 60m, and Session Close.
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

ARTIFACTS = ROOT / "artifacts" / "36_nq_unconditional_long_bias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30   # 09:30
RTH_CLOSE = 15 * 60 + 55 # 15:55
COST_PTS = 1.0           # Baseline NQ round-trip
PT_VAL = 20.0

CLOCKS = {
    "09:35": 9 * 60 + 35,
    "10:30": 10 * 60 + 30,
    "12:00": 12 * 60 + 0,
    "14:00": 14 * 60 + 0,
}

HORIZONS = {
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "60m": 60,
    "session_close": None, # exit at 15:55
}


def compute_metrics(trades: pd.DataFrame) -> dict[str, Any]:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": 0.0, "pf": 0.0, "gross_pts": 0.0, "net_pts": 0.0, "e_gross": 0.0, "e_net": 0.0, "max_dd_pts": 0.0}
    
    wins = trades[trades["net_pts"] > 0]
    losses = trades[trades["net_pts"] <= 0]
    n_wins = len(wins)
    wr = n_wins / n
    
    gross_win = wins["net_pts"].sum()
    gross_loss = abs(losses["net_pts"].sum())
    pf = gross_win / gross_loss if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
    
    tot_gross = trades["gross_pts"].sum()
    tot_net = trades["net_pts"].sum()
    
    # Cumulative drawdown in points
    cum_pts = trades["net_pts"].cumsum()
    peak = cum_pts.cummax()
    dd = peak - cum_pts
    max_dd = float(dd.max()) if len(dd) else 0.0
    
    return {
        "n": n,
        "win_rate": round(wr, 4),
        "pf": round(pf, 3),
        "gross_pts": round(tot_gross, 2),
        "net_pts": round(tot_net, 2),
        "e_gross": round(tot_gross / n, 2),
        "e_net": round(tot_net / n, 2),
        "max_dd_pts": round(max_dd, 2),
    }


def main():
    print("=" * 80)
    print("STRATEGY 36: UNCONDITIONAL NQ DRIFT PASS (MODE A: PURE HORIZONS)")
    print("=" * 80)
    
    print("Loading continuous NQ 1-minute dataset...")
    nq = load_nq()
    rth = nq[(nq.ny_min >= RTH_OPEN) & (nq.ny_min <= RTH_CLOSE)].copy()
    print(f"Loaded {len(rth):,} RTH bars across {rth['session_date'].nunique():,} sessions.")
    
    rth_indexed = rth.set_index(["session_date", "ny_min"]).sort_index()
    
    records = []
    
    # Run Arm 1: Session Milestone Clocks
    for clock_name, clock_min in CLOCKS.items():
        entry_min = clock_min + 1 # enter at open of T+1
        
        for h_name, h_mins in HORIZONS.items():
            for sd, g in rth.groupby("session_date", sort=True):
                if (sd, entry_min) not in rth_indexed.index:
                    continue
                    
                entry_bar = rth_indexed.loc[(sd, entry_min)]
                entry_price = float(entry_bar["open"])
                yr = int(entry_bar["year"])
                
                # Determine exit minute
                if h_mins is None:
                    exit_min = RTH_CLOSE
                else:
                    exit_min = entry_min + h_mins - 1
                    if exit_min > RTH_CLOSE:
                        exit_min = RTH_CLOSE
                        
                if (sd, exit_min) not in rth_indexed.index:
                    continue
                    
                exit_bar = rth_indexed.loc[(sd, exit_min)]
                exit_price = float(exit_bar["close"])
                
                # Long
                gross_long = exit_price - entry_price
                net_long = gross_long - COST_PTS
                records.append({
                    "arm": "SESSION_CLOCK",
                    "clock": clock_name,
                    "horizon": h_name,
                    "session_date": str(sd),
                    "year": yr,
                    "split": split_of(yr),
                    "side": "LONG",
                    "entry_min": entry_min,
                    "exit_min": exit_min,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_pts": gross_long,
                    "net_pts": net_long,
                })
                
                # Short
                gross_short = entry_price - exit_price
                net_short = gross_short - COST_PTS
                records.append({
                    "arm": "SESSION_CLOCK",
                    "clock": clock_name,
                    "horizon": h_name,
                    "session_date": str(sd),
                    "year": yr,
                    "split": split_of(yr),
                    "side": "SHORT",
                    "entry_min": entry_min,
                    "exit_min": exit_min,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_pts": gross_short,
                    "net_pts": net_short,
                })
                
    df_trades = pd.DataFrame(records)
    ledger_path = ARTIFACTS / "pure_drift_trades.parquet"
    df_trades.to_parquet(ledger_path, index=False)
    print(f"Saved {len(df_trades):,} trade records to {ledger_path}")
    
    # Generate pairwise Long vs Short performance matrix
    summary_rows = []
    
    for clock_name in CLOCKS.keys():
        for h_name in HORIZONS.keys():
            sub = df_trades[(df_trades["clock"] == clock_name) & (df_trades["horizon"] == h_name)]
            
            for side in ["LONG", "SHORT"]:
                s_df = sub[sub["side"] == side]
                
                is_m = compute_metrics(s_df[s_df["split"] == "IS"])
                val_m = compute_metrics(s_df[s_df["split"] == "Validation"])
                oos_m = compute_metrics(s_df[s_df["split"] == "OOS"])
                oos25_m = compute_metrics(s_df[s_df["year"] == 2025])
                oos26_m = compute_metrics(s_df[s_df["year"] == 2026])
                
                summary_rows.append({
                    "clock": clock_name,
                    "horizon": h_name,
                    "side": side,
                    "IS_N": is_m["n"],
                    "IS_WR": is_m["win_rate"],
                    "IS_PF": is_m["pf"],
                    "IS_E_gross": is_m["e_gross"],
                    "IS_E_net": is_m["e_net"],
                    "Val_N": val_m["n"],
                    "Val_WR": val_m["win_rate"],
                    "Val_PF": val_m["pf"],
                    "Val_E_net": val_m["e_net"],
                    "OOS_N": oos_m["n"],
                    "OOS_WR": oos_m["win_rate"],
                    "OOS_PF": oos_m["pf"],
                    "OOS_E_net": oos_m["e_net"],
                    "2025_E_net": oos25_m["e_net"],
                    "2026_E_net": oos26_m["e_net"],
                })
                
    sum_df = pd.DataFrame(summary_rows)
    sum_csv = ARTIFACTS / "pure_drift_summary.csv"
    sum_df.to_csv(sum_csv, index=False)
    print(f"Saved summary matrix to {sum_csv}")
    
    # Print formatted overview
    print("\n" + "=" * 120)
    print("UNCONDITIONAL LONG VS SHORT PERFORMANCE MATRIX (NET OF 1.0 PT FRICTION)")
    print("=" * 120)
    print(sum_df[["clock", "horizon", "side", "IS_WR", "IS_PF", "IS_E_net", "Val_PF", "Val_E_net", "OOS_PF", "OOS_E_net", "2025_E_net", "2026_E_net"]].to_string(index=False))
    print("=" * 120)


if __name__ == "__main__":
    main()
