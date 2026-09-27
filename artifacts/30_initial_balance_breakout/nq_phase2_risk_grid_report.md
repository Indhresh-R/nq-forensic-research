# NQ IB — Phase 2 risk/target grid

All stop and target alternatives were declared in code before this grid was run. Candidates below were selected using Discovery only; Validation and OOS are confirmation columns.

## Full grid: mean net NQ points per trade

| stop_rule      |   target_r |        IS |       OOS |   Validation |
|:---------------|-----------:|----------:|----------:|-------------:|
| 0.25x_ib_width |       0.75 | -0.627862 | -2.35731  |      0.72844 |
| 0.25x_ib_width |       1    | -0.317723 | -0.232939 |      1.39793 |
| 0.25x_ib_width |       1.5  |  0.276071 |  1.79814  |      2.52617 |
| 0.25x_ib_width |       2    |  0.19048  |  2.81655  |      3.16511 |
| 0.50x_ib_width |       0.75 |  0.57181  | -3.0152   |      3.79933 |
| 0.50x_ib_width |       1    |  0.140286 | -0.655743 |      4.70701 |
| 0.50x_ib_width |       1.5  |  0.550342 | -3.59307  |      4.02545 |
| 0.50x_ib_width |       2    |  0.78063  | -3.50203  |      3.70216 |
| 0.75x_ib_width |       0.75 |  0.160817 |  3.88066  |      3.2875  |
| 0.75x_ib_width |       1    |  0.676051 |  1.56199  |      3.09191 |
| 0.75x_ib_width |       1.5  |  0.8795   |  0.693074 |      2.84501 |
| 0.75x_ib_width |       2    |  1.04943  |  0.431588 |      5.83282 |
| 1.00x_ib_width |       0.75 |  0.625059 |  3.29645  |      3.64901 |
| 1.00x_ib_width |       1    |  1.00732  |  2.25811  |      3.04353 |
| 1.00x_ib_width |       1.5  |  1.00413  |  2.19831  |      6.70953 |
| 1.00x_ib_width |       2    |  0.758026 |  3.41486  |      5.96259 |
| opposite_ib    |       0.75 |  0.565864 |  4.69324  |      4.4491  |
| opposite_ib    |       1    |  0.4555   |  6.3      |      4.53094 |
| opposite_ib    |       1.5  |  0.384856 |  5.89088  |      6.33903 |
| opposite_ib    |       2    |  0.21093  |  4.42297  |      6.73345 |

## Discovery-only selected candidates

| stop_rule      |   target_r |      IS |       OOS |   Validation | selection_basis                     |
|:---------------|-----------:|--------:|----------:|-------------:|:------------------------------------|
| 0.75x_ib_width |        2   | 1.04943 |  0.431588 |      5.83282 | top_5 Discovery avg_net_points only |
| 1.00x_ib_width |        1   | 1.00732 |  2.25811  |      3.04353 | top_5 Discovery avg_net_points only |
| 1.00x_ib_width |        1.5 | 1.00413 |  2.19831  |      6.70953 | top_5 Discovery avg_net_points only |
| 0.75x_ib_width |        1.5 | 0.8795  |  0.693074 |      2.84501 | top_5 Discovery avg_net_points only |
| 0.50x_ib_width |        2   | 0.78063 | -3.50203  |      3.70216 | top_5 Discovery avg_net_points only |

Risk rules: opposite IB edge, or a fixed 0.25/0.50/0.75/1.00 × IB-width stop from entry. Targets are 0.75/1.00/1.50/2.00R. Same-minute collisions use stop first. Cost is 1.0 point round trip.