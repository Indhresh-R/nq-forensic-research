"""Causal explanatory study of 15m support-break failure versus matched down moves."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_es, load_nq
from common.splits import split_of

OUT = ROOT / "artifacts" / "15m_downside_break_failure"
OUT.mkdir(parents=True, exist_ok=True)
HORIZONS = (1, 5, 15, 30, 60)
BANDS = [-np.inf, 0.5, 1.0, 1.5, np.inf]
LABELS = ("<0.5", "0.5-1.0", "1.0-1.5", "1.5+")


def bars_15m(x: pd.DataFrame) -> pd.DataFrame:
    y = x.copy(); y["offset"] = (y.ny_min - 1080) % 1440; y["bucket"] = y.offset // 15
    return y.groupby(["session_date", "bucket"], sort=True).agg(end=("ts", "last"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size"), year=("year", "last"), key=("session_date", "last")).reset_index(drop=True).query("n == 15").reset_index(drop=True)


def collect(base: pd.DataFrame, market: str) -> list[dict]:
    b = bars_15m(base)
    h, l, o, c = (b[k].to_numpy(float) for k in ("high", "low", "open", "close"))
    prev_close = np.r_[np.nan, c[:-1]]
    tr = np.maximum(h-l, np.maximum(np.abs(h-prev_close), np.abs(l-prev_close)))
    atr = pd.Series(tr).rolling(20).mean().shift(1).to_numpy()
    support = pd.Series(l).rolling(20).min().shift(1).to_numpy()
    down = (o-c) / atr
    is_break = (c < support) & (np.r_[np.nan, c[:-1]] >= support)
    is_control = (c < o) & (c >= support) & np.isfinite(down)
    band = pd.cut(down, BANDS, labels=LABELS, right=False)
    candidates = pd.DataFrame({"i": np.arange(len(b)), "event_type": np.where(is_break, "break", "control"), "is_break": is_break, "is_control": is_control, "band": band, "key": b.key, "year": b.year})
    br = candidates[candidates.is_break & (candidates.i >= 21)].drop_duplicates(["key"], keep="first")
    ct = candidates[candidates.is_control & (candidates.i >= 21)].drop_duplicates(["key", "band"], keep="first")
    selected = pd.concat([br, ct], ignore_index=True).sort_values("i")
    ix = pd.DatetimeIndex(base.ts)
    rows = []
    for r in selected.itertuples(index=False):
        i = int(r.i); last = ix.get_indexer([b.end.iat[i]])[0]; entry_i = last + 1
        if last < 0 or entry_i + 60 >= len(base): continue
        entry, level = float(base.open.iat[entry_i]), float(support[i])
        path60 = base.iloc[entry_i:entry_i+60]
        closes = path60.close.to_numpy(float)
        above = np.flatnonzero(closes > level)
        common = dict(market=market, event_type=r.event_type, signal_time=str(b.end.iat[i]), split=split_of(int(r.year)), year=int(r.year), band=str(r.band), normalized_down_move=float(down[i]), entry=entry, support=level)
        for horizon in HORIZONS:
            p = base.iloc[entry_i:entry_i+horizon]
            ret = float(p.close.iat[-1] - entry); mfe = float(p.high.max() - entry); mae = float(p.low.min() - entry)
            rows.append(common | dict(horizon_min=horizon, fade_return_pts=ret, fade_mfe_pts=mfe, fade_mae_pts=mae, positive_return=int(ret > 0), time_to_recover_min=(int(above[0])+1 if len(above) else np.nan), fraction_below_60=float(np.mean(closes < level)), max_recovery_60_pts=float(path60.high.max()-level)))
    return rows


def main() -> None:
    rows = []
    for market, loader in (("NQ", load_nq), ("ES", load_es)):
        rows.extend(collect(loader().sort_values("ts").reset_index(drop=True), market))
    d = pd.DataFrame(rows); d.to_csv(OUT / "events.csv", index=False)
    summary = d.groupby(["market", "split", "event_type", "band", "horizon_min"], as_index=False).agg(events=("fade_return_pts", "size"), mean_fade_return_pts=("fade_return_pts", "mean"), median_fade_return_pts=("fade_return_pts", "median"), p10_fade_return_pts=("fade_return_pts", lambda x: x.quantile(.10)), p90_fade_return_pts=("fade_return_pts", lambda x: x.quantile(.90)), positive_rate=("positive_return", "mean"), mfe_pts=("fade_mfe_pts", "mean"), mae_pts=("fade_mae_pts", "mean"), time_to_recover_min=("time_to_recover_min", "mean"), fraction_below_60=("fraction_below_60", "mean"), max_recovery_60_pts=("max_recovery_60_pts", "mean"))
    summary.to_csv(OUT / "summary.csv", index=False)
    # Difference uses identical market/split/band/horizon cells: break minus control.
    piv = summary.pivot_table(index=["market", "split", "band", "horizon_min"], columns="event_type", values=["mean_fade_return_pts", "positive_rate"], aggfunc="first")
    diff = piv.dropna().copy(); diff["fade_return_diff_break_minus_control"] = diff[("mean_fade_return_pts", "break")] - diff[("mean_fade_return_pts", "control")]; diff["positive_rate_diff_break_minus_control"] = diff[("positive_rate", "break")] - diff[("positive_rate", "control")]
    diff.reset_index().to_csv(OUT / "break_minus_control.csv", index=False)
    print(summary.to_string(index=False)); print(diff.reset_index().to_string(index=False))


if __name__ == "__main__": main()
