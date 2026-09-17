"""Frozen 15m support/resistance event-path study; no execution optimization."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_es, load_nq
from common.splits import split_of

OUT = ROOT / "artifacts" / "42_15m_sr_breakout_information"
OUT.mkdir(parents=True, exist_ok=True)
HORIZONS = (1, 5, 15, 30, 60)


def bars_15m(x: pd.DataFrame) -> pd.DataFrame:
    y = x.copy()
    y["offset"] = (y.ny_min - 18 * 60) % (24 * 60)
    y["bucket"] = y.offset // 15
    b = y.groupby(["session_date", "bucket"], sort=True).agg(
        end=("ts", "last"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size"), year=("year", "last"), key=("session_date", "last")
    ).reset_index(drop=True)
    return b[b.n == 15].reset_index(drop=True)


def events(base: pd.DataFrame, market: str) -> list[dict]:
    b = bars_15m(base)
    high, low, close = (b[c].to_numpy(float) for c in ("high", "low", "close"))
    resistance = pd.Series(high).rolling(20).max().shift(1).to_numpy()
    support = pd.Series(low).rolling(20).min().shift(1).to_numpy()
    long_i = np.flatnonzero((close[:-1] <= resistance[1:]) & (close[1:] > resistance[1:])) + 1
    short_i = np.flatnonzero((close[:-1] >= support[1:]) & (close[1:] < support[1:])) + 1
    raw = pd.concat([pd.DataFrame({"i": long_i, "side": 1}), pd.DataFrame({"i": short_i, "side": -1})], ignore_index=True)
    raw = raw[(raw.i >= 21) & (raw.i < len(b)-1)].sort_values("i")
    raw["key"] = b.key.to_numpy()[raw.i.to_numpy()]
    raw = raw.drop_duplicates(["key", "side"])
    base_index = pd.DatetimeIndex(base.ts)
    out = []
    for row in raw.itertuples(index=False):
        i, side = int(row.i), int(row.side)
        last_i = base_index.get_indexer([b.end.iat[i]])[0]
        entry_i = last_i + 1
        if last_i < 0 or entry_i + max(HORIZONS) >= len(base):
            continue
        level = resistance[i] if side == 1 else support[i]
        for h in HORIZONS:
            path = base.iloc[entry_i : entry_i + h]
            entry = float(base.open.iat[entry_i])
            end = float(path.close.iat[-1])
            signed_ret = side * (end - entry)
            mfe = side * ((float(path.high.max()) if side == 1 else float(path.low.min())) - entry)
            mae = side * ((float(path.low.min()) if side == 1 else float(path.high.max())) - entry)
            close_beyond = side * (end - level) > 0
            closes = path.close.to_numpy(float)
            failed = bool(np.any(closes <= level)) if side == 1 else bool(np.any(closes >= level))
            out.append(dict(market=market, signal_time=str(b.end.iat[i]), year=int(b.year.iat[i]), split=split_of(int(b.year.iat[i])), side="long" if side == 1 else "short", horizon_min=h, level=float(level), entry=entry, signed_return_pts=signed_ret, mfe_pts=mfe, mae_pts=mae, close_beyond_level=int(close_beyond), failed_through_level=int(failed)))
    return out


def main() -> None:
    rows = []
    for market, loader in (("NQ", load_nq), ("ES", load_es)):
        rows.extend(events(loader().sort_values("ts").reset_index(drop=True), market))
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "events.csv", index=False)
    summary = d.groupby(["market", "split", "side", "horizon_min"], as_index=False).agg(
        events=("signed_return_pts", "size"), forward_return_pts=("signed_return_pts", "mean"), mfe_pts=("mfe_pts", "mean"), mae_pts=("mae_pts", "mean"), close_beyond_rate=("close_beyond_level", "mean"), failure_rate=("failed_through_level", "mean")
    )
    summary.to_csv(OUT / "summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
