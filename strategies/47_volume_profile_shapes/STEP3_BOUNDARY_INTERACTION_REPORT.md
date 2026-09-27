# Step 3 — Prior-session structural boundaries

This report does not test profitability, entries, exits, or forward returns. Boundaries and interactions use the rules in `STEP3_PREREGISTRATION.md`. Those rules were not changed after the tables were seen. An LVN-band touch is not a trade.

## A. Dataset verification

- Prior material gaps: 54 from Step 2.
- With a later analysis session: 53.
- Without a later analysis session: 1.
- Interaction sample after completeness and sync checks: 53.
- Exclusions: {'': 53, 'no_next_session': 1}.
- Next-session path: one-minute OHLC built from the same `trades_24h` files as Step 1. The continuous adjusted 1-minute file is not used.
- Trade-bar high/low matches the stored next-session profile high/low within 1.0 point on every interaction-sample row.
- Detail: `results/step3_boundary_verification.json`, `results/step3_interaction_verification.json`.

The 0.20 separation cut, the 0.30 depth cut, the 0.25 size label, and the 0.70 width threshold stay frozen.

## B. Boundary objects

One row is one prior material gap. Valley depth is stored only as an audit field. Boundaries are not ranked by depth.

| Measure | Min | p25 | Median | p75 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Separation | 0.202 | 0.225 | 0.267 | 0.328 | 0.583 |
| Valley width | 0.021 | 0.127 | 0.173 | 0.216 | 0.499 |
| Lower region share | 0.044 | 0.348 | 0.463 | 0.604 | 0.828 |
| Upper region share | 0.096 | 0.321 | 0.451 | 0.565 | 0.932 |

`both_regions_sized` (min share ≥ 0.25): 36 of 54.
`clean` (no other detected peak in the gap): 18 of 54.

Median valley width is 0.173 of the prior range. That is a spatial band, not a single tick. Median separation remains 0.267.

## C. Touch rate

| Outcome | Boundaries | Share of interaction sample |
| --- | ---: | ---: |
| First LVN-band touch | 39 | 73.6% |
| No touch | 14 | 26.4% |

A prior separated structure is often revisited. It is not automatic: 14 of 53 next sessions never print into that band.

## D. Where the next session opens

| Open zone | Sessions | Share |
| --- | ---: | ---: |
| upper_region | 24 | 45.3% |
| lower_region | 10 | 18.9% |
| outside_above | 6 | 11.3% |
| lvn_band | 5 | 9.4% |
| outside_below | 4 | 7.5% |
| other_inside | 4 | 7.5% |

Opens already in an accepted region are common. Opens outside the prior profile happen, but they account for most of the no-touch cases:

| Open zone among no-touch | Sessions |
| --- | ---: |
| upper_region | 6 |
| outside_above | 4 |
| outside_below | 3 |
| other_inside | 1 |

## E. Approach into the first touch

Approach is the zone of the previous bar's close, or the open zone when the first bar is the touch. `lvn_band` is checked before the region labels, so a close already inside the band cannot be labeled as a region approach.

### All touches

Touches in this slice: 39.

| Approach | Touches | Share of touches | Later opposite HVN |
| --- | ---: | ---: | ---: |
| lower_region | 12 | 30.8% | 0.583 |
| upper_region | 22 | 56.4% | 0.773 |
| open_in_band | 5 | 12.8% | 0.800 |

Approaches with zero touches in this slice: outside_below, outside_above, other_inside.

Median minutes to first touch: 133.0. Quartiles: 9.0, 133.0, 325.0.

### Touches with both regions sized

Touches in this slice: 23.

| Approach | Touches | Share of touches | Later opposite HVN |
| --- | ---: | ---: | ---: |
| lower_region | 6 | 26.1% | 0.667 |
| upper_region | 14 | 60.9% | 0.714 |
| open_in_band | 3 | 13.0% | 0.667 |

Approaches with zero touches in this slice: outside_below, outside_above, other_inside.

Median minutes to first touch: 128.0. Quartiles: 2.5, 128.0, 218.5.

### Touches with a clean gap

Touches in this slice: 12.

| Approach | Touches | Share of touches | Later opposite HVN |
| --- | ---: | ---: | ---: |
| lower_region | 6 | 50.0% | 0.500 |
| upper_region | 5 | 41.7% | 1.000 |
| open_in_band | 1 | 8.3% | 1.000 |

Approaches with zero touches in this slice: outside_below, outside_above, other_inside.

Median minutes to first touch: 129.0. Quartiles: 0.0, 129.0, 181.2.

No touch in the full sample approached from `outside_below`, `outside_above`, or `other_inside`. Those open locations either never reached the band or, in the `other_inside` case, were rare among touches.

Upper-region approaches outnumber lower-region approaches (22 vs 12). That matches the open-zone mix: the next session more often starts already in the prior upper region.

## F. Path after the touch

Later opposite-HVN rates are in the tables above. On the full touch sample, 0.583 of lower-region approaches later reach the upper HVN, and 0.773 of upper-region approaches later reach the lower HVN.

`returned_to_approach` is 1.00 for every lower-region and upper-region touch in this sample. That is not evidence of mean reversion. The LVN band overlaps the edges of both regions by construction, so a bar that stays near the band still intersects the approach region. The flag is retained only because it was preregistered. It is not used in the verdict.

## G. What this does and does not show

1. The Step 2 separated-region object is real enough that the next session often prints into its low-volume band.
2. When it does, the path is usually from one of the two prior accepted regions, not from outside the prior structure.
3. Outside opens often never interact with that particular band.
4. Clean gaps and sized pairs do not create a different approach vocabulary. They shrink the count. They do not invent outside approaches.
5. Nothing here is a return, a directional edge, or an entry rule.

## Conclusion

The useful object is the prior-session HVN–LVN–HVN boundary under the frozen 0.20 separation rule, not a P/b/D/B label and not a valley-depth ranking.

Next-session price does interact with that boundary often enough to study. The first interaction is typically an approach from the upper or lower accepted region, or an open already in the band. Approaches from outside the prior profile are not the common touch path in this sample.

Forward returns are still not tested.

Verification snapshot: touched=39, no_touch=14, approach_counts={'lower_region': 12, 'upper_region': 22, 'outside_below': 0, 'outside_above': 0, 'other_inside': 0, 'open_in_band': 5}.
