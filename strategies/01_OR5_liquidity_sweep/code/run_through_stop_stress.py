"""Through-stop stress only — classification already proved same-bar amb=0."""
from __future__ import annotations

import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from common.paths import art
_LEGACY = _ROOT / "archive" / "legacy_scripts"
if str(_LEGACY) not in sys.path:
    sys.path.insert(0, str(_LEGACY))


import json

import numpy as np
import pandas as pd

from run_orb_vwap_smt_edge_report import ART, FRICTION, POINT_VAL, compute_smt_active, load, p
from run_regime_validation import ENTRY_SLIP, build_daily_features, extended_metrics
from run_exit_forensic import ORB_PCT, SL_PTS, TARGET_FRAC, stress_backtest, summarize_stress

OUT = art("exit_forensic_report.json")


def main():
    p("=" * 78)
    p(" THROUGH-STOP STRESS (same-bar amb already = 0 in classified book)")
    p("=" * 78)

    # Headline from existing classification
    t = pd.read_csv(art("exit_forensic_trades.csv"))
    tables = pd.read_csv(art("exit_forensic_tables.csv"))
    oos = t[(t["year"] >= 2024) & (t["orb_pct_252"] >= ORB_PCT)]
    geom = {
        "oos_orb_n": int(len(oos)),
        "oos_orb_through_stop_pct": round(100 * oos["through_stop_at_entry"].mean(), 1),
        "oos_orb_exit_on_fill_bar_pct": round(100 * oos["exit_on_fill_bar"].mean(), 1),
        "oos_orb_same_bar_ambiguous_n": int(oos["same_bar_ambiguous"].sum()),
        "oos_orb_same_bar_ambiguous_pct": round(100 * oos["same_bar_ambiguous"].mean(), 1),
        "engine_same_bar_rule": "BOTH stop+TP in bar -> SL (pessimistic). Observed count = 0.",
        "pnl_share_oos_orb": {},
    }
    tot = float(oos["pnl_usd"].sum())
    for cls, g in oos.groupby("exit_class"):
        geom["pnl_share_oos_orb"][cls] = {
            "trades": int(len(g)),
            "pct_trades": round(100 * len(g) / len(oos), 1),
            "pnl": round(float(g["pnl_usd"].sum()), 2),
            "pct_pnl": round(100 * float(g["pnl_usd"].sum()) / tot, 1),
            "avg": round(float(g["pnl_usd"].mean()), 2),
        }
        p(f"  {cls}: N={len(g)} PnL=${g['pnl_usd'].sum():,.0f} ({100*g['pnl_usd'].sum()/tot:.1f}%)")

    df = load()
    df["day_id"] = df["day_id"].astype(str)
    smt = compute_smt_active(df)
    daily = build_daily_features()

    stress = []
    for mode in ("baseline", "reject_through", "clip_through", "same_bar_optimistic", "same_bar_cancel"):
        p(f"\nmode={mode}...")
        bt = stress_backtest(df, smt, mode)
        s = summarize_stress(bt, daily, mode)
        stress.append(s)
        o = s["OOS_orb"]
        p(
            f"  OOS_orb N={o.get('trades')} WR={o.get('wr')}% PF={o.get('pf')} "
            f"exp=${o.get('exp')} PnL=${o.get('pnl'):,} MDD=${o.get('mdd')}"
        )
        y = s["live_2026_orb"]
        p(
            f"  2026_orb N={y.get('trades')} WR={y.get('wr')}% PF={y.get('pf')} "
            f"exp=${y.get('exp')} PnL=${y.get('pnl'):,}"
        )

    base = next(s for s in stress if s["mode"] == "baseline")["OOS_orb"]
    rej = next(s for s in stress if s["mode"] == "reject_through")["OOS_orb"]
    clip = next(s for s in stress if s["mode"] == "clip_through")["OOS_orb"]

    thru_share = geom["pnl_share_oos_orb"].get("favorable_through_stop", {}).get("pct_pnl", 0)
    if thru_share >= 50:
        verdict = (
            "CRITICAL — OOS ORB-gated PnL is dominated by favorable through-stop fills "
            f"({thru_share}% of PnL; entry already beyond ORB+/-15). Same-bar SL/TP ambiguity "
            "is NOT the issue (0 cases). Rejecting through-stop fills is the binding robustness test."
        )
    else:
        verdict = "Through-stop is material but not majority; review reject/clip stress PFs."

    report = {
        "frozen": {
            "target": "opposite ORB extreme inset 20% R",
            "stop": "15-point ORB-extreme stop",
            "orb_pct_gate": ORB_PCT,
        },
        "geometry": geom,
        "tables": tables.to_dict(orient="records"),
        "stress": stress,
        "stress_headline": {
            "baseline_oos_orb_pf": base.get("pf"),
            "reject_through_oos_orb_pf": rej.get("pf"),
            "clip_through_oos_orb_pf": clip.get("pf"),
            "baseline_oos_orb_exp": base.get("exp"),
            "reject_through_oos_orb_exp": rej.get("exp"),
            "clip_through_oos_orb_exp": clip.get("exp"),
        },
        "verdict": verdict,
    }
    with open(OUT, "w") as f:
        json.dump(report, f, indent=2, default=str)

    p("\n" + "=" * 78)
    p(" VERDICT")
    p("=" * 78)
    p(verdict)
    p(f"Saved {OUT}")


if __name__ == "__main__":
    main()
