"""Performance metrics, charts, IS/OOS, bootstrap."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import FIGS, REPORTS, RESULTS


def summarize_trades(trades: pd.DataFrame, label: str = "") -> dict:
    if trades is None or trades.empty:
        return {
            "label": label,
            "n_trades": 0,
            "win_rate": np.nan,
            "avg_win": np.nan,
            "avg_loss": np.nan,
            "avg_r": np.nan,
            "expectancy_r": np.nan,
            "expectancy_usd": np.nan,
            "profit_factor": np.nan,
            "total_pnl_nq": 0.0,
            "max_dd_usd": 0.0,
            "max_dd_pct": 0.0,
            "longest_lose_streak": 0,
            "sharpe": np.nan,
            "sortino": np.nan,
            "pct_profitable_months": np.nan,
            "avg_duration_min": np.nan,
        }
    t = trades.copy()
    t["win"] = t["pnl_nq"] > 0
    wins = t.loc[t["win"], "pnl_nq"]
    losses = t.loc[~t["win"], "pnl_nq"]
    gp = wins.sum() if len(wins) else 0.0
    gl = -losses.sum() if len(losses) else 0.0
    pf = (gp / gl) if gl > 0 else np.nan

    t = t.sort_values("entry_ts")
    eq = t["pnl_nq"].cumsum()
    peak = eq.cummax()
    dd = eq - peak
    max_dd = float(dd.min()) if len(dd) else 0.0
    max_dd_pct = float((dd / peak.replace(0, np.nan)).min()) if peak.max() != 0 else 0.0

    # losing streak
    streak = longest = 0
    for w in t["win"].tolist():
        if not w:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0

    # daily pnl sharpe
    t["day"] = pd.to_datetime(t["entry_ts"], utc=True).dt.date
    daily = t.groupby("day")["pnl_nq"].sum()
    sharpe = sortino = np.nan
    if len(daily) > 2 and daily.std() > 0:
        sharpe = float(np.sqrt(252) * daily.mean() / daily.std())
        downside = daily[daily < 0]
        if len(downside) > 1 and downside.std() > 0:
            sortino = float(np.sqrt(252) * daily.mean() / downside.std())

    t["month"] = pd.to_datetime(t["entry_ts"], utc=True).dt.tz_localize(None).dt.to_period("M")
    monthly = t.groupby("month")["pnl_nq"].sum()
    pct_m = float((monthly > 0).mean()) if len(monthly) else np.nan

    dur = (
        pd.to_datetime(t["exit_ts"]) - pd.to_datetime(t["entry_ts"])
    ).dt.total_seconds() / 60.0

    return {
        "label": label,
        "n_trades": int(len(t)),
        "win_rate": float(t["win"].mean()),
        "avg_win": float(wins.mean()) if len(wins) else np.nan,
        "avg_loss": float(losses.mean()) if len(losses) else np.nan,
        "avg_r": float(t["r_mult"].mean()),
        "expectancy_r": float(t["r_mult"].mean()),
        "expectancy_usd": float(t["pnl_nq"].mean()),
        "profit_factor": float(pf) if pf == pf else np.nan,
        "total_pnl_nq": float(t["pnl_nq"].sum()),
        "max_dd_usd": max_dd,
        "max_dd_pct": max_dd_pct,
        "longest_lose_streak": int(longest),
        "sharpe": sharpe,
        "sortino": sortino,
        "pct_profitable_months": pct_m,
        "avg_duration_min": float(dur.mean()) if len(dur) else np.nan,
    }


def bootstrap_expectancy_ci(trades: pd.DataFrame, n: int = 2000, seed: int = 42) -> dict:
    if trades is None or trades.empty:
        return {"mean": np.nan, "lo": np.nan, "hi": np.nan}
    rng = np.random.default_rng(seed)
    x = trades["r_mult"].to_numpy(float)
    means = []
    for _ in range(n):
        sample = rng.choice(x, size=len(x), replace=True)
        means.append(sample.mean())
    return {
        "mean": float(np.mean(means)),
        "lo": float(np.percentile(means, 2.5)),
        "hi": float(np.percentile(means, 97.5)),
    }


def chronological_split(trades: pd.DataFrame, is_frac: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    if trades is None or trades.empty:
        return trades, trades
    t = trades.sort_values("entry_ts").reset_index(drop=True)
    cut = int(len(t) * is_frac)
    # Prefer time-based split on sessions
    sessions = sorted(t["session_date"].unique())
    cut_s = int(len(sessions) * is_frac)
    is_set = set(sessions[:cut_s])
    is_df = t[t["session_date"].isin(is_set)]
    oos_df = t[~t["session_date"].isin(is_set)]
    return is_df, oos_df


def walkforward_monthly(trades: pd.DataFrame) -> pd.DataFrame:
    if trades is None or trades.empty:
        return pd.DataFrame()
    t = trades.copy()
    t["month"] = (
        pd.to_datetime(t["entry_ts"], utc=True).dt.tz_localize(None).dt.to_period("M").astype(str)
    )
    rows = []
    for m, g in t.groupby("month"):
        rows.append(summarize_trades(g, label=m))
    return pd.DataFrame(rows)


def by_weekday_hour(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if trades is None or trades.empty:
        return pd.DataFrame(), pd.DataFrame()
    wd = (
        trades.groupby("weekday")
        .agg(n=("pnl_nq", "count"), expectancy_r=("r_mult", "mean"), pnl=("pnl_nq", "sum"))
        .reset_index()
    )
    hr = (
        trades.groupby("entry_hour")
        .agg(n=("pnl_nq", "count"), expectancy_r=("r_mult", "mean"), pnl=("pnl_nq", "sum"))
        .reset_index()
    )
    return wd, hr


def plot_equity(trades: pd.DataFrame, path: Path, title: str) -> None:
    if trades is None or trades.empty:
        return
    t = trades.sort_values("entry_ts")
    eq = t["pnl_nq"].cumsum()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(pd.to_datetime(t["entry_ts"]), eq, color="#1f4e79", lw=1.2)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity ($ / 1 NQ)")
    ax.axhline(0, color="gray", lw=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_drawdown(trades: pd.DataFrame, path: Path, title: str) -> None:
    if trades is None or trades.empty:
        return
    t = trades.sort_values("entry_ts")
    eq = t["pnl_nq"].cumsum()
    dd = eq - eq.cummax()
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.fill_between(pd.to_datetime(t["entry_ts"]), dd, 0, color="#8b0000", alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown ($)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_monthly_heatmap(trades: pd.DataFrame, path: Path, title: str) -> None:
    if trades is None or trades.empty:
        return
    t = trades.copy()
    ts = pd.to_datetime(t["entry_ts"], utc=True).dt.tz_localize(None)
    t["year"] = ts.dt.year
    t["month"] = ts.dt.month
    pivot = t.pivot_table(index="year", columns="month", values="pnl_nq", aggfunc="sum")
    fig, ax = plt.subplots(figsize=(11, max(3, 0.35 * len(pivot))))
    im = ax.imshow(pivot.fillna(0).to_numpy(), aspect="auto", cmap="RdYlGn")
    ax.set_xticks(range(12))
    ax.set_xticklabels(list(range(1, 13)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(list(pivot.index))
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")
    fig.colorbar(im, ax=ax, fraction=0.02)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def random_percentile(strategy_exp: float, random_runs: pd.DataFrame) -> float:
    if random_runs is None or random_runs.empty or not np.isfinite(strategy_exp):
        return float("nan")
    return float((random_runs["expectancy_r"] < strategy_exp).mean() * 100.0)


def ensure_dirs() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
