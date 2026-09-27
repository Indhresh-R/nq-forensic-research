# Preregistration — Step 7 geometric null for prior-POC interaction

Date frozen: 2026-09-21, before any Step 7 observed-versus-null touch rate, reflected-band touch rate, or observed-minus-null difference was computed.

This file does not reopen Steps 2–5. It does not reinterpret the Step 5 verdict `MECHANISM NOT SUPPORTED` or the Step 6 verdict `INCONCLUSIVE`. It does not use LVN bands, traverse events, or reject events. It does not change the Step 6 definitions of the prior POC, the prior range, the prior dominant third, the POC ±10% band, the open-to-POC fraction, the migration fraction, the exact POC crossing, or the next-session bars.

Step 7 does not test profitability, entries, exits, stops, targets, forward returns, or P&L.

## Question

Given the prior-session range, the prior POC, and the next session’s opening price, does next-session bar contact with the prior POC band differ from contact with the mirror-image band around that open?

The mirror keeps the open-to-center distance and the band width, and it drops the identity of the prior POC.

## Sample

Use the 95 Step 6 pairs in `results/step6_volume_location.csv` with `in_location_sample` true. Do not add a pair, drop a pair, or bridge a missing session. The position of the reflected center is not an exclusion.

## Frozen Step 6 objects

From the stored Step 6 row and the same trade-built one-minute bars:

| Object | Rule |
| --- | --- |
| `O` | First-bar open of the next session |
| `P` | `prior_poc` |
| `R` | `prior_range` = prior profile high − prior profile low |
| POC band | `[P - 0.10 * R, P + 0.10 * R]` |
| Band touch | Any next-session bar whose `[low, high]` intersects the band, using the Step 6 comparison (`high >= band_low - 1e-12` and `low <= band_high + 1e-12`) |
| Exact cross | Any bar with `low <= level + 1e-12` and `high >= level - 1e-12` |
| Minutes to touch | Timestamp of the first intersecting bar minus the first bar, in minutes. Missing when there is no touch |
| VWAP proxy | Volume-weighted mean of bar typical price `(high + low + close) / 3` |
| Close imbalance | After the first bar that contains the level, later closes above the level minus later closes below it. Closes equal to the level count in neither side |

`0.10` is the frozen Step 1 / Step 6 band fraction. It is not searched.

## Frozen geometric null

For each pair:

```text
d = P - O
P_null = O - d
```

which is the same point as `P_null = 2 * O - P`.

```text
abs(P_null - O) = abs(P - O)
```

Observed band: `[P - 0.10 * R, P + 0.10 * R]`

Null band: `[P_null - 0.10 * R, P_null + 0.10 * R]`

Both bands are scored with the same next-session bars. The reflected center and the reflected band are not clipped to the prior range, even when they fall outside that range.

### Rationale, fixed before the comparison

A uniform draw of a center inside the prior range would change the open-to-location distance. The next session’s open is a property of where trade resumed, not a reason to treat a farther level as the matched control.

The reflection preserves the observed absolute distance from the open to the center and uses the same half-width `0.10 * R`. It removes the prior POC’s identity and which side of the open that POC sits on. What remains is the local geometry: how far a band of this width sits from the open.

This is a deterministic geometric counterfactual: what the same touch rule would record if the prior POC occupied the mirror-image location around the next open. It is not a draw, and no randomization is added. The reflection rule is not changed after the rates are known.

## Primary endpoint

One endpoint, on all 95 pairs:

```text
T_obs  = share of pairs whose bars intersect the POC band
T_null = share of pairs whose bars intersect the null band
delta  = T_obs - T_null
```

The difference equals `(n_poc_only - n_null_only) / 95`, where the four cells are both bands, POC band only, null band only, and neither. Those cells are the decomposition of `delta`, not extra endpoints.

Step 6 already recorded `T_obs = 70 / 95`. The recomputation must match that count. This preregistration does not use the null-band count; that count has not been calculated.

## Verdict rule

Applied only to the primary `delta` on the full 95 pairs, after the audit below passes.

| Condition | Verdict |
| --- | --- |
| Audit fails, or the recomputed POC-band touch count is not 70 | `INCONCLUSIVE` |
| Audit passes and `delta > 0` | `MECHANISM SUPPORTED` |
| Audit passes and `delta <= 0` | `MECHANISM NOT SUPPORTED` |

No probability threshold is added. No randomization distribution is computed.

Secondary measurements and the robustness slices do not enter this rule. They cannot change `MECHANISM NOT SUPPORTED` into `MECHANISM SUPPORTED`.

If the verdict is `MECHANISM NOT SUPPORTED`, the prior-volume-location branch is closed. This result does not open another LVN, POC, or volume-profile variant, and it does not authorize a trading test.

## Secondary measurements

Definitions are fixed here. They are computed only after the primary touch flags exist. Each one uses the same `P_null`. None of them is a second primary endpoint.

1. **Exact level.** Share of bars-paths that contain `P`, share that contain `P_null`, and `delta_exact` = first share minus second share. Intersection is the Step 6 point rule.

2. **First-touch time.** For each band: number of touches, median minutes among touches, and number of touches at 0 minutes. Paired order, used only as a count: a non-touch is later than every finite touch; two non-touches are a tie; equal finite times are a tie. Report how many pairs touch the POC band sooner, how many touch the null band sooner, and how many tie.

3. **Migration distance.** Using the Step 6 VWAP proxy, compare mean `|VWAP - P| / R` with mean `|VWAP - P_null| / R`. The reported difference is the POC distance minus the null distance. Also count pairs strictly closer to `P`, strictly closer to `P_null`, and ties. A tie is an absolute price gap of at most `1e-8` between the two distances.

4. **Post-cross close imbalance.** The Step 6 imbalance functional at `P`, on pairs that contain `P`, and the same functional at `P_null`, on pairs that contain `P_null`. A paired comparison is reported only on pairs that contain both levels. If that subset has fewer than 15 pairs, mark it unstable and do not interpret the paired imbalance. This item does not enter the verdict.

## Robustness

Same primary touch rule. These slices are reported and do not replace the verdict.

1. Exact level versus the ±10% band: the exact-level secondary above.
2. Opening location: pairs with `|P - O| > 0.10 * R`, and the complementary pairs with `|P - O| <= 0.10 * R`. When `|P - O| <= 0.10 * R`, the open lies in both bands. If the first bar contains the open, both touch flags are 1, and those pairs add nothing to `n_poc_only - n_null_only`.
3. Prior POC location, using the stored `prior_poc_location` and two cuts that are not searched: lower if `< 1/3`, middle if `1/3 <= location < 2/3`, upper if `>= 2/3`. If a bin has fewer than 15 pairs, report that bin as unstable and do not interpret it. Do not retune the cuts.

## Temporal description

Not a verdict input. If the primary rates are also shown by time, the only cut is `next_session` before `2026-06-20` versus on or after `2026-06-20`. That date is the calendar midpoint of the frozen trade-file window `2026-03-25` through `2026-09-16`, already fixed from the file span. No other cut is used.

## Audit required before a verdict

- The file contains 95 in-sample pairs and no other pairs are scored.
- For every pair, `abs(abs(P_null - O) - abs(P - O)) <= 1e-6`.
- Both half-widths equal `0.10 * R`.
- `P_null` is the raw reflection. Nothing is clipped to the prior profile.
- Recomputed POC-band touches match `touched_poc_band` on every row, and the count is 70.
- Recomputed exact crossings of `P` match `crossed_poc` on every row, and the count is 67.
- Recomputed open, POC, range, and VWAP proxy match the Step 6 columns (`VWAP` within `1e-6`).
- The first bar contains its open (`low <= O <= high`).
- Both bands are scored on that same bar array.
- For every pair with `|P - O| <= 0.10 * R`, both band-touch flags are true.

If any item fails, the verdict is `INCONCLUSIVE` and the failed item is the result. The reflection rule is not adjusted to make the audit pass.

## What this step will not do

- It will not place a uniform center in the prior range.
- It will not randomize signs, paths, or centers.
- It will not clip `P_null` or the null band.
- It will not change the 95-pair sample or the 0.10 fraction.
- It will not compute strategy P&L.
- It will not let a secondary measurement replace the primary verdict.
