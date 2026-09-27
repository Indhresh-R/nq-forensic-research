# NQ IB — low-volume re-entry fade

Low relative-volume threshold (frozen from 2010–2018 lower tertile): **0.631**.

Rules: first baseline IB breakout must be low-volume; wait for the first later completed five-minute close back inside IB; enter opposite direction at the next one-minute open; stop beyond the excursion extreme plus one tick. Both IB-midpoint and opposite-IB targets are reported as predeclared alternatives.

## Results

| target      | split            |   trades |   avg_net_points |   win_rate |   profit_factor |   median_risk |   median_reward_r |   target_rate |   stop_rate |
|:------------|:-----------------|---------:|-----------------:|-----------:|----------------:|--------------:|------------------:|--------------:|------------:|
| ib_mid      | Inner_Validation |      159 |        -3.28145  |   0.339623 |        0.765585 |         16.75 |           2.10196 |     0.27044   |    0.63522  |
| ib_mid      | OOS              |      109 |         9.22362  |   0.394495 |        1.43415  |         32.5  |           2.67626 |     0.284404  |    0.53211  |
| ib_mid      | Train            |      395 |        -0.376582 |   0.382278 |        0.907436 |          5    |           1.92308 |     0.313924  |    0.556962 |
| ib_mid      | Validation       |      174 |         1.6056   |   0.402299 |        1.08555  |         28.75 |           2.06429 |     0.356322  |    0.568966 |
| opposite_ib | Inner_Validation |      159 |        -6.22484  |   0.251572 |        0.615183 |         16.75 |           4.47619 |     0.081761  |    0.704403 |
| opposite_ib | OOS              |      109 |         3.05046  |   0.284404 |        1.11879  |         32.5  |           5.77698 |     0.0917431 |    0.623853 |
| opposite_ib | Train            |      395 |        -0.412658 |   0.291139 |        0.913459 |          5    |           4.11111 |     0.131646  |    0.622785 |
| opposite_ib | Validation       |      174 |         3.53592  |   0.333333 |        1.17179  |         28.75 |           4.4475  |     0.132184  |    0.637931 |

Same-minute stop/target collision is a stop. Costs are 1.0 NQ point round trip. The target variant must be selected only from Train + Inner Validation.