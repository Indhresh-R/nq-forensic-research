# MBO information diagnostic

Preregistered in `PREREGISTRATION.md` and run once. No feature was dropped after seeing these numbers.
The replay engine was not modified. Previous-session POC was not joined. Crossed rows remain in the store.

This is a 26-session diagnostic. It is not evidence of a durable edge.

## Exclusions

- Snapshot rows: 234000
- Crossed rows kept in the store and removed as anchors: 25
- Locked rows, also not usable quotes: 0
- Usable quotes (bid < ask): 233975

- Horizon 1s: future slots 233974, anchor crossed 25, anchor otherwise unusable 0, endpoint crossed 3, endpoint otherwise unusable 0, valid return anchors 233946.
- Horizon 5s: future slots 233870, anchor crossed 25, anchor otherwise unusable 0, endpoint crossed 15, endpoint otherwise unusable 0, valid return anchors 233830.
- Horizon 15s: future slots 233610, anchor crossed 25, anchor otherwise unusable 0, endpoint crossed 25, endpoint otherwise unusable 0, valid return anchors 233560.
- Horizon 30s: future slots 233220, anchor crossed 25, anchor otherwise unusable 0, endpoint crossed 25, endpoint otherwise unusable 0, valid return anchors 233170.
- Horizon 60s: future slots 232440, anchor crossed 25, anchor otherwise unusable 0, endpoint crossed 25, endpoint otherwise unusable 0, valid return anchors 232390.

Feature N is lower than the valid-anchor count when that feature is missing. Imbalance is missing when its denominator is 0. Rolling features are missing for the first w-1 seconds. Depth changes are missing unless both endpoints are usable quotes.

## Shape check

Horizon-stable means the five full-sample Spearman ICs share a sign. Split-stable means the early half and the late half at 5 seconds share that sign. Neither label selects a feature.

- trade_imbalance window 1: horizon-stable=True split-stable=True full-sample IC sign=-1
- trade_imbalance window 5: horizon-stable=False split-stable=False full-sample IC sign=-1
- trade_imbalance window 15: horizon-stable=False split-stable=False full-sample IC sign=-1
- trade_imbalance window 30: horizon-stable=False split-stable=False full-sample IC sign=-1
- trade_imbalance window 60: horizon-stable=False split-stable=False full-sample IC sign=-1
- obi_1 window 0: horizon-stable=True split-stable=True full-sample IC sign=1
- obi_5 window 0: horizon-stable=False split-stable=False full-sample IC sign=1
- depth_net_change window 1: horizon-stable=True split-stable=True full-sample IC sign=1
- depth_net_change window 5: horizon-stable=True split-stable=True full-sample IC sign=1
- depth_net_change window 15: horizon-stable=True split-stable=True full-sample IC sign=1
- replenish_net window 1: horizon-stable=False split-stable=False full-sample IC sign=1
- replenish_net window 5: horizon-stable=False split-stable=False full-sample IC sign=-1
- obi_x_flow window 5: horizon-stable=True split-stable=True full-sample IC sign=1

## Primary table

Median and mean are the forward mid return, in index points, when the feature is strictly positive. Sign % uses both nonzero sides. IC is the pooled Spearman correlation. Early is 2026-07-08 through 2026-07-24. Late is 2026-07-27 through 2026-08-12.

| Feature | Window | Horizon | N | Median fwd | Mean fwd | Median fwd x<0 | Sign % | IC | IC early | IC late |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| obi_1 | 0 | 1 | 233946 | 0.000 | 0.041 | 0.000 | 0.513 | 0.0161 | 0.0184 | 0.0138 |
| obi_1 | 0 | 5 | 233830 | 0.125 | 0.047 | 0.000 | 0.507 | 0.0082 | 0.0093 | 0.0071 |
| obi_1 | 0 | 15 | 233560 | 0.250 | 0.098 | 0.000 | 0.505 | 0.0074 | 0.0096 | 0.0054 |
| obi_1 | 0 | 30 | 233170 | 0.125 | 0.048 | 0.000 | 0.502 | 0.0037 | 0.0078 | -0.0002 |
| obi_1 | 0 | 60 | 232390 | 0.500 | 0.105 | 0.250 | 0.503 | 0.0068 | 0.0095 | 0.0042 |
| obi_5 | 0 | 1 | 233946 | 0.000 | 0.005 | 0.000 | 0.506 | 0.0094 | 0.0131 | 0.0056 |
| obi_5 | 0 | 5 | 233830 | 0.000 | -0.006 | 0.000 | 0.504 | 0.0032 | 0.0077 | -0.0012 |
| obi_5 | 0 | 15 | 233560 | 0.125 | -0.043 | 0.125 | 0.501 | -0.0019 | 0.0010 | -0.0047 |
| obi_5 | 0 | 30 | 233170 | 0.125 | -0.097 | 0.125 | 0.500 | -0.0038 | 0.0026 | -0.0104 |
| obi_5 | 0 | 60 | 232390 | 0.250 | -0.132 | 0.250 | 0.499 | -0.0015 | 0.0011 | -0.0040 |
| depth_net_change | 1 | 1 | 233917 | 0.000 | 0.016 | 0.000 | 0.507 | 0.0107 | 0.0114 | 0.0101 |
| depth_net_change | 1 | 5 | 233801 | 0.000 | 0.012 | 0.000 | 0.503 | 0.0040 | 0.0041 | 0.0038 |
| depth_net_change | 1 | 15 | 233531 | 0.125 | 0.009 | 0.000 | 0.502 | 0.0030 | 0.0032 | 0.0028 |
| depth_net_change | 1 | 30 | 233141 | 0.125 | -0.049 | 0.125 | 0.500 | 0.0010 | 0.0013 | 0.0008 |
| depth_net_change | 1 | 60 | 232361 | 0.375 | -0.061 | 0.250 | 0.501 | 0.0014 | 0.0016 | 0.0013 |
| depth_net_change | 5 | 1 | 233801 | 0.000 | 0.025 | 0.000 | 0.506 | 0.0097 | 0.0115 | 0.0081 |
| depth_net_change | 5 | 5 | 233685 | 0.000 | 0.028 | 0.000 | 0.502 | 0.0036 | 0.0068 | 0.0007 |
| depth_net_change | 5 | 15 | 233415 | 0.125 | 0.050 | 0.000 | 0.502 | 0.0046 | 0.0041 | 0.0051 |
| depth_net_change | 5 | 30 | 233025 | 0.125 | 0.003 | 0.125 | 0.500 | 0.0017 | 0.0014 | 0.0019 |
| depth_net_change | 5 | 60 | 232245 | 0.250 | -0.009 | 0.250 | 0.500 | 0.0009 | 0.0017 | 0.0002 |
| depth_net_change | 15 | 1 | 233531 | 0.000 | 0.030 | 0.000 | 0.508 | 0.0121 | 0.0138 | 0.0104 |
| depth_net_change | 15 | 5 | 233415 | 0.000 | 0.037 | 0.000 | 0.505 | 0.0075 | 0.0079 | 0.0073 |
| depth_net_change | 15 | 15 | 233145 | 0.125 | 0.043 | 0.000 | 0.503 | 0.0062 | 0.0057 | 0.0066 |
| depth_net_change | 15 | 30 | 232755 | 0.125 | -0.011 | 0.125 | 0.501 | 0.0022 | 0.0034 | 0.0010 |
| depth_net_change | 15 | 60 | 231975 | 0.375 | 0.005 | 0.250 | 0.500 | 0.0021 | 0.0030 | 0.0011 |
| obi_x_flow | 5 | 1 | 233842 | 0.000 | 0.002 | 0.000 | 0.503 | 0.0027 | -0.0011 | 0.0064 |
| obi_x_flow | 5 | 5 | 233726 | 0.000 | -0.005 | 0.000 | 0.500 | 0.0012 | 0.0001 | 0.0022 |
| obi_x_flow | 5 | 15 | 233456 | 0.125 | 0.035 | 0.125 | 0.501 | 0.0022 | -0.0014 | 0.0059 |
| obi_x_flow | 5 | 30 | 233066 | 0.250 | 0.052 | 0.000 | 0.503 | 0.0054 | 0.0035 | 0.0074 |
| obi_x_flow | 5 | 60 | 232286 | 0.375 | -0.008 | 0.250 | 0.500 | 0.0029 | -0.0032 | 0.0091 |
| replenish_net | 1 | 1 | 233946 | 0.000 | 0.033 | 0.000 | 0.496 | 0.0013 | 0.0026 | -0.0000 |
| replenish_net | 1 | 5 | 233830 | 0.000 | 0.033 | 0.000 | 0.499 | 0.0045 | 0.0035 | 0.0053 |
| replenish_net | 1 | 15 | 233560 | 0.125 | 0.022 | 0.125 | 0.499 | 0.0017 | -0.0001 | 0.0033 |
| replenish_net | 1 | 30 | 233170 | 0.125 | 0.019 | 0.125 | 0.501 | 0.0020 | 0.0033 | 0.0005 |
| replenish_net | 1 | 60 | 232390 | 0.250 | -0.028 | 0.250 | 0.500 | -0.0001 | 0.0006 | -0.0008 |
| replenish_net | 5 | 1 | 233842 | 0.000 | 0.025 | 0.000 | 0.497 | -0.0013 | -0.0065 | 0.0041 |
| replenish_net | 5 | 5 | 233726 | 0.000 | 0.028 | 0.125 | 0.495 | -0.0032 | -0.0045 | -0.0020 |
| replenish_net | 5 | 15 | 233456 | 0.125 | 0.066 | 0.125 | 0.500 | 0.0035 | 0.0019 | 0.0050 |
| replenish_net | 5 | 30 | 233066 | 0.125 | -0.015 | 0.125 | 0.501 | -0.0016 | 0.0030 | -0.0063 |
| replenish_net | 5 | 60 | 232286 | 0.250 | -0.073 | 0.250 | 0.500 | -0.0030 | -0.0014 | -0.0048 |
| trade_imbalance | 1 | 1 | 232693 | 0.000 | 0.007 | 0.000 | 0.495 | -0.0055 | -0.0049 | -0.0060 |
| trade_imbalance | 1 | 5 | 232578 | 0.000 | 0.012 | 0.000 | 0.497 | -0.0028 | -0.0027 | -0.0028 |
| trade_imbalance | 1 | 15 | 232314 | 0.000 | -0.001 | 0.125 | 0.499 | -0.0016 | -0.0013 | -0.0019 |
| trade_imbalance | 1 | 30 | 231929 | 0.125 | -0.012 | 0.125 | 0.500 | -0.0008 | 0.0016 | -0.0036 |
| trade_imbalance | 1 | 60 | 231162 | 0.250 | -0.055 | 0.375 | 0.500 | -0.0016 | 0.0004 | -0.0040 |
| trade_imbalance | 5 | 1 | 233842 | 0.000 | 0.001 | 0.000 | 0.495 | -0.0072 | -0.0124 | -0.0014 |
| trade_imbalance | 5 | 5 | 233726 | 0.000 | -0.028 | 0.125 | 0.494 | -0.0105 | -0.0124 | -0.0085 |
| trade_imbalance | 5 | 15 | 233456 | 0.125 | 0.002 | 0.125 | 0.500 | 0.0000 | 0.0007 | -0.0008 |
| trade_imbalance | 5 | 30 | 233066 | 0.125 | -0.064 | 0.125 | 0.499 | -0.0021 | 0.0032 | -0.0080 |
| trade_imbalance | 5 | 60 | 232286 | 0.250 | -0.069 | 0.250 | 0.501 | 0.0009 | 0.0063 | -0.0055 |
| trade_imbalance | 15 | 1 | 233582 | 0.000 | 0.000 | 0.000 | 0.497 | -0.0066 | -0.0110 | -0.0013 |
| trade_imbalance | 15 | 5 | 233466 | 0.000 | 0.006 | 0.000 | 0.499 | -0.0023 | -0.0072 | 0.0036 |
| trade_imbalance | 15 | 15 | 233196 | 0.125 | -0.017 | 0.000 | 0.502 | 0.0033 | 0.0082 | -0.0017 |
| trade_imbalance | 15 | 30 | 232806 | 0.000 | -0.152 | 0.250 | 0.496 | -0.0062 | 0.0009 | -0.0141 |
| trade_imbalance | 15 | 60 | 232026 | 0.375 | -0.075 | 0.250 | 0.501 | 0.0036 | 0.0116 | -0.0061 |
| trade_imbalance | 30 | 1 | 233192 | 0.000 | -0.001 | 0.000 | 0.497 | -0.0073 | -0.0087 | -0.0054 |
| trade_imbalance | 30 | 5 | 233076 | 0.000 | -0.022 | 0.000 | 0.499 | -0.0064 | -0.0044 | -0.0086 |
| trade_imbalance | 30 | 15 | 232806 | 0.125 | -0.071 | 0.125 | 0.500 | -0.0044 | 0.0035 | -0.0131 |
| trade_imbalance | 30 | 30 | 232416 | 0.000 | -0.144 | 0.125 | 0.498 | -0.0064 | 0.0046 | -0.0194 |
| trade_imbalance | 30 | 60 | 231636 | 0.250 | -0.092 | 0.250 | 0.501 | 0.0016 | 0.0132 | -0.0126 |
| trade_imbalance | 60 | 1 | 232412 | 0.000 | -0.006 | 0.000 | 0.496 | -0.0058 | -0.0051 | -0.0067 |
| trade_imbalance | 60 | 5 | 232296 | 0.000 | -0.033 | 0.000 | 0.498 | -0.0037 | -0.0001 | -0.0080 |
| trade_imbalance | 60 | 15 | 232026 | 0.125 | -0.045 | 0.000 | 0.502 | 0.0022 | 0.0109 | -0.0076 |
| trade_imbalance | 60 | 30 | 231636 | 0.125 | -0.125 | 0.125 | 0.499 | -0.0011 | 0.0118 | -0.0162 |
| trade_imbalance | 60 | 60 | 230856 | 0.375 | -0.121 | 0.250 | 0.503 | 0.0071 | 0.0163 | -0.0056 |

The full grid, including buy volume, sell volume, spread, depth, adds, and cancels, is in `results/information_summary.csv`.
Non-negative features have a rank correlation only. Their sign columns are blank.

Modification counts are not in the frozen store and were not tested.

## Reading

These numbers were not used to change the feature list.

Top-of-book imbalance is the only preregistered feature whose full-sample rank correlation stays positive at all five horizons, whose 5-second correlation has the same sign in both calendar halves, and whose 1-second correlation (0.016) matches the median of the 26 session correlations (0.018). Sign agreement is 51.3% at 1 second and 50.2% to 50.7% later. The median forward return is 0.00 points at 1 and 5 seconds. The mean, when imbalance is positive, is 0.041 points at 1 second. One NQ tick is 0.25 points.

Net depth change has the same sign pattern. Its 1-second correlation is 0.011 and it falls toward 0.001 by 60 seconds.

One-second trade imbalance is negative at every horizon, between -0.006 and -0.001, and both halves agree at 5 seconds. That is not trade continuation. Longer trade windows change sign across horizons and across the two halves.

The largest absolute correlation in the full grid is -0.020, for 30-second net replenishment against the 30-second return. The early half is -0.007 and the late half is -0.035, so that cell does not survive the split.

The product of book imbalance and 5-second trade imbalance stays between 0.001 and 0.005. The early half changes sign at horizons other than 5 seconds. It is not a separate result.

Previous-session POC was not joined.

