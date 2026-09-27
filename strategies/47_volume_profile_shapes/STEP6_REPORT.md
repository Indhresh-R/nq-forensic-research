# Step 6 — Prior volume location / acceptance

This report measures the objects in `STEP6_PREREGISTRATION.md`. Those definitions were not changed. LVN rejection results are not used as evidence. No entries, stops, targets, or P&L are computed.

The preregistration does not specify a location null, a p-value, a confidence interval, a chronological split, or a pass/fail rule. It says a later step may add a location null, and that this step only measures the location object. Those items were not added after the tables.

## A. Verdict

`INCONCLUSIVE`

## B. Frozen definitions

Prior geometry is taken from the stored Step 1 and Step 2 columns, before the next session is read.

| Field | Rule |
| --- | --- |
| `prior_poc` | Stored POC price |
| `prior_poc_location` | Stored POC index / range |
| Third shares | Step 2 lower, middle, and upper volume shares |
| `prior_dominant_third` | First of lower, middle, upper whose share equals the maximum |
| `prior_vw_std_norm`, `prior_poc_concentration_10` | Stored Step 1 concentration fields |
| `prior_range` | `prior_profile_high - prior_profile_low` |

Third cuts on a profile index `i = 0 .. R` are the Step 2 integer rule: lower if `3 * i < R`, middle if `3 * i < 2 * R` and the tick is not lower, upper otherwise.

Next-session measurements, from trade-built one-minute bars:

1. `open_to_poc_frac = (first_bar_open - prior_poc) / prior_range`.
2. Open third: the same integer cuts on the prior range. Labels are `prior_lower`, `prior_middle`, `prior_upper`, `outside_below`, `outside_above`.
3. A bar is near the prior POC when `[low, high]` intersects `[prior_poc - 0.10 * prior_range, prior_poc + 0.10 * prior_range]`. Report the share of bars that are near, and minutes from the first bar to the first near bar. Status is `no_touch` when none occurs.
4. `migration_frac = (next_vwap_proxy - prior_poc) / prior_range`, where `next_vwap_proxy` is the volume-weighted mean of bar typical price `(high + low + close) / 3`.
5. `crossed_poc` when some bar has `low <= prior_poc <= high`. After that bar, close imbalance is the count of later closes above the POC minus the count below. Closes equal to the POC are counted and are in neither side.

A pair is one analysis session and the next later analysis `session_date`. Missing calendar days are not filled with an invented session.

## C. Sample funnel

| Stage | N | Reason |
| --- | ---: | --- |
| Analysis sessions (`in_analysis_sample` matches `analysis_mask`) | 96 | Step 1 identity, verified again |
| Step 2 dates disagreeing with that sample | 0 | |
| Stored POC, POC location, `vw_std_norm`, or `poc_concentration_10` disagreeing with Step 1 | 0 | |
| Third shares not summing to 1, or dominant-third tie rule broken | 0 | |
| Excluded as a prior: no later analysis session | 1 | `2026-09-15` |
| Adjacent pairs in the sorted analysis-date list | 95 | Expected 95. Identity held |
| Excluded: incomplete next-session trades | 0 | Same completeness check as Step 3 |
| Excluded: high/low sync beyond 1.0 point | 0 | Mismatch would have stopped the run |
| Missing POC, third, or profile range | 0 | |
| Final location sample | 95 | |

All 95 next sessions are in 2026.

| Next-session month | Pairs |
| --- | ---: |
| 2026-03 | 3 |
| 2026-04 | 17 |
| 2026-05 | 16 |
| 2026-06 | 16 |
| 2026-07 | 17 |
| 2026-08 | 17 |
| 2026-09 | 9 |

Calendar spacing, included rather than dropped: 70 pairs are the next calendar day, 22 span 4 days, 2 span 5 days, and 1 spans 6 days. Those 25 gaps are the next analysis session in the date list. No session was invented for the hole.

## D. Primary results

No null expectation is defined. Observed − null, empirical p-values, and confidence intervals are blank for that reason.

| Summary | N | Observed |
| --- | ---: | --- |
| `open_to_poc_frac` mean / median (p25, p75) | 95 | 0.059 / 0.030 (−0.103, 0.177) |
| `open_to_poc_frac` min / max | 95 | −1.500 / 1.660 |
| Open inside the frozen 0.10 POC fraction (`abs(open_to_poc_frac) <= 0.10`) | 38 of 95 | 0.400 |
| Open third `prior_upper` / `prior_middle` / `prior_lower` / `outside_above` / `outside_below` | 95 | 30 / 27 / 20 / 13 / 5 |
| Touched prior POC band | 70 of 95 | 0.737 |
| Median minutes to first band touch, among touches | 70 | 0 |
| Touches on the first bar (0 minutes) | 41 of 70 | |
| `migration_frac` mean / median (p25, p75) | 95 | 0.079 / 0.054 (−0.365, 0.508) |
| Crossed the exact POC | 67 of 95 | 0.705 |
| Band touch without an exact cross | 3 | |
| After-cross close imbalance, mean / median | 67 | 29.7 / 89 |
| Imbalance above / below / tie | 67 | 36 / 31 / 0 |

The five preregistered summaries are the open-distance distribution, the dominant-third cross-tab, the POC-band touch rate and time, the migration distribution, and the after-cross imbalance. All five are in the sections below. None was dropped.

## E. POC results

Open distance is centered near zero and is wide. The median open is 0.030 of the prior range from the prior POC. The interquartile range runs from −0.103 to 0.177. The extremes are −1.500 and 1.660, so some next sessions open outside the prior profile.

70 of 95 next sessions print a bar that intersects the frozen 10% POC band. Among those 70, the median time to the first intersection is 0 minutes, and 41 intersections are the first bar. The median is an opening fact as often as it is a later visit. Mean time among touches is 127 minutes because the right tail reaches 1158 minutes.

67 sessions cross the exact POC. Three touch the band and never print the exact level. Every cross has at least one later close. Later closes finish above the POC on 36 sessions and below it on 31. The median imbalance is +89 closes. The mean is +29.7. The quartile range is −686.5 to +639. That spread is the result. There is no frozen rule that turns it into acceptance or rejection.

## F. Third-concentration results

Prior dominant third on the 95 pairs: lower 16, middle 48, upper 31.

Next open third by prior dominant third:

| Prior dominant third | Outside below | Prior lower | Prior middle | Prior upper | Outside above | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lower | 0 | 10 | 4 | 2 | 0 | 16 |
| Middle | 5 | 9 | 18 | 8 | 8 | 48 |
| Upper | 0 | 1 | 5 | 20 | 5 | 31 |

Same-third opens are 10 of 16 lower, 18 of 48 middle, and 20 of 31 upper. Those cells are reported because the cross-tab was preregistered. They are not a selected success.

`migration_frac` by prior dominant third:

| Prior dominant third | N | Mean | Median | p25 | p75 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lower | 16 | 0.000 | 0.085 | −0.132 | 0.173 |
| Middle | 48 | 0.192 | 0.096 | −0.435 | 0.697 |
| Upper | 31 | −0.055 | −0.028 | −0.281 | 0.290 |

`prior_vw_std_norm` and `prior_poc_concentration_10` are stored on every row. The preregistration does not define a comparison that uses them. No split on those fields was computed.

## G. Temporal stability

No chronological stability test is in the preregistration. No period boundary was chosen. Month counts in section C are sample accounting. They are not evidence that a relationship is stable, concentrated, absent, or changing.

## H. Direction / symmetry

The preregistered side split is prior dominant third, not a trade direction.

The migration medians are +0.085 (lower), +0.096 (middle), and −0.028 (upper). The means are about 0, +0.192, and −0.055. The three rows do not share one sign pattern, and the middle and upper quartiles both cross zero.

The open-third table is also asymmetric: lower priors have no outside opens in this sample, middle priors open in every label, and upper priors have one open in the prior lower third. Those differences stay as separate rows.

After the exact POC cross, 36 sessions have more later closes above and 31 have more below. That split is reported as two counts.

## I. Multiple-testing interpretation

No multiplicity correction was preregistered. The study has five primary summaries, a 3×5 cross-tab, and three migration slices. All of them are shown. No horizon, side, or statistic was chosen after seeing the numbers, because no significance test was run.

## J. Mechanism conclusion

On 95 adjacent analysis pairs, the next session’s open, POC-band contact, migration, and post-cross close counts were measured from prior-session volume location alone. The prior levels do not use the next session.

What that establishes is the measurement. The median open sits 0.030 prior-ranges from the prior POC, 70 of 95 sessions intersect the 10% POC band, and same-third opens are the largest cell in each dominant-third row. What it does not establish is that those patterns differ from a location null. The frozen text postponed that null. Calling the cross-tab or the touch rate a structural relationship would be a criterion invented after the tables.

No causal claim follows from these counts.

## K. Trading implication

No trading test is justified from this measurement.

A support claim would require a separate preregistration that freezes a location null for these same objects. This file does not add that null.
