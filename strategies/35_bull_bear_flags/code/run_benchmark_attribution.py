"""
Strategy 35: Benchmark Attribution Audit
Tests whether the "Flag" consolidation provides any incremental edge over:
1. Pure Impulse (Pole alone, enter next open without consolidation)
2. Unconditional Same-TOD Buy/Sell Drift
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from common.nq_session import load_nq, load_es
from common.splits import split_of

ARTIFACTS = ROOT / "artifacts" / "35_bull_bear_flags"
RTH_OPEN = 9 * 60 + 30
RTH_CLOSE = 15 * 60 + 55
COST_PTS = {"nq": 1.0, "es": 0.5}
PT_VAL = {"nq": 20.0, "es": 50.0}


def test_pure_impulse(market: str = "nq"):
    raw = load_nq() if market == "nq" else load_es()
    rth = raw[(raw.ny_min >= RTH_OPEN) & (raw.ny_min <= RTH_CLOSE)].copy()
    
    # Construct 5m bars
    rth["bar_5m_idx"] = (rth["ny_min"] - RTH_OPEN) // 5
    grouped = rth.groupby(["session_date", "bar_5m_idx"], sort=True)
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
    
    tr1 = bars_5m["high"] - bars_5m["low"]
    prev_close = bars_5m["close"].shift(1)
    tr = pd.concat([tr1, (bars_5m["high"] - prev_close).abs(), (bars_5m["low"] - prev_close).abs()], axis=1).max(axis=1)
    bars_5m["atr20"] = tr.rolling(20, min_periods=5).mean()
    
    rth_indexed = rth.set_index(["session_date", "ny_min"]).sort_index()
    
    records = []
    cost = COST_PTS[market]
    pt_val = PT_VAL[market]
    
    for sd, g in bars_5m.groupby("session_date", sort=True):
        g = g.reset_index(drop=True)
        if len(g) < 10:
            continue
        opens = g["open"].to_numpy(float)
        highs = g["high"].to_numpy(float)
        lows = g["low"].to_numpy(float)
        closes = g["close"].to_numpy(float)
        atrs = g["atr20"].to_numpy(float)
        close_mins = g["close_ny_min"].to_numpy(int)
        years = g["year"].to_numpy(int)
        
        found_bull = False
        found_bear = False
        
        for i in range(4, len(g)):
            c_min = close_mins[i]
            if c_min < (9 * 60 + 45) or c_min > (15 * 60):
                continue
                
            p_open = opens[i - 3]
            p_close = closes[i]
            atr = atrs[i]
            if np.isnan(atr) or atr <= 0:
                continue
                
            # Bull pole
            if not found_bull and (p_close - p_open) >= 1.5 * atr:
                p_sum_range = np.sum(highs[i-3:i+1] - lows[i-3:i+1])
                if p_sum_range > 0 and ((p_close - p_open) / p_sum_range) >= 0.65:
                    # Enter next minute open, hold to 15:55
                    entry_min = c_min + 1
                    if (sd, entry_min) in rth_indexed.index:
                        entry_bar = rth_indexed.loc[(sd, entry_min)]
                        entry_price = float(entry_bar["open"])
                        day_path = rth_indexed.loc[sd].loc[entry_min:RTH_CLOSE]
                        exit_price = float(day_path["close"].iloc[-1])
                        net_pts = (exit_price - entry_price) - cost
                        records.append({
                            "market": market.upper(),
                            "type": "PURE_POLE_NO_FLAG",
                            "side": 1,
                            "year": years[i],
                            "split": split_of(years[i]),
                            "net_pts": net_pts,
                            "net_dollars": net_pts * pt_val,
                        })
                        found_bull = True
                        
            # Bear pole
            if not found_bear and (p_open - p_close) >= 1.5 * atr:
                p_sum_range = np.sum(highs[i-3:i+1] - lows[i-3:i+1])
                if p_sum_range > 0 and ((p_open - p_close) / p_sum_range) >= 0.65:
                    entry_min = c_min + 1
                    if (sd, entry_min) in rth_indexed.index:
                        entry_bar = rth_indexed.loc[(sd, entry_min)]
                        entry_price = float(entry_bar["open"])
                        day_path = rth_indexed.loc[sd].loc[entry_min:RTH_CLOSE]
                        exit_price = float(day_path["close"].iloc[-1])
                        net_pts = (entry_price - exit_price) - cost
                        records.append({
                            "market": market.upper(),
                            "type": "PURE_POLE_NO_FLAG",
                            "side": -1,
                            "year": years[i],
                            "split": split_of(years[i]),
                            "net_pts": net_pts,
                            "net_dollars": net_pts * pt_val,
                        })
                        found_bear = True
                        
            if found_bull and found_bear:
                break
                
    return pd.DataFrame(records)


def main():
    print("Testing Pure Pole Breakouts without Flag Consolidation (Attribution Benchmark)...")
    res_list = []
    for m in ["nq", "es"]:
        df = test_pure_impulse(m)
        for sp in ["IS", "Validation", "OOS"]:
            for s in [1, -1]:
                sub = df[(df["split"] == sp) & (df["side"] == s)]
                n = len(sub)
                if n == 0:
                    continue
                wins = sub[sub["net_dollars"] > 0]
                losses = sub[sub["net_dollars"] <= 0]
                wr = len(wins) / n
                gw = wins["net_dollars"].sum()
                gl = abs(losses["net_dollars"].sum())
                pf = gw / gl if gl > 0 else 0.0
                res_list.append({
                    "market": m.upper(),
                    "side": "LONG" if s == 1 else "SHORT",
                    "split": sp,
                    "n": n,
                    "win_rate": round(wr, 4),
                    "pf": round(pf, 3),
                    "e_pts": round(sub["net_pts"].mean(), 2),
                    "e_dollars": round(sub["net_dollars"].mean(), 2),
                })
    res_df = pd.DataFrame(res_list)
    out_csv = ARTIFACTS / "audit_pure_impulse_benchmark.csv"
    res_df.to_csv(out_csv, index=False)
    print(res_df.to_string(index=False))


if __name__ == "__main__":
    main()
