# Strategy 55 — Price-Path Event Screen (research contract)

**Status:** FROZEN CONTRACT BEFORE ANY EVENT IS SELECTED.  
**Namespace:** `strategies/55_price_path_events/`  
**Parent boundary:** `strategies/RESEARCH_LEDGER_52_54.md`

---

## What this project is

A **new mechanism search** one level closer to price behavior.

Market state from Strategies 52–54 may be reported as **context only**. It must not define the hypothesis unless the chosen event definition itself requires a frozen state clause.

---

## What this project is not

- Not a rescue of Strategy 52 / 53 / 54
- Not `STATE → GENERIC STRATEGY`
- Not transition→magnitude screening of census labels
- Not a multi-step decomposition tree

---

## Research architecture (hard)

```text
PRICE-PATH EVENT
       ↓
Does it create a stable destination asymmetry?
       ↓
Is the effect stable across IS / Val / OOS?
       ↓
Can one simple fixed execution capture it?
       ↓
       KILL / ADVANCE
```

### Step budget (hard)

**Maximum 2–3 diagnostic steps before one executable test.**

| Step | Allowed question | Forbidden |
| --- | --- | --- |
| 1 | Define one objective event; measure destination asymmetry | Extra indicators, filters, optimization |
| 2 | Chronological stability (IS / Val / OOS) | Subgroup shopping |
| 3 (optional) | Path feasibility (size/timing vs cost scale) | Mechanism rabbit holes |
| Then | **One** simple fixed trade | Adding VWAP/CVD/ATR/TOD/second target after failure |

If the trade fails → **KILL that event.** No rescue stack.

---

## Core research question

> After this objectively defined **price-path event**, where does price actually go — and can one simple fixed execution capture a stable destination asymmetry under realistic NQ costs?

---

## Candidate event families (hypothesis menu — not yet selected)

Exactly one family is chosen **before** any outcome is computed. Do not run all four and pick the winner.

1. **Displacement → retracement**  
   Large directional move; first meaningful retracement; preferential destination?

2. **Range break → failed return**  
   Exit a defined range; return inside; where afterward?

3. **Impulse → partial retracement**  
   Impulse then retrace 25/50/75% of impulse; does reaching one zone change reach probabilities for another?

4. **Extreme excursion → rejection**  
   Unusually large excursion from a reference; rejection; revisit origin / mid / opposite?

These are **event hypotheses**, not strategies.

---

## Execution test rules (when an event graduates)

Frozen defaults unless a single alternative is written in that event’s prereg **before** P&L:

| Element | Default |
| --- | --- |
| Entry | `open[t+1]` after event bar `t` |
| Exit | fixed horizon **or** one structure target — not both grids |
| Cost | **1.0** NQ point round-trip |
| Stops/targets | none, or one predeclared pair — no search |
| Gate | `E_net > 0` on IS **and** Validation **and** OOS (min n per split frozen per event) |

Forbidden after seeing results: VWAP, CVD, volume, ATR filter, time filter, second target, second entry, state-routing rescue.

---

## Chronological splits (unchanged)

| Split | Years |
| --- | --- |
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

---

## Selection of Event A

Before any code runs on outcomes:

1. Write `EVENT_A_PREREGISTRATION.md` naming **exactly one** family from the menu
2. Freeze event definition, destinations, horizons, and trade rule (if advancing)
3. Only then compute asymmetries / P&L

Until Event A is named, this folder is a **contract only**.

---

## Relationship to Strategies 52–54

| Prior result | Implication here |
| --- | --- |
| 53 all REJECTED | Do not route generic families from coarse states |
| 54 no clean path-magnitude candidate | Do not trade activity transitions |
| 52 Step 9 KILL | Do not rescue ExpExit fade-to-mid |

State may appear in reports as context columns; it is not the edge claim.
