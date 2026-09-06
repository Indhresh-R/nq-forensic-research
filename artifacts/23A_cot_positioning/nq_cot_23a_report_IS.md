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
