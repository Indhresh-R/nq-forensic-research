"""
Strategy 36: Symmetric Stop/Target Active Trading Pass (Mode B)
Evaluates whether active risk boundaries create an exploitable edge on Long vs Short.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from common.nq_session import load_nq
from common.splits import split_of

ARTIFACTS = ROOT / "artifacts" / "36_nq_unconditional_long_bias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

RTH_OPEN = 9 * 60 + 30
RTH_CLOSE = 15 * 60 + 55
COST_PTS = 1.0

CLOCKS = {
    "09:35": 9 * 60 + 35,
    "10:30": 10 * 60 + 30,
    "12:00": 12 * 60 + 0,
    "14:00": 14 * 60 + 0,
}

MULTIPLES = [1.0, 1.5]


def main():
    print("=" * 80)
    print("STRATEGY 36: SYMMETRIC ACTIVE TRADING PASS (MODE B: ATR BOUNDARIES)")
    print("=" * 80)
    
    nq = load_nq()
    rth = nq[(nq.ny_min >= RTH_OPEN) & (nq.ny_min <= RTH_CLOSE)].copy()
    
    # Aggregate 5m bars for ATR calculation
    rth["bar_5m_idx"] = (rth["ny_min"] - RTH_OPEN) // 5
    grouped = rth.groupby(["session_date", "bar_5m_idx"], sort=True)
    bars_5m = grouped.agg(
        ts=("ts", "last"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        close_ny_min=("ny_min", "last"),
        year=("year", "first"),
    ).reset_index()
    
    tr1 = bars_5m["high"] - bars_5m["low"]
    prev_close = bars_5m["close"].shift(1)
    tr = pd.concat([tr1, (bars_5m["high"] - prev_close).abs(), (bars_5m["low"] - prev_close).abs()], axis=1).max(axis=1)
    bars_5m["atr20"] = tr.rolling(20, min_periods=5).mean()
    
    # Map ATR back to session and clock
    atr_map = bars_5m.set_index(["session_date", "close_ny_min"])["atr20"].to_dict()
    
    rth_indexed = rth.set_index(["session_date", "ny_min"]).sort_index()
    
    records = []
    
    for clock_name, clock_min in CLOCKS.items():
        entry_min = clock_min + 1
        
        for mult in MULTIPLES:
            cand_name = f"SYM_{mult}R"
            
            for sd, g in rth.groupby("session_date", sort=True):
                if (sd, entry_min) not in rth_indexed.index:
                    continue
                    
                # Look up nearest preceding 5m ATR
                # 5m bar ending at or just before clock_min
                prior_5m_close_min = (clock_min // 5) * 5 + 4
                atr = atr_map.get((sd, prior_5m_close_min))
                if atr is None or np.isnan(atr) or atr <= 0:
                    continue
                    
                entry_bar = rth_indexed.loc[(sd, entry_min)]
                entry_price = float(entry_bar["open"])
                yr = int(entry_bar["year"])
                
                day_path = rth_indexed.loc[sd].loc[entry_min:RTH_CLOSE]
                hi_arr = day_path["high"].to_numpy(float)
                lo_arr = day_path["low"].to_numpy(float)
                cl_arr = day_path["close"].to_numpy(float)
                n_path = len(hi_arr)
                if n_path == 0:
                    continue
                    
                risk_pts = mult * atr
                
                # Evaluate LONG
                stop_long = entry_price - risk_pts
                target_long = entry_price + risk_pts
                exit_price_long = None
                for m in range(n_path):
                    h_hit = hi_arr[m] >= target_long
                    l_hit = lo_arr[m] <= stop_long
                    if h_hit and l_hit: # stop first
                        exit_price_long = stop_long
                        break
                    elif l_hit:
                        exit_price_long = stop_long
                        break
                    elif h_hit:
                        exit_price_long = target_long
                        break
                if exit_price_long is None:
                    exit_price_long = cl_arr[-1]
                    
                gross_long = exit_price_long - entry_price
                records.append({
                    "clock": clock_name,
                    "candidate": cand_name,
                    "side": "LONG",
                    "year": yr,
                    "split": split_of(yr),
                    "gross_pts": gross_long,
                    "net_pts": gross_long - COST_PTS,
                })
                
                # Evaluate SHORT
                stop_short = entry_price + risk_pts
                target_short = entry_price - risk_pts
                exit_price_short = None
                for m in range(n_path):
                    l_hit = lo_arr[m] <= target_short
                    h_hit = hi_arr[m] >= stop_short
                    if h_hit and l_hit: # stop first
                        exit_price_short = stop_short
                        break
                    elif h_hit:
                        exit_price_short = stop_short
                        break
                    elif l_hit:
                        exit_price_short = target_short
                        break
                if exit_price_short is None:
                    exit_price_short = cl_arr[-1]
                    
                gross_short = entry_price - exit_price_short
                records.append({
                    "clock": clock_name,
                    "candidate": cand_name,
                    "side": "SHORT",
                    "year": yr,
                    "split": split_of(yr),
                    "gross_pts": gross_short,
                    "net_pts": gross_short - COST_PTS,
                })
                
    df_active = pd.DataFrame(records)
    active_path = ARTIFACTS / "symmetric_active_trades.parquet"
    df_active.to_parquet(active_path, index=False)
    print(f"Saved {len(df_active):,} active trade records to {active_path}")
    
    # Summary
    summary_rows = []
    for clock_name in CLOCKS.keys():
        for mult in MULTIPLES:
            cand_name = f"SYM_{mult}R"
            sub = df_active[(df_active["clock"] == clock_name) & (df_active["candidate"] == cand_name)]
            
            for side in ["LONG", "SHORT"]:
                s_df = sub[sub["side"] == side]
                
                def calc_s(d):
                    n = len(d)
                    if n == 0: return {"n": 0, "wr": 0.0, "pf": 0.0, "e_net": 0.0}
                    w = d[d["net_pts"] > 0]
                    l = d[d["net_pts"] <= 0]
                    gw = w["net_pts"].sum()
                    gl = abs(l["net_pts"].sum())
                    pf = gw / gl if gl > 0 else 0.0
                    return {"n": n, "wr": round(len(w)/n, 4), "pf": round(pf, 3), "e_net": round(d["net_pts"].mean(), 2)}
                    
                is_m = calc_s(s_df[s_df["split"] == "IS"])
                val_m = calc_s(s_df[s_df["split"] == "Validation"])
                oos_m = calc_s(s_df[s_df["split"] == "OOS"])
                oos25_m = calc_s(s_df[s_df["year"] == 2025])
                oos26_m = calc_s(s_df[s_df["year"] == 2026])
                
                summary_rows.append({
                    "clock": clock_name,
                    "candidate": cand_name,
                    "side": side,
                    "IS_N": is_m["n"], "IS_WR": is_m["wr"], "IS_PF": is_m["pf"], "IS_E_net": is_m["e_net"],
                    "Val_N": val_m["n"], "Val_WR": val_m["wr"], "Val_PF": val_m["pf"], "Val_E_net": val_m["e_net"],
                    "OOS_N": oos_m["n"], "OOS_WR": oos_m["wr"], "OOS_PF": oos_m["pf"], "OOS_E_net": oos_m["e_net"],
                    "2025_E_net": oos25_m["e_net"],
                    "2026_E_net": oos26_m["e_net"],
                })
                
    sum_df = pd.DataFrame(summary_rows)
    sum_csv = ARTIFACTS / "symmetric_active_summary.csv"
    sum_df.to_csv(sum_csv, index=False)
    print(f"Saved active summary to {sum_csv}")
    print("\n" + "=" * 120)
    print("SYMMETRIC ACTIVE TRADING SUMMARY (NET OF 1.0 PT FRICTION)")
    print("=" * 120)
    print(sum_df[["clock", "candidate", "side", "IS_WR", "IS_PF", "IS_E_net", "Val_PF", "Val_E_net", "OOS_PF", "OOS_E_net", "2025_E_net", "2026_E_net"]].to_string(index=False))


if __name__ == "__main__":
    main()
