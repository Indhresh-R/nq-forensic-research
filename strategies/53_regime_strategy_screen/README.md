# Strategy 53 — Regime Strategy Screen

**Status: COMPLETE / FROZEN.** All four cells `REJECTED`. Do not rescue.

Screening study: route frozen Strategy 52 market-state flags into one simple representative rule per family.

See `COMPLETE.md` and `results/REGIME_STRATEGY_SCREEN.md`.

## Run (historical only)

```bash
python strategies/53_regime_strategy_screen/code/run_screen.py
```

## Cells (all REJECTED)

| Cell | State flag | Family |
| --- | --- | --- |
| A | TRENDING (`flag_trending`) | continuation |
| B | CHOP (`flag_chop`) | mean reversion |
| C | COMPRESSION | breakout |
| D | EXPANSION | exhaustion / reversal |
