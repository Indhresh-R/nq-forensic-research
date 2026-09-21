# Step 7 — Geometric null for prior-POC contact

This report uses `STEP7_PREREGISTRATION.md`. The reflection rule, the ±10% band, the 95-pair sample, and the verdict rule were not changed after the rates were computed. Step 5 remains `MECHANISM NOT SUPPORTED`. Step 6 remains `INCONCLUSIVE`. No entries, stops, targets, or P&L are computed.

## A. Frozen hypothesis

On the 95 Step 6 analysis pairs, does next-session bar contact with the prior POC band differ from contact with the mirror-image band around the next-session open?

The mirror keeps the absolute open-to-center distance and the band width `0.10 * prior_range`. It drops the identity of the prior POC.

## B. Frozen null

For each pair, with `O` the next-session first-bar open, `P` the prior POC, and `R` the prior profile range:

```text
d = P - O
P_null = O - d = 2*O - P
```

```text
abs(P_null - O) = abs(P - O)
```

Observed band: `[P - 0.10*R, P + 0.10*R]`

Null band: `[P_null - 0.10*R, P_null + 0.10*R]`

A touch is any next-session bar whose `[low, high]` intersects the band, using the Step 6 comparison. Both bands use the same bars. `P_null` is not clipped to the prior range. No randomization is used.

The construction is the deterministic counterfactual in the preregistration: the same touch rule if the prior POC sat at the mirror-image location around the open.

## C. Sample

| Stage | N | Result |
| --- | ---: | --- |
| Step 6 in-sample pairs | 95 | Unchanged |
| Pairs scored | 95 | |
| Excluded | 0 | |
| Recomputed POC-band touches vs Step 6 `touched_poc_band` | 70 and 70 | Match on every row |
| Recomputed exact crossings of `P` vs Step 6 `crossed_poc` | 67 and 67 | Match on every row |
| Open, POC, range, bar count, VWAP proxy | 95 | Match Step 6 |
| Distance identity `abs(P_null - O) = abs(P - O)` | 95 | Maximum absolute error 0 |
| Half-width `0.10 * R` | 95 | Maximum absolute error about `1e-14` |
| First bar contains its open | 95 | |
| Open inside both bands, and both flags true | 38 | |
| `P_null` outside the prior profile, left unclipped | 40 | |

## D. Primary endpoint

| Statistic | Count | Rate |
| --- | ---: | ---: |
| POC-band touch | 70 / 95 | 0.736842 |
| Null-band touch | 76 / 95 | 0.800000 |
| Observed minus null | −6 / 95 | −0.063158 |

Decomposition of the same difference:

| Cell | Pairs |
| --- | ---: |
| Both bands | 58 |
| POC band only | 12 |
| Null band only | 18 |
| Neither | 7 |

`delta = (12 - 18) / 95`.

## E. Null summary

The preregistration specifies one reflected band per pair, not a randomization distribution. The null summary is that single counterfactual.

| Item | Value |
| --- | --- |
| Observed rate | 0.736842 |
| Null rate | 0.800000 |
| Null mean / median / standard deviation across draws | Not defined. No draws were run |
| Observed minus null | −0.063158 |
| Empirical tail probability | Not defined. No threshold and no draw distribution were preregistered |

## F. Secondary endpoints

These were defined before the primary rates were computed. They do not enter the verdict.

### Exact level

| Statistic | Count | Rate |
| --- | ---: | ---: |
| Bar contains `P` | 67 / 95 | 0.705263 |
| Bar contains `P_null` | 68 / 95 | 0.715789 |
| Observed minus null | −1 / 95 | −0.010526 |

Cells: both 50, `P` only 17, `P_null` only 18, neither 10.

### First-touch time

| Band | Touches | Median minutes among touches | Touches at 0 minutes |
| --- | ---: | ---: | ---: |
| POC band | 70 | 0 | 41 |
| Null band | 76 | 0 | 42 |

Paired order, with a non-touch later than any touch: POC band sooner on 23 pairs, null band sooner on 26, tie on 46.

### Migration distance

Mean `|VWAP - P| / R` is 0.526234. Mean `|VWAP - P_null| / R` is 0.523745. The POC distance minus the null distance is +0.002489.

The VWAP proxy is strictly closer to `P` on 48 pairs, strictly closer to `P_null` on 46, and tied on 1.

### Post-cross close imbalance

| Level | Crosses | Mean imbalance | Median | p25 | p75 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `P` | 67 | 29.70 | 89 | −686.5 | 639 |
| `P_null` | 68 | 8.85 | 10 | −660.75 | 481.25 |

Both levels are crossed on 50 pairs, which is above the preregistered instability cut of 15. On those 50, the POC imbalance minus the null imbalance has mean 23.42, median 15.5, p25 −277.25, and p75 368.25.

## G. Robustness

Same band-touch rule. None of these slices replaces the primary verdict.

| Slice | N | POC touches | Null touches | Observed minus null |
| --- | ---: | ---: | ---: | ---: |
| Open inside both bands | 38 | 38 | 38 | 0 |
| Open outside the band | 57 | 32 | 38 | −0.105263 |
| Prior POC location lower (`< 1/3`) | 22 | 15 | 16 | −0.045455 |
| Prior POC location middle | 38 | 27 | 34 | −0.184211 |
| Prior POC location upper (`>= 2/3`) | 35 | 28 | 26 | +0.057143 |

Every location bin has at least 15 pairs. The upper bin is the slice whose difference is positive. The open-inside slice contributes 0 to the paired count difference. The −6 pair gap in the primary table is the open-outside slice: 12 POC-only touches and 18 null-only touches.

Calendar description, using the preregistered cut `2026-06-20` and not used for the verdict:

| Block | N | POC touches | Null touches | Observed minus null |
| --- | ---: | ---: | ---: | ---: |
| Next session before 2026-06-20 | 46 | 30 | 33 | −0.065217 |
| Next session on or after 2026-06-20 | 49 | 40 | 43 | −0.061224 |

## H. Interpretation

**Descriptive fact.** On these 95 pairs the next session prints the prior POC ±10% band on 70 pairs. Step 6 already measured that rate. Forty of the reflected centers lie outside the prior profile and stay there.

**Null-calibrated evidence.** The same bars intersect the distance-matched mirror band on 76 pairs. The primary difference is −6 pairs, or −0.063158. Twelve pairs reach the POC band and miss the mirror. Eighteen do the reverse.

**Mechanism.** The proposed mechanism is that prior-POC location draws next-session trade beyond this geometry. The primary comparison shows the mirror band contacted more often than the POC band. The exact-level comparison is −1 pair. The open-outside slice, both calendar blocks, and the lower and middle POC-location bins have a negative difference. The upper location bin has a positive difference of +2 pairs (28 versus 26). That slice is reported because it was preregistered. The verdict rule does not use it.

No causal claim follows from these counts. The comparison does not identify why a path reached one band.

## I. Verdict

`MECHANISM NOT SUPPORTED`

The audit passed, including the recomputed POC-band count of 70. The frozen rule then assigns `MECHANISM SUPPORTED` only when the primary difference is strictly positive. The primary difference is −0.063158, so the result falls under `MECHANISM NOT SUPPORTED`.

The prior-volume-location branch is closed. This result does not open another LVN, POC, or volume-profile variant, and it does not authorize a trading test.
