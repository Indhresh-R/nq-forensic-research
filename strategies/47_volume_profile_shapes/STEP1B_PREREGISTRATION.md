# Preregistration — Step 1B continuous P / b / D / B shape similarity

Date frozen: 2026-09-20, before any continuous score, ranking, gallery, or histogram in this step was computed.

This file freezes the scoring geometry. It does not replace `PREREGISTRATION.md` or `code/frozen.py`. The Step 1 classifier is not edited, refit, or reinterpreted.

Step 1B does not test profitability, entries, exits, forward returns, P&L, ATR, VWAP, previous-day direction, order flow, or MBO. A high score is not a forecast. `top_shape` is not a trading label.

## Sample

Use `results/profile_shape_dataset.parquet` and the stored `in_analysis_sample` flag. Recompute that flag with the existing `analysis_mask` in `code/detect_shapes.py`. If the recomputed mask does not match the stored flag on every row, stop.

The primary sample is the sessions where that flag is true. Expected identity, taken from the finished Step 1 report and not from these scores:

- 96 sessions
- primary labels: P-like 1, b-like 2, D-like 0, B-like 7, UNCLASSIFIED 86

If the count or the label totals differ, stop. Do not drop or add sessions to force the count.

Session identity is `session_date`. Profiles come from `results/raw_price_volume.parquet` for those dates only. Do not rebuild the session clock. The profile remains executed trade volume on the 0.25-point grid, unsmoothed, full `[18:00, next 18:00)` session, maintenance break unfilled.

## Inputs

Scores use columns already stored by Step 1. They are not recomputed under a new definition for the primary table.

| Formula name | Stored column |
| --- | --- |
| POC location | `poc_location` |
| above-share | `volume_above_share` |
| below-share | `volume_below_share` |
| lower tail width | `lower_tail_width_10` |
| upper tail width | `upper_tail_width_10` |
| upper-body share | `upper_body_share` |
| lower-body share | `lower_body_share` |
| major-peak count | `n_major_peaks` |
| prominence-qualified local-maximum count | `n_local_maxima` |
| normalized separation | `normalized_separation` |
| valley depth | `valley_depth` |
| peak balance | `peak_balance` |
| peak volumes | `peak1_volume`, `peak2_volume` |
| POC volume | `poc_volume` |
| Step 1 label | `primary_class` |

"Two strongest prominence-qualified local maxima" means the Step 1 pair already stored: the two local maxima with the largest original volume, lower price on a tie, then ordered so peak 1 is the lower price. Strength is not re-ranked by prominence. Major-peak status (volume at least half of POC volume) is not required for the B score.

`clip(x, 0, 1)` means the closed interval: values below 0 become 0 and values above 1 become 1. Weights are equal. The mean is the arithmetic mean of the four components. No weight is changed after results are seen.

If any input to P1–P4, b1–b4, or D1–D3 is not finite on an analysis session, stop. Do not impute it.

## P score

```text
P1 = clip((poc_location - 0.50) / 0.30, 0, 1)
P2 = clip((volume_above_share - 0.50) / 0.20, 0, 1)
P3 = clip((lower_tail_width_10 - upper_tail_width_10 - 0.00) / 0.30, 0, 1)
P4 = clip((upper_body_share - 0.33) / 0.27, 0, 1)
P_score = mean(P1, P2, P3, P4)
```

`0.33` is the decimal written here, not `1/3`.

## b score

```text
b1 = clip((0.50 - poc_location) / 0.30, 0, 1)
b2 = clip((volume_below_share - 0.50) / 0.20, 0, 1)
b3 = clip((upper_tail_width_10 - lower_tail_width_10) / 0.30, 0, 1)
b4 = clip((lower_body_share - 0.33) / 0.27, 0, 1)
b_score = mean(b1, b2, b3, b4)
```

## D score

```text
distance_from_center = abs(poc_location - 0.50)
D1 = clip(1 - distance_from_center / 0.30, 0, 1)
D2 = clip(1 - abs(volume_above_share - 0.50) / 0.25, 0, 1)
tail_difference = abs(upper_tail_width_10 - lower_tail_width_10)
D3 = clip(1 - tail_difference / 0.30, 0, 1)
```

D4 uses `n_major_peaks` and is not a gate:

```text
1 major peak  -> 1.00
2 major peaks -> 0.50
3 major peaks -> 0.25
4 or more     -> 0.00
```

Zero major peaks is not part of the stated map. On these profiles the POC is always a local maximum and its volume equals POC volume, so the count is not expected to be zero. If it is zero, D4 = 0.00 and the session is reported. That assignment is an edge case, not a fitted penalty.

```text
D_score = mean(D1, D2, D3, D4)
```

## B score

Do not require exactly two major peaks.

If `n_local_maxima` is below 2, set `B_score = 0`, set B1 = B2 = B3 = B4 = 0, and record the reason `fewer than two prominence-qualified local maxima`.

Otherwise:

```text
B1 = clip((normalized_separation - 0.05) / 0.25, 0, 1)
B2 = clip((valley_depth - 0.20) / 0.70, 0, 1)
B3 = clip((peak_balance - 0.20) / 0.80, 0, 1)
peak1_strength = peak1_volume / poc_volume
peak2_strength = peak2_volume / poc_volume
weak_peak_strength = min(peak1_strength, peak2_strength)
B4 = clip((weak_peak_strength - 0.30) / 0.70, 0, 1)
B_score = mean(B1, B2, B3, B4)
```

If two local maxima exist but one of those inputs is not finite, that component is 0 and the reason names the missing input. The other finite components still enter the mean. This is the only missing-value rule. It is not a new shape threshold.

## Competition statistics

These are descriptive. They are not a classifier and they do not replace the Step 1 primary label.

```text
top_score = max(P_score, b_score, D_score, B_score)
second_score = the second value in that list after sorting descending
shape_margin = top_score - second_score
shape_ambiguity = 1 - shape_margin
```

`top_shape` is the name of a score equal to `top_score`. If two or more scores tie, `top_shape_tie` is true and the stored name uses this order only as a stable key: P, then b, then D, then B. The tie is not broken by economic meaning. The margin is still zero when the top two values are equal.

## Rankings and galleries

Sort each score descending. Ties keep the earlier `session_date`. Ranks use that order. `results/shape_rankings.csv` contains every analysis session under each score. The report quotes the first 10. Plots use the first 10 of each list, not a hand-picked subset.

Galleries draw the stored raw profile. The x-axis is executed volume with a limit from 0 to that profile's maximum, so each silhouette fills its panel. The y-axis is that profile's traded price range. Figure size, colors, and markers are shared. This display scale does not change the stored volume.

Markers: POC as a horizontal line; Step 1 major maxima as circles; the stored peak-1 / peak-2 pair as squares when a point is not already a major maximum; valley as an x when Step 1 stored a valley. A dashed line at the profile midpoint is a display aid only.

Random gallery: sort the 96 dates ascending, then `numpy.random.default_rng(42).choice(96, size=10, replace=False)`. Display the 10 in the order returned. Do not replace the draw.

Histograms use bins of width 0.05 from 0 to 1, the same edges for all four scores. Percentiles use linear interpolation. Counts "above" 0.50, 0.60, 0.70, and 0.80 are strict. Those cutoffs are descriptive and are not used to relabel sessions.

## Stability check

After the primary scores are written, recompute the same geometry with the existing `classify_volume` baseline on `raw_price_volume.parquet`. Score that recomputation with the formulas above. Do not replace the primary table if the two differ. Report the maximum absolute difference and the overlap of each top-10 date set. Do not add a new prominence, separation, tail, or body parameter.

## What this step will not do

- It will not change a formula after looking at ranks or pictures.
- It will not choose a cutoff for trading.
- It will not claim that a score predicts return.
