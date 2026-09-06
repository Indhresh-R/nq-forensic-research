# Strategy 14 — Multi-session Residual Economics (Phase B)

## Freeze

- Residual = max(MFE, MAE) from entry over H; entry = next open (stress delay1)
- Costs RT pts: {'tight': 0.5, 'mid': 1.0, 'wide': 2.0}
- Primary: H=30, cost=mid
- HIGH/LOW: frozen IS `rng_psr` terciles from strategy 12
- Sessions independent; order: LONDON → NY_PM → NY_AM → ASIA

## Stack (conceptual)

```text
Gross residual opportunity
     − spread/slippage/fees (cost scenarios)
     − entry delay stress
     → Net residual / Net R vs break-even
     → OOS stability + HIGH vs LOW lift
```

## Primary (HIGH, next_open, H30, mid cost)

| Session | Split | n | Mean resid | Cover mid | Mean net | Mean netR | P(net>0) | Pre-exc pts |
|---------|-------|---|------------|-----------|----------|-----------|----------|-------------|
| LONDON | IS | 4092 | 9.29 | 99.9% | 8.29 | +8.29 | 98.9% | 13.81 |
| LONDON | Validation | 1618 | 25.28 | 100.0% | 24.28 | +24.28 | 100.0% | 35.08 |
| LONDON | OOS | 376 | 38.95 | 100.0% | 37.95 | +37.95 | 100.0% | 64.19 |

| NY_PM | IS | 3980 | 16.94 | 100.0% | 15.94 | +15.94 | 99.9% | 20.75 |
| NY_PM | Validation | 1447 | 45.59 | 100.0% | 44.59 | +44.59 | 100.0% | 57.15 |
| NY_PM | OOS | 686 | 70.81 | 100.0% | 69.81 | +69.81 | 100.0% | 88.18 |

| NY_AM | IS | 3280 | 20.20 | 100.0% | 19.20 | +19.20 | 100.0% | 28.78 |
| NY_AM | Validation | 922 | 64.83 | 100.0% | 63.83 | +63.83 | 100.0% | 91.74 |
| NY_AM | OOS | 580 | 98.38 | 100.0% | 97.38 | +97.38 | 100.0% | 136.22 |

| ASIA | IS | 4196 | 10.44 | 98.5% | 9.44 | +9.44 | 96.4% | 16.02 |
| ASIA | Validation | 1122 | 23.01 | 100.0% | 22.01 | +22.01 | 100.0% | 43.38 |
| ASIA | OOS | 1252 | 42.37 | 100.0% | 41.37 | +41.37 | 100.0% | 64.22 |

## HIGH vs LOW cover lift (OOS, H30, mid)

| Session | HIGH cover | LOW cover | Δ | Mean net HIGH | Mean net LOW |
|---------|------------|-----------|---|---------------|--------------|
| LONDON | 100.0% | 100.0% | +0.0pp | 37.95 | 37.76 |
| NY_PM | 100.0% | 100.0% | +0.0pp | 69.81 | 49.14 |
| NY_AM | 100.0% | 100.0% | +0.0pp | 97.38 | 92.35 |
| ASIA | 100.0% | 100.0% | +0.0pp | 41.37 | 29.81 |

## Cost / delay stress (HIGH, H30, OOS mean net)

| Session | tight | mid | wide | delay1 mid |
|---------|-------|-----|------|------------|
| LONDON | 38.45 | 37.95 | 36.95 | 37.61 |
| NY_PM | 70.31 | 69.81 | 68.81 | 69.00 |
| NY_AM | 97.88 | 97.38 | 96.38 | 96.36 |
| ASIA | 41.87 | 41.37 | 40.37 | 41.25 |

## Per-session verdicts

| Session | Verdict | OOS net mid | Cover lift vs LOW |
|---------|---------|-------------|-------------------|
| LONDON | **NO_EDGE_VS_LOW** | 37.95 | +0.0pp |
| NY_PM | **NO_EDGE_VS_LOW** | 69.81 | +0.0pp |
| NY_AM | **NO_EDGE_VS_LOW** | 97.38 | +0.0pp |
| ASIA | **NO_EDGE_VS_LOW** | 41.37 | +0.0pp |

**Program call:** residual exists in the activity sense, but under frozen costs / latency it does **not** clear a tradeable Phase B econ gate (or fails vs LOW). Same failure mode family as strategy 11 is possible.

