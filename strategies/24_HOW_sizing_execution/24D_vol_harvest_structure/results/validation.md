# Hypothesis 24D — Validation (documentation; freeze unchanged)

IS tag was `IS_PARTIAL`. Val scored once. Headline = **`uncond_wide` vs `regime_width`** (HIGH-conditional value), not each-vs-base alone.

## Freeze

| Item | Value |
|------|-------|
| bo_frac | 0.1 |
| stop_r | 1.0 |
| tgt_r | 1.5 |
| width_high | 1.5 |
| width_non | 1.0 |
| max_hold | 60 |
| cost_rt | 1.0 |
| Panel rows | 64,064 |

## Headline — `uncond_wide` vs `regime_width` (decisive)

Q2 only: does regime-conditioning the width beat always-wide? (Q1 width-vs-base already answered on IS.)

| Policy | E[pts] | Sharpe | Sortino | n |
|--------|--------|--------|---------|---|
| `uncond_base` | -4.241 | -7.285 | — | — |
| `uncond_wide` | -1.735 | -2.165 | -3.917 | 3062 |
| `regime_width` | -3.124 | -4.959 | -7.740 | 3062 |

**ΔSharpe (`regime_width` − `uncond_wide`):** -2.794 [-3.532, -2.118]

**ΔSortino (`regime_width` − `uncond_wide`):** -3.822 [-4.932, -2.774]

Reading: `uncond_wide` dominates `regime_width` on Sharpe; best policy still **E < 0** — not a tradeable structure.

## All policies — Validation pooled

| Policy | n | win | E[pts] | Sharpe | Sortino | MaxDD | dSharpe vs base | dSharpe vs wide |
|--------|---|-----|--------|--------|---------|-------|----------------|-----------------|
| `uncond_base` | 3062 | 29.3% | -4.241 | -7.285 | -10.909 | -13187.6 | 0 | — |
| `uncond_wide` | 3062 | 39.8% | -1.735 | -2.165 | -3.917 | -5728.0 | 5.121 [4.175, 6.098] | — |
| `regime_width` | 3062 | 34.4% | -3.124 | -4.959 | -7.740 | -9807.3 | 2.327 [1.666, 3.039] | -2.794 [-3.532, -2.118] |
| `high_only_base` | 1565 | 26.1% | -4.257 | -6.803 | -10.447 | -6643.5 | 0.514 [-0.717, 1.713] | — |

## Direction audit

`uncond_wide` fills: long 1521 / short 1541; E_long -0.794 / E_short -2.663.

## Validation tag

**`VAL_WIDE_DOMINATES`**

- ΔSharpe (regime − wide) 90% CI entirely below 0 — unconditional width wins; no HIGH-conditional incremental value.
- Best policy `uncond_wide` still E=-1.735 < 0 — not tradeable; HOW answer is scientific (no monetizable Strategy-12 structure under costs).
- Q1 held: width helps vs narrow base (general execution-parameter effect, not HIGH).

## Reading

Documentation Val. Decisive cell is regime − wide. Even if width still beats base, negative E on best policy keeps HOW non-tradeable.

## Stop

- No refit. 24B remains folded. 24C unlock only after this Val review.
