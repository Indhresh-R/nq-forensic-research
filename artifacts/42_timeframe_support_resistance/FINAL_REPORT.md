# Strategy 42: Does timeframe create an S/R edge?

**Verdict: C — no executable timeframe edge.**

The same frozen 20-bar support/resistance setup was tested on continuous NQ and ES futures from 2010 through August 2026 at 1m, 5m, 15m, 30m, 1h, 2h, 4h, 7h, daily, and weekly resolution. Every signal used causal next-available-minute entry, one fixed round-trip cost (NQ 1.0 point; ES 0.5), and a five-signal-bar exit. Two arms were tested: breakout immediately, and breakout followed by a retest within three bars.

## Headline result

No timeframe/entry arm satisfies the frozen requirement of positive net expectancy in **both** markets across IS, Validation, and OOS with at least 30 OOS trades.

OOS net expectancy for the retest arm (points/trade):

| Timeframe | NQ (n) | ES (n) |
| --- | ---: | ---: |
| 1m | +1.10 (304) | -0.19 (342) |
| 5m | -1.81 (458) | -0.98 (466) |
| 15m | +0.49 (478) | -0.38 (517) |
| 30m | -1.53 (409) | -0.37 (458) |
| 1h | -4.07 (283) | -3.80 (301) |
| 2h | -7.86 (173) | -2.63 (187) |
| 4h | -14.97 (118) | -4.73 (123) |
| 7h | -22.70 (97) | -14.60 (99) |
| Daily | -134.84 (48) | -26.17 (42) |
| Weekly | -512.06 (8) | -46.28 (10) |

The immediate-breakout arm is also net negative in both markets in every OOS timeframe. Its NQ/ES OOS expectations range from -0.07/-0.33 at 1m to -95.41/-53.37 at weekly; the daily and weekly OOS samples are low-power and descriptive only.

## Interpretation

Increasing timeframe changes the unit of information and holding period: a 20-bar level and five-bar hold spans minutes at 1m but weeks at weekly. Costs become a much smaller percentage of gross movement as timeframe rises, but that does **not** turn into a stable payoff. Post-1h OOS results are uniformly negative in both markets for both arms.

The positive NQ OOS cells are unstable, not an edge: 1m retest is +1.10 OOS but -0.89 IS and ES is -0.19 OOS; 15m retest is +0.49 OOS but -1.43 IS and ES is -0.38 OOS. Daily/weekly retest reverses from positive IS/Validation to sharply negative OOS, with only 8–48 NQ OOS trades.

Higher timeframe is therefore not an observed retail advantage here. It can reduce screen time, trade frequency, and relative friction, but it does not supply predictive S/R edge. This rejects only the generic claim that moving the same simple breakout/retest setup to a higher timeframe creates a reliable retail edge; it does not rule out a separately justified S/R strategy using new information.

## Audit files

- `summary.csv` — all market × timeframe × arm × split metrics.
- `all_trades.csv` — each causal signal, fill, exit, and net P&L.
- `strategies/42_timeframe_support_resistance/PREREGISTRATION.md` — frozen design.
