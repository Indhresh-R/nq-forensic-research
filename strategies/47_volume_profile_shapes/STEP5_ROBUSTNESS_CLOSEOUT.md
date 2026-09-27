# Step 6 — Robustness close-out of LVN rejection

This report does not test profitability, entries, exits, stops, targets, or forward returns. It does not change the Step 4 or Step 5 definitions. A reject is not a trade.

## Scope conflict, preserved as written

`STEP6_PREREGISTRATION.md` already exists. It is a different, unrun study: prior-session volume **location / acceptance**. That file forbids LVN bands, traverse events, and reject events as inputs. It was not executed here and was not rewritten.

`VERDICT.md` already closed HVN → LVN → rejection after Step 5 and forbade a later filter rescue of the same object.

This file answers the robustness question against that already-frozen object:

> Does LVN rejection differ from the preregistered geometric null, and does that comparison survive the checks that were already specified?

No threshold was searched after the tables. No new LVN, rejection, horizon, or null formula was introduced. The only new aggregation is an outcome-blind chronological split of the same 34 primary rows (`code/step6_audit.py` → `results/step6_temporal_audit.csv`).

## A. Frozen definitions

**LVN / structural boundary.** A prior material gap from Step 2: adjacent major peaks with `separation >= 0.20` and `valley_depth >= 0.30`. The interaction target is the low-volume band: the maximal contiguous run of ticks between those peaks, containing the valley tick, with `volume <= 0.70 * min(left_peak_volume, right_peak_volume)`. Prices: `[valley_left_price, valley_right_price]`.

**Structural event.** Next analysis session’s first one-minute bar whose `[low, high]` intersects that band, approached from an accepted region (`lower_region` or `upper_region`). `open_in_band` touches are not in the primary sample. Measurement price is the touch-bar open.

**Rejection.** First competing HVN print inside the horizon, using the prior HVN prices, not the full region spans.

- Lower-region approach: reject when `low <= lower_hvn_price`; traverse when `high >= upper_hvn_price`.
- Upper-region approach: reject when `high >= upper_hvn_price`; traverse when `low <= lower_hvn_price`.
- Same bar both: `ambiguous_same_bar` (none occurred).
- Neither by the horizon: `remain`.

**Forward horizons.** H30, H60, H120, and `session_end`. Primary mechanism horizons: **H60** and **H120**. A bar is inside H when its open timestamp is at most `touch_ts + H` minutes.

**Matched null.** On every primary row both distances were positive, so the null is defined for all 34.

```text
null_traverse_prob = dist_to_approach / (dist_to_approach + dist_to_opposite)
null_reject_prob = 1 - null_traverse_prob
```

Distances use the touch-bar open and the two prior HVN prices. This is the one-dimensional Brownian first-barrier probability. It is not fitted to outcomes.

**Primary claim (Step 5 B).** On all primary rows:

```text
difference = mean(1{outcome == reject} - null_reject_prob)
```

Remain and traverse count as non-reject. Step 5 states that a rejection claim needs support from **B**, not only from the decided complementary test **A**. Tests C and D remove same-minute / touch-bar approach-HVN hits. They were preregistered before the tables.

No empirical p-value and no confidence interval were part of that design. None were added after the results.

## B. Sample audit

NQ only. The frozen trade window is 2026-03-25 through 2026-09-16. ES is not in this framework, so no NQ-versus-ES split exists to report.

| Stage | N |
| --- | ---: |
| Analysis sessions | 96 |
| Prior material gaps (Step 2) | 54 |
| Excluded: no later analysis session | 1 |
| Interaction sample after completeness and high/low sync | 53 |
| Excluded: no LVN-band touch | 14 |
| First LVN-band touches | 39 |
| Excluded from primary: `open_in_band` (no approach side) | 5 |
| Approaches from outside / other_inside | 0 |
| Primary events, each horizon | 34 |
| Null undefined | 0 |

Side of the 34 primary events: **12 lower → upper**, **22 upper → lower**.

All 34 next-session dates fall in **2026**. Counts by next-session month (event counts, not tests):

| Month | Events | Lower | Upper |
| --- | ---: | ---: | ---: |
| 2026-03 | 1 | 1 | 0 |
| 2026-04 | 6 | 2 | 4 |
| 2026-05 | 5 | 1 | 4 |
| 2026-06 | 7 | 2 | 5 |
| 2026-07 | 9 | 2 | 7 |
| 2026-08 | 4 | 3 | 1 |
| 2026-09 | 2 | 1 | 1 |

Month blocks have 1–9 events. They are sample accounting. They are not robustness tests.

## C. Primary result

Statistic: Null B, unconditional reject rate minus mean `null_reject_prob`.

The null probability is the same at every horizon because it uses only touch geometry. On the 34 rows its distribution is:

| | min | p25 | median | p75 | max | mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `null_reject_prob` | 0.458 | 0.762 | 0.867 | 0.959 | 0.996 | 0.835 |

Row-level effect `1{reject} - null_reject_prob` at H60: p25 **−0.812**, median **+0.012**, p75 **+0.131**, mean **−0.276**. The mean sits in the left tail: non-rejects against a high geometric reject probability pull the average down. The median near zero is not the preregistered statistic. The preregistered statistic is the mean.

| Horizon | Test | N | Observed reject | Null mean | Observed − null | Reject N | Same-minute | Delayed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H60 | B unconditional | 34 | 0.559 | 0.835 | **−0.276** | 19 | 8 | 11 |
| H120 | B unconditional | 34 | 0.647 | 0.835 | **−0.187** | 22 | 8 | 14 |

H60 outcomes: reject 19, remain 14, traverse 1, ambiguous 0.

H120 outcomes: reject 22, remain 9, traverse 3, ambiguous 0.

Null A (decided rows only) is positive at these horizons (H60 **+0.105**, N=20; H120 **+0.046**, N=25). Step 5 preregistered A as the mirror of the killed traverse test, not as independent evidence that rejection works.

## D. Robustness

Every preregistered comparison is below. Descriptive slices were specified before the results and are not a new primary sample. A positive cell in a slice does not override a negative pooled Null B.

| Check | Horizon | N | Observed | Null mean | Observed − null |
| --- | --- | ---: | ---: | ---: | ---: |
| B unconditional | H30 | 34 | 0.500 | 0.835 | −0.335 |
| B unconditional | H60 | 34 | 0.559 | 0.835 | −0.276 |
| B unconditional | H120 | 34 | 0.647 | 0.835 | −0.187 |
| B unconditional | session_end | 34 | 0.765 | 0.835 | −0.070 |
| D no touch-bar approach hit | H60 | 26 | 0.423 | 0.803 | −0.380 |
| D no touch-bar approach hit | H120 | 26 | 0.538 | 0.803 | −0.264 |
| C delayed decided | H60 | 12 | 0.917 | 0.783 | +0.134 |
| C delayed decided | H120 | 17 | 0.824 | 0.785 | +0.038 |
| B lower → upper | H60 | 12 | 0.667 | 0.853 | −0.186 |
| B upper → lower | H60 | 22 | 0.500 | 0.824 | −0.324 |
| B lower → upper | H120 | 12 | 0.750 | 0.853 | −0.103 |
| B upper → lower | H120 | 22 | 0.591 | 0.824 | −0.234 |
| B clean | H60 | 11 | 0.818 | 0.869 | −0.050 |
| B clean | H120 | 11 | 0.909 | 0.869 | +0.041 |
| B both regions sized | H60 | 20 | 0.550 | 0.843 | −0.293 |
| B both regions sized | H120 | 20 | 0.600 | 0.843 | −0.243 |

Null C positive is the decided-path mirror after dropping same-minute rejects. It is not Null B. The `clean` H120 cell is **+0.041** on 11 rows. The pooled H120 Null B on all 34 rows is **−0.187**. One narrow slice does not validate the mechanism.

Not run, because they are not in the frozen framework:

- ES versus NQ
- a second independent multi-year sample
- session-segment filters
- a new matched non-LVN location definition
- any retuned separation, depth, width, or horizon

## E. Temporal stability

The frozen window is one partial year. Multi-year blocks are not available. The outcome-blind split is the calendar midpoint of that window, **2026-06-20**. Ordering the 34 events by next-session date and cutting at 17/17 lands on the same partition (last early date 2026-06-09, first late date 2026-06-24). Those are one split, not two confirmations.

Null B on that split:

| Horizon | Block | N | Dates | Observed | Null mean | Observed − null |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| H60 | early | 17 | 2026-03-30 to 2026-06-09 | 0.529 | 0.836 | −0.306 |
| H60 | late | 17 | 2026-06-24 to 2026-09-15 | 0.588 | 0.833 | −0.245 |
| H120 | early | 17 | 2026-03-30 to 2026-06-09 | 0.588 | 0.836 | −0.247 |
| H120 | late | 17 | 2026-06-24 to 2026-09-15 | 0.706 | 0.833 | −0.128 |

The shortfall versus the geometric null is present in both halves at both primary horizons. The late H120 gap is smaller than the early gap. With 17 events per half, that change is not a demonstrated trend. The effect is **not stable as a null-beating reaction**. It is **absent** relative to the preregistered null in both periods.

## F. Placebo / null validation

The frozen matched baseline is the geometric `null_reject_prob`, not a reshuffle of LVN labels. A label-randomization or relocated-LVN placebo was not in Step 5 and was not added after seeing the tables.

What that baseline already shows:

- Geometry known at the touch-bar open expects rejection about **83.5%** of the time, because the measurement price usually sits much closer to the approach HVN than to the opposite HVN.
- The observed unconditional reject rate is lower than that at H30, H60, H120, and session end.
- 8 of 19 H60 rejects are the same minute as the LVN touch. Removing touch-bar approach-HVN hits (Null D) widens the shortfall.
- Most rejects are `band_only`: they never clear the far LVN edge (H60: 18 of 19).

The raw reject count (19/34 at H60) is what nearby approach-HVN geometry produces. The same pipeline does not show an excess rejection once that matched null is applied.

## G. Verdict

`MECHANISM NOT SUPPORTED`

Preregistered rule: a rejection claim needs Null B, not only Null A. Null B is negative at H60 (−0.276) and H120 (−0.187), on both approach sides, on both chronological halves, and after removing same-minute touch-bar hits. The positive decided-path and single `clean` cells do not replace the pooled unconditional test.

No trading-rule test is authorized. No further LVN filter is authorized.
