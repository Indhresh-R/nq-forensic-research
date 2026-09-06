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
