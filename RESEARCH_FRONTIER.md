# Research frontier

This file follows `RESEARCH_INVENTORY.md`. It does not propose a strategy. It asks whether any information class still open in this repository is different from the claims already closed.

## What failed, in one paragraph

Directional price geometry, directional use of the activity/volatility state, overnight and opening-auction conditioning, OHLC volume as flow, and the LVN/POC profile-reaction branch are closed on the terms in the inventory. Two geometry results remain `INCONCLUSIVE` (prior-day penetration, ICT SMT with 16 OOS trades). They are not a license to retune those rules. Passive drift and volatility clustering are real and do not point to a direction.

## True order flow versus what was already measured

MBO is not OHLC, not a volume profile, and not a signed-volume proxy. The reconstructed book has order ids, add, cancel, modify, trade, and fill. Strategy 27 showed that a 1-minute signed-volume proxy is mostly the return. A profile POC is a volume-by-price summary of trades after the session. Neither object can see a queue.

The tests that have actually been run used only the part of MBO that survives a one-second sum:

| MBO object | Absent from OHLC and from a profile? | What was done |
| --- | --- | --- |
| Inside-queue size imbalance | Yes | H01. Killed. 1-second IC +0.016, quintile spread +0.086 pt, inside one tick. |
| Five-level depth imbalance | Yes | H01. Noise after a few seconds. |
| Aggressor buy vs sell | Yes, as a separate print | Corrected diagnostic. 1-second imbalance IC about −0.006 to −0.001. Not continuation. |
| Adds, cancels, replenishment, summed per second | Yes | Diagnostic. Not horizon-stable. Largest cell failed the early/late split. |
| Product of imbalance and trade flow | Yes | Diagnostic. IC 0.001–0.005. |
| Absorption (size hits a level and price does not move) | Partly visible in bars as “high volume, small range,” which 27 already found is not signed flow | Named test exists only on a retracted clock. Not a result. |
| Order lifetime | Yes | Not tested. |
| Whether a specific order was cancelled or filled | Yes | Not tested. |
| Modify events | Yes | Not in the frozen one-second store. Not tested. |
| Order of events inside the second | Yes | Destroyed by the one-second bin. Not tested. |
| Liquidity moving from one price to another | Yes | Not tested. |

So the MBO infrastructure is a different frontier from OHLC and from the closed profile branch. Most of the obvious scalar summaries of that frontier have already been looked at, on 26 mornings from 2026-07-08 through 2026-08-12, 09:30–12:00 New York, and they are economically tiny. The diagnostic report does not call that a multi-year kill. It also does not leave a large residual sitting in those sums.

What the sums cannot represent is the identity of an order: how long it rested, and whether it died by cancel or by fill. That is the only information class in the current data that is both unused and not a rename of a closed hypothesis.

## Directions that are not open

These were considered and set aside.

- Another LVN, POC, value-area, or profile-location rule. Steps 4, 5, and 7 already lost to geometry nulls. Step 6 had no null and is not a positive result.
- Another candle, flag, opening-range, VWAP, or support/resistance parameterization. The inventory's geometry section is the record.
- Another volatility filter in front of a failed entry. 39–41 and 24A/24D closed that use of a supported clustering fact.
- Another external series of the family-23 type. ES, ZN, and COT failed. ZB was not downloaded. The hard stop still applies.
- SPX 0DTE dealer gamma. The pipeline is real and the sample is not. FirmTape blocked the archive. Untested is not a negative, and it is also not testable on the files we have.
- Replaying the same one-second imbalance features on the overnight session. That changes the clock, not the information.

## Remaining directions

Only one direction survives the filter above. A second and third are not listed, because the next-best candidates are either data-blocked or rebrands.

### 1. Order lifetime and cancel-versus-fill fate

1. **Information.** For each resting order at the inside quote, the time from add to exit, and whether the exit was a cancel or a fill. Built from `order_id` on the MBO event stream. Not from a one-second sum.
2. **Why it is different.** H01 and the corrected diagnostic already measured queue size, five-level depth, aggressor imbalance, and per-second add/cancel totals. Those totals can be large because many short-lived orders were added and pulled, or because one order was filled. The lifetime and the fate separate those cases. OHLC, CVD, and a volume profile do not contain this split.
3. **Mechanism that could exist.** A queue that is being cancelled has different information from a queue that is being executed, even when the displayed size change is the same. If that difference does not show up in the subsequent mid, the mechanism is absent in this sample.
4. **Null.** After residualizing on the four aggregates already measured (`obi_1`, 1-second `depth_net_change`, 1-second `trade_imbalance`, 1-second `replenish_net`), the partial rank association is zero. The null is incremental.
5. **Data.** Raw MBO with order ids. The frozen one-second store does not contain lifetime or fate. The 26-session morning window can host the test. It cannot host a multi-year claim.
6. **Falsifier.** Held-out 1-second partial association below 0.02 in absolute value for every prespecified feature, or a sign that disagrees with the discovery block. Confirmatory horizons cannot rescue a failed 1-second cell. No trade is attached.
7. **Infrastructure.** A read-only pass over the frozen replay can emit the events. The engine stays unmodified.

The freeze, including the split between completed-order association and real-time information, is `mbo_orderflow/order_fate/PREREGISTRATION.md`. That file was not changed after the numbers existed.

**Result (2026-09-21):** question verdict `NOT SUPPORTED`. Study P `NOT SUPPORTED`. All four held-out 1-second partial associations were below 0.02 in absolute value. Report: `mbo_orderflow/order_fate/REPORT.md`.

# Recommended Next Research Question

The order-fate information test is closed on this sample.

After controlling for one-second inside imbalance, depth change, trade imbalance, and replenishment, neither resting age / trade exposure while the order is live, nor completed lifetime / fill-versus-cancel after the order ends, cleared the frozen 1-second gate.

That does not authorize another MBO feature search, another lifetime bin, or an execution study of these features. On the information currently testable in this repository, the directional classes examined in the inventory and this order-fate test are exhausted. The honest next step is to stop searching for a standalone directional edge in the existing files, unless a genuinely new data source is introduced.
