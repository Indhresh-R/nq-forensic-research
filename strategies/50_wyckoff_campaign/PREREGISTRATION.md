# Preregistration — 50 Wyckoff trading-range campaign process

**Status:** FROZEN BEFORE OUTCOME ANALYSIS (Step 1 complete).  
**Label:** Mechanism research only. Not an executable strategy. No entries, exits, stops, targets, or friction model.  
**Companion:** `WYCKOFF_SOURCE_MAP.md`  
**Namespace note:** Draft path `48_wyckoff_campaign` was requested; ID **50** is used because `48_daily_candle_continuation` already exists.

No NQ event scan, event count, forward return, win rate, or P&L may be computed under this file until a separate Step 2 implementation note is opened. Definitions below must not be edited after any outcome table exists.

---

## Question

Does the **complete Wyckoff sequence**

```text
qualifying trading range
  → terminal false break (spring or upthrust)
  → return into the range
  → confirmatory test
```

exhibit subsequent **leave-range / auction behavior** that differs from appropriate controls that lack the full context and confirmation?

This is **not**:

- “spring = bullish”
- “upthrust = bearish”
- “failed break of a level predicts reversal”
- a trading-system authorization

### Causal hypothesis (mechanism only)

> A terminal boundary event occurring within a qualifying trading-range campaign and followed by the specified confirmatory behavior may have different subsequent auction behavior from ordinary false breaks lacking the full Wyckoff context/sequence.

---

## Data

| Item | Freeze |
| --- | --- |
| Instrument | Continuous NQ futures |
| Source file | `data/nq_1m_continuous.parquet` via `common.nq_session.load_nq` (read-only) |
| Clock | `America/New_York` |
| Session | Globex `session_date` as in `common.nq_session` (roll at 18:00 ET) |
| Working bar | **15-minute** bars aggregated from 1-minute bars, aligned from 18:00 ET |
| Volume | Sum of 1-minute volumes inside each 15-minute bar |
| Spreads | `high − low` of the 15-minute bar |
| ES | Not required for the primary NQ process test |

Incomplete Globex sessions follow the completeness conventions already used by Strategies 46/48/49 when session-level pairing is needed. The TR process itself runs on the continuous 15-minute series; a range may span session boundaries.

---

## Chronological splits

Reuse `common.splits` exactly:

| Sample | Calendar years of the **event’s sequence-completion** `session_date` year |
| --- | --- |
| Discovery / IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

No shuffling. No mixing future years into discovery. OOS must not revise any rule below.

If Step 2 finds IS event counts too small for the frozen grammar, that fact is reported as a **power failure**, not a license to retune definitions using Validation/OOS.

---

## Composite Operator rule

**Forbidden as measurable variables:**

- “smart money is accumulating / distributing”
- “Composite Operator intent”
- “institutions are absorbing supply”

These are interpretive narratives. Only observable price/volume/time constructions below are allowed.

---

## Stage A — Qualifying trading range (market state)

### Source grounding

Wyckoff Analytics (S2): a trading range is where the prior trend has halted and relative equilibrium exists; support/resistance emerge from the structure (classically SC/ST lows and AR high). Springs occur relative to **already established** TR support.

This study does **not** require naming PS/SC/AR/ST (discretionary). It requires a causal box with repeated reactions.

### Bar and pivot definitions (`RESEARCHER-DEFINED`)

On the completed 15-minute series, index bars `0…T` in time order.

A bar `i` is a **confirmed swing low** at the first bar `i+L` when:

- `L = 2`
- `low[i] = min(low[i-L], …, low[i+L])`
- all bars through `i+L` are complete

A bar `i` is a **confirmed swing high** symmetrically on `high`.

Confirmation time of that swing is the close of bar `i+L`. No future bars beyond `i+L` are used.

### Range construction (`SOURCE-INSPIRED ADAPTATION` + numeric freezes `RESEARCHER-DEFINED`)

A **candidate support set** is the most recent two confirmed swing lows `SL1` (earlier) and `SL2` (later) such that:

```text
abs(low[SL1] - low[SL2]) <= 0.25 * ATR20[t_elig]
```

where `ATR20` is the 20-bar average true range of 15-minute bars using only bars ≤ the eligibility bar, and `t_elig` is defined below.

A **candidate resistance set** is the most recent two confirmed swing highs `SH1`, `SH2` in the same interval spanning `SL1…SL2` (or the minimal interval covering both pairs) such that:

```text
abs(high[SH1] - high[SH2]) <= 0.25 * ATR20[t_elig]
```

and at least one of `SH1`,`SH2` occurs **after** `SL1` and at least one of `SL1`,`SL2` occurs **after** `SH1` in calendar time (the box must show **two-sided** reaction, not a one-sided staircase).

**Boundaries at eligibility:**

```text
TR_low  = min(low[SL1], low[SL2])
TR_high = max(high[SH1], high[SH2])
TR_mid  = 0.5 * (TR_low + TR_high)
TR_height = TR_high - TR_low
```

### Eligibility (`RESEARCHER-DEFINED`)

The TR becomes **eligible** at the confirmation time of the **later** of the four pivots `{SL1,SL2,SH1,SH2}`, call it `t_TR_eligible`, only if all hold:

1. `TR_height >= 0.75 * ATR20[t_TR_eligible]`
2. Number of completed 15-minute bars from the earliest of the four pivots to `t_TR_eligible` is **≥ 12** (minimum development / cause-building proxy; 3 hours of 15m bars)
3. During that interval, price has printed at least one bar with `low <= TR_low + 0.15*TR_height` and at least one bar with `high >= TR_high - 0.15*TR_height` **in addition to** the defining pivots’ own bars (re-visit / use of both sides)
4. No **acceptance break** (defined below) of either boundary has already occurred between the earliest pivot and `t_TR_eligible`

If any condition fails, no TR is declared from that pivot set. Search continues causally with newer pivots. No hindsight redraw of past boundaries after later extrema.

### Boundary freeze

Once eligible, `TR_low` and `TR_high` are **frozen** for that TR instance. They do not expand to later swing extremes. (Allowing expansion would recreate lookahead-friendly “the real range.”)

### Invalidation of a TR (`SOURCE-INSPIRED ADAPTATION`)

After eligibility, the TR is **invalidated** (no longer eligible for new springs/upthrusts) when either:

- **Acceptance below:** a 15-minute bar **closes** `< TR_low` and the next **3** completed 15-minute bars also all close `< TR_low`, or
- **Acceptance above:** mirrored with closes `> TR_high` for 4 consecutive closes (1 + 3),

**unless** that excursion is currently inside an open spring/upthrust recovery window (Stage C), in which case Stage C rules govern first.

A TR may also be superseded when a **new** TR becomes eligible with `t_TR_eligible` strictly later; the old TR stops accepting new terminal events at the new TR’s eligibility time.

### Accumulation vs distribution label

**Not assigned** before outcomes. The same eligible TR may host springs and/or upthrusts. Campaign direction is implied only by the completed sequence type (spring sequence → upside leave hypothesis; upthrust sequence → downside leave hypothesis).

---

## Stage B — Location

Terminal events are defined **only** relative to an eligible, non-invalidated TR’s frozen `TR_low` / `TR_high`.

Events that break a floating 20-bar high/low **without** an eligible TR are Control A material, not treatment.

---

## Stage C — Terminal event (spring / upthrust)

### Source grounding

S2: a spring “takes price below the low of the TR and then reverses to close within the TR.” UT/UTAD is the upside mirror. Springs usually occur **late** within a TR; they are not required in every schematic.

### Late-TR filter (`SOURCE-INSPIRED ADAPTATION` + `RESEARCHER-DEFINED`)

A terminal event may start only if:

```text
bars_since_eligibility = index(t_start) - index(t_TR_eligible) >= 8
```

(8 fifteen-minute bars ≈ 2 hours after eligibility; proxy for not treating the first touch of a newborn box as a “Phase C” spring.)

### Spring event grammar

Let `TR` be eligible and not invalidated.

1. **Qualifying TR already exists** at the bar before the violation.
2. **Violation start** `t_viol`: first 15-minute bar with `low < TR_low`.
3. **Minimum violation** (`RESEARCHER-DEFINED`):  
   `TR_low - low[t_viol] >= max(0.25 point, 0.05 * TR_height)`  
   (more than a trivial tick nick relative to range height; 0.25 is one NQ tick).
4. **Spring extreme** `E_spring = min(low)` over bars from `t_viol` through recovery (inclusive).
5. **Return into the range** (`SOURCE-EXPLICIT` close-back-in-range + freeze):  
   first later bar `t_return` with `close >= TR_low`, and `t_return` occurs within **`R_max = 6`** completed 15-minute bars after `t_viol` (inclusive of `t_viol` as bar 0 → bars 0…5).  
   “Quickly” is source language; **6 bars (90 minutes)** is `RESEARCHER-DEFINED`.
6. **Invalidation of this spring candidate** if any of:
   - no `t_return` within `R_max`
   - before `t_return`, four consecutive closes remain `< TR_low` (acceptance path → may invalidate TR)
   - `E_spring < TR_low - 1.00 * TR_height` (excursion larger than the entire prior range height — treated as range failure, not a spring)
7. **Spring detected timestamp** `t_spring_event = t_return`  
   (return is required; violation alone is not the event).

### Upthrust / UTAD-type event grammar (exact mirror)

1. Eligible TR exists.
2. `t_viol`: first bar with `high > TR_high`.
3. Minimum violation: `high[t_viol] - TR_high >= max(0.25, 0.05 * TR_height)`.
4. `E_upthrust = max(high)` over violation through recovery.
5. Return: first `t_return` with `close <= TR_high` within `R_max = 6` bars.
6. Invalidation mirrored (four consecutive closes `> TR_high`; or `E_upthrust > TR_high + 1.00 * TR_height`).
7. `t_upthrust_event = t_return`.

### Duplicate / overlapping terminal events

- From a given TR, each completed spring (unique `t_return`) is a separate **terminal-event observation**.
- A new spring cannot start until the prior spring’s confirmation window has ended or failed (see Stage D).
- The same TR may produce both springs and upthrusts over its life.
- If violation bars overlap two TRs, assign the event to the **oldest still-eligible** TR whose boundary was violated.

---

## Stage D — Confirmatory test

### Source grounding

S2: a spring is often followed by one or more tests; a **successful** test typically makes a **higher low on lesser volume**.  
S4: successful tests show higher bottom than the spring, lower average volume than the approach/spring development, preferably narrower spreads; failed tests often make a lower low and/or higher volume.

**Returning into the range is Stage C, not confirmation.**

### Confirmation window (`RESEARCHER-DEFINED`)

After `t_spring_event` (or `t_upthrust_event`), search bars `t_spring_event+1 … t_spring_event+W` with:

```text
W = 12   # 12 fifteen-minute bars = 3 hours
```

### Spring confirmation — primary grammar (frozen)

Define:

- **Spring excursion bars:** `t_viol … t_return` inclusive.  
  `V_spring = mean(volume)` on those bars.  
  `E_spring` as above.

- **Post-event rally segment:** from `t_return` forward, the first run of bars that stays with `low >= TR_low` until a pullback begins.

- **Test pullback:** the first subsequent swing-low confirmation (same `L=2` rule) whose low is ≤ `TR_mid` (pullback reaches at least the lower half of the range), occurring at confirmation time `t_test_pivot` ≤ `t_spring_event + W`.

**Successful confirmation** at `t_confirm = t_test_pivot` if and only if all hold:

| # | Condition | Class |
| --- | ---: | --- |
| D1 | `low[t_test_pivot] > E_spring` (higher low than spring extreme) | `SOURCE-EXPLICIT` |
| D2 | `mean(volume on the test pullback bars) < V_spring` (lesser volume than spring excursion) | `SOURCE-EXPLICIT` |
| D3 | No 15-minute **close** `< TR_low` between `t_return` and `t_confirm` | `SOURCE-INSPIRED` (respect sprung support) |
| D4 | `t_confirm` within `W` bars of `t_spring_event` | `RESEARCHER-DEFINED` |

**Test pullback bars** for D2: from the bar after the highest high between `t_return` and the test pivot, through the test pivot bar (the declining segment into the test). If that set is empty, use the three bars ending at `t_test_pivot`.

**Failed confirmation** (Control B material for this TR event):

- a test pivot occurs with `low[t_test_pivot] <= E_spring`, or
- a test pivot occurs with mean test volume `>= V_spring`, or
- a close `< TR_low` occurs before any successful test, or
- window `W` expires with no qualifying test pivot

**Primary confirmation does NOT require:**

- narrower spread (recorded as descriptive quality only)
- SOS after the test
- “low-volume spring” on the excursion itself (descriptive stratification only)
- nine buying tests
- P&F counts

### Upthrust confirmation — mirror

Successful confirmation requires:

- `high[t_test_pivot] < E_upthrust` (lower high)
- mean test-rally volume `< V_upthrust`
- no close `> TR_high` before confirm
- within `W`

### Sequence-completion timestamp

```text
t_sequence_complete = t_confirm
```

Outcome measurement may begin only **after** this timestamp (see Information boundary).

```text
t_terminal_event = t_return     # spring/upthrust geometry complete
t_sequence_complete = t_confirm # full Wyckoff sequence complete
```

These are **separate**. An observation is Treatment C only if confirmation succeeds.

---

## Stage E — Future outcomes (specify now; do not compute now)

Outcomes measure **leave-range / auction behavior**, not trade P&L.

Horizons (15-minute bars after `t_sequence_complete`):

```text
H ∈ {8, 16, 32}    # 2h, 4h, 8h of 15m bars
```

Only these three. No additional horizons after seeing results.

### Primary outcome (spring sequences)

At each `H`, binary:

```text
LEAVE_UP(H) = 1 iff max(close over the next H bars) > TR_high
```

i.e., the auction prints a close beyond the opposite (upper) range boundary within `H`.

### Primary outcome (upthrust sequences)

```text
LEAVE_DOWN(H) = 1 iff min(close over the next H bars) < TR_low
```

### Secondary outcomes (reported; not a second way to “pass” by shopping)

1. `EXTENT(H) =` signed max favorable excursion beyond the opposite boundary within `H`, divided by `TR_height` (0 if opposite boundary not reached).
2. `FAIL_BACK(H) = 1` if price again prints beyond the spring/upthrust extreme in the break direction within `H` (loss of the test’s implication).

**Primary verdict uses only `LEAVE_UP` / `LEAVE_DOWN` at the frozen horizons**, with the statistical rule below.

---

## Controls / null design (frozen before outcomes)

### Control A — Ordinary false break without qualifying TR

On the same 15-minute series:

- Let `support20` = minimum low of the prior 20 completed bars (no eligible-TR requirement).
- **A-spring-like:** `low < support20` by at least `max(0.25, 0.05 * (max20-min20 of prior 20))`, then `close >= support20` within `R_max=6`, with the same minimum-violation spirit.
- Exclude any A-event whose violation bar falls while an eligible TR exists whose `TR_low` equals that support (to avoid double-counting Treatment geometry as A).

Mirror for resistance20 upthrust-like events.

**Role:** Does the full Wyckoff sequence differ from generic failed breaks?

### Control B — Qualifying TR false break **without** successful confirmation

- Same Stage A–C spring/upthrust as Treatment.
- Confirmation fails or window expires (Stage D failure).

**Role:** Within TR context, does confirmation add information beyond terminal false-break geometry?

### Treatment C — Full sequence

Stages A–D all succeed; outcomes measured from `t_sequence_complete`.

### Primary comparison (locked)

**Primary null contrast:**

```text
C vs A
```

on the matched primary leave-range outcome at each frozen `H`, within each chronological sample.

**Secondary contrast (decomposition):**

```text
C vs B
```

at the same horizons.

Both are reported. The study does **not** assume C is special because it is named Wyckoff.

### Matching / pooling

- Springs and upthrusts analyzed separately for direction-specific leave outcomes, then pooled only via a pre-specified signed “leave in implied campaign direction” indicator:  
  `LEAVE_IMPLIED = LEAVE_UP` for springs, `LEAVE_DOWN` for upthrusts.
- Primary reported family: **pooled `LEAVE_IMPLIED`**.
- Separate spring-only and upthrust-only tables are descriptive companions.

### Statistical test (frozen)

Within each sample (IS, Validation, OOS):

- Let `p_C` = rate of `LEAVE_IMPLIED(H)` in Treatment C.  
- Let `p_A` = rate in Control A.  
- Primary statistic: `Δ(H) = p_C - p_A`.
- Two-proportion test (normal approximation) or Fisher exact if any cell expected count `< 5`.
- Two-sided α = 0.05 on IS for discovery reporting; Validation and OOS require **same sign** of `Δ(H)` as IS for the horizon to be considered stable.

### Pass / fail criterion (mechanism, not profit)

Frozen before outcomes:

| Label | Rule |
| --- | --- |
| `SUPPORTED` | For **at least two** of the three horizons `H∈{8,16,32}`, `Δ(H)` has the same sign in IS, Validation, and OOS, and the IS two-sided p-value ≤ 0.05 for those horizons, and each of C and A has `n ≥ 30` in IS and `n ≥ 20` in OOS for those horizons |
| `NOT SUPPORTED` | Primary contrast fails the above |
| `INCONCLUSIVE` | Sample sizes below the floors above in IS or OOS, or sign instability without a clear kill |

Secondary C vs B cannot rescue a failed C vs A into `SUPPORTED`. C vs B may be labeled descriptively as `CONFIRMATION ADDS` / `CONFIRMATION DOES NOT ADD` using the same multi-split sign rule without changing the primary label.

---

## Volume and effort/result — boundary with Strategy 27

| Allowed | Forbidden |
| --- | --- |
| Unsigned bar volume means inside the Wyckoff sequence (D2 lesser volume) | Signed volume / CVD / aggressor IC as a standalone feature |
| Optional descriptive: mean spread on test vs spring | Replacing the sequence with volume→return correlation |
| Stratify C by whether spring excursion volume was below TR median (descriptive) | Optimizing volume thresholds after seeing leave rates |

The research question for volume is contextual:

> Does lesser volume on the confirmatory test, **inside** the TR→terminal→return sequence, coincide with different leave-range behavior than the same geometry without that confirmation?

Not:

> Does volume predict returns?

---

## Contamination audit

| Prior work | Overlap | Material difference required here |
| --- | --- | --- |
| 15m downside-break failure | Failed support break + bounce | That study matched ordinary down closes; **no qualifying TR campaign, no return-into-frozen-TR grammar, no confirmatory higher-low/lesser-volume test, no leave-opposite-boundary outcome** |
| Strategy 42 / 42b S/R | Break or retest of 20-bar high/low | 42 trades breakout/retest payoff; here Control A is the contamination twin, and Treatment requires TR context + confirmation + leave-range mechanism outcome |
| Strategy 43 compression range | Detected range + edge behavior | 43 is fade/breakout-pullback **execution** grid; different state machine; this study is information-only Wyckoff sequence |
| Strategy 03 / 16 / 46 prior-day levels | Level reference + reaction | Prior-day objects are not Wyckoff TR campaigns |
| Strategy 47 LVN/POC | Profile geometry rejection/location | Explicitly excluded; no profile levels in this grammar |
| Strategy 27 signed volume | Volume vs return | Unsigned contextual volume only inside confirmation |
| Strategy 17 session extreme trap | Trap at extreme | No multi-touch TR cause-building + confirmatory test grammar |
| Strategy 35 flags | Pattern continuation | Unrelated geometry |

**Contamination flag:** any analysis that reports forward returns from `t_return` **without** requiring Stage D confirmation is **not** this study’s Treatment C. It collapses to failed-break feature mining.

---

## Event dependence (frozen)

| Rule | Freeze |
| --- | --- |
| Multiple springs from same TR | Separate observations if each has its own `t_return` and non-overlapping confirmation windows |
| Spring and upthrust same TR | Both allowed |
| Repeated tests | Only the **first** successful or failed confirmation attempt in `W` counts for that terminal event |
| Minimum separation | Next terminal violation for the same TR may not start before `max(t_confirm, t_spring_event+W)` for the prior event |
| Superseding TR | Old TR accepts no new terminal events after new TR eligibility |

---

## Information boundary / lookahead prohibitions

For every component, only information available at declaration time may be used.

| Object | Known at |
| --- | --- |
| Swing pivot | Close of `i+L` |
| TR eligibility + frozen bounds | `t_TR_eligible` |
| Terminal violation | End of `t_viol` |
| Terminal event (return) | End of `t_return` |
| Confirmation | End of `t_confirm` |
| Outcomes | Strictly after `t_sequence_complete` |

**Prohibited:**

- Future highs/lows to draw or revise `TR_low`/`TR_high`
- Future volume to define the terminal event
- Retrospective “this was accumulation because it went up later”
- Using outcome-window bars to accept/reject confirmation
- Same-bar leakage: outcomes start at the **next** 15-minute bar after `t_sequence_complete`
- Treating `t_return` as sequence completion

---

## FROZEN BEFORE OUTCOME ANALYSIS

The following are locked. No optimization loop after this point.

1. **Working bar:** 15-minute Globex-aligned NQ from 1-minute continuous.  
2. **Pivot rule:** `L=2` confirmed swings.  
3. **TR construction:** two near swing lows + two near swing highs; tolerance `0.25*ATR20`; two-sided reaction; `TR_height >= 0.75*ATR20`; ≥12 bars development; re-visit condition; frozen bounds.  
4. **TR invalidation:** four consecutive closes beyond a boundary (unless inside open recovery).  
5. **Late filter:** ≥8 bars after eligibility before terminal start.  
6. **Spring / upthrust:** min violation `max(0.25, 0.05*TR_height)`; return close back inside within `R_max=6`; max excursion cap `1.00*TR_height`.  
7. **Confirmation primary:** higher low (spring) / lower high (upthrust) + lesser mean volume vs excursion + no adverse close through boundary; window `W=12`.  
8. **Spread narrowing:** descriptive only, not primary gate.  
9. **SOS/SOW, nine tests, P&F, Composite Operator labels:** excluded from primary grammar.  
10. **Timestamps:** `t_terminal_event = t_return`; `t_sequence_complete = t_confirm`; outcomes from next bar.  
11. **Controls:** A = ordinary 20-bar false break; B = TR terminal without successful confirmation; C = full sequence.  
12. **Primary contrast:** C vs A on pooled `LEAVE_IMPLIED`.  
13. **Secondary contrast:** C vs B.  
14. **Primary outcome:** leave opposite boundary by close within `H∈{8,16,32}`.  
15. **Secondary outcomes:** extent / fail-back (non-verdict).  
16. **Splits:** IS 2010–2021 / Val 2022–2024 / OOS 2025–2026 via `common.splits`.  
17. **Statistical test:** two-proportion (or Fisher); two-sided α=0.05 on IS.  
18. **Pass/fail:** `SUPPORTED` / `NOT SUPPORTED` / `INCONCLUSIVE` rule as specified.  
19. **Volume scope:** unsigned contextual only; no Strategy 27 revival.  
20. **No parameter search** on Validation/OOS; undersized IS ⇒ `INCONCLUSIVE`, not retune.

---

## Implementation ambiguities — settled in Step 2

Resolved ex ante in `STEP2_ADDENDUM.md` (no alternative comparison):

1. **ATR:** causal simple mean of true range (length 20, lag 1), matching existing 15m causal studies — not Wilder, not a Wyckoff source rule.  
2. **Gaps:** incomplete 15m buckets dropped (no OHLC forward-fill); time gap > 20 minutes breaks segments, pivots, open TRs, and open recovery/confirmation windows.  
3. **Tick grid:** all price equality / boundary comparisons use integer ticks at `0.25` point.

---

## Explicit non-actions for Step 1

This document does not:

- scan the dataset for springs
- report frequencies
- calculate forward returns, win rate, Sharpe, or P&L
- authorize trading
- claim the framework works

**Next allowed step:** implement detectors that emit only TR/event/audit counts **without** outcome joins, or implement the full pipeline under a Step 2 note that still forbids changing the freezes above after outcomes exist.
