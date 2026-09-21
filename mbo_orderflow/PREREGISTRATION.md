# Information tests, preregistered

Written before any forward-return number from this phase was computed.
The replay engine is not modified. The volume-profile dataset is not read.
Previous-session POC is not an input.

```text
Engine: REPLAY_ENGINE_V2_TIMESTAMP_CORRECT
Execution window: 09:30–12:00 America/New_York
Sessions: the 26 dates in research/mbo/sessions.py IS_SESSIONS
Crossed-book rows: kept in the store
Infrastructure: ACCEPTED / FROZEN
```

This sample is an information diagnostic. It is not large enough to establish a durable multi-year edge. No regime split is added. No horizon is chosen after the results. No cell is promoted.

## Crossed-book rule

A snapshot is crossed when bid and ask are both finite and bid > ask.
Those 25 rows stay in the raw store.

A usable quote is finite bid and ask with bid < ask.
The midpoint is (bid + ask) / 2 only on a usable quote.
The stored `mid_px` column is not used, because it was filled on crossed rows too.
A locked book (bid = ask) is counted and is not a usable quote.

Crossed rows are excluded from quote-derived features and from forward-return anchors.

- Do not calculate imbalance from bid size and ask size on a crossed row.
- Do not calculate a midpoint from a crossed bid and ask.
- Do not start a forward-return observation at a crossed snapshot.
- Do not delete the session or the surrounding seconds.
- Trade, add, and cancel records on a crossed second stay in rolling trade and order-flow sums. Those records are not quotes.

A forward return at horizon h exists only when both t and t+h are usable quotes, and t+h is the snapshot h seconds later on the same session. The return is mid[t+h] - mid[t], in index points. There is no second price target. The snapshot store has no separate last-trade price, and this test does not build one.

The same exclusion applies to every feature family. A trade-flow feature may be finite on a crossed row, and that row is still not an anchor.

## What is not in the frozen store

Action M (modify) counts were not written by the frozen replay. This test does not rebuild the book to add them. The order-flow family is adds, cancels, and depth changes only.

## Features

Windows are 1, 5, 15, 30, and 60 seconds. A window of w seconds at t is the sum of the completed one-second bins (t-w, t]. The first w-1 seconds of a session are missing. Nothing is backfilled.

Horizons are 1, 5, 15, 30, and 60 seconds. They are all reported.

Trade aggression. Buy and sell volume are non-negative, so they have a rank correlation only. The directional columns use the signed transforms.

- `buy_volume`: aggressor-buy size
- `sell_volume`: aggressor-sell size
- `trade_imbalance`: (buy - sell) / (buy + sell), missing when the denominator is 0
- `signed_volume`: buy - sell
- `count_imbalance`: (buy count - sell count) / (buy count + sell count), missing when the denominator is 0

Book state, defined only on a usable quote.

- `obi_1`: (q_b1 - q_a1) / (q_b1 + q_a1), missing when the denominator is 0
- `obi_5`: (q_b5 - q_a5) / (q_b5 + q_a5), missing when the denominator is 0
- `spread`: ask - bid. Non-negative. Rank correlation only.
- `tob_depth`: q_b1 + q_a1. Non-negative. Rank correlation only.

Depth change. Both t and t-w must be usable quotes. Otherwise the change is missing. A crossed second between them does not by itself blank the change.

- `depth_bid_change`: q_b1[t] - q_b1[t-w]
- `depth_ask_change`: q_a1[t] - q_a1[t-w]
- `depth_net_change`: depth_bid_change - depth_ask_change

Order-flow change, from add and cancel size. Crossed seconds remain inside the sum.

- `add_signed`: added bid size - added ask size
- `cancel_signed`: cancelled bid size - cancelled ask size
- `replenish_net`: (added bid - cancelled bid) - (added ask - cancelled ask)

One combined feature, declared here rather than after seeing which family moved:

- `obi_x_flow`: obi_1 multiplied by trade_imbalance at 5 seconds. Missing if either leg is missing.

Positive feature value is the raw sign above. Ask-side features are not flipped. A negative rank correlation is a result, not a failure to be recoded.

## Statistics

For each feature and horizon, on the pooled valid anchors:

- N: anchors where the feature and the forward return are both finite
- Median fwd and mean fwd: forward return when the feature is strictly positive
- Median fwd when the feature is strictly negative, stored beside the positive side
- Sign %: share of anchors with both feature and return nonzero whose signs match
- IC: Spearman rank correlation of the raw feature with the forward return

Sign % and the conditional medians are blank for non-negative features.

An IC is blank when N is under 30 or either side has no variation.
The temporal split is the first 13 dates against the last 13, in `IS_SESSIONS` order:

- Early: 2026-07-08 through 2026-07-24
- Late: 2026-07-27 through 2026-08-12

The same IC is computed inside each half. A per-session Spearman is computed when that session has at least 100 finite pairs and both sides vary. The median of those session ICs is reported and is not a replacement for the pooled IC.

No threshold is searched. No feature is dropped because its IC is small.

## How a shape will be read

After the table exists, a signed feature is called horizon-stable only if its five full-sample ICs are all positive or all negative.
It is called split-stable only if the early IC and the late IC at 5 seconds have that same sign.
This label is a description. It does not select a feature for a later POC test.

The features checked for that shape are `trade_imbalance` at each window, `obi_1`, `obi_5`, `depth_net_change` at 1, 5, and 15 seconds, `replenish_net` at 1 and 5 seconds, and `obi_x_flow`.
