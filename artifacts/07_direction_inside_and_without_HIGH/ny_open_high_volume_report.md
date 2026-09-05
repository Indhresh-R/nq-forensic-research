# HIGH + Volume Directional — Minimal Report

**Classification: `B`** — Volume leftovers exist but fail multi-clock stability / consistency. Single-clock spikes ignored.

Frozen HIGH: `vol_expansion_high` (untouched). Family: volume only.

Strong cells: 1 · Soft: 14 · Multi-clock strong mechs: 0

## Mechanism IS summary (median across clocks/horizons)

| Mechanism | med n | med win | med Δ vs HIGH-FOLLOW |
|-----------|-------|---------|----------------------|
| `thin_vol_follow` | 279 | 52.0% | +4.6pp |
| `hivol_efficient` | 106 | 49.6% | +1.1pp |
| `tod_low_vol_follow` | 291 | 48.1% | +0.5pp |
| `vol_pct_low_follow` | 291 | 48.1% | +0.5pp |
| `lovol_move` | 291 | 48.1% | +0.5pp |
| `tod_high_vol_follow` | 296 | 48.5% | +0.1pp |
| `vol_pct_high_follow` | 296 | 48.5% | +0.1pp |
| `hivol_impulse` | 296 | 48.5% | +0.1pp |
| `vol_accel_follow` | 279 | 48.0% | -0.1pp |
| `vol_exp_dir` | 279 | 48.0% | -0.1pp |
| `vol_decel_follow` | 270 | 48.5% | -0.8pp |
| `vol_exp_efficient` | 99 | 47.1% | -1.4pp |
| `heavy_vol_follow` | 269 | 45.9% | -2.4pp |

## Surviving cells (if any)

| Tier | X | T+ | H | IS n | IS | Δ | Val | OOS | 2025 | 2026 |
|------|---|----|---|------|----|---|-----|-----|------|------|
| strong | `thin_vol_follow` | +10 | 30 | 279 | 58.1% | +7.0pp | 56.8% | 58.1% | 54.2% | 64.7% |
| soft | `thin_vol_follow` | +80 | 30 | 279 | 54.8% | +9.2pp | 53.9% | 50.9% | 50.7% | 51.1% |
| soft | `thin_vol_follow` | +15 | 10 | 279 | 57.3% | +6.6pp | 50.6% | 53.8% | 50.8% | 58.1% |
| soft | `thin_vol_follow` | +55 | 15 | 279 | 55.2% | +6.6pp | 52.5% | 52.6% | 52.9% | 52.3% |
| soft | `thin_vol_follow` | +35 | 30 | 279 | 53.4% | +6.3pp | 50.0% | 53.9% | 50.7% | 59.5% |
| soft | `thin_vol_follow` | +10 | 15 | 279 | 54.5% | +5.4pp | 60.1% | 57.0% | 52.5% | 64.7% |
| soft | `thin_vol_follow` | +15 | 15 | 279 | 56.3% | +4.9pp | 52.4% | 57.7% | 60.7% | 53.5% |
| soft | `thin_vol_follow` | +50 | 30 | 279 | 52.7% | +4.4pp | 52.7% | 52.9% | 53.2% | 52.5% |
| soft | `thin_vol_follow` | +25 | 30 | 279 | 56.3% | +4.0pp | 53.3% | 57.8% | 56.5% | 60.0% |
| soft | `vol_accel_follow` | +70 | 30 | 278 | 50.7% | +3.6pp | 51.4% | 60.5% | 65.2% | 55.0% |
| soft | `vol_exp_dir` | +70 | 30 | 278 | 50.7% | +3.6pp | 51.4% | 60.5% | 65.2% | 55.0% |
| soft | `thin_vol_follow` | +75 | 30 | 280 | 51.1% | +3.4pp | 57.0% | 50.4% | 50.0% | 51.1% |
| soft | `tod_high_vol_follow` | +65 | 10 | 291 | 54.0% | +3.3pp | 50.5% | 54.8% | 54.3% | 55.6% |
| soft | `vol_pct_high_follow` | +65 | 10 | 291 | 54.0% | +3.3pp | 50.5% | 54.8% | 54.3% | 55.6% |
| soft | `hivol_impulse` | +65 | 10 | 291 | 54.0% | +3.3pp | 50.5% | 54.8% | 54.3% | 55.6% |

All strong cells fail multi-clock bar — not promotable.

## Stability

- `hivol_impulse` H10: 1 clocks (0 strong) [65]
- `thin_vol_follow` H10: 1 clocks (0 strong) [15]
- `thin_vol_follow` H15: 3 clocks (0 strong) [10, 15, 55]
- `thin_vol_follow` H30: 6 clocks (1 strong) [10, 25, 35, 50, 75, 80]
- `tod_high_vol_follow` H10: 1 clocks (0 strong) [65]
- `vol_accel_follow` H30: 1 clocks (0 strong) [70]
- `vol_exp_dir` H30: 1 clocks (0 strong) [70]
- `vol_pct_high_follow` H10: 1 clocks (0 strong) [65]

## Final: **B**

Kill for promotion (no multi-clock strong mechanism). Closest leftover: `thin_vol_follow` (soft cluster, not promotable).

Next family: **multi-scale**.

