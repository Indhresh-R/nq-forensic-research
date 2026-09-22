# Step 8 Preregistration — Path feasibility audit (low-ER ExpExit)

**Status:** FROZEN BEFORE PATH ANALYSIS.  
**Parent:** Strategy 52 Steps 0–7 (frozen).  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Path-feasibility audit only. **Not** a trading strategy. **Not** mechanism deepening.

---

## Objective

> Does the already-observed low-transition-ER ExpExit C/D destination asymmetry occur early enough and with sufficient raw price excursion to potentially support a simple executable hypothesis?

Answer is a go/no-go for **whether to construct one hypothesis later** — not whether a strategy works.

---

## Frozen population

Identical to Step 7:

- ExpExit only; event = first EXPANSION → NORMAL
- `te_er_60 ≤` Step 6 IS q33 (`≈ 0.1210191083`), not re-fit
- Origin cells C / D unchanged
- Expected counts: n ≈ 9,442 (C ≈ 4,529, D ≈ 4,913)

If population counts differ by more than 1% from these figures: **STOP**.

Load event_ids from `results/step7_population.parquet`. Do not re-filter.

---

## Horizons (fixed)

Exactly **5, 15, 30, 60** minutes. All path bars are strictly **after** `te` (`te+1 … te+h`).  
No horizon selection / optimization.

---

## Measurements (fixed)

### A. Raw price excursion (NQ points, vs `close[te]`)

No trade side is assigned. Report **upside** and **downside** excursions (not “favorable/adverse” P&L):

- `max_up` = max(high) − close_e over `(te, te+h]`
- `max_down` = close_e − min(low)
- `abs_max_excursion` = max(max_up, max_down)
- `net_displacement` = close[te+h] − close_e
- `hl_range` = max(high) − min(low)

Quantiles: mean, p10, p25, p50, p75, p90; fractions > 0 and exceeding descriptive point levels {5, 10, 15, 20} (not candidate stops/targets).

### B. Destination geometry (unchanged Step 2 definitions)

- return to origin range / reach opposite range by horizon
- C rate, D rate, D−C

### C. Destination timing (among events that reach within 60m)

- time_to_origin_range, time_to_opposite_range (minutes after te)
- median / p25 / p75; censor “not reached by 60m” from timing stats

### D. Competing path (within 60m)

Which occurs first: return_to_origin / reach_opposite / neither.  
Frequencies by C and D. No win/loss language.

### E. ATR context

Event-time `atr_e` distribution (raw NQ points) for scale context only.

### F. Chronological stability

Key metrics by IS / Validation / OOS with the **same** frozen population and low-ER cut. No refit.

### G. Cost context

Place median excursions beside project mid round-trip cost (**1.0 NQ point**; see `research_framework/execution_assumptions.md` / engine sanity mid scenario).  
No cost subtraction, no P&L, no expectancy.

---

## Predeclared classification (exactly one)

| Class | Rule (all clauses evaluated on valid paths; MIN_N=200 per cell where rates are claimed) |
| --- | --- |
| **PATH_FEASIBLE** | (1) At 15m **and** 30m: D−C return and opposite keep the same signs as the low-ER pooled 30m reference, with \|return_diff\| ≥ 0.05 and \|opposite_diff\| ≥ 0.05. (2) Median `hl_range` at 15m **and** 30m ≥ **5.0** NQ points (pooled). (3) Among events that reach either destination by 60m, median time to first destination ≤ **15** minutes (pooled). (4) At 30m, D−C return_diff has the **same sign** in IS, Validation, and OOS (each split eligible). |
| **PATH_UNSTABLE** | Pooled 30m destination association remains material (clause 1 at 30m), but clause (4) fails. |
| **PATH_WEAK** | Destination association present at 30m (same signs as reference, \|diff\| ≥ 0.05 both endpoints) but clause (2) or (3) fails. |
| **PATH_INCONCLUSIVE** | Insufficient eligible sample or censoring prevents evaluating the above. |

Priority if multiple could apply: INCONCLUSIVE → UNSTABLE → WEAK → FEASIBLE (first match in that order after checking INCONCLUSIVE/UNSTABLE/WEAK; else FEASIBLE).

Descriptive point levels {5,10,15,20} and the 5.0-point median-range bar are **not** strategy parameters.

---

## Forbidden

Stop/target/entry/holding optimization; threshold search; subgroup shopping; new features/filters; P&L; long/short/buy/sell language; constructing Step 9 hypothesis in this step.

---

## Decision

- `PATH_FEASIBLE` → may proceed to a **separate** Step 9 (one simple preregistered hypothesis).
- Otherwise → **STOP. Do not build a strategy.**

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step8_event_paths.parquet` | Per-event × horizon path rows |
| `results/step8_path_feasibility.csv` | Aggregated feasibility table |
| `results/step8_verdict.json` | Classification + decision |
| `results/step8_audit.json` | Leakage / population audit |
| `STEP8_PATH_FEASIBILITY.md` | Report |
