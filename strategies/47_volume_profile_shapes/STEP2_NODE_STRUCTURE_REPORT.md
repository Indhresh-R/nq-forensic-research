# Step 2 — Accepted volume regions

This report does not test profitability, entries, exits, or forward returns. Region counts use the rules in `STEP2_PREREGISTRATION.md`. Those rules were not changed after the tables or the pictures were seen. `one_region`, `two_regions`, and `many_regions` are bins of a count. They are not P, b, D, or B labels, and they are not a trading setup.

## A. Dataset verification

The run stopped unless the stored Step 1 sample still matched the Step 1 report, and unless the recomputed peaks and concentration matched the stored geometry.

- Analysis sessions: 96.
- Stored `in_analysis_sample` matches `analysis_mask`.
- Primary labels: P-like 1, b-like 2, D-like 0, B-like 7, UNCLASSIFIED 86.
- Recomputed POC location, `vw_std_norm`, `poc_concentration_10`, major-peak count, and local-maximum count match the stored Step 1 columns on every analysis session.
- Region volumes sum to the session volume on every analysis session.
- Detail is in `results/step2_verification.json`.

The peak detector, the 50% major-peak rule, and the 0.20 / 0.30 gap cuts are the Step 1 constants. Nothing in this file refits them.

## B. What was measured

Four facts, kept separate.

Location is the share of volume in the lower, middle, and upper third of the session's own price range. The dominant third is the largest share. An exact tie would go to lower, then middle. The name is only a label for the cross-tab.

Concentration is `vw_std_norm` and `poc_concentration_10`. A larger standard deviation is a broader profile. A larger POC concentration is a tighter band around the POC. The share of volume in the largest region is not concentration: one region can cover a wide day.

Modality is the number of accepted regions. Only major peaks seed a region. Adjacent major peaks stay in one region unless the gap between them is material: separation at least 0.20 of the range and valley depth at least 0.30. A material gap is clean when no other detected local maximum sits strictly between those two major peaks.

Separation is reported on those adjacent gaps. The deepest gap is not a score for the session.

## C. Location

| Third | Sessions where it dominates | Share of sessions |
| --- | ---: | ---: |
| Middle | 48 | 50.0% |
| Upper | 32 | 33.3% |
| Lower | 16 | 16.7% |

Volume shares across the 96 sessions:

| Share | Min | p10 | p25 | Median | p75 | p90 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lower third | 0.026 | 0.090 | 0.141 | 0.237 | 0.333 | 0.480 | 0.755 |
| Middle third | 0.054 | 0.200 | 0.305 | 0.409 | 0.521 | 0.571 | 0.734 |
| Upper third | 0.064 | 0.103 | 0.171 | 0.294 | 0.462 | 0.603 | 0.921 |

The middle third is the most common place for the plurality of volume. Upper dominates twice as often as lower. That is the same direction as Step 1, where a P-like profile existed and a b-like profile was rarer, but it is not a letter classification. The median middle share is 0.409. No third is empty on the median day.

| Dominant third | One region | Two regions | Three regions |
| --- | ---: | ---: | ---: |
| lower | 10 | 5 | 1 |
| middle | 24 | 18 | 6 |
| upper | 15 | 17 | 0 |

## D. Concentration

| Measure | Min | p10 | p25 | Median | p75 | p90 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vw_std_norm` | 0.127 | 0.185 | 0.205 | 0.222 | 0.245 | 0.272 | 0.297 |
| `poc_concentration_10` | 0.121 | 0.263 | 0.312 | 0.374 | 0.426 | 0.503 | 0.715 |

The normalized standard deviation sits in a narrow band, from 0.127 to 0.297. Median POC concentration is 0.374. Days with one accepted region are a little tighter than days with more than one. Medians:

| Structure | Sessions | Median `vw_std_norm` | Median POC concentration | Median major peaks |
| --- | ---: | ---: | ---: | ---: |
| One region | 49 | 0.211 | 0.402 | 2.0 |
| Two regions | 40 | 0.226 | 0.359 | 3.0 |
| Three regions | 7 | 0.248 | 0.276 | 4.0 |

The shift is small next to the spread inside each bin. Concentration does not separate the region counts into different kinds of day.

## E. Modality

Major-peak counts and region counts are not the same object.

| Count | Major peaks | Accepted regions |
| --- | ---: | ---: |
| Min | 1 | 1 |
| Median | 3.0 | 1.0 |
| Max | 6 | 3 |

| Bin | Sessions | Share |
| --- | ---: | ---: |
| One region | 49 | 51.0% |
| Two regions | 40 | 41.7% |
| Three or more | 7 | 7.3% |

No session produced four or more accepted regions. The maximum is 3. The median session has one accepted region and three major peaks.

Of the 49 one-region sessions, 42 still contain two or more major peaks. Those peaks were not split apart because the gap between them failed the material test. One accepted region does not mean one peak. It means the major peaks that do exist are not far enough apart under the frozen rule.

The 7 sessions with three regions are the ones the merge could not collapse. They are listed in section H. None has more than three regions.

## F. Separation

There are 200 gaps between price-adjacent major peaks. 54 are material. 18 of those are clean. 36 of the 54 material gaps have at least one other local maximum between the two major peaks.

The depth cut does not bind. Every adjacent major-peak gap in this sample has valley depth at least 0.414. Of the 146 gaps that are not material, 146 fail because separation is below 0.20, and 0 fail because depth is below 0.30. The non-material gaps are the closer pairs. Their separation percentiles (p10, median, p90) are 0.105, 0.131, 0.172. Their depth percentiles at the same points are 0.539, 0.726, 0.921.

A close pair of major peaks still has a deep tick valley. The minimum tick between them is a poor description of an empty zone. On this sample, region membership is decided by whether the two major peaks are at least 20% of the range apart.

Material gaps that do pass that distance cut have separation percentiles (p10, median, p90) 0.206, 0.267, 0.386, and depth percentiles 0.824, 0.935, 0.998. Depth among the survivors is high because depth was already high before the cut.

## G. Two regions are not two equal masses

A second region is seeded by a major peak, which is a height rule: the peak tick is at least half of POC volume. The region's share of the day's volume can still be small.

Among the 40 two-region sessions:

| | Smaller region's volume share |
| --- | --- |
| Min, p25, median, p75, max | 0.068, 0.264, 0.343, 0.430, 0.498 |
| Smaller share below 0.25 | 10 |
| Smaller share at least 0.30 | 27 |

Median split is about 0.657 / 0.343. That is a real second mass on the median two-region day. It is not what the deepest-gap ranking shows. 10 of these 40 days put less than a quarter of the volume in the smaller region.

`clean_two` is narrower: two regions and no other detected peak in the gap. There are 14 such sessions. 4 of them still have a smaller share below 0.25, and 9 have a smaller share of at least 0.30. An empty gap is not the same thing as two substantial masses. 2026-08-04 is clean, with valley depth 1.000 and a smaller share of 0.068. 2026-07-28 is clean, with a smaller share of 0.079.

26 of the 40 two-region sessions have another local maximum inside the one material gap. The distance rule called the gap material. The gap is often not an empty shelf.

The depth-ranked gallery is `results/figures/step2/gallery_two_regions.png`. It is the first 10 of 40 by valley depth, not a sample of balanced splits.

| Rank | Session | Step 1 | Depth | Separation | Smaller share | Minors in gap | Clean |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | 2026-08-04 | UNCLASSIFIED | 1.000 | 0.331 | 0.068 | 0 | yes |
| 2 | 2026-03-30 | UNCLASSIFIED | 1.000 | 0.247 | 0.406 | 0 | yes |
| 3 | 2026-03-26 | B-like | 1.000 | 0.222 | 0.285 | 0 | yes |
| 4 | 2026-06-10 | UNCLASSIFIED | 1.000 | 0.203 | 0.307 | 0 | yes |
| 5 | 2026-07-28 | UNCLASSIFIED | 0.998 | 0.205 | 0.079 | 0 | yes |
| 6 | 2026-08-03 | B-like | 0.997 | 0.309 | 0.334 | 1 | no |
| 7 | 2026-04-01 | B-like | 0.994 | 0.583 | 0.437 | 1 | no |
| 8 | 2026-07-09 | UNCLASSIFIED | 0.990 | 0.298 | 0.281 | 1 | no |
| 9 | 2026-04-13 | UNCLASSIFIED | 0.984 | 0.297 | 0.492 | 1 | no |
| 10 | 2026-06-29 | B-like | 0.982 | 0.263 | 0.381 | 0 | yes |

2026-04-13, in that list, is the near-even case: smaller share 0.492. 2026-04-01, a Step 1 B-like session, has smaller share 0.437 and separation 0.583, with one minor peak in the gap. The same sheet contains both objects. Sorting by depth does not tell them apart.

## H. Three-region sessions

All 7 are Step 1 UNCLASSIFIED. None is `clean_two`. Largest region share runs from 0.435 to 0.554. The deepest gap on these days is not a description of the whole profile: each of them also has a second material gap.

| Session | Regions | Major peaks | Weakest depth | Strongest depth | Largest share |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-04-14 | 3 | 4 | 0.958 | 0.993 | 0.451 |
| 2026-04-21 | 3 | 3 | 0.933 | 0.995 | 0.521 |
| 2026-06-04 | 3 | 4 | 0.997 | 1.000 | 0.554 |
| 2026-06-08 | 3 | 5 | 0.969 | 0.976 | 0.473 |
| 2026-07-01 | 3 | 4 | 0.964 | 0.983 | 0.451 |
| 2026-07-23 | 3 | 4 | 0.854 | 0.863 | 0.435 |
| 2026-08-10 | 3 | 4 | 0.837 | 0.895 | 0.484 |

The contact sheet is `results/figures/step2/gallery_many_regions.png`.

## I. Step 1 labels

This is a consistency check. The region rule does not use the Step 1 label.

| Step 1 label | One region | Two regions | Three regions |
| --- | ---: | ---: | ---: |
| P-like | 1 | 0 | 0 |
| b-like | 2 | 0 | 0 |
| D-like | 0 | 0 | 0 |
| B-like | 0 | 7 | 0 |
| UNCLASSIFIED | 46 | 33 | 7 |

All 7 Step 1 B-like sessions fall in the two-region bin. 3 of them are clean. Their smaller-region shares run from 0.235 to 0.464. The Step 1 rule required exactly two major peaks, so these seven were already the days without a third major peak. They are not the days with the deepest gaps, and they are not a new result.

The one Step 1 P-like session, 2026-04-07, is one region with the upper third holding 0.921 of volume. The two b-like sessions, 2026-06-22 and 2026-08-17, are one region each, with lower-third shares 0.750 and 0.755. The geometry that survived Step 1B shows up here as location inside a single accepted region, not as a second node.

## J. Sensitivity

The looser and stricter settings change only the existing peak-detector prominence and minimum spacing. The major-peak fraction and the 0.20 / 0.30 gap cuts stay fixed. The baseline is not replaced.

| Setting | Prominence | Separation | One | Two | Three or more | Clean two | Same region count as baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.20 | 0.10 | 49 | 40 | 7 | 14 | 96 of 96 |
| looser | 0.12 | 0.06 | 61 | 30 | 5 | 0 | 83 of 96 |
| stricter | 0.30 | 0.15 | 38 | 41 | 17 | 36 | 75 of 96 |

Looser detection finds peaks closer together. A peak that lands inside a wide gap can break that gap into two shorter gaps, and both can then fail the 0.20 separation cut. The profile collapses toward one region, and the clean-two count goes to zero. Stricter detection keeps fewer peaks, leaves more gaps empty, and raises both the two-region count and the clean-two count. The region count moves with the detector. That is a reason to keep it as a description under the baseline detector, not as a type to trade.

## K. Random gallery

Seed 42 on the 96 dates sorted ascending is the same draw as Step 1B. The dates, in draw order, are: 2026-09-09 (one region, Step 1 UNCLASSIFIED), 2026-07-29 (one region, Step 1 UNCLASSIFIED), 2026-04-08 (two regions, Step 1 UNCLASSIFIED), 2026-07-13 (two regions, Step 1 UNCLASSIFIED), 2026-06-03 (two regions, Step 1 UNCLASSIFIED), 2026-09-07 (one region, Step 1 UNCLASSIFIED), 2026-07-23 (many regions, Step 1 UNCLASSIFIED), 2026-04-13 (two regions, Step 1 UNCLASSIFIED), 2026-04-29 (two regions, Step 1 UNCLASSIFIED), 2026-08-17 (one region, Step 1 b-like).

The sheet is `results/figures/step2/gallery_random.png`. It was not edited. Histograms of the region count and the dominant third are `results/figures/step2/n_regions.png` and `results/figures/step2/dominant_third.png`.

## Conclusion

The letter scores are not how this sample is organized. The median day is one accepted region, even though it usually contains several major peaks, because those peaks sit closer than 20% of the range. A second region is common but not typical: 40 of 96 sessions, and only 14 of those 40 have an empty detected gap. Several of the empty-gap cases are a tall peak in a thin tail, not a second mass. Three accepted regions happen 7 times. Four or more do not happen.

Valley depth between adjacent major peaks is high almost everywhere, including the pairs that stay inside one region. It does not identify a low-volume shelf. Distance does the splitting, and a minor peak inside that distance is common.

Location is usable on its own. Upper volume is more common than lower volume. The original P-like day and both b-like days are single regions sitting in the upper or lower third.

No cutoff here is a trading rule. The question of what happens when the next session trades through a prior low-volume gap is not tested in this step.
