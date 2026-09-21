"""Run ICT NY SMT discretionary backtest grid (look-ahead-free)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    FIGS,
    SL_MODES,
    SLIPPAGE_GRID,
    TP_MODES,
    VARIANTS,
    BacktestConfig,
    REPORTS,
    RESULTS,
)
from engine import (  # noqa: E402
    build_store,
    materialize_variant,
    random_baseline,
    scan_setups,
)
from market_data import load_markets  # noqa: E402
from metrics import (  # noqa: E402
    bootstrap_expectancy_ci,
    by_weekday_hour,
    chronological_split,
    ensure_dirs,
    plot_drawdown,
    plot_equity,
    plot_monthly_heatmap,
    random_percentile,
    summarize_trades,
    walkforward_monthly,
)


ASSUMPTIONS = [
    "Timestamps in parquet are UTC; converted to America/New_York with DST via zoneinfo.",
    "session_date = CME Globex day labeled by the calendar date of the RTH portion (bars from 18:00 ET map to next calendar date), matching repo convention.",
    "Daily candle = 18:00 -> 17:00 ET (mins_from_anchor < 23h). Known after its close_ts.",
    "7H NY filter uses ONLY bin0 (18:00–01:00) as C1 and bin1 (01:00–08:00) as C2. The 08:00–15:00 bin is NOT used for morning entries because it has not closed by 08:30–11:30 (lookahead).",
    "Daily bias: C2 vs C1 continuation/reversal direction; if neither, fallback to C2 close vs open.",
    "Daily FVG reaction: CONFIRMED if price traded into FVG and a subsequent 1m close resumed through the FVG in bias direction (last event wins if both resume and against occurred). UNCONFIRMED if closed against. Untested/pending/no_fvg require HTF 1H C1->C2 in bias direction before trades.",
    "Protected level: latest 1H engulfing (prior opposite candle, close beyond its extreme); fallback to 4H. Invalidation on wick through level.",
    "Variant A SMT: require 1H SMT (NQ vs ES) AND 5m SMT confirmation, both at/inside a 1H FVG, live during 1H C2 (after C1 close, before C2 close).",
    "SMT swings: fractal with lookback=3 each side; usable only after right-side bars close (confirmed_at).",
    "Bearish SMT = one market HH vs prior swing high, other fails; bullish = one LL, other fails.",
    "Variant B entry: 5m market structure shift (sweep prior confirmed swing and close beyond) OR bullish/bearish close inside 1H FVG.",
    "Entry at confirming 5m candle close (decision_ts = close_ts - 1m).",
    "Same-bar SL+TP -> SL first. Force flat at 15:55 ET. Costs: $2.50/side + N ticks slippage/side.",
    "Liquidity TP: nearest equal high/low (2-tick tol) or nearest confirmed 15m swing beyond entry; fallback 2R if none.",
    "IS/OOS = chronological 60/40 by session_date count. No parameter choice on OOS.",
    "Random baseline samples 400 sessions/run × 500 runs; not identical trade-count matched — used as expectancy distribution reference.",
    "MNQ P&L uses $2/point with same commission (conservative vs typical MNQ fees).",
    "Do not tune parameters to fit; defaults from the brief only.",
]


def maybe_filter_years(df: pd.DataFrame, years: list[int] | None) -> pd.DataFrame:
    if not years:
        return df
    return df[df["ts"].dt.year.isin(years)].reset_index(drop=True)


def main(years: list[int] | None = None, quick: bool = False) -> None:
    ensure_dirs()
    cfg = BacktestConfig()
    if quick:
        cfg.random_runs = 50
        years = years or list(range(2022, 2027))

    t0 = time.time()
    nq, es, qc = load_markets(cfg)
    nq = maybe_filter_years(nq, years)
    es = maybe_filter_years(es, years)
    # Align calendars
    lo = max(nq["ts"].min(), es["ts"].min())
    hi = min(nq["ts"].max(), es["ts"].max())
    nq = nq[(nq["ts"] >= lo) & (nq["ts"] <= hi)].reset_index(drop=True)
    es = es[(es["ts"] >= lo) & (es["ts"] <= hi)].reset_index(drop=True)
    print(f"Aligned range: {lo} -> {hi} | NQ bars={len(nq)} ES bars={len(es)}")

    nq_store = build_store(nq, cfg, "NQ")
    es_store = build_store(es, cfg, "ES")

    print("Scanning setups (single causal pass)...")
    setups, fvg_counts = scan_setups(nq, nq_store, es_store, cfg)
    setups.to_csv(RESULTS / "setups_raw.csv", index=False)
    print(f"Raw setups: {len(setups)}")
    print("Daily FVG state counts (session-level):", fvg_counts)

    from engine import _swing_pack

    m15_swings = _swing_pack(nq_store.m15, cfg.swing_lookback)

    grid_rows = []
    all_trades = []
    primary_key = None

    for variant in VARIANTS:
        for sl_mode in SL_MODES:
            for tp_mode in TP_MODES:
                trades = materialize_variant(
                    setups, nq, nq_store, cfg, variant, sl_mode, tp_mode, m15_swings
                )
                key = f"{variant}_SL{sl_mode}_TP{tp_mode}"
                if primary_key is None and variant == "A" and sl_mode == "A" and tp_mode == "2R":
                    primary_key = key
                is_df, oos_df = chronological_split(trades, cfg.is_frac)
                for split_name, part in (("ALL", trades), ("IS", is_df), ("OOS", oos_df)):
                    summ = summarize_trades(part, label=f"{key}|{split_name}")
                    summ["variant"] = variant
                    summ["sl_mode"] = sl_mode
                    summ["tp_mode"] = tp_mode
                    summ["split"] = split_name
                    grid_rows.append(summ)
                if not trades.empty:
                    trades = trades.copy()
                    trades["grid_key"] = key
                    all_trades.append(trades)
                print(
                    f"  {key}: n={len(trades)} "
                    f"E[R]={summ['expectancy_r'] if trades.empty else summarize_trades(trades)['expectancy_r']:.3f}"
                )

    grid = pd.DataFrame(grid_rows)
    grid.to_csv(RESULTS / "grid_summary.csv", index=False)
    trades_all = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    trades_all.to_csv(RESULTS / "trades_all_grid.csv", index=False)

    # Primary cell detailed outputs: A / SL-A / 2R (not cherry-picked — fixed a priori)
    primary_variant, primary_sl, primary_tp = "A", "A", "2R"
    primary = materialize_variant(
        setups, nq, nq_store, cfg, primary_variant, primary_sl, primary_tp, m15_swings
    )
    primary.to_csv(RESULTS / "trades_primary_A_SLA_2R.csv", index=False)
    is_p, oos_p = chronological_split(primary, cfg.is_frac)
    is_p.to_csv(RESULTS / "trades_primary_IS.csv", index=False)
    oos_p.to_csv(RESULTS / "trades_primary_OOS.csv", index=False)

    # Cost sensitivity on primary
    cost_rows = []
    for slip in SLIPPAGE_GRID:
        cfg_c = BacktestConfig(slippage_ticks=slip)
        tr = materialize_variant(
            setups, nq, nq_store, cfg_c, primary_variant, primary_sl, primary_tp, m15_swings
        )
        for split_name, part in (
            ("ALL", tr),
            ("IS", chronological_split(tr, cfg.is_frac)[0]),
            ("OOS", chronological_split(tr, cfg.is_frac)[1]),
        ):
            s = summarize_trades(part, label=f"slip{slip}|{split_name}")
            s["slippage_ticks"] = slip
            s["split"] = split_name
            cost_rows.append(s)
    pd.DataFrame(cost_rows).to_csv(RESULTS / "cost_sensitivity.csv", index=False)

    # Random baseline
    print(f"Random baseline ({cfg.random_runs} runs)...")
    rnd = random_baseline(nq, cfg, primary_sl, primary_tp, cfg.random_runs)
    rnd.to_csv(RESULTS / "random_baseline.csv", index=False)

    # Charts for primary
    plot_equity(primary, FIGS / "equity_primary.png", "Primary A / SL-A / 2R equity (1 NQ)")
    plot_drawdown(primary, FIGS / "drawdown_primary.png", "Primary drawdown")
    plot_monthly_heatmap(primary, FIGS / "monthly_heatmap_primary.png", "Primary monthly P&L ($)")
    plot_equity(oos_p, FIGS / "equity_primary_OOS.png", "Primary OOS equity")

    wd, hr = by_weekday_hour(primary)
    wd.to_csv(RESULTS / "by_weekday.csv", index=False)
    hr.to_csv(RESULTS / "by_hour.csv", index=False)
    walkforward_monthly(primary).to_csv(RESULTS / "walkforward_monthly.csv", index=False)

    boot_all = bootstrap_expectancy_ci(primary)
    boot_oos = bootstrap_expectancy_ci(oos_p)
    prim_sum = summarize_trades(primary, "primary_all")
    oos_sum = summarize_trades(oos_p, "primary_oos")
    is_sum = summarize_trades(is_p, "primary_is")
    pct = random_percentile(prim_sum["expectancy_r"], rnd)

    meta = {
        "assumptions": ASSUMPTIONS,
        "data_quality": [q.to_dict() for q in qc],
        "fvg_state_counts": fvg_counts,
        "aligned_range": [str(lo), str(hi)],
        "n_setups": int(len(setups)),
        "primary": {
            "cell": "A / SL-A / TP-2R",
            "all": prim_sum,
            "is": is_sum,
            "oos": oos_sum,
            "bootstrap_E_R_all": boot_all,
            "bootstrap_E_R_oos": boot_oos,
            "random_percentile_E_R": pct,
        },
        "runtime_sec": time.time() - t0,
        "years_filter": years,
        "quick": quick,
    }
    with open(RESULTS / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    write_report(meta, grid, fvg_counts)
    print(f"Done in {meta['runtime_sec']:.1f}s. Report: {REPORTS / 'BACKTEST_REPORT.md'}")


def write_report(meta: dict, grid: pd.DataFrame, fvg_counts: dict) -> None:
    p = meta["primary"]
    lines = [
        "# ICT NY SMT Discretionary Backtest Report",
        "",
        "## Verdict (plain language)",
        "",
    ]
    oos = p["oos"]
    exp = oos.get("expectancy_r", float("nan"))
    n = oos.get("n_trades", 0)
    if n < 30:
        verdict = (
            f"**INCONCLUSIVE / likely no reliable edge.** OOS trades={n} is too small "
            f"for confidence. OOS E[R]={exp}. Treat any positive IS result as fragile."
        )
    elif exp is not None and exp == exp and exp > 0 and oos.get("total_pnl_nq", 0) > 0:
        verdict = (
            f"**WEAK / tentative positive OOS signal only if costs hold.** "
            f"OOS n={n}, E[R]={exp:.3f}, total P&L=${oos.get('total_pnl_nq', 0):.0f}. "
            f"Bootstrap 95% CI on E[R] (OOS): {p['bootstrap_E_R_oos']}. "
            f"Random-baseline percentile of ALL-sample E[R]: {p['random_percentile_E_R']:.1f}th. "
            f"Review full grid for sensitivity; do not promote a single cell."
        )
    else:
        verdict = (
            f"**NO EVIDENCE OF EDGE after costs on OOS.** "
            f"OOS n={n}, E[R]={exp}, total P&L=${oos.get('total_pnl_nq', 0):.0f}. "
            f"IS may look better — that is an overfitting risk flag."
        )
    lines += [verdict, "", "## Assumptions I made", ""]
    for a in meta["assumptions"]:
        lines.append(f"- {a}")
    lines += ["", "## Data quality", ""]
    for q in meta["data_quality"]:
        lines.append(f"- **{q['symbol']}**: {q['date_start']} -> {q['date_end']}, "
                     f"bars={q['bar_count']}, dupes={q['duplicate_ts']}, "
                     f"gaps>5m={q['gaps_gt_5m']}, gaps>60m={q['gaps_gt_60m']}, "
                     f"tz={q['tz_detected']}")
    lines += [
        "",
        f"Aligned range: {meta['aligned_range'][0]} -> {meta['aligned_range'][1]}",
        "",
        "## Daily FVG state counts (sessions evaluated)",
        "",
        "```",
        json.dumps(fvg_counts, indent=2),
        "```",
        "",
        "## Primary cell (fixed a priori: Variant A, SL-A, TP 2R)",
        "",
        f"- ALL: {p['all']}",
        f"- IS: {p['is']}",
        f"- OOS: {p['oos']}",
        f"- Bootstrap E[R] ALL: {p['bootstrap_E_R_all']}",
        f"- Bootstrap E[R] OOS: {p['bootstrap_E_R_oos']}",
        f"- Random baseline percentile (E[R]): {p['random_percentile_E_R']}",
        "",
        "## Full grid (see `results/grid_summary.csv`)",
        "",
    ]
    # Compact grid table for ALL split
    if grid is not None and not grid.empty:
        allg = grid[grid["split"] == "ALL"][
            ["variant", "sl_mode", "tp_mode", "n_trades", "win_rate", "expectancy_r", "expectancy_usd", "profit_factor", "total_pnl_nq", "max_dd_usd"]
        ]
        try:
            lines.append(allg.to_markdown(index=False))
        except Exception:
            lines.append("```")
            lines.append(allg.to_string(index=False))
            lines.append("```")
        lines.append("")
        lines.append("### IS vs OOS (all cells)")
        lines.append("")
        iso = grid[grid["split"].isin(["IS", "OOS"])][
            ["variant", "sl_mode", "tp_mode", "split", "n_trades", "expectancy_r", "total_pnl_nq"]
        ]
        try:
            lines.append(iso.to_markdown(index=False))
        except Exception:
            lines.append("```")
            lines.append(iso.to_string(index=False))
            lines.append("```")
    lines += [
        "",
        "## Charts",
        "",
        "- `reports/figures/equity_primary.png`",
        "- `reports/figures/drawdown_primary.png`",
        "- `reports/figures/monthly_heatmap_primary.png`",
        "- `reports/figures/equity_primary_OOS.png`",
        "",
        "## Overfitting / sample-size flags",
        "",
        "- Large discrete grid (variants × SL × TP) without hierarchical testing inflates false positives.",
        "- SMT + multi-filter stack produces sparse trades; small-n OOS is expected.",
        "- Several rule ambiguities were resolved with conservative causal defaults (see assumptions).",
        "- Random baseline is not trade-count matched; use as rough expectancy reference only.",
        "",
        f"Runtime: {meta['runtime_sec']:.1f}s",
        "",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "BACKTEST_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    years = None
    for a in sys.argv[1:]:
        if a.startswith("--years="):
            years = [int(x) for x in a.split("=", 1)[1].split(",")]
    main(years=years, quick=quick)
