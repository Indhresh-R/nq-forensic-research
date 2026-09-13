"""Frozen first-pass Initial Balance breakout backtest for NQ and ES.

The signal is known only once a five-minute bar has closed.  The simulated
entry is the following one-minute open.  Stop has priority when both a stop
and target lie inside one one-minute OHLC bar; this is deliberately hostile.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.nq_session import load_es, load_nq
from common.splits import split_of

ART = ROOT / "artifacts" / "30_initial_balance_breakout"
OPEN, IB_END, LAST_SIGNAL_CLOSE, FLAT_OPEN = 9 * 60 + 30, 10 * 60 + 30, 15 * 60 + 29, 15 * 60 + 55
POINT_VALUE = {"nq": 20.0, "es": 50.0}
DEFAULT_COST = {"nq": 1.0, "es": 0.5}  # round-trip points; override with actual execution assumptions


def load_market(market: str) -> pd.DataFrame:
    return load_nq() if market == "nq" else load_es()


def simulate_day(g0: pd.DataFrame, tick: float, cost: float) -> dict | None:
    """Return one first-breakout trade, or None. All timestamps are NY minutes."""
    # We need every minute through the planned 15:55 exit; early closes/holes are excluded.
    g = g0[(g0.ny_min >= OPEN) & (g0.ny_min <= FLAT_OPEN)].sort_values("ny_min").set_index("ny_min")
    required = pd.Index(range(OPEN, FLAT_OPEN + 1), name="ny_min")
    if not g.index.is_unique or not required.isin(g.index).all():
        return None
    g = g.loc[required]
    ib = g.loc[OPEN : IB_END - 1]
    ib_high, ib_low = float(ib.high.max()), float(ib.low.min())
    if ib_high <= ib_low:
        return None

    # Five-minute bars are [10:30,10:34], [10:35,10:39], ... .  Signal bar
    # closes at minute m; entry is known and made at open of m+1.
    signal_min = None
    side = 0
    for close_min in range(IB_END + 4, LAST_SIGNAL_CLOSE + 1, 5):
        five = g.loc[close_min - 4 : close_min]
        close = float(five.close.iloc[-1])
        if close >= ib_high + tick:
            signal_min, side = close_min, 1
            break
        if close <= ib_low - tick:
            signal_min, side = close_min, -1
            break
    if signal_min is None:
        return None

    entry_min = signal_min + 1
    entry = float(g.at[entry_min, "open"])
    stop = ib_low if side > 0 else ib_high
    risk = side * (entry - stop)
    if risk <= 0:  # defensive guard for a gapped-through entry
        return None
    target = entry + side * risk  # fixed 1R target

    exit_kind, exit_min, exit_price = "time", FLAT_OPEN, float(g.at[FLAT_OPEN, "open"])
    for minute in range(entry_min, FLAT_OPEN):
        hi, lo = float(g.at[minute, "high"]), float(g.at[minute, "low"])
        stop_hit = lo <= stop if side > 0 else hi >= stop
        target_hit = hi >= target if side > 0 else lo <= target
        if stop_hit:  # same-bar ambiguity resolves against the strategy
            exit_kind, exit_min, exit_price = "stop", minute, stop
            break
        if target_hit:
            exit_kind, exit_min, exit_price = "target", minute, target
            break
    gross = side * (exit_price - entry)
    return {
        "session_date": str(g0.session_date.iloc[0]),
        "year": int(g0.year.iloc[0]),
        "split": split_of(int(g0.year.iloc[0])),
        "side": "long" if side > 0 else "short",
        "ib_high": ib_high,
        "ib_low": ib_low,
        "ib_width": ib_high - ib_low,
        "signal_ny_min": signal_min,
        "entry_ny_min": entry_min,
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk_points": risk,
        "exit_ny_min": exit_min,
        "exit": exit_price,
        "exit_kind": exit_kind,
        "gross_points": gross,
        "cost_points": cost,
        "net_points": gross - cost,
        "net_r": (gross - cost) / risk,
    }


def summarize(t: pd.DataFrame, point_value: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for split, x in t.groupby("split", sort=False):
        pnl = x.net_points.to_numpy(float)
        wins, losses = pnl[pnl > 0], pnl[pnl < 0]
        equity = np.cumsum(pnl)
        dd = equity - np.maximum.accumulate(np.r_[0.0, equity])[1:]
        rows.append({
            "split": split, "trades": len(x), "win_rate": float(np.mean(pnl > 0)),
            "avg_net_points": float(np.mean(pnl)), "median_net_points": float(np.median(pnl)),
            "net_points": float(pnl.sum()), "net_dollars_1_contract": float(pnl.sum() * point_value),
            "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) else np.nan,
            "max_drawdown_points": float(dd.min()) if len(dd) else np.nan,
            "max_drawdown_dollars_1_contract": float(dd.min() * point_value) if len(dd) else np.nan,
            "target_rate": float(np.mean(x.exit_kind == "target")),
            "stop_rate": float(np.mean(x.exit_kind == "stop")),
            "time_rate": float(np.mean(x.exit_kind == "time")),
            "long_trades": int(np.sum(x.side == "long")), "short_trades": int(np.sum(x.side == "short")),
        })
    yearly = (t.groupby(["year", "split"], as_index=False)
                .agg(trades=("net_points", "size"), net_points=("net_points", "sum"),
                     avg_net_points=("net_points", "mean"), win_rate=("net_points", lambda s: (s > 0).mean())))
    yearly["net_dollars_1_contract"] = yearly.net_points * point_value
    return pd.DataFrame(rows), yearly


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=("nq", "es"), default="nq")
    parser.add_argument("--cost-points", type=float, default=None, help="round-trip cost in index points")
    args = parser.parse_args()
    cost = DEFAULT_COST[args.market] if args.cost_points is None else args.cost_points
    tick = 0.25
    ART.mkdir(parents=True, exist_ok=True)
    df = load_market(args.market)
    trades = [r for _, g in df.groupby("session_date", sort=True) if (r := simulate_day(g, tick, cost))]
    t = pd.DataFrame(trades)
    if t.empty:
        raise RuntimeError("No qualifying trades; inspect source coverage and session clock.")
    summary, yearly = summarize(t, POINT_VALUE[args.market])
    stem = f"{args.market}_baseline"
    t.to_csv(ART / f"{stem}_trades.csv", index=False)
    summary.to_csv(ART / f"{stem}_summary.csv", index=False)
    yearly.to_csv(ART / f"{stem}_yearly.csv", index=False)
    verdict = {
        "market": args.market.upper(), "status": "DESCRIPTIVE_BASELINE_ONLY",
        "rules": {"ib": "09:30-10:29 ET", "signal": "first 5m close >= IB high + 1 tick or <= IB low - 1 tick",
                  "entry": "next 1m open", "stop": "opposite IB edge", "target": "1R", "flat": "15:55 ET open",
                  "same_bar_rule": "stop first", "max_trades_per_day": 1},
        "cost_points_round_trip": cost, "point_value_1_contract": POINT_VALUE[args.market],
        "split_summary": summary.to_dict(orient="records"),
        "pass_condition": "Validation and OOS expectancy both positive after costs; then perform robustness tests.",
    }
    (ART / f"{stem}_verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    report = [f"# {args.market.upper()} Initial Balance breakout — frozen baseline", "",
              "Not a live recommendation. This is a first mechanical test; no parameters were selected from its results.", "",
              "## Split summary", "", summary.to_markdown(index=False), "", "## Yearly results", "",
              yearly.to_markdown(index=False), "", "## Rules", "",
              "- IB: 09:30–10:29 ET; first qualifying five-minute close starts at 10:34.",
              "- Entry: next one-minute open. One trade maximum per session.",
              "- Stop: opposite IB edge. Target: 1R. Time exit: 15:55 ET open.",
              "- Same-bar stop/target collision: stop is assumed first. Net P&L deducts the configured round-trip cost.",
              "", "A positive discovery result is not a finding. Require positive Validation and OOS results, then test cost, stop/target, and session-width sensitivity without repeatedly selecting on OOS."]
    (ART / f"{stem}_report.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
