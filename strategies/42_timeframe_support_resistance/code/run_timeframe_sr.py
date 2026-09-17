"""Frozen Strategy 42: identical support/resistance rules across timeframes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_es, load_nq
from common.splits import split_of

OUT = ROOT / "artifacts" / "42_timeframe_support_resistance"
OUT.mkdir(parents=True, exist_ok=True)
TIMEFRAMES = [("1m", 1), ("5m", 5), ("15m", 15), ("30m", 30), ("1h", 60), ("2h", 120), ("4h", 240), ("7h", 420)]
COST = {"NQ": 1.0, "ES": 0.5}


def aggregate(df: pd.DataFrame, name: str, minutes: int | None) -> pd.DataFrame:
    x = df.copy()
    if name == "1m":
        return pd.DataFrame({"start": x.ts, "end": x.ts, "open": x.open, "high": x.high, "low": x.low, "close": x.close, "n": 1, "year": x.year, "key": x.session_date})
    if name == "1D":
        x["bucket"] = x["session_date"]
        g = x.groupby("bucket", sort=True)
        b = g.agg(start=("ts", "first"), end=("ts", "last"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size"), year=("year", "last"), key=("session_date", "last")).reset_index(drop=True)
        return b[b.n >= 1200].reset_index(drop=True)
    if name == "1W":
        d = aggregate(df, "1D", None)
        d["bucket"] = pd.to_datetime(d["key"]).dt.to_period("W-FRI")
        g = d.groupby("bucket", sort=True)
        b = g.agg(start=("start", "first"), end=("end", "last"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), sessions=("close", "size"), year=("year", "last"), key=("bucket", "last")).reset_index(drop=True)
        return b[b.sessions == 5].reset_index(drop=True)
    # Each Globex session starts at 18:00 NY. Only fully observed bars are retained.
    x["offset"] = (x["ny_min"] - 18 * 60) % (24 * 60)
    x["bucket"] = x["offset"] // int(minutes)
    g = x.groupby(["session_date", "bucket"], sort=True)
    b = g.agg(start=("ts", "first"), end=("ts", "last"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size"), year=("year", "last"), key=("session_date", "last")).reset_index(drop=True)
    return b[b.n == minutes].reset_index(drop=True)


def run_arm(base: pd.DataFrame, bars: pd.DataFrame, tf: str, market: str) -> list[dict]:
    H, L, C = (bars[c].to_numpy(float) for c in ("high", "low", "close"))
    # Precompute the causal 20-bar levels and only visit actual crossings.  This
    # matters for the 1-minute series (millions of bars), while leaving the rule
    # exactly unchanged.
    resistance = pd.Series(H).rolling(20).max().shift(1).to_numpy()
    support = pd.Series(L).rolling(20).min().shift(1).to_numpy()
    long_ix = np.flatnonzero((C[:-1] <= resistance[1:]) & (C[1:] > resistance[1:])) + 1
    short_ix = np.flatnonzero((C[:-1] >= support[1:]) & (C[1:] < support[1:])) + 1
    raw = pd.concat([pd.DataFrame({"i": long_ix, "side": 1}), pd.DataFrame({"i": short_ix, "side": -1})], ignore_index=True)
    raw = raw[(raw.i >= 21) & (raw.i < len(bars)-9)].sort_values("i")
    raw["key"] = bars.key.to_numpy()[raw.i.to_numpy()]
    # The one-per-side-per-session rule is resolved before doing any expensive
    # retest work; later same-session crossings are not candidates by definition.
    candidates = list(raw.drop_duplicates(["key", "side"])[["i", "side"]].itertuples(index=False, name=None))
    if tf == "1m" and len(bars) == len(base):
        end_ix = np.arange(len(base), dtype=int)
    else:
        end_ix = pd.DatetimeIndex(base.ts).get_indexer(pd.DatetimeIndex(bars.end))
    base_low = base.low.to_numpy(float)
    base_high = base.high.to_numpy(float)
    base_close = base.close.to_numpy(float)
    rows: list[dict] = []
    for i, side in candidates:
        entry_i = end_ix[i] + 1
        if end_ix[i] < 0 or entry_i >= len(base):
            continue
        level = resistance[i] if side == 1 else support[i]
        # Breakout: frozen five-bar exit.
        rows.append(dict(market=market, timeframe=tf, arm="breakout", signal_time=str(bars.end.iat[i]), signal_year=int(bars.year.iat[i]), side=side, level=level, entry_time=str(base.ts.iat[entry_i]), entry=float(base.open.iat[entry_i]), exit_time=str(bars.end.iat[i+5]), exit=float(C[i+5])))
        # Retest: search only in the next three completed frame bars, minute by minute.
        found = None
        for j in range(i+1, i+4):
            a, z = end_ix[i] + 1, end_ix[j] + 1
            if a < 1 or z <= a:
                continue
            ok = (base_low[a:z] <= level) & (base_high[a:z] >= level) & ((base_close[a:z] > level) if side == 1 else (base_close[a:z] < level))
            if ok.any():
                p = a + int(np.flatnonzero(ok)[0])
                found = (p, j)
                break
        if found is not None:
            p, j = found
            ri = p + 1
            if ri < len(base):
                rows.append(dict(market=market, timeframe=tf, arm="retest", signal_time=str(bars.end.iat[i]), signal_year=int(bars.year.iat[i]), side=side, level=level, entry_time=str(base.ts.iat[ri]), entry=float(base.open.iat[ri]), exit_time=str(bars.end.iat[j+5]), exit=float(C[j+5])))
    return rows


def metrics(x: pd.DataFrame) -> dict:
    net = x.net.to_numpy(float)
    pos, neg = net[net > 0].sum(), -net[net < 0].sum()
    return {"trades": len(x), "win_rate": float((net > 0).mean()), "gross_expectancy_pts": float(x.gross.mean()), "net_expectancy_pts": float(net.mean()), "net_total_pts": float(net.sum()), "profit_factor": float(pos / neg) if neg else None, "cost_burden_of_abs_gross": float(x.cost.sum() / x.gross.abs().sum()) if x.gross.abs().sum() else None}


def main() -> None:
    all_rows = []
    for market, loader in (("NQ", load_nq), ("ES", load_es)):
        base = loader().sort_values("ts").reset_index(drop=True)
        for name, mins in TIMEFRAMES + [("1D", None), ("1W", None)]:
            bars = aggregate(base, name, mins)
            all_rows.extend(run_arm(base, bars, name, market))
            print(market, name, len(bars))
    trades = pd.DataFrame(all_rows)
    trades["gross"] = trades.side * (trades.exit - trades.entry)
    trades["cost"] = trades.market.map(COST)
    trades["net"] = trades.gross - trades.cost
    trades["split"] = trades.signal_year.map(split_of)
    trades.to_csv(OUT / "all_trades.csv", index=False)
    summary = []
    for keys, x in trades.groupby(["market", "timeframe", "arm", "split"], sort=False):
        summary.append(dict(zip(["market", "timeframe", "arm", "split"], keys)) | metrics(x))
    s = pd.DataFrame(summary)
    s.to_csv(OUT / "summary.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(s.to_string(index=False))


if __name__ == "__main__":
    main()
