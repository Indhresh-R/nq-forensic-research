"""
Engine sanity benchmarks — NOT a research strategy (not Strategy 23).

Purpose: verify the local NQ pipeline computes P&L / signals correctly against
known identities and an external cash-index reference.

1) Buy-and-hold: engine return MUST equal last_close - first_close (gross).
2) SMA 50/200 golden/death cross: list every causal crossover on Globex daily
   bars; optionally compare dates to Yahoo ^NDX daily SMAs.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import art, load_nq
from common.splits import split_of

warnings.filterwarnings("ignore", category=FutureWarning)

# Pre-specified costs (same ballparks as research_framework/execution_assumptions.md)
COST_SCENARIOS = {"gross": 0.0, "tight": 0.50, "mid": 1.00, "wide": 2.00}
SMA_FAST = 50
SMA_SLOW = 200
MIN_BARS_GLOBEX_DAY = 60


def build_globex_daily(df: pd.DataFrame) -> pd.DataFrame:
    """One OHLC row per session_date (Globex day starting 18:00 ET)."""
    rows: list[dict[str, Any]] = []
    for sd, g in df.groupby("session_date", sort=True):
        if len(g) < MIN_BARS_GLOBEX_DAY:
            continue
        g = g.sort_values("ts")
        o = float(g.iloc[0]["open"])
        h = float(g["high"].max())
        l = float(g["low"].min())
        c = float(g.iloc[-1]["close"])
        ts0 = g.iloc[0]["ts"]
        ts1 = g.iloc[-1]["ts"]
        rows.append(
            {
                "session_date": sd,
                "year": int(pd.Timestamp(sd).year),
                "day_open": o,
                "day_high": h,
                "day_low": l,
                "day_close": c,
                "day_range": h - l,
                "ts_open": ts0,
                "ts_close": ts1,
                "n_bars": int(len(g)),
            }
        )
    daily = pd.DataFrame(rows).sort_values("session_date").reset_index(drop=True)
    daily["split"] = daily["year"].map(split_of)
    return daily


def buy_and_hold(daily: pd.DataFrame, cost_rt: float) -> dict[str, Any]:
    """Long from first daily close to last daily close (1 contract, points)."""
    if len(daily) < 2:
        raise ValueError("need >= 2 daily bars for buy-and-hold")
    entry = float(daily.iloc[0]["day_close"])
    exit_ = float(daily.iloc[-1]["day_close"])
    entry_d = daily.iloc[0]["session_date"]
    exit_d = daily.iloc[-1]["session_date"]
    gross_pts = exit_ - entry
    net_pts = gross_pts - cost_rt
    # Independent identity: must match hand calculation
    hand_pts = float(daily["day_close"].iloc[-1] - daily["day_close"].iloc[0])
    return {
        "strategy": "buy_and_hold",
        "cost_rt": cost_rt,
        "entry_date": str(entry_d),
        "exit_date": str(exit_d),
        "entry_px": entry,
        "exit_px": exit_,
        "gross_pts": gross_pts,
        "net_pts": net_pts,
        "hand_pts": hand_pts,
        "identity_ok": bool(np.isclose(gross_pts, hand_pts, rtol=0.0, atol=1e-9)),
        "return_pct_gross": 100.0 * gross_pts / entry if entry else np.nan,
        "n_days": int(len(daily)),
    }


def sma_crossover_trades(
    daily: pd.DataFrame, cost_rt: float
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Causal SMA50/SMA200 on prior closes only.
    Signal on day t uses SMA computed from closes through t (inclusive of day t close).
    Trade fills at NEXT day open (next-bar execution — matches causal research rule).
    Long when fast > slow; flat when fast <= slow (long-only benchmark).
    """
    d = daily.copy()
    d["sma_fast"] = d["day_close"].rolling(SMA_FAST, min_periods=SMA_FAST).mean()
    d["sma_slow"] = d["day_close"].rolling(SMA_SLOW, min_periods=SMA_SLOW).mean()
    d["regime"] = np.where(
        d["sma_fast"].isna() | d["sma_slow"].isna(),
        np.nan,
        np.where(d["sma_fast"] > d["sma_slow"], 1.0, 0.0),
    )
    # Cross detected on close of day t; enter/exit next session open
    d["prev_regime"] = d["regime"].shift(1)
    d["cross"] = np.where(
        d["regime"].isna() | d["prev_regime"].isna(),
        "",
        np.where(
            (d["prev_regime"] == 0) & (d["regime"] == 1),
            "golden",
            np.where((d["prev_regime"] == 1) & (d["regime"] == 0), "death", ""),
        ),
    )

    # Next-bar open fill
    d["next_open"] = d["day_open"].shift(-1)
    d["next_date"] = d["session_date"].shift(-1)

    crosses = d[d["cross"] != ""].copy()
    trade_rows: list[dict[str, Any]] = []
    position = 0
    entry_px = np.nan
    entry_date = None
    entry_signal_date = None

    for _, row in d.iterrows():
        if row["cross"] == "golden" and position == 0 and pd.notna(row["next_open"]):
            position = 1
            entry_px = float(row["next_open"])
            entry_date = row["next_date"]
            entry_signal_date = row["session_date"]
        elif row["cross"] == "death" and position == 1 and pd.notna(row["next_open"]):
            exit_px = float(row["next_open"])
            exit_date = row["next_date"]
            gross = exit_px - entry_px
            trade_rows.append(
                {
                    "side": "LONG",
                    "signal_entry": str(entry_signal_date),
                    "signal_exit": str(row["session_date"]),
                    "entry_date": str(entry_date),
                    "exit_date": str(exit_date),
                    "entry_px": entry_px,
                    "exit_px": exit_px,
                    "gross_pts": gross,
                    "net_pts": gross - cost_rt,
                    "hold_days": (
                        pd.Timestamp(exit_date) - pd.Timestamp(entry_date)
                    ).days
                    if entry_date is not None
                    else None,
                    "sma_fast_at_signal": float(row["sma_fast"]),
                    "sma_slow_at_signal": float(row["sma_slow"]),
                }
            )
            position = 0
            entry_px = np.nan
            entry_date = None
            entry_signal_date = None

    # Force flat at last available next_open if still long after final death never fills
    if position == 1 and len(d) >= 2:
        last = d.iloc[-1]
        exit_px = float(last["day_close"])
        exit_date = last["session_date"]
        gross = exit_px - entry_px
        trade_rows.append(
            {
                "side": "LONG",
                "signal_entry": str(entry_signal_date),
                "signal_exit": "EOD_FORCE_FLAT",
                "entry_date": str(entry_date),
                "exit_date": str(exit_date),
                "entry_px": entry_px,
                "exit_px": exit_px,
                "gross_pts": gross,
                "net_pts": gross - cost_rt,
                "hold_days": (
                    pd.Timestamp(exit_date) - pd.Timestamp(entry_date)
                ).days
                if entry_date is not None
                else None,
                "sma_fast_at_signal": float(last["sma_fast"])
                if pd.notna(last["sma_fast"])
                else np.nan,
                "sma_slow_at_signal": float(last["sma_slow"])
                if pd.notna(last["sma_slow"])
                else np.nan,
            }
        )

    trades = pd.DataFrame(trade_rows)
    cross_log = crosses[
        [
            "session_date",
            "year",
            "split",
            "day_close",
            "sma_fast",
            "sma_slow",
            "cross",
            "next_date",
            "next_open",
        ]
    ].copy()

    if len(trades) == 0:
        summary: dict[str, Any] = {
            "strategy": "sma_50_200_long_only",
            "cost_rt": cost_rt,
            "n_trades": 0,
            "n_golden": int((cross_log["cross"] == "golden").sum()),
            "n_death": int((cross_log["cross"] == "death").sum()),
            "gross_pts": 0.0,
            "net_pts": 0.0,
            "win_rate": np.nan,
            "avg_trade_gross": np.nan,
        }
    else:
        g = trades["gross_pts"].to_numpy(float)
        summary = {
            "strategy": "sma_50_200_long_only",
            "cost_rt": cost_rt,
            "n_trades": int(len(trades)),
            "n_golden": int((cross_log["cross"] == "golden").sum()),
            "n_death": int((cross_log["cross"] == "death").sum()),
            "gross_pts": float(np.sum(g)),
            "net_pts": float(np.sum(trades["net_pts"].to_numpy(float))),
            "win_rate": float(np.mean(g > 0)),
            "avg_trade_gross": float(np.mean(g)),
        }

    # Independent SMA recompute check on last ready row
    ready = d.dropna(subset=["sma_fast", "sma_slow"])
    if len(ready) >= 1:
        i = ready.index[-1]
        closes = d.loc[:i, "day_close"].to_numpy(float)
        hand_fast = float(np.mean(closes[-SMA_FAST:]))
        hand_slow = float(np.mean(closes[-SMA_SLOW:]))
        summary["sma_identity_ok"] = bool(
            np.isclose(hand_fast, float(ready.iloc[-1]["sma_fast"]), atol=1e-6)
            and np.isclose(hand_slow, float(ready.iloc[-1]["sma_slow"]), atol=1e-6)
        )
        summary["hand_sma_fast_last"] = hand_fast
        summary["hand_sma_slow_last"] = hand_slow
        summary["engine_sma_fast_last"] = float(ready.iloc[-1]["sma_fast"])
        summary["engine_sma_slow_last"] = float(ready.iloc[-1]["sma_slow"])
    else:
        summary["sma_identity_ok"] = False

    return trades, cross_log, d, summary


def fetch_ndx_crosses(start: str, end: str) -> pd.DataFrame | None:
    """External cash Nasdaq-100 reference for approximate cross-date comparison."""
    try:
        import yfinance as yf
    except ImportError:
        return None
    # ^NDX = Nasdaq-100 cash index (not futures; rolls/basis differ)
    raw = yf.download("^NDX", start=start, end=end, progress=False, auto_adjust=True)
    if raw is None or len(raw) == 0:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
    else:
        close = raw["Close"]
    ndx = pd.DataFrame({"date": pd.to_datetime(close.index).tz_localize(None), "close": close.to_numpy(float)})
    ndx = ndx.dropna().sort_values("date").reset_index(drop=True)
    ndx["sma_fast"] = ndx["close"].rolling(SMA_FAST, min_periods=SMA_FAST).mean()
    ndx["sma_slow"] = ndx["close"].rolling(SMA_SLOW, min_periods=SMA_SLOW).mean()
    ndx["regime"] = np.where(
        ndx["sma_fast"].isna() | ndx["sma_slow"].isna(),
        np.nan,
        np.where(ndx["sma_fast"] > ndx["sma_slow"], 1.0, 0.0),
    )
    ndx["prev_regime"] = ndx["regime"].shift(1)
    ndx["cross"] = np.where(
        ndx["regime"].isna() | ndx["prev_regime"].isna(),
        "",
        np.where(
            (ndx["prev_regime"] == 0) & (ndx["regime"] == 1),
            "golden",
            np.where((ndx["prev_regime"] == 1) & (ndx["regime"] == 0), "death", ""),
        ),
    )
    return ndx[ndx["cross"] != ""][["date", "close", "sma_fast", "sma_slow", "cross"]].reset_index(drop=True)


def match_crosses(nq_cross: pd.DataFrame, ndx_cross: pd.DataFrame, tol_days: int = 10) -> pd.DataFrame:
    """Nearest same-type NDX cross within tol_days of each NQ Globex cross."""
    rows: list[dict[str, Any]] = []
    for _, r in nq_cross.iterrows():
        d0 = pd.Timestamp(r["session_date"])
        same = ndx_cross[ndx_cross["cross"] == r["cross"]].copy()
        if len(same) == 0:
            rows.append(
                {
                    "nq_date": str(r["session_date"]),
                    "nq_cross": r["cross"],
                    "ndx_date": None,
                    "delta_days": None,
                    "matched": False,
                }
            )
            continue
        same["delta"] = (same["date"] - d0).dt.days.abs()
        best = same.loc[same["delta"].idxmin()]
        ok = int(best["delta"]) <= tol_days
        rows.append(
            {
                "nq_date": str(r["session_date"]),
                "nq_cross": r["cross"],
                "ndx_date": str(best["date"].date()),
                "delta_days": int(best["delta"]),
                "matched": bool(ok),
            }
        )
    return pd.DataFrame(rows)


def yearly_bh(daily: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for y, g in daily.groupby("year", sort=True):
        if len(g) < 2:
            continue
        e0 = float(g.iloc[0]["day_close"])
        e1 = float(g.iloc[-1]["day_close"])
        pts = e1 - e0
        rows.append(
            {
                "year": int(y),
                "split": split_of(int(y)),
                "start": str(g.iloc[0]["session_date"]),
                "end": str(g.iloc[-1]["session_date"]),
                "start_px": e0,
                "end_px": e1,
                "gross_pts": pts,
                "return_pct": 100.0 * pts / e0 if e0 else np.nan,
                "hand_pts": float(g["day_close"].iloc[-1] - g["day_close"].iloc[0]),
            }
        )
    out = pd.DataFrame(rows)
    out["identity_ok"] = np.isclose(out["gross_pts"], out["hand_pts"], atol=1e-9)
    return out


def pct(x: Any) -> str:
    return f"{x:.2f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pts(x: Any) -> str:
    return f"{x:+.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def write_report(
    bh: dict[str, Any],
    bh_yearly: pd.DataFrame,
    sma_sum: dict[str, Any],
    cross_log: pd.DataFrame,
    trades: pd.DataFrame,
    match: pd.DataFrame | None,
    daily: pd.DataFrame,
) -> str:
    lines: list[str] = []
    lines.append("# Engine sanity benchmark — NQ continuous")
    lines.append("")
    lines.append("**Not a trading hypothesis.** Verifies P&L / SMA math against identities + external ^NDX.")
    lines.append("")
    lines.append(f"- Globex days: **{len(daily)}** ({daily.iloc[0]['session_date']} → {daily.iloc[-1]['session_date']})")
    lines.append(f"- Daily close range: **{daily.iloc[0]['day_close']:.2f}** → **{daily.iloc[-1]['day_close']:.2f}**")
    lines.append("")
    lines.append("## 1. Buy-and-hold (engine identity)")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|------|-------|")
    lines.append(f"| Entry (first close) | {bh['entry_date']} @ {bh['entry_px']:.2f} |")
    lines.append(f"| Exit (last close) | {bh['exit_date']} @ {bh['exit_px']:.2f} |")
    lines.append(f"| Engine gross pts | {pts(bh['gross_pts'])} |")
    lines.append(f"| Hand calc (last−first) | {pts(bh['hand_pts'])} |")
    lines.append(f"| Identity match | **{'PASS' if bh['identity_ok'] else 'FAIL'}** |")
    lines.append(f"| Gross return | {pct(bh['return_pct_gross'])} |")
    lines.append(f"| Net mid cost (−1.0 pt RT) | {pts(bh['gross_pts'] - 1.0)} |")
    lines.append("")
    lines.append("### Yearly buy-and-hold (must identity-match)")
    lines.append("")
    lines.append("| Year | Split | Start→End | Pts | Ret% | ID |")
    lines.append("|------|-------|-----------|-----|------|----|")
    for _, r in bh_yearly.iterrows():
        lines.append(
            f"| {int(r['year'])} | {r['split']} | {r['start']}→{r['end']} | "
            f"{pts(r['gross_pts'])} | {pct(r['return_pct'])} | "
            f"{'PASS' if r['identity_ok'] else 'FAIL'} |"
        )
    lines.append("")
    n_fail = int((~bh_yearly["identity_ok"]).sum())
    lines.append(f"Yearly identity failures: **{n_fail}**")
    lines.append("")
    lines.append("## 2. SMA 50/200 long-only (causal next-open fill)")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|------|-------|")
    lines.append(f"| Trades | {sma_sum['n_trades']} |")
    lines.append(f"| Golden / death crosses | {sma_sum['n_golden']} / {sma_sum['n_death']} |")
    lines.append(f"| Sum gross pts | {pts(sma_sum['gross_pts'])} |")
    lines.append(f"| Sum net pts (mid 1.0) | {pts(sma_sum.get('net_pts_mid', sma_sum['net_pts']))} |")
    wr = sma_sum["win_rate"]
    lines.append(
        f"| Win rate | {pct(100.0 * wr) if isinstance(wr, (int, float)) and np.isfinite(wr) else '—'} |"
    )
    lines.append(f"| SMA hand recompute | **{'PASS' if sma_sum.get('sma_identity_ok') else 'FAIL'}** |")
    lines.append("")
    lines.append("### Crossover log (NQ Globex daily)")
    lines.append("")
    lines.append("| Signal date | Type | Close | SMA50 | SMA200 | Fill date | Fill open |")
    lines.append("|-------------|------|-------|-------|--------|-----------|-----------|")
    for _, r in cross_log.iterrows():
        no = f"{r['next_open']:.2f}" if pd.notna(r["next_open"]) else "—"
        nd = str(r["next_date"]) if pd.notna(r["next_date"]) else "—"
        lines.append(
            f"| {r['session_date']} | {r['cross']} | {r['day_close']:.2f} | "
            f"{r['sma_fast']:.2f} | {r['sma_slow']:.2f} | {nd} | {no} |"
        )
    lines.append("")
    if match is not None and len(match):
        lines.append("### External check vs Yahoo ^NDX (cash index)")
        lines.append("")
        lines.append(
            "Futures continuous ≠ cash NDX (rolls/basis). Expect **near** dates, not identical prices."
        )
        lines.append("")
        lines.append("| NQ Globex | Type | Nearest ^NDX | Δ days | ≤10d? |")
        lines.append("|-----------|------|--------------|--------|-------|")
        for _, r in match.iterrows():
            lines.append(
                f"| {r['nq_date']} | {r['nq_cross']} | {r['ndx_date'] or '—'} | "
                f"{r['delta_days'] if r['delta_days'] is not None else '—'} | "
                f"{'Y' if r['matched'] else 'N'} |"
            )
        hit = float(match["matched"].mean()) if len(match) else np.nan
        lines.append("")
        lines.append(f"Match rate within 10 calendar days: **{pct(100 * hit)}**")
        lines.append("")
    lines.append("### Trades")
    lines.append("")
    if len(trades) == 0:
        lines.append("_No completed trades._")
    else:
        lines.append("| Entry | Exit | Entry px | Exit px | Gross | Net mid |")
        lines.append("|-------|------|----------|---------|-------|---------|")
        for _, r in trades.iterrows():
            lines.append(
                f"| {r['entry_date']} | {r['exit_date']} | {r['entry_px']:.2f} | "
                f"{r['exit_px']:.2f} | {pts(r['gross_pts'])} | {pts(r['gross_pts'] - 1.0)} |"
            )
    lines.append("")
    lines.append("## How to use this as a reality check")
    lines.append("")
    lines.append("1. **Buy-and-hold PASS** → price load + subtract P&L path is correct.")
    lines.append("2. **SMA hand recompute PASS** → rolling math is correct.")
    lines.append("3. **Cross dates ≈ ^NDX** → signal calendar is in the right ballpark vs public data.")
    lines.append("4. If (1) or (2) FAIL, fix the engine before trusting any strategy dossier.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    print("=== Engine sanity: buy-and-hold + SMA 50/200 ===", flush=True)
    df = load_nq()
    daily = build_globex_daily(df)
    daily_path = art("nq_engine_sanity_daily.parquet")
    daily.to_parquet(daily_path, index=False)
    print(f"Globex days: {len(daily)} -> {daily_path}", flush=True)

    bh = buy_and_hold(daily, cost_rt=0.0)
    bh_yearly = yearly_bh(daily)
    print(
        f"BH gross={bh['gross_pts']:+.2f} hand={bh['hand_pts']:+.2f} "
        f"identity={'PASS' if bh['identity_ok'] else 'FAIL'}",
        flush=True,
    )

    trades, cross_log, daily_sma, sma_sum = sma_crossover_trades(daily, cost_rt=1.0)
    sma_sum["net_pts_mid"] = sma_sum["net_pts"]
    print(
        f"SMA trades={sma_sum['n_trades']} gross={sma_sum['gross_pts']:+.2f} "
        f"sma_id={'PASS' if sma_sum.get('sma_identity_ok') else 'FAIL'}",
        flush=True,
    )

    start = str(daily.iloc[0]["session_date"])
    end = str(pd.Timestamp(daily.iloc[-1]["session_date"]) + pd.Timedelta(days=5))[:10]
    ndx_cross = fetch_ndx_crosses(start, end)
    match = None
    if ndx_cross is not None and len(ndx_cross) and len(cross_log):
        match = match_crosses(cross_log, ndx_cross, tol_days=10)
        print(
            f"^NDX crosses={len(ndx_cross)}; "
            f"NQ match@10d={match['matched'].mean():.0%}",
            flush=True,
        )
        ndx_path = art("nq_engine_sanity_ndx_crosses.csv")
        ndx_cross.to_csv(ndx_path, index=False)
    else:
        print("^NDX fetch skipped or empty — local checks only", flush=True)

    bh_yearly_path = art("nq_engine_sanity_bh_yearly.csv")
    bh_yearly.to_csv(bh_yearly_path, index=False)
    cross_path = art("nq_engine_sanity_sma_crosses.csv")
    cross_log.to_csv(cross_path, index=False)
    trades_path = art("nq_engine_sanity_sma_trades.csv")
    trades.to_csv(trades_path, index=False)
    if match is not None:
        match_path = art("nq_engine_sanity_cross_match.csv")
        match.to_csv(match_path, index=False)

    report_md = write_report(bh, bh_yearly, sma_sum, cross_log, trades, match, daily)
    md_path = art("nq_engine_sanity_report.md")
    md_path.write_text(report_md, encoding="utf-8")

    payload = {
        "buy_and_hold": bh,
        "buy_and_hold_yearly_identity_failures": int((~bh_yearly["identity_ok"]).sum()),
        "sma": {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in sma_sum.items()},
        "external_ndx_match_rate_10d": (
            float(match["matched"].mean()) if match is not None and len(match) else None
        ),
        "n_globex_days": int(len(daily)),
        "date_start": str(daily.iloc[0]["session_date"]),
        "date_end": str(daily.iloc[-1]["session_date"]),
        "verdict": (
            "ENGINE_OK"
            if bh["identity_ok"]
            and int((~bh_yearly["identity_ok"]).sum()) == 0
            and bool(sma_sum.get("sma_identity_ok"))
            else "ENGINE_FAIL"
        ),
    }
    json_path = art("nq_engine_sanity_report.json")
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Mirror into strategy results/
    results_dir = _CODE.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "full_report.md").write_text(report_md, encoding="utf-8")

    print(f"Report -> {md_path}", flush=True)
    print(f"Verdict: {payload['verdict']}", flush=True)


if __name__ == "__main__":
    main()
