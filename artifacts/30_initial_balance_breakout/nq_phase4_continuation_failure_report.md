# NQ IB — continuation vs failed-breakout audit

Labels use only the later outcome: `continuation` = target hit before stop; `failure` = stop hit before target. Time exits are intentionally excluded from this classification. Every candidate feature is known no later than the completed signal bar.

Clean labeled trades: **1117** (continuations: 559, failures: 558).

## Pre-2022 patterns that preserved their ordering

| feature               | continuation_bin   | failure_bin   |   train_gap |   inner_gap |     oos_gap |
|:----------------------|:-------------------|:--------------|------------:|------------:|------------:|
| breakout_excess_ib    | High               | Mid           |   0.100328  |   0.0481355 | -0.167059   |
| range_sofar_ib        | High               | Low           |   0.0683777 |   0.0241903 |  0.123333   |
| signal_delay_min      | Low                | Mid           |   0.0449627 |   0.0939755 | -0.080026   |
| signal_range_ib       | High               | Low           |   0.10023   |   0.0995671 | -0.00678295 |
| signal_vol_vs_ib5mean | High               | Low           |   0.0628571 |   0.105984  |  0.0941558  |
| trend_efficiency      | High               | Low           |   0.0514286 |   0.0676163 | -0.00775862 |

## Full tercile / boolean table

| feature               | period           | bin              |   n |   continuation_rate |   failure_rate |
|:----------------------|:-----------------|:-----------------|----:|--------------------:|---------------:|
| ib_vs_prior20         | Inner_Validation | Low              |  82 |            0.52439  |       0.47561  |
| ib_vs_prior20         | Inner_Validation | Mid              |  67 |            0.522388 |       0.477612 |
| ib_vs_prior20         | Inner_Validation | High             |  74 |            0.459459 |       0.540541 |
| ib_vs_prior20         | OOS              | Low              |  40 |            0.45     |       0.55     |
| ib_vs_prior20         | OOS              | Mid              |  35 |            0.628571 |       0.371429 |
| ib_vs_prior20         | OOS              | High             |  36 |            0.5      |       0.5      |
| ib_vs_prior20         | Train            | Low              | 173 |            0.468208 |       0.531792 |
| ib_vs_prior20         | Train            | Mid              | 172 |            0.453488 |       0.546512 |
| ib_vs_prior20         | Train            | High             | 172 |            0.52907  |       0.47093  |
| ib_vs_prior20         | Validation       | Low              |  86 |            0.523256 |       0.476744 |
| ib_vs_prior20         | Validation       | Mid              | 103 |            0.543689 |       0.456311 |
| ib_vs_prior20         | Validation       | High             |  70 |            0.485714 |       0.514286 |
| signal_delay_min      | Inner_Validation | Low              | 101 |            0.534653 |       0.465347 |
| signal_delay_min      | Inner_Validation | Mid              |  59 |            0.440678 |       0.559322 |
| signal_delay_min      | Inner_Validation | High             |  63 |            0.507937 |       0.492063 |
| signal_delay_min      | OOS              | Low              |  53 |            0.471698 |       0.528302 |
| signal_delay_min      | OOS              | Mid              |  29 |            0.551724 |       0.448276 |
| signal_delay_min      | OOS              | High             |  29 |            0.586207 |       0.413793 |
| signal_delay_min      | Train            | Low              | 201 |            0.507463 |       0.492537 |
| signal_delay_min      | Train            | Mid              | 160 |            0.4625   |       0.5375   |
| signal_delay_min      | Train            | High             | 163 |            0.478528 |       0.521472 |
| signal_delay_min      | Validation       | Low              | 115 |            0.478261 |       0.521739 |
| signal_delay_min      | Validation       | Mid              |  66 |            0.590909 |       0.409091 |
| signal_delay_min      | Validation       | High             |  78 |            0.525641 |       0.474359 |
| breakout_excess_ib    | Inner_Validation | Low              |  78 |            0.525641 |       0.474359 |
| breakout_excess_ib    | Inner_Validation | Mid              |  73 |            0.465753 |       0.534247 |
| breakout_excess_ib    | Inner_Validation | High             |  72 |            0.513889 |       0.486111 |
| breakout_excess_ib    | OOS              | Low              |  52 |            0.461538 |       0.538462 |
| breakout_excess_ib    | OOS              | Mid              |  34 |            0.647059 |       0.352941 |
| breakout_excess_ib    | OOS              | High             |  25 |            0.48     |       0.52     |
| breakout_excess_ib    | Train            | Low              | 175 |            0.468571 |       0.531429 |
| breakout_excess_ib    | Train            | Mid              | 174 |            0.442529 |       0.557471 |
| breakout_excess_ib    | Train            | High             | 175 |            0.542857 |       0.457143 |
| breakout_excess_ib    | Validation       | Low              |  97 |            0.515464 |       0.484536 |
| breakout_excess_ib    | Validation       | Mid              |  87 |            0.494253 |       0.505747 |
| breakout_excess_ib    | Validation       | High             |  75 |            0.56     |       0.44     |
| signal_body_fraction  | Inner_Validation | Low              |  75 |            0.533333 |       0.466667 |
| signal_body_fraction  | Inner_Validation | Mid              |  63 |            0.52381  |       0.47619  |
| signal_body_fraction  | Inner_Validation | High             |  85 |            0.458824 |       0.541176 |
| signal_body_fraction  | OOS              | Low              |  52 |            0.461538 |       0.538462 |
| signal_body_fraction  | OOS              | Mid              |  31 |            0.612903 |       0.387097 |
| signal_body_fraction  | OOS              | High             |  28 |            0.535714 |       0.464286 |
| signal_body_fraction  | Train            | Low              | 175 |            0.417143 |       0.582857 |
| signal_body_fraction  | Train            | Mid              | 174 |            0.511494 |       0.488506 |
| signal_body_fraction  | Train            | High             | 175 |            0.525714 |       0.474286 |
| signal_body_fraction  | Validation       | Low              | 103 |            0.436893 |       0.563107 |
| signal_body_fraction  | Validation       | Mid              |  74 |            0.608108 |       0.391892 |
| signal_body_fraction  | Validation       | High             |  82 |            0.54878  |       0.45122  |
| signal_range_ib       | Inner_Validation | Low              |  77 |            0.415584 |       0.584416 |
| signal_range_ib       | Inner_Validation | Mid              |  80 |            0.575    |       0.425    |
| signal_range_ib       | Inner_Validation | High             |  66 |            0.515152 |       0.484848 |
| signal_range_ib       | OOS              | Low              |  43 |            0.465116 |       0.534884 |
| signal_range_ib       | OOS              | Mid              |  44 |            0.613636 |       0.386364 |
| signal_range_ib       | OOS              | High             |  24 |            0.458333 |       0.541667 |
| signal_range_ib       | Train            | Low              | 175 |            0.44     |       0.56     |
| signal_range_ib       | Train            | Mid              | 175 |            0.474286 |       0.525714 |
| signal_range_ib       | Train            | High             | 174 |            0.54023  |       0.45977  |
| signal_range_ib       | Validation       | Low              |  84 |            0.511905 |       0.488095 |
| signal_range_ib       | Validation       | Mid              | 100 |            0.52     |       0.48     |
| signal_range_ib       | Validation       | High             |  75 |            0.533333 |       0.466667 |
| signal_vol_vs_ib5mean | Inner_Validation | Low              |  68 |            0.514706 |       0.485294 |
| signal_vol_vs_ib5mean | Inner_Validation | Mid              |  97 |            0.42268  |       0.57732  |
| signal_vol_vs_ib5mean | Inner_Validation | High             |  58 |            0.62069  |       0.37931  |
| signal_vol_vs_ib5mean | OOS              | Low              |  44 |            0.477273 |       0.522727 |
| signal_vol_vs_ib5mean | OOS              | Mid              |  39 |            0.538462 |       0.461538 |
| signal_vol_vs_ib5mean | OOS              | High             |  28 |            0.571429 |       0.428571 |
| signal_vol_vs_ib5mean | Train            | Low              | 175 |            0.462857 |       0.537143 |
| signal_vol_vs_ib5mean | Train            | Mid              | 174 |            0.465517 |       0.534483 |
| signal_vol_vs_ib5mean | Train            | High             | 175 |            0.525714 |       0.474286 |
| signal_vol_vs_ib5mean | Validation       | Low              |  91 |            0.505495 |       0.494505 |
| signal_vol_vs_ib5mean | Validation       | Mid              |  98 |            0.469388 |       0.530612 |
| signal_vol_vs_ib5mean | Validation       | High             |  70 |            0.614286 |       0.385714 |
| vwap_distance_ib      | Inner_Validation | Low              |  73 |            0.493151 |       0.506849 |
| vwap_distance_ib      | Inner_Validation | Mid              |  76 |            0.526316 |       0.473684 |
| vwap_distance_ib      | Inner_Validation | High             |  74 |            0.486486 |       0.513514 |
| vwap_distance_ib      | OOS              | Low              |  49 |            0.44898  |       0.55102  |
| vwap_distance_ib      | OOS              | Mid              |  39 |            0.615385 |       0.384615 |
| vwap_distance_ib      | OOS              | High             |  23 |            0.521739 |       0.478261 |
| vwap_distance_ib      | Train            | Low              | 175 |            0.451429 |       0.548571 |
| vwap_distance_ib      | Train            | Mid              | 174 |            0.454023 |       0.545977 |
| vwap_distance_ib      | Train            | High             | 175 |            0.548571 |       0.451429 |
| vwap_distance_ib      | Validation       | Low              |  97 |            0.525773 |       0.474227 |
| vwap_distance_ib      | Validation       | Mid              |  80 |            0.525    |       0.475    |
| vwap_distance_ib      | Validation       | High             |  82 |            0.512195 |       0.487805 |
| trend_efficiency      | Inner_Validation | Low              |  59 |            0.389831 |       0.610169 |
| trend_efficiency      | Inner_Validation | Mid              |  70 |            0.657143 |       0.342857 |
| trend_efficiency      | Inner_Validation | High             |  94 |            0.457447 |       0.542553 |
| trend_efficiency      | OOS              | Low              |  29 |            0.482759 |       0.517241 |
| trend_efficiency      | OOS              | Mid              |  42 |            0.595238 |       0.404762 |
| trend_efficiency      | OOS              | High             |  40 |            0.475    |       0.525    |
| trend_efficiency      | Train            | Low              | 175 |            0.451429 |       0.548571 |
| trend_efficiency      | Train            | Mid              | 174 |            0.5      |       0.5      |
| trend_efficiency      | Train            | High             | 175 |            0.502857 |       0.497143 |
| trend_efficiency      | Validation       | Low              |  78 |            0.5      |       0.5      |
| trend_efficiency      | Validation       | Mid              |  91 |            0.571429 |       0.428571 |
| trend_efficiency      | Validation       | High             |  90 |            0.488889 |       0.511111 |
| range_sofar_ib        | Inner_Validation | Low              |  82 |            0.45122  |       0.54878  |
| range_sofar_ib        | Inner_Validation | Mid              |  80 |            0.575    |       0.425    |
| range_sofar_ib        | Inner_Validation | High             |  61 |            0.47541  |       0.52459  |
| range_sofar_ib        | OOS              | Low              |  50 |            0.46     |       0.54     |
| range_sofar_ib        | OOS              | Mid              |  37 |            0.567568 |       0.432432 |
| range_sofar_ib        | OOS              | High             |  24 |            0.583333 |       0.416667 |
| range_sofar_ib        | Train            | Low              | 176 |            0.448864 |       0.551136 |
| range_sofar_ib        | Train            | Mid              | 174 |            0.488506 |       0.511494 |
| range_sofar_ib        | Train            | High             | 174 |            0.517241 |       0.482759 |
| range_sofar_ib        | Validation       | Low              | 102 |            0.509804 |       0.490196 |
| range_sofar_ib        | Validation       | Mid              |  88 |            0.477273 |       0.522727 |
| range_sofar_ib        | Validation       | High             |  69 |            0.594203 |       0.405797 |
| es_confirms           | Inner_Validation | Confirms         | 131 |            0.503817 |       0.496183 |
| es_confirms           | Inner_Validation | Does_not_confirm |  92 |            0.5      |       0.5      |
| es_confirms           | OOS              | Confirms         |  73 |            0.493151 |       0.506849 |
| es_confirms           | OOS              | Does_not_confirm |  38 |            0.578947 |       0.421053 |
| es_confirms           | Train            | Confirms         | 312 |            0.448718 |       0.551282 |
| es_confirms           | Train            | Does_not_confirm | 212 |            0.537736 |       0.462264 |
| es_confirms           | Validation       | Confirms         | 156 |            0.544872 |       0.455128 |
| es_confirms           | Validation       | Does_not_confirm | 103 |            0.485437 |       0.514563 |