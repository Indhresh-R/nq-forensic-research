"""
Strategy 35: Cost Sensitivity and Friction Sweep
Evaluates NQ and ES candidate performance across a spectrum of round-trip transaction costs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

ARTIFACTS = ROOT / "artifacts" / "35_bull_bear_flags"
TRADES_FILE = ARTIFACTS / "flag_trades_master.parquet"

POINT_VAL = {"nq": 20.0, "es": 50.0}
COST_LEVELS = {
    "nq": [0.0, 0.25, 0.50, 0.75, 1.0, 1.5, 2.0],
    "es": [0.0, 0.125, 0.25, 0.50, 0.75, 1.0],
}


def main():
    if not TRADES_FILE.exists():
        print(f"Error: {TRADES_FILE} does not exist.")
        return

    df = pd.read_parquet(TRADES_FILE)
    rows = []

    for m in ["nq", "es"]:
        pt_val = POINT_VAL[m]
        m_df = df[df["market"] == m]
        
        for cand in sorted(m_df["candidate"].unique()):
            c_df = m_df[m_df["candidate"] == cand]
            
            for cost in COST_LEVELS[m]:
                # Recompute net pts and net dollars
                c_df_copy = c_df.copy()
                c_df_copy["net_pts"] = c_df_copy["gross_pts"] - cost
                c_df_copy["net_dollars"] = c_df_copy["net_pts"] * pt_val
                
                for sp in ["IS", "Validation", "OOS"]:
                    sp_df = c_df_copy[c_df_copy["split"] == sp]
                    n = len(sp_df)
                    if n == 0:
                        continue
                    wins = sp_df[sp_df["net_dollars"] > 0]
                    losses = sp_df[sp_df["net_dollars"] <= 0]
                    wr = len(wins) / n
                    gw = wins["net_dollars"].sum()
                    gl = abs(losses["net_dollars"].sum())
                    pf = gw / gl if gl > 0 else (99.0 if gw > 0 else 0.0)
                    e_pts = sp_df["net_pts"].mean()
                    e_dlr = sp_df["net_dollars"].mean()
                    
                    rows.append({
                        "market": m.upper(),
                        "candidate": cand,
                        "cost_pts": cost,
                        "split": sp,
                        "n": n,
                        "win_rate": round(wr, 4),
                        "pf": round(pf, 3),
                        "e_pts": round(e_pts, 2),
                        "e_dollars": round(e_dlr, 2),
                    })

    cost_df = pd.DataFrame(rows)
    cost_csv = ARTIFACTS / "audit_cost_sensitivity.csv"
    cost_df.to_csv(cost_csv, index=False)
    print(f"Saved cost sensitivity results to {cost_csv}")


if __name__ == "__main__":
    main()
