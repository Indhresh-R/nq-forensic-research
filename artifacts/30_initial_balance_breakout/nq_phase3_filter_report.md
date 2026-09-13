# NQ IB — Phase 3 standalone causal filters

The entry and exit rules are unchanged. No filter combinations were searched. Selection uses only 2010–2018 Train and 2019–2021 Inner Validation.

## Mean net points per trade

| filter                          |   Inner_Validation |       OOS |     Train |   Validation |   n_Inner_Validation |   n_OOS |   n_Train |   n_Validation |
|:--------------------------------|-------------------:|----------:|----------:|-------------:|---------------------:|--------:|----------:|---------------:|
| baseline_all                    |            3.53582 |   6.3     | -0.991672 |      4.53094 |                  677 |     370 |      1441 |            695 |
| early_by_1130                   |            3.79526 |   3.99154 | -0.918814 |      8.14415 |                  464 |     266 |       970 |            496 |
| narrow_ib_le_0.80x_prior20      |            2.41509 |  -4.22991 | -1.95139  |      5.02669 |                  212 |     112 |       432 |            178 |
| normal_ib_0.80_to_1.25x_prior20 |            5.59117 |  25.0285  | -1.76805  |      5.125   |                  266 |     149 |       568 |            342 |
| risk_le_100pts                  |            1.04613 |  17.4022  | -1.24822  |     -0.42963 |                  401 |      23 |      1406 |            135 |
| risk_le_50pts                   |           -2.61051 | nan       | -1.55065  |    -11.625   |                  138 |     nan |      1234 |              4 |
| risk_le_75pts                   |            0.23741 |  25.25    | -1.13924  |     -7.05851 |                  278 |       6 |      1361 |             47 |
| strong_5m_breakout              |            3.19504 |  12.3129  | -1.03838  |      3.97331 |                  564 |     278 |      1205 |            562 |
| vwap_aligned                    |            3.53582 |   6.3     | -0.991672 |      4.53094 |                  677 |     370 |      1441 |            695 |

## Pre-2022 survivors

| filter        |   Inner_Validation |     OOS |     Train |   Validation |   n_Inner_Validation |   n_OOS |   n_Train |   n_Validation | selection_basis                                       |
|:--------------|-------------------:|--------:|----------:|-------------:|---------------------:|--------:|----------:|---------------:|:------------------------------------------------------|
| early_by_1130 |            3.79526 | 3.99154 | -0.918814 |      8.14415 |                  464 |     266 |       970 |            496 | better than baseline in Train + Inner_Validation only |

Filters are known at signal time: risk uses the already-known stop distance; VWAP uses RTH data through the completed signal bar; candle quality uses the completed five-minute signal bar; IB width uses only prior 20 completed sessions.