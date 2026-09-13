# Phase 6 — continuation matrix

Predeclared filters: all, low/high signal-bar relative volume (Train tertiles), early signal (by 11:30), and high-volume early. Each is crossed with the Phase 2 stop/target grid. Selection uses Train and Inner only.

## Survivors

| stop_rule      |   target_r | filter        |    Inner |      OOS |      Train |   Validation |   n_Inner |   n_OOS |   n_Train |   n_Validation | selection                                          |
|:---------------|-----------:|:--------------|---------:|---------:|-----------:|-------------:|----------:|--------:|----------:|---------------:|:---------------------------------------------------|
| 0.25x_ib_width |       2    | highvol_early |  1.43975 |  3.79529 |  0.161014  |      7.06898 |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       1    | early         |  2.19397 | -1.61419 | -0.598969  |      5.59652 |       464 |     266 |       970 |            496 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       1    | high_volume   |  2.88269 |  5.97059 | -0.558212  |      9.24601 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       1    | highvol_early |  4.76497 | 12.8986  | -0.334302  |     11.4268  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       1.5  | high_volume   |  5.21571 |  9.42794 | -0.567438  |      7.78757 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       1.5  | highvol_early |  7.22942 | 17.2129  | -0.0197028 |      9.46494 |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       2    | early         |  4.38605 | -4.5437  | -0.198711  |      6.01815 |       464 |     266 |       970 |            496 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       2    | high_volume   |  6.81474 |  9.82647 | -0.130717  |      8.78923 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 0.50x_ib_width |       2    | highvol_early | 10.8263  | 17.7844  |  0.606266  |     10.0991  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       0.75 | high_volume   |  4.22099 | 14.7048  | -0.600117  |      9.42952 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       0.75 | highvol_early |  4.72661 | 25.6135  | -0.787306  |     12.969   |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       1    | high_volume   |  6.84519 | 16.0441  | -0.346674  |      7.57447 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       1    | highvol_early |  7.54266 | 28.0797  | -0.177164  |     10.1204  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       1.5  | early         |  5.14278 | -2.48872 | -0.436823  |      5.69764 |       464 |     266 |       970 |            496 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       1.5  | high_volume   |  6.99022 | 16.2412  |  0.231744  |      8.77111 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       1.5  | highvol_early |  9.98859 | 28.0371  |  0.590924  |     10.5861  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       2    | early         |  4.87029 | -2.67058 | -0.168686  |      9.02684 |       464 |     266 |       970 |            496 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       2    | high_volume   |  7.42885 | 11.6441  |  0.456471  |     11.8763  |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 0.75x_ib_width |       2    | highvol_early | 10.8118  | 21.2763  |  0.793766  |     13.4813  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       0.75 | high_volume   |  7.55449 | 11.7904  | -0.39514   |      8.56383 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       0.75 | highvol_early |  7.97829 | 24.8822  | -0.243863  |     10.3857  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       1    | high_volume   |  9.36026 |  6.55    |  0.307173  |      9.76463 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       1    | highvol_early | 12.1796  | 18.5072  |  0.641473  |     11.1128  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       1.5  | early         |  4.40221 |  0.43468 | -0.454253  |     10.4808  |       464 |     266 |       970 |            496 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       1.5  | high_volume   |  7.94167 |  6.39706 |  0.382017  |     13.502   |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       1.5  | highvol_early | 11.0195  | 16.8551  |  0.705103  |     14.0701  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       2    | high_volume   |  7.01026 |  7.94118 |  0.0452183 |     10.7766  |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| 1.00x_ib_width |       2    | highvol_early |  9.80689 | 19.6232  |  0.408915  |     11.6037  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       0.75 | high_volume   |  8.41026 | 15.2537  | -0.310681  |      8.45379 |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       0.75 | highvol_early |  8.69611 | 22.538   | -0.0306848 |      9.75419 |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       1    | early         |  3.79526 |  3.99154 | -0.918814  |      8.14415 |       464 |     266 |       970 |            496 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       1    | high_volume   |  7.01154 | 17.9941  | -0.0265073 |     12.0851  |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       1    | highvol_early |  9.27246 | 25.8514  |  0.332687  |     13.1006  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       1.5  | high_volume   |  6.47692 | 14.6515  | -0.306653  |     10.8384  |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       1.5  | highvol_early |  8.66542 | 22.3931  |  0.0151809 |     12.2454  |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       2    | high_volume   |  5.4141  | 10.3206  | -0.735447  |     11.004   |       195 |      85 |       481 |            188 | beats same geometry unfiltered in Train+Inner only |
| opposite_ib    |       2    | highvol_early |  7.44311 | 17.058   | -0.449612  |     12.157   |       167 |      69 |       387 |            164 | beats same geometry unfiltered in Train+Inner only |

## Full matrix

| stop_rule      |   target_r | filter        |      Inner |        OOS |      Train |   Validation |   n_Inner |   n_OOS |   n_Train |   n_Validation |
|:---------------|-----------:|:--------------|-----------:|-----------:|-----------:|-------------:|----------:|--------:|----------:|---------------:|
| 0.25x_ib_width |       0.75 | all           | -0.603674  | -2.35731   | -0.639226  |    0.72844   |       677 |     370 |      1441 |            695 |
| 0.25x_ib_width |       0.75 | early         | -0.0886988 | -1.55257   | -0.71838   |    0.310452  |       464 |     266 |       970 |            496 |
| 0.25x_ib_width |       0.75 | high_volume   |  0.776442  |  3.74908   | -0.913039  |    3.72847   |       195 |      85 |       481 |            188 |
| 0.25x_ib_width |       0.75 | highvol_early |  1.7907    |  6.39493   | -0.917595  |    4.73666   |       167 |      69 |       387 |            164 |
| 0.25x_ib_width |       0.75 | low_volume    | -1.01183   | -6.53826   | -0.720082  |   -0.0168688 |       210 |     136 |       481 |            201 |
| 0.25x_ib_width |       1    | all           |  0.315916  | -0.232939  | -0.615415  |    1.39793   |       677 |     370 |      1441 |            695 |
| 0.25x_ib_width |       1    | early         |  0.801724  | -0.0265508 | -0.665851  |    1.61757   |       464 |     266 |       970 |            496 |
| 0.25x_ib_width |       1    | high_volume   |  1.04231   |  1.73971   | -0.735317  |    5.04056   |       195 |      85 |       481 |            188 |
| 0.25x_ib_width |       1    | highvol_early |  1.93862   |  3.63406   | -0.744348  |    6.43255   |       167 |      69 |       387 |            164 |
| 0.25x_ib_width |       1    | low_volume    | -0.728571  | -3.91314   | -1.01468   |   -0.92444   |       210 |     136 |       481 |            201 |
| 0.25x_ib_width |       1.5  | all           |  1.58189   |  1.79814   | -0.337418  |    2.52617   |       677 |     370 |      1441 |            695 |
| 0.25x_ib_width |       1.5  | early         |  1.55422   |  0.76445   | -0.473067  |    2.85515   |       464 |     266 |       970 |            496 |
| 0.25x_ib_width |       1.5  | high_volume   |  2.49263   |  3.56066   | -0.408199  |    4.47407   |       195 |      85 |       481 |            188 |
| 0.25x_ib_width |       1.5  | highvol_early |  3.71707   |  4.08288   | -0.383559  |    5.90053   |       167 |      69 |       387 |            164 |
| 0.25x_ib_width |       1.5  | low_volume    |  2.27604   | -0.286075  | -1.01085   |    0.591729  |       210 |     136 |       481 |            201 |
| 0.25x_ib_width |       2    | all           |  1.32099   |  2.81655   | -0.340649  |    3.16511   |       677 |     370 |      1441 |            695 |
| 0.25x_ib_width |       2    | early         |  0.290275  |  3.57284   | -0.345103  |    3.67477   |       464 |     266 |       970 |            496 |
| 0.25x_ib_width |       2    | high_volume   |  0.667308  |  2.90294   |  0.119932  |    5.26762   |       195 |      85 |       481 |            188 |
| 0.25x_ib_width |       2    | highvol_early |  1.43975   |  3.79529   |  0.161014  |    7.06898   |       167 |      69 |       387 |            164 |
| 0.25x_ib_width |       2    | low_volume    |  3.09821   |  0.69807   | -1.09005   |    1.15516   |       210 |     136 |       481 |            201 |
| 0.50x_ib_width |       0.75 | all           |  3.10931   | -3.0152    | -0.620337  |    3.79933   |       677 |     370 |      1441 |            695 |
| 0.50x_ib_width |       0.75 | early         |  3.51778   | -5.97357   | -0.698035  |    4.08191   |       464 |     266 |       970 |            496 |
| 0.50x_ib_width |       0.75 | high_volume   |  3.8726    |  2.075     | -1.03567   |    6.98521   |       195 |      85 |       481 |            188 |
| 0.50x_ib_width |       0.75 | highvol_early |  5.83009   |  6.75906   | -0.843427  |    8.17454   |       167 |      69 |       387 |            164 |
| 0.50x_ib_width |       0.75 | low_volume    |  3.69762   | -5.38097   | -1.76442   |   -0.855566  |       210 |     136 |       481 |            201 |
| 0.50x_ib_width |       1    | all           |  2.18408   | -0.655743  | -0.819917  |    4.70701   |       677 |     370 |      1441 |            695 |
| 0.50x_ib_width |       1    | early         |  2.19397   | -1.61419   | -0.598969  |    5.59652   |       464 |     266 |       970 |            496 |
| 0.50x_ib_width |       1    | high_volume   |  2.88269   |  5.97059   | -0.558212  |    9.24601   |       195 |      85 |       481 |            188 |
| 0.50x_ib_width |       1    | highvol_early |  4.76497   | 12.8986    | -0.334302  |   11.4268    |       167 |      69 |       387 |            164 |
| 0.50x_ib_width |       1    | low_volume    |  3.14345   | -3.18382   | -1.93139   |    1.13371   |       210 |     136 |       481 |            201 |
| 0.50x_ib_width |       1.5  | all           |  3.51099   | -3.59307   | -0.840605  |    4.02545   |       677 |     370 |      1441 |            695 |
| 0.50x_ib_width |       1.5  | early         |  3.25175   | -4.73167   | -0.551289  |    6.03415   |       464 |     266 |       970 |            496 |
| 0.50x_ib_width |       1.5  | high_volume   |  5.21571   |  9.42794   | -0.567438  |    7.78757   |       195 |      85 |       481 |            188 |
| 0.50x_ib_width |       1.5  | highvol_early |  7.22942   | 17.2129    | -0.0197028 |    9.46494   |       167 |      69 |       387 |            164 |
| 0.50x_ib_width |       1.5  | low_volume    |  7.63185   | -6.81158   | -1.50065   |    2.01897   |       210 |     136 |       481 |            201 |
| 0.50x_ib_width |       2    | all           |  3.65657   | -3.50203   | -0.570524  |    3.70216   |       677 |     370 |      1441 |            695 |
| 0.50x_ib_width |       2    | early         |  4.38605   | -4.5437    | -0.198711  |    6.01815   |       464 |     266 |       970 |            496 |
| 0.50x_ib_width |       2    | high_volume   |  6.81474   |  9.82647   | -0.130717  |    8.78923   |       195 |      85 |       481 |            188 |
| 0.50x_ib_width |       2    | highvol_early | 10.8263    | 17.7844    |  0.606266  |   10.0991    |       167 |      69 |       387 |            164 |
| 0.50x_ib_width |       2    | low_volume    |  7.01071   | -3.92463   | -1.43373   |    2.51119   |       210 |     136 |       481 |            201 |
| 0.75x_ib_width |       0.75 | all           |  2.69071   |  3.88066   | -1.02776   |    3.2875    |       677 |     370 |      1441 |            695 |
| 0.75x_ib_width |       0.75 | early         |  2.40369   |  2.07924   | -1.13988   |    4.59479   |       464 |     266 |       970 |            496 |
| 0.75x_ib_width |       0.75 | high_volume   |  4.22099   | 14.7048    | -0.600117  |    9.42952   |       195 |      85 |       481 |            188 |
| 0.75x_ib_width |       0.75 | highvol_early |  4.72661   | 25.6135    | -0.787306  |   12.969     |       167 |      69 |       387 |            164 |
| 0.75x_ib_width |       0.75 | low_volume    |  8.96793   |  3.37868   | -1.94241   |   -0.804882  |       210 |     136 |       481 |            201 |
| 0.75x_ib_width |       1    | all           |  4.10303   |  1.56199   | -0.933987  |    3.09191   |       677 |     370 |      1441 |            695 |
| 0.75x_ib_width |       1    | early         |  4.00418   | -0.620301  | -0.830992  |    5.18271   |       464 |     266 |       970 |            496 |
| 0.75x_ib_width |       1    | high_volume   |  6.84519   | 16.0441    | -0.346674  |    7.57447   |       195 |      85 |       481 |            188 |
| 0.75x_ib_width |       1    | highvol_early |  7.54266   | 28.0797    | -0.177164  |   10.1204    |       167 |      69 |       387 |            164 |
| 0.75x_ib_width |       1    | low_volume    | 12.1887    |  1.36765   | -1.50624   |    0.0668532 |       210 |     136 |       481 |            201 |
| 0.75x_ib_width |       1.5  | all           |  4.1623    |  0.693074  | -0.662799  |    2.84501   |       677 |     370 |      1441 |            695 |
| 0.75x_ib_width |       1.5  | early         |  5.14278   | -2.48872   | -0.436823  |    5.69764   |       464 |     266 |       970 |            496 |
| 0.75x_ib_width |       1.5  | high_volume   |  6.99022   | 16.2412    |  0.231744  |    8.77111   |       195 |      85 |       481 |            188 |
| 0.75x_ib_width |       1.5  | highvol_early |  9.98859   | 28.0371    |  0.590924  |   10.5861    |       167 |      69 |       387 |            164 |
| 0.75x_ib_width |       1.5  | low_volume    | 12.3783    |  5.3534    | -1.55405   |   -0.538246  |       210 |     136 |       481 |            201 |
| 0.75x_ib_width |       2    | all           |  4.2885    |  0.431588  | -0.472328  |    5.83282   |       677 |     370 |      1441 |            695 |
| 0.75x_ib_width |       2    | early         |  4.87029   | -2.67058   | -0.168686  |    9.02684   |       464 |     266 |       970 |            496 |
| 0.75x_ib_width |       2    | high_volume   |  7.42885   | 11.6441    |  0.456471  |   11.8763    |       195 |      85 |       481 |            188 |
| 0.75x_ib_width |       2    | highvol_early | 10.8118    | 21.2763    |  0.793766  |   13.4813    |       167 |      69 |       387 |            164 |
| 0.75x_ib_width |       2    | low_volume    | 11.9524    |  4.01562   | -1.4987    |    1.52767   |       210 |     136 |       481 |            201 |
| 1.00x_ib_width |       0.75 | all           |  4.09647   |  3.29645   | -1.00586   |    3.64901   |       677 |     370 |      1441 |            695 |
| 1.00x_ib_width |       0.75 | early         |  3.36773   |  2.44008   | -1.05232   |    6.24168   |       464 |     266 |       970 |            496 |
| 1.00x_ib_width |       0.75 | high_volume   |  7.55449   | 11.7904    | -0.39514   |    8.56383   |       195 |      85 |       481 |            188 |
| 1.00x_ib_width |       0.75 | highvol_early |  7.97829   | 24.8822    | -0.243863  |   10.3857    |       167 |      69 |       387 |            164 |
| 1.00x_ib_width |       0.75 | low_volume    | 11.3176    |  3.66131   | -1.61136   |    0.775187  |       210 |     136 |       481 |            201 |
| 1.00x_ib_width |       1    | all           |  4.6743    |  2.25811   | -0.715475  |    3.04353   |       677 |     370 |      1441 |            695 |
| 1.00x_ib_width |       1    | early         |  5.22144   |  0.50282   | -0.754639  |    6.62752   |       464 |     266 |       970 |            496 |
| 1.00x_ib_width |       1    | high_volume   |  9.36026   |  6.55      |  0.307173  |    9.76463   |       195 |      85 |       481 |            188 |
| 1.00x_ib_width |       1    | highvol_early | 12.1796    | 18.5072    |  0.641473  |   11.1128    |       167 |      69 |       387 |            164 |
| 1.00x_ib_width |       1    | low_volume    | 10.4786    |  7.55882   | -1.48181   |   -0.15796   |       210 |     136 |       481 |            201 |
| 1.00x_ib_width |       1.5  | all           |  4.34915   |  2.19831   | -0.567401  |    6.70953   |       677 |     370 |      1441 |            695 |
| 1.00x_ib_width |       1.5  | early         |  4.40221   |  0.43468   | -0.454253  |   10.4808    |       464 |     266 |       970 |            496 |
| 1.00x_ib_width |       1.5  | high_volume   |  7.94167   |  6.39706   |  0.382017  |   13.502     |       195 |      85 |       481 |            188 |
| 1.00x_ib_width |       1.5  | highvol_early | 11.0195    | 16.8551    |  0.705103  |   14.0701    |       167 |      69 |       387 |            164 |
| 1.00x_ib_width |       1.5  | low_volume    | 11.0762    |  6.88695   | -1.52365   |    2.36567   |       210 |     136 |       481 |            201 |
| 1.00x_ib_width |       2    | all           |  4.28287   |  3.41486   | -0.897988  |    5.96259   |       677 |     370 |      1441 |            695 |
| 1.00x_ib_width |       2    | early         |  3.89547   |  1.68891   | -0.88634   |    9.66986   |       464 |     266 |       970 |            496 |
| 1.00x_ib_width |       2    | high_volume   |  7.01026   |  7.94118   |  0.0452183 |   10.7766    |       195 |      85 |       481 |            188 |
| 1.00x_ib_width |       2    | highvol_early |  9.80689   | 19.6232    |  0.408915  |   11.6037    |       167 |      69 |       387 |            164 |
| 1.00x_ib_width |       2    | low_volume    | 11.2774    |  5.83272   | -1.54782   |    1.82338   |       210 |     136 |       481 |            201 |
| opposite_ib    |       0.75 | all           |  3.80475   |  4.69324   | -0.955803  |    4.4491    |       677 |     370 |      1441 |            695 |
| opposite_ib    |       0.75 | early         |  3.09281   |  3.15602   | -0.96134   |    7.01109   |       464 |     266 |       970 |            496 |
| opposite_ib    |       0.75 | high_volume   |  8.41026   | 15.2537    | -0.310681  |    8.45379   |       195 |      85 |       481 |            188 |
| opposite_ib    |       0.75 | highvol_early |  8.69611   | 22.538     | -0.0306848 |    9.75419   |       167 |      69 |       387 |            164 |
| opposite_ib    |       0.75 | low_volume    | 11.8149    |  3.07215   | -1.55821   |    1.55348   |       210 |     136 |       481 |            201 |
| opposite_ib    |       1    | all           |  3.53582   |  6.3       | -0.991672  |    4.53094   |       677 |     370 |      1441 |            695 |
| opposite_ib    |       1    | early         |  3.79526   |  3.99154   | -0.918814  |    8.14415   |       464 |     266 |       970 |            496 |
| opposite_ib    |       1    | high_volume   |  7.01154   | 17.9941    | -0.0265073 |   12.0851    |       195 |      85 |       481 |            188 |
| opposite_ib    |       1    | highvol_early |  9.27246   | 25.8514    |  0.332687  |   13.1006    |       167 |      69 |       387 |            164 |
| opposite_ib    |       1    | low_volume    | 10.8333    |  6.84007   | -1.57848   |   -0.253731  |       210 |     136 |       481 |            201 |
| opposite_ib    |       1.5  | all           |  3.4387    |  5.89088   | -1.04988   |    6.33903   |       677 |     370 |      1441 |            695 |
| opposite_ib    |       1.5  | early         |  2.87527   |  3.91494   | -1.03892   |   10.1074    |       464 |     266 |       970 |            496 |
| opposite_ib    |       1.5  | high_volume   |  6.47692   | 14.6515    | -0.306653  |   10.8384    |       195 |      85 |       481 |            188 |
| opposite_ib    |       1.5  | highvol_early |  8.66542   | 22.3931    |  0.0151809 |   12.2454    |       167 |      69 |       387 |            164 |
| opposite_ib    |       1.5  | low_volume    | 10.8458    |  6.15441   | -1.71778   |    2.35448   |       210 |     136 |       481 |            201 |
| opposite_ib    |       2    | all           |  3.35192   |  4.42297   | -1.26475   |    6.73345   |       677 |     370 |      1441 |            695 |
| opposite_ib    |       2    | early         |  2.45043   |  1.06955   | -1.3317    |   10.6618    |       464 |     266 |       970 |            496 |
| opposite_ib    |       2    | high_volume   |  5.4141    | 10.3206    | -0.735447  |   11.004     |       195 |      85 |       481 |            188 |
| opposite_ib    |       2    | highvol_early |  7.44311   | 17.058     | -0.449612  |   12.157     |       167 |      69 |       387 |            164 |
| opposite_ib    |       2    | low_volume    | 11.0643    |  0.415441  | -1.6159    |    2.34453   |       210 |     136 |       481 |            201 |