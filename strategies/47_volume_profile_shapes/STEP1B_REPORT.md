# Step 1B — Continuous P / b / D / B shape similarity

This report does not test profitability, entries, exits, or forward returns. Scores were computed from the formulas in `STEP1B_PREREGISTRATION.md` after that file was written. The formulas were not changed after the rankings or the pictures were seen. `top_shape` is not a trading label.

## A. Dataset verification

The scoring run stopped unless the stored Step 1 sample matched the Step 1 report.

- Analysis sessions: 96.
- Stored `in_analysis_sample` matches `analysis_mask` on every row of `results/profile_shape_dataset.parquet`.
- Primary labels: P-like 1, b-like 2, D-like 0, B-like 7, UNCLASSIFIED 86.
- Every analysis `session_date` is in `results/raw_price_volume.parquet`, and the raw volume sum matches the session total.
- Session dates are listed in `results/step1b_verification.json`.
- Inputs are the stored profile geometry for that session only: executed volume on the 0.25-point grid. No later session, no return, no ATR, no VWAP, no order flow, and no MBO enters a score.

Rebuilding the same geometry with the existing Step 1 `classify_volume` on the raw profiles changes no scoring input. See section H.

## B. Scoring definitions

`clip(x, 0, 1)` clamps to the closed unit interval. Each final score is the equal-weight arithmetic mean of its four components. `0.33` is that decimal, not one third.

P, upper concentration with a longer lower tail:

```text
P1 = clip((poc_location - 0.50) / 0.30, 0, 1)
P2 = clip((volume_above_share - 0.50) / 0.20, 0, 1)
P3 = clip((lower_tail_width_10 - upper_tail_width_10) / 0.30, 0, 1)
P4 = clip((upper_body_share - 0.33) / 0.27, 0, 1)
P_score = mean(P1, P2, P3, P4)
```

b, the mirror:

```text
b1 = clip((0.50 - poc_location) / 0.30, 0, 1)
b2 = clip((volume_below_share - 0.50) / 0.20, 0, 1)
b3 = clip((upper_tail_width_10 - lower_tail_width_10) / 0.30, 0, 1)
b4 = clip((lower_body_share - 0.33) / 0.27, 0, 1)
b_score = mean(b1, b2, b3, b4)
```

D, centered and balanced, with a soft peak-count penalty:

```text
D1 = clip(1 - abs(poc_location - 0.50) / 0.30, 0, 1)
D2 = clip(1 - abs(volume_above_share - 0.50) / 0.25, 0, 1)
D3 = clip(1 - abs(upper_tail_width_10 - lower_tail_width_10) / 0.30, 0, 1)
D4 = 1.00 if 1 major peak, 0.50 if 2, 0.25 if 3, 0.00 if 0 or 4+
D_score = mean(D1, D2, D3, D4)
```

No analysis session had zero major peaks.

B, the strongest stored pair of prominence-qualified local maxima, not the Step 1 "exactly two major peaks" rule:

```text
B1 = clip((normalized_separation - 0.05) / 0.25, 0, 1)
B2 = clip((valley_depth - 0.20) / 0.70, 0, 1)
B3 = clip((peak_balance - 0.20) / 0.80, 0, 1)
B4 = clip((min(peak1_volume, peak2_volume) / poc_volume - 0.30) / 0.70, 0, 1)
B_score = mean(B1, B2, B3, B4)
```

If fewer than two prominence-qualified local maxima exist, `B_score` is 0 and the reason is stored. That case did not occur. All 96 sessions have at least two, so every B score is the four-component mean. Extra major peaks are not penalized. That is the frozen rule, and it matters for the pictures in section F.

`top_shape` names the largest of the four scores. There were no ties. `shape_margin` is the gap to the second score. `shape_ambiguity = 1 - shape_margin`. The median margin is 0.167, so the median ambiguity is 0.833. The higher B level described below is why B is the numeric maximum for 60 of 96 sessions. That count is not a classification.

## C. Score distributions

Percentiles are linear. "Above" is strict. These cutoffs are descriptive only.

| Shape | Min | p10 | p25 | Median | p75 | p90 | Max | >0.50 | >0.60 | >0.70 | >0.80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P | 0.000 | 0.000 | 0.007 | 0.166 | 0.618 | 0.826 | 1.000 | 32 | 26 | 17 | 13 |
| b | 0.000 | 0.000 | 0.000 | 0.023 | 0.296 | 0.610 | 1.000 | 11 | 11 | 6 | 3 |
| D | 0.062 | 0.199 | 0.287 | 0.429 | 0.542 | 0.642 | 0.769 | 31 | 16 | 6 | 0 |
| B | 0.322 | 0.503 | 0.607 | 0.705 | 0.801 | 0.892 | 0.999 | 86 | 72 | 49 | 25 |

P and b are piled near zero, with a thin upper tail. D is compressed: nothing reaches 0.80, and the best score is 0.769. B sits high across the sample. Its median, 0.705, is close to the Step 1 B-like median below. A high B score is common, not a rare textbook event.

Histograms with bins of width 0.05 are in `results/figures/score_histograms.png`. The same numbers are in `results/score_distributions.csv`.

| Shape | Top score | Median of top 10 | Median of all 96 |
| --- | ---: | ---: | ---: |
| P | 1.000 | 0.893 | 0.166 |
| b | 1.000 | 0.729 | 0.023 |
| D | 0.769 | 0.708 | 0.429 |
| B | 0.999 | 0.939 | 0.705 |

P and b separate their top 10 from the middle of the sample. D's top 10 is only moderately above the middle. B's top 10 is high, but so is the middle of the sample.

## D. Rankings

Full order, with component scores and the stored geometry, is `results/shape_rankings.csv`. Ties would keep the earlier session date. The first 10 rows of each shape are below. Component columns are that shape's four scores, in the order frozen above.

### P

| Rank | Session | Score | Step 1 | P1 | P2 | P3 | P4 | POC loc | Major peaks |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-04-07 | 1.000 | P-like | 1.000 | 1.000 | 1.000 | 1.000 | 0.804 | 1 |
| 2 | 2026-07-20 | 1.000 | UNCLASSIFIED | 1.000 | 1.000 | 1.000 | 1.000 | 0.960 | 2 |
| 3 | 2026-09-01 | 0.955 | UNCLASSIFIED | 1.000 | 1.000 | 1.000 | 0.820 | 0.815 | 2 |
| 4 | 2026-05-07 | 0.925 | UNCLASSIFIED | 1.000 | 1.000 | 0.858 | 0.841 | 0.880 | 2 |
| 5 | 2026-09-10 | 0.900 | UNCLASSIFIED | 1.000 | 1.000 | 0.602 | 1.000 | 0.815 | 2 |
| 6 | 2026-04-16 | 0.885 | UNCLASSIFIED | 1.000 | 1.000 | 0.540 | 1.000 | 0.877 | 2 |
| 7 | 2026-05-04 | 0.869 | UNCLASSIFIED | 0.910 | 1.000 | 0.615 | 0.951 | 0.773 | 1 |
| 8 | 2026-07-13 | 0.854 | UNCLASSIFIED | 0.929 | 1.000 | 0.488 | 0.999 | 0.779 | 3 |
| 9 | 2026-07-08 | 0.835 | B-like | 1.000 | 1.000 | 0.574 | 0.766 | 0.844 | 2 |
| 10 | 2026-08-12 | 0.830 | UNCLASSIFIED | 1.000 | 1.000 | 0.322 | 1.000 | 0.873 | 2 |

Eight of these ten were UNCLASSIFIED. Two have a single major peak. Seven have two. One has three. P3, the lower-tail component, is the one that falls off first.

### b

| Rank | Session | Score | Step 1 | b1 | b2 | b3 | b4 | POC loc | Major peaks |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-06-22 | 1.000 | b-like | 1.000 | 1.000 | 1.000 | 1.000 | 0.136 | 3 |
| 2 | 2026-08-17 | 1.000 | b-like | 1.000 | 1.000 | 1.000 | 1.000 | 0.133 | 2 |
| 3 | 2026-04-27 | 0.829 | UNCLASSIFIED | 0.602 | 1.000 | 0.927 | 0.787 | 0.319 | 2 |
| 4 | 2026-08-31 | 0.752 | UNCLASSIFIED | 0.946 | 1.000 | 0.148 | 0.915 | 0.216 | 2 |
| 5 | 2026-05-14 | 0.737 | UNCLASSIFIED | 0.579 | 1.000 | 0.997 | 0.372 | 0.326 | 2 |
| 6 | 2026-05-26 | 0.721 | UNCLASSIFIED | 0.520 | 1.000 | 0.829 | 0.535 | 0.344 | 1 |
| 7 | 2026-09-09 | 0.698 | UNCLASSIFIED | 0.901 | 1.000 | 0.281 | 0.609 | 0.230 | 3 |
| 8 | 2026-08-19 | 0.665 | UNCLASSIFIED | 1.000 | 1.000 | 0.113 | 0.547 | 0.200 | 2 |
| 9 | 2026-07-06 | 0.618 | UNCLASSIFIED | 0.226 | 1.000 | 0.872 | 0.373 | 0.432 | 3 |
| 10 | 2026-09-03 | 0.614 | UNCLASSIFIED | 0.934 | 1.000 | 0.374 | 0.235 | 0.220 | 2 |

Both Step 1 b-like sessions are at the top, with score 1. Only one other session exceeds 0.80. From rank 4 downward, at least one of the tail or lower-body components is weak even when the POC is low and most sided volume is below the midpoint.

### D

| Rank | Session | Score | Step 1 | D1 | D2 | D3 | D4 | POC loc | Major peaks |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-04-06 | 0.769 | UNCLASSIFIED | 0.977 | 0.857 | 0.993 | 0.250 | 0.507 | 3 |
| 2 | 2026-07-16 | 0.763 | UNCLASSIFIED | 0.853 | 0.833 | 0.866 | 0.500 | 0.544 | 2 |
| 3 | 2026-05-28 | 0.751 | UNCLASSIFIED | 0.752 | 0.779 | 0.974 | 0.500 | 0.574 | 2 |
| 4 | 2026-08-18 | 0.714 | UNCLASSIFIED | 0.856 | 0.630 | 0.871 | 0.500 | 0.457 | 2 |
| 5 | 2026-06-15 | 0.711 | UNCLASSIFIED | 0.000 | 0.934 | 0.912 | 1.000 | 0.803 | 1 |
| 6 | 2026-07-14 | 0.705 | UNCLASSIFIED | 0.851 | 0.515 | 0.954 | 0.500 | 0.455 | 2 |
| 7 | 2026-05-18 | 0.690 | UNCLASSIFIED | 0.964 | 0.991 | 0.807 | 0.000 | 0.489 | 6 |
| 8 | 2026-08-20 | 0.655 | UNCLASSIFIED | 0.786 | 0.950 | 0.885 | 0.000 | 0.564 | 4 |
| 9 | 2026-04-28 | 0.651 | UNCLASSIFIED | 0.729 | 0.662 | 0.714 | 0.500 | 0.581 | 2 |
| 10 | 2026-04-09 | 0.646 | UNCLASSIFIED | 0.883 | 0.739 | 0.962 | 0.000 | 0.535 | 5 |

Every one of these was UNCLASSIFIED. Step 1 found no D-like session, and this ranking does not uncover a unimodal bell at the top. Rank 5 has one major peak, which sets D4 to 1, but D1 is 0 because the POC location is 0.803. The mean still places it fifth. Rank 7 has six major peaks and D4 of 0, and still sits in the top 10 because the other three components are high.

### B

| Rank | Session | Score | Step 1 | B1 | B2 | B3 | B4 | Separation | Valley depth | Major peaks |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-04-29 | 0.999 | UNCLASSIFIED | 1.000 | 1.000 | 0.999 | 0.999 | 0.403 | 0.960 | 5 |
| 2 | 2026-05-12 | 0.980 | UNCLASSIFIED | 1.000 | 1.000 | 0.963 | 0.958 | 0.451 | 0.948 | 4 |
| 3 | 2026-06-03 | 0.971 | UNCLASSIFIED | 1.000 | 1.000 | 0.946 | 0.938 | 0.398 | 0.946 | 6 |
| 4 | 2026-07-23 | 0.940 | UNCLASSIFIED | 1.000 | 0.966 | 0.904 | 0.890 | 0.401 | 0.876 | 4 |
| 5 | 2026-09-15 | 0.940 | UNCLASSIFIED | 1.000 | 1.000 | 0.888 | 0.872 | 0.496 | 0.971 | 4 |
| 6 | 2026-07-09 | 0.939 | UNCLASSIFIED | 1.000 | 1.000 | 0.886 | 0.870 | 0.467 | 0.993 | 4 |
| 7 | 2026-05-11 | 0.901 | UNCLASSIFIED | 1.000 | 1.000 | 0.816 | 0.790 | 0.399 | 0.923 | 3 |
| 8 | 2026-05-21 | 0.898 | UNCLASSIFIED | 0.950 | 0.813 | 0.921 | 0.909 | 0.288 | 0.769 | 4 |
| 9 | 2026-08-10 | 0.894 | UNCLASSIFIED | 1.000 | 0.943 | 0.829 | 0.804 | 0.345 | 0.860 | 4 |
| 10 | 2026-05-05 | 0.893 | UNCLASSIFIED | 0.761 | 0.957 | 0.932 | 0.922 | 0.240 | 0.870 | 5 |

None of the top 10 has exactly two major peaks. The counts run from 3 to 6. All ten were UNCLASSIFIED. The seven Step 1 B-like sessions are not in this list. Their B ranks are 26, 27, 43, 47, 54, 58, and 59.

## E. Step 1 comparison

This is a consistency check, not a validation test. Medians:

| Step 1 label | N | Median P | Median b | Median D | Median B |
| --- | ---: | ---: | ---: | ---: | ---: |
| P-like | 1 | 1.000 | 0.000 | 0.250 | 0.336 |
| b-like | 2 | 0.000 | 1.000 | 0.094 | 0.629 |
| D-like | 0 |  |  |  |  |
| B-like | 7 | 0.639 | 0.000 | 0.390 | 0.706 |
| UNCLASSIFIED | 86 | 0.161 | 0.027 | 0.433 | 0.706 |

The single Step 1 P-like session, 2026-04-07, has P score 1.000 and is rank 1 on P. The two Step 1 b-like sessions, 2026-06-22 and 2026-08-17, have b score 1.000 and are ranks 1 and 2 on b. There is no Step 1 D-like session to place.

The Step 1 B-like sessions do not lead the B ranking:

| Session | B score | B rank | P score | b score | D score |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-08-03 | 0.799 | 26 | 0.749 | 0.000 | 0.279 |
| 2026-06-29 | 0.786 | 27 | 0.639 | 0.000 | 0.390 |
| 2026-03-26 | 0.723 | 43 | 0.000 | 0.410 | 0.504 |
| 2026-07-21 | 0.706 | 47 | 0.791 | 0.000 | 0.246 |
| 2026-07-22 | 0.684 | 54 | 0.000 | 0.607 | 0.406 |
| 2026-04-01 | 0.670 | 58 | 0.606 | 0.000 | 0.490 |
| 2026-07-08 | 0.662 | 59 | 0.835 | 0.000 | 0.232 |

Their B scores sit around the sample median of 0.705. Several of them score as high or higher on P than on B. 2026-07-08 is B-like in Step 1 and is also rank 9 on the continuous P score. The frozen B score is doing something different from the Step 1 B rule: it rewards a strong separated pair and ignores additional peaks, so the lumpiest profiles outrank the sessions Step 1 called B-like.

The formula was not changed after this table.

## F. Visual gallery

Each panel is the stored raw profile. The horizontal axis is executed volume, limited to that profile's own maximum so the silhouette fills the panel. The vertical axis is that profile's traded prices. POC is a solid line, the range midpoint is dashed, major peaks are filled circles, a stored peak that is not major is an open square, and a stored valley is an x. The same style is used on every panel. Nothing was hand-picked. Rank order chooses the ten.

Windows treats `top_b` and `top_B` as one folder, and `gallery_b.png` as the same file as `gallery_B.png`. The two rankings are therefore saved under names that can exist at the same time:

| Score | Contact sheet | Single profiles |
| --- | --- | --- |
| P | `results/figures/gallery_P.png` | `results/figures/top_P/` |
| b | `results/figures/gallery_b_lower.png` | `results/figures/top_b_lower/` |
| D | `results/figures/gallery_D.png` | `results/figures/top_D/` |
| B | `results/figures/gallery_B_double.png` | `results/figures/top_B_double/` |

The random draw is `numpy.random.default_rng(42)` on the 96 dates sorted ascending, 10 sessions without replacement, shown in draw order in `results/figures/gallery_random.png`. The dates are 2026-09-09, 2026-07-29, 2026-04-08, 2026-07-13, 2026-06-03, 2026-09-07, 2026-07-23, 2026-04-13, 2026-04-29, and 2026-08-17. Nine are UNCLASSIFIED. 2026-08-17 is the Step 1 b-like session with b score 1. The same draw also contains the top B session, 2026-04-29, and P rank 8, 2026-07-13. That overlap is what seed 42 produced. It was not edited.

What the panels show, next to that random set:

- Top P is more upper-heavy than the random set as a group. 2026-04-07, the only Step 1 P-like session, is a single major peak high in the range with a long thin region underneath. 2026-07-20 was UNCLASSIFIED and scores 1.000 as well: the volume sits in an upper cluster (POC location 0.960, above-share 0.907, lower tail 0.531, upper tail 0.042) with a second major peak inside that cluster and a thin lower extension. Several other top-P days also have two major peaks. They resemble an upper node more than they resemble a smooth single-node letter, but they are visibly not centered and not lower-heavy.
- Top b matches that pattern in reverse at the very top. 2026-06-22 and 2026-08-17 put the volume low, with a thinner extension above. 2026-04-27, UNCLASSIFIED, score 0.829, still has the mass below the midpoint and a thinner upper region. By 2026-09-03, rank 10, score 0.614, the POC is still low (0.220) but b3 is 0.374 and b4 is 0.235: two substantial nodes low in the range, not a thin upper stem. The b ranking is visually sharp only at the top.
- Top D does not look like a single bell. 2026-04-06 is the best D score, 0.769. The POC is near the middle (0.507) and the tails match, and there are three major peaks with a valley between the middle and upper node. 2026-07-16, score 0.763, is a centered pair of nodes. 2026-06-15, score 0.711, is not centered: POC location 0.803, D1 is 0, and the volume is in the upper half. It ranks fifth because one major peak, side balance, and tail symmetry are averaged with that zero.
- Top B does not look like a clean two-node profile, and it does not look sharply different from the random gallery. 2026-04-29, score 0.999, has five major peaks, a high POC (0.918), and a deep gap under the upper node, with more nodes below. 2026-07-09, score 0.939, has four major peaks and POC location 0.931. The random gallery includes this same 2026-04-29 profile, plus 2026-06-03 (six major peaks, B score 0.971) and other three-to-five-peak days. Both galleries are lumpy. The B score's top end is the lumpier end, because additional peaks are not penalized.

## G. Interpretation

These answers use the pictures and the frozen scores. They are not a claim that any score predicts price.

1. The continuous P score does put upper-concentrated profiles at the top, including UNCLASSIFIED sessions that look like the one profile Step 1 accepted. The resemblance is real and stronger than in the random gallery. It is often an upper cluster with a second peak and a thin lower extension, not a textbook single-node P.

2. The continuous b score does the same in the other direction for its first few sessions, including both profiles Step 1 accepted and at least one UNCLASSIFIED neighbor (2026-04-27). Further down the top 10 the lower-tail or lower-body component gives way, and the picture is only partly a b. Only three sessions score above 0.80.

3. The continuous D score does not produce a gallery of textbook D profiles. The best scores belong to centered but multi-peaked profiles, or, in the case of 2026-06-15, to a profile that is not centered. No session scores above 0.80. Step 1's count of zero D-like sessions is not explained by a hidden set of clean bells.

4. The continuous B score does not produce a gallery of textbook double distributions. The highest scores have three to six major peaks. The seven sessions Step 1 called B-like rank from 26 to 59. Random sessions often score high on B as well. The score detects a strong pair inside a lumpy profile. That is common in this sample.

5. The 86 UNCLASSIFIED sessions are not primarily a large set of recognizable P, b, D, and B profiles rejected only by hard cutoffs. P, and a smaller set of b profiles, do show that the Step 1 clauses were strict: a perfect P score and a near-b score were left UNCLASSIFIED. That is a threshold effect, and it covers a minority. Thirteen P scores and three b scores exceed 0.80.

6. The rest of the sample looks irregular. The median major-peak count is 3, and 57 of 96 sessions have three or more. Median P is 0.166 and median b is 0.023. Median D is 0.429 with a ceiling of 0.769. Median B is 0.705 because a separated pair inside a multi-peak profile is ordinary here. The typical margin between the leading score and the runner-up is 0.167. The random gallery, even though it happened to include a few high-scoring days, is mostly that lumpy profile.

The Step 1 classifier was strict for P and, more narrowly, for b. It was not the main reason D and B fail to show up as clean textbook shapes. Those two letters do not describe the usual NQ profile in this sample, and the frozen continuous scores do not manufacture them.

## H. Stability

The primary table uses the stored Step 1 columns. After it was written, the same sessions were scored again from geometry recomputed by the existing baseline `classify_volume` on `raw_price_volume.parquet`. No prominence, separation, tail, or body parameter was added.

Maximum absolute difference on every compared input, and on all four scores, is 0. Each top-10 date set overlaps on 10 of 10 sessions. The ranking does not move under that recompute. Detail is in `results/stability_diagnostic.csv`.

## Conclusion

### PARTIAL THRESHOLD ARTIFACT

Some shapes become visually recognizable under continuous scoring, but other shapes remain poorly represented.

P, and the top of the b ranking, show upper or lower concentration that Step 1's full clause list mostly refused. D and B do not. The highest D profiles are balanced and still multi-peaked, or not centered. The highest B profiles are multi-peaked, and high B scores are typical rather than distinctive. The unclassified majority is not a pile of missed textbook letters. It is mostly irregular volume-by-price.

No cutoff from this step is a trading rule. No score here is a forecast.
