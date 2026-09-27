# Mechanism report

These are conditional descriptions. They are not a trading rule.
Parameters were fixed in CONFIG.yaml before the results were read.
Touch tolerance is 1 NQ tick. Horizons are [1, 5, 15, 30, 60] minutes.
Crossing continuation is 4 ticks, observed for 60 minutes.
Return means the later trade price minus the touched level, in index points. A positive number means the later trade printed above the level.
MFE and MAE are path statistics over the same window, measured in the direction of the recorded approach. They are not a result.
Bootstrap intervals are percentile intervals of the mean, seed 42, 1000 draws. With about six months of sessions they describe sampling variation. They are not a license to rank horizons.

## POC first touch

Question: after the next complete CME session first trades within one tick of the previous POC, where is price at the fixed horizons?

Definition: first trade in `(ts_event, sequence)` order with absolute distance of at most one tick. Approach uses the last earlier trade outside that band. Ambiguous opens are excluded from these rows. Roll-transition sessions and incomplete sessions are excluded.

Sample, from_below: N=22. Median 5-minute price-minus-POC=0.125. Mean=7.830 (interval -3.626 to 22.489). Fraction above the level=0.500. Median 5-minute MFE=11.250, MAE=13.250.
Stability, from_below: early median=9.750 (N=7); late median=-1.000 (N=15).
Sample, from_above: N=28. Median 5-minute price-minus-POC=-10.250. Mean=-14.027 (interval -31.603 to 0.393). Fraction above the level=0.357. Median 5-minute MFE=20.375, MAE=9.375.
Stability, from_above: early median=-11.750 (N=13); late median=-10.000 (N=15).

The same fixed calculation is in `results/poc_first_touch.csv` for 1, 15, 30, and 60 minutes. Those horizons were not ranked.

## VAH and VAL first touch

Question: after the first trade within one tick of the previous value-area boundary, does the later trade sit beyond that boundary or back inside it?

Definition: same touch and approach rules as POC. For an approach from below, a later trade above VAH has crossed upward. For an approach from above, a later trade below VAL has crossed downward. The sign reported here is still price minus the level, so the two boundaries are not flipped into a common score.

VAH from_below: N=39, median 5-minute price-minus-level=-0.250, mean=3.917, fraction above the level=0.436.
VAH from_above: N=7, median 5-minute price-minus-level=-1.250, mean=-34.357, fraction above the level=0.286.
VAH cross check: share of directional touches that print 4 ticks through the boundary before the session window ends=1.000. This share is not a selected threshold.
VAL from_below: N=11, median 5-minute price-minus-level=7.000, mean=5.227, fraction above the level=0.727.
VAL from_above: N=34, median 5-minute price-minus-level=7.875, mean=3.022, fraction above the level=0.647.
VAL cross check: share of directional touches that print 4 ticks through the boundary before the session window ends=1.000. This share is not a selected threshold.

## Opening location and distance from previous POC

Question: where does the first trade of session D sit relative to the previous value area and previous POC, and what is the 5-minute response after the later POC touch?

Definition: open is the first trade of session D. Location is below previous VAL, inside previous VAL to VAH, or above previous VAH. Distance bins are the predeclared fractions of the previous profile range. A zero range is left undefined.

profile_location above_vah: N=6, median 5-minute POC response=-6.625, mean=-31.625.
profile_location below_val: N=6, median 5-minute POC response=19.750, mean=24.875.
profile_location inside_value: N=38, median 5-minute POC response=-2.750, mean=-4.737.
distance_from_poc 0-25%: N=43, median 5-minute POC response=-3.500, mean=-3.605.
distance_from_poc 25-50%: N=5, median 5-minute POC response=4.250, mean=-29.000.
distance_from_poc 50-75%: N=1, median 5-minute POC response=-27.000, mean=-27.000.
distance_from_poc 75-100%: N=1, median 5-minute POC response=106.500, mean=106.500.

## POC migration

Question: is the already completed migration from POC(D-2) to POC(D-1), scaled by the D-2 profile range, associated with where session D opens or with the later 5-minute POC response?

Definition: session D does not contribute its own POC. Rows are dropped when D, D-1, or D-2 is a roll transition. Bins were declared in CONFIG.yaml.

-25% to +25%: N=16, median 5-minute POC response=-8.125, share inside previous value=0.440, share below VAL=0.200, share above VAH=0.360.
-50% to -25%: N=4, median 5-minute POC response=25.750, share inside previous value=0.400, share below VAL=0.400, share above VAH=0.200.
<=-50% range: N=8, median 5-minute POC response=0.125, share inside previous value=0.750, share below VAL=0.167, share above VAH=0.083.
>+50% range: N=14, median 5-minute POC response=-0.125, share inside previous value=0.688, share below VAL=0.062, share above VAH=0.250.

## Limitations

- About six months of one continuous contract series. A month with a small N cannot confirm or reject a mechanism.
- `NQ.c.0` changes contracts. Flagged transition sessions are removed from these tables rather than back-adjusted.
- The first and last sessions can be incomplete because the files start and end on UTC midnights. The 30-minute coverage rule removes them. It does not use the later price path.
- Forward prices stop at the session boundary. A horizon that would run into the next session is left empty.
- Same-timestamp order is Databento sequence, not an exchange match-time finer than that.
- The diagnostic profile and path use the middle eligible session date 2026-06-24, not a date chosen after seeing the response.
- No horizon, tolerance, value-area percentage, or bin was changed after seeing these numbers.

