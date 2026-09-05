# Results — HIGH Opportunity / Activity State

**Verdict: `A*`** (`A_opportunity_timing_found`) — **gate / state detector only, not a trade**

Canonical:
- [`artifacts/06_HIGH_opportunity_state/ny_open_opp_timing_report.md`](../../../artifacts/06_HIGH_opportunity_state/ny_open_opp_timing_report.md)
- [`artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.md`](../../../artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.md)
- [`artifacts/06_HIGH_opportunity_state/nq_high_mech_report.md`](../../../artifacts/06_HIGH_opportunity_state/nq_high_mech_report.md)

Panel: **64,748** rows · **3,600** days. STRUCT_FRAC=**0.25** · PRIMARY ARM = `vol_expansion_high` (`rng_onr ≥ IS p66[T]`).

## Counts

| Tier | Count |
|------|------:|
| Strong cells | **878** (LOW 363 / HIGH 515) |
| Soft | 353 |
| Strong discrimination pairs | **533** |

## Unconditional IS P(structural resolve ≥0.25·ONR)

| T+ \ H | H10 | H15 | H20 | H30 | H45 |
|--------|----:|----:|----:|----:|----:|
| +5m | 72.1% | 82.6% | 87.4% | 92.5% | 95.8% |
| +30m | 61.5% | 73.8% | 80.1% | 87.4% | 92.2% |
| +60m | 48.5% | 61.6% | 70.0% | 79.9% | 88.2% |

## Headline LOW cut (example)

`wide_ON_quiet_open` +30m H10: IS n=451, P=**26.8%**, Δ=**−34.6pp**; Val −25.8; OOS −26.0; 2025 −25.8; 2026 −24.7 (all same sign).

## Headline HIGH−LOW discrimination

`low_local_vol` vs `high_local_vol` +50m H10:

| Split | Gap | P(low→high) |
|-------|----:|-------------|
| IS | **+62.0pp** | 18.1% → **80.0%** |
| Val | +62.4pp | — |
| OOS | +56.5pp | — |
| 2025 | +55.2pp | — |
| 2026 | +59.0pp | — |

Clock stability (low vs high vol, H10): median OOS gap **+59.2pp**, **18/18** strong clocks.

ONR-matched control T+30 H15: `high_local_vol` raw +21.6 → matched **+22.9pp**; `low_local_vol` −27.8 → **−24.9pp**.

## Mechanism decomposition (frozen HIGH)

Nature: **`persistence_already_moving`**

| Metric (IS H30 unless noted) | Value |
|------------------------------|------:|
| Med share of eventual open→T+H excursion already in at T | **94.8%** |
| % already_moving (≥60% pre) | **90.0%** |
| % early_transition (≤40% pre) | **2.1%** |
| P(struct resolve) HIGH vs LOW | **96.0%** vs **65.8%** (gap **+30.2pp**) |
| Med pre-excursion at HIGH (ONR) | **1.156** |
| Med incremental post-T max (ONR) | **0.588** |
| OOS H30 share_pre / already / P(res) | 94.0% / 88.7% / 95.3% |
| 2025 / 2026 H30 P(res) | 95.2% / 95.6% |

## Standardized table (activity, not direction)

| Metric | IS | Validation | OOS | 2025 | 2026 |
|--------|---:|----------:|----:|-----:|-----:|
| Disc gap example (pp) | +62.0 | +62.4 | +56.5 | +55.2 | +59.0 |
| HIGH P(struct) H30 | 96.0% | 96.0% | 95.3% | 95.2% | 95.6% |
| Already-moving share H30 | 90.0% | 90.3% | 88.7% | 91.4% | 84.2% |

**Caveat number:** already-moving **90%** / early transition **2.1%** → late persistence detector, not early alarm.
