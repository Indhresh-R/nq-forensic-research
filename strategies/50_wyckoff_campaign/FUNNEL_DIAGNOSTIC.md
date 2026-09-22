# Funnel diagnostic — frozen grammar only

**Status:** Descriptive. No rule changes. No optimization.  
**Date:** 2026-09-21  
**Source:** `results/funnel.json` from instrumented Step 2 extractor (same event grammar as preregistration).

Question answered here:

> Are the 20 Class-C events rare because the Wyckoff sequence is rare, or because one operational adaptation collapses the sample at a specific stage?

---

## Funnel

```text
eligible TRs                         2,402
        ↓
terminal violations                  4,491   (spring 2,058 / upthrust 2,433)
        ↓  recover aborts
           excursion cap (>1× TR height)  3,538
           acceptance (4 closes outside)    285
           segment break                    188
           recovery timeout (R_max)           0
        ↓
returns into TR                        480   (spring 270 / upthrust 210)
        ↓  confirm window without a scored test
           adverse close through boundary   185
           window expire                     32
           segment break during confirm      42
        ↓
candidate tests                        221   (first scored test pivot)
        ↓
confirm success (Class C)               20
confirm fail (test quality)            201
```

Continuity check: returns (480) − confirm segment aborts (42) = 438 = Class B (418) + Class C (20).

---

## Where the sample collapses

| Stage | Count in | Count out | Drop | Share of drop at this stage |
| --- | ---: | ---: | ---: | --- |
| TR → terminal violation | 2,402 TRs | 4,491 violations | — | Violations are *more* numerous than TRs (multiple attempts per TR). Not the rarity bottleneck. |
| Violation → return | 4,491 | 480 | **4,011** | **Dominant collapse.** Mostly `recover_abort_excursion` (3,538): the frozen max-excursion rule (`> 1.00 × TR_height`) kills ~79% of terminal attempts before a return can complete. |
| Return → candidate test | 480 | 221 | 259 | Second-order: adverse close / window / gap during the confirm search before a test pivot prints. |
| Candidate test → C | 221 | 20 | 201 | Confirmation quality filter (higher/lower extreme + lesser volume) passes **9%** of scored tests. |

### Plain reading

1. **Rarity is not “we never find TRs.”** 2,402 TRs and 4,491 terminal violations exist.
2. **The largest choke is return completion**, especially the researcher-defined excursion cap — not the confirmatory-test grammar alone.
3. **Confirmation is a second choke:** of 221 scored tests, only 20 become C. So C’s smallness is *both* recovery scarcity and strict confirm quality — with recovery dominating the absolute drop.
4. This does **not** authorize loosening the excursion cap or the confirm rules. Those freezes were locked before outcomes. Changing them is a **new specification**.

---

## Implication for Step 3

- Class C n = 20 (IS 10 / Val 6 / OOS 4) is consistent with this funnel.
- The preregistered gate correctly yields **`INCONCLUSIVE`** on power grounds.
- A future study that wants more TRs is asking a different research question (e.g. different excursion / recovery operationalization) and must preregister separately — not rescue this run.

---

## Explicit non-actions

- No parameter change after inspecting this funnel.
- No “fix” that redefines excursion or confirmation to inflate C.
- Funnel counts are not leave-range outcomes and not a trading result.
