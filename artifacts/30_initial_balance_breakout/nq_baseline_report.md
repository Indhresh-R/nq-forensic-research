# NQ Initial Balance breakout — frozen baseline

Not a live recommendation. This is a first mechanical test; no parameters were selected from its results.

## Split summary

| split      |   trades |   win_rate |   avg_net_points |   median_net_points |   net_points |   net_dollars_1_contract |   profit_factor |   max_drawdown_points |   max_drawdown_dollars_1_contract |   target_rate |   stop_rate |   time_rate |   long_trades |   short_trades |
|:-----------|---------:|-----------:|-----------------:|--------------------:|-------------:|-------------------------:|----------------:|----------------------:|----------------------------------:|--------------:|------------:|------------:|--------------:|---------------:|
| IS         |     2118 |   0.492918 |          0.4555  |               -0.25 |       964.75 |                    19295 |         1.03077 |              -2184.25 |                            -43685 |      0.172805 |    0.179887 |    0.647309 |          1186 |            932 |
| Validation |      695 |   0.551079 |          4.53094 |               10.25 |      3149    |                    62980 |         1.1132  |              -1275.75 |                            -25515 |      0.194245 |    0.178417 |    0.627338 |           358 |            337 |
| OOS        |      370 |   0.540541 |          6.3     |               16    |      2331    |                    46620 |         1.12215 |              -1853.25 |                            -37065 |      0.156757 |    0.143243 |    0.7      |           211 |            159 |

## Yearly results

|   year | split      |   trades |   net_points |   avg_net_points |   win_rate |   net_dollars_1_contract |
|-------:|:-----------|---------:|-------------:|-----------------:|-----------:|-------------------------:|
|   2010 | IS         |       27 |        -5    |        -0.185185 |   0.444444 |                     -100 |
|   2011 | IS         |       60 |       -27    |        -0.45     |   0.416667 |                     -540 |
|   2012 | IS         |       94 |       -71    |        -0.755319 |   0.414894 |                    -1420 |
|   2013 | IS         |      185 |      -335.25 |        -1.81216  |   0.448649 |                    -6705 |
|   2014 | IS         |      186 |       -56.5  |        -0.303763 |   0.510753 |                    -1130 |
|   2015 | IS         |      206 |      -595.5  |        -2.89078  |   0.466019 |                   -11910 |
|   2016 | IS         |      230 |      -672    |        -2.92174  |   0.421739 |                   -13440 |
|   2017 | IS         |      224 |       -52.5  |        -0.234375 |   0.46875  |                    -1050 |
|   2018 | IS         |      229 |       385.75 |         1.6845   |   0.502183 |                     7715 |
|   2019 | IS         |      218 |       -83.5  |        -0.383028 |   0.495413 |                    -1670 |
|   2020 | IS         |      235 |       354    |         1.50638  |   0.548936 |                     7080 |
|   2021 | IS         |      224 |      2123.25 |         9.47879  |   0.625    |                    42465 |
|   2022 | Validation |      233 |      2179    |         9.35193  |   0.587983 |                    43580 |
|   2023 | Validation |      232 |       847.5  |         3.65302  |   0.556034 |                    16950 |
|   2024 | Validation |      230 |       122.5  |         0.532609 |   0.508696 |                     2450 |
|   2025 | OOS        |      230 |      1483.25 |         6.44891  |   0.552174 |                    29665 |
|   2026 | OOS        |      140 |       847.75 |         6.05536  |   0.521429 |                    16955 |

## Rules

- IB: 09:30–10:29 ET; first qualifying five-minute close starts at 10:34.
- Entry: next one-minute open. One trade maximum per session.
- Stop: opposite IB edge. Target: 1R. Time exit: 15:55 ET open.
- Same-bar stop/target collision: stop is assumed first. Net P&L deducts the configured round-trip cost.

A positive discovery result is not a finding. Require positive Validation and OOS results, then test cost, stop/target, and session-width sensitivity without repeatedly selecting on OOS.