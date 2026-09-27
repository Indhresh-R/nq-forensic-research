"""
Strategy 36: Passive Beta Attribution & Risk-Adjusted Comparison
Tests whether active long exposure generates genuine Alpha or simply represents
a fee-burdened, diluted capture of passive equity index beta.
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


def calc_stats(daily_net_series: pd.Series) -> dict:
    n_days = len(daily_net_series)
    if n_days == 0:
        return {"n": 0, "annual_pts": 0.0, "annual_vol": 0.0, "sharpe": 0.0, "max_dd_pts": 0.0, "calmar": 0.0}
        
    mean_daily = daily_net_series.mean()
    std_daily = daily_net_series.std()
    
    annual_pts = mean_daily * 252
    annual_vol = std_daily * np.sqrt(252) if std_daily > 0 else 0.0
    sharpe = annual_pts / annual_vol if annual_vol > 0 else 0.0
    
    cum = daily_net_series.cumsum()
    peak = cum.cummax()
    dd = peak - cum
    max_dd = float(dd.max())
    calmar = annual_pts / max_dd if max_dd > 0 else 0.0
    
    return {
        "n_days": n_days,
        "tot_net_pts": round(cum.iloc[-1], 2),
        "annual_pts": round(annual_pts, 2),
        "annual_vol": round(annual_vol, 2),
        "sharpe": round(sharpe, 3),
        "max_dd_pts": round(max_dd, 2),
        "calmar": round(calmar, 3),
    }


def main():
    print("=" * 80)
    print("STRATEGY 36: PASSIVE BETA ATTRIBUTION & BENCHMARK AUDIT")
    print("=" * 80)
    
    nq = load_nq()
    rth = nq[(nq.ny_min >= RTH_OPEN) & (nq.ny_min <= RTH_CLOSE)].copy()
    rth_indexed = rth.set_index(["session_date", "ny_min"]).sort_index()
    
    # 1. Passive RTH Buy-and-Hold Benchmark: Buy 09:30 open, sell 15:55 close
    passive_records = []
    for sd, g in rth.groupby("session_date", sort=True):
        if (sd, RTH_OPEN) not in rth_indexed.index or (sd, RTH_CLOSE) not in rth_indexed.index:
            continue
        op = float(rth_indexed.loc[(sd, RTH_OPEN)]["open"])
        cl = float(rth_indexed.loc[(sd, RTH_CLOSE)]["close"])
        yr = int(rth_indexed.loc[(sd, RTH_OPEN)]["year"])
        
        gross = cl - op
        net = gross - COST_PTS # paying 1 turnover per day
        passive_records.append({
            "session_date": str(sd),
            "year": yr,
            "split": split_of(yr),
            "gross_pts": gross,
            "net_pts": net,
            "friction_pts": COST_PTS,
        })
    df_passive = pd.DataFrame(passive_records)
    
    # 2. Compare against Active Long Horizon Trades from pure_drift_trades.parquet
    drift_trades_file = ARTIFACTS / "pure_drift_trades.parquet"
    if not drift_trades_file.exists():
        print(f"Error: {drift_trades_file} not found. Run run_preregistered_drift_pass.py first.")
        return
        
    df_drift = pd.read_parquet(drift_trades_file)
    
    # Analyze benchmarks across splits
    rows = []
    
    for sp in ["IS", "Validation", "OOS", "ALL"]:
        p_sub = df_passive if sp == "ALL" else df_passive[df_passive["split"] == sp]
        p_stats = calc_stats(p_sub.set_index("session_date")["net_pts"])
        p_gross_sum = p_sub["gross_pts"].sum()
        p_fric_sum = p_sub["friction_pts"].sum()
        
        rows.append({
            "strategy": "PASSIVE_RTH_HOLD (09:30-15:55)",
            "split": sp,
            **p_stats,
            "friction_drag_pct": round((p_fric_sum / p_gross_sum) * 100, 2) if p_gross_sum > 0 else 0.0,
        })
        
        # Compare active long candidates (e.g. Clock 09:35 session close, Clock 10:30 session close, Clock 09:35 60m)
        for clk in ["09:35", "10:30", "12:00"]:
            for horiz in ["60m", "session_close"]:
                a_sub = df_drift[(df_drift["clock"] == clk) & (df_drift["horizon"] == horiz) & (df_drift["side"] == "LONG")]
                if sp != "ALL":
                    a_sub = a_sub[a_sub["split"] == sp]
                if len(a_sub) == 0:
                    continue
                    
                a_daily = a_sub.groupby("session_date")["net_pts"].sum()
                a_stats = calc_stats(a_daily)
                a_gross_sum = a_sub["gross_pts"].sum()
                a_fric_sum = len(a_sub) * COST_PTS
                
                rows.append({
                    "strategy": f"ACTIVE_LONG ({clk} {horiz})",
                    "split": sp,
                    **a_stats,
                    "friction_drag_pct": round((a_fric_sum / a_gross_sum) * 100, 2) if a_gross_sum > 0 else 0.0,
                })
                
    comp_df = pd.DataFrame(rows)
    comp_csv = ARTIFACTS / "passive_beta_comparison.csv"
    comp_df.to_csv(comp_csv, index=False)
    print(f"Saved passive beta comparison to {comp_csv}")
    print("\n" + "=" * 120)
    print("PASSIVE RTH BENCHMARK VS ACTIVE LONG TRADING (SHARPE & DRAWDOWN ATTRIBUTION)")
    print("=" * 120)
    print(comp_df[["strategy", "split", "tot_net_pts", "annual_pts", "sharpe", "max_dd_pts", "calmar", "friction_drag_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
