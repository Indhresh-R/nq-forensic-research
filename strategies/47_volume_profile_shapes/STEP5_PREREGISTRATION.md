# Preregistration — Step 5 null-calibrated LVN rejection

Date frozen: 2026-09-21, before any Step 5 rejection-null table, same-minute split, or location tally was computed.

This file does not replace earlier preregistrations. Step 4 path outcomes are inputs. The HVN event definitions, horizons, and geometric distances stay exactly as in Step 4. Traverse remains killed; this step does not reopen it.

Step 5 does not test profitability, entries, exits, stops, targets, forward returns, or P&L. A reject is not a trade.

## Question

After an accepted-region approach into a prior-session LVN band, is the probability of returning through the approach HVN within a fixed horizon above an appropriate geometric null — and is that rejection a later reaction, or often the same minute as the LVN touch?

`Traversal failed` does not imply `rejection works`.

## Sample

Use `results/step4_paths.csv`.

Primary sample, unchanged:

```text
approach in {lower_region, upper_region}
```

Expected identity from Step 4: 34 rows per horizon (12 lower, 22 upper). If a horizon block differs, stop.

Descriptive slices, reported separately and not combined after seeing results:

- lower→upper
- upper→lower
- clean
- both_regions_sized

Horizons: H30, H60, H120, session_end. Primary mechanism tables: **H60** and **H120**.

## Inherited event definitions

From Step 4, unchanged:

- Reject / traverse / remain / ambiguous_same_bar
- Measurement price = touch-bar open
- `dist_to_approach`, `dist_to_opposite`
- `null_traverse_prob = dist_to_approach / (dist_to_approach + dist_to_opposite)` when both distances are positive

Define:

```text
null_reject_prob = 1 - null_traverse_prob
```

when the traverse null is defined. Otherwise the reject null is undefined.

## Two null comparisons

### A. Decided complementary null

On rows with outcome in `{reject, traverse}` and a defined null:

```text
observed_reject_share = share with outcome == reject
mean_null_reject = mean(null_reject_prob)
difference = mean(1{reject} - null_reject_prob)
```

This is the mirror of Step 4's decided traverse test. It is reported for completeness. It is **not** independent evidence that rejection “works.”

### B. Unconditional rejection null

On all primary rows with a defined null:

```text
observed_reject_rate = share with outcome == reject
mean_null_reject = mean(null_reject_prob)
difference = mean(1{reject} - null_reject_prob)
```

Remain and traverse both count as non-reject. This asks whether rejection is the typical resolution inside the horizon, not merely the winner among rows that already hit a barrier.

A rejection claim strong enough to justify a later return test needs support from **B**, not only from **A**.

## Same-minute vs delayed rejection

A reject is **same-minute** when `reject_bar == touch_bar` (minutes to event are 0).

A reject is **delayed** when `reject_bar > touch_bar`.

Report counts of same-minute vs delayed rejects.

### C. Delayed-only decided null

Repeat null A on the subset of decided rows that are not same-minute rejects. Same-minute rejects are excluded from this slice entirely (they are neither delayed reject nor traverse for this comparison). Traverses remain. If a row is a same-minute reject, drop it from C.

### D. Delayed unconditional rate

Among rows whose touch bar does **not** already print the approach HVN, compute the unconditional reject rate and difference vs mean `null_reject_prob` on that subset.

Touch bar already prints the approach HVN when, on the touch bar alone, the Step 4 reject condition is true. Those rows are excluded from D's denominator.

C and D ask whether rejection survives after removing same-minute barrier hits that may be the wide first LVN minute rather than a reaction.

## Where rejection occurs

For each reject row, using bars from the touch bar through the reject bar inclusive, and only OHLC:

Let `far_edge` be `valley_right_price` for a lower-region approach and `valley_left_price` for an upper-region approach.

Let `max_toward_opposite` be the maximum high (lower approach) or the minimum low (upper approach) on that inclusive path.

Classify:

| Label | Rule |
| --- | --- |
| `band_only` | Lower: `max_toward_opposite <= far_edge`. Upper: `max_toward_opposite >= far_edge`. Never cleared the far LVN edge before rejecting. |
| `past_far_edge` | Cleared the far edge toward the opposite side, but the opposite HVN was not printed before the reject (otherwise traverse would have won). |

If `lvn_span == 0`, location is `undefined`.

Also store, on the reject path only (touch through reject):

- minutes to rejection
- max LVN penetration
- max opposite excursion (fraction of HVN span)
- max opposite points
- whether the reject is same-minute

These path extents stop at the reject bar. They are not the full-horizon extents from Step 4 when the horizon continues after rejection.

## What this step will not do

- It will not revive the traverse hypothesis.
- It will not treat null A alone as evidence to trade rejection.
- It will not add ATR, VWAP, CVD, MBO, day-of-week, opening range, or volatility filters.
- It will not compute a forward return from the reject.
- It will not change horizons or HVN levels after seeing the splits.
