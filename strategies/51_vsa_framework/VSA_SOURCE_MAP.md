# VSA Source Map — Step 1

**Status:** Source recovery and operationalization notes only.  
**Namespace:** `strategies/51_vsa_framework/`  
**Date frozen for grammar intent:** 2026-09-22  
**No outcome scan has been run. No event counts. No forward returns. No P&L.**

This file records what established Volume Spread Analysis (VSA) sources claim, what is observable in NQ data, and which operational rules in `PREREGISTRATION.md` are source-explicit versus adaptations.

---

## Sources consulted

| ID | Source | Role |
| --- | --- | --- |
| S1 | Tom Williams — *The Undeclared Secrets That Drive the Stock Market* (1993; lineage continued into later TradeGuider revisions) | Primary historical VSA manuscript |
| S2 | Tom Williams / TradeGuider — *Master the Markets* (3rd ed. lineage, ©1993–2005; co-revised with Roy Didlock) | Primary systematic exposition of VSA bar grammar, effort vs result, background, no demand, up-thrusts, stopping volume, tests |
| S3 | Philip Friston / established VSA educational restatements of Williams bar rules (as documented in ATAS VSA educational series citing Friston’s No Demand description) | Secondary confirmation of operational bar checks used by Williams-lineage educators |
| S4 | Repository `RESEARCH_FRAMEWORKS/FRAMEWORK_DISCOVERY.md` Framework 3 (VSA) | Local research framing; **not** a VSA primary |
| S5 | Strategy 27 dossier (`hypothesis.md`, `conclusion.md`, `LITERATURE.md`, `DATA_NOTES.md`) | Contamination boundary — signed OHLCV proxy already killed |
| S6 | Strategy 50 Wyckoff source map / preregistration | Contamination boundary — TR spring/upthrust campaign already specified |

**Excluded as authoritative definitions:** random trading blogs, YouTube summaries, modern “VSA indicator” scripts, and proprietary TradeGuider software signal streams (Williams’ written principles are tested; the software label stream is not).

Page citations below refer to *Master the Markets* printed page markers recovered from the TradeGuider edition text (S2).

---

## Classification legend

| Label | Meaning |
| --- | --- |
| `SOURCE-EXPLICIT` | Stated directly in a listed primary/secondary source |
| `SOURCE-INSPIRED ADAPTATION` | Faithful to source intent; quantitative freeze not unique in the text |
| `RESEARCHER-DEFINED` | Required for causal NQ research; not claimed as Williams’ numeric rule |

---

## Why this is not Strategy 27 (mandatory separation)

Strategy 27 tested whether **OHLCV signed-volume proxies** (and unsigned activity) carry incremental short-horizon directional / RV information after controlling for contemporaneous return and range. The signed proxy collapsed into a return transform (Spearman ≈ 0.93 with `ret_1m`); residual forward association ≈ 0. Unsigned volume tracked future |return|/RV (activity persistence), not signed pressure.

| Strategy 27 object | This VSA object |
| --- | --- |
| `signed_vol_proxy` / CVD-like bar pressure | **Forbidden** as primary feature |
| Volume percentile / volume spike alone | **Forbidden** as primary feature |
| Candle direction × volume alone | **Forbidden** as primary feature |
| Scalar Spearman / IC of a bar feature vs forward return | **Not** the research design |
| Bar volume as “order flow” | Explicitly forbidden language |

VSA’s claimed mechanism is a **contextual process**:

```text
background (latent strength/weakness)
  → effort vs result reading on a bar / small bar sequence
  → confirmation on subsequent bar(s)
  → path of least resistance
```

not:

```text
unusual volume → future return
```

If a volume comparison appears inside this study, it operates only inside that sequence (relative volume vs the prior two bars; optional trailing median for “narrow/wide”), never as a standalone IC.

---

## Concept ledger

### 1. Professional / “smart money” / syndicate / market-maker narrative

| Field | Content |
| --- | --- |
| Source | S2 throughout (e.g. accumulation/distribution narrative; “professional operators”) |
| Source-explicit definition | Large operators accumulate/distribute; their activity is said to leave readable volume traces that the public cannot hide |
| Observable in NQ data? | **No** as a participant label |
| Discretionary? | Yes — interpretive attribution |
| Operationalization | **Excluded as a measurable variable.** Translate only into observable price/volume/close constructions |
| Class | Narrative `SOURCE-EXPLICIT`; measurement exclusion `RESEARCHER-DEFINED` |

### 2. The VSA trinity: volume, spread, close location

| Field | Content |
| --- | --- |
| Source | S2 preamble / method statement; FRAMEWORK_DISCOVERY §3 |
| Source-explicit definition | Cause of price movement is supply/demand imbalance readable from the **relationship** of volume, price spread (high–low), and where the bar closes within that spread — not from volume alone |
| Observable? | Yes on OHLCV bars |
| Discretionary? | Low for raw variables; high for qualitative “high/low/narrow/wide” without freezes |
| Operationalization | See preregistration: unsigned bar volume; `spread = high − low`; `close_frac = (close − low) / (high − low)` with dead-bar guard |
| Class | Trinity `SOURCE-EXPLICIT`; numeric cuts for qualitative adjectives `RESEARCHER-DEFINED` / `SOURCE-INSPIRED ADAPTATION` |

### 3. Effort versus result

| Field | Content |
| --- | --- |
| Source | S2 “Effort versus Results” (~p.38–39) |
| Source-explicit definition | **Effort to go up:** wide-spread up-bar, closing on the highs, with increased (but not excessive) volume. **Effort to go down:** wide-spread down-bar, closing on the lows, increased volume. If there has been effort, there should be a **result** (progress). Effort without corresponding progress implies opposing supply/demand. High volume up with **no progress next day** implies the volume contained more selling than buying |
| Observable? | Volume and spread/progress yes; “excessive” and “professional selling” narrative no |
| Discretionary? | Yes for “excessive,” “no progress,” and multi-bar campaigns without frozen rules |
| Role in this study | Central **mechanism language**. Primary experiment uses one concrete low-effort indication (No Demand) after a frozen background weakness seed that itself encodes effort-without-result / up-thrust-class weakness — not an exhaustive matrix of all effort/result cells |
| Class | Law `SOURCE-EXPLICIT`; selection of one primary grammar `RESEARCHER-DEFINED` scope limit |

**Combinations Williams discusses (not all become separate signals here):**

| Effort / result combination | Source reading (qualitative) | In primary experiment? |
| --- | --- | --- |
| High volume + wide spread + close in direction | Genuine effort; expect result if background agrees | Background / descriptive only |
| High volume + narrow spread / little progress | Absorption / opposing force | Background SOW seed (effort-without-result) |
| High volume up + next bar fails to progress | Weakness / supply in the volume | Background SOW seed |
| Low volume + narrow spread up | No demand (lack of professional participation) | **Primary event** |
| Low volume + successful movement | Possible lack of opposition / thin market | Not primary |
| Repeated effort without result | Persistent opposing pressure | Captured only via background SOW seed presence, not as a separate scanner |

### 4. Background / context

| Field | Content |
| --- | --- |
| Source | S2 repeatedly (e.g. No Demand requires background weakness; up-thrusts “rarely seen in strong markets”; “near background indications are just as important as the most recent”) |
| Source-explicit definition | Current bar observations mean little alone. Latent strength or weakness already embedded in recent price/volume history conditions how a bar is read. No Demand after strength may be a pause; No Demand after weakness is a weakness confirmation candidate. Location near old tops / resistance matters in examples |
| Observable? | Partially — recent bar sequences and proximity to prior highs/lows are observable; “the specialists have seen weakness you missed” is not |
| Discretionary? | **High** in the books (chart narrative) |
| Proposed objective operationalization | Two causal, frozen components: (1) **location** — the indication bar interacts with a recent swing extreme; (2) **SOW seed** — at least one completed prior effort-without-result or up-thrust-class bar in a lookback window. No discretionary “distribution campaign” label |
| Class | Concept `SOURCE-EXPLICIT`; NQ freeze `SOURCE-INSPIRED ADAPTATION` + numeric windows `RESEARCHER-DEFINED` |

### 5. No Demand

| Field | Content |
| --- | --- |
| Source | S2 ~p.19, ~p.152–153; S3 Friston restatement |
| Source-explicit definition (S2) | Weakness on **up-bars**, especially when spreads are **narrow**, with volume **less than the previous two bars**. TradeGuider/Williams definition: a **narrow-spread** bar on **low volume** that **closes in the middle or low**. Principle is seen **after a sign of weakness**; professionals not interested in the upside |
| Source-explicit confirmation (S3) | Next bar should be a **down bar** to confirm No Demand (when background is weak) |
| Observable? | Yes once narrow/low/middle-or-low are frozen |
| Discretionary? | “After weakness” and “near old top” without freezes |
| Operationalization | Primary event grammar in `PREREGISTRATION.md` |
| Class | Core morphology `SOURCE-EXPLICIT`; location/background windows and narrow-spread median cut `RESEARCHER-DEFINED` / `SOURCE-INSPIRED ADAPTATION` |

### 6. No Supply / Test of supply

| Field | Content |
| --- | --- |
| Source | S2 “Testing Supply” (~p.33–34); Williams treats successful low-volume downside probes as critical strength; S3 notes Williams often called No Supply a “Test” |
| Source-explicit definition | Downside probe / down-bar character with **low volume**, often closing mid/high, indicating absence of selling pressure after strength indications; Williams: testing is “by far the most important of the low volume buy signals” |
| Role in this study | **Documented secondary** (mirror of No Demand). **Not** the primary Treatment C. Avoids dual-side fishing |
| Class | Concept `SOURCE-EXPLICIT`; deferred from primary gate `RESEARCHER-DEFINED` |

### 7. Up-thrust

| Field | Content |
| --- | --- |
| Source | S2 ~p.77–78, glossary ~p.177 |
| Source-explicit definition | Wide spread up during the bar, accompanied by high (or sometimes low) volume, **closing on or very near the lows**. Usually after a rise / overbought conditions / weakness in the background. Trap dynamics (marks up to catch buyers and stops) |
| Observable? | Yes with frozen wide/close/volume cuts |
| Role in this study | Used as one allowed **background SOW seed** type, and documented as a secondary event class. **Not** the primary Treatment (Strategy 50 already tests TR-bound upthrust campaigns; standalone upthrust-as-trade would also collide with failed-break research) |
| Class | Concept `SOURCE-EXPLICIT`; background-seed use `SOURCE-INSPIRED ADAPTATION` |

### 8. Stopping volume

| Field | Content |
| --- | --- |
| Source | S2 ~p.96–97 |
| Source-explicit definition | During a bear move/reaction, resistance to further decline often appears as a **down-day on very high volume closing on the highs** (buying entering). If close is on the lows, wait for next bar; if next is level/up, prior high volume likely contained buying. Changes direction or forces sideways action. Low-volume tests after this are signs of strength |
| Role in this study | Documented; **not** primary. Would require ultra-high volume freezes and a separate bullish sequence (stopping → test → upside). Deferred to avoid dual primary mechanisms |
| Class | `SOURCE-EXPLICIT`; omission from primary `RESEARCHER-DEFINED` |

### 9. Climactic behavior / buying climax

| Field | Content |
| --- | --- |
| Source | S2 (buying climax: exceptionally high volume, narrow spreads into new high ground; distribution into public buying) |
| Role in this study | Not primary. Effort-without-result into highs is partially captured by the SOW seed “no progress on high volume,” without claiming “buying climax” labels |
| Class | `SOURCE-EXPLICIT` concept; simplified proxy only via SOW seed |

### 10. Confirmation / follow-through

| Field | Content |
| --- | --- |
| Source | S2 (effort vs result requires observing subsequent progress; stopping volume often needs next-bar response; No Demand narrative expects weakness to show); S3 explicit next down-bar after No Demand |
| Source-explicit definition | An indication is incomplete until subsequent bars validate or refute it. Isolated bars without background and follow-through are incomplete reads |
| Operationalization | Separate timestamps: `t_event` (No Demand bar complete) `< t_confirmation` (confirming down-bar complete). Outcomes measured only after `t_confirmation` |
| Class | Requirement `SOURCE-EXPLICIT`; one-bar confirmation freeze `SOURCE-INSPIRED ADAPTATION` |

### 11. Path of least resistance / expected reaction

| Field | Content |
| --- | --- |
| Source | S2 “Path of Least Resistance” |
| Source-explicit definition | After validated weakness, expect difficulty sustaining upside / downside path; after validated strength, expect upside path |
| Operationalization | Mechanism outcomes after confirmation: failure to clear the No Demand high; net downside close progress over frozen horizons — **not** a trading system |
| Class | Expectation `SOURCE-EXPLICIT`; outcome metrics `RESEARCHER-DEFINED` |

### 12. Timeframe

| Field | Content |
| --- | --- |
| Source | S2 explicitly applies bar language to “day (or any timeframe)” / “whatever other time period is being used” |
| Source-explicit definition | Principles are not daily-only; examples are often daily stocks |
| Operationalization | Primary working clock: **15-minute** Globex-aligned NQ bars aggregated from 1-minute continuous (same construction family as Strategy 50). Rationale: Williams allows any timeframe; 15m balances event frequency for chronological splits with multi-year OHLC; daily deferred (not mined after outcomes) |
| Class | Multi-timeframe applicability `SOURCE-EXPLICIT`; 15m choice `RESEARCHER-DEFINED` |

### 13. Volume definition for NQ

| Field | Content |
| --- | --- |
| Source | S2 assumes exchange-traded volume on the instrument charted |
| NQ data | Continuous 1m OHLCV from Databento GLBX.MDP3 (`data/nq_1m_continuous.parquet`); unsigned contract volume; no aggressor side (Strategy 27 DATA_NOTES) |
| Operationalization | Bar volume = sum of 1m volumes inside the 15m bar. **No CVD. No signed volume. No buy−sell.** Session-relative TOD z-scores are **not** used in the primary gate (would reopen Strategy 27 activity mining) |
| Class | Unsigned total volume `SOURCE-INSPIRED ADAPTATION` to futures; exclusion of signed proxies `RESEARCHER-DEFINED` (contamination lock) |

### 14. Spread definition

| Field | Content |
| --- | --- |
| Source | S2: spread = range of the bar (high to low), **not** bid–ask |
| Operationalization | `spread = high − low` on the working bar. True range is **not** primary (Williams’ examples are high–low). Narrow/wide vs trailing median of prior completed bars |
| Class | Definition `SOURCE-EXPLICIT`; median comparison window `RESEARCHER-DEFINED` |

### 15. Close location

| Field | Content |
| --- | --- |
| Source | S2: No Demand closes “in the middle or low”; up-thrust closes “on or very near the lows”; stopping volume often “closing on the highs” |
| Operationalization | `close_frac = (close − low) / max(high − low, ε)`. No Demand: `close_frac ≤ 0.50` (“middle or low”). Up-thrust-class SOW seed: `close_frac ≤ 0.25` (“near the lows”) |
| Class | Qualitative phrases `SOURCE-EXPLICIT`; cutoffs `RESEARCHER-DEFINED` (not optimized) |

---

## NQ futures transfer audit

### Transferable (use)

- Price/volume relationship on a centralized futures tape (CME NQ volume is complete for the contract)
- Effort (volume) vs result (spread / progress)
- Close location within the bar
- No Demand / No Supply style relative-volume bar grammar
- Requirement for background and confirmation
- Tests after climactic / stopping-type action (secondary)
- Failed upside probes / up-thrust geometry as weakness indications

### Potentially non-transferable (do not import silently)

- Downstairs specialist / syndicate stock-campaign narratives of Williams’ era
- Individual equity float absorption and “marking the stock up/down”
- TradeGuider proprietary red/green software signals
- Cash vs futures premium games as a required read (S2 discusses this for indices; **not** required for primary NQ bar grammar)
- Assuming “professional operators” as a measurable agent
- Stock-news climax microstructure as the only valid climax form

---

## Coherent causal sequence recovered from sources

Williams’ process is **not** “volume + candle shape → return.”

Recovered process:

```text
1. Background embeds latent strength or weakness (recent effort/result history + location).
2. An indication bar appears (e.g., No Demand: up-bar, narrow spread, volume < prior two, close mid/low).
3. The indication is incomplete until confirmation (e.g., next bar down after No Demand in weak background).
4. After confirmation, expect path of least resistance consistent with the validated reading
   (weakness → difficulty sustaining upside / downside progress).
```

### Primary research object (selected)

```text
BACKGROUND WEAKNESS (location near recent highs + SOW seed in lookback)
  → NO DEMAND EVENT (up-bar, narrow spread, vol < prior 2, close mid/low)
  → CONFIRMATION (next completed bar is a down-bar)
  → EXPECTED REACTION (inability to clear the ND high / net downside progress)
```

### Secondary (documented only; not Treatment C)

- Mirror: background strength + No Supply + up-bar confirmation → upside path  
- Stopping volume → low-volume test → upside path  
- Standalone up-thrust event class (overlaps Strategy 50 TR upthrust if TR-bound)

---

## Mapping to preregistration objects

| Source idea | Preregistration object |
| --- | --- |
| Background weakness near highs | Stage A location + SOW seed |
| Effort vs result | SOW seed (no-progress high volume / up-thrust-class) + ND low-effort morphology |
| No Demand indication | Stage B event at `t_event` |
| Next-bar confirmation | Stage C at `t_confirmation` |
| Path of least resistance down | Primary outcomes after `t_sequence_complete` |
| ND morphology without background | Control A |
| Background + ordinary up-bar (not ND) | Control B |
| Full sequence | Treatment C |

---

## Contamination audit vs closed / adjacent research

| Prior work | Surface overlap | What makes VSA different — or rejection flag |
| --- | --- | --- |
| **Strategy 27** signed volume / unsigned activity | Uses volume | 27 is scalar feature→forward association. VSA requires background + effort/result bar grammar + confirmation sequence. **Signed volume / CVD forbidden.** If an analysis drops background+confirmation and correlates volume with returns, **reject as 27 rebrand** |
| **44 H02 / CVD / trade imbalance** | “Pressure” language | Aggressor delta / MBO objects. VSA here is OHLCV unsigned bar grammar only |
| **44 H03 absorption** | High volume, little progress | Thematic cousin of effort-without-result. H03 was `NOT TESTED` on a valid clock and is MBO absorption. VSA SOW seed is bar OHLCV, contextualized into ND sequence — not a mid-impact absorption IC |
| **47 volume profile / POC / LVN** | Volume location | Profile geometry by price. VSA does **not** use POC/VAH/VAL/LVN. Profile branch closed |
| **30 / 33 relative volume** | Volume filters | IB breakout economics with relative-volume tertiles. Not ND grammar; not background SOW → confirmation process |
| **15m failed break / 42 S/R** | Failure near highs | Those studies are break/retest geometry vs matched moves. VSA Treatment requires ND morphology + volume\<prior2 + confirmation; Control A/B exist specifically to stop “failed rally near highs” rebrands |
| **43 compression** | Narrow range | Compression is range-detection execution grid. ND is low **volume** + narrow spread on an **up-bar** after weakness — different object |
| **39 multi-day compression** | Low activity | Day-scale range clustering; opposite expansion claim failed. Not VSA ND |
| **Price-action candle pack** | Candle shapes | No volume-relative-to-prior-two + VSA background/confirmation process |
| **Strategy 50 Wyckoff** | Up-thrust / effort–result language | 50 requires qualifying **TR campaign → spring/UT → return → confirmatory test → leave-range**. Primary VSA here is **No Demand after background weakness**, **without** requiring a Wyckoff TR box. If someone requires Strategy 50’s TR+spring grammar and calls it VSA, **reject as 50 rebrand** |

---

## Source fidelity audit (freeze table)

| Component | Source says | Our implementation | Status |
| --- | --- | --- | --- |
| Background | Latent weakness/strength in recent history; ND meaningful after SOW; location near tops matters | Causal SOW seed in lookback + proximity to recent swing high; no “smart money” label | adaptation |
| Effort | Volume / participation attempting a move; wide+increased volume = effort | Unsigned bar volume; SOW seed uses above-median volume on wide/up bars | adaptation |
| Result | Spread and subsequent progress (or failure to progress) | Bar `high−low`; “no progress” = next bar fails to improve on the effort bar | adaptation |
| Event | No Demand: up-bar, narrow spread, vol \< prior two, close mid/low, after weakness | Exact morphology + background gate | mostly source; cuts adapted |
| Confirmation | Subsequent validation; next down-bar for ND (educator restatement of Williams practice) | First next bar must be down-bar (`close < prior close`) | adaptation |
| Expected reaction | Path of least resistance consistent with validated weakness | After `t_confirmation`: fail to clear ND high; net downside close over frozen H | adaptation |

---

## Explicit non-claims

- This map does not claim VSA is profitable on NQ.
- Numeric medians, lookbacks, and close-fraction cuts are research freezes, not quotations of Williams’ unique thresholds (the texts are qualitative).
- Omitting No Supply / stopping-volume / climax as primary Treatment is a scope choice for one coherent mechanism test, not a denial those concepts exist in VSA.
- “Smart money is distributing” is never a data column.
