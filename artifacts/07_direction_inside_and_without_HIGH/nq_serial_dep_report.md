# NQ Serial Dependence — Minimal Report (NO HIGH)

**Classification: `B`** — Weak/inconsistent serial dependence leftovers; no multi-clock strong memory. Do not promote.

Kill family: **True**. Scope: liquid RTH, independent of frozen HIGH.

Strong: 1 · Soft: 6 · Multi-clock strong mechs: 0

## Uncond long IS (sanity)

| T+ | H | win | mean |
|----|---|-----|------|
| +0m | 15 | 52.6% | +0.64 |
| +0m | 30 | 52.7% | +0.97 |
| +30m | 15 | 50.8% | -0.51 |
| +30m | 30 | 52.6% | +0.23 |
| +60m | 15 | 51.4% | -0.29 |
| +60m | 30 | 51.2% | -0.64 |
| +120m | 15 | 48.6% | -0.39 |
| +120m | 30 | 51.1% | -0.05 |
| +180m | 15 | 52.2% | +0.17 |
| +180m | 30 | 53.6% | +0.12 |

## Mechanism IS summary (|Δ| vs 50%)

| Mechanism | med n | med win | med Δ50 |
|-----------|-------|---------|---------|
| `follow_30_ext` | 794 | 47.2% | -2.8pp |
| `follow_30` | 2308 | 48.3% | -1.7pp |
| `run_continue` | 403 | 48.4% | -1.6pp |
| `follow_5_ext` | 795 | 48.5% | -1.5pp |
| `follow_15_ext` | 795 | 48.5% | -1.5pp |
| `follow_1_ext` | 800 | 48.6% | -1.4pp |
| `follow_15` | 2292 | 48.7% | -1.3pp |
| `follow_5` | 2249 | 48.7% | -1.3pp |
| `follow_1` | 2185 | 48.7% | -1.3pp |
| `fade_30_ext` | 794 | 51.2% | +1.2pp |
| `alt_fade` | 533 | 49.3% | -0.7pp |
| `fade_5` | 2249 | 49.3% | -0.7pp |

## Surviving cells

| Tier | X | T+ | H | IS n | IS | Δ50 | Val | OOS | 2025 | 2026 |
|------|---|----|---|------|----|-----|-----|-----|------|------|
| strong | `fade_30_ext` | +195 | 15 | 794 | 54.2% | +4.2pp | 53.8% | 53.1% | 51.9% | 54.7% |
| soft | `fade_5_ext` | +300 | 15 | 794 | 54.0% | +4.0pp | 50.8% | 53.3% | 52.5% | 54.3% |
| soft | `fade_15_ext` | +240 | 5 | 794 | 53.8% | +3.8pp | 50.2% | 51.6% | 51.2% | 52.2% |
| soft | `fade_30_ext` | +180 | 30 | 794 | 53.7% | +3.7pp | 52.3% | 55.8% | 54.9% | 57.1% |
| soft | `fade_5_ext` | +150 | 15 | 803 | 53.4% | +3.4pp | 53.3% | 56.6% | 58.4% | 53.3% |
| soft | `follow_1_ext` | +0 | 60 | 817 | 53.2% | +3.2pp | 54.7% | 55.5% | 59.3% | 50.0% |
| soft | `run_fade` | +105 | 5 | 434 | 53.2% | +3.2pp | 55.9% | 56.1% | 55.6% | 56.7% |

## Stability

- `fade_15_ext` H5: 1 clocks (0 strong) [240]
- `fade_30_ext` H15: 1 clocks (1 strong) [195]
- `fade_30_ext` H30: 1 clocks (0 strong) [180]
- `fade_5_ext` H15: 2 clocks (0 strong) [150, 300]
- `follow_1_ext` H60: 1 clocks (0 strong) [0]
- `run_fade` H5: 1 clocks (0 strong) [105]

## Final: **B**

Kill serial-dependence family for promotion.
Next independent family: **return / imbalance asymmetry** (vol-standardized).
HIGH remains frozen for later timing tests only.
