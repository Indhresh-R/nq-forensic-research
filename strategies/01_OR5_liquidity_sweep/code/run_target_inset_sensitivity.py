"""
Target-inset sensitivity — freeze everything except opposite-ORB inset %.

Target definition (engine truth):
  SHORT TP = ORB_low  + inset * R
  LONG  TP = ORB_high - inset * R

Stop unchanged: 15-point ORB-extreme stop.
"""
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

from run_orb_vwap_smt_edge_report import ART, FRICTION, compute_smt_active, load, p
from run_regime_validation import (
    ENTRY_SLIP,
    build_daily_features,
    extended_backtest,
    extended_metrics,
)

INSETS = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50]
ORB_PCT_FROZEN = 0.8452380952380952  # IS q66, frozen
OUT = art("target_inset_sensitivity.json")
OUT_CSV = art("target_inset_sensitivity.csv")


def attach_orb_pct(trades: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    t = trades.copy()
    t["session_date"] = pd.to_datetime(t["day_id"]).dt.date
    feat = daily[["session_date", "orb_pct_252"]].copy()
    feat["session_date"] = pd.to_datetime(feat["session_date"]).dt.date
    t = t.merge(feat, on="session_date", how="left")
    t["entry_time"] = pd.to_datetime(t["entry_time"], utc=True)
    return t


def slice_metrics(t: pd.DataFrame, label: str) -> dict:
    m = extended_metrics(t)
    if len(t) == 0:
        m.update(
            label=label,
            avg_win=0.0,
            avg_loss=0.0,
            win_loss_ratio=0.0,
            tp_pct=0.0,
            sl_pct=0.0,
        )
        return m
    w = t[t["pnl_usd"] > 0]["pnl_usd"]
    l = t[t["pnl_usd"] <= 0]["pnl_usd"]
    avg_w = float(w.mean()) if len(w) else 0.0
    avg_l = float(l.mean()) if len(l) else 0.0
    m.update(
        label=label,
        avg_win=round(avg_w, 2),
        avg_loss=round(avg_l, 2),
        win_loss_ratio=round(abs(avg_w / avg_l), 2) if avg_l != 0 else 0.0,
        tp_pct=round(100 * (t["exit_reason"] == "TP").mean(), 1),
        sl_pct=round(100 * (t["exit_reason"].isin(["SL", "SL_SAME"])).mean(), 1),
    )
    return m


def run_one(df, smt, daily, inset: float) -> dict:
    p(f"\n--- inset={inset:.0%}  (TP = opp ORB +/- {inset:.0%} R) ---")
    trades = extended_backtest(
        df,
        smt,
        fill="next_open",
        entry_slippage=ENTRY_SLIP,
        orb_filter="wide",
        vwap_filter=True,
        orb_touch=True,
        require_smt=True,
        target_frac=inset,
        sl_pts=15.0,
    )
    t = attach_orb_pct(trades, daily)
    is_t = t[t["year"] <= 2023]
    oos_t = t[t["year"] >= 2024]
    y26 = t[t["year"] == 2026]
    oos_orb = oos_t[oos_t["orb_pct_252"] >= ORB_PCT_FROZEN]
    y26_orb = y26[y26["orb_pct_252"] >= ORB_PCT_FROZEN]

    if inset == 0:
        meaning = "opposite ORB extreme"
    elif inset == 0.5:
        meaning = "ORB midpoint"
    else:
        meaning = f"opposite ORB inset {inset:.0%} R"

    block = {
        "inset": inset,
        "inset_pct": int(round(100 * inset)),
        "meaning": meaning,
        "IS_baseline": slice_metrics(is_t, "IS_baseline"),
        "OOS_baseline": slice_metrics(oos_t, "OOS_baseline"),
        "OOS_orb_gate": slice_metrics(oos_orb, "OOS_orb_gate"),
        "live_2026_baseline": slice_metrics(y26, "live_2026_baseline"),
        "live_2026_orb_gate": slice_metrics(y26_orb, "live_2026_orb_gate"),
    }
    for key in (
        "IS_baseline",
        "OOS_baseline",
        "OOS_orb_gate",
        "live_2026_baseline",
        "live_2026_orb_gate",
    ):
        m = block[key]
        p(
            f"  {key:22s} N={m['trades']:4d}  WR={m['wr']:5.1f}%  PF={m['pf']:5.2f}  "
            f"exp=${m['exp']:7.2f}  PnL=${m['pnl']:10,.0f}  MDD=${m['mdd']:7,.0f}  "
            f"W/L={m['win_loss_ratio']:4.2f}  TP%={m['tp_pct']:4.1f}"
        )
    return block


def main():
    p("=" * 78)
    p(" TARGET INSET SENSITIVITY — opposite-ORB fade")
    p(" Frozen: wide ORB, VWAP+/-1.28, SMT, 15pt ORB-extreme stop, next-open+1pt slip")
    p(f" ORB percentile gate frozen at {ORB_PCT_FROZEN}")
    p(f" Insets: {INSETS}")
    p("=" * 78)

    df = load()
    smt = compute_smt_active(df)
    daily = build_daily_features()

    rows = []
    for inset in INSETS:
        rows.append(run_one(df, smt, daily, inset))

    table = []
    for r in rows:
        for sample_key in (
            "IS_baseline",
            "OOS_baseline",
            "OOS_orb_gate",
            "live_2026_orb_gate",
        ):
            m = r[sample_key]
            table.append(
                dict(
                    inset_pct=r["inset_pct"],
                    meaning=r["meaning"],
                    sample=sample_key,
                    trades=m["trades"],
                    wr=m["wr"],
                    pf=m["pf"],
                    exp=m["exp"],
                    pnl=m["pnl"],
                    mdd=m["mdd"],
                    win_loss_ratio=m["win_loss_ratio"],
                    tp_pct=m["tp_pct"],
                    months_pos=m.get("months_pos", 0),
                    months_total=m.get("months_total", 0),
                )
            )
    df_tab = pd.DataFrame(table)
    df_tab.to_csv(OUT_CSV, index=False)

    oos_gate = df_tab[df_tab["sample"] == "OOS_orb_gate"].copy()
    pfs = oos_gate["pf"].tolist()
    min_pf, max_pf = min(pfs), max(pfs)
    broad = all(x >= 1.5 for x in pfs)
    spike = False
    for i, pf in enumerate(pfs):
        others = [pfs[j] for j in range(len(pfs)) if j != i]
        if others and pf > 2.0 * float(np.median(others)):
            spike = True

    if broad and not spike and min_pf >= 2.0:
        verdict = (
            "BROAD REGION — OOS ORB-gated PF stays strong across 0-50% insets; "
            "20% is not a knife-edge optimum."
        )
    elif broad and not spike:
        verdict = (
            "ACCEPTABLE REGION — profitable across insets, but edge softens at some levels; "
            "20% not uniquely magical."
        )
    elif spike:
        verdict = (
            "SUSPICIOUS — 20% (or one inset) spikes vs neighbors; treat current PF as "
            "target-placement sensitive."
        )
    else:
        verdict = (
            "FRAGILE — profitability collapses away from 20%; do not treat structural "
            "cross-ORB target as robust."
        )

    report = {
        "terminology": {
            "stop": "15-point ORB-extreme stop (ORB high/low +/- 15)",
            "target": "Opposite ORB extreme, inset X% of ORB range",
            "not": "entry +/- 20% ORB scalp",
        },
        "frozen": {
            "fill": "next_open",
            "entry_slippage_pts": ENTRY_SLIP,
            "friction_pts": FRICTION,
            "sl": "ORB extreme +/- 15",
            "orb_filter": "wide 1.10x SMA20 / 40",
            "vwap": "+/- 1.28 sigma",
            "smt": True,
            "orb_pct_gate": ORB_PCT_FROZEN,
        },
        "insets": rows,
        "oos_orb_gate_pf_by_inset": {
            int(r["inset_pct"]): r["OOS_orb_gate"]["pf"] for r in rows
        },
        "oos_orb_gate_pf_min": min_pf,
        "oos_orb_gate_pf_max": max_pf,
        "suspicious_spike": spike,
        "broad_region": broad and not spike,
        "verdict": verdict,
    }

    with open(OUT, "w") as f:
        json.dump(report, f, indent=2, default=str)

    p("\n" + "=" * 78)
    p(" OOS ORB-GATE PF BY INSET")
    p("=" * 78)
    for r in rows:
        m = r["OOS_orb_gate"]
        mark = " <-- current" if r["inset_pct"] == 20 else ""
        p(
            f"  {r['inset_pct']:2d}%  PF={m['pf']:5.2f}  exp=${m['exp']:7.2f}  "
            f"N={m['trades']:4d}  WR={m['wr']:5.1f}%  W/L={m['win_loss_ratio']:4.2f}{mark}"
        )
    p(f"\nVERDICT: {verdict}")
    p(f"Saved {OUT}")
    p(f"Saved {OUT_CSV}")
    return report


if __name__ == "__main__":
    main()
