# Preregistration — Step 2 accepted volume regions

Date frozen: 2026-09-20, before any Step 2 region count, gap table, gallery, or histogram was computed.

This file does not replace `PREREGISTRATION.md`, `code/frozen.py`, or `STEP1B_PREREGISTRATION.md`. Those cutoffs are reused as written. They are not refit.

Step 2 does not test profitability, entries, exits, forward returns, P&L, or the next session's reaction to a prior gap. A region count is not a forecast and not a P, b, D, or B label.

## Question

On the same 96 analysis sessions, how many substantial accepted price regions does each profile contain, and how strong is the low-volume gap between regions that are next to each other?

This is a description of the volume-by-price grid. It is not a shape letter and not a trade.

## Sample

Use `results/profile_shape_dataset.parquet` and `results/raw_price_volume.parquet`.

Recompute `analysis_mask` the same way Step 1B did. If it does not match stored `in_analysis_sample` on every row, stop. If the analysis sample is not 96 sessions, or the Step 1 primary labels are not P-like 1, b-like 2, D-like 0, B-like 7, UNCLASSIFIED 86, stop.

Session identity is `session_date`. The profile is executed volume on the unsmoothed 0.25-point grid for that session only. Do not rebuild the session clock.

## Peak seeds

Candidate peaks are the Step 1 baseline local maxima: prominence `0.20` of POC volume, separation `0.10` of the range in ticks, flat plateaus represented by their lower-price edge, POC kept. The function is the existing `detect_extrema`. Do not change it.

A peak is major when its raw volume is at least `0.50` of POC volume. That is the existing major-peak rule. Only major peaks can seed or split an accepted region. A local maximum below that height can sit inside a region or inside a gap. It does not become its own region.

If an analysis session has zero major peaks, stop. Do not impute a region.

## Adjacent gaps

Order the major peaks by price index. A gap is the pair of major peaks with no other major peak between them.

`range_ticks` is the number of ticks from the low to the high, `R = n - 1`.

```text
separation = (right_index - left_index) / R
```

If no tick lies strictly between the two peaks, the valley is undefined, the gap is not material, and it does not split the profile.

Otherwise the valley is the minimum raw volume strictly between them. Ties use the tick closest to the midpoint, then the lower tick. That is the existing valley rule.

```text
valley_depth = 1 - valley_volume / min(left_volume, right_volume)
```

`minor_peaks_between` is the number of prominence-qualified local maxima, major or not, whose index lies strictly between the two major peaks, excluding those two peaks. A non-major local maximum counts. The major endpoints do not.

A gap is material when the valley exists and both of these hold:

```text
separation >= 0.20
valley_depth >= 0.30
```

Those two numbers are the Step 1 B-like pair cuts. They are not a new search. A material gap is not a B label.

A material gap is clean when `minor_peaks_between` is 0. Clean means the split is not sitting on another detected peak. It is still not a trading signal.

## Accepted regions

Walk the major peaks from low price to high price. Start one region at the profile low. A material gap ends the current region and starts the next. A gap that is not material leaves both peaks in the same region.

The valley tick of a material gap belongs to the lower region. The next region starts on the following tick. The last region runs through the profile high. Region volumes therefore sum to the session volume. If they do not, stop.

A one-major-peak profile is one region covering the whole grid, including every minor peak.

The region mode is the lowest-price tick of maximum volume inside that span.

These are recorded for each region: price span, volume share, mode price, mode location (`mode_index / R`), and how many major peaks sit inside the span.

## What is not a score

Do not average location, concentration, modality, and separation into one number. Do not rank sessions by the deepest gap and call that rank a shape. The deepest gap answers only: a strong adjacent split exists. The region count answers how many accepted regions that split, and the ones beside it, actually produced.

## Location

Divide the price index `i = 0 .. R` with integer cuts:

```text
lower  if 3 * i < R
middle if 3 * i < 2 * R and the tick is not lower
upper  otherwise
```

Each share is the volume on those ticks divided by session volume. The dominant third is the first of lower, middle, upper whose raw volume equals the maximum. An exact tie goes to the earlier name in that list. The three shares are the result. The name is only a label for the cross-tab.

## Concentration

Report the stored Step 1 quantities, recomputed from the same grid as a check:

- `vw_std_norm`: volume-weighted population standard deviation of price, divided by the price range
- `poc_concentration_10`: volume within `max(10% of the range, one tick)` of the POC, divided by session volume
- `poc_location`: POC index divided by `R`

If any analysis session disagrees with the stored value by more than `1e-8`, or if the recomputed major-peak count or local-maximum count disagrees with the stored count, stop. Do not replace the stored Step 1 table.

`largest_region_share` is mass in the biggest region, not a tightness measure. A single region that covers a wide profile has share 1 and can still be diffuse. Tightness is `vw_std_norm` and `poc_concentration_10`.

## Diagnostics that do not change the regions

Assign every tick to the nearest candidate peak. An equal distance goes to the lower-price peak. A peak's basin share is the volume on its ticks divided by session volume.

Record, and do not feed back into the region count:

- height of the second-largest candidate peak divided by POC volume
- basin share of that peak
- largest basin share among candidate peaks that are not major, or 0 when every candidate peak is major

## Session summary

`n_regions` is the number of accepted regions. The structure name is only this bin:

```text
1    -> one_region
2    -> two_regions
3+   -> many_regions
```

`clean_two` is true only when `n_regions` is 2 and that single gap is clean. It is a count, not a setup.

For material gaps only, also store the weakest and the strongest:

- weakest: smallest valley depth, then smallest separation, then lower valley price
- strongest: largest valley depth, then largest separation, then lower valley price

The strongest gap is reported so it can be compared with the region count. It is not a B score.

## Sensitivity

After the baseline table is written, repeat the region count at the existing looser pair (prominence `0.12`, separation `0.06`) and the existing stricter pair (prominence `0.30`, separation `0.15`). The major-peak fraction and the `0.20` / `0.30` gap cuts stay put. Do not adopt the looser or stricter count as a new baseline after seeing it.

## Galleries

Draw the stored raw profile. The x-axis is that profile's own executed volume. The y-axis is its traded prices. POC is a solid line. The range midpoint is dashed. Major peaks are filled circles. Other candidate peaks are open circles. A material valley is a black x. A non-material valley is a gray x.

Two-region gallery: sessions with `n_regions = 2`, sorted by that gap's valley depth descending, then separation descending, then earlier `session_date`. If there are 10 or fewer, draw all of them. If there are more, draw the first 10. The table still contains every session.

Many-region gallery: sessions with `n_regions >= 3`, sorted by region count descending, then earlier date. Draw the first 10, or all if fewer.

Random gallery: sort the 96 dates ascending, then `numpy.random.default_rng(42).choice(96, size=10, replace=False)`. Draw those 10 in the order returned. Do not replace the draw.

Histograms of the region count use one bin per integer count.

## What this step will not do

- It will not change a cutoff after looking at counts or pictures.
- It will not emit a P, b, D, or B label.
- It will not test a return, a retracement, or an interaction between today's price and yesterday's gap.
- It will not choose a size, stop, or filter.
