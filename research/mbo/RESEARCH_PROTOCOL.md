# Research protocol

This protocol separates mechanism evidence from strategy selection. The replay engine does not choose trades.

## Mechanism research versus strategy optimization

Mechanism research asks whether a fact in the order book is followed by a price change. The output is a table: bucket, horizon, sample size, mean, median, hit rate, quantiles.

Strategy research asks whether a rule makes money after costs, with a frozen entry, exit, and size. That work is out of scope until a mechanism result is stable under the rules below.

Do not turn the best cell of a mechanism table into an order.

## Lookahead

- A feature at time `t` may use events with `ts_event <= t` only.
- The one-second row at `t` is `(t-1s, t]`. It is not `[t, t+1s)`.
- `fwd_ret_k = mid[t+k] - mid[t]`, and the timestamp of `mid[t+k]` is greater than `t`.
- A trade's entry mid is the book at that trade's `ts_event`. The future mid is the first grid snapshot at or after `ts_event + horizon`, and that snapshot must be strictly later than the trade.
- Do not backfill a rolling window with a later value.
- Do not fit a threshold on the same observations that are then scored with that threshold, unless the report labels the number as in-sample description and does not treat it as a trading rule.

The tests in `research/mbo/tests/` are the check for the clock, the forward return, chunk equivalence, and determinism. A new replay version needs those tests green before a dataset is trusted.

## Predefined variation

Variation is the grid in `research/mbo/grid.py`, written down before the run.

Size buckets are half-open: 50-89, 90-129, 130-169, 170-199, 200+. Horizons are 1s, 5s, 15s, 30s, 60s, 2m, 5m, 10m, and 15m. Both aggressor sides are reported.

Adding a bucket after seeing the table is a new experiment, not a correction of the old one. Do not search arbitrary thresholds and publish the maximum.

## Train, validation, and untouched data

The 26 sessions from 2026-07-08 through 2026-08-12 are the current in-sample disk set. They are not a promotion.

- Fit nothing on the validation dates.
- Do not open 2026-08-13 through 2026-08-28 until the corrected in-sample mechanism table is frozen.
- Dates after that stay untouched.
- One pass over raw MBO writes the normalized partitions. Later cuts of the same dates read Parquet.

## Multiple testing

A grid of 5 buckets, 3 side labels, and 9 horizons is 135 cells. They are not 135 independent bets. Report the whole grid. Do not star the minimum p-value. If a later test needs a significance claim, predeclare the cell and use a day-level statistic, not one row per second as if the seconds were independent.

## Strategy selection

Strategy selection starts only after all of the following:

1. The replay version is `REPLAY_ENGINE_V2_TIMESTAMP_CORRECT` or a later version that has passed the same clock tests.
2. The mechanism table was produced from normalized Parquet, not from a fresh raw replay with a different clock.
3. The cell was declared before looking at validation.
4. Costs are applied on a book that was known at the decision time, not on a mid that already includes the signal's own trades.

Until then, do not add an entry rule, an exit rule, or a position size.
