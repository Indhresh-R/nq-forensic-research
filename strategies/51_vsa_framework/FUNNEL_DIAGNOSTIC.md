# Funnel diagnostic — frozen VSA grammar only

**Status:** Descriptive. No rule changes. No optimization.  
**Date:** 2026-09-22  
**Source:** `results/funnel.json` from instrumented Step 2 extractor (same event grammar as preregistration).

Question answered here:

> Is Class C rare because the VSA sequence is rare, or because one operational stage collapses the sample?

---

## Funnel

```text
15m bars                           288,266
        ↓ warmup (seg_pos ≥ 22, finite medians/ATR)
warmup-eligible bars               193,071
        ↓
up-bars                             97,716
        ↓
location near prior high (A1)       18,870   (among up-bars)
SOW seed in lookback (A2)           85,204   (among up-bars; not requiring location)
BG_WEAK = A1 ∧ A2                   18,420
        ↓
ND morphology (narrow ∧ vol<prior2 ∧ close≤0.50)
                                     4,120
        ↓ path split (before dependence filters)
ND ∧ BG     → C candidates             456
ND ∧ ¬BG    → A candidates           3,664
BG ∧ ¬ND    → B candidates          17,964
        ↓ shared dependence / confirmation
skipped (min separation)             8,609
confirm gap abort                      249
confirm fail (not down-bar)          6,939
        ↓
C confirmed                             78
A confirmed                          1,535
B confirmed                          4,674
```

Continuity check:

```text
456 + 3,664 + 17,964 = 22,084 candidates
8,609 + 249 + 6,939 + 78 + 1,535 + 4,674 = 22,084
```

---

## Where the C sample collapses

| Stage | In | Out | Reading |
| --- | ---: | ---: | --- |
| Up-bars → ND morphology | 97,716 | 4,120 | ND bar shape is uncommon (~4.2% of up-bars). Expected: vol < both prior bars + narrow + weak close. |
| ND → ND∧BG | 4,120 | 456 | **Primary C choke.** Only ~11% of ND bars also sit in `BG_WEAK` (near-high + SOW seed). |
| C candidates → C confirmed | 456 | 78 | Shared confirmation filter (next bar down) plus separation. Same filter applies to A/B. |

### Plain reading

1. **Rarity is not “we never find up-bars near highs.”** Location and SOW seeds are abundant; `BG_WEAK` n≈18k among up-bars.
2. **The largest C-specific choke is context ∩ morphology:** No Demand without background is common (A path 3,664); full VSA Treatment needs both.
3. **Confirmation is a second, shared choke:** next-bar-down rejects many candidates across A/B/C (6,939 not-down fails).
4. This does **not** authorize loosening `K`, ATR fraction, `L`, close cuts, or narrow/volume rules. Those freezes were locked before outcomes. Changing them is a **new specification**.

---

## Comparison to Strategy 50 Wyckoff Step 2

| Framework | Class C n | Dominant choke (descriptive) |
| --- | ---: | --- |
| 50 Wyckoff TR campaign | 20 | Return-into-TR / excursion recovery, then confirm quality |
| 51 VSA No Demand sequence | 78 | ND∧background intersection, then next-bar-down |

VSA’s contextual **bar sequence** remains more observable under frozen rules than Wyckoff’s full **campaign** sequence — without implying either mechanism is real.

---

## Implication for Step 3

- C total 78 (IS 41 / Val 20 / OOS 17).
- Preregistered floors: IS C≥30 (met), OOS C≥20 (**not met** at 17).
- Under the frozen gate, power alone can force **`INCONCLUSIVE`** regardless of Δ sign — report that honestly; do not retune to inflate OOS C.

---

## Explicit non-actions

- No parameter change after inspecting this funnel.
- No daily timeframe rescue.
- Funnel counts are not mechanism outcomes and not a trading result.
