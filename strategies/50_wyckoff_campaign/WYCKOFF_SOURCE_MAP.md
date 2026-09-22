# Wyckoff Source Map — Step 1

**Status:** Source recovery and operationalization notes only.  
**Namespace:** `strategies/50_wyckoff_campaign/` (requested draft name `48_wyckoff_campaign` collides with existing `48_daily_candle_continuation`; inventory ID is **50**).  
**Date frozen for grammar intent:** 2026-09-21  
**No outcome scan has been run. No event counts. No forward returns.**

This file records what established Wyckoff sources claim, what is observable in NQ data, and which operational rules in `PREREGISTRATION.md` are source-explicit vs adaptations.

---

## Sources consulted

| ID | Source | Role |
| --- | --- | --- |
| S1 | Richard D. Wyckoff — *The Richard D. Wyckoff Course / Method of Trading and Investing in Stocks* (1930s lineage; Composite Man language, judging the market by its own action) | Primary historical framework |
| S2 | Wyckoff Analytics — *The Wyckoff Method* tutorial (StockCharts ChartSchool material reproduced with permission; phases, events, schematics, laws, nine tests) | Established modern educational synthesis of Wyckoff schematics |
| S3 | Henry O. Pruden — *The Three Skills of Top Trading* (Wiley, 2007), as cited by S2 for nine buying/selling tests | Established secondary for readiness tests |
| S4 | Wyckoff Stock Market Institute (WSMI) educational articles on springs and tests of springs | Established school lineage on spring → test quality criteria |
| S5 | Repository `RESEARCH_FRAMEWORKS/FRAMEWORK_DISCOVERY.md` Wyckoff section | Local research framing; not a Wyckoff primary |

Page numbers below cite S2’s published tutorial text where section references are available; WSMI articles are cited by title when page numbers are absent.

---

## Classification legend

| Label | Meaning |
| --- | --- |
| `SOURCE-EXPLICIT` | Stated directly in a listed source |
| `SOURCE-INSPIRED ADAPTATION` | Faithful to source intent; quantitative freeze not stated in source |
| `RESEARCHER-DEFINED` | Required for causal NQ research; not claimed as Wyckoff’s numeric rule |

---

## Concept ledger

### 1. Composite Man / Composite Operator

| Field | Content |
| --- | --- |
| Source | S1 section 9 / 9M; S2 “Wyckoff's Composite Man” |
| Source-explicit definition | Study fluctuations as if one operator plans, executes, and concludes campaigns; motives inferred from chart behavior |
| Observable in NQ data? | **No** as a label |
| Discretionary? | Yes — interpretive heuristic |
| Operationalization | **Excluded as a measurable variable.** See preregistration Composite Operator rule |
| Class | `SOURCE-EXPLICIT` concept; measurement = excluded (`RESEARCHER-DEFINED` restriction) |

### 2. Trading range (TR)

| Field | Content |
| --- | --- |
| Source | S2 “Analyses of Trading Ranges” |
| Source-explicit definition | Places where the previous trend has been halted and there is relative equilibrium between supply and demand; institutions prepare next campaign; extent of accumulation/distribution is the “cause” |
| Observable in NQ data? | Partially — price box and repeated reactions are observable; “institutional preparation” is not |
| Discretionary? | High if phases A–E or accumulation vs distribution must be labeled by eye |
| Proposed objective operationalization | Causal swing-constructed price box with repeated support and resistance reactions, minimum development time, and width floor — **without** labeling accumulation vs distribution before outcomes |
| Class | Concept `SOURCE-EXPLICIT`; NQ box grammar `SOURCE-INSPIRED ADAPTATION` + numeric freezes `RESEARCHER-DEFINED` |

### 3. Phase A stopping action (PS, SC/BC, AR, ST)

| Field | Content |
| --- | --- |
| Source | S2 Accumulation/Distribution Events and Phases |
| Source-explicit definition | Climactic stopping (wide spread, heavy volume), automatic rally/reaction defining opposite boundary, secondary test of climax area on diminished volume/spread |
| Observable? | Volume and spread yes; “climax” and “preliminary support” are judgmental without frozen cuts |
| Discretionary? | Yes for classic schematic labeling |
| Operationalization in this study | **Not required** as named PS/SC/AR/ST detectors. The TR box stands in for “range established after trend halt,” without claiming Phase A event names |
| Class | Source concepts `SOURCE-EXPLICIT`; omission from primary grammar is `RESEARCHER-DEFINED` (to avoid discretionary climax labeling) |

### 4. Phase B “building a cause”

| Field | Content |
| --- | --- |
| Source | S2 Phase B |
| Source-explicit definition | Time inside the TR during which inventory is transferred; early swings often wider/higher volume; later downswings (in accumulation) tend to diminish in volume |
| Observable? | Duration and repeated rotations yes; net institutional inventory no |
| Discretionary? | Yes for “ready for Phase C” |
| Operationalization | Minimum development duration after TR eligibility before a terminal event may be declared — proxy for “not the first hour of a brand-new box” |
| Class | Intent `SOURCE-INSPIRED ADAPTATION`; duration numeric `RESEARCHER-DEFINED` |

### 5. Spring

| Field | Content |
| --- | --- |
| Source | S2 Accumulation Events / Phase C; S4 WSMI springs articles |
| Source-explicit definition | Price moves **below the support level of the TR** and then **reverses and moves/closes back within the TR**; late TR supply test; bear trap; **not required** in every accumulation schematic |
| Observable? | Yes once TR boundaries and return rule are frozen |
| Discretionary? | “Quickly,” “late,” and quality grades need freezes |
| Operationalization | See `PREREGISTRATION.md` spring grammar |
| Class | Core geometry `SOURCE-EXPLICIT`; min violation, recovery window, bar timeframe `RESEARCHER-DEFINED` |

### 6. Upthrust (UT) / UTAD

| Field | Content |
| --- | --- |
| Source | S2 Distribution Events / Phase C |
| Source-explicit definition | Price moves **above TR resistance** and **quickly reverses to close below resistance / back in the TR**; UTAD is late distributional counterpart of spring/shakeout; not required in every schematic |
| Observable? | Yes with mirrored spring grammar |
| Discretionary? | Same as spring |
| Operationalization | Exact mirror of spring in preregistration |
| Class | Core geometry `SOURCE-EXPLICIT`; numeric windows `RESEARCHER-DEFINED` |

### 7. Test of a spring / confirmatory test

| Field | Content |
| --- | --- |
| Source | S2 (“a spring is often followed by one or more tests; a successful test typically makes a **higher low on lesser volume**”); S4 *Test of Springs* (higher bottom than spring; lower average volume than approach to spring; preferably narrower spreads; respect sprung support) |
| Source-explicit definition | Subsequent revisit of the spring area that checks whether supply reappears; successful test → higher low, lesser volume; failed test → supply takes control (often lower low / higher volume) |
| Observable? | Higher low vs spring extreme: yes. Lesser volume: yes with frozen volume averages. Narrower spread: yes but secondary quality |
| Discretionary? | Identifying when the “test” has started/ended without a freeze |
| Operationalization | Primary confirmation = higher low than spring extreme **and** lesser mean volume on test pullback vs spring excursion; must not close below TR support. Spread narrowing is **descriptive quality**, not primary gate |
| Class | Higher low + lesser volume `SOURCE-EXPLICIT`; test window detection `SOURCE-INSPIRED ADAPTATION`; exact bar counts `RESEARCHER-DEFINED` |

### 8. Sign of Strength / Sign of Weakness (SOS / SOW)

| Field | Content |
| --- | --- |
| Source | S2 |
| Source-explicit definition | SOS: advance on increasing spread and relatively higher volume, often after spring. SOW: down-move on increased spread/volume |
| Observable? | Partially |
| Role in this study | **Not part of primary sequence completion.** May be reported descriptively after confirmation; must not redefine the event after seeing leave-range outcomes |
| Class | `SOURCE-EXPLICIT` concept; excluded from primary gate (`RESEARCHER-DEFINED` scope limit) |

### 9. Effort versus result (volume vs spread/progress)

| Field | Content |
| --- | --- |
| Source | S2 Law of Effort versus Result; supply/demand bar analysis |
| Source-explicit definition | Divergences between volume (effort) and price progress/spread (result) warn of absorption or exhaustion |
| Observable? | Bar volume and high–low spread yes; signed aggressor flow no (and Strategy 27 forbids treating signed OHLCV as order flow) |
| Role in this study | Used only as already embedded in confirmatory **lesser volume** (and optional descriptive spread comparison). Not a standalone signed-volume IC |
| Class | Law `SOURCE-EXPLICIT`; application limited to sequence-contextual volume comparison `SOURCE-INSPIRED ADAPTATION` |

### 10. Nine buying / selling tests

| Field | Content |
| --- | --- |
| Source | S2 / S3 |
| Source-explicit definition | Checklist for readiness to leave a TR (objectives, climax structure, activity, trendline break, higher highs/lows, relative strength, base/crown, R:R) |
| Role in this study | **Not implemented as a nine-test score.** Too many discretionary and stock-relative items for a single NQ process test |
| Class | `SOURCE-EXPLICIT` checklist; omission `RESEARCHER-DEFINED` |

### 11. Point & Figure cause counts

| Field | Content |
| --- | --- |
| Source | S1/S2 Cause and Effect; P&F count guide |
| Role in this study | **Excluded** from primary mechanism test (targets / R:R are strategy objects) |
| Class | `SOURCE-EXPLICIT`; excluded `RESEARCHER-DEFINED` |

---

## NQ futures transfer audit

### Transferable (use)

- Trading-range / equilibrium box after a halt in directional progress
- Support and resistance as repeatedly defended extremes
- Spring / upthrust geometry (temporary boundary violation + return into range)
- Confirmatory test of remaining supply/demand (higher/lower extreme + reduced opposing effort via volume)
- Effort vs result as bar volume vs spread/progress
- Leave-range behavior as the campaign “effect”

### Non-transferable or uncertain (do not import silently)

- Specialist / floor operator tape of Wyckoff’s era
- Float absorption of an individual equity issue
- Identifiable “Composite Operator” inventory
- Comparative strength vs a stock’s industry group (optional later with ES; **not** required for primary NQ process)
- Multi-month stock accumulation campaigns as the only valid scale (futures TR scale is an adaptation)
- P&F box size conventions tuned to stock prices
- Earnings-news buying climaxes as distribution machinery

---

## Plain-English sequence recovered from sources

```text
1. A trading range exists (prior trend halted; relative equilibrium; cause being built).
2. Late in that range, price temporarily violates a boundary (spring below support, or UT/UTAD above resistance).
3. Price returns into the range (false break / trap geometry).
4. A subsequent test checks remaining opposing pressure:
      successful → does not exceed the spring/UT extreme in the break direction,
      and shows lesser volume (reduced opposing effort).
5. Only then is the campaign considered more ready to leave the range
      in the direction implied by the successful test (markup after spring; markdown after UT/UTAD).
```

This study does **not** test “spring alone is bullish.”

---

## Mapping to preregistration objects

| Source idea | Preregistration object |
| --- | --- |
| TR with established support/resistance | Qualifying TR (15m causal swing box) |
| Late Phase C terminal test | Min development duration before event eligibility |
| Spring / UT geometry | Terminal event + return |
| Successful test of spring | Primary confirmation grammar |
| Markup / markdown leave TR | Primary outcomes after `t_sequence_complete` |
| Ordinary false break without campaign | Control A |
| TR false break without successful test | Control B |
| Full sequence | Treatment C |

---

## Explicit non-claims

- This map does not claim Wyckoff is profitable on NQ.
- Numeric bars/windows in the preregistration are freezes for research reproducibility, not quotations from Wyckoff.
- Omitting Phase A climax names and nine-test scoring is a scope choice to keep the object falsifiable, not a denial that those concepts exist in the literature.
