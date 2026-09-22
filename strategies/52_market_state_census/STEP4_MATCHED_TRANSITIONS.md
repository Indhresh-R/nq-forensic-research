# Step 4 — Matched transition experiment

**Status:** Complete (mechanism description only).
**Parent:** Steps 0–3 frozen.
**Question:** After making C/D (and A/B) transitions more comparable on **pre-event geometry**, does destination asymmetry remain?

This step does **not** claim causality, continuation/reversal, or a trade.

---

## Matching recipe (frozen CEM)

`wait_stratum × volatility × volume × TOD × origin_run tercile × pre_range_atr tercile × pre_er tercile × dist_mid_atr tercile`

Geometry terciles frozen on IS within family (see `step4_tercile_cuts_frozen.json`).

- **CompExit** cuts available for: origin_run_bars, pre_range_atr, pre_er, dist_mid_atr
- **ExpExit** cuts available for: origin_run_bars, pre_range_atr, pre_er, dist_mid_atr

---

## Unmatched vs CEM estimates (primary horizon 30m)

### ExpExit (primary): D − C

| design | n_a | n_b | retained_frac | n_strata | return | opposite |
| --- | --- | --- | --- | --- | --- | --- |
| unmatched | 22560 | 5231 | 1.0000 | nan | +14.9 pp | -14.8 pp |
| CEM | 5803 | 2242 | 0.2690 | 234.000 | +12.6 pp | -12.8 pp |

### CompExit (secondary): B − A

| design | n_a | n_b | retained_frac | n_strata | return | opposite |
| --- | --- | --- | --- | --- | --- | --- |
| unmatched | 8618 | 13599 | 1.0000 | nan | -6.3 pp | +4.2 pp |
| CEM | 5329 | 7100 | 0.5137 | 404.000 | -3.1 pp | +2.0 pp |

Full table incl. 60m: `results/step4_matched_estimates.csv`.

---

## Covariate balance (SMD, treatment − control)

### ExpExit_C_vs_D

| covariate | smd_before | smd_after | mean_a_before | mean_b_before | mean_a_after | mean_b_after |
| --- | --- | --- | --- | --- | --- | --- |
| wait_to_event | -0.7245 | -0.4396 | 17.204 | 6.9070 | 11.360 | 5.3572 |
| origin_run_bars | -0.3341 | -0.2394 | 27.962 | 20.196 | 17.798 | 13.071 |
| pre_range_atr | -0.5733 | -0.3780 | 3.7814 | 2.5252 | 2.9027 | 2.0319 |
| pre_er | 0.4157 | 0.1510 | 0.3495 | 0.4941 | 0.5575 | 0.6136 |
| dist_mid_atr | -0.3151 | -0.3141 | 0.9332 | 0.6754 | 0.8495 | 0.5751 |
| dist_edge_atr | -0.5125 | -0.2871 | 0.9575 | 0.5872 | 0.6018 | 0.4408 |

### CompExit_A_vs_B

| covariate | smd_before | smd_after | mean_a_before | mean_b_before | mean_a_after | mean_b_after |
| --- | --- | --- | --- | --- | --- | --- |
| wait_to_event | -0.1666 | -0.1038 | 5.7626 | 4.7685 | 6.2465 | 5.5226 |
| origin_run_bars | 0.1047 | -0.0170 | 16.421 | 18.644 | 16.698 | 16.338 |
| pre_range_atr | -0.0387 | -0.0527 | 2.2419 | 2.1935 | 2.3090 | 2.2343 |
| pre_er | 0.2275 | 0.1318 | 0.5881 | 0.6673 | 0.5883 | 0.6328 |
| dist_mid_atr | 0.0897 | 0.0183 | 0.7031 | 0.7567 | 0.7744 | 0.7866 |
| dist_edge_atr | -0.2252 | -0.1519 | 0.4179 | 0.3401 | 0.3801 | 0.3306 |

---

## Leave-one-in diagnostics (drop one geometry tercile from CEM key)

### ExpExit_C_vs_D

| dropped_factor | n_strata | retained_frac | return | opposite |
| --- | --- | --- | --- | --- |
| origin_run_bars_tercile | 315 | 0.4834 | +13.7 pp | -14.7 pp |
| pre_range_atr_tercile | 328 | 0.3979 | +12.0 pp | -12.1 pp |
| pre_er_tercile | 325 | 0.5023 | +12.2 pp | -15.1 pp |
| dist_mid_atr_tercile | 316 | 0.4580 | +12.8 pp | -13.0 pp |

### CompExit_A_vs_B

| dropped_factor | n_strata | retained_frac | return | opposite |
| --- | --- | --- | --- | --- |
| origin_run_bars_tercile | 437 | 0.7418 | -5.5 pp | +3.9 pp |
| pre_range_atr_tercile | 483 | 0.6840 | -3.7 pp | +2.3 pp |
| pre_er_tercile | 434 | 0.6444 | -3.8 pp | +2.4 pp |
| dist_mid_atr_tercile | 434 | 0.6964 | -3.9 pp | +2.3 pp |

---

## Predeclared classification

### ExpExit_C_vs_D

- **Overall:** `A_SURVIVES`
- **Interpretation hint:** `A_SURVIVES`
- Unmatched return diff: +14.9 pp
- Matched return diff: +12.6 pp
- Unmatched opposite diff: -14.8 pp
- Matched opposite diff: -12.8 pp
- Retained fraction: 0.26903655151657024
- Outcome-C candidate factors: []
- `return` class=`A_SURVIVES` ratio=0.8505189433507531
- `opposite` class=`A_SURVIVES` ratio=0.8623225017985853

### CompExit_A_vs_B

- **Overall:** `B_COMPOSITIONAL`
- **Interpretation hint:** `B_COMPOSITIONAL`
- Unmatched return diff: -6.3 pp
- Matched return diff: -3.1 pp
- Unmatched opposite diff: +4.2 pp
- Matched opposite diff: +2.0 pp
- Retained fraction: 0.513679947098694
- Outcome-C candidate factors: []
- `return` class=`B_COMPOSITIONAL` ratio=0.49153433376449773
- `opposite` class=`B_COMPOSITIONAL` ratio=0.4731756759621039

---

## Leakage / scope audit

```text
LOOKAHEAD_CHECK = PASS
MATCHING_USES_POST_EVENT_INFO = False
MATCHING_RECIPE_FROZEN = True
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
```

---

## STEP 4 VERDICT

- **ExpExit (primary):** `A_SURVIVES` / hint `A_SURVIVES`.
- **CompExit (secondary):** `B_COMPOSITIONAL` / hint `B_COMPOSITIONAL`.
- **Important caveats (not failures of the freeze):** ExpExit CEM retains only ~27% of events on common support (234 strata); wait SMD improves but remains imperfect (~−0.44 after). The residual association is therefore **conditional on matched support**, not a claim about all C/D exits.
- **Wording discipline:** surviving matched differences mean the origin cell still *associates* with destination behavior after coarsened pre-event geometry matching — **not** that we have identified a causal range-recycling mechanism, and **not** that a side should be traded.
- **Still forbidden:** continuation/reversal trade labels; P&L; optimizing the match.

## NEXT RESEARCH QUESTION

Given the Step 4 classification, what is the smallest *additional* pre-event structural feature (still frozen before outcomes) needed to decide whether the residual association is better described as **directionality-at-exit** vs **geometry-not-yet-matched** — without introducing a directional trade hypothesis?

_Do not answer by building a strategy in this step._
