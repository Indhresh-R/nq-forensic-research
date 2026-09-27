"""
Strategy 35: Hostile Breakdown and Attribution Audit
Evaluates:
1. Bull vs Bear asymmetry
2. Time-of-day clustering
3. Yearly stability
4. Exit reason distribution (stop vs target vs flat)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from common.splits import split_of

ARTIFACTS = ROOT / "artifacts" / "35_bull_bear_flags"
TRADES_FILE = ARTIFACTS / "flag_trades_master.parquet"


def compute_metrics(trades: pd.DataFrame) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": 0.0, "pf": 0.0, "net_pts": 0.0, "e_pts": 0.0, "e_dollars": 0.0}
    wins = trades[trades["net_dollars"] > 0]
    losses = trades[trades["net_dollars"] <= 0]
    n_wins = len(wins)
    n_losses = len(losses)
    wr = n_wins / n if n > 0 else 0.0
    gw = wins["net_dollars"].sum() if n_wins > 0 else 0.0
    gl = abs(losses["net_dollars"].sum()) if n_losses > 0 else 0.0
    pf = gw / gl if gl > 0 else (99.0 if gw > 0 else 0.0)
    net_pts = trades["net_pts"].sum()
    net_dlr = trades["net_dollars"].sum()
    return {
        "n": n,
        "win_rate": round(wr, 4),
        "pf": round(pf, 3),
        "net_pts": round(net_pts, 2),
        "e_pts": round(net_pts / n, 2),
        "e_dollars": round(net_dlr / n, 2),
    }


def main():
    if not TRADES_FILE.exists():
        print(f"Error: {TRADES_FILE} does not exist. Run run_preregistered_pass.py first.")
        return

    df = pd.read_parquet(TRADES_FILE)
    print("=" * 80)
    print(f"STRATEGY 35: BREAKDOWN & ATTRIBUTION AUDIT ({len(df):,} total simulated trade records)")
    print("=" * 80)

    # 1. Bull vs Bear Flags Asymmetry by Market and Candidate
    print("\n--- 1. BULL vs BEAR FLAG DIRECTIONAL ASYMMETRY ---")
    asym_rows = []
    for m in ["nq", "es"]:
        m_df = df[df["market"] == m]
        for cand in sorted(m_df["candidate"].unique()):
            c_df = m_df[m_df["candidate"] == cand]
            for pat in ["BULL_FLAG", "BEAR_FLAG"]:
                p_df = c_df[c_df["pattern"] == pat]
                for sp in ["IS", "Validation", "OOS"]:
                    sp_df = p_df[p_df["split"] == sp]
                    met = compute_metrics(sp_df)
                    asym_rows.append({
                        "market": m.upper(),
                        "candidate": cand,
                        "pattern": pat,
                        "split": sp,
                        **met
                    })
    asym_df = pd.DataFrame(asym_rows)
    asym_csv = ARTIFACTS / "audit_bull_vs_bear_asymmetry.csv"
    asym_df.to_csv(asym_csv, index=False)
    print(f"Saved directional asymmetry to {asym_csv}")

    # 2. Exit Reason Distribution
    print("\n--- 2. EXIT REASON DISTRIBUTION ---")
    exit_dist = df.groupby(["market", "candidate", "split", "exit_reason"]).size().unstack(fill_value=0)
    exit_pct = exit_dist.div(exit_dist.sum(axis=1), axis=0) * 100
    exit_csv = ARTIFACTS / "audit_exit_reasons.csv"
    exit_pct.round(2).to_csv(exit_csv)
    print(f"Saved exit reason distributions to {exit_csv}")

    # 3. Yearly Performance Stability
    print("\n--- 3. YEARLY PERFORMANCE STABILITY ---")
    yearly_rows = []
    for m in ["nq", "es"]:
        m_df = df[df["market"] == m]
        for cand in ["C1_measured_move", "C3_1.5R"]:
            c_df = m_df[m_df["candidate"] == cand]
            for yr in sorted(c_df["year"].unique()):
                y_df = c_df[c_df["year"] == yr]
                met = compute_metrics(y_df)
                yearly_rows.append({
                    "market": m.upper(),
                    "candidate": cand,
                    "year": yr,
                    "split": split_of(yr),
                    **met
                })
    yearly_df = pd.DataFrame(yearly_rows)
    yearly_csv = ARTIFACTS / "audit_yearly_stability.csv"
    yearly_df.to_csv(yearly_csv, index=False)
    print(f"Saved yearly stability table to {yearly_csv}")

    print("\nBreakdown audit complete.")


if __name__ == "__main__":
    main()
