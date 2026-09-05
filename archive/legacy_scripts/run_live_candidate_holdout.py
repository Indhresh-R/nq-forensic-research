"""
Frozen live-candidate holdout.

Uses trades already generated with frozen rules:
  next-bar open, 0.25pt friction, 1.0pt entry slippage,
  1.10x SMA20 / 40pt wide ORB, 15pt SL, 20% ORB target, SMT + VWAP ±1.28σ.

No re-optimization. ORB percentile gate frozen at IS q66 = 0.8452380952380952.

Reports:
  1) OOS year slices 2024 / 2025 / 2026 (baseline + ORB-high)
  2) Monthly PF / PnL for each year
  3) Untouched 2026-01-01 → latest as live-like period
"""
from __future__ import annotations

from common.paths import art

import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_orb_vwap_smt_edge_report import ART, FRICTION, POINT_VAL, metrics, p

ORB_PCT_FROZEN = 0.8452380952380952
LIVE_START = pd.Timestamp("2026-01-01", tz="UTC")


def load_trades() -> pd.DataFrame:
    t = pd.read_csv(art("regime_trades_enriched.csv"))
    t["entry_time"] = pd.to_datetime(t["entry_time"], utc=True)
    t["exit_time"] = pd.to_datetime(t["exit_time"], utc=True)
    t["pnl_usd"] = t["pnl_usd"].astype(float)
    return t.sort_values("entry_time").reset_index(drop=True)


def pf_of(g: pd.DataFrame) -> float:
    if len(g) == 0:
        return 0.0
    gp = float(g.loc[g["pnl_usd"] > 0, "pnl_usd"].sum())
    gl = abs(float(g.loc[g["pnl_usd"] <= 0, "pnl_usd"].sum()))
    if gl == 0:
        return 0.0 if gp == 0 else float("inf")
    return round(gp / gl, 2)


def losing_streak(t: pd.DataFrame) -> int:
    mx = cur = 0
    for x in t["pnl_usd"]:
        if x <= 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def longest_dd_days(t: pd.DataFrame) -> dict:
    """Longest peak-to-recovery duration in calendar days (entry timestamps)."""
    if len(t) == 0:
        return dict(days=0, start=None, trough=None, recover=None)
    d = t.sort_values("entry_time")
    cum = d["pnl_usd"].cumsum()
    peak = cum.cummax()
    dd = peak - cum
    in_dd = dd > 1e-9
    longest = 0.0
    best = dict(days=0.0, start=None, trough=None, recover=None)
    start_i = None
    trough_i = None
    trough_val = 0.0
    times = d["entry_time"].to_numpy()
    for i, flag in enumerate(in_dd.to_numpy()):
        if flag:
            if start_i is None:
                start_i = i
                trough_i = i
                trough_val = float(dd.iloc[i])
            elif float(dd.iloc[i]) > trough_val:
                trough_i = i
                trough_val = float(dd.iloc[i])
        elif start_i is not None:
            days = (pd.Timestamp(times[i]) - pd.Timestamp(times[start_i])).days
            if days >= longest:
                longest = days
                best = dict(
                    days=int(days),
                    start=str(pd.Timestamp(times[start_i]).date()),
                    trough=str(pd.Timestamp(times[trough_i]).date()),
                    recover=str(pd.Timestamp(times[i]).date()),
                )
            start_i = trough_i = None
            trough_val = 0.0
    if start_i is not None:
        days = (pd.Timestamp(times[-1]) - pd.Timestamp(times[start_i])).days
        if days >= longest:
            best = dict(
                days=int(days),
                start=str(pd.Timestamp(times[start_i]).date()),
                trough=str(pd.Timestamp(times[trough_i]).date()),
                recover="OPEN",
            )
    return best


def extra_metrics(t: pd.DataFrame) -> dict:
    m = metrics(t)
    if len(t) == 0:
        m.update(
            losing_streak=0,
            largest_loss=0.0,
            longest_dd_days=0,
            longest_dd=None,
            monthly_pf=[],
        )
        return m
    m["losing_streak"] = losing_streak(t)
    m["largest_loss"] = round(float(t["pnl_usd"].min()), 2)
    ldd = longest_dd_days(t)
    m["longest_dd_days"] = ldd["days"]
    m["longest_dd"] = ldd
    m["first_trade"] = str(t["entry_time"].min())
    m["last_trade"] = str(t["entry_time"].max())
    return m


def monthly_table(t: pd.DataFrame) -> list[dict]:
    if len(t) == 0:
        return []
    d = t.copy()
    d["ym"] = d["entry_time"].dt.to_period("M")
    rows = []
    for ym, g in d.groupby("ym"):
        rows.append(
            dict(
                month=str(ym),
                trades=int(len(g)),
                wr=round(100 * (g["pnl_usd"] > 0).mean(), 1),
                pnl=round(float(g["pnl_usd"].sum()), 2),
                pf=pf_of(g),
                exp=round(float(g["pnl_usd"].mean()), 2),
            )
        )
    return rows


def year_block(t: pd.DataFrame, year: int, label: str) -> dict:
    g = t[t["year"] == year]
    return dict(
        year=year,
        subset=label,
        **extra_metrics(g),
        monthly=monthly_table(g),
        months_pos=sum(1 for r in monthly_table(g) if r["pnl"] > 0),
        months_total=len(monthly_table(g)),
    )


def print_block(title: str, block: dict) -> None:
    p("")
    p("=" * 78)
    p(title)
    p("=" * 78)
    p(
        f"  N={block['trades']}  WR={block['wr']}%  PF={block['pf']}  "
        f"exp=${block['exp']}  PnL=${block['pnl']:,}  MDD=${block['mdd']}"
    )
    p(
        f"  losing_streak={block['losing_streak']}  largest_loss=${block['largest_loss']}  "
        f"longest_DD={block['longest_dd_days']}d  {block.get('longest_dd')}"
    )
    p(f"  window: {block.get('first_trade')} -> {block.get('last_trade')}")
    p(f"  months + : {block.get('months_pos')}/{block.get('months_total')}")
    p("  monthly:")
    p(f"  {'month':<10} {'N':>4} {'WR':>6} {'PF':>6} {'exp':>9} {'PnL':>10}")
    for r in block.get("monthly", []):
        p(
            f"  {r['month']:<10} {r['trades']:>4} {r['wr']:>5.1f}% "
            f"{r['pf']:>6} ${r['exp']:>8.2f} ${r['pnl']:>9.2f}"
        )


def main():
    t = load_trades()
    p("=" * 78)
    p(" FROZEN LIVE-CANDIDATE HOLDOUT - no re-optimization")
    p(f" ORB percentile gate = {ORB_PCT_FROZEN}")
    p(f" Friction {FRICTION}pt + 1.0pt entry slip | POINT_VAL ${POINT_VAL}")
    p(f" Trade file: {len(t):,} rows | {t['entry_time'].min()} -> {t['entry_time'].max()}")
    p("=" * 78)

    oos = t[t["year"] >= 2024]
    orb = t[t["orb_pct_252"] >= ORB_PCT_FROZEN]

    yearly = []
    for yr in (2024, 2025, 2026):
        yearly.append(year_block(t, yr, "baseline"))
        yearly.append(year_block(orb, yr, "orb_pct_high"))

    p("\nOOS YEAR SLICES - baseline (no ORB-pct gate)")
    for b in yearly:
        if b["subset"] == "baseline":
            print_block(f"BASELINE {b['year']}", b)

    p("\nOOS YEAR SLICES - ORB percentile >= 0.845238 (frozen IS q66)")
    for b in yearly:
        if b["subset"] == "orb_pct_high":
            print_block(f"ORB-HIGH {b['year']}", b)

    # Live-like: 2026-01-01 → latest, complete frozen strategy
    live_base = t[t["entry_time"] >= LIVE_START]
    live_orb = live_base[live_base["orb_pct_252"] >= ORB_PCT_FROZEN]

    live_base_m = extra_metrics(live_base)
    live_base_m["monthly"] = monthly_table(live_base)
    live_base_m["months_pos"] = sum(1 for r in live_base_m["monthly"] if r["pnl"] > 0)
    live_base_m["months_total"] = len(live_base_m["monthly"])
    live_base_m["subset"] = "baseline_2026_live"

    live_orb_m = extra_metrics(live_orb)
    live_orb_m["monthly"] = monthly_table(live_orb)
    live_orb_m["months_pos"] = sum(1 for r in live_orb_m["monthly"] if r["pnl"] > 0)
    live_orb_m["months_total"] = len(live_orb_m["monthly"])
    live_orb_m["subset"] = "orb_pct_high_2026_live"

    print_block("LIVE-LIKE 2026-01-01 -> latest  |  BASELINE (no ORB-pct gate)", live_base_m)
    print_block(
        "LIVE-LIKE 2026-01-01 -> latest  |  COMPLETE FROZEN (ORB-pct >= 0.845238)",
        live_orb_m,
    )

    # Why OOS PF jumped: contribution by year
    oos_pnl = float(oos["pnl_usd"].sum())
    contrib = []
    for yr, g in oos.groupby("year"):
        contrib.append(
            dict(
                year=int(yr),
                trades=int(len(g)),
                pnl=round(float(g["pnl_usd"].sum()), 2),
                pct_oos_pnl=round(100 * float(g["pnl_usd"].sum()) / oos_pnl, 1) if oos_pnl else 0,
                pf=pf_of(g),
                exp=round(float(g["pnl_usd"].mean()), 2),
            )
        )

    # Note on leftover metric
    note = (
        "pct_oos_pnl_in_2022_plus is tautological: OOS is defined as year>=2024, "
        "so year>=2022 covers 100% of OOS by construction. It is not evidence of "
        "a pre-2022 vs post-2022 split inside OOS."
    )

    report = {
        "classification": (
            "HIGH-CONFIDENCE RESEARCH CANDIDATE — strong persistence in 2024-2026, "
            "not yet proven regime-invariant or production-ready."
        ),
        "claim_correction": note,
        "frozen": {
            "orb_pct_threshold": ORB_PCT_FROZEN,
            "fill": "next_open",
            "friction_pts": FRICTION,
            "entry_slippage_pts": 1.0,
            "sl_pts": 15,
            "target_frac": 0.20,
            "wide_mult": 1.10,
            "fixed_orb_thresh": 40,
            "vwap": "±1.28σ",
            "smt": True,
        },
        "oos_year_contribution": contrib,
        "yearly": yearly,
        "live_2026_baseline": live_base_m,
        "live_2026_orb_filter": live_orb_m,
        "data_span": {
            "first_trade": str(t["entry_time"].min()),
            "last_trade": str(t["entry_time"].max()),
            "last_2026_trade": str(live_base["entry_time"].max()) if len(live_base) else None,
        },
    }

    def _json(o):
        if isinstance(o, (np.floating, np.integer)):
            return float(o) if isinstance(o, np.floating) else int(o)
        if isinstance(o, float) and (np.isinf(o) or np.isnan(o)):
            return None
        raise TypeError

    out = art("live_candidate_holdout.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2, default=_json)

    monthly_rows = []
    for b in yearly:
        for r in b["monthly"]:
            monthly_rows.append(dict(year=b["year"], subset=b["subset"], **r))
    for label, blk in (("baseline_2026_live", live_base_m), ("orb_pct_high_2026_live", live_orb_m)):
        for r in blk["monthly"]:
            monthly_rows.append(dict(year=2026, subset=label, **r))
    pd.DataFrame(monthly_rows).to_csv(art("live_candidate_monthly.csv"), index=False)

    p("\n" + "=" * 78)
    p(" OOS PnL MIX (why aggregate PF 5.60 is not a single regime)")
    p("=" * 78)
    for c in contrib:
        p(f"  {c['year']}: N={c['trades']}  PF={c['pf']}  exp=${c['exp']}  "
          f"PnL=${c['pnl']:,}  ({c['pct_oos_pnl']}% of OOS PnL)")
    p(f"\n{note}")
    p(f"\nSaved {out}")
    p(f"Saved {art('live_candidate_monthly.csv')}")
    return report


if __name__ == "__main__":
    main()
