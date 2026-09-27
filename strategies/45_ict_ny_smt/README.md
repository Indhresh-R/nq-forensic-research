# 45. ICT NY SMT Discretionary Backtest

**Verdict: see `reports/BACKTEST_REPORT.md` (filled after run)**

Look-ahead-free backtest of a multi-timeframe ICT/SMT discretionary ruleset on continuous NQ 1-minute futures, with ES for SMT. Default costs: $2.50/side + 1 tick/side slippage.

## Data

- NQ: `data/nq_1m_continuous.parquet` (UTC timestamps → America/New_York)
- ES: `data/es_1m_continuous.parquet` (required for Variant A)

## Run

```bat
set PYTHONPATH=d:\NQ-2
cd d:\NQ-2\strategies\45_ict_ny_smt\code
python test_lookahead.py
python run_backtest.py
python run_backtest.py --quick
python run_backtest.py --years=2020,2021,2022,2023,2024,2025,2026
```

## Outputs

- `results/grid_summary.csv` — full variant × SL × TP grid (IS / OOS / ALL)
- `results/trades_primary_A_SLA_2R.csv` — primary trade log
- `results/trades_all_grid.csv` — all cells
- `results/random_baseline.csv` — Variant E distribution
- `results/cost_sensitivity.csv` — 0/1/2 tick slippage
- `reports/BACKTEST_REPORT.md` — assumptions, QC, verdict
- `reports/figures/` — equity, drawdown, monthly heatmap

## Variants

| Code | Meaning |
|------|---------|
| A | Full (SMT + daily FVG filter + 7H NY filter) |
| B | No SMT (5m MSS / FVG reaction) |
| C | Ablation: no daily FVG filter |
| D | Ablation: no 7H filter |
| E | Random-entry baseline (same session/SL/TP costs) |
