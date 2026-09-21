# Step 4 — LVN reaction path

This report does not test profitability, entries, exits, or forward returns. Competing events use the rules in `STEP4_PREREGISTRATION.md`. Those rules were not changed after the tables were seen. A traverse is not a trade.

## A. Sample

- Primary rows: 34 (12 lower→upper, 22 upper→lower).
- `open_in_band` side table: 5 touches.
- Path events use the approach and opposite HVN prices, not the full accepted-region spans.
- Geometric null: `dist_to_approach / (dist_to_approach + dist_to_opposite)` from the touch-bar open.
- Primary horizons: H60 and H120. H30 and session_end are reported.

## B. Outcome counts by horizon (all primary approaches)

| Horizon | N | Traverse | Reject | Remain | Ambiguous same bar |
| --- | ---: | ---: | ---: | ---: | ---: |
| H30 | 34 | 1 | 17 | 16 | 0 |
| H60 | 34 | 1 | 19 | 14 | 0 |
| H120 | 34 | 3 | 22 | 9 | 0 |
| session_end | 34 | 8 | 26 | 0 | 0 |

## C. Traverse vs reject against the geometric null

The observed traverse share uses only rows that decided traverse or reject and have a defined null. Remain and ambiguous rows are excluded from that ratio.

| Horizon | Decided N | Null N | Observed traverse share | Mean null | Observed − null |
| --- | ---: | ---: | ---: | ---: | ---: |
| H30 | 18 | 18 | 0.056 | 0.142 | -0.086 |
| H60 | 20 | 20 | 0.050 | 0.155 | -0.105 |
| H120 | 25 | 25 | 0.120 | 0.166 | -0.046 |
| session_end | 34 | 34 | 0.235 | 0.165 | 0.070 |

## D. Slices on the primary horizons

### H60

| Slice | N | Trav | Rej | Rem | Amb | Decided | Obs trav | Null | Obs − null | Med min to trav | Med min to rej | Med LVN pen. | Med opp. excursion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 34 | 1 | 19 | 14 | 0 | 20 | 0.050 | 0.155 | -0.105 | 15.0 | 2.0 | 0.520 | 0.382 |
| lower_to_upper | 12 | 0 | 8 | 4 | 0 | 8 | 0.000 | 0.141 | -0.141 |  | 1.0 | 0.292 | 0.283 |
| upper_to_lower | 22 | 1 | 11 | 10 | 0 | 12 | 0.083 | 0.164 | -0.081 | 15.0 | 5.0 | 0.578 | 0.401 |
| clean | 11 | 0 | 9 | 2 | 0 | 9 | 0.000 | 0.141 | -0.141 |  | 0.0 | 0.663 | 0.467 |
| both_regions_sized | 20 | 0 | 11 | 9 | 0 | 11 | 0.000 | 0.137 | -0.137 |  | 2.0 | 0.471 | 0.333 |

### H120

| Slice | N | Trav | Rej | Rem | Amb | Decided | Obs trav | Null | Obs − null | Med min to trav | Med min to rej | Med LVN pen. | Med opp. excursion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 34 | 3 | 22 | 9 | 0 | 25 | 0.120 | 0.166 | -0.046 | 63.0 | 6.0 | 0.610 | 0.446 |
| lower_to_upper | 12 | 1 | 9 | 2 | 0 | 10 | 0.100 | 0.153 | -0.053 | 63.0 | 2.0 | 0.481 | 0.440 |
| upper_to_lower | 22 | 2 | 13 | 7 | 0 | 15 | 0.133 | 0.174 | -0.041 | 41.0 | 7.0 | 0.869 | 0.446 |
| clean | 11 | 0 | 10 | 1 | 0 | 10 | 0.000 | 0.129 | -0.129 |  | 1.0 | 0.663 | 0.467 |
| both_regions_sized | 20 | 1 | 12 | 7 | 0 | 13 | 0.077 | 0.161 | -0.084 | 67.0 | 3.5 | 0.544 | 0.421 |

## E. `open_in_band` side table

These touches have no approach side. The table is first HVN printed within the horizon.

| Horizon | N | Lower HVN first | Upper HVN first | Both same bar | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| H30 | 5 | 1 | 2 | 0 | 2 |
| H60 | 5 | 1 | 2 | 0 | 2 |
| H120 | 5 | 2 | 2 | 0 | 1 |
| session_end | 5 | 2 | 3 | 0 | 0 |

## F. Interpretation

1. Competing events are HVN-to-HVN. They do not reuse Step 3's region-span return flag.
2. The geometric null already expects some traverses when the measurement price sits closer to the approach HVN than to the opposite HVN.
3. The mechanism claim needs observed traverse share above that null on the decided subset, not merely a raw opposite-HVN hit rate from Step 3.
4. Remain rates matter: a large remain share means the boundary often does not resolve into either story inside the horizon.

## Conclusion

At H60: traverse 1, reject 19, remain 14 (N=34). Among decided rows, observed traverse share 0.050 vs mean null 0.155 (difference -0.105).

At H120: traverse 3, reject 22, remain 9. Observed traverse share 0.120 vs mean null 0.166 (difference -0.046).

The preferential-traverse story does not hold on this sample. After an accepted-region approach into the prior LVN band, the first HVN event is usually a return through the approach HVN, not a cross to the opposite HVN. Observed traverse shares sit at or below the geometric null at H60 and H120. Session-end eventually prints more opposite-HVN hits, but rejects still dominate (8 traverse vs 26 reject).

Slices (lower→upper, upper→lower, clean, sized) do not rescue a traverse mechanism at the primary horizons.

No forward return is computed here. No entry is defined. A return test built on `lower HVN → LVN → opposite HVN` as the typical path would be testing the wrong event.
