# Phase 12 — upside-failure asymmetry

No threshold selection. This report compares entire event distributions between failure directions and rank-correlates each continuous feature with 60-minute reversal net, separately by direction and period.

## Broad, same-sign feature/outcome relationships across all four periods

| direction             | feature           |   consistent_sign | correlations                                                                                                                 |
|:----------------------|:------------------|------------------:|:-----------------------------------------------------------------------------------------------------------------------------|
| downside_failure_long | excursion_ib      |                 1 | {'Inner': 0.1043397622978402, 'OOS': 0.040018452312305386, 'Train': 0.16184406538298216, 'Validation': 0.06268169712471273}  |
| downside_failure_long | outside_5m        |                 1 | {'Inner': 0.1565150716119931, 'OOS': 0.08931199077539566, 'Train': 0.15906524207936856, 'Validation': 0.048162790379489784}  |
| downside_failure_long | reentry_end       |                 1 | {'Inner': 0.05423898767599586, 'OOS': 0.09043643226699326, 'Train': 0.10372413691255361, 'Validation': 0.012891610709797514} |
| downside_failure_long | rejection_minutes |                 1 | {'Inner': 0.1918713446643436, 'OOS': 0.14860840147157311, 'Train': 0.15796747474398526, 'Validation': 0.011468609299656898}  |
| upside_failure_short  | excursion_ib      |                 1 | {'Inner': 0.08319140676136329, 'OOS': 0.008049722624015605, 'Train': 0.18845414019677215, 'Validation': 0.12005100933362275} |
| upside_failure_short  | outside_5m        |                 1 | {'Inner': 0.09581437461048237, 'OOS': 0.04676027806346663, 'Train': 0.1654240385673928, 'Validation': 0.17265331859414684}   |

## Directional distributions

| period     | feature           |   up_n |   up_median |   down_n |   down_median |   ks_stat |        ks_p |
|:-----------|:------------------|-------:|------------:|---------:|--------------:|----------:|------------:|
| Inner      | excursion_ib      |    283 |   0.186047  |      215 |     0.274686  | 0.213937  | 2.16244e-05 |
| Inner      | outside_5m        |    283 |   3         |      215 |     3         | 0.0692415 | 0.570151    |
| Inner      | reentry_depth_ib  |    283 |   0.0443925 |      215 |     0.0662252 | 0.141491  | 0.0131895   |
| Inner      | rejection_minutes |    283 |  10         |      215 |    10         | 0.0246692 | 0.999996    |
| Inner      | relvol            |    283 |   0.700791  |      215 |     0.947949  | 0.37349   | 1.05204e-15 |
| Inner      | reentry_end       |    283 | 694         |      215 |   689         | 0.0901471 | 0.253613    |
| OOS        | excursion_ib      |    163 |   0.155425  |      116 |     0.271185  | 0.323725  | 8.4133e-07  |
| OOS        | outside_5m        |    163 |   2         |      116 |     2         | 0.0486038 | 0.993777    |
| OOS        | reentry_depth_ib  |    163 |   0.0509317 |      116 |     0.0738187 | 0.166861  | 0.039717    |
| OOS        | rejection_minutes |    163 |   5         |      116 |     5         | 0.0642056 | 0.920183    |
| OOS        | relvol            |    163 |   0.648249  |      116 |     0.862617  | 0.372964  | 6.41535e-09 |
| OOS        | reentry_end       |    163 | 679         |      116 |   676.5       | 0.0698646 | 0.864396    |
| Train      | excursion_ib      |    545 |   0.210526  |      468 |     0.289178  | 0.180942  | 1.09359e-07 |
| Train      | outside_5m        |    545 |   3         |      468 |     3         | 0.0612091 | 0.286516    |
| Train      | reentry_depth_ib  |    545 |   0.0437956 |      468 |     0.0528464 | 0.073171  | 0.126489    |
| Train      | rejection_minutes |    545 |  10         |      468 |    10         | 0.0482475 | 0.578423    |
| Train      | relvol            |    545 |   0.674741  |      468 |     0.89978   | 0.268223  | 1.93127e-16 |
| Train      | reentry_end       |    545 | 699         |      468 |   689         | 0.0672508 | 0.193149    |
| Validation | excursion_ib      |    271 |   0.191651  |      257 |     0.235294  | 0.143753  | 0.00744274  |
| Validation | outside_5m        |    271 |   3         |      257 |     3         | 0.092897  | 0.188405    |
| Validation | reentry_depth_ib  |    271 |   0.0509491 |      257 |     0.0565371 | 0.0661191 | 0.579137    |
| Validation | rejection_minutes |    271 |   5         |      257 |    10         | 0.0916335 | 0.200512    |
| Validation | relvol            |    271 |   0.71716   |      257 |     0.824045  | 0.192715  | 8.93072e-05 |
| Validation | reentry_end       |    271 | 689         |      257 |   689         | 0.0815685 | 0.31971     |

## Directional continuous correlations

| period     | direction             | feature           |   n |   spearman_r |           p |
|:-----------|:----------------------|:------------------|----:|-------------:|------------:|
| Inner      | downside_failure_long | excursion_ib      | 215 |  0.10434     | 0.127217    |
| Inner      | downside_failure_long | outside_5m        | 215 |  0.156515    | 0.0216902   |
| Inner      | downside_failure_long | reentry_depth_ib  | 215 |  0.0383641   | 0.575852    |
| Inner      | downside_failure_long | rejection_minutes | 215 |  0.191871    | 0.00475373  |
| Inner      | downside_failure_long | relvol            | 215 |  0.108551    | 0.112493    |
| Inner      | downside_failure_long | reentry_end       | 215 |  0.054239    | 0.4288      |
| Inner      | upside_failure_short  | excursion_ib      | 283 |  0.0831914   | 0.162798    |
| Inner      | upside_failure_short  | outside_5m        | 283 |  0.0958144   | 0.107744    |
| Inner      | upside_failure_short  | reentry_depth_ib  | 283 |  0.0231937   | 0.697643    |
| Inner      | upside_failure_short  | rejection_minutes | 283 |  0.0868749   | 0.144909    |
| Inner      | upside_failure_short  | relvol            | 283 |  0.00429545  | 0.942649    |
| Inner      | upside_failure_short  | reentry_end       | 283 |  0.0299867   | 0.615432    |
| OOS        | downside_failure_long | excursion_ib      | 116 |  0.0400185   | 0.669733    |
| OOS        | downside_failure_long | outside_5m        | 116 |  0.089312    | 0.340383    |
| OOS        | downside_failure_long | reentry_depth_ib  | 116 |  0.00753088  | 0.936052    |
| OOS        | downside_failure_long | rejection_minutes | 116 |  0.148608    | 0.111366    |
| OOS        | downside_failure_long | relvol            | 116 | -0.038204    | 0.683889    |
| OOS        | downside_failure_long | reentry_end       | 116 |  0.0904364   | 0.334313    |
| OOS        | upside_failure_short  | excursion_ib      | 163 |  0.00804972  | 0.91877     |
| OOS        | upside_failure_short  | outside_5m        | 163 |  0.0467603   | 0.553365    |
| OOS        | upside_failure_short  | reentry_depth_ib  | 163 | -0.000326977 | 0.996695    |
| OOS        | upside_failure_short  | rejection_minutes | 163 | -0.00635186  | 0.935862    |
| OOS        | upside_failure_short  | relvol            | 163 |  0.0449454   | 0.568883    |
| OOS        | upside_failure_short  | reentry_end       | 163 | -0.0717346   | 0.362838    |
| Train      | downside_failure_long | excursion_ib      | 468 |  0.161844    | 0.000439655 |
| Train      | downside_failure_long | outside_5m        | 468 |  0.159065    | 0.000552501 |
| Train      | downside_failure_long | reentry_depth_ib  | 468 |  0.0239808   | 0.604827    |
| Train      | downside_failure_long | rejection_minutes | 468 |  0.157967    | 0.000604075 |
| Train      | downside_failure_long | relvol            | 468 |  0.0955179   | 0.0388694   |
| Train      | downside_failure_long | reentry_end       | 468 |  0.103724    | 0.0248355   |
| Train      | upside_failure_short  | excursion_ib      | 545 |  0.188454    | 9.46045e-06 |
| Train      | upside_failure_short  | outside_5m        | 545 |  0.165424    | 0.000104561 |
| Train      | upside_failure_short  | reentry_depth_ib  | 545 | -0.00518586  | 0.903859    |
| Train      | upside_failure_short  | rejection_minutes | 545 |  0.158116    | 0.000210464 |
| Train      | upside_failure_short  | relvol            | 545 |  0.0852636   | 0.0466401   |
| Train      | upside_failure_short  | reentry_end       | 545 |  0.0684175   | 0.110617    |
| Validation | downside_failure_long | excursion_ib      | 257 |  0.0626817   | 0.316851    |
| Validation | downside_failure_long | outside_5m        | 257 |  0.0481628   | 0.442018    |
| Validation | downside_failure_long | reentry_depth_ib  | 257 | -0.174028    | 0.00514738  |
| Validation | downside_failure_long | rejection_minutes | 257 |  0.0114686   | 0.854825    |
| Validation | downside_failure_long | relvol            | 257 | -0.166663    | 0.00741664  |
| Validation | downside_failure_long | reentry_end       | 257 |  0.0128916   | 0.837049    |
| Validation | upside_failure_short  | excursion_ib      | 271 |  0.120051    | 0.0483477   |
| Validation | upside_failure_short  | outside_5m        | 271 |  0.172653    | 0.00436462  |
| Validation | upside_failure_short  | reentry_depth_ib  | 271 | -0.0900096   | 0.139435    |
| Validation | upside_failure_short  | rejection_minutes | 271 |  0.168178    | 0.00551066  |
| Validation | upside_failure_short  | relvol            | 271 | -0.0943148   | 0.121407    |
| Validation | upside_failure_short  | reentry_end       | 271 |  0.151469    | 0.0125463   |