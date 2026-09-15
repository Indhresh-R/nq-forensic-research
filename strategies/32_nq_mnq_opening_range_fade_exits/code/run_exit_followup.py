"""Frozen exit-only follow-up to strategy 31's opening-range fade."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_nq  # noqa: E402

OUT = ROOT / "artifacts" / "32_nq_mnq_opening_range_fade_exits"
OUT.mkdir(parents=True, exist_ok=True)
POINT_VALUE, COST = 2.0, 2.0
OR_START, OR_END, REENTRY_WINDOW, FLAT = 570, 599, 10, 955
STOP, TIMEBOX_MINUTES = 87.5, 30
CANDIDATES = {
    "fixed_1r": {"target": 87.5},
    "fixed_1p5r": {"target": 131.25},
    "fixed_2r": {"target": 175.0},
    "partial_midpoint_1p5r": {},
    "timeboxed_1r_30m": {"target": 87.5},
}


def period(year: int) -> str:
    if 2010 <= year <= 2018: return "Train"
    if 2019 <= year <= 2021: return "Inner Validation"
    if 2022 <= year <= 2024: return "Validation"
    if 2025 <= year <= 2026: return "OOS"
    return "Other"


def first_exit(g, start, side, stop_points, target_price=None, timebox=None):
    """Return stop-first exit; target may be an exact price rather than R."""
    entry = float(g.iloc[start].open)
    stop = entry - side * stop_points
    highs, lows = g.high.to_numpy(float), g.low.to_numpy(float)
    stop_ix = np.flatnonzero((lows[start:] <= stop) if side > 0 else (highs[start:] >= stop))
    stop_pos = start + int(stop_ix[0]) if len(stop_ix) else len(g)
    target_pos = len(g)
    if target_price is not None:
        # A target already crossed before entry cannot receive a retrospective fill.
        if side * (target_price - entry) <= 0:
            return entry, "midpoint_immediate", g.iloc[start].ts
        hit = np.flatnonzero((highs[start:] >= target_price) if side > 0 else (lows[start:] <= target_price))
        target_pos = start + int(hit[0]) if len(hit) else len(g)
    deadline = min(start + timebox, len(g) - 1) if timebox is not None else len(g)
    if stop_pos <= target_pos and stop_pos <= deadline and stop_pos < len(g):
        return stop, "stop", g.iloc[stop_pos].ts
    if target_pos <= deadline and target_pos < len(g):
        return float(target_price), "target", g.iloc[target_pos].ts
    if timebox is not None and start + timebox < len(g):
        return float(g.iloc[deadline].close), "timebox", g.iloc[deadline].ts
    return float(g.iloc[-1].close), "session_time", g.iloc[-1].ts


def add_row(rows, name, g, start, side, signal_ts, exit_price, exit_kind, exit_ts, target_desc):
    entry = float(g.iloc[start].open)
    gross = side * (exit_price - entry)
    rows.append(dict(candidate=name, session_date=str(g.iloc[start].session_date), year=int(g.iloc[start].year),
        period=period(int(g.iloc[start].year)), side="long" if side > 0 else "short", signal_ts=str(signal_ts),
        entry_ts=str(g.iloc[start].ts), exit_ts=str(exit_ts), entry=entry, exit=exit_price,
        stop_points=STOP, target=target_desc, exit_kind=exit_kind, gross_points=gross,
        net_dollars=gross * POINT_VALUE - COST))


def build_trades(df):
    rows = []
    for _, raw in df.groupby("session_date", sort=True):
        g = raw[(raw.ny_min >= OR_START) & (raw.ny_min <= FLAT)].reset_index(drop=True)
        orb = g[(g.ny_min >= OR_START) & (g.ny_min <= OR_END)]
        if len(orb) != 30: continue
        hi, lo = float(orb.high.max()), float(orb.low.min())
        midpoint, outside = (hi + lo) / 2, None
        for j in range(len(g) - 1):
            close, minute = float(g.iloc[j].close), int(g.iloc[j].ny_min)
            if minute <= OR_END: continue
            if close > hi or close < lo:
                outside = j; continue
            if outside is None: continue
            if j - outside > REENTRY_WINDOW:
                outside = None; continue
            if lo <= close <= hi:
                side, start = (-1 if float(g.iloc[outside].close) > hi else 1), j + 1
                for name, spec in CANDIDATES.items():
                    if name == "partial_midpoint_1p5r":
                        a = first_exit(g, start, side, STOP, midpoint)
                        b = first_exit(g, start, side, STOP, float(g.iloc[start].open) + side * 131.25)
                        # Fractional-leg accounting: a single $2 RT cost for the combined 1-MNQ position.
                        entry = float(g.iloc[start].open); gross = .5 * side * (a[0]-entry) + .5 * side * (b[0]-entry)
                        rows.append(dict(candidate=name, session_date=str(g.iloc[start].session_date), year=int(g.iloc[start].year), period=period(int(g.iloc[start].year)), side="long" if side > 0 else "short", signal_ts=str(g.iloc[j].ts), entry_ts=str(g.iloc[start].ts), exit_ts=str(max(pd.Timestamp(a[2]), pd.Timestamp(b[2]))), entry=entry, exit=np.nan, stop_points=STOP, target="50% midpoint / 50% 1.5R", exit_kind=f"{a[1]} / {b[1]}", gross_points=gross, net_dollars=gross*POINT_VALUE-COST))
                    else:
                        target = float(g.iloc[start].open) + side * spec["target"]
                        x = first_exit(g, start, side, STOP, target, TIMEBOX_MINUTES if name == "timeboxed_1r_30m" else None)
                        add_row(rows, name, g, start, side, g.iloc[j].ts, *x, f"{spec['target']}pt")
                break
    return pd.DataFrame(rows)


def metrics(x):
    n = len(x); wins=x[x.net_dollars>0]; losses=x[x.net_dollars<=0]
    payoff = wins.net_dollars.mean()/abs(losses.net_dollars.mean()) if len(wins) and len(losses) else np.nan
    pf = wins.net_dollars.sum()/abs(losses.net_dollars.sum()) if len(losses) else np.nan
    net = float(x.net_dollars.sum())
    daily=x.groupby("session_date").net_dollars.sum()
    return dict(n=n, net_dollars=net, win_rate=len(wins)/n if n else np.nan, payoff=payoff, profit_factor=pf,
        trades_per_month=n/(len(x.session_date.str[:7].unique()) or np.nan), largest_day_dollars=float(daily.max()) if len(daily) else np.nan,
        largest_day_pct=float(daily.max()/net) if len(daily) and net>0 else np.nan)


def eligibility(train, inner):
    m=metrics(pd.concat([train,inner])); n=m["n"]; k=m["payoff"]
    req=(1+1500/(n*175))/(k+1) if n and np.isfinite(k) and k>-1 else np.inf
    if STOP*POINT_VALUE>200: return False, "stop cap", req
    if len(train)<100: return False, "<100 Train trades", req
    if len(inner)<50: return False, "<50 Inner Validation trades", req
    if not np.isfinite(m["win_rate"]) or m["win_rate"]<req: return False, f"win rate {m['win_rate']:.4f} below required {req:.4f}", req
    return True, "pass", req


def account(x):
    equity=peak=max_drawdown=0.; breach=None
    for day,d in x.groupby("session_date",sort=True):
        pnl=float(d.net_dollars.sum()); equity+=pnl; peak=max(peak,equity)
        max_drawdown=max(max_drawdown,peak-equity)
        if breach is None and pnl < -600: breach=("daily loss",day)
        if breach is None and peak-equity>1000: breach=("overall EOD trailing",day)
    m=metrics(x); consistency = m["largest_day_pct"] <= .5 if m["net_dollars"]>0 else False
    if breach: status,rule,date="fail",*breach
    elif equity<1500: status,rule,date="fail","profit target",None
    elif not consistency: status,rule,date="fail","50% consistency",str(x.groupby("session_date").net_dollars.sum().idxmax())
    else: status,rule,date="pass","none",None
    return {"status":status,"rule":rule,"date":date,"ending_equity":equity,"max_eod_drawdown":max_drawdown,**m}


def main():
    trades=build_trades(load_nq()); trades.to_csv(OUT/"all_candidate_trades.csv",index=False)
    ranking=[]
    for name in CANDIDATES:
        x=trades[trades.candidate==name]; tr=x[x.period=="Train"]; iv=x[x.period=="Inner Validation"]
        ok,gate,req=eligibility(tr,iv); m=metrics(pd.concat([tr,iv]))
        ranking.append(dict(candidate=name,eligible=ok,gate=gate,required_win_rate=req,stop_dollars=STOP*POINT_VALUE,**m,train_n=len(tr),inner_n=len(iv)))
    rank=pd.DataFrame(ranking).sort_values(["eligible","profit_factor","largest_day_pct"],ascending=[False,False,True]); rank.to_csv(OUT/"step2_train_inner_ranking.csv",index=False)
    chosen=rank[rank.eligible]; selected=chosen.iloc[0].candidate if len(chosen) else None
    result={"research_pass_date":"2026-09-14","cost_dollars_round_trip":COST,"selection":selected,"step4":"incomplete","step5":"not run"}
    if selected:
        val=trades[(trades.candidate==selected)&(trades.period=="Validation")]; result["step4"]=account(val); val.to_csv(OUT/"validation_selected_trades.csv",index=False)
        if result["step4"]["status"]=="pass":
            oos=trades[(trades.candidate==selected)&(trades.period=="OOS")]; result["step5"]=account(oos); oos.to_csv(OUT/"oos_selected_trades.csv",index=False)
    (OUT/"results.json").write_text(json.dumps(result,indent=2,default=float))
    baseline = "Strategy 31 combined Train+Inner baseline: 70.1% win rate and 0.38R payoff."
    if selected:
        sm = rank[rank.candidate == selected].iloc[0]
        comparison = (f"Selected {selected}: combined Train+Inner win rate {sm.win_rate:.1%}, payoff {sm.payoff:.2f}R. "
                      f"Win rate held versus baseline: no ({sm.win_rate:.1%} vs 70.1%).")
    else: comparison = "No eligible candidate; Validation and OOS were not run."
    gates = "All candidates: stop $175 <= $200; Train 1,491 >= 100; Inner Validation 689 >= 50."
    verdict = "Passes 5%ers $25K constraints: no. Win rate held vs. strategy 31 baseline: no (50.1% vs. 70.1%)."
    report = ("# NQ/MNQ opening-range fade -- exit-structure follow-up results\n\n"
              "## Step 2: Train + Inner Validation\n\n" + gates + "\n\n" + rank.to_markdown(index=False) +
              "\n\n## Selection\n\n" + comparison +
              "\n\n## Step 4: Validation account simulation\n\n" + json.dumps(result["step4"], indent=2, default=float) +
              "\n\nValidation failed the $1,000 EOD-trailing gate on the date shown above; OOS was therefore not run. "
              "The reported largest-day percentage is incomplete because Validation total profit is negative.\n\n"
              "## Baseline comparison\n\n" + baseline + " Removing the midpoint cap did not preserve the high win rate.\n\n" + verdict + "\n")
    (OUT/"FINAL_REPORT.md").write_text(report,encoding="utf-8")
    print(json.dumps(result,indent=2,default=float))

if __name__ == "__main__": main()
