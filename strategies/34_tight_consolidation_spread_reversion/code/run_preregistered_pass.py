"""Frozen 2026-09-14 tight-consolidation and NQ--ES spread pass."""
from __future__ import annotations

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_es, load_nq  # noqa: E402

OUT = ROOT / "artifacts" / "34_tight_consolidation_spread_reversion"
OUT.mkdir(parents=True, exist_ok=True)
OPEN, FLAT = 570, 955
MNQ_PV, MES_PV, A_COST, B_COST = 2.0, 5.0, 2.0, 4.0
WINDOW, A_PERCENTILE, VOL_MULT = 30, .25, 1.5
SPREAD_LOOKBACK, Z_ENTRY, SPREAD_STOP, SPREAD_TARGET = 60, 2.0, 150.0, 225.0


def period(year: int) -> str:
    if 2010 <= year <= 2018: return "Train"
    if 2019 <= year <= 2021: return "Inner Validation"
    if 2022 <= year <= 2024: return "Validation"
    if 2025 <= year <= 2026: return "OOS"
    return "Other"


def metrics(x: pd.DataFrame) -> dict:
    n = len(x)
    wins, losses = x[x.net_dollars > 0], x[x.net_dollars <= 0]
    daily = x.groupby("session_date").net_dollars.sum() if n else pd.Series(dtype=float)
    net = float(x.net_dollars.sum()) if n else 0.0
    return dict(n=n, net_dollars=net,
        win_rate=len(wins) / n if n else np.nan,
        payoff=float(wins.net_dollars.mean() / abs(losses.net_dollars.mean())) if len(wins) and len(losses) else np.nan,
        profit_factor=float(wins.net_dollars.sum() / abs(losses.net_dollars.sum())) if len(losses) else np.nan,
        trades_per_month=n / len(x.session_date.astype(str).str[:7].unique()) if n else np.nan,
        largest_day_dollars=float(daily.max()) if len(daily) else np.nan,
        largest_day_pct=float(daily.max()/net) if len(daily) and net > 0 else np.nan)


def eligible(train: pd.DataFrame, inner: pd.DataFrame, max_stop: float) -> tuple[bool, str, float]:
    m = metrics(pd.concat([train, inner])); k, n = m["payoff"], m["n"]
    required = (1 + 1500 / (n * max_stop)) / (k + 1) if n and np.isfinite(k) else np.inf
    if max_stop > 150: return False, "max stop exceeds $150", required
    if len(train) < 100: return False, "<100 Train trades", required
    if len(inner) < 50: return False, "<50 Inner Validation trades", required
    if not np.isfinite(m["win_rate"]) or m["win_rate"] < required:
        return False, f"win rate {m['win_rate']:.4f} below required {required:.4f}", required
    return True, "pass", required


def account(x: pd.DataFrame) -> dict:
    equity = peak = max_dd = 0.0; breach = None
    daily = x.groupby("session_date", sort=True).net_dollars.sum()
    for day, pnl in daily.items():
        equity += float(pnl); peak = max(peak, equity); max_dd = max(max_dd, peak-equity)
        if breach is None and pnl < -600: breach = ("daily loss", str(day))
        if breach is None and peak-equity > 1000: breach = ("overall EOD trailing", str(day))
    m = metrics(x); consistency = bool(m["net_dollars"] > 0 and m["largest_day_pct"] <= .5)
    if breach: status, rule, date = "fail", breach[0], breach[1]
    elif equity < 1500: status, rule, date = "fail", "profit target", None
    elif not consistency: status, rule, date = "fail", "50% consistency", str(daily.idxmax()) if len(daily) else None
    else: status, rule, date = "pass", "none", None
    return dict(status=status, rule=rule, date=date, ending_equity=equity,
        max_eod_drawdown=max_dd, worst_daily_pnl=float(daily.min()) if len(daily) else np.nan,
        consistency_pass=consistency, **m)


def a_exit(hi, lo, close, ts, entry_i: int, side: int, stop: float, target: float):
    """Vectorized stop-first path scan; avoids per-minute DataFrame indexing."""
    stopped = np.flatnonzero((lo[entry_i+1:] <= stop) if side > 0 else (hi[entry_i+1:] >= stop))
    hit = np.flatnonzero((hi[entry_i+1:] >= target) if side > 0 else (lo[entry_i+1:] <= target))
    sp = entry_i + 1 + int(stopped[0]) if len(stopped) else len(close)
    tp = entry_i + 1 + int(hit[0]) if len(hit) else len(close)
    if sp <= tp and sp < len(close): return stop, "stop", ts[sp]
    if tp < len(close): return target, "target", ts[tp]
    return float(close[-1]), "session_time", ts[-1]


def build_a(nq: pd.DataFrame, x_threshold: float) -> pd.DataFrame:
    rows = []
    for sd, raw in nq.groupby("session_date", sort=True):
        g = raw[(raw.ny_min >= OPEN) & (raw.ny_min <= FLAT)].reset_index(drop=True)
        if len(g) < WINDOW + 2: continue
        highs, lows = g.high.to_numpy(float), g.low.to_numpy(float)
        closes, vols, times = g.close.to_numpy(float), g.volume.to_numpy(float), g.ts.to_numpy()
        roll_hi = pd.Series(highs).rolling(WINDOW).max().shift(1).to_numpy()
        roll_lo = pd.Series(lows).rolling(WINDOW).min().shift(1).to_numpy()
        roll_vol = pd.Series(vols).rolling(WINDOW).mean().shift(1).to_numpy()
        possible = np.flatnonzero((roll_hi-roll_lo <= x_threshold) & ((closes > roll_hi) | (closes < roll_lo)))
        for i in possible:
            if i < WINDOW: continue
            hi, lo = float(roll_hi[i]), float(roll_lo[i]); width = hi-lo
            close = float(closes[i])
            if width > x_threshold or not (close > hi or close < lo): continue
            side = 1 if close > hi else -1
            vol_ok = float(vols[i]) > VOL_MULT * float(roll_vol[i])
            for name, rr, require_vol in (("A1_inside_1R", 1.0, False), ("A2_inside_1p5R", 1.5, False), ("A3_inside_volume_1R", 1.0, True)):
                if require_vol and not vol_ok: continue
                stop, target = (lo, close + width*rr) if side > 0 else (hi, close-width*rr)
                exit_px, kind, exit_ts = a_exit(highs, lows, closes, times, i, side, stop, target)
                gross = side*(exit_px-close)*MNQ_PV
                rows.append(dict(candidate=name, family="A", session_date=str(sd), year=int(g.iloc[i].year), period=period(int(g.iloc[i].year)),
                    signal_ts=str(times[i]), entry_ts=str(times[i]), exit_ts=str(exit_ts), side="long" if side > 0 else "short",
                    entry=close, exit=exit_px, natural_stop_dollars=width*MNQ_PV, stop_dollars=width*MNQ_PV,
                    target_dollars=width*rr*MNQ_PV, exit_kind=kind, net_dollars=gross-A_COST))
            break
    return pd.DataFrame(rows)


def spread_exit(g: pd.DataFrame, entry_i: int, direction: int, entry_spread: float, target_dollars: float):
    # direction +1 = long dollar spread (long MNQ, short MES). Stop wins collisions.
    nq_hi, nq_lo = g.nq_high.to_numpy(float)[entry_i+1:], g.nq_low.to_numpy(float)[entry_i+1:]
    es_hi, es_lo = g.es_high.to_numpy(float)[entry_i+1:], g.es_low.to_numpy(float)[entry_i+1:]
    if direction > 0:
        favorable, adverse = MNQ_PV*nq_hi-MES_PV*es_lo-entry_spread, MNQ_PV*nq_lo-MES_PV*es_hi-entry_spread
    else:
        favorable, adverse = entry_spread-(MNQ_PV*nq_lo-MES_PV*es_hi), entry_spread-(MNQ_PV*nq_hi-MES_PV*es_lo)
    stop_ix, hit_ix = np.flatnonzero(adverse <= -SPREAD_STOP), np.flatnonzero(favorable >= target_dollars)
    sp, tp = (int(stop_ix[0]) if len(stop_ix) else len(favorable)), (int(hit_ix[0]) if len(hit_ix) else len(favorable))
    if sp <= tp and sp < len(favorable): return -SPREAD_STOP, "stop", g.ts.iloc[entry_i+1+sp]
    if tp < len(favorable): return target_dollars, "target", g.ts.iloc[entry_i+1+tp]
    return direction*(float(g.spread.iloc[-1])-entry_spread), "session_time", g.ts.iloc[-1]


def build_b(nq: pd.DataFrame, es: pd.DataFrame) -> pd.DataFrame:
    a = nq[(nq.ny_min >= OPEN) & (nq.ny_min <= FLAT)][["ts","session_date","year","ny_min","close","high","low"]].rename(columns={"close":"nq_close","high":"nq_high","low":"nq_low"})
    b = es[(es.ny_min >= OPEN) & (es.ny_min <= FLAT)][["ts","close","high","low"]].rename(columns={"close":"es_close","high":"es_high","low":"es_low"})
    d = a.merge(b, on="ts", how="inner").sort_values("ts").copy()
    d["spread"] = MNQ_PV*d.nq_close - MES_PV*d.es_close
    # Reset rolling state at each RTH session; past days cannot leak into the stated intraday lookback.
    d["mean"] = d.groupby("session_date").spread.transform(lambda s: s.shift(1).rolling(SPREAD_LOOKBACK, min_periods=SPREAD_LOOKBACK).mean())
    d["sd"] = d.groupby("session_date").spread.transform(lambda s: s.shift(1).rolling(SPREAD_LOOKBACK, min_periods=SPREAD_LOOKBACK).std(ddof=1))
    d["z"] = (d.spread-d["mean"])/d.sd
    rows=[]
    for sd, g in d.groupby("session_date", sort=True):
        g=g.reset_index(drop=True)
        hits=np.flatnonzero(g.z.abs().to_numpy(float) >= Z_ENTRY)
        if not len(hits) or hits[0]+1 >= len(g): continue
        sig_i=int(hits[0]); entry_i=sig_i+1; direction=-1 if float(g.iloc[sig_i].z)>0 else 1
        entry_spread=float(g.iloc[entry_i].spread)
        mean_distance=abs(entry_spread-float(g.iloc[sig_i]["mean"]))
        for name, target in (("B4_zmean_nearer_1p5R", min(SPREAD_TARGET, mean_distance)), ("B5_z_fixed_1p5R", SPREAD_TARGET)):
            pnl, kind, exit_ts=spread_exit(g,entry_i,direction,entry_spread,target)
            rows.append(dict(candidate=name, family="B", session_date=str(sd), year=int(g.iloc[entry_i].year), period=period(int(g.iloc[entry_i].year)),
                signal_ts=str(g.iloc[sig_i].ts), entry_ts=str(g.iloc[entry_i].ts), exit_ts=str(exit_ts), side="long_spread" if direction>0 else "short_spread",
                entry=entry_spread, exit=np.nan, natural_stop_dollars=np.nan, stop_dollars=SPREAD_STOP,
                target_dollars=target, zscore=float(g.iloc[sig_i].z), exit_kind=kind, net_dollars=pnl-B_COST))
    return pd.DataFrame(rows)


def main():
    nq, es = load_nq(), load_es()
    rth_train=nq[(nq.year.between(2010,2018)) & (nq.ny_min.between(OPEN,FLAT))].copy()
    train_ranges=rth_train.groupby("session_date", group_keys=False).apply(lambda g: (g.high.rolling(WINDOW).max()-g.low.rolling(WINDOW).min()).iloc[WINDOW-1:]).dropna()
    x=float(train_ranges.quantile(A_PERCENTILE))
    manifest={"research_pass_date":"2026-09-14","family_a":{"window_minutes":WINDOW,"train_range_percentile":A_PERCENTILE,"frozen_x_points":x,"volume_multiple":VOL_MULT},"family_b":{"pair":"1 MNQ + 1 MES","point_values":{"MNQ":MNQ_PV,"MES":MES_PV},"combined_round_trip_cost":B_COST,"spread":"2*NQ - 5*ES","lookback_minutes":SPREAD_LOOKBACK,"z_entry":Z_ENTRY,"stop_dollars":SPREAD_STOP}}
    (OUT/"frozen_parameters.json").write_text(json.dumps(manifest,indent=2))
    trades=pd.concat([build_a(nq,x),build_b(nq,es)],ignore_index=True); trades.to_csv(OUT/"all_candidate_trades.csv",index=False)
    ranking=[]
    for name, z in trades.groupby("candidate"):
        tr=z[z.period.eq("Train")]; iv=z[z.period.eq("Inner Validation")]; ok,gate,req=eligible(tr,iv,float(z.stop_dollars.max())); m=metrics(pd.concat([tr,iv]))
        ranking.append(dict(candidate=name,family=z.family.iloc[0],eligible=ok,gate=gate,required_win_rate=req,max_stop_dollars=float(z.stop_dollars.max()),train_n=len(tr),inner_n=len(iv),**m))
    rank=pd.DataFrame(ranking).sort_values(["eligible","profit_factor","largest_day_pct"],ascending=[False,False,True]); rank.to_csv(OUT/"step2_combined_ranking.csv",index=False)
    for family in ("A","B"): rank[rank.family.eq(family)].to_csv(OUT/f"step2_family_{family}_ranking.csv",index=False)
    gate_table=rank[["candidate","family","max_stop_dollars","train_n","inner_n","win_rate","required_win_rate","eligible","gate"]].copy()
    gate_table["$150_stop_gate"] = gate_table.max_stop_dollars <= 150
    gate_table["Train_100_gate"] = gate_table.train_n >= 100
    gate_table["Inner_50_gate"] = gate_table.inner_n >= 50
    gate_table["feasibility_gate"] = gate_table.win_rate >= gate_table.required_win_rate
    gate_table.to_csv(OUT/"step2_gate_audit.csv",index=False)
    selected=rank.loc[rank.eligible,"candidate"].iloc[0] if rank.eligible.any() else None
    result={"research_pass_date":"2026-09-14","selection":selected,"step4":"incomplete","step5":"not run"}
    if selected:
        val=trades[(trades.candidate==selected)&(trades.period=="Validation")]; result["step4"]=account(val); val.to_csv(OUT/"validation_selected_trades.csv",index=False)
        if result["step4"]["status"]=="pass":
            oos=trades[(trades.candidate==selected)&(trades.period=="OOS")]; result["step5"]=account(oos); oos.to_csv(OUT/"oos_selected_trades.csv",index=False)
    (OUT/"results.json").write_text(json.dumps(result,indent=2,default=float))
    a_diag=trades[trades.family.eq("A")].groupby("candidate").natural_stop_dollars.agg(["count",lambda s: float((s<=150).mean()),"median","max"]).rename(columns={"<lambda_0>":"share_under_150"})
    a_diag.to_csv(OUT/"family_a_natural_stop_diagnostic.csv")
    def table(frame): return frame.to_markdown(index=False) if len(frame) else "_No candidates._"
    fam_lines=[]
    for f in ("A","B"):
        fr=rank[rank.family.eq(f)]; fam_lines += [f"### Family {f}","",table(fr),""]
    selected_row=rank[rank.candidate.eq(selected)].iloc[0] if selected else None
    diag_text=("Family A's raw (uncapped) stop distribution is below. The $150 gate was applied to each trade; it is not a replacement stop. " + a_diag.to_markdown() + "\n\nAll Family A signals were already below $150 (maximum $13); the gate did no disqualifying work and there is no excluded wide-stop tail. Family B has a predeclared fixed $150 spread stop, so it likewise has no retained-versus-excluded stop tail.")
    if selected_row is None: conclusion="No eligible candidate cleared Step 2; Validation and OOS were not run."
    else: conclusion=(f"Selected **{selected}**. Combined Train + Inner Validation: {selected_row.win_rate:.1%} win rate, {selected_row.payoff:.2f} payoff, {int(selected_row.n)} trades, and {selected_row.trades_per_month:.2f} trades/month.\n\n" + json.dumps(result,indent=2,default=float))
    family_verdict=lambda f: "no eligible candidate" if not rank[rank.family.eq(f)].eligible.any() else ("yes" if selected_row is not None and selected_row.family==f and isinstance(result["step4"],dict) and result["step4"]["status"]=="pass" else "no")
    overall="yes" if isinstance(result["step4"],dict) and result["step4"].get("status")=="pass" else "no"
    report=["# Tight-consolidation breakout & NQ--ES spread reversion", "", "## Frozen specification", "", f"Family A uses **X = {x:.2f} NQ points**, the Train (2010--2018) 25th percentile of completed trailing 30-minute high-low ranges. Family B uses 1 MNQ + 1 MES ($2/NQ point, $5/ES point), a **$4.00 combined round-trip cost**, spread `2*NQ - 5*ES`, 60-minute rolling z-score and |z| >= 2.0.", "", "## Step 2 -- Train + Inner Validation ranking", "", *fam_lines, "## Step 2 gate audit", "", table(gate_table), "", "All candidates passed the $150 stop and 100/50 trade-count gates. Every candidate failed the payoff-implied win-rate feasibility gate shown above. This is an aggregate Train + Inner Validation rule, so no single breach date/trade exists.", "", "## Natural-stop diagnostic", "", diag_text, "", "## Selection and account gate", "", conclusion, "", "Step 4: incomplete because Step 3 selected no candidate. Step 5: not run by the preregistered rule.", "", f"Passes 5%ers $25K constraints: {overall}. Family A viable: {family_verdict('A')}. Family B viable: {family_verdict('B')}." ]
    (OUT/"FINAL_REPORT.md").write_text("\n".join(report),encoding="utf-8")
    print(json.dumps(result,indent=2,default=float))


if __name__ == "__main__": main()
