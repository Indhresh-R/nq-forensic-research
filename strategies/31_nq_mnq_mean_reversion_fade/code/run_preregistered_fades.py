"""NQ/MNQ mean-reversion fade -- frozen pre-registration, 2026-09-14.

This script intentionally contains one fixed five-candidate list.  Do not edit
the constants after inspecting its Train/Inner-Validation outputs.  The source
of truth for the rules is the PREREGISTRATION.md alongside this script.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import build_day_context, load_nq  # noqa: E402

OUT = ROOT / "artifacts" / "31_nq_mnq_mean_reversion_fade"
OUT.mkdir(parents=True, exist_ok=True)

# FROZEN BEFORE EXECUTION.  Costs are the prior 1.0 NQ-point RT assumption,
# scaled from $20/point NQ to $2/point MNQ: $2.00 RT = 1.0 index point.
MNQ_POINT_VALUE, COST_DOLLARS = 2.0, 2.0
SESSION_START, FIRST_SIGNAL, LAST_ENTRY, FLAT = 570, 585, 900, 955
VWAP_BAND_POINTS, VWAP_EXTENSION_POINTS = 20.0, 10.0
OR_START, OR_END, OR_REENTRY_WINDOW = 570, 599, 10
FIVE_MIN_SMA_BARS, FIVE_MIN_Z = 20, 2.0
HIGH_THRESHOLDS = json.loads((ROOT / "artifacts" / "06_HIGH_opportunity_state" /
                              "ny_open_opp_timing_thresholds_IS.json").read_text())["state_terciles"]["rng_onr"]

CANDIDATES = {
    "vwap_fade_1r": dict(stop=75.0, target_r=1.0),
    "vwap_fade_1p5r": dict(stop=75.0, target_r=1.5),
    "opening_range_fade": dict(stop=87.5, target_r=None),
    "high_state_vwap_fade_1r": dict(stop=75.0, target_r=1.0),
    "extension_5m_fade_1p5r": dict(stop=100.0, target_r=1.5),
}


def period(year: int) -> str:
    if 2010 <= year <= 2018: return "Train"
    if 2019 <= year <= 2021: return "Inner Validation"
    if 2022 <= year <= 2024: return "Validation"
    if 2025 <= year <= 2026: return "OOS"
    return "Other"


def exit_trade(g: pd.DataFrame, start_i: int, side: int, entry: float, stop_pts: float, target_pts: float):
    """Stop-first intrabar convention; final unclosed position exits 15:55 close."""
    stop = entry - side * stop_pts
    target = entry + side * target_pts
    highs, lows = g.high.to_numpy(float), g.low.to_numpy(float)
    stop_hits = np.flatnonzero((lows[start_i:] <= stop) if side > 0 else (highs[start_i:] >= stop))
    target_hits = np.flatnonzero((highs[start_i:] >= target) if side > 0 else (lows[start_i:] <= target))
    stop_pos = start_i + int(stop_hits[0]) if len(stop_hits) else len(g)
    target_pos = start_i + int(target_hits[0]) if len(target_hits) else len(g)
    if stop_pos < len(g) and stop_pos <= target_pos:  # intentionally adverse on collisions
        return stop, "stop", g.iloc[stop_pos].ts
    if target_pos < len(g):
        return target, "target", g.iloc[target_pos].ts
    b = g.iloc[-1]
    return float(b.close), "time", b.ts


def high_state(g: pd.DataFrame, ctx: pd.Series, i: int) -> bool:
    """Existing validated vol_expansion_high, evaluated causally at prior 5m clock."""
    elapsed = int(g.iloc[i].ny_min) - SESSION_START
    clock = min(90, 5 * (elapsed // 5))
    if clock < 5 or clock > 90 or not ctx.onr > 0:
        return False
    seen = g.iloc[: i + 1]
    rng_onr = (seen.high.max() - seen.low.min()) / float(ctx.onr)
    return rng_onr >= float(HIGH_THRESHOLDS[str(clock)]["p66"])


def append_trade(rows, name, g, i, side, stop_pts, target_pts, signal_ts):
    entry = float(g.iloc[i].open)
    exit_px, kind, exit_ts = exit_trade(g, i, side, entry, stop_pts, target_pts)
    gross_pts = side * (exit_px - entry)
    rows.append(dict(candidate=name, session_date=str(g.iloc[i].session_date), year=int(g.iloc[i].year),
                     period=period(int(g.iloc[i].year)), side="long" if side > 0 else "short",
                     signal_ts=str(signal_ts), entry_ts=str(g.iloc[i].ts), exit_ts=str(exit_ts),
                     entry=entry, exit=exit_px, stop_points=stop_pts, target_points=target_pts,
                     exit_kind=kind, gross_points=gross_pts, net_dollars=gross_pts * MNQ_POINT_VALUE - COST_DOLLARS))


def build_trades(df: pd.DataFrame, contexts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ctx_map = {r.session_date: r for _, r in contexts.iterrows()}
    for sd, raw in df.groupby("session_date", sort=True):
        ctx = ctx_map.get(sd)
        if ctx is None: continue
        g = raw[(raw.ny_min >= SESSION_START) & (raw.ny_min <= FLAT)].reset_index(drop=True)
        if len(g) < 100: continue
        # cumulative session VWAP, only RTH bars through each completed bar.
        typical = (g.high + g.low + g.close) / 3
        vwap = (typical * g.volume).cumsum() / g.volume.cumsum()
        # Candidate 1, 2, 4: first completed signal, next one-minute open.
        chosen = {"vwap_fade_1r": False, "vwap_fade_1p5r": False, "high_state_vwap_fade_1r": False}
        for j in range(len(g) - 1):
            minute = int(g.iloc[j].ny_min)
            if minute < FIRST_SIGNAL or minute > LAST_ENTRY: continue
            delta = float(g.iloc[j].close - vwap.iloc[j])
            if abs(delta) < VWAP_BAND_POINTS + VWAP_EXTENSION_POINTS: continue
            side = -1 if delta > 0 else 1
            for name in ("vwap_fade_1r", "vwap_fade_1p5r"):
                if not chosen[name]:
                    c = CANDIDATES[name]; append_trade(rows, name, g, j + 1, side, c["stop"], c["stop"] * c["target_r"], g.iloc[j].ts); chosen[name] = True
            if not chosen["high_state_vwap_fade_1r"] and high_state(g, ctx, j):
                c = CANDIDATES["high_state_vwap_fade_1r"]; append_trade(rows, "high_state_vwap_fade_1r", g, j + 1, side, c["stop"], c["stop"], g.iloc[j].ts); chosen["high_state_vwap_fade_1r"] = True
            if all(chosen.values()): break
        # Candidate 3: 09:30-09:59 OR; first close back inside within 10 min of a close outside.
        or_bars = g[(g.ny_min >= OR_START) & (g.ny_min <= OR_END)]
        if len(or_bars) == 30:
            hi, lo, mid, outside_j = float(or_bars.high.max()), float(or_bars.low.min()), float((or_bars.high.max()+or_bars.low.min())/2), None
            for j in range(len(g) - 1):
                m, close = int(g.iloc[j].ny_min), float(g.iloc[j].close)
                if m <= OR_END: continue
                if close > hi or close < lo: outside_j = j; continue
                if outside_j is not None and j - outside_j <= OR_REENTRY_WINDOW and lo <= close <= hi:
                    side = -1 if float(g.iloc[outside_j].close) > hi else 1
                    target = min(abs(float(g.iloc[j+1].open) - mid), CANDIDATES["opening_range_fade"]["stop"])
                    if target > 0: append_trade(rows, "opening_range_fade", g, j + 1, side, 87.5, target, g.iloc[j].ts)
                    break
                if outside_j is not None and j - outside_j > OR_REENTRY_WINDOW: outside_j = None
        # Candidate 5: 5m bar closing >2 SD from prior 20 completed 5m closes, then next 1m open.
        h = g.copy(); h["bin"] = ((h.ny_min - SESSION_START) // 5).astype(int)
        bars = h.groupby("bin", sort=True).agg(close=("close", "last"), last_i=("close", lambda x: x.index[-1]))
        for k in range(FIVE_MIN_SMA_BARS, len(bars)):
            j = int(bars.iloc[k].last_i); m = int(g.iloc[j].ny_min)
            if j + 1 >= len(g) or m < FIRST_SIGNAL or m > LAST_ENTRY: continue
            prior = bars.iloc[k-FIVE_MIN_SMA_BARS:k].close.astype(float)
            sdv = float(prior.std(ddof=0)); z = (float(bars.iloc[k].close) - float(prior.mean())) / sdv if sdv > 0 else 0
            if abs(z) > FIVE_MIN_Z:
                append_trade(rows, "extension_5m_fade_1p5r", g, j + 1, -1 if z > 0 else 1, 100.0, 150.0, g.iloc[j].ts); break
    return pd.DataFrame(rows)


def metrics(x: pd.DataFrame) -> dict:
    n = len(x); wins = x[x.net_dollars > 0]; losses = x[x.net_dollars <= 0]
    payoff = wins.net_dollars.mean() / abs(losses.net_dollars.mean()) if len(wins) and len(losses) else np.nan
    pf = wins.net_dollars.sum() / abs(losses.net_dollars.sum()) if len(losses) else np.nan
    return dict(n=n, net_dollars=x.net_dollars.sum(), win_rate=(len(wins)/n if n else np.nan), payoff=payoff, profit_factor=pf,
                trades_per_month=n / (len(x.session_date.str[:7].unique()) or np.nan), largest_day_pct=(x.groupby("session_date").net_dollars.sum().max()/x.net_dollars.sum() if x.net_dollars.sum()>0 else np.nan))


def eligible(train: pd.DataFrame, inner: pd.DataFrame, c: dict) -> tuple[bool, str]:
    if c["stop"] * MNQ_POINT_VALUE > 200: return False, "stop cap"
    if len(train) < 100: return False, "<100 Train trades"
    if len(inner) < 50: return False, "<50 Inner Validation trades"
    m = metrics(pd.concat([train, inner])); required = 1 / (1 + m["payoff"]) if np.isfinite(m["payoff"]) else np.inf
    if not np.isfinite(m["win_rate"]) or m["win_rate"] < required: return False, f"win rate {m['win_rate']:.3f} below payoff-implied {required:.3f}"
    return True, "pass"


def account_sim(x: pd.DataFrame) -> dict:
    """Day-by-day $1k EOD trailing, $600 daily and 50% cumulative-profit rule."""
    equity = peak = 0.0
    for day, d in x.groupby("session_date", sort=True):
        pnl = float(d.net_dollars.sum()); equity += pnl; peak = max(peak, equity)
        if pnl < -600: return dict(status="fail", rule="daily loss", date=day, equity=equity)
        if peak - equity > 1000: return dict(status="fail", rule="overall EOD trailing", date=day, equity=equity)
        if equity > 0 and pnl > 0.5 * equity: return dict(status="fail", rule="50% consistency", date=day, equity=equity)
    return dict(status="pass" if equity >= 1500 else "fail", rule="profit target" if equity < 1500 else "none", date=None, equity=equity)


def main():
    print("Frozen MNQ fade pre-registration. Cost: $2.00 RT.", flush=True)
    df = load_nq()
    contexts = build_day_context(df)
    trades = build_trades(df, contexts); trades.to_csv(OUT / "all_candidate_trades.csv", index=False)
    ranking = []
    for name, c in CANDIDATES.items():
        x = trades[trades.candidate == name]; train, inner = x[x.period == "Train"], x[x.period == "Inner Validation"]
        ok, reason = eligible(train, inner, c); comb = pd.concat([train, inner]); m = metrics(comb)
        ranking.append(dict(candidate=name, eligible=ok, gate=reason, combined_pf=m["profit_factor"], combined_net=m["net_dollars"], largest_day_pct=m["largest_day_pct"], **{f"{p}_{k}":v for p in ("Train", "Inner Validation") for k,v in metrics(x[x.period==p]).items()}))
    rank = pd.DataFrame(ranking).sort_values(["eligible", "combined_pf", "largest_day_pct"], ascending=[False, False, True]); rank.to_csv(OUT / "step2_train_inner_ranking.csv", index=False)
    selected = rank[rank.eligible]
    selected_name = selected.iloc[0].candidate if len(selected) else None
    result = {"cost_dollars_round_trip": COST_DOLLARS, "selection": selected_name, "step4": "incomplete", "step5": "not run"}
    if selected_name:
        tx = trades[trades.candidate == selected_name]
        val = tx[tx.period == "Validation"]; vmet = metrics(val); sim = account_sim(val)
        result["step4"] = {**sim, **vmet}; val.to_csv(OUT / "validation_selected_trades.csv", index=False)
        if sim["status"] == "pass":
            oos = tx[tx.period == "OOS"]; result["step5"] = {**account_sim(oos), **metrics(oos)}; oos.to_csv(OUT / "oos_selected_trades.csv", index=False)
    (OUT / "results.json").write_text(json.dumps(result, indent=2, default=float))
    lines=["# NQ/MNQ mean-reversion fade -- results", "", "## Step 2 ranking", "", rank.to_markdown(index=False), "", "## Selection / account gates", "", "```json", json.dumps(result, indent=2, default=float), "```"]
    (OUT / "FINAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2, default=float))

if __name__ == "__main__": main()
