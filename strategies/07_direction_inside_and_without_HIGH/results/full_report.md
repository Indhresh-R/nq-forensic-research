# Results — Direction Inside HIGH + Intrinsic OHLC Families

**Overall: directional layer missing** — multi-clock strong mechanisms across 07a–h = **0**

Canonical reports under `artifacts/07_direction_inside_and_without_HIGH/` (`ny_open_high_*`, `nq_serial_dep_*`, `nq_extreme_asym_*`, `nq_failed_move_*`, `nq_exp_retrace_*`).

## 07a Inside HIGH (price patterns) — `B_weak`

Panel: **19,941** HIGH rows · **1,885** days. Multi-clock strong mechs: **0**. Strong cells: **2** (single-clock only).

| Cell | IS | Val | OOS | 2025 | 2026 |
|------|---:|----:|----:|-----:|-----:|
| HIGH_ALONE_FOLLOW +15/H15 | 51.3% (+0.65) | 53.6% | 55.0% (+8.76) | — | — |
| HIGH_ALONE_LONG +15/H15 | 50.3% | — | **43.3%** (−22.64) | — | — |
| `on_open_continue` +85/H15 (n=281) | **56.2%** (+10.1pp) | 53.5% | 59.6% | 60.0% | 59.1% |
| soft `loc_now_fade` +50/H10 | 51.6% (+4.4pp) | — | — | — | — |

## 07b Cross-asset ES — `C`

Panel 19,924. Strong **0** / Soft **0**.

## 07c Volume — `B`

Strong cells **1**, multi-clock strong **0**. `thin_vol_follow` med Δ vs FOLLOW **+4.6pp**; best +10/H30 IS **58.1%** / Val 56.8 / OOS 58.1; 2025 **54.2%** / 2026 **64.7%**.

## 07d Multi-scale — `B`

Strong **0** / Soft **4**. Best soft `disagree_follow_short` +90/H30: IS **52.2%** (+4.2pp); OOS 57.1%; 2025 55.2 / 2026 59.3.

## 07e Serial dependence (NO HIGH) — `B`

Strong **1** / multi-clock **0**. `fade_30_ext` +195/H15: IS n=794 **54.2%** (+4.2pp); Val 53.8; OOS 53.1; 2025 51.9 / 2026 54.7.

## 07f Extreme asymmetry (NO HIGH) — `B`

Strong **2** / multi-clock **0**. `fade_30` +180/H5: IS **57.9%** (+7.9pp); Val 55.9; OOS 55.1; 2025 57.1 / 2026 **51.9**.

## 07g Failed movement (NO HIGH) — `B`

Strong **0** / Soft **7**. Best soft `fade_reject_10` +195/H30: IS **56.5%**; Val 54.8; OOS 53.9; 2025 56.4 / 2026 **50.0**.

## 07h Expansion→retracement (NO HIGH) — `B` → **stop OHLC directional tree**

Strong **1** / multi-clock **0**. `rev_fast_15` +135/H30: IS n=508 **55.1%** (+5.1pp); Val **61.2%**; OOS **58.0%**; 2025 56.5 / 2026 61.5.

## Standardized summary

| Subfamily | Verdict | Multi-clock strong | Headline |
|-----------|---------|-------------------:|----------|
| Inside HIGH | B | 0 | single-clock ≤~56–59% |
| ES | C | 0 | survivors 0 |
| Volume | B | 0 | 1 strong clock |
| Multiscale | B | 0 | soft ≤52–57% |
| Serial / extreme / fail / retrace | B | 0 | stop tree after retrace |

**Kill number:** multi-clock strong = **0** across all tested directional classes.
