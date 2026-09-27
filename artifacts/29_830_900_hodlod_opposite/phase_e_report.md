# Strategy 29 — Phase E parameter comparison

Survivors Val+OOS: **0** / class `C`

## By entry family (median E_net, n≥20 cells)

| family     | split      |   median_E |    mean_E |   n_cells |    pct_pos |
|:-----------|:-----------|-----------:|----------:|----------:|-----------:|
| at_open    | Discovery  |  -1.38328  | -1.37486  |       120 | 0          |
| at_open    | OOS        |  -3.30769  | -3.40065  |       120 | 0.00833333 |
| at_open    | Validation |  -0.833763 | -0.730479 |       120 | 0.208333   |
| break      | Discovery  |  -0.466176 | -0.418775 |       360 | 0.25       |
| break      | OOS        |  -3.26257  | -2.46283  |       360 | 0.166667   |
| break      | Validation |  -2.58947  | -2.76363  |       360 | 0          |
| impulse_pb | Discovery  |  -0.373476 | -0.434228 |       720 | 0.269444   |
| impulse_pb | OOS        |  -2.74599  | -2.48134  |       720 | 0.116667   |
| impulse_pb | Validation |  -3.17511  | -2.84183  |       720 | 0.00555556 |
| reclaim    | Discovery  |   0.147188 |  0.200312 |       360 | 0.519444   |
| reclaim    | OOS        |  -3.62436  | -3.67328  |       360 | 0.0416667  |
| reclaim    | Validation |  -1.36008  | -1.24716  |       360 | 0.102778   |

## By risk style

| stop_mode   | tgt_mode   | split      |   median_E |   pct_pos |   n_cells |
|:------------|:-----------|:-----------|-----------:|----------:|----------:|
| fixed       | fixed      | Discovery  |  -0.504954 | 0.301282  |       780 |
| fixed       | fixed      | OOS        |  -3.18156  | 0.0461538 |       780 |
| fixed       | fixed      | Validation |  -2.13981  | 0.0192308 |       780 |
| fixed       | rr         | Discovery  |  -0.403703 | 0.318376  |       468 |
| fixed       | rr         | OOS        |  -3.24599  | 0.117521  |       468 |
| fixed       | rr         | Validation |  -2.23628  | 0.0106838 |       468 |
| structural  | fixed      | Discovery  |  -0.260945 | 0.307692  |       195 |
| structural  | fixed      | OOS        |  -2.28143  | 0.153846  |       195 |
| structural  | fixed      | Validation |  -2.55637  | 0.123077  |       195 |
| structural  | rr         | Discovery  |  -0.610494 | 0.230769  |       117 |
| structural  | rr         | OOS        |  -1.77703  | 0.333333  |       117 |
| structural  | rr         | Validation |  -3.36553  | 0.188034  |       117 |

## By hold

|   hold_h | split      |   median_E |   pct_pos |
|---------:|:-----------|-----------:|----------:|
|       15 | Discovery  |  -0.628809 | 0.253846  |
|       15 | OOS        |  -3.05408  | 0.101923  |
|       15 | Validation |  -2.23661  | 0.0615385 |
|       30 | Discovery  |  -0.458944 | 0.265385  |
|       30 | OOS        |  -3.08462  | 0.103846  |
|       30 | Validation |  -2.28924  | 0.0307692 |
|       60 | Discovery  |  -0.291259 | 0.386538  |
|       60 | OOS        |  -3.11538  | 0.101923  |
|       60 | Validation |  -2.2991   | 0.0346154 |

## Survivors

_none_

## Best by min(Val,OOS) E_net

| entry         | stop_mode   |   stop_pts | tgt_mode   |   tgt_pts |    rr |   hold_h |   E_net_disc |   E_net_val |   E_net_oos |   n_val |   n_oos |
|:--------------|:------------|-----------:|:-----------|----------:|------:|---------:|-------------:|------------:|------------:|--------:|--------:|
| at_open_wstop | structural  |        nan | rr         |       nan |   2   |       60 |   -1.19425   |   3.84691   |   0.659856  |     485 |     208 |
| imp20_pb5     | fixed       |         25 | fixed      |        40 | nan   |       60 |    0.192598  |   0.119949  |   0.50838   |     396 |     179 |
| imp20_pb10    | fixed       |         25 | fixed      |        40 | nan   |       60 |    0.129573  |   0.119949  |   0.50838   |     396 |     179 |
| imp20_pb5     | fixed       |         25 | fixed      |        40 | nan   |       30 |   -0.608006  |  -0.111111  |   0.368715  |     396 |     179 |
| imp20_pb10    | fixed       |         25 | fixed      |        40 | nan   |       30 |   -0.483994  |  -0.111111  |   0.368715  |     396 |     179 |
| reclaim_dip10 | fixed       |         25 | rr         |       nan |   2   |       30 |   -0.557491  |  -0.192971  |   0.612903  |     377 |     155 |
| at_open_wstop | structural  |        nan | rr         |       nan |   2   |       30 |   -0.175087  |   2.18505   |  -0.272837  |     485 |     208 |
| reclaim_dip10 | fixed       |         25 | rr         |       nan |   2   |       15 |    0.336237  |  -0.301724  |   0.332258  |     377 |     155 |
| reclaim_dip15 | fixed       |         25 | rr         |       nan |   2   |       60 |    0.196934  |   1.08407   |  -0.328859  |     339 |     149 |
| reclaim_dip15 | fixed       |         25 | rr         |       nan |   2   |       30 |    1.06958   |   1.0236    |  -0.328859  |     339 |     149 |
| imp20_pb10    | fixed       |         25 | rr         |       nan |   1.5 |       60 |   -0.28811   |  -0.378788  |   0.187151  |     396 |     179 |
| imp20_pb5     | fixed       |         25 | rr         |       nan |   1.5 |       60 |   -0.0279456 |  -0.378788  |   0.187151  |     396 |     179 |
| reclaim_dip10 | structural  |        nan | fixed      |        40 | nan   |       60 |    1.41725   |  -0.0749337 |  -0.437097  |     377 |     155 |
| at_open_wstop | structural  |        nan | rr         |       nan |   1   |       60 |   -0.874564  |   2.8866    |  -0.46274   |     485 |     208 |
| reclaim_dip10 | fixed       |         25 | rr         |       nan |   2   |       60 |   -1.33014   |  -0.465517  |   0.612903  |     377 |     155 |
| imp20_pb5     | fixed       |         25 | fixed      |        40 | nan   |       15 |   -2.00529   |  -0.529672  |   0.0782123 |     396 |     179 |
| imp20_pb10    | fixed       |         25 | fixed      |        40 | nan   |       15 |   -2.19665   |  -0.529672  |   0.0782123 |     396 |     179 |
| imp20_pb10    | fixed       |         25 | rr         |       nan |   1.5 |       30 |   -0.714939  |  -0.565657  |   0.075419  |     396 |     179 |
| imp20_pb5     | fixed       |         25 | rr         |       nan |   1.5 |       30 |   -0.663142  |  -0.565657  |   0.075419  |     396 |     179 |
| reclaim_dip5  | fixed       |         25 | rr         |       nan |   2   |       60 |   -2.05108   |  -0.586493  |   0.183432  |     422 |     169 |