# Step 3 Report — Mechanism outcomes under frozen VSA grammar

**Status:** Complete.  
**Date:** 2026-09-22  
**Governing docs:** `PREREGISTRATION.md`, `STEP2_REPORT.md`, `FUNNEL_DIAGNOSTIC.md`  
**Code:** `code/run_outcomes.py`

### Non-negotiables honored

- No retuning of `K`, ATR frac, `L`, close cuts, wide multiple, or confirmation.
- No threshold / horizon search after seeing outcomes.
- No strategy / entry / exit / P&L.
- Outcomes only after `t_confirmation`; path must stay in-segment through `t_confirmation+H`.
- IS cannot rescue OOS. One horizon cannot rescue the gate.

---

## Three layers (keep separate)

| Layer | Question | Result |
| --- | --- | --- |
| **1. Formal preregistered gate** | Can `SUPPORTED` be declared under frozen floors + multi-split rule? | **`INCONCLUSIVE`** |
| **2. Mechanism evidence (ignoring floors)** | Do ≥2 horizons show same-sign Δ(C−A) on IS/Val/OOS with IS p≤0.05? | **No** (`stable_horizons = []`) |
| **3. Statistical power** | Do sample floors hold? | IS yes (C=41, A=886); **OOS C=17 < 20** |

OOS C = 17 does **not** close the research as “VSA is false.” It blocks `SUPPORTED` under the frozen gate. Separately, the multi-split sign pattern also fails — so this is not a case of “strong consistent effect blocked only by n=17.”

---

## 1. Formal primary verdict (C vs A, `DOWN_CLOSE`)

### `INCONCLUSIVE`

**Reason (preregistered):** OOS sample floor not met.

| Floor | Required | Observed |
| --- | ---: | ---: |
| IS Treatment C | ≥ 30 | **41** |
| IS Control A | ≥ 30 | **886** |
| OOS Treatment C | ≥ 20 | **17** |
| OOS Control A | ≥ 20 | **251** |

`is_floor_met = true`, `oos_floor_met = false` → underpowered → **`INCONCLUSIVE`**.

Artifact: `results/step3_verdict.json`.

---

## 2. Mechanism evidence on `DOWN_CLOSE` (does not override the gate)

Primary statistic: `Δ(H) = p_C(H) − p_A(H)` where  
`DOWN_CLOSE(H) = 1` iff `close[t_confirmation+H] < close[t_confirmation]`.  
Horizons frozen: `H ∈ {4, 8, 16}`.

### C vs A — full table (usable rows only)

| Split | H | n_C | n_A | p_C | p_A | Δ | IS p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IS | 4 | 38 | 792 | 0.605 | 0.427 | **+0.178** | **0.030** |
| IS | 8 | 32 | 718 | 0.500 | 0.414 | +0.086 | 0.332 |
| IS | 16 | 20 | 515 | 0.350 | 0.425 | −0.075 | 0.504 |
| Validation | 4 | 18 | 349 | 0.556 | 0.513 | +0.043 | — |
| Validation | 8 | 18 | 327 | 0.500 | 0.495 | +0.005 | — |
| Validation | 16 | 14 | 273 | 0.429 | 0.509 | −0.081 | — |
| OOS | 4 | 17 | 220 | 0.412 | 0.491 | **−0.079** | — |
| OOS | 8 | 15 | 207 | 0.333 | 0.478 | **−0.145** | — |
| OOS | 16 | 13 | 162 | 0.538 | 0.481 | +0.057 | — |

Artifact: `results/contrast_C_vs_A.csv`.

### Horizon gate limbs (ignoring sample floors)

| H | Same sign IS/Val/OOS? | IS p≤0.05? | Passes horizon rule? |
| --- | --- | --- | --- |
| 4 | **No** (IS/Val +, OOS −) | Yes | **No** |
| 8 | **No** (IS/Val +, OOS −) | No | **No** |
| 16 | **No** (IS/Val −, OOS +) | No | **No** |

`stable_horizons = []`. Even if OOS C had been 20, the multi-split limb would still fail on these estimates. **IS H=4 does not rescue OOS.**

---

## 3. Secondary contrast — C vs B (`DOWN_CLOSE`)

Question: given background weakness, does the No Demand morphology add information?

### Descriptive label: `INCONCLUSIVE`

(Still underpowered on OOS C floor; also no stable horizons.)

| Split | H | n_C | n_B | p_C | p_B | Δ | IS p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IS | 4 | 38 | 2312 | 0.605 | 0.476 | +0.129 | 0.114 |
| IS | 8 | 32 | 2069 | 0.500 | 0.462 | +0.038 | 0.665 |
| IS | 16 | 20 | 1665 | 0.350 | 0.473 | −0.123 | 0.272 |
| Validation | 4 | 18 | 1310 | 0.556 | 0.470 | +0.085 | — |
| Validation | 8 | 18 | 1218 | 0.500 | 0.462 | +0.038 | — |
| Validation | 16 | 14 | 1070 | 0.429 | 0.446 | −0.017 | — |
| OOS | 4 | 17 | 719 | 0.412 | 0.476 | −0.064 | — |
| OOS | 8 | 15 | 672 | 0.333 | 0.442 | −0.109 | — |
| OOS | 16 | 13 | 584 | 0.538 | 0.447 | +0.092 | — |

Cannot award `ND_SIGNATURE_ADDS`. Cannot change the primary label.

Artifact: `results/contrast_C_vs_B.csv`.

---

## 4. Companion outcome — `FAIL_CLEAR_ND` (descriptive only)

`FAIL_CLEAR_ND(H) = 1` iff `max(high[t_confirmation+1 … t_confirmation+H]) ≤ high[t_event]`.

Cannot alone award `SUPPORTED`.

### C vs A (selected)

| Split | H | p_C | p_A | Δ | IS p |
| --- | ---: | ---: | ---: | ---: | ---: |
| IS | 4 | 0.579 | 0.482 | +0.097 | 0.244 |
| IS | 8 | 0.469 | 0.308 | +0.161 | 0.055 |
| IS | 16 | 0.350 | 0.173 | +0.177 | 0.067 |
| Validation | 4–16 | mixed | mixed | ~0 / small | — |
| OOS | 4 | 0.471 | 0.445 | +0.025 | — |
| OOS | 8 | 0.333 | 0.357 | −0.024 | — |
| OOS | 16 | 0.385 | 0.210 | +0.175 | — |

IS shows modest positive Δ at longer horizons that does **not** clear α=0.05 and does **not** establish multi-split stability. Not a rescue.

Artifacts: `results/contrast_FAIL_CLEAR_C_vs_A.csv`, `results/contrast_FAIL_CLEAR_C_vs_B.csv`.

---

## Usable-path note

Segment-break / horizon incompleteness drops some rows:

| Class | Usable rate (event×horizon rows) |
| --- | ---: |
| A | 0.774 |
| B | 0.829 |
| C | 0.791 |

Longer H → fewer usable C rows (OOS H=16: n_C=13). Floor check uses **event counts** (C OOS=17), not horizon-usable counts.

---

## Interpretation (mechanism research, not trading)

1. **Formal answer:** `INCONCLUSIVE` because OOS C < 20 under the frozen gate.
2. **Mechanism pattern:** no horizon has same-sign Δ(C−A) across IS, Validation, and OOS. The only IS-significant cell (H=4) **reverses in OOS**.
3. **Background vs morphology:** C vs B likewise shows no stable multi-split edge.
4. **Do not retune** thresholds or switch to daily to chase support. That would be a new experiment.
5. **Do not promote a trading rule** from these tables.

---

## Explicit non-actions

- No parameter changes after outcomes.
- No Sharpe / PF / stops / targets.
- No claim that VSA “works” or “does not work” as a universal methodology — only that **this preregistered NQ/15m No Demand sequence** does not clear its frozen support gate, and the chronological sign pattern does not support a stable mechanism claim even before the OOS floor.
