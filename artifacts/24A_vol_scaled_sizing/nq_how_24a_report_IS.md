# Hypothesis 24A — Vol-Scaled Sizing (IS only)

## Stage gate

**Val / OOS not scored in this artifact.** (Unlock separately.)

## Freeze

| Item | Value |
|------|-------|
| Vol lookback W | 30 |
| rv_ref (IS median) | 1.264130 |
| Size clips | [0.25, 4.0] |
| HIGH multiplier | 0.7 (non-HIGH 1.0) |
| Cost RT | 1.0 pt x |size| |
| Risk-trade rows (IS) | 9,508 |
| Panel rows (all clocks) | 54,245 |
| HIGH share (risk IS) | 34.0% |

## Direction audit

Primary book = **coin-flip**. Long/short audit under identical sizing.

## Primary book (coin-flip) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 9508 | 2551 | -1.896 | -2.249 | -10141.2 | 0 | 0 | 1.000 |
| `invvol` | 9508 | 2551 | -5.169 | -7.182 | -12053.2 | -3.273 [-3.599, -2.920] | -4.933 [-5.416, -4.411] | 1.206 |
| `invvol_high_aware` | 9508 | 2551 | -5.122 | -7.069 | -10969.4 | -3.226 [-3.572, -2.854] | -4.820 [-5.333, -4.284] | 1.101 |

## Audit book (always long) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 9508 | 2551 | -1.841 | -2.240 | -9381.5 | 0 | 0 | 1.000 |
| `invvol` | 9508 | 2551 | -4.996 | -6.895 | -11162.4 | -3.154 [-3.496, -2.831] | -4.656 [-5.180, -4.199] | 1.206 |
| `invvol_high_aware` | 9508 | 2551 | -4.929 | -6.708 | -10121.4 | -3.087 [-3.454, -2.754] | -4.468 [-5.024, -3.968] | 1.101 |

## Audit book (always short) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 9508 | 2551 | -1.940 | -2.596 | -10196.5 | 0 | 0 | 1.000 |
| `invvol` | 9508 | 2551 | -5.247 | -7.998 | -11897.0 | -3.307 [-3.691, -2.900] | -5.402 [-5.856, -4.904] | 1.206 |
| `invvol_high_aware` | 9508 | 2551 | -5.232 | -7.964 | -10925.7 | -3.292 [-3.704, -2.851] | -5.368 [-5.862, -4.845] | 1.101 |

## Multi-session (coin-flip, H=30) — Sharpe vs fixed

| Session | Policy | Sharpe | dSharpe vs fixed [90% CI] | n_tr |
|---------|--------|--------|---------------------------|------|
| ASIA | `fixed` | -2.227 | 0 | 2320 |
| ASIA | `invvol` | -4.805 | -2.578 [-3.090, -2.113] | 2320 |
| ASIA | `invvol_high_aware` | -4.705 | -2.479 [-3.015, -1.986] | 2320 |
| LONDON | `fixed` | -1.689 | 0 | 2413 |
| LONDON | `invvol` | -3.457 | -1.768 [-2.137, -1.390] | 2413 |
| LONDON | `invvol_high_aware` | -3.380 | -1.691 [-2.062, -1.298] | 2413 |
| NY_AM | `fixed` | -0.321 | 0 | 2415 |
| NY_AM | `invvol` | -0.689 | -0.368 [-0.579, -0.167] | 2415 |
| NY_AM | `invvol_high_aware` | -0.687 | -0.366 [-0.586, -0.145] | 2415 |
| NY_PM | `fixed` | -1.151 | 0 | 2360 |
| NY_PM | `invvol` | -2.351 | -1.200 [-1.559, -0.847] | 2360 |
| NY_PM | `invvol_high_aware` | -2.299 | -1.148 [-1.534, -0.759] | 2360 |

## Multi-horizon coin-flip (pooled sessions)

| H | Policy | Sharpe | Sortino | MaxDD | dSharpe vs fixed |
|---|--------|--------|---------|-------|------------------|
| 30 | `fixed` | -1.896 | -2.249 | -10141.2 | 0 |
| 30 | `invvol` | -5.169 | -7.182 | -12053.2 | -3.273 |
| 30 | `invvol_high_aware` | -5.122 | -7.069 | -10969.4 | -3.226 |
| 60 | `fixed` | -1.240 | -1.557 | -9320.5 | 0 |
| 60 | `invvol` | -3.319 | -4.927 | -10877.7 | -2.079 |
| 60 | `invvol_high_aware` | -3.234 | -4.772 | -9769.0 | -1.995 |

## MAE / MFE by regime (all clocks, coin-flip side, diagnostic)

| Regime | n | MAE mean | MAE p50 | MAE p90 | MFE mean | MFE p50 | MFE p90 |
|--------|---|----------|---------|---------|----------|---------|---------|
| HIGH | 12184 | 8.57 | 4.25 | 20.50 | 8.66 | 4.25 | 20.75 |
| nonHIGH | 23244 | 8.16 | 4.00 | 19.75 | 8.13 | 3.75 | 20.25 |
| ALL | 35428 | 8.30 | 4.00 | 20.00 | 8.31 | 4.00 | 20.25 |

## IS tag

**`IS_NULL`**

- Bootstrap 90% CI for dSharpe vs fixed entirely below 0 for both sizing policies.

## Hostile IS reading

Zero-edge coin-flip + proportional costs: inv-vol upsizes quiet clocks and increases cost drag. Mechanical null — does **not** kill 24D (different mechanism).

## Stop

- Val / OOS unlocked only after review.
