# Step 3 — Destination asymmetry: stability + orthogonal conditioning

**Status:** Complete (mechanism description only).
**Parent:** Steps 0–2 frozen.
**Focus:** destination / recycling after →NORMAL — **not** magnitude, **not** trading.

Primary horizon: **30m**. Secondary: **60m**. Minimum n per origin cell for eligible claims: **200**.

---

## Frozen wait terciles (IS only, before destination stratification)

- **CompExit**: n_IS=16429, q33=2.0, q67=5.0
- **ExpExit**: n_IS=20835, q33=4.0, q67=15.0

---

## 1. Chronological split stability

Differences are B−A for CompExit and D−C for ExpExit.

### CompExit: A→NORMAL vs B→NORMAL

| slice | n_a | n_b | eligible | return_a | return_b | return_diff_pp | opp_a | opp_b | opp_diff_pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POOLED | 8618 | 13599 | True | 59.5% | 53.3% | -6.3 | 50.3% | 54.5% | +4.2 |
| IS | 6066 | 8990 | True | 59.7% | 53.8% | -5.9 | 51.4% | 55.2% | +3.8 |
| Validation | 1619 | 2985 | True | 58.7% | 51.1% | -7.6 | 47.5% | 54.2% | +6.7 |
| OOS | 933 | 1624 | True | 60.2% | 54.7% | -5.5 | 47.8% | 51.1% | +3.3 |

### ExpExit: C→NORMAL vs D→NORMAL

| slice | n_a | n_b | eligible | return_a | return_b | return_diff_pp | opp_a | opp_b | opp_diff_pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POOLED | 22560 | 5231 | True | 49.9% | 64.8% | +14.9 | 68.4% | 53.6% | -14.8 |
| IS | 15498 | 3849 | True | 51.3% | 66.1% | +14.8 | 67.1% | 53.2% | -13.9 |
| Validation | 4620 | 853 | True | 46.8% | 63.8% | +17.0 | 71.7% | 52.1% | -19.6 |
| OOS | 2442 | 529 | True | 47.0% | 56.7% | +9.7 | 70.9% | 59.7% | -11.2 |

Secondary horizon tables: `results/step3_split_stability.csv`.

---

## 2. Wait-to-NORMAL stratification (confounder diagnostic)

### CompExit

| wait_stratum | n_a | n_b | eligible | return_diff_pp | opp_diff_pp | return_rate_a | return_rate_b | opposite_rate_a | opposite_rate_b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SHORT | 3641 | 6358 | True | -5.3 | +2.7 | 0.6493 | 0.5963 | 0.4721 | 0.4992 |
| MEDIUM | 2059 | 3487 | True | -6.9 | +6.6 | 0.5969 | 0.5277 | 0.4823 | 0.5483 |
| LONG | 2918 | 3754 | True | -9.7 | +6.4 | 0.5274 | 0.4307 | 0.5548 | 0.6188 |

### ExpExit

| wait_stratum | n_a | n_b | eligible | return_diff_pp | opp_diff_pp | return_rate_a | return_rate_b | opposite_rate_a | opposite_rate_b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SHORT | 6916 | 2728 | True | +13.3 | -12.6 | 0.5500 | 0.6826 | 0.6342 | 0.5081 |
| MEDIUM | 6995 | 1890 | True | +12.3 | -11.5 | 0.4988 | 0.6222 | 0.6763 | 0.5608 |
| LONG | 8649 | 613 | True | +11.5 | -14.4 | 0.4596 | 0.5742 | 0.7313 | 0.5873 |

---

## 3. Orthogonal conditioning (one covariate at a time)

Event-bar only. No crossed combinations.

### CompExit

#### volatility_state

| level | n_a | n_b | eligible | return_diff_pp | opp_diff_pp |
| --- | --- | --- | --- | --- | --- |
| HIGH_VOLATILITY | 3111 | 5466 | True | -6.1 | +6.1 |
| LOW_VOLATILITY | 2650 | 3810 | True | -5.8 | +4.1 |
| NORMAL_VOLATILITY | 2857 | 4323 | True | -5.6 | +1.5 |

#### volume_state

| level | n_a | n_b | eligible | return_diff_pp | opp_diff_pp |
| --- | --- | --- | --- | --- | --- |
| HIGH_VOLUME | 2131 | 3978 | True | -4.2 | +2.7 |
| LOW_VOLUME | 3233 | 4233 | True | -7.0 | +4.1 |
| NORMAL_VOLUME | 3254 | 5388 | True | -5.1 | +4.0 |

#### tod_block

| level | n_a | n_b | eligible | return_diff_pp | opp_diff_pp |
| --- | --- | --- | --- | --- | --- |
| FIRST_30 | 506 | 1516 | True | -6.0 | +0.3 |
| 1000_1200 | 2945 | 4533 | True | -9.9 | +7.1 |
| 1200_1400 | 3109 | 4142 | True | -6.3 | +4.3 |
| 1400_1600 | 2058 | 3408 | True | -5.7 | +3.2 |

### ExpExit

#### volatility_state

| level | n_a | n_b | eligible | return_diff_pp | opp_diff_pp |
| --- | --- | --- | --- | --- | --- |
| HIGH_VOLATILITY | 8294 | 1992 | True | +14.4 | -16.3 |
| LOW_VOLATILITY | 6731 | 1441 | True | +12.8 | -13.4 |
| NORMAL_VOLATILITY | 7535 | 1798 | True | +16.9 | -14.1 |

#### volume_state

| level | n_a | n_b | eligible | return_diff_pp | opp_diff_pp |
| --- | --- | --- | --- | --- | --- |
| HIGH_VOLUME | 8160 | 1612 | True | +14.3 | -13.7 |
| LOW_VOLUME | 6141 | 1669 | True | +15.0 | -15.3 |
| NORMAL_VOLUME | 8259 | 1950 | True | +16.6 | -17.6 |

#### tod_block

| level | n_a | n_b | eligible | return_diff_pp | opp_diff_pp |
| --- | --- | --- | --- | --- | --- |
| FIRST_30 | 2023 | 379 | True | +3.1 | +7.8 |
| 1000_1200 | 6786 | 1731 | True | +16.9 | -22.3 |
| 1200_1400 | 8088 | 1997 | True | +17.3 | -14.0 |
| 1400_1600 | 5663 | 1124 | True | +10.4 | -12.0 |

---

## Predeclared criteria checklist

### CompExit_A_vs_B

- **Interesting (either endpoint):** True
- **return_to_origin:** pass=True; pooled=True; same_sign_splits=True; not_wait_only=True; not_tiny_only=True; pooled_diff=-0.06251742910874014
- **reach_opposite:** pass=True; pooled=True; same_sign_splits=True; not_wait_only=True; not_tiny_only=True; pooled_diff=0.042266675547502075

### ExpExit_C_vs_D

- **Interesting (either endpoint):** True
- **return_to_origin:** pass=True; pooled=True; same_sign_splits=True; not_wait_only=True; not_tiny_only=True; pooled_diff=0.1485915593210687
- **reach_opposite:** pass=True; pooled=True; same_sign_splits=True; not_wait_only=True; not_tiny_only=True; pooled_diff=-0.14806830461067477

---

## Leakage / scope audit

```text
LOOKAHEAD_CHECK = PASS
WAIT_CUTS_FROZEN_BEFORE_DESTINATION_CLAIMS = True
COVARIATES_AT_EVENT_BAR_ONLY = True
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
```

---

## STEP 3 VERDICT

- **CompExit destination asymmetry:** interesting=True (return pass=True, opposite pass=True).
- **ExpExit destination asymmetry:** interesting=True (return pass=True, opposite pass=True).
- Criteria require pooled presence, same sign across eligible chronological splits, breadth beyond a single tiny subgroup, and survival under wait stratification.
- Orthogonal tables are descriptive supports for the same question — not a search for the largest cell.
- **Still not a strategy.** Surviving asymmetries are mechanism leads only.

## NEXT RESEARCH QUESTION

If any Step 3 destination asymmetry is marked interesting, is it best understood as a **range-recycling mechanism** that should next be tested with a *matched* wait design (or wait-conditioned event definition) before any directional trade hypothesis? If none survive, which frozen orthogonal dimension at the event bar shows the most *stable* within-family destination separation — still without constructing a trade?

_Do not answer by building a strategy in this step._
