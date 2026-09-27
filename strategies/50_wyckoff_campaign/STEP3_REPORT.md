# Step 3 Report — Leave-range outcomes under frozen grammar

**Status:** Complete.  
**Date:** 2026-09-21  
**Governing docs:** `PREREGISTRATION.md`, `STEP2_ADDENDUM.md`, `STEP2_REPORT.md`  
**Companion:** `FUNNEL_DIAGNOSTIC.md` (descriptive only; no rule changes)

### Funnel summary (see that file)

```text
2,402 TRs → 4,491 terminal violations → 480 returns → 221 candidate tests → 20 C
```

Largest drop: violation → return (excursion-cap aborts). Confirmation is a second choke (221 → 20). Neither fact authorizes retuning.

---

## Non-negotiables honored

- No retuning of TR / spring / confirmation parameters.
- No threshold search.
- No strategy / entry / exit / P&L construction.
- Outcomes measured only after sequence-declaration timestamps (`t_return` ≠ `t_confirm` for C).
- Preregistered sample floors applied before interpreting point estimates.

---

## Primary verdict (C vs A)

### `INCONCLUSIVE`

**Reason (preregistered):** sample floors not met.

| Floor | Required | Observed |
| --- | ---: | ---: |
| IS Treatment C | ≥ 30 | **10** |
| IS Control A | ≥ 30 | 7,386 |
| OOS Treatment C | ≥ 20 | **4** |
| OOS Control A | ≥ 20 | 1,918 |

Under the frozen gate, undersized C **forces `INCONCLUSIVE`**. It does not authorize loosening the grammar.

### Point estimates (descriptive only — not a pass)

Pooled `LEAVE_IMPLIED` rates and `Δ = p_C − p_A`:

| Split | H | n_C | n_A | p_C | p_A | Δ | IS p-value |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IS | 8 | 10 | 7386 | 0.70 | 0.19 | +0.51 | 0.0007 |
| IS | 16 | 10 | 7386 | 0.70 | 0.30 | +0.40 | 0.011 |
| IS | 32 | 10 | 7386 | 0.70 | 0.44 | +0.26 | 0.118 |
| Validation | 8 | 6 | 3768 | 0.50 | 0.23 | +0.27 | — |
| Validation | 16 | 6 | 3768 | 0.67 | 0.34 | +0.33 | — |
| Validation | 32 | 6 | 3768 | 0.67 | 0.48 | +0.18 | — |
| OOS | 8 | 4 | 1918 | 0.75 | 0.18 | +0.57 | — |
| OOS | 16 | 4 | 1918 | 0.75 | 0.29 | +0.46 | — |
| OOS | 32 | 4 | 1917 | 0.75 | 0.45 | +0.30 | — |

Horizons 8 and 16 would have satisfied the *sign + IS significance* limb of the gate if sample floors had been met. **They do not override the floor.** With n_C = 4–10, these deltas are not a supported mechanism result.

Artifacts: `results/contrast_C_vs_A.csv`, `results/outcomes.parquet`, `results/step3_verdict.json`.

---

## Secondary contrast (C vs B) — confirmation information

### Descriptive label: `INCONCLUSIVE`

Also underpowered (IS C=10, OOS C=4; B is larger but C is the binding constraint).

| Split | H | n_C | n_B | p_C | p_B | Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| IS | 8 | 10 | 204 | 0.70 | 0.33 | +0.37 |
| IS | 16 | 10 | 204 | 0.70 | 0.43 | +0.27 |
| IS | 32 | 10 | 204 | 0.70 | 0.50 | +0.20 |
| Validation | 8–32 | 6 | 121 | ~0.50–0.67 | ~0.46–0.66 | ~0 |
| OOS | 8–32 | 4 | 93 | 0.75 | 0.40–0.62 | +0.13–0.35 |

This contrast remains the right *conceptual* question for a future adequately powered specification. It cannot rescue the primary verdict.

Artifact: `results/contrast_C_vs_B.csv`.

---

## Interpretation (mechanism research, not trading)

1. **Rare ≠ false.** The frozen Wyckoff sequence is rare (20 C events). That is a property of the operational grammar on this panel, not evidence the idea is wrong.
2. **This experiment cannot claim support.** The preregistered answer is **`INCONCLUSIVE`** due to power, full stop.
3. **Do not retune to inflate C.** Any looser TR/confirm rule is a **new preregistration**, not a rescue of Strategy 50.
4. Point estimates that look favorable on tiny C are **hypothesis-generating at best**, not a green light.

---

## Outcome clock (frozen)

| Class | Outcome `t0` (then start at next 15m bar) |
| --- | --- |
| C | `t_sequence_complete` (= successful `t_confirm`) |
| B | first failed confirm pivot, else `t_return+W` on window expire, else fail bar |
| A | `t_return` |

`LEAVE_IMPLIED`: spring → close above `TR_high`; upthrust → close below `TR_low`. Horizons `H ∈ {8,16,32}` only.

---

## Explicit non-actions

- No parameter changes after seeing outcomes.
- No Sharpe / PF / stops / targets.
- No claim that Wyckoff “works” on NQ.
