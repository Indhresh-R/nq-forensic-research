# Strategy 18 — Causal Direction Discovery

## HIGH forward skew (no resolver)

| Session | Split | H | n | P(up) | E[pts] |
|---------|-------|---|---|-------|--------|
| LONDON | IS | 30 | 3274 | 49.3% | -0.09 |
| LONDON | IS | 60 | 3274 | 50.7% | +0.08 |
| LONDON | Validation | 30 | 1315 | 48.7% | -0.25 |
| LONDON | Validation | 60 | 1315 | 49.6% | -0.51 |
| LONDON | OOS | 30 | 318 | 52.2% | -0.82 |
| LONDON | OOS | 60 | 318 | 54.1% | -0.20 |
| NY_PM | IS | 30 | 3177 | 53.0% | +0.24 |
| NY_PM | IS | 60 | 3177 | 53.4% | +0.44 |
| NY_PM | Validation | 30 | 1162 | 52.2% | +0.17 |
| NY_PM | Validation | 60 | 1162 | 53.8% | +1.19 |
| NY_PM | OOS | 30 | 555 | 50.3% | +6.78 |
| NY_PM | OOS | 60 | 555 | 52.6% | +9.38 |
| NY_AM | IS | 30 | 1640 | 53.5% | +0.24 |
| NY_AM | IS | 60 | 1640 | 54.1% | +0.18 |
| NY_AM | Validation | 30 | 454 | 49.8% | -3.03 |
| NY_AM | Validation | 60 | 454 | 54.6% | -0.32 |
| NY_AM | OOS | 30 | 302 | 51.7% | -0.33 |
| NY_AM | OOS | 60 | 302 | 52.0% | -3.34 |
| ASIA | IS | 30 | 3433 | 49.9% | +0.07 |
| ASIA | IS | 60 | 3433 | 51.2% | +0.42 |
| ASIA | Validation | 30 | 904 | 49.6% | +1.46 |
| ASIA | Validation | 60 | 904 | 50.2% | +3.05 |
| ASIA | OOS | 30 | 1025 | 50.9% | +1.33 |
| ASIA | OOS | 60 | 1025 | 52.4% | +2.49 |

## Resolver scoreboard (H=30, best IS lift clock per session — then median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS win | Survives gate? |
|----------|-------------|--------------|--------------|-------------------|----------------|
| `mom5_follow` | +2.4pp | +1.1pp | +1.5pp | 54.5% | YES |
| `mom15_follow` | +0.2pp | -0.8pp | -3.0pp | 50.2% | no |
| `mom15_fade` | +1.3pp | +0.5pp | +2.3pp | 58.5% | no |
| `vwap_follow` | +0.2pp | +0.6pp | -2.2pp | 50.4% | YES |
| `vwap_fade` | +1.5pp | +0.8pp | +2.6pp | 56.5% | no |
| `ext_fade` | +2.0pp | +1.8pp | +0.6pp | 60.0% | no |
| `prior_sess_mid` | +1.0pp | +1.3pp | -0.7pp | 52.9% | YES |
| `gap_follow` | +2.1pp | -0.9pp | -0.3pp | 54.0% | YES |
| `path30_follow` | +1.1pp | +0.2pp | +0.2pp | 52.3% | YES |
| `path30_fade` | +1.6pp | -0.1pp | +3.5pp | 59.8% | no |

## Candidates (lift gate)

| Tier | Resolver | Session | T+ | H | Lift IS | Lift Val | Lift OOS | HIGH OOS |
|------|----------|---------|----|---|---------|----------|----------|----------|
| soft | `path30_follow` | ASIA | 90 | 30 | +1.8pp | +2.1pp | -2.1pp | 42.1% |
| soft | `mom5_follow` | ASIA | 180 | 60 | +1.6pp | -2.2pp | +7.7pp | 60.9% |
| soft | `gap_follow` | NY_AM | 30 | 30 | +1.4pp | +2.4pp | +4.2pp | 53.0% |
| soft | `path30_follow` | NY_PM | 120 | 60 | +1.3pp | -0.4pp | -1.3pp | 47.4% |
| soft | `prior_sess_mid` | NY_PM | 90 | 60 | +0.2pp | -1.4pp | -1.3pp | 49.3% |
| soft | `prior_sess_mid` | NY_PM | 120 | 60 | -1.6pp | -0.8pp | -3.2pp | 47.4% |
| strong | `vwap_follow` | NY_PM | 90 | 60 | +1.3pp | +2.4pp | -2.6pp | 45.8% |
| strong | `prior_sess_mid` | NY_AM | 60 | 30 | +1.1pp | +2.7pp | -0.2pp | 52.9% |
| strong | `vwap_follow` | ASIA | 180 | 60 | +0.1pp | +1.4pp | +3.8pp | 51.5% |
| strong | `vwap_follow` | NY_AM | 60 | 30 | -0.0pp | +1.3pp | -4.5pp | 47.7% |

## Verdict

**`B_lead` (machine) / `C_null` (practical)**

Machine gate found fragile multi-clock soft on `prior_sess_mid` @ NY_PM H60,
but candidate rows include **negative OOS win lifts** carried by E-lift.
**Do not promote.** Treat as clean null for direction.

### What this means

- Strategy 12 (WHEN) remains valid; HIGH alone is ~coin-flip for UP/DOWN.
- This scan does **not** authorize a direction strategy.
- Next requires **new signed information**, not more NQ-path bias formulas.

