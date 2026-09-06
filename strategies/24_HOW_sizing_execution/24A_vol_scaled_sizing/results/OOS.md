# Hypothesis 24A — OOS (documentation triple; not a rescue)

IS tag `IS_NULL`. OOS recorded for IS/Val/OOS parity — **not** to promote a sizing claim.

## Freeze

| Item | Value |
|------|-------|
| Vol lookback W | 30 |
| rv_ref (IS median) | 1.264130 |
| Size clips | [0.25, 4.0] |
| HIGH multiplier | 0.7 (non-HIGH 1.0) |
| Cost RT | 1.0 pt x |size| |
| Risk-trade rows (OOS) | 1,637 |

## Direction audit

Primary book = **coin-flip**. Long/short audit under identical sizing.

## Primary book (coin-flip) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 1637 | 414 | 0.222 | 0.351 | -2203.0 | 0 | 0 | 1.000 |
| `invvol` | 1637 | 414 | 0.045 | 0.072 | -663.6 | -0.177 [-0.303, -0.059] | -0.279 [-0.496, -0.089] | 0.284 |
| `invvol_high_aware` | 1637 | 414 | 0.042 | 0.065 | -591.3 | -0.180 [-0.434, 0.081] | -0.285 [-0.725, 0.124] | 0.255 |

## Audit book (always long) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 1637 | 414 | -0.182 | -0.232 | -1902.5 | 0 | 0 | 1.000 |
| `invvol` | 1637 | 414 | -0.230 | -0.296 | -482.5 | -0.048 [-0.161, 0.064] | -0.064 [-0.211, 0.082] | 0.284 |
| `invvol_high_aware` | 1637 | 414 | -0.416 | -0.532 | -487.4 | -0.234 [-0.471, 0.021] | -0.300 [-0.617, 0.020] | 0.255 |

## Audit book (always short) — H=30

| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |
|--------|------|--------|--------|---------|-------|---------------------------|----------------------------|-----------|
| `fixed` | 1637 | 414 | -0.928 | -1.550 | -4680.8 | 0 | 0 | 1.000 |
| `invvol` | 1637 | 414 | -1.012 | -1.696 | -1241.4 | -0.084 [-0.199, 0.028] | -0.146 [-0.338, 0.040] | 0.284 |
| `invvol_high_aware` | 1637 | 414 | -0.863 | -1.477 | -1072.7 | 0.065 [-0.196, 0.309] | 0.072 [-0.352, 0.467] | 0.255 |

## OOS tag

**`OOS_NULL`**

- No Sharpe lift vs fixed.

## Reading

Documentation OOS. Sizing claim remains null. 24D is a separate ticket.

## Stop

- Triple complete for 24A. No sizing promote.
