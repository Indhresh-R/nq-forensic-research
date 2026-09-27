# 25. SPX 0DTE Dealer Gamma → ES/NQ Intraday

**Verdict: `E`** (incomplete FirmTape minute archive — bulk download blocked)

Hostile causal test of whether publicly reconstructed SPX 0DTE dealer-gamma regimes change the conditional distribution of subsequent S&P 500 (ES) and NQ returns/volatility — not a hunt for a directional GEX signal.

See `DATA_BLOCKER.md` before interpreting any numeric pilot output.

## Documents

| File | Purpose |
|------|---------|
| hypothesis.md | Mechanism under test |
| rules.md | Frozen definitions / lags / regimes |
| testing_methodology.md | Splits, placebos, costs |
| conclusion.md | Verdict with numbers |
| code/README.md | Reproduce |
| results/full_report.md | Full structured report |

## Reproduce

```bash
python strategies/25_spx_0dte_dealer_gamma/code/download_firmtape.py
python strategies/25_spx_0dte_dealer_gamma/code/normalize_firmtape.py
python strategies/25_spx_0dte_dealer_gamma/code/run_spx_dealer_gamma_experiment.py
```

Artifacts: `artifacts/25_spx_0dte_dealer_gamma/`.
Raw FirmTape JSON: `data/firmtape/raw/` (preserved).
