# Hypothesis 24D — Vol-Harvest Structure (IS only)

## Stage gate

**Val unlocked only after review.** Two independent questions (multiplicity):

1. Does width help at all? (`uncond_wide` vs `uncond_base`)
2. Does HIGH-conditioning add anything on top of unconditional-wide? (`regime_width` vs `uncond_wide`) — **decisive HOW cell**

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
| `uncond_base` | -2.223 | -8.244 | — | — |
| `uncond_wide` | -1.242 | -3.166 | -4.555 | 9552 |
| `regime_width` | -1.905 | -6.265 | -8.043 | 9552 |

**ΔSharpe (`regime_width` − `uncond_wide`):** -3.099 [-3.563, -2.642]

**ΔSortino (`regime_width` − `uncond_wide`):** -3.489 [-4.056, -2.963]

Reading: `uncond_wide` dominates `regime_width` on Sharpe; best policy still **E < 0** — not a tradeable structure.

## All policies — IS pooled

| Policy | n | win | E[pts] | Sharpe | Sortino | MaxDD | dSharpe vs base | dSharpe vs wide |
|--------|---|-----|--------|--------|---------|-------|----------------|-----------------|
| `uncond_base` | 9552 | 27.2% | -2.223 | -8.244 | -10.203 | -21230.6 | 0 | — |
| `uncond_wide` | 9552 | 38.3% | -1.242 | -3.166 | -4.555 | -11897.2 | 5.078 [4.521, 5.636] | — |
| `regime_width` | 9552 | 32.1% | -1.905 | -6.265 | -8.043 | -18200.0 | 1.979 [1.624, 2.347] | -3.099 [-3.563, -2.642] |
| `high_only_base` | 4933 | 24.8% | -2.181 | -6.371 | -8.690 | -10769.5 | 1.906 [1.031, 2.715] | — |

## Multi-session — Sharpe

| Session | Policy | Sharpe | dSharpe vs base | dSharpe vs wide | n |
|---------|--------|--------|-----------------|-----------------|---|
| ASIA | `uncond_base` | -3.381 | 0 | — | 2334 |
| ASIA | `uncond_wide` | -2.272 | 1.108 [0.709, 1.541] | — | 2334 |
| ASIA | `regime_width` | -2.774 | 0.607 [0.272, 0.990] | -0.502 [-0.776, -0.253] | 2334 |
| ASIA | `high_only_base` | -3.220 | -1.179 [-1.999, -0.339] | — | 1125 |
| LONDON | `uncond_base` | -2.933 | 0 | — | 2399 |
| LONDON | `uncond_wide` | -1.417 | 1.516 [1.061, 2.009] | — | 2399 |
| LONDON | `regime_width` | -2.338 | 0.595 [0.342, 0.859] | -0.921 [-1.307, -0.532] | 2399 |
| LONDON | `high_only_base` | -5.073 | -1.794 [-2.677, -0.886] | — | 1246 |
| NY_AM | `uncond_base` | -9.311 | 0 | — | 2415 |
| NY_AM | `uncond_wide` | -1.997 | 7.314 [6.564, 8.080] | — | 2415 |
| NY_AM | `regime_width` | -7.036 | 2.275 [1.855, 2.747] | -5.038 [-5.654, -4.478] | 2415 |
| NY_AM | `high_only_base` | -14.882 | -0.531 [-2.291, 1.221] | — | 1201 |
| NY_PM | `uncond_base` | -2.373 | 0 | — | 2404 |
| NY_PM | `uncond_wide` | -1.089 | 1.284 [0.815, 1.767] | — | 2404 |
| NY_PM | `regime_width` | -1.648 | 0.725 [0.406, 1.038] | -0.559 [-0.950, -0.179] | 2404 |
| NY_PM | `high_only_base` | -3.080 | -2.108 [-2.785, -1.472] | — | 1361 |

## Direction audit

`uncond_wide` fills: long 4848 / short 4704; E_long -0.994 / E_short -1.498.

## IS tag

**`IS_PARTIAL`**

- ΔSharpe (regime − wide) 90% CI entirely below 0 — unconditional width wins; no HIGH-conditional incremental value.
- Best policy `uncond_wide` still E=-1.242 < 0 — not tradeable; HOW answer is scientific (no monetizable Strategy-12 structure under costs).
- Q1 held: width helps vs narrow base (general execution-parameter effect, not HIGH).

## Hostile IS reading

`uncond_wide` crushing `regime_width` means wider helps *unconditionally* — not because of HIGH. That also answers **24B** (regime-conditional stop/target) as a side-by-side arm: fold into this dossier; do not open a separate 24B ticket. 24C (holding period) remains distinct — hold until after Val.

## Stop

- Val next (headline = wide vs regime). OOS optional for triple.
- Standalone **24B skipped** (absorbed here). **24C held**.
