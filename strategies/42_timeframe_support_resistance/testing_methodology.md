# Testing Methodology

## Causality card

```text
Information available at signal: completed bars through T only
Breakout entry: next available 1-minute open after T
Retest entry: next available 1-minute open after the qualifying retest minute
Exit: close of a later completed signal-timeframe bar
Future information in signal: NO
```

## Outputs

Each arm is reported by market, timeframe, and chronological split with trade count, win rate, gross/net expectancy, profit factor, total net points, and a cost-burden diagnostic. Every individual trade is retained for audit.

## Interpretation controls

- Same 20-bar lookback and five-bar holding period are deliberately invariant in bar units. Thus increasing timeframe also increases the information/holding horizon; that is the object being measured.
- Weekly and possibly daily results have far fewer independent observations. They cannot establish a retail edge without the pre-registered OOS count.
- NQ-only success is not sufficient because NQ has a well-documented long-drift confound in this program. ES is a replication check.
