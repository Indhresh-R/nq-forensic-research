# Hypothesis 23A — COT Positioning under Strategy-12 HIGH (IS only)

## Stage gate

**Val / OOS not scored.** Publish IS first per program discipline.

## Lag rule (audit)

Tuesday snapshot → Friday ~15:30 ET release → next session only (never Tue–Fri of snapshot week).

## Freeze

- Market: NASDAQ-100 Consolidated FutOnly
- Extreme: trailing 104-week z, then p10/p90 of trailing z
- Sides: `lev_fade`, `am_follow` only
- HIGH: Strategy-12 frozen `rng_psr` p66
- Panel rows (signal weeks ∩ sessions): **30,696**
- Soft IS candidates: **28**
- Strong IS candidates: **5**
- Provisional IS verdict tag: **`IS_PROMISING_PENDING_VAL`**

## Primary contrast H=30 — `lev_fade`

| Session | T+ | ALL+COT | HIGH+COT | HIGH long | Lift vs ALL | Lift vs HIGH-long |
|---------|----|---------|----------|-----------|-------------|-------------------|
| LONDON | 90 | 48.3% | 48.5% | 48.6% | +0.2pp | -0.0pp |
| NY_PM | 90 | 48.3% | 49.2% | 48.4% | +1.0pp | +0.8pp |
| NY_AM | 30 | 53.1% | 58.7% | 56.2% | +5.6pp | +2.5pp |
| ASIA | 15 | 47.7% | 51.7% | 49.3% | +4.0pp | +2.4pp |

## Primary contrast H=30 — `am_follow`

| Session | T+ | ALL+COT | HIGH+COT | HIGH long | Lift vs ALL | Lift vs HIGH-long |
|---------|----|---------|----------|-----------|-------------|-------------------|
| LONDON | 120 | 49.0% | 51.5% | 52.3% | +2.4pp | -0.8pp |
| NY_PM | 60 | 51.4% | 55.4% | 52.3% | +4.0pp | +3.1pp |
| NY_AM | 15 | 49.4% | 53.6% | 51.8% | +4.2pp | +1.8pp |
| ASIA | 30 | 46.8% | 48.0% | 50.3% | +1.1pp | -2.3pp |

## IS candidates (soft/strong)

| Tier | Signal | Session | T+ | H | HIGH+COT win | Lift vs ALL | Lift vs HIGH-long | n |
|------|--------|---------|----|---|--------------|-------------|-------------------|---|
| strong | am_follow | NY_AM | 15 | 60 | 54.9% | +6.5pp | +2.3pp | 233 |
| strong | lev_fade | NY_AM | 30 | 30 | 58.7% | +5.6pp | +2.5pp | 179 |
| strong | am_follow | NY_PM | 60 | 30 | 55.4% | +4.0pp | +3.1pp | 242 |
| strong | am_follow | NY_PM | 30 | 60 | 52.5% | +2.4pp | +1.1pp | 236 |
| strong | am_follow | NY_PM | 60 | 60 | 52.9% | +0.2pp | +1.2pp | 242 |
| soft | am_follow | NY_AM | 15 | 30 | 53.6% | +4.2pp | +1.8pp | 233 |
| soft | lev_fade | NY_AM | 30 | 60 | 55.3% | +4.2pp | +2.6pp | 179 |
| soft | lev_fade | ASIA | 15 | 30 | 51.7% | +4.0pp | +2.4pp | 205 |
| soft | lev_fade | ASIA | 90 | 30 | 55.5% | +3.0pp | +6.0pp | 164 |
| soft | lev_fade | ASIA | 15 | 60 | 51.2% | +2.9pp | -4.6pp | 205 |
| soft | am_follow | LONDON | 120 | 30 | 51.5% | +2.4pp | -0.8pp | 239 |
| soft | lev_fade | ASIA | 30 | 30 | 51.6% | +2.0pp | +1.4pp | 213 |
| soft | am_follow | LONDON | 60 | 30 | 53.4% | +2.0pp | +6.7pp | 238 |
| soft | lev_fade | ASIA | 180 | 60 | 51.6% | +2.0pp | -0.0pp | 190 |
| soft | lev_fade | ASIA | 30 | 120 | 51.9% | +1.9pp | -0.4pp | 212 |
| soft | am_follow | LONDON | 120 | 60 | 51.9% | +1.2pp | +3.1pp | 239 |
| soft | am_follow | ASIA | 180 | 60 | 52.9% | +1.1pp | +1.3pp | 206 |
| soft | lev_fade | ASIA | 30 | 60 | 51.9% | +0.9pp | +0.2pp | 212 |
| soft | am_follow | LONDON | 120 | 120 | 51.9% | +0.6pp | -2.5pp | 239 |
| soft | lev_fade | NY_PM | 90 | 120 | 49.2% | +0.6pp | -3.9pp | 199 |
| soft | lev_fade | LONDON | 60 | 30 | 49.7% | +0.0pp | +3.0pp | 199 |
| soft | am_follow | LONDON | 15 | 120 | 51.9% | -0.0pp | -4.4pp | 239 |
| soft | lev_fade | ASIA | 180 | 120 | 46.3% | -0.1pp | -10.2pp | 190 |
| soft | lev_fade | ASIA | 15 | 120 | 52.7% | -0.2pp | -1.8pp | 205 |
| soft | am_follow | NY_PM | 30 | 30 | 49.8% | -0.4pp | -5.3pp | 239 |
| soft | am_follow | LONDON | 60 | 120 | 49.6% | -0.8pp | +0.5pp | 238 |
| soft | am_follow | LONDON | 60 | 60 | 49.2% | -0.9pp | -0.2pp | 238 |
| soft | am_follow | LONDON | 30 | 120 | 49.8% | -1.1pp | -0.8pp | 253 |
| soft | am_follow | LONDON | 15 | 60 | 50.6% | -1.3pp | -4.3pp | 239 |
| soft | am_follow | NY_PM | 30 | 120 | 50.0% | -1.4pp | -3.5pp | 236 |
| soft | am_follow | LONDON | 30 | 60 | 51.8% | -1.8pp | +1.7pp | 253 |
| soft | am_follow | LONDON | 90 | 120 | 49.6% | -2.3pp | -2.1pp | 238 |
| soft | am_follow | LONDON | 90 | 60 | 47.9% | -3.1pp | -6.7pp | 238 |

## Hostile IS reading

IS shows multi-clock structure under freeze. **Next:** score Val once (no refit). Do not build an executable system yet (check A vs A* if Val/OOS hold).

## Pre-registered Val expectation (written BEFORE Val look)

Calibrate against this program's own kill history — same magnitude, same n-range:

| Prior | IS shape | Fate |
|-------|----------|------|
| 03 | best soft IS win **52.2%** | **C** kill |
| 04 | OOS spike **59.6%** but IS mean **−0.3** pts | **B→kill** |
| 16A | HIGH+bias ~**51–52%**, lifts ~1–3pp | **B→kill** |

23A headline: **58.7%** vs ALL **53.1%** (+5.6pp), vs HIGH-long **56.2%** (+2.5pp), **n=179**.
That sits in the same 2–6pp / low-hundreds-n band that routinely failed Val/OOS here.

**Base-rate expectation (pre-registered):** If 23A behaves like the program's typical prior,
Val will show **partial decay** of lifts, and OOS (when later unlocked) will likely show a
**year-flip or collapse toward baseline**. Surviving that base rate — especially on the
**HIGH+COT vs HIGH-long** incremental contrast — is the bar, not merely a non-zero Val win rate.

**Primary Val contrast to watch:** HIGH+COT vs HIGH-long (incremental sign on top of Strategy 12),
not HIGH+COT vs ALL+COT (which can partly restate activity-state).

## Multiplicity (written BEFORE Val look)

| Quantity | Count |
|----------|------:|
| Sessions | 4 (LONDON, NY_PM, NY_AM, ASIA) |
| Decision clocks | **20** |
| Horizons | **3** (30, 60, 120) |
| Frozen signals | **2** (`lev_fade`, `am_follow`) |
| **Grid cells scanned** | **20 × 3 × 2 = 120** |
| Eligible cells (HIGH+COT and ALL+COT both n≥60 on IS) | **110** |
| Soft / strong hits | 28 / **5** |
| Strong hit rate among eligible | **5 / 110 ≈ 4.5%** |

At conventional single-test false-positive rates (~5%), **5 strong hits from ~110 cells is
near what noise alone would produce**. Treat the headline cell as one draw from a large
search, not a solitary pre-specified test. Family-23 (23D still pending) raises the bar further.

## Multi-comparison note

Family 23 tests multiple external sources (23A COT, 23D cross-asset). One IS hit does not promote the family without acknowledging that multiplicity.


---

# Hypothesis 23A — Validation (one-shot, frozen IS definitions)

## Freeze confirmation

| Item | Status |
|------|--------|
| Decile / W=104 extremes | **unchanged** (features parquet; no refit) |
| Sides `lev_fade` / `am_follow` | **unchanged** |
| Strategy-12 HIGH p66 | **unchanged** (`nq_multi_sess_opp_thresholds_IS.json`) |
| Friday-lag join | **unchanged** |
| Splits | IS 2010–2021 / **Val 2022–2024** (OOS not scored) |
| Threshold adjustment on Val | **none** |

## Multiplicity (from IS pre-registration)

- Grid cells scanned: **120** (20 clocks × 3 H × 2 signals)
- Eligible IS cells (n≥60 both HIGH+COT & ALL+COT): **110**
- IS strong hits: **5** (~4.5% of eligible — near single-test noise rate)

## Pre-registered base-rate check

Expectation written in `results/IS.md` before this run: Val likely shows **partial decay**; incremental HIGH+COT vs HIGH-long is the decisive contrast.

**Val tag:** `VAL_PARTIAL_DECAY`

## Headline three-way — NY_AM `lev_fade` T+30 H30

| Split | ALL+COT | HIGH-long | HIGH+COT | Lift vs ALL | Lift vs HIGH-long | n_HIGH+COT |
|-------|---------|-----------|----------|-------------|-------------------|------------|
| IS | 53.1% | 56.2% | 58.7% | +5.6pp | +2.5pp | 179 |
| Validation | 45.8% | 57.4% | 50.0% | +4.2pp | -7.4pp | 42 |

## IS-strong cells — three-way at Validation

| Signal | Session | T+ | H | IS HIGH+COT | Val ALL+COT | Val HIGH-long | Val HIGH+COT | Val lift vs ALL | Val lift vs HIGH-long | Val n |
|--------|---------|----|---|-------------|-------------|---------------|--------------|----------------|-----------------------|-------|
| lev_fade | NY_AM | 30 | 30 | 58.7% | 45.8% | 57.4% | 50.0% | +4.2pp | -7.4pp | 42 |
| am_follow | NY_PM | 30 | 60 | 52.5% | 54.3% | 54.3% | 56.5% | +2.2pp | +2.2pp | 46 |
| am_follow | NY_PM | 60 | 30 | 55.4% | 58.6% | 50.0% | 66.1% | +7.5pp | +16.1pp | 56 |
| am_follow | NY_PM | 60 | 60 | 52.9% | 52.1% | 50.0% | 53.6% | +1.4pp | +3.6pp | 56 |
| am_follow | NY_AM | 15 | 60 | 54.9% | 47.9% | 50.9% | 51.2% | +3.3pp | +0.3pp | 41 |

IS-strong cells with Val lift vs ALL > 0: **5/5**; with Val lift vs HIGH-long > 0: **4/5**.

### H=30 session table — `lev_fade` (best IS win-lift clock, scored at Val)

| Session | T+ | Split | ALL+COT | HIGH-long | HIGH+COT | Lift vs ALL | Lift vs HIGH-long | n_HIGH+COT |
|---------|----|-------|---------|-----------|----------|-------------|-------------------|------------|
| LONDON | 90 | IS | 48.3% | 48.6% | 48.5% | +0.2pp | -0.0pp | 202 |
| LONDON | 90 | Validation | 51.0% | 45.4% | 55.9% | +4.8pp | +10.5pp | 68 |
| NY_PM | 90 | IS | 48.3% | 48.4% | 49.2% | +1.0pp | +0.8pp | 199 |
| NY_PM | 90 | Validation | 46.7% | 58.0% | 36.5% | -10.2pp | -21.5pp | 52 |
| NY_AM | 30 | IS | 53.1% | 56.2% | 58.7% | +5.6pp | +2.5pp | 179 |
| NY_AM | 30 | Validation | 45.8% | 57.4% | 50.0% | +4.2pp | -7.4pp | 42 |
| ASIA | 15 | IS | 47.7% | 49.3% | 51.7% | +4.0pp | +2.4pp | 205 |
| ASIA | 15 | Validation | 47.2% | 49.0% | 54.3% | +7.1pp | +5.3pp | 35 |

### H=30 session table — `am_follow` (best IS win-lift clock, scored at Val)

| Session | T+ | Split | ALL+COT | HIGH-long | HIGH+COT | Lift vs ALL | Lift vs HIGH-long | n_HIGH+COT |
|---------|----|-------|---------|-----------|----------|-------------|-------------------|------------|
| LONDON | 120 | IS | 49.0% | 52.3% | 51.5% | +2.4pp | -0.8pp | 239 |
| LONDON | 120 | Validation | 47.9% | 45.7% | 43.1% | -4.9pp | -2.7pp | 72 |
| NY_PM | 60 | IS | 51.4% | 52.3% | 55.4% | +4.0pp | +3.1pp | 242 |
| NY_PM | 60 | Validation | 58.6% | 50.0% | 66.1% | +7.5pp | +16.1pp | 56 |
| NY_AM | 15 | IS | 49.4% | 51.8% | 53.6% | +4.2pp | +1.8pp | 233 |
| NY_AM | 15 | Validation | 52.1% | 50.9% | 61.0% | +8.9pp | +10.0pp | 41 |
| ASIA | 30 | IS | 46.8% | 50.3% | 48.0% | +1.1pp | -2.3pp | 196 |
| ASIA | 30 | Validation | 42.8% | 53.6% | 41.2% | -1.6pp | -12.4pp | 34 |

## Reading vs pre-registered expectation

Matches pre-registered **partial decay** expectation. Incremental lift vs HIGH-long is weak or gone even if absolute HIGH+COT win rate looks non-zero. Treat as program-typical soft leftover unless multi-clock incremental lifts hold — they do not promote without OOS, and OOS is not unlocked here.

## Stop

- OOS **not** scored in this stage.
- 23D **not** started.


---

# Hypothesis 23A — OOS (documentation only; not a rescue)

Val already killed the headline incremental claim (`VAL_PARTIAL_DECAY`). OOS is recorded for historical parity with other dossier rows — **not** to promote.

## Freeze confirmation

| Item | Status |
|------|--------|
| Definitions vs IS | **unchanged** (zero adjustment) |
| Purpose | documentation triple IS/Val/OOS |

**OOS tag:** `OOS_INCREMENTAL_NEGATIVE`

## Headline three-way — NY_AM `lev_fade` T+30 H30

| Split | ALL+COT | HIGH-long | HIGH+COT | Lift vs ALL | Lift vs HIGH-long | n |
|-------|---------|-----------|----------|-------------|-------------------|---|
| IS | 53.1% | 56.2% | 58.7% | +5.6pp | +2.5pp | 179 |
| Validation | 45.8% | 57.4% | 50.0% | +4.2pp | -7.4pp | 42 |
| OOS | 47.5% | 54.7% | 43.5% | -4.1pp | -11.3pp | 69 |
| Y2025 | 47.1% | 57.6% | 42.9% | -4.2pp | -14.7pp | 49 |
| Y2026 | 48.9% | 48.3% | 45.0% | -3.9pp | -3.3pp | 20 |

## IS-strong cells — three-way at OOS

| Signal | Session | T+ | H | OOS ALL+COT | OOS HIGH-long | OOS HIGH+COT | lift vs ALL | lift vs HIGH-long | n |
|--------|---------|----|---|-------------|---------------|--------------|------------|-------------------|---|
| lev_fade | NY_AM | 30 | 30 | 47.5% | 54.7% | 43.5% | -4.1pp | -11.3pp | 69 |
| am_follow | NY_PM | 30 | 60 | 49.0% | 52.3% | 57.4% | +8.4pp | +5.1pp | 54 |
| am_follow | NY_PM | 60 | 30 | 47.6% | 61.1% | 43.9% | -3.8pp | -17.2pp | 57 |
| am_follow | NY_PM | 60 | 60 | 51.7% | 60.0% | 45.6% | -6.1pp | -14.4pp | 57 |
| am_follow | NY_AM | 15 | 60 | 46.8% | 53.9% | 57.5% | +10.7pp | +3.6pp | 40 |

## Multiplicity reminder

IS scanned **120** cells; 5 strong ≈ noise rate. Do not cherry-pick OOS soft leftovers.

## Family stop

- Verdict **C** (see `conclusion.md`).
- No 23B/23C rescue. 23D is a separate external-source sibling, not a COT retune.
