# Framework Discovery

**Date:** 2026-09-21  
**Task type:** Research inventory only. No backtest. No strategy code. No profitability claim.  
**Inputs:** `RESEARCH_INVENTORY.md`, `RESEARCH_FRONTIER.md`, closed branch reports, primary/high-quality methodology sources.  
**Closed context:** Isolated directional feature classes in the inventory are exhausted. MBO order-fate (Studies P/R) is `NOT SUPPORTED`. This document does not reopen those branches.

---

## Purpose

The research program is shifting from:

> feature → return

to:

> framework → context → event → reaction → mechanism → falsification

The question answered here is not “what makes money,” but:

> Which established trading frameworks provide a sufficiently explicit market mechanism, contextual decision process, and observable rules that we can independently reconstruct and falsify using data already available in this repository?

---

## Already-tested mechanisms (do not rebrand)

| Closed / exhausted class | Inventory IDs (examples) | Implication for framework search |
| --- | --- | --- |
| Opening-range / IB breakout-fade parameterization | 01, 30, 31, 32, 33 | Do not reinvent OR/IB as a new “framework name.” |
| Overnight / prior-day level accept–reject | 03, 04, 05, 16A/B, 37, 38 | Do not treat Dalton references alone as a new claim. |
| Generic S/R breakout / retest / matched-move | 42, 42b, 15m S/R studies | Zone frameworks must differ by **process**, not by another level band. |
| Compression → break → pullback | 34A, 43, 39 | Not a new range-break story. |
| Activity/vol state as directional resolver | 06–14, 40, 41 | Supported as activity; closed for direction. |
| LVN traverse/reject; prior POC location preference | 47 Steps 4–7 | Profile **geometry** claims closed. AMT process ≠ LVN/POC touch rules. |
| Signed OHLCV as order flow | 27 | VSA must not be smuggled in as signed-volume IC. |
| One-second book/trade imbalance scalars | 44 H01; MBO diagnostic | Footprint/Jigsaw must be full **process**, not another IC feature. |
| Order lifetime / fill-vs-cancel | order_fate P/R | Do not add MBO because MBO exists. |
| ICT SMT | 45 `INCONCLUSIVE` | Do not retrofit SMT. |

---

## What counts as a framework (acceptance filter)

Accepted only if the source documents a sequence resembling:

```text
MARKET STATE
      ↓
LOCATION / CONTEXT
      ↓
EVENT
      ↓
REACTION
      ↓
DECISION
      ↓
EXPECTED MARKET BEHAVIOR
```

Rejected as candidates: EMA/RSI/MACD systems, generic “X above Y,” social-media strategies without reconstructible rules, arbitrary indicator stacks, and profitability marketing.

---

## Candidates researched

Five frameworks received full structured extraction. A sixth adjacent candidate (Seiden Supply/Demand) was reviewed and set aside for contamination risk with closed S/R work; notes appear after the comparison table.

Primary / high-quality sources preferred over blogs:

| Framework | Primary / high-quality sources used |
| --- | --- |
| Auction Market Theory / Market Profile | CBOT *A Six-Part Study Guide to Market Profile*; Steidlmayer & Koy, *Markets and Market Logic*; Steidlmayer, *Steidlmayer on Markets*; Dalton et al., *Markets in Profile* / *Mind Over Markets* lineage |
| Wyckoff | Richard D. Wyckoff course / tape-reading lineage; Wyckoff Analytics method overview (phases, events, laws) |
| Volume Spread Analysis | Tom Williams, *The Undeclared Secrets That Drive the Stock Market* / *Master the Markets* |
| Footprint / bid×ask auction | Documented bid×ask footprint definitions (diagonal imbalance, stacked imbalance, absorption, finished/unfinished auction) as used in established order-flow tooling literature |
| DOM / order-flow reversal process | Peter Davies / Jigsaw Trading educational materials (absorption → aggressor fade → “the roll”) |

---

# Framework 1 — Auction Market Theory / Market Profile

## A. Core market hypothesis

Markets are continuous two-sided auctions whose purpose is to **facilitate trade**. They alternate between **imbalance** (directional discovery seeking an opposite response) and **balance** (two-sided trade around an accepted fair price / value). Price advertises opportunity; time and volume measure acceptance or rejection of that advertisement.

## B. Market state

Documented distinctions include:

- **Balance** — roughly equal buying and selling; rotation around a fair price.
- **Imbalance** — one side predominant; directional auction seeking opposite response.
- **Day-structure / range-development types** (Steidlmayer/CBOT lineage): Normal, Normal Variation, Trend, Neutral (and later Dalton elaborations such as double-distribution trend / non-trend).
- **Control** — short-term (local) vs longer-term (“other time frame”) participant influence, often inferred from initial balance vs range extension.
- **Acceptance vs rejection** of price — high time/volume = acceptance; excess / single prints / low time = rejection.

## C. Context / location

**Essential**

- Prior session value / prior auction range (value area, prior high/low, overnight inventory as references).
- Developing auction: Initial Balance (period in which two-sided trade first forms), current range, extremes.
- Location of price relative to prior and developing value (above / in / below value).

**Optional tools (not the mechanism itself)**

- TPO letter profile, volume value area, Liquidity Data Bank, day-type labels as summaries.

## D. Event

Examples documented in the methodology:

- Open relative to prior value / overnight references.
- **Opening type** (Dalton): Open-Drive, Open-Test-Drive, Open-Rejection-Reverse, Open-Auction.
- Range extension beyond Initial Balance (initiative longer-term activity).
- Attempt to auction outside value / prior extremes (**failed auction** candidate).
- Formation of excess / single-print extremes.

## E. Reaction

AMT has a strong reaction concept:

- **Acceptance** outside prior value → continued imbalance / migration of value.
- **Rejection / failed auction** → return toward previously accepted value.
- Initiative activity that fails to attract follow-through → responsive inventory correction.
- Successful range extension → adjusted balance at new levels (Normal Variation) or sustained imbalance (Trend).

If only “touch prior POC/LVN” is observed without acceptance/rejection language, that is **not** full AMT; it is the closed profile-geometry branch.

## F. Decision logic (observability)

| Condition | Classification |
| --- | --- |
| Prior RTH/Globex high, low, close, midpoint | objectively measurable |
| Initial Balance high/low over a fixed clock window | objectively measurable once IB duration is frozen |
| Value area (TPO 70% or volume VA) | measurable but requires explicit operational definition |
| Open-Drive vs Open-Auction classification | measurable but requires explicit operational definition |
| “Other time frame” conviction | inherently discretionary |
| Failed auction = leave value + fail to attract sustained trade + reverse | measurable but requires explicit operational definition |
| Exact discretionary day-type call mid-session | inherently discretionary |

## G. Expected mechanism

> If price attempts to establish trade away from a previously accepted value area and fails to attract sustained two-sided acceptance (or fails to continue after initiative extension), the auction should return toward the previously accepted area. If initiative activity successfully attracts like response and range extension persists, value should migrate in the initiative direction.

Hypothesis only — not a result.

## Data feasibility

| Class | Status |
| --- | --- |
| Available | NQ/ES 1-minute OHLC (~2010–2026); session clocks; volume per bar; overnight/RTH splits |
| Reconstructable | IB; day types from IB vs range extension; TPO-style profiles from 30m brackets; volume value area from trades or bar volume; opening-type classifiers once rules are frozen |
| Missing | Live pit “other time frame” identity; true LDB-style volume-by-price for full multi-year history at original CBOT resolution (trade-built profiles exist only on shorter recent windows) |

## Discretion audit

**Score: 2**

- IB clock length, value-area algorithm, and opening-type thresholds are operational ambiguities (formalizable).
- Mid-session judgment of “who is in control” and qualitative initiative/responsive reading remain substantial.
- Not score 3 if the study freezes IB window, VA definition, and opening-type rules before any outcome look.

## Falsifiability test

| Question | Answer |
| --- | --- |
| 1. State before looking forward? | Yes, if IB/value/open type use only information known at label time. |
| 2. Event without future information? | Yes for open type / IB break / leave-value events with frozen clocks. |
| 3. Reaction without lookahead? | Yes if acceptance/rejection windows are fixed ex ante. |
| 4. Counterfactual/null? | Yes (e.g., matched leave-value events without failure criteria; shuffle of day-type labels; geometry nulls). |
| 5. Measurable outcome? | Yes (return-to-value, range extension persistence, day-type path stats). |
| 6. Chronological discovery/validation/OOS? | Yes on multi-year 1m panel. |
| 7. Independent reproduction from source? | Partially — sources are coherent but leave judgment; operational freeze is mandatory. |

## Relation to closed work

High contamination risk. IB continuation/fade (30/33), overnight accept/reject (03), opening-auction information (38), and LVN/POC geometry (47) already tested **pieces**. Any AMT preregistration must test a **documented process sequence** (e.g., opening type → developing balance/imbalance → failed auction reaction), not another isolated reference touch.

---

# Framework 2 — Wyckoff Method

## A. Core market hypothesis

Price is the result of the law of **supply and demand**, organized as if by a **Composite Operator**: large interests accumulate or distribute within trading ranges (building a **cause**), then mark price up or down (the **effect**). Effort (volume) that fails to produce result (progress) warns of absorption or exhaustion.

## B. Market state

Documented states / phases:

- **Trading range (TR)** vs **trending** (markup / markdown).
- **Accumulation / re-accumulation** vs **distribution / re-distribution**.
- Phases **A–E** within schematics (stop of prior trend → building cause → test → sign of strength/weakness → leave TR).
- Relative equilibrium of supply and demand inside the TR.

## C. Context / location

**Essential**

- Identified trading-range boundaries after stopping action.
- Position within the schematic (early vs late TR).
- Volume behavior on rallies vs reactions (supply/demand character).

**Optional**

- Point & Figure cause counts for targets.
- Comparative/relative strength across instruments (stock-centric in originals; ES available here as sibling).

## D. Event

Canonical events include:

- Preliminary Support / Selling Climax / Automatic Rally / Secondary Test (accumulation).
- **Spring** / terminal shakeout (false break below TR support that returns into the range).
- **Upthrust** / UTAD (false break above TR resistance that returns into the range).
- Sign of Strength (SOS) / Sign of Weakness (SOW).
- Last Point of Support / Supply; Backup / “jump across the creek.”

## E. Reaction

Wyckoff’s reaction concept is explicit:

- After a spring: successful **test** on reduced volume / narrower spread → readiness for markup.
- After SOS: backup that holds → continuation of markup.
- Failed test (supply returns) → not ready; remain in TR or revise interpretation.
- Effort vs result divergences during climaxes → transfer of inventory, then opposite campaign.

## F. Decision logic (observability)

| Condition | Classification |
| --- | --- |
| Local swing high/low TR box over a frozen lookback | measurable but requires explicit operational definition |
| Spring = break below TR low then close back inside within N bars | measurable but requires explicit operational definition |
| Volume diminution on test vs climax | measurable but requires explicit operational definition (relative volume baseline) |
| Phase A–E labeling | inherently discretionary (can be partially formalized with event grammar) |
| “Composite Operator intent” | inherently discretionary |
| P&F horizontal count targets | measurable but requires explicit operational definition |

## G. Expected mechanism

> After supply has been absorbed in an accumulation trading range, a late false break below support (spring) that fails to attract sustained selling—and is confirmed by a lower-volume test—should precede a markup that leaves the range. The symmetric claim holds for distribution and upthrusts.

Hypothesis only.

## Data feasibility

| Class | Status |
| --- | --- |
| Available | Multi-year NQ (and ES) OHLC + bar volume; session structure |
| Reconstructable | TR boxes; springs/upthrusts; relative volume; effort–result bar flags; SOS/SOW proxies from spread×volume |
| Missing | True tape of specialist/operator orders from Wyckoff’s era; stock-float / issue-specific operator campaigns (futures are a different microstructure). Comparative strength across many equities not required for an NQ-only process test |

## Discretion audit

**Score: 2**

- Springs/upthrusts can be made objective once TR construction is frozen.
- Phase narratives and “campaign readiness” remain the main discretion.
- Score would become 3 if the study requires human schematic labeling without frozen event grammar.

## Falsifiability test

| Question | Answer |
| --- | --- |
| 1. State before looking forward? | Yes if TR is defined from data available before the spring/upthrust. |
| 2. Event without future information? | Yes for spring/upthrust with frozen break-and-return rules. |
| 3. Reaction without lookahead? | Yes for confirmatory test window fixed ex ante. |
| 4. Counterfactual/null? | Yes (false breaks without prior TR/phase constraints; matched breakouts that hold; volume-matched controls). |
| 5. Measurable outcome? | Yes (leave-range success, follow-through after confirmatory test). |
| 6. Chronological splits? | Yes on multi-year panel. |
| 7. Independent reproduction? | Yes at event-grammar level; full schematic storytelling is harder. |

## Relation to closed work

Related to, but not identical with, failed support/resistance breaks (15m downside-break failure `NOT SUPPORTED`). Those tests matched ordinary down closes **without** requiring a prior accumulation TR, climax/test sequence, and confirmatory low-volume retest. Wyckoff’s claim is the **campaign process**, not “any support break bounces.”

---

# Framework 3 — Volume Spread Analysis (VSA)

## A. Core market hypothesis

Price moves because of imbalances between supply and demand created by professional / “smart money” activity. That activity is readable from the **relationship of volume, price spread (high–low), and close location**, not from volume alone.

## B. Market state

Documented qualitative states:

- Strength vs weakness entering the market.
- Trends / trading ranges as background.
- Climactic vs non-climactic conditions (buying/selling climax language shared with Wyckoff lineage).
- “Locked in” markets vs markets offering path of least resistance.

## C. Context / location

**Essential**

- Recent relative volume and relative spread (vs neighboring bars).
- Close position within the bar.
- Background: proximity to prior resistance/support or trend context in Williams’ examples.

**Optional**

- Proprietary TradeGuider / VSA software indicators (not required to test the written principles).
- Multi-market confirmation (indices vs stocks) as discussed in the books.

## D. Event

Named indications include:

- **No Demand** — up-bar, narrow spread, low volume.
- **No Supply** — down-bar, narrow spread, low volume.
- **Up-thrust** — probe above resistance / highs that fails, often with characteristic volume/spread.
- Stopping volume / climactic action.
- Tests of supply after strength indications.
- Effort vs result: wide effort with little progress, or narrow spread on high volume into highs.

## E. Reaction

VSA expects confirmation after the indication:

- After weakness indications (e.g., up-thrust, no demand near highs): subsequent bars should show inability to rally / path of least resistance down.
- After strength (stopping volume, successful test): subsequent bars should show demand / upward path.
- Isolated bars without background and follow-through are treated as incomplete reads in the source material.

## F. Decision logic (observability)

| Condition | Classification |
| --- | --- |
| Bar high, low, close, volume | objectively measurable |
| Relative volume vs trailing window | measurable but requires explicit operational definition |
| Narrow/wide spread vs trailing distribution | measurable but requires explicit operational definition |
| Close in upper/lower fraction of bar | objectively measurable once fraction is frozen |
| “Professional” attribution | inherently discretionary |
| Background “near resistance” without frozen rule | inherently discretionary |

## G. Expected mechanism

> When professional supply is absorbed or distributed, it appears as characteristic mismatches between effort (volume) and result (spread/progress). After a validated weakness (or strength) indication in context, subsequent price should follow the implied path of least resistance.

Hypothesis only.

## Data feasibility

| Class | Status |
| --- | --- |
| Available | Full multi-year 1m/session OHLC volume on NQ (and ES) |
| Reconstructable | Relative volume/spread/close-location grammars; sequence rules (indication → next-bar confirmation) |
| Missing | True downstairs specialist tape Williams describes; proprietary software signal stream |

## Discretion audit

**Score: 2**

- Bar grammar is formalizable.
- “Background” and narrative professional intent are the discretion centers.
- Must not silently replace VSA with signed-volume IC (already killed in 27).

## Falsifiability test

| Question | Answer |
| --- | --- |
| 1. State before looking forward? | Yes for relative volume/spread state at bar close. |
| 2. Event without future information? | Yes for frozen bar patterns. |
| 3. Reaction without lookahead? | Yes for fixed confirmation horizon. |
| 4. Null? | Yes (pattern without volume condition; volume without spread condition; shuffled volumes). |
| 5. Outcome measurable? | Yes. |
| 6. Chronological splits? | Yes. |
| 7. Independent reproduction? | Partially — books give many examples; exact numeric cuts are not unique in the text. |

## Relation to closed work

Distinct from Strategy 27’s signed-volume proxy. Overlaps thematically with “high volume, little progress” absorption language (H03 still `NOT TESTED` on a valid MBO clock). A VSA study must stay on **documented bar effort–result sequences**, not reopen scalar order-flow IC mining.

---

# Framework 4 — Footprint / Bid×Ask Auction Methodology

## A. Core market hypothesis

Within each time bar, the market auctions level by level. Aggressive buyers lift offers; aggressive sellers hit bids. Whether aggression is **rewarded** (price advances) or **absorbed** (heavy aggression, little progress) is visible in the bid×ask volume ladder, not in the OHLC candle alone.

## B. Market state

Common documented states:

- Initiative imbalance vs balanced two-sided trade at a price.
- Absorption regimes (aggression present, progress denied).
- Finished vs unfinished auctions at bar extremes.
- Local support/resistance implied by stacked imbalances.

## C. Context / location

**Essential**

- Price level inside the bar.
- Structural location (session extreme, prior level, range boundary) in most practitioner presentations.

**Optional**

- Volume profile / VA overlays (do **not** add these because profiles were collected; only if the chosen source requires them).
- DOM resting size (belongs more to Framework 5).

## D. Event

Documented event classes:

- **Diagonal imbalance** at a price (ask at P vs bid at P−1 tick, typically ≥3:1 or similar configured ratio).
- **Stacked imbalances** (multiple consecutive imbalance prices).
- **Absorption** prints (anomalous volume at a level / extreme with failed progress).
- **Unfinished auction** (both bid and ask nonzero at the bar extreme) vs **finished auction** (zero opposing volume at the extreme).

## E. Reaction

Explicit reaction language:

- Stacked imbalance often expected to act as support/resistance on revisit.
- Absorption at a meaningful location → aggressor exhaustion → reversal or stalled continuation.
- Unfinished extreme → magnet / revisit to “complete” the auction.
- Finished extreme → less unfinished business at that edge.

## F. Decision logic (observability)

| Condition | Classification |
| --- | --- |
| Trade volume classified buy (at ask) / sell (at bid) | reconstructable from tick/MBO aggressor rules |
| Diagonal imbalance ratio ≥ R | objectively measurable once R and min volume are frozen |
| Stacked count ≥ K | objectively measurable once K is frozen |
| Absorption = size + failed progress + rejection wick | measurable but requires explicit operational definition |
| “Meaningful location” filter | inherently discretionary unless replaced by frozen references |
| Exact 3:1 industry default | measurable but requires explicit operational definition (threshold choice) |

## G. Expected mechanism

> When aggressive flow dominates diagonally across consecutive prices, that initiative should leave a footprint of acceptance in that direction; when aggressive flow is large but price cannot progress (absorption), or when an extreme remains unfinished, subsequent auction should revisit or reverse from that condition.

Hypothesis only.

## Data feasibility

| Class | Status |
| --- | --- |
| Available | Recent trade prints (strategy 47 window ~months); MBO/order-book reconstruction (~26 RTH mornings in the frozen store) |
| Reconstructable | Bid×ask ladders; delta; imbalances; unfinished extremes; absorption proxies from aggressor volume vs mid change |
| Missing | Multi-year footprint history at tick resolution for full IS/Val/OOS comparable to the OHLC panel |

## Discretion audit

**Score: 2**

- Ladder geometry is highly formalizable.
- Location filters and absorption thresholds retain discretion.
- Sample length, not theory, is the binding constraint for chronological OOS.

## Falsifiability test

| Question | Answer |
| --- | --- |
| 1. State before looking forward? | Yes for completed bars / completed levels. |
| 2. Event without future information? | Yes. |
| 3. Reaction without lookahead? | Yes with fixed horizons. |
| 4. Null? | Yes (ratio-matched random levels; unfinished vs finished controls). |
| 5. Outcome measurable? | Yes. |
| 6. Chronological discovery/validation/OOS? | **Weak** on current tick/MBO span; multi-year OOS Needs longer tick history than the frozen 26-session morning store. |
| 7. Independent reproduction? | Yes for core ladder definitions; practitioner overlays vary. |

## Relation to closed work

Not the same object as H01 depth imbalance or one-second trade-imbalance IC. Still adjacent: aggressive delta diagnostics were tiny on the corrected clock, and H03 absorption was never completed on a valid clock. A footprint preregistration would be a **process** test (imbalance/absorption/unfinished → reaction), not an authorization to resume scalar MBO feature search.

---

# Framework 5 — DOM / Order-Flow Reversal Process (Jigsaw lineage)

## A. Core market hypothesis

In the ultra-short term, price moves when market orders consume resting liquidity. Reversals occur when aggressive flow **fails to consume** liquidity (absorption), aggressors **give up**, and/or opposite aggressors **appear** (“the roll”). Order flow shows **current intent** at the touch, beyond what candles show.

## B. Market state

Documented distinctions:

- Absorption / iceberg-like replenishment vs thin liquidity.
- Aggressor persistence vs fade.
- Vacuum / thin opposite liquidity after a one-way move.
- Context extremes: session extremes, temporary value, defended high-volume areas, stop-run areas (as location filters in the materials).

## C. Context / location

**Essential (per the materials)**

- A **meaningful location** (extremes / defended areas). Absorption without location is explicitly warned against.

**Essential data objects**

- Executed tape (trades at bid/ask).
- Resting depth behavior (offers/bids holding, pulling, replenishing).

## D. Event

Reversal components (long-to-short example):

1. **Absorption** — offers stay firm despite continued buying; delta rises, price does not.
2. **Buyers fade** — repeated failure to hit the offer.
3. **The roll** — sellers appear and dominate trades at the bid.

These are not mutually exclusive.

## E. Reaction

The framework’s decision is reaction-centered:

- After absorption at location: wait for fade and/or opposing aggression before treating the reversal as confirmed.
- Less aggressive variants: wait for reclaim through the absorption cluster / retest.
- Continued aggressive selling through a “bid wall” → absorption failed; do not fade mechanically.

## F. Decision logic (observability)

| Condition | Classification |
| --- | --- |
| Aggressor volume vs mid change over a short window | measurable but requires explicit operational definition |
| Depth replenishment while being hit (iceberg proxy) | reconstructable from MBO order_id behavior |
| Repeated failed touches of same price | measurable but requires explicit operational definition |
| “The roll” = opposite aggressor dominance after stall | measurable but requires explicit operational definition |
| “Meaningful location” | inherently discretionary unless frozen |
| Real-time trader judgment of pace/“feel” | inherently discretionary |

## G. Expected mechanism

> At a meaningful location, if aggressive buying (selling) is absorbed by persistent opposing liquidity and aggressors then fade or reverse, price should reverse because the consuming side can no longer advance the auction.

Hypothesis only.

## Data feasibility

| Class | Status |
| --- | --- |
| Available | MBO with order ids (add/cancel/modify/fill) on the research window; reconstructed top-of-book/depth |
| Reconstructable | Absorption sequences; replenishment; aggressor fade; roll proxies |
| Missing | Multi-year DOM history; trader visual “pace” judgment; guaranteed iceberg labels (only proxies) |

## Discretion audit

**Score: 3** (as practiced) / **2** (if fully formalized)

- Educational materials emphasize discretion, location, and non-mechanical use.
- A frozen sequence grammar could reduce this to 2, but reproducing the **documented practice** without that freeze is fundamentally discretionary.

## Falsifiability test

| Question | Answer |
| --- | --- |
| 1. State before looking forward? | Only after location and absorption windows are frozen. |
| 2. Event without future information? | Yes if absorption is defined on past/current book+tape only. |
| 3. Reaction without lookahead? | Yes for fade/roll windows fixed ex ante. |
| 4. Null? | Yes (absorption-sized prints away from location; depth holds without aggressor fade). |
| 5. Outcome measurable? | Yes. |
| 6. Chronological multi-year OOS? | **No** with current MBO span alone. |
| 7. Independent reproduction? | Partial — process is documented; thresholds are not unique. |

## Relation to closed work

Closest open relative is H03 absorption (`NOT TESTED` on a valid clock). Frontier guidance forbids another MBO **feature search**; a formal Jigsaw-style **sequence** study would still consume the same short sample and risks becoming that search under a new name.

---

# Adjacent candidate reviewed and not advanced

## Supply & Demand zones (Sam Seiden / patent US8650115B1)

- **Mechanism:** Origin of a strong departure from a compact base marks an imbalance zone (DBR/RBR demand; RBD/DBD supply). First return to proximal/distal zone is the event; expected reaction is rejection from the zone.
- **Why not advanced as a primary candidate:** Highly explicit and OHLC-feasible, but the operational object is a **zone + return**, which is adjacent to the closed generic S/R / matched-move family (42, 15m studies). Elevating it would require an unusually strong differentiation argument (freshness, departure R-multiple rules, first-touch-only) that still risks being read as a rebrand.
- **Discretion:** 1–2 if proximal/distal rules follow the patent; still a contamination risk.

---

# 10. Framework comparison

| Framework | Core mechanism | Context | Event | Reaction | Data coverage | Discretion 0–3 | Falsifiable? |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| AMT / Market Profile | Balance↔imbalance auction; facilitate trade | Prior/developing value, IB, references | Open type; leave value; IB extension; failed auction | Acceptance vs rejection; return to value or migrate | Strong on multi-year OHLC; VA/TPO reconstructable; full LDB-like history limited | 2 | Yes, with frozen ops; **high overlap with closed tests** |
| Wyckoff | Composite Operator campaigns; cause→effect in TRs | TR phase / supply–demand character | Spring/upthrust; climax; SOS/SOW; test | Confirmatory low-effort test; leave TR in campaign direction | Strong on multi-year OHLC+volume | 2 | Yes, if event grammar frozen |
| VSA | Effort (volume) vs result (spread/close) reveals professional imbalance | Relative volume/spread background | No demand/supply; up-thrust; stopping volume; tests | Follow-through along path of least resistance | Strong on multi-year OHLC+volume | 2 | Yes, with frozen bar grammar; thresholds not unique in texts |
| Footprint bid×ask auction | Aggression rewarded vs absorbed at price levels | Bar ladder ± structural location | Diagonal/stacked imbalance; absorption; unfinished extreme | Hold as S/R; reverse; revisit unfinished | Reconstructable on recent trades/MBO; **weak multi-year OOS** | 2 | Yes on short sample; weak long OOS |
| Jigsaw DOM reversal process | Absorb → fade → roll at meaningful location | Extremes / defended areas + book | Absorption; failed hits; opposing aggression | Confirmed reversal after sequence | MBO window only; multi-year OOS missing | 2–3 | Conditionally; sample-bound |

No profitability ranking. This is feasibility only.

---

# 11. Anti-overfitting compliance notes

- No MBO features were added because MBO is available.
- No Volume Profile / LVN / POC claims were revived because those files exist.
- No SMT retrofit from Strategy 45.
- No ATR/vol filter grafted on to “improve” a framework.
- Frameworks were recovered from documentation first; operationalization notes come after.
- Closed IB/OR/S/R/profile/order-fate branches are marked as contamination hazards, not as templates to tweak.

---

# 12. Final frontier recommendation

## Shortlist (at most three)

1. **Wyckoff trading-range campaign process** (spring/upthrust + confirmatory test → leave-range behavior)  
   - Documented context→event→reaction.  
   - Multi-year observability.  
   - Materially different from isolated failed-break tests because of required prior TR/campaign structure.

2. **VSA effort-versus-result bar sequences**  
   - Explicit mechanism in Williams’ primary texts.  
   - Multi-year observability.  
   - Distinct from signed-volume IC (27), but needs strict separation from absorption feature-mining.

3. **AMT failed-auction / opening-type → developing auction process**  
   - Strongest classical mechanism documentation.  
   - Multi-year observability.  
   - Ranked third because of heavy overlap with already-tested IB, open, level, and profile fragments; only a full process preregistration that forbids isolated reference-touch endpoints would stay honest.

Footprint and Jigsaw remain coherent frameworks but are **sample-constrained** on this repository’s tick/MBO history and sit next to exhausted/near-zero microstructure scalar tests. They are not selected for the immediate shortlist.

## Proposed next preregistration (one)

> The next framework recommended for formal preregistration is **Wyckoff** (specifically the documented trading-range campaign process culminating in spring/upthrust, confirmatory test, and subsequent leave-range behavior) because its documented mechanism is sufficiently explicit, its key variables are observable/reconstructable in our multi-year OHLC+volume data, and it represents a materially different hypothesis from the mechanisms already tested.

This is **not** a claim that Wyckoff works.  
This is **not** a backtest.  
This is **not** an entry/exit rule set.

A later preregistration would need to freeze, before any outcome look:

- trading-range construction,
- spring/upthrust event grammar,
- confirmatory-test definition,
- outcome horizon and null,
- chronological discovery / validation / OOS splits.

---

## Explicit non-actions (this task)

- No forward returns calculated.
- No thresholds optimized.
- No Sharpe / profit factor.
- No strategy code.
- No modification of existing research branches.
- No declaration that any framework is profitable.

---

## Source bibliography (for later reconstruction)

1. Chicago Board of Trade — *A Six-Part Study Guide to Market Profile*.
2. J. Peter Steidlmayer & Kevin Koy — *Markets and Market Logic*.
3. J. Peter Steidlmayer — *Steidlmayer on Markets* (Market Profile editions).
4. James F. Dalton et al. — *Markets in Profile*; *Mind Over Markets* lineage (opening types, day development).
5. Richard D. Wyckoff — course / method of tape reading and investing in stocks (1930s lineage).
6. Wyckoff Analytics — method overview (laws, phases, events, schematics).
7. Tom Williams — *The Undeclared Secrets That Drive the Stock Market*; *Master the Markets* (VSA).
8. Established footprint methodology documentation — diagonal imbalance, stacked imbalance, absorption, finished/unfinished auctions.
9. Peter Davies / Jigsaw Trading — order-flow education materials on absorption, fade, and roll.
10. US Patent US8650115B1 — supply/demand zone proximal/distal construction (adjacent candidate only).
