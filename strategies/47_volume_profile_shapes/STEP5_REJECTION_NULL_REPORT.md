# Step 5 — Null-calibrated LVN rejection

This report does not test profitability, entries, exits, or forward returns. Tests use `STEP5_PREREGISTRATION.md`. Those rules were not changed after the tables were seen. A reject is not a trade.

`Traversal failed` is already established in Step 4. This step asks whether **rejection works** as a structural effect.

## A. Sample

- Primary rows: 34 per horizon (12 lower→upper, 22 upper→lower), inherited from Step 4.
- `null_reject_prob = 1 - null_traverse_prob` from the touch-bar open distances.
- Null A is the complementary decided test. It is not independent of Step 4.
- Null B is unconditional: remain and traverse count against rejection.
- Null C/D remove same-minute / touch-bar approach-HVN hits.

## B. Same-minute vs delayed rejects

| Horizon | Rejects | Same-minute | Delayed |
| --- | ---: | ---: | ---: |
| H30 | 17 | 8 | 9 |
| H60 | 19 | 8 | 11 |
| H120 | 22 | 8 | 14 |
| session_end | 26 | 8 | 18 |

## C. Null comparisons

| Horizon | Test | N | Null N | Reject N | Observed reject | Mean null reject | Observed − null |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H30 | A_decided | 18 | 18 | 17 | 0.944 | 0.858 | 0.086 |
| H30 | B_unconditional | 34 | 34 | 17 | 0.500 | 0.835 | -0.335 |
| H30 | C_delayed_decided | 10 | 10 | 9 | 0.900 | 0.794 | 0.106 |
| H30 | D_no_touch_hit_unconditional | 26 | 26 | 9 | 0.346 | 0.803 | -0.457 |
| H60 | A_decided | 20 | 20 | 19 | 0.950 | 0.845 | 0.105 |
| H60 | B_unconditional | 34 | 34 | 19 | 0.559 | 0.835 | -0.276 |
| H60 | C_delayed_decided | 12 | 12 | 11 | 0.917 | 0.783 | 0.134 |
| H60 | D_no_touch_hit_unconditional | 26 | 26 | 11 | 0.423 | 0.803 | -0.380 |
| H120 | A_decided | 25 | 25 | 22 | 0.880 | 0.834 | 0.046 |
| H120 | B_unconditional | 34 | 34 | 22 | 0.647 | 0.835 | -0.187 |
| H120 | C_delayed_decided | 17 | 17 | 14 | 0.824 | 0.785 | 0.038 |
| H120 | D_no_touch_hit_unconditional | 26 | 26 | 14 | 0.538 | 0.803 | -0.264 |
| session_end | A_decided | 34 | 34 | 26 | 0.765 | 0.835 | -0.070 |
| session_end | B_unconditional | 34 | 34 | 26 | 0.765 | 0.835 | -0.070 |
| session_end | C_delayed_decided | 26 | 26 | 18 | 0.692 | 0.803 | -0.110 |
| session_end | D_no_touch_hit_unconditional | 26 | 26 | 18 | 0.692 | 0.803 | -0.110 |

## D. Primary horizons in words

### H60

- Null A (decided, complementary): observed 0.950 vs null 0.845 (difference 0.105).
- Null B (unconditional): observed 0.559 vs null 0.835 (difference -0.276).
- Null C (delayed decided): N=12, observed 0.917 vs null 0.783 (difference 0.134).
- Null D (no touch-bar approach hit): N=26, observed 0.423 vs null 0.803 (difference -0.380).

### H120

- Null A (decided, complementary): observed 0.880 vs null 0.834 (difference 0.046).
- Null B (unconditional): observed 0.647 vs null 0.835 (difference -0.187).
- Null C (delayed decided): N=17, observed 0.824 vs null 0.785 (difference 0.038).
- Null D (no touch-bar approach hit): N=26, observed 0.538 vs null 0.803 (difference -0.264).

## E. Reject location and path extent

| Horizon | Location | N | Share | Med minutes | Med LVN pen. | Med opp. excursion |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| H30 | band_only | 16 | 0.941 | 1.0 | 0.085 | 0.161 |
| H30 | past_far_edge | 1 | 0.059 | 28.0 | 1.000 | 0.281 |
| H30 | ALL_REJECTS | 17 | 1.000 | 2.0 | 0.090 | 0.171 |
| H60 | band_only | 18 | 0.947 | 2.0 | 0.085 | 0.161 |
| H60 | past_far_edge | 1 | 0.053 | 28.0 | 1.000 | 0.281 |
| H60 | ALL_REJECTS | 19 | 1.000 | 2.0 | 0.090 | 0.171 |
| H120 | band_only | 21 | 0.955 | 5.0 | 0.101 | 0.187 |
| H120 | past_far_edge | 1 | 0.045 | 28.0 | 1.000 | 0.281 |
| H120 | ALL_REJECTS | 22 | 1.000 | 6.0 | 0.140 | 0.217 |
| session_end | band_only | 23 | 0.885 | 7.0 | 0.178 | 0.247 |
| session_end | past_far_edge | 3 | 0.115 | 183.0 | 1.000 | 0.656 |
| session_end | ALL_REJECTS | 26 | 1.000 | 8.0 | 0.279 | 0.287 |

## F. Slices on Null B (unconditional)

| Horizon | Slice | N | Observed reject | Mean null | Observed − null |
| --- | --- | ---: | ---: | ---: | ---: |
| H60 | lower_to_upper | 12 | 0.667 | 0.853 | -0.186 |
| H60 | upper_to_lower | 22 | 0.500 | 0.824 | -0.324 |
| H60 | clean | 11 | 0.818 | 0.869 | -0.050 |
| H60 | both_regions_sized | 20 | 0.550 | 0.843 | -0.293 |
| H120 | lower_to_upper | 12 | 0.750 | 0.853 | -0.103 |
| H120 | upper_to_lower | 22 | 0.591 | 0.824 | -0.234 |
| H120 | clean | 11 | 0.909 | 0.869 | 0.041 |
| H120 | both_regions_sized | 20 | 0.600 | 0.843 | -0.243 |

## G. Interpretation

1. Null A must match the opposite of Step 4's decided traverse gap. If it does, that only restates the killed traverse result.
2. Null B is the claim that matters for a rejection mechanism inside a fixed horizon.
3. A large same-minute share means many “rejects” are the first LVN minute also printing the nearby approach HVN, not a later reaction.
4. Null C/D ask whether any rejection effect remains after removing that same-minute geometry.

## Conclusion

At H60, same-minute rejects are 8 of 19 rejects; delayed are 11.

Null B at H60: observed reject rate 0.559 vs mean null 0.835 (difference -0.276).

Null B at H120: observed 0.647 vs null 0.835 (difference -0.187).

Null D at H60: observed 0.423 vs null 0.803 (difference -0.380), N=26.

Null D at H120: observed 0.538 vs null 0.803 (difference -0.264), N=26.

Null C at H60 (delayed decided): observed 0.917 vs null 0.783 (difference 0.134), N=12.

The short-horizon rejection claim does not clear the geometric null once remain outcomes and same-minute barrier hits are treated honestly. Rejects are common among decided paths, but that is largely the mirror of the killed traverse plus nearby approach-HVN geometry.

No forward return is computed here. No entry is defined.
