# HIGH Mechanism Decomposition — What Does HIGH Detect?

**Nature: `persistence_already_moving`**

HIGH primarily labels an already-active / already-excursed state (activity/range persistence). Median share of eventual open-based excursion already present at T is very high; the early state-transition subset is rare. HIGH is not mainly an early compression-to-expansion detector.

Split-stability of already-moving share: **yes**. No strategy. Frozen `vol_expansion_high` only.

## Bottom line

| Question | Answer (IS, H30) |
|----------|------------------|
| How much of eventual open→T+H excursion is already in by HIGH? | **94.8%** median |
| Pre-excursion at HIGH (ONR units) | med **1.156** |
| Incremental post-T max excursion (next-open path) | med **0.588** ONR |
| P(structural resolve 0.25·ONR) HIGH vs LOW | **96.0%** vs **65.8%** (gap +30.2pp) |
| Share of HIGH that are early_transition (≤40% pre) | **2.1%** |
| Share already_moving (≥60% pre) | **90.0%** |

HIGH still separates opportunity from LOW — but it usually fires **after** most of the open-based excursion is already underway.

## 1. Predictive vs contemporaneous (share of eventual excursion already in by T)

For each HIGH at T: `share_pre = (open→T max excursion) / (open→T+H max excursion)`. `already_moving` if share_pre≥60%; `early_transition` if ≤40%.

| Split | H | n | med share_pre | % already | % early | P(resolve) | early→resolve | already→resolve |
|-------|---|---|---------------|-----------|---------|------------|---------------|-----------------|
| IS | 15 | 14777 | 100.0% | 95.3% | 0.7% | 85.9% | 100.0% | 85.2% |
| Validation | 15 | 4067 | 100.0% | 96.0% | 0.3% | 85.7% | 100.0% | 85.1% |
| OOS | 15 | 2258 | 100.0% | 94.3% | 1.1% | 85.6% | 100.0% | 84.7% |
| IS | 30 | 14777 | 94.8% | 90.0% | 2.1% | 96.0% | 100.0% | 95.6% |
| Validation | 30 | 4067 | 94.0% | 90.3% | 1.7% | 96.0% | 100.0% | 95.6% |
| OOS | 30 | 2258 | 94.0% | 88.7% | 3.0% | 95.3% | 100.0% | 94.8% |

## 2. Within HIGH: does more pre-excursion mean more post opportunity?

IS H30 resolve gradient (high_pre − low_pre pre-excursion tercile): **-1.4%**

| Split | H | bucket | n | med pre_exc | P(resolve) | med post_max | med share_pre |
|-------|---|--------|---|-------------|------------|--------------|---------------|
| IS | 30 | `high_pre` | 5025 | 1.765 | 96.1% | 0.600 | 100.0% |
| IS | 30 | `low_pre` | 4891 | 0.762 | 97.4% | 0.623 | 83.3% |
| IS | 30 | `mid_pre` | 4860 | 1.150 | 94.5% | 0.541 | 97.8% |
| Validation | 30 | `high_pre` | 1392 | 1.708 | 95.2% | 0.560 | 96.5% |
| Validation | 30 | `low_pre` | 1316 | 0.779 | 97.3% | 0.619 | 82.1% |
| Validation | 30 | `mid_pre` | 1359 | 1.141 | 95.7% | 0.586 | 99.2% |
| OOS | 30 | `high_pre` | 794 | 1.799 | 96.2% | 0.584 | 97.9% |
| OOS | 30 | `low_pre` | 735 | 0.778 | 94.8% | 0.594 | 81.3% |
| OOS | 30 | `mid_pre` | 729 | 1.167 | 94.9% | 0.530 | 96.9% |

## 3. HIGH vs LOW pre-T mechanism gaps (IS medians)

| Mechanism | Feature | HIGH med | LOW med | Gap |
|-----------|---------|----------|---------|-----|
| already_excursed_by_T | `pre_exc_onr` | 1.156 | 0.405 | 0.752 |
| directional_move_by_T | `abs_move_onr` | 0.810 | 0.191 | 0.619 |
| range_expansion_ratio | `expand_ratio` | 1.971 | 1.553 | 0.417 |
| volatility_clustering | `vol_cluster` | 0.689 | 0.660 | 0.029 |
| acceleration | `accel` | -0.002 | -0.000 | -0.001 |
| compression_to_expansion | `compress_then_expand` | 0.000 | 0.000 | 0.000 |

## 4. Profile snapshot @ T+30 (IS)

| Regime | n | med pre_exc | vol_cluster | expand_ratio | accel | %compress→exp | P(res H30) | med share_pre |
|--------|---|-------------|-------------|--------------|-------|---------------|------------|---------------|
| `HIGH` | 821 | 1.045 | 0.754 | 1.621 | -0.003 | 0.0% | 97.8% | 88.5% |
| `LOW` | 791 | 0.369 | 0.726 | 1.359 | -0.001 | 0.0% | 72.3% | 81.8% |
| `MID` | 796 | 0.638 | 0.726 | 1.459 | -0.002 | 0.0% | 91.7% | 87.1% |

## 5. Year check

| Year | H | n | med share_pre | % already | % early | P(resolve) |
|------|---|---|---------------|-----------|---------|------------|
| 2025 | 15 | 1391 | 100.0% | 95.5% | 0.9% | 85.8% |
| 2025 | 30 | 1391 | 95.9% | 91.4% | 2.3% | 95.2% |
| 2026 | 15 | 867 | 97.8% | 92.4% | 1.4% | 85.4% |
| 2026 | 30 | 867 | 90.8% | 84.2% | 4.0% | 95.6% |


## Interpretation

```text
                 HIGH
                  │
      ┌───────────┴───────────┐
      │                       │
 Already-moving state    State-transition
 (persistence)           (early detector)
      ▲
      └── dominant (~90% IS H30)
```

**Favors the left branch.** HIGH is largely an **activity/persistence detector**: the morning is already expanded/active. Post-T structural opportunity remains elevated vs LOW (incremental movement still happens), but detection is typically **late relative to the open-based path**.

### Mechanism gaps (IS HIGH−LOW)

- **already_excursed_by_T**: HIGH med 1.156 vs LOW 0.405 (gap 0.752)
- **directional_move_by_T**: HIGH med 0.810 vs LOW 0.191 (gap 0.619)
- **range_expansion_ratio**: HIGH med 1.971 vs LOW 1.553 (gap 0.417)
- **volatility_clustering**: HIGH med 0.689 vs LOW 0.660 (gap 0.029)
- **acceleration**: HIGH med -0.002 vs LOW -0.000 (gap -0.001)
- **compression_to_expansion**: HIGH med 0.000 vs LOW 0.000 (gap 0.000)

Largest separations are in **already-excursed size / range**, then expansion ratio and vol clustering — consistent with persistence, not a pure early transition.

### Trading implication (not a strategy)

- Do **not** treat HIGH as an early compression→go alarm.
- Any future use must assume: **state is often already moving** when HIGH flips on.
- Remaining question: residual post-T excursion economics under costs — different bar, later.

## Forbidden

- No new directional family
- No HIGH tercile retune
- No entries yet
