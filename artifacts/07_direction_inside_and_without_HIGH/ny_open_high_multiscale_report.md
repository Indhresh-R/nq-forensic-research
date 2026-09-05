# HIGH + Multi-Scale Directional — Minimal Report

**Classification: `B`** — Multi-scale leftovers exist (~soft/single-clock) without stable multi-clock incremental improvement over HIGH. Kill family for promotion.

Frozen HIGH: `vol_expansion_high` (untouched). Kill family: **True**.

Strong cells: 0 · Soft: 4 · Multi-clock strong mechs: 0

## Mechanism IS summary (median Δ vs HIGH-FOLLOW)

| Mechanism | med n | med win | med Δ |
|-----------|-------|---------|-------|
| `disagree_follow_short` | 324 | 50.0% | +1.8pp |
| `accel_with_med` | 368 | 49.6% | +1.0pp |
| `flip_5m` | 379 | 49.3% | +1.0pp |
| `align_1_5` | 492 | 48.6% | +0.8pp |
| `align_1_5_15` | 347 | 49.7% | +0.6pp |
| `follow_15` | 812 | 48.7% | +0.5pp |
| `rev_short_vs_med` | 324 | 48.1% | +0.3pp |
| `align_5_15` | 543 | 48.5% | +0.2pp |
| `follow_5` | 802 | 48.4% | +0.0pp |
| `persist_5m` | 399 | 47.8% | -0.1pp |

## Surviving cells

| Tier | X | T+ | H | IS n | IS | Δ | Val | OOS | 2025 | 2026 |
|------|---|----|---|------|----|---|-----|-----|------|------|
| soft | `disagree_follow_short` | +90 | 30 | 295 | 52.2% | +4.2pp | 55.1% | 57.1% | 55.2% | 59.3% |
| soft | `align_1_5_15` | +65 | 30 | 337 | 55.8% | +4.0pp | 54.5% | 58.2% | 54.5% | 62.9% |
| soft | `persist_5m` | +25 | 15 | 420 | 52.6% | +3.9pp | 55.8% | 60.9% | 66.7% | 52.0% |
| soft | `align_1_5_15` | +80 | 15 | 347 | 53.6% | +3.3pp | 53.8% | 62.9% | 64.3% | 60.0% |

## Stability

- `align_1_5_15` H15: 1 clocks (0 strong) Δmed=+3.3pp [80]
- `align_1_5_15` H30: 1 clocks (0 strong) Δmed=+4.0pp [65]
- `disagree_follow_short` H30: 1 clocks (0 strong) Δmed=+4.2pp [90]
- `persist_5m` H15: 1 clocks (0 strong) Δmed=+3.9pp [25]

## Final: **B**

Kill multi-scale family. Directional search **inside HIGH is exhausted** (price / levels / ES / volume / multi-scale).

Pivot: find direction **independently**, then test whether frozen HIGH improves its timing.
