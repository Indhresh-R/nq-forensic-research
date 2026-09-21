# Order lifetime and cancel-versus-fill fate

Written before any lifetime, age, fate, or forward-return number for this question is computed.
No cell in this file may be changed after those numbers exist.

This is a mechanism and information test. It is not an entry, a stop, a target, or a strategy.
A pass is not permission to design a trade. The next question after a pass would be why the association exists.

```text
Engine: REPLAY_ENGINE_V2_TIMESTAMP_CORRECT
Do not modify the replay engine or the frozen one-second store.
Window: [09:30, 12:00) America/New_York
Sessions: the 26 dates in research/mbo/sessions.py IS_SESSIONS
Discovery, sign check only: 2026-07-08 through 2026-07-24 (first 13)
Held-out, the only verdict block: 2026-07-27 through 2026-08-12 (last 13)
Volume profile is not read. Previous-session POC is not an input.
```

The one-second store cannot answer this question. Lifetime, age, and fate are read from the raw MBO event stream in a new read-only pass that uses the frozen clock: an event belongs to the snapshot that already contains it, and a forward mid uses a later snapshot. The 26 mornings are not a multi-year sample. A result here does not establish a durable edge.

## Question

After controlling for one-second inside imbalance, depth change, trade imbalance, and replenishment, does the resting lifetime and eventual cancel-versus-fill fate of inside-quote orders contain incremental information about subsequent mid-price changes?

That sentence is two studies. They are not interchangeable, and a column from one is forbidden in the other.

| Study | What is known at the anchor | What it can mean |
| --- | --- | --- |
| R, retrospective | Completed lifetime and terminal fate | Whether finished orders are followed by a different mid path. Not a real-time signal. Not tradable. |
| P, real-time | Age so far, and trade size that has already printed at the order's price | Whether information available while the order is still resting predicts the later mid. |

Study R does not get promoted into Study P. Eventual lifetime and eventual fate are unknown at arrival and unknown while the order rests.

## Null

After the four one-second controls, the Study R features and the Study P features each have zero partial rank association with the side-signed forward mid change.

The pass rule below is the only rule. Discovery is not searched for a cutoff, a bin, a horizon, or a transform.

## What is deliberately not in the test

No lifetime bins. No age bins. Cuts such as 100 ms, 250 ms, or 500 ms are not defined and may not be added after a histogram or a return table.

The tested transform is `log(1 + x)` with `x` in milliseconds. It is fixed because order durations are right-skewed. The raw millisecond value is stored and is not a second tested feature. Queue-size percentiles, session filters, and side-specific models are not fit.

Queue position is reconstructable as size ahead of the order at the same price. It is written to the audit file and is not in the regression. It cannot change the verdict.

## Side sign

`side_sign` is +1 for a bid and −1 for an ask.

The outcome is `side_sign * (mid[t + h] − mid[t])`, in index points.
Each control is multiplied by the same `side_sign` before residualizing.

A positive association means the feature lines up with the mid moving in the order's favor: up after a bid order, down after an ask order. A negative association is a result. The sign is not recoded.

## Controls

All four are required. A row with any control missing is dropped. Nothing is imputed.

They are the completed one-second bin ending at the anchor snapshot `t`. The bin is `(t − 1s, t]`. It contains no event after `t`.

| Control | Definition, before the side sign |
| --- | --- |
| Inside imbalance | `(q_b1 − q_a1) / (q_b1 + q_a1)`, missing when the denominator is 0 |
| Depth change | Change in best-bid size minus change in best-ask size, from the prior usable snapshot one second earlier. Missing unless both snapshots are usable quotes |
| Trade imbalance | `(buy − sell) / (buy + sell)` on aggressor size in the bin, missing when the denominator is 0 |
| Replenishment | `(added bid − cancelled bid) − (added ask − cancelled ask)` in the bin |

A usable quote is a finite bid and ask with bid < ask. A crossed snapshot is not an anchor and is not a forward endpoint. Crossed rows stay in the store. A locked book is not a usable quote. The stored `mid_px` on a crossed row is not used. The midpoint is `(bid + ask) / 2` on a usable quote only.

## Forward mid

Horizons are 1, 5, 15, and 30 seconds. All four are reported. None is added or dropped later.

`mid[t + h]` is the midpoint of the snapshot `h` seconds after the anchor, on the same session. The return exists only when that snapshot is a usable quote. There is no trade-price target and no stop.

The decision horizon is 1 second. Horizons 5, 15, and 30 are confirmatory. A confirmatory horizon cannot rescue a failed 1-second result, and it cannot be selected as the place the effect "really" was.

## Inside spell

A spell is one continuous stay at the inside quote.

It starts at the first event where the order's price equals the best bid, for a bid, or the best ask, for an ask, after that event is applied. Time already spent behind the touch does not count. An order that leaves the inside and later returns starts a new spell.

It ends at the first event that removes the order from that price:

- a cancel, or the book-reducing cancel that follows fills, which takes remaining size to zero
- a modify that changes price
- a book clear
- the 12:00 boundary

Same-price modifies do not end the spell.

Orders already resting at 09:30 are excluded. Their arrival is outside the window, so the spell start is unknown. Spells still open at 12:00 are excluded from Study R. They may appear in Study P only at snapshots where they are still resting, with features known at that snapshot.

Timestamps are the MBO `ts_event` values, in nanoseconds. Durations are `(t_end − t_start) / 1e6` milliseconds.

## Fate

On this feed a fill message does not change the book. The book update is the cancel that follows the fill. Fate uses both.

During the spell, sum the fill size on that `order_id`. At the terminal event:

| Terminal state | Label | In the primary Study R sample |
| --- | --- | --- |
| Removed by cancel, fill size is 0, price was not modified away | `cancel` | Yes |
| Fill size equals the size still resting just before the removing update, and the order's price was not modified away | `fill` | Yes |
| Some fill size, and a later cancel removes a remainder | `partial_then_cancel` | No |
| Modify changes the price | `modify_away` | No |
| Book clear, or still open at 12:00 | `censored` | No |

The primary fate feature is 1 for `fill` and 0 for `cancel`. Excluded labels are counted in the audit. They are not folded into fill or cancel after the counts are seen.

## Study R

Anchor `t` is the first snapshot strictly after the terminal `ts_event`. The completing event is not inside the forward window.

Features, known only because the spell is over:

- `log(1 + lifetime_ms)`
- fate, 1 for fill and 0 for cancel

These two features are scored separately. They are not entered in one regression and then dropped. Each has its own partial association against the same four controls.

Study R is not tradable. The lifetime was not known when the order arrived.

## Study P

A row exists only while the spell is still open. The snapshot is strictly before the terminal event. Completed lifetime, fate, and any fill that has not yet happened are not columns in this table. A run that carries them is invalid and is not a market result.

One row per open spell per snapshot second.

Features known at that snapshot:

- `log(1 + age_ms)`, with age measured from the spell start to `t`
- `log(1 + trade_size_at_price)`, the aggressor size printed at the order's price from the spell start through `t`

The second feature is exposure already survived. It is not an eventual fill label.

The same order appears in many seconds. Those rows share a path. The gate is a magnitude on the pooled held-out rows. It is not a p-value that treats rows as independent. The mean of the per-session partial associations, and the count of held-out sessions whose sign matches the pooled sign, are reported and cannot override the magnitude gate.

## Incremental association

Inside one evaluation block, for one feature and one horizon:

1. Keep rows where the feature, the side-signed outcome, and all four side-signed controls are finite.
2. Rank the feature, the outcome, and the four controls within that block.
3. Residualize the ranked feature and the ranked outcome on the four ranked controls by linear least squares, with an intercept, fit inside that block only.
4. The partial association is the Pearson correlation of the two residual vectors.

Discovery and held-out are residualized separately. Discovery coefficients are not applied to held-out rows. Discovery is used only to record sign.

The association is blank when the block has fewer than 30 finite rows or the feature does not vary.

## Verdict

Each of the four features is judged on its own held-out 1-second partial association.

| Feature | Study |
| --- | --- |
| `log(1 + lifetime_ms)` | R |
| fate, fill versus cancel | R |
| `log(1 + age_ms)` | P |
| `log(1 + trade_size_at_price)` | P |

`SUPPORTED` for that feature only when the held-out 1-second partial association is at least 0.02 in absolute value and its sign equals the discovery sign.

`NOT SUPPORTED` for that feature when the held-out 1-second absolute association is below 0.02.

`INCONCLUSIVE` for that feature when discovery and held-out signs differ, or the held-out association is blank.

The question as a whole is `NOT SUPPORTED` when all four features are `NOT SUPPORTED`. It is `SUPPORTED` when at least one feature is `SUPPORTED`. Any `INCONCLUSIVE` feature with no `SUPPORTED` feature leaves the question `INCONCLUSIVE`.

The equal-frequency fifth-to-fifth spread of the side-signed 1-second outcome is reported for a supported feature. It is not a second gate and it is not a cutoff search. A supported association whose fifth-to-fifth spread is inside one NQ tick, 0.25 point, is still not a trade.

Confirmatory horizons are printed in the same table. They do not change these labels.

## Invalid run

The run is discarded, and no verdict is issued, if any of these are true:

- a Study P row contains completed lifetime or fate
- a Study R forward window includes the terminal event
- a control bin contains an event after the anchor
- a definition, horizon, transform, or split was changed after a return was computed
- the replay engine version string was edited to produce the file

## After the verdict

A `NOT SUPPORTED` result means that, on this NQ MBO sample, the event-level features above add no incremental 1-second directional association beyond the one-second state already tested.

A `SUPPORTED` result is an association in this sample. It does not authorize an execution rule.
