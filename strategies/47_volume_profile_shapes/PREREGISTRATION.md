# Preregistration — Step 1 volume-profile shape geometry

Date frozen: 2026-09-20, before any session in this study was classified.

This step does not test profitability, entries, exits, stops, targets, ATR, VWAP as a trading filter, previous-day direction, order flow, or forward returns.

The question is only whether daily NQ volume-by-price distributions contain objectively separable single-distribution, skewed, and double-distribution geometries corresponding to the visual labels D, P, b, and B.

P is not coded as bullish. b is not coded as bearish. D is not coded as neutral. Those words are not used as causes.

## Session

Same convention as `volume_profile/CONFIG.yaml` and `assign_cme_session`.

- Timezone: `America/New_York`. Offsets are not hardcoded.
- A New York timestamp at or after 18:00 belongs to that New York calendar date.
- An earlier New York timestamp belongs to the previous calendar date.
- The profile uses every executed trade assigned to that session. The window is `[18:00, next 18:00)`.
- The economic close is 17:00 New York. The 17:00–18:00 maintenance break stays inside the window.
- Source files: `data/trades_24h_6m/trades_24h_2026-03-25.dbn.zst` through `trades_24h_2026-09-16.dbn.zst` (126 files).
- Prices: Databento fixed-point values with absolute value above 1,000,000 are divided by `1e9`. Tick size is 0.25. Tick = `round(price / 0.25)`.
- Volume is the sum of executed trade size at each tick. Bars, quotes, and the book are not used.
- POC tie-break: lowest price. This matches the existing volume-profile study and is not a shape threshold.

A session is complete when its first trade is within 30 minutes after 18:00 New York and its last trade is within 30 minutes before 17:00 New York the next day. Incomplete sessions stay in the dataset.

A roll transition is an `instrument_id` change from the previous session, more than one `instrument_id` inside the session, or an absolute gap of at least 150 points between the previous session's last trade and this session's first trade. The first session is a roll only if it contains two instrument ids. Roll sessions stay in the dataset.

## Analysis sample

Every parsed session is saved. Nothing is deleted because it is hard to label.

The primary counts, monthly table, sensitivity agreement, and example plots use only sessions that are complete, not a roll transition, have positive volume, and have a positive profile range. This exclusion is declared here, before classification. Roll gaps and partial edge sessions are data-quality problems, not shape evidence.

Symbol mismatches, negative sizes, and ranges above 500,000 ticks are recorded and kept out of the analysis sample. They are not dropped from the files.

## Profile

For each session, sum executed size on the integer tick grid from the lowest traded tick to the highest traded tick. Untraded ticks inside that range have volume 0. The raw series is not smoothed.

Saved columns per tick: price, volume, share of session volume, cumulative volume from the low.

## Statistics

Let the inclusive tick grid be `k = 0 .. R`, price `p_k`, volume `v_k`, total `V = sum v_k`.

- Profile high / low: max and min traded prices.
- Profile range: `(high_tick - low_tick) * 0.25`. `R = high_tick - low_tick`.
- POC: minimum `k` maximizing `v_k`.
- POC location: `k_poc / R` when `R > 0`.
- Volume-weighted mean: `sum(p_k v_k) / V`. This is the first moment of the volume-by-price distribution. It is not an intraday VWAP and it is not a classification input.
- Volume-weighted standard deviation: population `sqrt(sum(v_k (p_k - mean)^2) / V)`, also divided by profile range for a scale-free figure. Not a classification input.
- Volume concentration around POC: volume with `|p - poc| <= max(0.10 * range, 0.25)` , divided by `V`.
- Midpoint: `(high + low) / 2`.
- Above-share: volume strictly above the midpoint, divided by volume strictly above plus strictly below. Volume exactly at the midpoint is reported and excluded from the share.
- Lower 10% tail width: smallest distance from the low, as a fraction of range, that accumulates at least 10% of `V`. Upper tail is the same from the high. A wide tail means the outer volume is thin.
- Upper-body share: volume at prices `>= high - 0.30 * range`, divided by `V`. Lower-body share uses `<= low + 0.30 * range`.

## Local extrema

On the raw dense grid, flat local-maximum plateaus keep their volume on the lower-price edge. Other ticks in that plateau are reduced by 1 contract only inside the peak finder, so the lower edge is the representative. Valley volumes use the original grid, not the collapsed one.

Baseline (`scipy.signal.find_peaks`):

- prominence at least `0.20 * POC volume`
- distance at least `max(1, round(0.10 * R))` ticks

A local maximum is major when its original volume is at least `0.50 * POC volume`. The POC tick is always eligible. If the distance filter drops it, it is put back and lower peaks inside the distance are removed, higher volume first, then lower price.

Local minima use the same prominence and distance on the negated collapsed grid.

The two candidate peaks are the two local maxima with the largest volume. Ties keep the lower price. They are then ordered so peak 1 is the lower price.

If at least one tick lies strictly between them:

- valley = the minimum original volume on that open interval
- valley price ties: tick closest to the midpoint of the two peaks, then the lower tick
- `valley_ratio = V_valley / V_min_peak`
- `valley_depth = 1 - valley_ratio`
- `normalized_separation = |peak2 - peak1| / range`

## Flags

Flags may overlap. Thresholds are structural round numbers, not fitted.

**B-like / bimodal**, all of:

- exactly two major peaks
- normalized separation of those peaks at least 0.20
- valley depth at least 0.30

Three or more major peaks set `flag_multimodal` and do not set B-like.

**P-like**, all of:

- POC location at least 0.70
- above-share at least 0.62
- lower tail width minus upper tail width at least 0.20
- upper-body share at least 0.55

**b-like**, all of:

- POC location at most 0.30
- below-share at least 0.62
- upper tail width minus lower tail width at least 0.20
- lower-body share at least 0.55

**D-like**, all of:

- POC location in `[0.40, 0.60]`
- absolute above-share minus 0.50 at most 0.10
- absolute upper-tail minus lower-tail at most 0.12
- exactly one major peak
- POC-band concentration at least 0.45

Degenerate sessions (`R = 0`, non-positive volume, or corrupt range) receive no shape flags.

## Primary label

- Exactly one of P-like, b-like, D-like, B-like: that label.
- None of them: `UNCLASSIFIED`.
- Two or more of them: `UNCLASSIFIED` with `conflict = true`.

Multimodal is not a fifth shape class. A multimodal session with no shape flag stays unclassified.

No rule here is allowed to change after the classification tables are seen. Synthetic self-checks may fix implementation bugs. They may not move these cutoffs.

## Sensitivity

Only the extrema parameters move. P/b/D numeric cutoffs stay fixed.

| Setting | Prominence fraction | Separation fraction |
| --- | --- | --- |
| Looser | 0.12 | 0.06 |
| Baseline | 0.20 | 0.10 |
| Stricter | 0.30 | 0.15 |

Agreement is the fraction of analysis-sample sessions whose primary label equals the baseline label. Agreement below 0.70 on either comparison means the split is unstable.

## Verdict rule

Let the analysis sample have size `n`. Let `n_P, n_b, n_D, n_B` be primary-label counts. Let `u` be the unclassified share of `n`.

**CLEAR STRUCTURE** only if all of:

- each of the four named counts is at least 8
- agreement with the looser setting is at least 0.85
- agreement with the stricter setting is at least 0.85
- `u < 0.60`

**WEAK STRUCTURE** if the clear rule fails and all of:

- at least two named classes have count at least 5
- both agreements are at least 0.70

**NO CLEAR STRUCTURE** otherwise, including `n = 0`.

Plots do not enter this rule. A plot cannot move a label or a cutoff.

## Plots

Drawn only from the analysis sample, after labels exist.

- Strongest P, b, D, and B by the ranking scores below, among sessions already carrying that primary label. Ties break toward the earlier session date.
- One unclassified session with the smallest total rule shortfall (closest to a cutoff, not a hand-picked chart). Ties break toward the earlier session date.
- Three sessions per primary class drawn with NumPy seed 42, or fewer if the class is smaller.

Ranking scores are not classifiers:

- P: POC location + upper-body share + (lower tail − upper tail)
- b: (1 − POC location) + lower-body share + (upper tail − lower tail)
- D: `(1 - 2|POC location - 0.5|) + (1 - 2|above-share - 0.5|) + POC concentration + (1 - |tail difference|)`
- B: valley depth + peak balance + normalized separation

If a roll session has primary label B-like, the strongest such roll is plotted once, titled as a roll artifact, and is not the B example.

## What this file forbids after the run

Changing a cutoff, a completeness rule, a roll rule, or the verdict inequalities because of how many sessions landed in a class. Adding a trading filter. Computing forward returns.
