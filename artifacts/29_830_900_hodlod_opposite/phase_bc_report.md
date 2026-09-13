# Strategy 29 — Phase B/C scalp

Verdict: `C` — ORACLE_ONLY_NOT_TRADEABLE
Survivors Val+OOS: total=6 oracle=6 causal=0

## Headline oracle dip=10 target=25

| split      |   n |   trig_rate |      win |   E_net |   target_hit |   stop_hit |
|:-----------|----:|------------:|---------:|--------:|-------------:|-----------:|
| Discovery  | 109 |    0.196751 | 0.697248 | 7.37615 |     0.550459 |   0.247706 |
| OOS        |  72 |    0.666667 | 0.666667 | 2.94097 |     0.666667 |   0.305556 |
| Validation | 152 |    0.649573 | 0.684211 | 7.38322 |     0.677632 |   0.276316 |

## Headline fade_raid dip=10 target=25

| split      |   n |   trig_rate |      win |    E_net |   target_hit |   stop_hit |
|:-----------|----:|------------:|---------:|---------:|-------------:|-----------:|
| Discovery  | 205 |    0.312024 | 0.560976 |  1.79146 |     0.385366 |   0.312195 |
| OOS        |  89 |    0.735537 | 0.651685 | -4.06742 |     0.640449 |   0.303371 |
| Validation | 242 |    0.724551 | 0.549587 | -1       |     0.545455 |   0.409091 |

## Survivors

| setup   |   dip | target_mode   |   target |   E_Discovery |   E_Validation |   E_OOS |   n_Validation |   n_OOS |
|:--------|------:|:--------------|---------:|--------------:|---------------:|--------:|---------------:|--------:|
| oracle  |     5 | fixed         |       20 |       5.04274 |        6.78954 | 3.43072 |            196 |      83 |
| oracle  |     5 | fixed         |       25 |       6.34615 |        8.41071 | 3.30723 |            196 |      83 |
| oracle  |     5 | fixed         |       30 |       6.91132 |       10.3801  | 2.53614 |            196 |      83 |
| oracle  |    10 | fixed         |       20 |       6.20183 |        5.30099 | 4.07639 |            152 |      72 |
| oracle  |    10 | fixed         |       25 |       7.37615 |        7.38322 | 2.94097 |            152 |      72 |
| oracle  |    10 | fixed         |       30 |       7.93578 |        9.80099 | 1       |            152 |      72 |

## Full grid (top by OOS E_net)

| setup           |   dip | target_mode   |   target | split   |   n |   win |   E_net |   median |   target_hit |   stop_hit |   time_exit |   n_days |   n_trig |   trig_rate |
|:----------------|------:|:--------------|---------:|:--------|----:|------:|--------:|---------:|-------------:|-----------:|------------:|---------:|---------:|------------:|
| fade_last_touch |     5 | opposite      |   242.25 | OOS     |   1 |     1 |  169.5  |   169.5  |            0 |          0 |           1 |        1 |        1 |           1 |
| fade_last_touch |    10 | opposite      |   242.25 | OOS     |   1 |     1 |  169.5  |   169.5  |            0 |          0 |           1 |        1 |        1 |           1 |
| fade_raid       |     5 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |     5 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |    10 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |     5 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_raid       |    10 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| oracle          |    10 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| oracle          |     5 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |    10 | opposite      |   145.75 | OOS     |   1 |     1 |  144.75 |   144.75 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |    10 | opposite      |   138    | OOS     |   1 |     1 |  137    |   137    |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |     5 | opposite      |   138    | OOS     |   1 |     1 |  137    |   137    |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_raid       |     5 | opposite      |   138    | OOS     |   1 |     1 |  137    |   137    |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_raid       |    10 | opposite      |   138    | OOS     |   1 |     1 |  137    |   137    |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |     5 | opposite      |   138    | OOS     |   1 |     1 |  137    |   137    |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |    10 | opposite      |   138    | OOS     |   1 |     1 |  137    |   137    |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |    10 | opposite      |   122.25 | OOS     |   1 |     1 |  121.25 |   121.25 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |     5 | opposite      |   122.25 | OOS     |   1 |     1 |  121.25 |   121.25 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |     5 | opposite      |   116.25 | OOS     |   1 |     1 |  115.25 |   115.25 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |     5 | opposite      |   116.25 | OOS     |   1 |     1 |  115.25 |   115.25 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |    10 | opposite      |   116.25 | OOS     |   1 |     1 |  115.25 |   115.25 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_extent     |    10 | opposite      |   116.25 | OOS     |   1 |     1 |  115.25 |   115.25 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |    10 | opposite      |   115.25 | OOS     |   2 |     1 |  114.25 |   114.25 |            1 |          0 |           0 |        2 |        2 |           1 |
| fade_extent     |     5 | opposite      |   115.25 | OOS     |   1 |     1 |  114.25 |   114.25 |            1 |          0 |           0 |        1 |        1 |           1 |
| fade_last_touch |     5 | opposite      |   115.25 | OOS     |   2 |     1 |  114.25 |   114.25 |            1 |          0 |           0 |        2 |        2 |           1 |