# B4 cost-sensitivity diagnostic

This is a post-registration diagnostic, not a new candidate search or a re-selection. Entries, signals, targets, stops, and all trade paths are exactly those in the frozen B4 results. Only the combined round-trip cost is changed.

| candidate            |   combined_round_trip_cost |   required_win_rate | clears_feasibility   |    n |   net_dollars |   win_rate |   payoff |   profit_factor |
|:---------------------|---------------------------:|--------------------:|:---------------------|-----:|--------------:|-----------:|---------:|----------------:|
| B4_zmean_nearer_1p5R |                          0 |            0.782147 | True                 | 2416 |      9433.25  |   0.840232 | 0.283824 |        1.49265  |
| B4_zmean_nearer_1p5R |                          2 |            0.769908 | True                 | 2416 |      4601.25  |   0.801738 | 0.304232 |        1.23027  |
| B4_zmean_nearer_1p5R |                          4 |            0.687735 | False                | 2416 |      -230.754 |   0.682533 | 0.460067 |        0.989114 |

The feasibility requirement is recalculated from each scenario's realized net payoff using the locked formula. This diagnostic cannot change the original Step 2 selection result.