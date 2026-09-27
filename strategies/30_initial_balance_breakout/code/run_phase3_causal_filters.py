"""Causal, standalone filters for the unchanged NQ IB baseline.

Filters are selected only by Train (2010-18) and inner validation (2019-21).
Later periods are shown but never used for selection.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_nq  # noqa: E402

ART = ROOT / "artifacts" / "30_initial_balance_breakout"
OPEN, IB_END = 570, 630

def period(year: int) -> str:
    if year <= 2018: return "Train"
    if year <= 2021: return "Inner_Validation"
    if year <= 2024: return "Validation"
    return "OOS"

def summary(x: pd.DataFrame) -> dict:
    p = x.net_points.to_numpy(float); w, l = p[p > 0], p[p < 0]
    return {"trades": len(x), "avg_net_points": p.mean() if len(p) else np.nan,
            "win_rate": (p > 0).mean() if len(p) else np.nan,
            "profit_factor": w.sum()/abs(l.sum()) if len(l) else np.nan,
            "median_risk": x.risk_points.median() if len(x) else np.nan,
            "max_risk": x.risk_points.max() if len(x) else np.nan}

def main() -> None:
    trades = pd.read_csv(ART / "nq_baseline_trades.csv")
    nq = load_nq()
    rth = nq[(nq.ny_min >= OPEN) & (nq.ny_min <= 959)].copy()
    rth["sd"] = rth.session_date.astype(str)
    rth["typical"] = (rth.high + rth.low + rth.close) / 3
    rth["pv"] = rth.typical * rth.volume
    rth["cum_pv"] = rth.groupby("sd", sort=False).pv.cumsum()
    rth["cum_vol"] = rth.groupby("sd", sort=False).volume.cumsum()
    rth["vwap"] = rth.cum_pv / rth.cum_vol
    ib = (rth[rth.ny_min < IB_END].groupby("sd", as_index=False)
          .agg(ib_high=("high", "max"), ib_low=("low", "min")))
    ib["ib_width"] = ib.ib_high - ib.ib_low
    ib["prior20_median_ib"] = ib.ib_width.shift(1).rolling(20, min_periods=20).median()
    ib["ib_vs_prior20"] = ib.ib_width / ib.prior20_median_ib

    # One causally complete 5-minute signal bar per baseline trade.
    rth["bucket"] = (rth.ny_min - OPEN) // 5
    five = (rth.groupby(["sd", "bucket"], as_index=False)
            .agg(bar_open=("open", "first"), bar_high=("high", "max"), bar_low=("low", "min"),
                 bar_close=("close", "last"), bar_close_min=("ny_min", "last")))
    meta = trades.merge(ib[["sd", "ib_vs_prior20"]], left_on="session_date", right_on="sd", how="left")
    meta = meta.merge(rth[["sd", "ny_min", "vwap"]], left_on=["session_date", "signal_ny_min"], right_on=["sd", "ny_min"], how="left")
    meta = meta.merge(five, left_on=["session_date", "signal_ny_min"], right_on=["sd", "bar_close_min"], how="left")
    body = (meta.bar_close - meta.bar_open).abs()
    rng = meta.bar_high - meta.bar_low
    strong = (body / rng.replace(0, np.nan) >= 0.50) & (((meta.side == "long") & (meta.bar_close > meta.bar_open)) | ((meta.side == "short") & (meta.bar_close < meta.bar_open)))
    vwap_ok = ((meta.side == "long") & (meta.bar_close > meta.vwap)) | ((meta.side == "short") & (meta.bar_close < meta.vwap))
    filters = {
        "baseline_all": pd.Series(True, index=meta.index),
        "risk_le_50pts": meta.risk_points <= 50,
        "risk_le_75pts": meta.risk_points <= 75,
        "risk_le_100pts": meta.risk_points <= 100,
        "early_by_1130": meta.signal_ny_min <= 690,
        "vwap_aligned": vwap_ok,
        "strong_5m_breakout": strong,
        "narrow_ib_le_0.80x_prior20": meta.ib_vs_prior20 <= 0.80,
        "normal_ib_0.80_to_1.25x_prior20": meta.ib_vs_prior20.between(0.80, 1.25),
    }
    rows=[]
    for name, mask in filters.items():
        for label, x in meta[mask.fillna(False)].assign(period=lambda d: d.year.map(period)).groupby("period", sort=False):
            rows.append({"filter": name, "period": label, **summary(x)})
    res=pd.DataFrame(rows)
    piv=res.pivot(index="filter",columns="period",values="avg_net_points").reset_index()
    count=res.pivot(index="filter",columns="period",values="trades").add_prefix("n_").reset_index()
    grid=piv.merge(count,on="filter")
    base=grid[grid["filter"].eq("baseline_all")].iloc[0]
    # Selection sees only the two pre-2022 periods, with minimum sample requirements.
    survivors=grid[(grid.Train > base.Train) & (grid.Inner_Validation > base.Inner_Validation) & (grid.n_Train >= 150) & (grid.n_Inner_Validation >= 75)].copy()
    survivors["selection_basis"]="better than baseline in Train + Inner_Validation only"
    res.to_csv(ART / "nq_phase3_filter_summary.csv",index=False)
    grid.to_csv(ART / "nq_phase3_filter_grid.csv",index=False)
    survivors.to_csv(ART / "nq_phase3_filter_survivors.csv",index=False)
    report=["# NQ IB — Phase 3 standalone causal filters", "", "The entry and exit rules are unchanged. No filter combinations were searched. Selection uses only 2010–2018 Train and 2019–2021 Inner Validation.", "", "## Mean net points per trade", "", grid.to_markdown(index=False), "", "## Pre-2022 survivors", "", survivors.to_markdown(index=False) if len(survivors) else "_None._", "", "Filters are known at signal time: risk uses the already-known stop distance; VWAP uses RTH data through the completed signal bar; candle quality uses the completed five-minute signal bar; IB width uses only prior 20 completed sessions."]
    (ART / "nq_phase3_filter_report.md").write_text("\n".join(report),encoding="utf-8")
    print(grid.to_string(index=False)); print("\nSURVIVORS\n",survivors.to_string(index=False))

if __name__ == "__main__": main()
