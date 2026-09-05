# NQ Failed Movement / Exhaustion — Minimal Report (NO HIGH)

**Classification: `B`** — Weak/inconsistent failed-movement leftovers; no multi-clock strong effect. Kill for promotion.

Kill family: **True**. Failure = missed `0.75·vol` extension within `15m` after IS-qualified attempt — **fully known at T**. Outcomes from T+1.

Strong: 0 · Soft: 7 · Multi-clock strong: 0

## Mechanism IS summary (median across clocks/horizons)

| Mechanism | med n | win | Δ50 | mean z | MFE>MAE | P(+1R≺) | med exc |
|-----------|-------|-----|-----|--------|---------|---------|---------|
| `fade_weak_30` | 119 | 52.0% | +2.0pp | +0.131 | 52.3% | 51.5% | 0.24 |
| `fade_reject_30` | 517 | 51.1% | +1.1pp | +0.018 | 50.8% | 51.4% | 1.34 |
| `fade_fail_30` | 225 | 51.0% | +1.0pp | +0.038 | 51.5% | 51.6% | 0.45 |
| `fade_weak_15` | 115 | 50.9% | +0.9pp | +0.138 | 52.2% | 52.6% | 0.22 |
| `fade_fail_10` | 212 | 49.5% | -0.5pp | +0.021 | 49.9% | 51.5% | 0.44 |
| `fade_weak_10` | 121 | 49.5% | -0.5pp | +0.055 | 50.4% | 50.5% | 0.22 |
| `fade_fail_15` | 213 | 49.8% | -0.2pp | +0.064 | 50.9% | 52.6% | 0.45 |
| `fade_reject_15` | 514 | 50.2% | +0.2pp | +0.048 | 50.6% | 52.0% | 1.41 |
| `fade_reject_10` | 523 | 49.9% | -0.1pp | +0.027 | 50.1% | 52.0% | 1.39 |

## Bull vs bear failure → fade (IS median win)

| Side | med win | Δ50 | cells |
|------|---------|-----|-------|
| `bull_fail_fade_10` | 47.3% | -2.7pp | 120 |
| `bear_fail_fade_10` | 52.7% | +2.7pp | 120 |
| `bull_fail_fade_15` | 48.3% | -1.7pp | 120 |
| `bear_fail_fade_15` | 52.3% | +2.3pp | 120 |
| `bull_fail_fade_30` | 48.3% | -1.7pp | 114 |
| `bear_fail_fade_30` | 53.2% | +3.2pp | 114 |

## Surviving cells

| Tier | X | T+ | H | n | IS | Δ50 | mean z | Val | OOS | 2025 | 2026 |
|------|---|----|---|---|----|-----|--------|-----|-----|------|------|
| soft | `fade_reject_10` | +195 | 30 | 503 | 56.5% | +6.5pp | +0.194 | 54.8% | 53.9% | 56.4% | 50.0% |
| soft | `fade_reject_10` | +315 | 45 | 514 | 56.2% | +6.2pp | +0.463 | 52.6% | 56.1% | 51.4% | 61.3% |
| soft | `fade_reject_15` | +195 | 10 | 511 | 56.0% | +6.0pp | +0.247 | 56.4% | 57.5% | 56.1% | 59.4% |
| soft | `fade_reject_15` | +195 | 15 | 511 | 55.4% | +5.4pp | +0.254 | 55.8% | 54.8% | 58.5% | 50.0% |
| soft | `fade_reject_15` | +195 | 5 | 511 | 54.2% | +4.2pp | +0.157 | 55.8% | 53.4% | 53.7% | 53.1% |
| soft | `fade_reject_10` | +195 | 10 | 503 | 53.9% | +3.9pp | +0.155 | 56.1% | 59.6% | 58.2% | 61.8% |
| soft | `fade_reject_10` | +195 | 5 | 503 | 53.7% | +3.7pp | +0.116 | 52.2% | 57.3% | 56.4% | 58.8% |

No multi-clock strong mechanism — not promotable.

## Stability

- `fade_reject_10` H5: 1 clocks (0 strong) [195]
- `fade_reject_10` H10: 1 clocks (0 strong) [195]
- `fade_reject_10` H30: 1 clocks (0 strong) [195]
- `fade_reject_10` H45: 1 clocks (0 strong) [315]
- `fade_reject_15` H5: 1 clocks (0 strong) [195]
- `fade_reject_15` H10: 1 clocks (0 strong) [195]
- `fade_reject_15` H15: 1 clocks (0 strong) [195]

## Final: **B**

Kill failed-movement / exhaustion family.
Next: **expansion → retracement** (last planned intrinsic family).
HIGH remains frozen for later timing-only tests.
