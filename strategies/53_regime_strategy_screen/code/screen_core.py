"""
Strategy 53 — regime-conditioned strategy family screen (core).

Frozen rules only. No optimization.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from common.splits import split_of

from constants import (
    CELLS,
    COST_RT,
    HOLD_MINUTES,
    MIN_N_SPLIT,
    PATH_MFE15_MIN,
    RESULTS,
    S52_RESULTS,
    SHUFFLE_SEED,
)


def load_panel() -> pd.DataFrame:
    states = pd.read_parquet(S52_RESULTS / "market_states.parquet")
    feats = pd.read_parquet(
        S52_RESULTS / "market_state_features.parquet",
        columns=["ts", "open", "high", "low", "close", "atr_30"],
    )
    if len(states) != len(feats):
        raise RuntimeError("Strategy 52 states/features length mismatch")
    panel = states.copy()
    for c in ("open", "high", "low", "close", "atr_30"):
        panel[c] = feats[c].to_numpy(np.float64)
    panel = (
        panel.loc[panel["census_eligible"]]
        .sort_values(["session_date", "ny_min"])
        .reset_index(drop=True)
    )
    g = panel.groupby("segment_id", sort=False)
    panel["hh60"] = g["high"].transform(lambda s: s.rolling(60, min_periods=60).max())
    panel["ll60"] = g["low"].transform(lambda s: s.rolling(60, min_periods=60).min())
    panel["hh20_prev"] = g["high"].transform(
        lambda s: s.rolling(20, min_periods=20).max().shift(1)
    )
    panel["ll20_prev"] = g["low"].transform(
        lambda s: s.rolling(20, min_periods=20).min().shift(1)
    )
    panel["close_lag5"] = g["close"].transform(lambda s: s.shift(5))
    panel["split"] = [split_of(int(y)) for y in panel["session_year"].to_numpy()]
    return panel


def horizon_valid_mask(panel: pd.DataFrame, h: int) -> np.ndarray:
    """True at t if bars t+1..t+h exist, same session/segment, ny advances by h."""
    n = len(panel)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    ok = np.zeros(n, dtype=bool)
    if h <= 0:
        return ok
    # entry needs t+1; full horizon uses t+h
    idx = np.arange(0, n - h, dtype=np.int64)
    t_h = idx + h
    ok[idx] = (
        (session[t_h] == session[idx])
        & (seg[t_h] == seg[idx])
        & (ny[t_h] == ny[idx] + h)
    )
    return ok


def generate_signals(panel: pd.DataFrame) -> pd.DataFrame:
    open_ = panel["open"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    atr = panel["atr_30"].to_numpy(np.float64)
    hh60 = panel["hh60"].to_numpy(np.float64)
    ll60 = panel["ll60"].to_numpy(np.float64)
    hh20p = panel["hh20_prev"].to_numpy(np.float64)
    ll20p = panel["ll20_prev"].to_numpy(np.float64)
    c5 = panel["close_lag5"].to_numpy(np.float64)
    valid = horizon_valid_mask(panel, HOLD_MINUTES)
    split = panel["split"].to_numpy(dtype=object)
    session_date = panel["session_date"].to_numpy()
    session_year = panel["session_year"].to_numpy(np.int16)

    frames = []
    for meta in CELLS:
        flag = panel[meta["state_flag"]].to_numpy(bool) & valid
        side = np.zeros(len(panel), dtype=np.int8)
        if meta["cell_id"] == "A":
            side = np.where(close > open_, 1, np.where(close < open_, -1, 0)).astype(np.int8)
        elif meta["cell_id"] == "B":
            mid = 0.5 * (hh60 + ll60)
            disp = close - mid
            ok = (
                np.isfinite(hh60)
                & np.isfinite(ll60)
                & np.isfinite(atr)
                & (atr > 0)
                & (np.abs(disp) >= 0.5 * atr)
            )
            side = np.where(ok & (disp > 0), -1, np.where(ok & (disp < 0), 1, 0)).astype(
                np.int8
            )
        elif meta["cell_id"] == "C":
            ok = np.isfinite(hh20p) & np.isfinite(ll20p)
            side = np.where(
                ok & (close > hh20p),
                1,
                np.where(ok & (close < ll20p), -1, 0),
            ).astype(np.int8)
        elif meta["cell_id"] == "D":
            move5 = close - c5
            ok = np.isfinite(c5) & np.isfinite(atr) & (atr > 0) & np.isfinite(close)
            side = np.where(
                ok & (move5 < -1.0 * atr),
                1,
                np.where(ok & (move5 > 1.0 * atr), -1, 0),
            ).astype(np.int8)

        mask = flag & (side != 0)
        idx = np.flatnonzero(mask)
        if len(idx) == 0:
            continue
        frames.append(
            pd.DataFrame(
                {
                    "cell_id": meta["cell_id"],
                    "cell_name": meta["name"],
                    "state_label": meta["state_label"],
                    "family": meta["family"],
                    "signal_idx": idx,
                    "side": side[idx].astype(np.int8),
                    "split": split[idx],
                    "session_date": session_date[idx],
                    "session_year": session_year[idx],
                }
            )
        )
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _forward_roll_max(arr: np.ndarray, w: int) -> np.ndarray:
    rev = arr[::-1]
    out = pd.Series(rev).rolling(w, min_periods=1).max().to_numpy()[::-1]
    return out.astype(np.float64)


def _forward_roll_min(arr: np.ndarray, w: int) -> np.ndarray:
    rev = arr[::-1]
    out = pd.Series(rev).rolling(w, min_periods=1).min().to_numpy()[::-1]
    return out.astype(np.float64)


def simulate_from_signals(panel: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return pd.DataFrame()
    open_ = panel["open"].to_numpy(np.float64)
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    n = len(panel)

    hi5 = _forward_roll_max(high, 5)
    lo5 = _forward_roll_min(low, 5)
    hi15 = _forward_roll_max(high, 15)
    lo15 = _forward_roll_min(low, 15)

    t = signals["signal_idx"].to_numpy(np.int64)
    side = signals["side"].to_numpy(np.int8)
    entry_i = t + 1
    exit_i = t + HOLD_MINUTES
    ok = (exit_i < n) & (entry_i < n)
    t = t[ok]
    side = side[ok]
    entry_i = entry_i[ok]
    exit_i = exit_i[ok]
    sig = signals.loc[ok].reset_index(drop=True)

    entry = open_[entry_i]
    exit_px = close[exit_i]
    side_f = side.astype(np.float64)
    gross = side_f * (exit_px - entry)
    net = gross - COST_RT

    # windows from entry bar: 5 bars => t+1..t+5; 15 bars => t+1..t+15
    mfe5 = np.where(side > 0, hi5[entry_i] - entry, entry - lo5[entry_i])
    mae5 = np.where(side > 0, entry - lo5[entry_i], hi5[entry_i] - entry)
    mfe15 = np.where(side > 0, hi15[entry_i] - entry, entry - lo15[entry_i])
    mae15 = np.where(side > 0, entry - lo15[entry_i], hi15[entry_i] - entry)

    out = sig.copy()
    out["entry_idx"] = entry_i
    out["exit_idx"] = exit_i
    out["entry_price"] = entry
    out["exit_price"] = exit_px
    out["hold_minutes"] = HOLD_MINUTES
    out["gross_pts"] = gross
    out["net_pts"] = net
    out["mfe_5"] = mfe5
    out["mae_5"] = mae5
    out["mfe_15"] = mfe15
    out["mae_15"] = mae15
    out["winner"] = net > 0
    return out


def _metrics_block(g: pd.DataFrame) -> dict:
    n = len(g)
    if n == 0:
        return {
            "n_trades": 0,
            "mean_gross": np.nan,
            "mean_net": np.nan,
            "median_net": np.nan,
            "sum_net": np.nan,
            "win_rate": np.nan,
            "avg_winner": np.nan,
            "avg_loser": np.nan,
            "payoff_ratio": np.nan,
            "profit_factor": np.nan,
            "median_mfe_5": np.nan,
            "median_mfe_15": np.nan,
            "median_mae_5": np.nan,
            "median_mae_15": np.nan,
            "n_sessions": 0,
            "signals_per_session": np.nan,
        }
    net = g["net_pts"].to_numpy(float)
    gross = g["gross_pts"].to_numpy(float)
    wins = net[net > 0]
    losses = net[net <= 0]
    sum_win = float(wins.sum()) if len(wins) else 0.0
    sum_loss = float((-losses).sum()) if len(losses) else 0.0
    avg_w = float(wins.mean()) if len(wins) else np.nan
    avg_l = float(losses.mean()) if len(losses) else np.nan
    n_sess = int(g["session_date"].nunique())
    return {
        "n_trades": n,
        "mean_gross": float(gross.mean()),
        "mean_net": float(net.mean()),
        "median_net": float(np.median(net)),
        "sum_net": float(net.sum()),
        "win_rate": float((net > 0).mean()),
        "avg_winner": avg_w,
        "avg_loser": avg_l,
        "payoff_ratio": (
            avg_w / abs(avg_l)
            if np.isfinite(avg_w) and np.isfinite(avg_l) and avg_l != 0
            else np.nan
        ),
        "profit_factor": (sum_win / sum_loss) if sum_loss > 0 else np.nan,
        "median_mfe_5": float(np.nanmedian(g["mfe_5"])),
        "median_mfe_15": float(np.nanmedian(g["mfe_15"])),
        "median_mae_5": float(np.nanmedian(g["mae_5"])),
        "median_mae_15": float(np.nanmedian(g["mae_15"])),
        "n_sessions": n_sess,
        "signals_per_session": float(n / n_sess) if n_sess else np.nan,
    }


def summarize_splits(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    years_span = {"IS": 12.0, "Validation": 3.0, "OOS": 2.0, "ALL": 17.0}
    for cell_id in trades["cell_id"].unique():
        tc = trades.loc[trades["cell_id"] == cell_id]
        meta = tc.iloc[0]
        for split in ("IS", "Validation", "OOS", "ALL"):
            g = tc if split == "ALL" else tc.loc[tc["split"] == split]
            block = _metrics_block(g)
            yrs = years_span[split]
            rows.append(
                {
                    "cell_id": cell_id,
                    "cell_name": meta["cell_name"],
                    "state_label": meta["state_label"],
                    "family": meta["family"],
                    "split": split,
                    "signals_per_year": block["n_trades"] / yrs if yrs else np.nan,
                    **block,
                }
            )
    return pd.DataFrame(rows)


def summarize_years(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (cell_id, year), g in trades.groupby(["cell_id", "session_year"], sort=True):
        meta = g.iloc[0]
        rows.append(
            {
                "cell_id": cell_id,
                "cell_name": meta["cell_name"],
                "session_year": int(year),
                "n_trades": len(g),
                "mean_net": float(g["net_pts"].mean()),
                "sum_net": float(g["net_pts"].sum()),
                "win_rate": float((g["net_pts"] > 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def shuffle_side_baseline(panel: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SHUFFLE_SEED)
    rows = []
    for cell_id, g in trades.groupby("cell_id", sort=True):
        sides = g["side"].to_numpy().copy()
        rng.shuffle(sides)
        sig = g[
            [
                "signal_idx",
                "cell_id",
                "cell_name",
                "state_label",
                "family",
                "split",
                "session_date",
                "session_year",
            ]
        ].copy()
        sig["side"] = sides
        # Skip MFE loop: only need net — lightweight path
        open_ = panel["open"].to_numpy(np.float64)
        close = panel["close"].to_numpy(np.float64)
        t = sig["signal_idx"].to_numpy(np.int64)
        entry = open_[t + 1]
        exit_px = close[t + HOLD_MINUTES]
        gross = sides.astype(np.float64) * (exit_px - entry)
        net = gross - COST_RT
        tmp = sig.copy()
        tmp["gross_pts"] = gross
        tmp["net_pts"] = net
        for split in ("IS", "Validation", "OOS", "ALL"):
            gg = tmp if split == "ALL" else tmp.loc[tmp["split"] == split]
            rows.append(
                {
                    "baseline": "shuffle_side",
                    "cell_id": cell_id,
                    "split": split,
                    "n_trades": len(gg),
                    "mean_net": float(gg["net_pts"].mean()) if len(gg) else np.nan,
                    "mean_gross": float(gg["gross_pts"].mean()) if len(gg) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def all_bars_baseline(panel: pd.DataFrame) -> pd.DataFrame:
    open_ = panel["open"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    split = panel["split"].to_numpy(dtype=object)
    valid = horizon_valid_mask(panel, HOLD_MINUTES)
    n = len(panel)
    entry = open_[1:]
    # align: for signal t, entry open[t+1], exit close[t+15]
    long_gross = np.full(n, np.nan)
    idx = np.flatnonzero(valid)
    long_gross[idx] = close[idx + HOLD_MINUTES] - open_[idx + 1]
    short_gross = -long_gross

    rows = []
    for meta in CELLS:
        flag = panel[meta["state_flag"]].to_numpy(bool) & valid
        for side_name, gross_arr in (
            ("all_bars_long", long_gross),
            ("all_bars_short", short_gross),
        ):
            for sp in ("IS", "Validation", "OOS", "ALL"):
                if sp == "ALL":
                    m = flag
                else:
                    m = flag & (split == sp)
                g = gross_arr[m]
                g = g[np.isfinite(g)]
                net = g - COST_RT
                rows.append(
                    {
                        "baseline": side_name,
                        "cell_id": meta["cell_id"],
                        "state_label": meta["state_label"],
                        "split": sp,
                        "n_trades": int(len(net)),
                        "mean_net": float(net.mean()) if len(net) else np.nan,
                        "mean_gross": float(g.mean()) if len(g) else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def classify_cells(summary: pd.DataFrame) -> dict:
    verdicts = {}
    for cell_id in summary["cell_id"].unique():
        s = summary.loc[summary["cell_id"] == cell_id]
        meta = s.iloc[0]
        by = {r.split: r for r in s.itertuples(index=False)}
        detail = {}
        passes = []
        for sp in ("IS", "Validation", "OOS"):
            r = by.get(sp)
            if r is None:
                detail[sp] = {"pass": False, "reason": "missing"}
                passes.append(False)
                continue
            ok = (
                int(r.n_trades) >= MIN_N_SPLIT
                and np.isfinite(r.mean_net)
                and float(r.mean_net) > 0
            )
            detail[sp] = {
                "n_trades": int(r.n_trades),
                "mean_net": float(r.mean_net),
                "median_mfe_15": float(r.median_mfe_15),
                "pass": ok,
            }
            passes.append(ok)

        is_net = float(by["IS"].mean_net) if "IS" in by else np.nan
        val_net = float(by["Validation"].mean_net) if "Validation" in by else np.nan
        is_mfe = float(by["IS"].median_mfe_15) if "IS" in by else np.nan

        if all(passes):
            cls = "PROMISING"
        elif (
            np.isfinite(is_net)
            and is_net <= 0
            and np.isfinite(is_mfe)
            and is_mfe >= PATH_MFE15_MIN
            and is_mfe >= 2.0 * abs(is_net)
        ):
            cls = "PATH-ONLY"
        elif np.isfinite(is_net) and np.isfinite(val_net) and is_net <= 0 and val_net <= 0:
            cls = "REJECTED"
        else:
            cls = "INCONCLUSIVE"

        verdicts[cell_id] = {
            "cell_id": cell_id,
            "cell_name": meta["cell_name"],
            "state_label": meta["state_label"],
            "family": meta["family"],
            "classification": cls,
            "detail": detail,
        }
    return {
        "cells": verdicts,
        "cost_rt": COST_RT,
        "hold_minutes": HOLD_MINUTES,
        "min_n_split": MIN_N_SPLIT,
        "note": "Cells classified independently; no ranking.",
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading Strategy 52 panel…", flush=True)
    panel = load_panel()
    print(f"panel bars={len(panel):,}", flush=True)

    print("Generating signals…", flush=True)
    signals = generate_signals(panel)
    print(
        f"signals={len(signals):,} by_cell={signals.groupby('cell_id').size().to_dict()}",
        flush=True,
    )

    print("Simulating trades (incl. MFE/MAE)…", flush=True)
    trades = simulate_from_signals(panel, signals)
    trades.to_parquet(RESULTS / "trades.parquet", index=False)
    print(f"trades={len(trades):,}", flush=True)

    summary = summarize_splits(trades)
    summary.to_csv(RESULTS / "summary_by_split.csv", index=False)
    summarize_years(trades).to_csv(RESULTS / "summary_by_year.csv", index=False)

    path_rows = []
    for cell_id, g in trades.groupby("cell_id"):
        for split in ("IS", "Validation", "OOS", "ALL"):
            gg = g if split == "ALL" else g.loc[g["split"] == split]
            path_rows.append(
                {
                    "cell_id": cell_id,
                    "split": split,
                    "median_mfe_5": float(np.nanmedian(gg["mfe_5"])) if len(gg) else np.nan,
                    "median_mfe_15": float(np.nanmedian(gg["mfe_15"])) if len(gg) else np.nan,
                    "median_mae_5": float(np.nanmedian(gg["mae_5"])) if len(gg) else np.nan,
                    "median_mae_15": float(np.nanmedian(gg["mae_15"])) if len(gg) else np.nan,
                    "n": len(gg),
                }
            )
    pd.DataFrame(path_rows).to_csv(RESULTS / "path_metrics.csv", index=False)

    print("Baselines…", flush=True)
    shuffle = shuffle_side_baseline(panel, trades)
    allbars = all_bars_baseline(panel)
    pd.concat([shuffle, allbars], ignore_index=True).to_csv(
        RESULTS / "baselines.csv", index=False
    )

    verdict = classify_cells(summary)
    (RESULTS / "verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    for cid, v in verdict["cells"].items():
        print(f"  {cid} {v['classification']}", flush=True)


if __name__ == "__main__":
    main()
