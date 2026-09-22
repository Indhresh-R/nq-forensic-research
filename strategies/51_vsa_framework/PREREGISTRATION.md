# Preregistration — 51 VSA framework (No Demand sequence)

**Status:** FROZEN BEFORE OUTCOME ANALYSIS (Step 1 complete).  
**Label:** Mechanism research only. Not an executable strategy. No entries, exits, stops, targets, or friction model.  
**Companion:** `VSA_SOURCE_MAP.md`  
**Namespace:** `strategies/51_vsa_framework/`

No NQ event scan, event count, forward return, win rate, or P&L may be computed under this file until a separate Step 2 implementation note is opened. Definitions below must not be edited after any outcome table exists.

---

## Question

Does the **complete VSA No Demand sequence**

```text
background weakness (location near recent highs + SOW seed)
  → No Demand indication bar
  → confirming down-bar
```

exhibit subsequent **path-of-least-resistance / inability-to-advance behavior** that differs from appropriate controls that lack the full VSA context or the key effort/result characteristic?

This is **not**:

- “unusual volume predicts returns”
- “narrow candle predicts returns”
- “signed volume / CVD predicts direction”
- a trading-system authorization
- a rename of Strategy 27 or Strategy 50

### Causal hypothesis (mechanism only)

> When a No Demand indication occurs in a weak background and is confirmed by a subsequent down-bar, subsequent auction behavior may differ from (A) the same No Demand morphology without that background, and from (B) the same background with an ordinary up-bar that lacks the No Demand effort/result signature.

---

## Source set (frozen)

| ID | Source |
| --- | --- |
| S1 | Tom Williams — *The Undeclared Secrets That Drive the Stock Market* |
| S2 | Tom Williams / TradeGuider — *Master the Markets* (3rd-ed. lineage) |
| S3 | Williams-lineage educational restatements of No Demand confirmation (Friston / ATAS VSA series) |
| S4 | `RESEARCH_FRAMEWORKS/FRAMEWORK_DISCOVERY.md` Framework 3 (local framing only) |

Primary grammar claims rest on S2; confirmation next-down-bar practice is S2-consistent and made explicit via S3.

---

## Data

| Item | Freeze |
| --- | --- |
| Instrument | Continuous NQ futures |
| Source file | `data/nq_1m_continuous.parquet` via `common.nq_session.load_nq` (read-only) |
| Clock | `America/New_York` |
| Session | Globex `session_date` as in `common.nq_session` (roll at 18:00 ET) |
| Working bar | **15-minute** bars aggregated from 1-minute bars, aligned from 18:00 ET |
| Volume | Sum of 1-minute **unsigned** volumes inside each 15-minute bar |
| Spread | `high − low` of the 15-minute bar (**not** bid–ask; **not** true range as primary) |
| Close location | `close_frac = (close − low) / max(high − low, 1e-12)` |
| ES | Not required for the primary NQ process test |
| Signed volume / CVD / aggressor | **Forbidden** in event construction |

Incomplete Globex sessions follow completeness conventions used by Strategies 46/48/49 when session-level pairing is needed. The VSA process runs on the continuous 15-minute series and may span session boundaries, subject to missing-bar rules below.

---

## Chronological splits

Reuse `common.splits` exactly. Split membership is by the **sequence-completion** timestamp’s `session_date` year:

| Sample | Calendar years |
| --- | --- |
| Discovery / IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

No shuffling. No mixing future years into discovery. OOS must not revise any rule below.

If Step 2 finds IS event counts too small for the frozen grammar, that fact is reported as a **power failure**, not a license to retune definitions using Validation/OOS.

---

## “Smart money” / composite-operator rule

**Forbidden as measurable variables or outcome labels:**

- “smart money is distributing / accumulating”
- “institutions are selling / buying”
- “professionals are absorbing”
- “syndicate operators are marking the market”

These are explanatory narratives in VSA texts. Only observable price / unsigned volume / time constructions below are allowed.

---

## Primary VSA sequence (frozen)

```text
BACKGROUND WEAKNESS
  → NO DEMAND EVENT
  → CONFIRMATION (down-bar)
  → EXPECTED REACTION (mechanism outcomes)
```

Secondary event classes (No Supply mirror, stopping-volume→test, standalone up-thrust-as-Treatment) are **out of scope** for Treatment C. They may be listed in Step 2 diagnostics only if predeclared as non-decision descriptive tables — they cannot change pass/fail.

---

## Bar predicates (shared)

Index completed 15-minute bars `0…T` in time order. All predicates use only completed bars.

| Symbol | Definition | Class |
| --- | --- | --- |
| `up_bar[t]` | `close[t] > close[t-1]` | `SOURCE-EXPLICIT` up-bar |
| `down_bar[t]` | `close[t] < close[t-1]` | `SOURCE-EXPLICIT` down-bar |
| `spread[t]` | `high[t] − low[t]` | `SOURCE-EXPLICIT` |
| `close_frac[t]` | `(close[t] − low[t]) / max(spread[t], 1e-12)` | `RESEARCHER-DEFINED` math |
| `vol_lt_prior2[t]` | `volume[t] < volume[t-1]` **and** `volume[t] < volume[t-2]` | `SOURCE-EXPLICIT` (S2) |
| `med_spread[t]` | median of `spread[t-20…t-1]` (20 prior completed bars) | `RESEARCHER-DEFINED` window |
| `med_vol[t]` | median of `volume[t-20…t-1]` | `RESEARCHER-DEFINED` window |
| `narrow[t]` | `spread[t] ≤ med_spread[t]` | `SOURCE-INSPIRED ADAPTATION` |
| `wide[t]` | `spread[t] ≥ 1.25 * med_spread[t]` | `RESEARCHER-DEFINED` (up-thrust/effort seed) |
| `high_vol[t]` | `volume[t] ≥ med_vol[t]` | `SOURCE-INSPIRED ADAPTATION` |

Bars with fewer than 22 prior completed bars available for medians/prior-2 checks are **ineligible** for event declaration.

---

## Stage A — Background weakness (market state / context)

### Source grounding

S2: No Demand is read **after a sign of weakness**; location near old tops matters; background is as important as the current bar.

### A1 — Location (`SOURCE-INSPIRED ADAPTATION` + numeric freeze `RESEARCHER-DEFINED`)

Let `HH[t] = max(high[t-K…t-1])` with `K = 32` (eight hours of 15m bars).

Location condition at candidate event bar `t`:

```text
high[t] >= HH[t] - 0.15 * ATR20[t]
```

where `ATR20[t]` is the 20-bar average true range using only bars `≤ t` (Wilder or simple mean of true ranges — **freeze:** simple mean of `max(high-low, |high-prev_close|, |low-prev_close|)` over the prior 20 completed bars).

Interpretation: the bar is probing into / near the recent high region (Williams’ “near an old top” proxy). This is **not** a Wyckoff TR box and **not** Strategy 50.

### A2 — SOW seed in lookback (`SOURCE-INSPIRED ADAPTATION`)

Within bars `t-L … t-1` with `L = 24`, there must exist at least one completed seed bar `s` of either type:

**Seed type W1 — Effort without result (no progress on high volume up):**

- `up_bar[s]`
- `high_vol[s]`
- `wide[s]` **or** `spread[s] ≥ med_spread[s]` (at least not narrow)
- Next bar `s+1` shows **no progress**: `close[s+1] ≤ close[s]` **or** `high[s+1] ≤ high[s]`
- Seed is known only at the close of `s+1` (so `s+1 ≤ t-1`)

**Seed type W2 — Up-thrust-class bar:**

- `up_bar[s]` **or** (`high[s] > high[s-1]` and `close[s] < open[s]` is allowed but **not required**)
- `wide[s]`
- `high_vol[s]` **or** `vol_lt_prior2[s]` (S2: up-thrust volume may be high **or** low/no-demand)
- `close_frac[s] ≤ 0.25` (close on/near lows)
- Known at close of `s`

At least one valid W1 or W2 seed with `s+1 ≤ t-1` (for W1) or `s ≤ t-1` (for W2) is required.

### Background flag

```text
BG_WEAK[t] = Location(A1) AND SOW_seed(A2)
```

Known at the close of bar `t` only using information `≤ t`.

---

## Stage B — No Demand event (`t_event`)

### Source grounding

S2: up-bar; narrow spread; volume less than previous two bars; close in the middle or low; after weakness.

### Morphology (`SOURCE-EXPLICIT` + close/narrow freezes)

Bar `t` is a **No Demand indication** if all hold:

1. `up_bar[t]`
2. `narrow[t]`
3. `vol_lt_prior2[t]`
4. `close_frac[t] ≤ 0.50`  (“middle or low”)
5. `BG_WEAK[t]` is true  (**context mandatory** — ND without background is Control A material, not Treatment)

```text
t_event = t   # close of the No Demand bar
```

**Initial indication only.** Not yet eligible for outcomes.

---

## Stage C — Confirmation (`t_confirmation`)

### Source grounding

S2 requires subsequent result validation; S3: next bar should be a down-bar to confirm No Demand under weak background.

### Rule (`SOURCE-INSPIRED ADAPTATION`)

Let `u = t_event + 1` (must exist and be complete).

Confirmation succeeds iff:

```text
down_bar[u] is true
```

```text
t_confirmation = u
t_sequence_complete = t_confirmation
```

If bar `u` is missing (gap), confirmation **fails** and the indication is discarded (no outcome eligibility).

If `down_bar[u]` is false, the indication is a **failed confirmation** — recorded only for optional descriptive failure tables; **not** Treatment C; **not** used to redefine the event with future information.

**Timestamp separation (mandatory):**

```text
t_event < t_confirmation
```

Outcomes use information **strictly after** `t_confirmation`.

---

## Treatment and controls (null design — frozen before outcomes)

### Treatment C — Complete VSA sequence

```text
BG_WEAK[t_event]
  AND No Demand morphology at t_event
  AND down_bar confirmation at t_confirmation = t_event+1
```

Observation becomes outcome-eligible at `t_sequence_complete = t_confirmation`.

### Control A — Morphology without VSA background

Same No Demand morphology at some `t`:

- `up_bar`, `narrow`, `vol_lt_prior2`, `close_frac ≤ 0.50`
- **`BG_WEAK[t]` is false**
- Same confirmation rule: `down_bar[t+1]` required for inclusion in the A-vs-C comparison set (so both arms share confirmation timing structure)

**Purpose:** Does background add information beyond the ND candle shape + next down-bar?

### Control B — Background without No Demand effort/result signature

At some `t`:

- `BG_WEAK[t]` true
- `up_bar[t]` true
- Location A1 true (same near-high context)
- **Fails** at least one of: `narrow[t]`, `vol_lt_prior2[t]`, `close_frac[t] ≤ 0.50`  
  (i.e. an ordinary / non-ND up-bar into the weak background)
- Confirmation analog: require `down_bar[t+1]` for inclusion (matched confirmation structure)

**Purpose:** Does the ND effort/result signature add information beyond “up-bar near highs after SOW seed, then a down-bar”?

### Explicit non-nulls

- **Not** “all random bars”
- **Not** signed-volume quintiles
- **Not** Strategy 50 TR springs

### Primary contrast

**C vs A** is the primary null contrast.

**C vs B** is the secondary mechanism contrast (does the ND signature matter given background?).

Secondary cannot promote a failed primary into `SUPPORTED`.

---

## Outcome concept (mechanism only — do not compute in Step 1)

Eligibility clock: first outcome bar is `t_confirmation + 1` (no same-bar contamination).

Horizons (15-minute bars): **`H ∈ {4, 8, 16}`** only  
(= 1h, 2h, 4h). No additional horizons. No horizon search after results.

### Primary outcome

```text
DOWN_CLOSE(H) = 1  iff  close[t_confirmation + H] < close[t_confirmation]
```

Interpretation: net progress in the validated weakness direction over horizon H.

### Companion mechanism outcome (predeclared; not a rescue)

```text
FAIL_CLEAR_ND(H) = 1  iff  max(high[t_confirmation+1 … t_confirmation+H]) ≤ high[t_event]
```

Interpretation: inability to clear the No Demand high (failed upside continuation through the indication).

### Explicit non-outcomes for pass/fail

- P&L, win rate with stops/targets, profit factor  
- MFE/MAE optimization  
- Any frictioned trade simulation  

Those may appear only in a later step **after** mechanism verdict, if ever, under a new freeze.

---

## Statistical test (frozen)

For each horizon H:

- `p_C(H) = mean DOWN_CLOSE(H)` in Treatment C  
- `p_A(H) = mean DOWN_CLOSE(H)` in Control A  
- Primary statistic: `Δ(H) = p_C(H) − p_A(H)`
- Two-proportion test (normal approximation) or Fisher exact if any expected cell `< 5`
- Two-sided α = 0.05 on IS for discovery reporting
- Validation and OOS require **same sign** of `Δ(H)` as IS for stability

Companion `FAIL_CLEAR_ND` uses the same contrast structure descriptively; it cannot alone award `SUPPORTED`.

### Pass / fail criterion (mechanism, not profit)

| Label | Rule |
| --- | --- |
| `SUPPORTED` | For **at least two** of `H∈{4,8,16}`, `Δ(H)` has the same sign in IS, Validation, and OOS; IS two-sided p ≤ 0.05 for those horizons; each of C and A has `n ≥ 30` in IS and `n ≥ 20` in OOS for those horizons |
| `NOT SUPPORTED` | Primary contrast fails the above |
| `INCONCLUSIVE` | Sample sizes below floors in IS or OOS, or sign instability without a clear kill |

Secondary C vs B: descriptive label `ND_SIGNATURE_ADDS` / `ND_SIGNATURE_DOES_NOT_ADD` using the same multi-split sign rule on `Δ_{C−B}(H)`; cannot change the primary label.

---

## Event dependence (frozen)

| Rule | Freeze |
| --- | --- |
| Overlapping ND events | If a new `t_event` would fall inside `[t_event_prev, t_confirmation_prev]`, skip it |
| Minimum separation | After a completed or failed confirmation attempt, next eligible `t_event` must satisfy `t_event ≥ t_event_prev + 3` |
| Multiple events from same SOW seed | Allowed if separation rule holds; each observation is a separate row |
| Session boundaries | Allowed to span Globex sessions |
| Missing bars / gaps | If any bar required for morphology, seed next-bar, confirmation, or horizon path is missing, discard that observation |
| Scheduled macro events | **No filter** in primary (Strategy 09 already closed impulse/fade; do not reopen as a VSA rescue). Optional descriptive stratification by “within 30m of frozen event timestamps” only after primary verdict, without changing labels |
| Rolls / continuity | Use continuous contract series as-is; no special roll deletion beyond existing continuous construction |

---

## Missing-data treatment

- Require finite OHLCV on all bars used in predicates and horizons.  
- `volume` in the continuous file is documented min=1 (Strategy 27); treat non-finite volume as missing → discard.  
- Zero spread bars: `close_frac` undefined for ND close rule → not an ND event (cannot satisfy middle/low meaningfully).  

---

## Information boundary / lookahead prohibitions

| Object | Known at |
| --- | --- |
| Medians / ATR at t | End of bar t (using bars ≤ t only; medians use ≤ t−1) |
| SOW seed W1 | End of bar s+1 |
| SOW seed W2 | End of bar s |
| BG_WEAK[t] | End of bar t |
| No Demand event | End of `t_event` |
| Confirmation | End of `t_confirmation` |
| Outcomes | Bars **after** `t_confirmation` only |

**Prohibited:**

- Future volume, highs, lows, closes to build background or ND  
- Using confirmation success to rewrite whether `t_event` “was” No Demand  
- Using outcome-window path to accept/reject confirmation  
- Same-bar outcome leakage (outcomes start at `t_confirmation+1`)  
- Forward returns inside event construction  
- Signed volume / CVD as a substitute for VSA effort  
- Expanding horizons or thresholds after seeing Δ  

---

## NQ adaptation summary

| Transferable | Implementation |
| --- | --- |
| Volume–spread–close relationship | Unsigned 15m OHLCV grammar |
| Effort vs result | SOW seeds + ND low-effort morphology |
| Background + confirmation | Stages A–C |
| Path of least resistance | `DOWN_CLOSE` / `FAIL_CLEAR_ND` |

| Non-transferable | Rule |
| --- | --- |
| Specialist / syndicate intent | Excluded |
| TradeGuider software signals | Excluded |
| Equity float absorption stories | Excluded |
| CVD as “true VSA” | Excluded (and Strategy 27-killed as flow) |

---

## Timeframe freeze

| Choice | Value |
| --- | --- |
| Primary | 15-minute Globex-aligned from 1m |
| Rationale | S2 allows any timeframe; 15m supports chronological power on multi-year NQ; comparable construction to Strategy 50 without importing TR grammar |
| Deferred | Daily VSA grammar — **not** to be scanned after 15m outcomes to rescue a fail |

---

## Contamination lock (analysis rules)

An analysis is **rejected as off-preregistration** if it:

1. Reports volume→return IC / Spearman as the primary result (Strategy 27 rebrand)  
2. Uses CVD or signed OHLCV as the event  
3. Drops `BG_WEAK` and still calls the result “VSA”  
4. Drops confirmation and measures outcomes from `t_event` while calling it Treatment C  
5. Requires Strategy 50 TR spring/upthrust campaign grammar and relabels it VSA  
6. Sweeps narrow/volume/close thresholds or horizons after outcomes exist  

---

## FROZEN BEFORE OUTCOME ANALYSIS

The following are locked. No optimization loop after this point.

1. **Source set:** S1–S4 as above.  
2. **Primary sequence:** BG weakness → No Demand → down-bar confirmation → mechanism outcomes.  
3. **Background:** A1 location (`K=32`, `0.15*ATR20`) + A2 SOW seed (`L=24`, W1/W2).  
4. **Context/location:** near recent highs only as in A1 (not mid-range ND as Treatment).  
5. **Effort:** unsigned volume; high_vol / wide for seeds; low relative volume for ND.  
6. **Result:** spread = high−low; no-progress rule for W1; ND narrow spread.  
7. **Volume definition:** sum of 1m unsigned volumes; no CVD/signed.  
8. **Spread definition:** high−low; narrow ≤ prior-20 median.  
9. **Close location:** ND `close_frac ≤ 0.50`; W2 `≤ 0.25`.  
10. **Event:** Stage B morphology + BG_WEAK.  
11. **Confirmation:** Stage C `down_bar[t_event+1]`; `t_event < t_confirmation`.  
12. **Timeframe:** 15m Globex-aligned.  
13. **NQ adaptation:** transferable/non-transferable rules above.  
14. **Controls:** A = ND+confirm without BG; B = BG+up+confirm without ND signature; primary contrast C vs A.  
15. **Primary outcome:** `DOWN_CLOSE(H)`.  
16. **Horizons:** `{4,8,16}` only.  
17. **Event dependence:** separation, gap, overlap rules above.  
18. **Missing data:** discard incomplete observations.  
19. **Chronological split:** IS 2010–2021 / Val 2022–2024 / OOS 2025–2026 via `common.splits`.  
20. **Statistical test:** two-proportion Δ(C−A); α=0.05 IS; multi-split sign stability.  
21. **Pass/fail:** table above (`SUPPORTED` / `NOT SUPPORTED` / `INCONCLUSIVE`).  
22. **Lookahead rules:** information boundary table above.

---

## Step 1 stop rule

This preregistration ends Step 1.

**Do not** in this step:

- scan the historical dataset for events  
- count events  
- calculate returns, P&L, or win rate  
- optimize thresholds  
- compare signals for profitability  
- modify definitions after peeking at outcomes  

Step 2, if opened later, implements extraction under these freezes only.
