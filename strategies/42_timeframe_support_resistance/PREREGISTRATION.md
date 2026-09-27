# Strategy 42: Timeframe Effect on Simple Support/Resistance

**Pre-registration date:** 2026-09-15  
**Status:** FROZEN BEFORE EXECUTION

## Question

Does the same simple support/resistance breakout setup have a stable or improving net edge as its signal timeframe rises? This is a comparison of signal resolutions, not a search for an optimal S/R strategy.

## Universe and splits

- Continuous NQ futures (primary; 1.0 point round-trip cost) and ES futures (replication; 0.5 point round-trip cost).
- Full CME Globex sessions. Intraday bars are aligned from 18:00 America/New_York; daily bars are complete Globex sessions; weekly bars require five complete sessions.
- IS: 2010--2021. Validation: 2022--2024. OOS: 2025--2026 (reported separately where possible).

## Frozen signal and trade rules

For each timeframe in 1m, 5m, 15m, 30m, 1h, 2h, 4h, 7h, daily, and weekly:

1. At completed bar `T`, resistance is the maximum high and support the minimum low of the preceding **20 completed bars**. The signal is long if `close[T-1] <= resistance` and `close[T] > resistance`; it is short if `close[T-1] >= support` and `close[T] < support`.
2. At most one long and one short signal per signal session (per calendar week for weekly bars). No thresholds are tuned by timeframe or market.
3. **Breakout arm:** enter at the open of the next available 1-minute bar after `T` completes. Exit at the close of the fifth subsequent signal-timeframe bar. Gross P&L is direction-signed; subtract the round-trip cost once.
4. **Breakout-retest arm:** after a breakout, watch the next three completed signal-timeframe bars. A long retest occurs when a 1-minute bar touches/crosses resistance and closes above it; a short retest analogously touches/crosses support and closes below it. Enter at the next available minute open and exit at the close of the fifth signal-timeframe bar after the retest bar. If no retest occurs, no trade is recorded.
5. No stop or target is used. This deliberately measures the signal's fixed-horizon directional payoff without parameterizing a risk model that would differ mechanically by timeframe.

## Causality and execution

All level and breakout facts use data at or before completed bar `T`. Entries occur after the signal/retest minute has completed. Exit prices are later observed. If the immediate next minute is unavailable, the candidate is discarded. No overlapping-position restriction is imposed: this is a per-signal payoff study, not a capital-allocation simulation.

## Decision rule

An apparent timeframe advantage requires positive net expectancy in NQ **and** ES, in IS, Validation, and OOS, with adequate OOS sample size (at least 30 trades). A higher-timeframe result that lacks this sample is descriptive only. We will not infer an advantage over institutional participants from OHLC data; retail relevance is assessed only through trade frequency, holding time, transaction-cost burden, and evidence stability.
