# Preregistration — previous-day directional structure (mechanism only)

**Status:** event definition replaced before the rerun. The original rule — first bar that crosses the previous close — was discarded after review. It measured the Globex open, not a later retracement. Outcome tables from that discarded event are not evidence. This file locks the replacement event. Bucket edges, horizons, and the verdict rule are unchanged. No outcome under this event has been used to edit it.

**Label:** Pre-cost mechanism analysis — no executable strategy.

This file is the definition lock for Step 1. It does not authorize an entry, exit, stop, target, or filter. No threshold below may be revised after results are seen.

## Question

Does the previous trading day's directional candle create a meaningful reference range such that the following session's behavior differs depending on how deeply price retraces into that range?

This is not a test of whether a trade makes money.

## Data

- Instrument: continuous NQ 1-minute OHLC.
- Requested path `d:\NQ\nq_data` is not present on this machine.
- Read-only source actually used: the repository frozen file `data/nq_1m_continuous.parquet` via `common.nq_session.load_nq`. That file is not modified.
- Clock: `America/New_York`.
- Trading day: existing Globex `session_date`. Bars at or after 18:00 ET belong to the next calendar date. This is the same construction as `common.nq_session.load_nq` and strategy 16A (prior Globex daily candle).
- "End of the session" in this study means the last 1-minute bar of that Globex `session_date` (the electronic day ends before the 17:00 ET maintenance break). It is not a cash-RTH-only sample and not a new session definition.
- Splits, reused exactly from `common.splits`: IS 2010–2021, Validation 2022–2024, OOS 2025–2026. The split year is the **following** session's `session_date` year. No shuffling.

## Complete sessions

A session is complete only if all three structural checks hold. These were set from the bar-count shape of the file (a mass of truncated stubs versus a full-session mass), not from any price outcome:

1. At least 1100 one-minute bars.
2. The first bar falls in 18:00–18:05 ET inclusive (`ny_min` 1080 through 1085), so the Globex open is present.
3. At least one bar falls in 16:00–16:59 ET, so the session reaches the last hour of the electronic day.

Incomplete sessions are counted in the audit and are not used as either the previous day or the following day. Pairs must be **adjacent observed session dates**. An incomplete day is not bridged: Monday is not paired with Wednesday if Tuesday exists but is incomplete.

## Previous-day candle

For following session D, the previous day is the adjacent prior `session_date` D-1. Its OHLC uses only D-1 bars:

- `previous_open` = open of the first bar
- `previous_high` = max high
- `previous_low` = min low
- `previous_close` = close of the last bar
- `previous_range` = high − low
- `previous_body` = abs(close − open)
- `previous_body_fraction` = body / range
- `previous_upper_wick` = high − max(open, close)
- `previous_lower_wick` = min(open, close) − low

Direction, and only this:

- bullish if close > open
- bearish if close < open
- doji if close == open

Dojis are not given a direction and are excluded from the primary sample. Today's high, low, and close are not used to classify yesterday. No candle-quality cutoff is applied.

## Reference range

Bullish previous day:

- `reference_start` = previous close
- `reference_extreme` = previous low
- `reference_range` = previous close − previous low
- depth at a price extreme = previous close − that low extreme

Bearish previous day:

- `reference_start` = previous close
- `reference_extreme` = previous high
- `reference_range` = previous high − previous close
- depth at a price extreme = that high extreme − previous close

`penetration_pct` = depth / `reference_range` × 100.

If `reference_range` <= 0 the pair is undefined and excluded (close equals the relevant extreme). This is not a tuned volatility filter.

0% means price has touched the previous close and gone no further. Negative penetration means price has not entered the close-to-extreme range. 100% means price has reached the previous extreme. Above 100% means price has gone through that extreme. The 50% level is only a bin edge, not an entry.

## Separation, then retracement

On the following session's 1-minute bars, in time order. No ATR and no point-distance cutoff. One tick of separation counts.

Bullish previous day:

1. A bar is clean separation when `low > previous_close`. The bar is entirely above the close.
2. A bar is a range entry when `low <= previous_close`.
3. Scan until the first range entry. If that entry occurs before any clean-separation bar, the session has **no qualifying retracement**. A bar with `low <= previous_close` and `high > previous_close` does not establish separation.
4. Otherwise the first clean-separation bar is separation, including a one-tick separation.
5. The retracement is the first **later** bar with `low <= previous_close`. The separation bar itself cannot be the retracement.

Bearish previous day, mirrored:

1. Clean separation: `high < previous_close` (the bar is entirely below the close).
2. Range entry: `high >= previous_close`.
3. A range entry before any clean-separation bar is not a qualifying retracement.
4. The retracement is the first later bar with `high >= previous_close`.

At 1-minute resolution the first bar is either a range entry or clean separation. Qualifying separation is therefore that first bar, and the retracement is a subsequent bar. That is this definition, not an extra delay filter.

Separation followed by no return is an audit count. It is not assigned a penetration bucket.

**Retracement penetration** is the penetration of that later bar's relevant extreme (`low` if the previous day was bullish, `high` if bearish). At 1-minute resolution this is an upper bound on the instantaneous entry depth: the same minute can travel from the boundary to a deep extreme. It is not a tick-level first print. It is not the opening bar unless that bar is a later bar, which this sequence forbids.

**Maximum penetration** is the same calculation using the whole following session's low (bullish previous day) or high (bearish previous day). Its timestamp is the first bar that prints that session extreme. Maximum penetration is an outcome. It is not an entry-time classifier.

The causal forward-outcome tables are stratified by retracement penetration. Tables stratified by maximum penetration are reported separately and labeled non-causal, because the session extreme can print after the forward window.

## Penetration buckets (fixed)

Right edge is exclusive except the last two bins:

| Bucket | Rule |
|---|---|
| no penetration | penetration < 0 |
| 0–10% | 0 ≤ x < 10 |
| 10–20% | 10 ≤ x < 20 |
| 20–30% | 20 ≤ x < 30 |
| 30–40% | 30 ≤ x < 40 |
| 40–50% | 40 ≤ x < 50 |
| 50–75% | 50 ≤ x < 75 |
| 75–100% | 75 ≤ x ≤ 100 |
| >100% | x > 100 |

These edges are not revised after results. Exactly 0% (a touch of the previous close and no deeper print on that measurement) sits in 0–10%. Exactly 100% sits in 75–100%.

## Forward outcomes

There is no trade.

The retracement bar is fully known only at its close. The measurement price is the **open of the next bar**. Forward paths start strictly after the retracement bar. If the retracement is on the session's last bar, that session has no forward path. Separation is known at the close of the separation bar, which is strictly earlier.

Horizons, measured from the measurement bar's open timestamp:

- 5, 15, 30, 60, and 120 minutes: the close of the 1-minute bar that ends at that clock time.
- If that exact minute is missing, the prior minute is accepted (one-minute tolerance for a missing print). A larger hole makes that horizon unavailable. It is not filled with a later price.
- Session end: the last bar's close of the same Globex session.

Bullish previous day:

- `forward_return` = future price − measurement price

Bearish previous day:

- `forward_return` = measurement price − future price

Positive values are movement in the previous day's direction. They are not a win rate and not P&L.

Primary depth comparisons use the fixed 30-minute and 60-minute horizons. Those windows have the same clock length whenever they exist. The session-end horizon is reported, but residual time depends on when the touch occurred, so it is not used by itself to claim that depth matters.

### MFE and MAE

From the measurement bar through the horizon bar, inclusive. The retracement bar itself is excluded.

Bullish previous day (favorable = up):

- MFE = max(high − measurement price)
- MAE = max(measurement price − low)

Bearish previous day (favorable = down):

- MFE = max(measurement price − low)
- MAE = max(high − measurement price)

### Scale

Raw differences are NQ index points, as specified. NQ's price level rises several-fold over 2010–2026, so point averages are not commensurate across years.

A second, pre-registered unit is `forward_return / previous_range` (and the same for MFE and MAE), where `previous_range` is the previous day's high − low, known before the following session opens. This is a unit, not a filter, not ATR, and not a candle-quality rule. The stability verdict uses this unit. Point results are still reported.

## Baseline control

For every eligible pair, the same direction-normalized returns, MFE, and MAE are computed from the following session's **first bar open** (18:00 ET), regardless of whether price later enters the reference range. This is the unconditional previous-day-direction drift. It is the control for the claim that penetration itself is informative.

The same open-baseline is also summarized on the subset of sessions that record a qualifying retracement with a forward bar, so a difference in sample composition is not mistaken for a difference in the measurement clock. That subset is defined by the retracement event, not by the later return.

## Candle structure (descriptive only)

Body fraction, fixed:

- <25%
- 25–50%
- 50–75%
- >75%

Also report upper wick / range and lower wick / range. No threshold is searched.

Candle structure does not enter the mechanism verdict. It is called relevant enough to justify a later dedicated test only if both of the following are true on the 30-minute range-normalized return: the four combined-sample body-fraction medians span at least 0.02 previous-day ranges, and the Spearman correlation of body fraction with that return has the same sign in IS and in Validation with absolute value at least 0.03 in both. Otherwise this pass does not justify a structure follow-up.

## Depth pools used only to summarize stability

These pools are unions of the frozen buckets. They are not new cut-points and are not chosen after looking at which bucket printed a large number.

- shallow: retracement penetration in [0, 30)
- mid: [30, 75)
- deep: >75 (includes through the extreme and beyond)

A minimum of 50 observations is required in a pool before that pool can support a stability claim.

## What will be reported

For each bucket and horizon, where defined: N, mean, median, standard deviation, percentage of strictly positive returns, MFE, MAE.

Separately for bullish previous days, bearish previous days, and the combined direction-normalized sample.

Chronological: IS, Validation, OOS, and year by year.

No costs. No position size. No win rate.

## Verdict rule (frozen)

Let the metric be the median of `forward_return / previous_range` at 30 minutes and at 60 minutes, inside the shallow, mid, and deep pools, using retracement penetration only.

**MECHANISM SUPPORTED** only if all of the following hold:

1. On both 30m and 60m, the ordering of (shallow, mid, deep) medians is identical in IS and in Validation, each pool has N ≥ 50 in both periods, and the spread between the highest and lowest of the three medians is at least 0.02 previous-day ranges.
2. On both horizons, bullish and bearish full-sample orderings are the same as that shared IS/Validation ordering, with N ≥ 50 in each pool.
3. OOS shows that same ordering on both horizons, each OOS pool has N ≥ 50, and each OOS spread is at least 0.02. An under-powered, flat, or differently ordered OOS blocks SUPPORTED and leaves the verdict UNCLEAR unless the NOT SUPPORTED rule applies.

**MECHANISM NOT SUPPORTED** if IS and Validation orderings disagree on both 30m and 60m, and the Spearman rank correlation between continuous retracement penetration and the range-normalized return is below 0.03 in absolute value on the combined sample for both horizons.

**MECHANISM UNCLEAR** in every remaining case, including a pattern that appears in only one horizon, one side, one period, or one bucket.

One attractive bucket is not a mechanism. No language of profitability, win rate, alpha, or edge is used unless a later, separate preregistration earns it. This one does not.

## Explicitly excluded

Lookahead, using today's range to label yesterday, optimizing buckets, entries and exits, SMT, order flow, volume profile, Fibonacci signals, lower-timeframe confirmation, ATR filters, recovery-speed or recovery-strength rules, trading costs, and P&L.
