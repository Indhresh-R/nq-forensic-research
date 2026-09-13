# ES Initial Balance breakout — frozen baseline

Not a live recommendation. This is a first mechanical test; no parameters were selected from its results.

## Split summary

| split      |   trades |   win_rate |   avg_net_points |   median_net_points |   net_points |   net_dollars_1_contract |   profit_factor |   max_drawdown_points |   max_drawdown_dollars_1_contract |   target_rate |   stop_rate |   time_rate |   long_trades |   short_trades |
|:-----------|---------:|-----------:|-----------------:|--------------------:|-------------:|-------------------------:|----------------:|----------------------:|----------------------------------:|--------------:|------------:|------------:|--------------:|---------------:|
| IS         |     2187 |   0.475995 |        -0.422268 |               -0.5  |      -923.5  |                 -46175   |        0.907788 |              -1288.75 |                          -64437.5 |      0.221765 |    0.216735 |    0.5615   |          1204 |            983 |
| Validation |      715 |   0.511888 |         0.153497 |                0.5  |       109.75 |                   5487.5 |        1.01612  |               -443.75 |                          -22187.5 |      0.272727 |    0.25035  |    0.476923 |           365 |            350 |
| OOS        |      389 |   0.511568 |         0.674165 |                0.75 |       262.25 |                  13112.5 |        1.06048  |               -691.25 |                          -34562.5 |      0.208226 |    0.203085 |    0.588689 |           214 |            175 |

## Yearly results

|   year | split      |   trades |   net_points |   avg_net_points |   win_rate |   net_dollars_1_contract |
|-------:|:-----------|---------:|-------------:|-----------------:|-----------:|-------------------------:|
|   2010 | IS         |       29 |        10.25 |         0.353448 |   0.551724 |                    512.5 |
|   2011 | IS         |       63 |        23.25 |         0.369048 |   0.492063 |                   1162.5 |
|   2012 | IS         |       96 |       -61.25 |        -0.638021 |   0.40625  |                  -3062.5 |
|   2013 | IS         |      191 |      -111.25 |        -0.582461 |   0.460733 |                  -5562.5 |
|   2014 | IS         |      188 |      -123    |        -0.654255 |   0.441489 |                  -6150   |
|   2015 | IS         |      212 |      -179    |        -0.84434  |   0.495283 |                  -8950   |
|   2016 | IS         |      240 |      -185.25 |        -0.771875 |   0.483333 |                  -9262.5 |
|   2017 | IS         |      223 |       -32.75 |        -0.146861 |   0.466368 |                  -1637.5 |
|   2018 | IS         |      240 |       107.75 |         0.448958 |   0.5      |                   5387.5 |
|   2019 | IS         |      232 |      -318.25 |        -1.37177  |   0.422414 |                 -15912.5 |
|   2020 | IS         |      237 |      -160    |        -0.675105 |   0.481013 |                  -8000   |
|   2021 | IS         |      236 |       106    |         0.449153 |   0.538136 |                   5300   |
|   2022 | Validation |      238 |       221.5  |         0.930672 |   0.546218 |                  11075   |
|   2023 | Validation |      236 |       -70    |        -0.29661  |   0.516949 |                  -3500   |
|   2024 | Validation |      241 |       -41.75 |        -0.173237 |   0.473029 |                  -2087.5 |
|   2025 | OOS        |      235 |        65.25 |         0.27766  |   0.52766  |                   3262.5 |
|   2026 | OOS        |      154 |       197    |         1.27922  |   0.487013 |                   9850   |

## Rules

- IB: 09:30–10:29 ET; first qualifying five-minute close starts at 10:34.
- Entry: next one-minute open. One trade maximum per session.
- Stop: opposite IB edge. Target: 1R. Time exit: 15:55 ET open.
- Same-bar stop/target collision: stop is assumed first. Net P&L deducts the configured round-trip cost.

A positive discovery result is not a finding. Require positive Validation and OOS results, then test cost, stop/target, and session-width sensitivity without repeatedly selecting on OOS.