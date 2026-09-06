# Hypothesis 24A — Validation (documentation; freeze unchanged)

IS provisional tag was `IS_NULL`. Val scored once with **zero** parameter adjustment.

## Freeze

| Item | Value |
|------|-------|
| Vol lookback W | 30 |
| rv_ref (IS median) | 1.264130 |
| Size clips | [0.25, 4.0] |
| HIGH multiplier | 0.7 (non-HIGH 1.0) |
| Cost RT | 1.0 pt x |size| |
| Risk-trade rows (Validation) | 3,076 |

## Direction audit

Primary book = **coin-flip**. Long/short audit under identical sizing.

## Primary book (coin-flip) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 3076 | 775 | -0.727 | -1.053 | -3290.0 | 0 | 0 | 1.000 |
| `invvol` | 3076 | 775 | -1.083 | -1.610 | -1103.4 | -0.356 [-0.566, -0.151] | -0.556 [-0.876, -0.264] | 0.367 |
| `invvol_high_aware` | 3076 | 775 | -1.035 | -1.565 | -977.8 | -0.308 [-0.570, -0.067] | -0.512 [-0.902, -0.164] | 0.336 |

## Audit book (always long) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 3076 | 775 | -0.161 | -0.240 | -2579.2 | 0 | 0 | 1.000 |
| `invvol` | 3076 | 775 | -0.307 | -0.479 | -794.2 | -0.146 [-0.350, 0.041] | -0.239 [-0.554, 0.059] | 0.367 |
| `invvol_high_aware` | 3076 | 775 | -0.221 | -0.349 | -679.0 | -0.060 [-0.325, 0.190] | -0.109 [-0.524, 0.295] | 0.336 |

## Audit book (always short) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 3076 | 775 | -1.527 | -2.435 | -5744.5 | 0 | 0 | 1.000 |
| `invvol` | 3076 | 775 | -1.980 | -3.033 | -2010.0 | -0.453 [-0.636, -0.264] | -0.598 [-0.908, -0.290] | 0.367 |
| `invvol_high_aware` | 3076 | 775 | -2.083 | -3.199 | -1926.0 | -0.556 [-0.798, -0.302] | -0.765 [-1.172, -0.383] | 0.336 |

## Validation tag

**`VAL_CONFIRMS_NULL`**

- Bootstrap 90% CI for dSharpe vs fixed entirely below 0 for both sizing policies.

## Reading

Documentation Val after IS_NULL. Expect same mechanical cost-drag pattern. Not a promote path. OOS optional for triple parity.

## Stop

- No refit. OOS documentation may follow.
