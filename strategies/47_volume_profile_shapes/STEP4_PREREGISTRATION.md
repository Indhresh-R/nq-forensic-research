# Preregistration — Step 4 LVN reaction path

Date frozen: 2026-09-21, before any Step 4 traverse/reject table, horizon count, or null comparison was computed.

This file does not replace earlier preregistrations. Step 3 boundaries and the first-touch definition are inputs. The 0.20 separation cut stays frozen. No new market feature is introduced.

Step 4 does not test profitability, entries, exits, stops, targets, forward returns, or P&L. A traverse is not a trade.

## Question

After the next session's first touch of a prior-session LVN band, when that touch was approached from an accepted region, which competing event happens first within a fixed horizon:

1. **Traverse** — price reaches the opposite HVN.
2. **Reject** — price returns through the approach HVN.
3. **Remain** — neither has happened by the horizon.

Is the observed traverse share above the geometric first-barrier null that uses only the distances from the measurement price to the two HVNs?

## Sample

Start from `results/step3_interactions_sample.csv`.

Primary path sample:

```text
touched == True
approach in {lower_region, upper_region}
```

Expected identity from the finished Step 3 report, not from these path labels:

- 12 lower-region touches
- 22 upper-region touches
- 34 primary rows

If those counts differ, stop.

`open_in_band` touches (expected 5) are not in the primary sample. They have no approach side. They receive a separate first-HVN table only.

`clean` and `both_regions_sized` are descriptive slices of the primary sample. They are not filters that redefine the object. Do not invent a combined `clean and sized` primary rule after seeing results.

No-touch rows are out of scope.

## Price path

Reuse the Step 3 trade-built one-minute OHLC for the next session, including the same sync check against that session's stored profile high and low. Do not switch to continuous adjusted bars.

## Measurement clock

The touch bar is the Step 3 first LVN-band intersection bar. Its timestamp is `touch_ts`.

Path events are evaluated on bars from the touch bar through the horizon, inclusive. The LVN touch itself is not a path event. The path events are HVN prints.

Measurement price for distances, penetration, and the null:

```text
measurement_price = open of the touch bar
```

That price is known at the start of the interacting minute. It is not optimized.

## Competing events

Let:

```text
L = lower_hvn_price
U = upper_hvn_price
```

These are the Step 3 HVN prices from the prior session. They do not move.

### Lower-region approach (`lower → upper`)

- **Traverse** on a bar when `high >= U`.
- **Reject** on a bar when `low <= L`.

### Upper-region approach (`upper → lower`)

- **Traverse** on a bar when `low <= L`.
- **Reject** on a bar when `high >= U`.

These invalidation levels are the approach and opposite HVNs. They are not the full accepted-region spans. Step 3 showed that returning into the approach region span is almost automatic because the LVN band overlaps those spans. That definition is not reused.

### Same-bar conflict

If one bar satisfies both traverse and reject, the outcome for that horizon is `ambiguous_same_bar`. It is neither traverse nor reject in the primary rates.

### First event

Among bars in `[touch_bar, last_bar_in_horizon]`, take the earliest bar that prints traverse or reject.

- Traverse bar strictly before reject bar → `traverse`
- Reject bar strictly before traverse bar → `reject`
- Same bar → `ambiguous_same_bar`
- Neither → `remain`

## Horizons

Minutes are measured from `touch_ts`. A bar is inside the horizon when its open timestamp is at most `touch_ts + H` minutes.

Frozen horizons:

| Name | H |
| --- | ---: |
| H30 | 30 |
| H60 | 60 |
| H120 | 120 |
| session_end | through the last bar of the next session |

Primary mechanism tables use **H60** and **H120**. H30 and session_end are reported. No horizon is added after results are seen.

If the touch bar itself is after the last bar that would fall in H, that row cannot occur for ordinary touches; if a horizon contains no bar, the outcome is `remain` and times are missing.

## Distances and null

```text
dist_to_approach = |measurement_price - approach_hvn|
dist_to_opposite = |measurement_price - opposite_hvn|
```

For lower approach, approach HVN is `L` and opposite is `U`. For upper approach, the reverse.

If either distance is 0, the null is undefined for that row. Count it and exclude it from the null comparison only. Still keep it in the event counts.

Geometric first-barrier null with no drift:

```text
null_traverse_prob = dist_to_approach / (dist_to_approach + dist_to_opposite)
```

This is the probability that a one-dimensional Brownian motion started at the measurement price hits the opposite HVN before the approach HVN. It uses only geometry known at the touch. It is not fitted to outcomes.

Report:

- mean `null_traverse_prob` on the primary rows with defined distances
- observed traverse share among rows whose outcome is `traverse` or `reject` (ambiguous and remain excluded from this ratio)
- the difference: observed − null mean, on that same decided subset, comparing each row's traverse indicator to its own null probability (mean of `1{traverse} - null_traverse_prob`)

Do not search for a significance threshold after the fact. The report states the numbers. A later return test is not authorized by a large difference alone.

## Penetration and excursion

Computed on bars in the horizon, inclusive of the touch bar, using only highs and lows. Still not a return.

Lower approach:

```text
lvn_span = valley_right_price - valley_left_price
hvn_span = U - L
max_lvn_penetration = max(0, min(high, valley_right_price) - valley_left_price) / lvn_span
  over bars in the horizon; if lvn_span == 0, missing
max_opposite_excursion = max(0, high - measurement_price) / hvn_span
```

Upper approach:

```text
max_lvn_penetration = max(0, valley_right_price - max(low, valley_left_price)) / lvn_span
max_opposite_excursion = max(0, measurement_price - low) / hvn_span
```

If `hvn_span <= 0`, stop.

Also store raw point versions: max favorable excursion toward the opposite HVN in NQ points, and max adverse excursion toward the approach HVN in NQ points, over the same horizon. Adverse for lower approach is `max(0, measurement_price - low)`; for upper approach `max(0, high - measurement_price)`. These are path extents, not P&L.

## Times

For traverse or reject outcomes:

```text
minutes_to_event = (event_bar_ts - touch_ts) in minutes
```

For remain or ambiguous, the field is missing.

## open_in_band side table

For the five expected `open_in_band` touches only, within each horizon, record which HVN is printed first (`L` first, `U` first, same bar both, or neither). No null comparison is required for this side table.

## What this step will not do

- It will not change HVN levels, horizons, or the null formula after seeing outcomes.
- It will not add ATR, VWAP, CVD, MBO, day-of-week, opening range, or volatility filters.
- It will not revive P, b, D, or B labels.
- It will not compute a forward return from the touch.
- It will not treat `clean` or `both_regions_sized` as a strategy gate.
