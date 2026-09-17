# Testing Methodology

## Causality card

```text
State information: completed 1m bars through t only
Signal: close of t
Entry: open of t+1
Stops/targets: later 1m OHLC, adverse collision policy
Future session/range boundaries: prohibited
```

Outputs include the full detector grid, selected-cell trade ledger, split/year/side/regime/time-of-day metrics, detected range diagnostics, breakout/pullback diagnostics, and fade vs continuation vs combined comparisons.
