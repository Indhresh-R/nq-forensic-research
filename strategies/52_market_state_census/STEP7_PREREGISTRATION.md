# Step 7 Preregistration — Low-transition-ER origin-history decomposition

**Status:** FROZEN BEFORE HISTORY ANALYSIS.  
**Parent:** Strategy 52 Steps 0–6.  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Mechanism decomposition audit only. **Not** a trading strategy.

Scope: **ExpExit C vs D only**, restricted to the **low `ER_60[te]` regime** identified in Step 6.  
No CompExit primary claims. No new CEM. No P&L / entries / stops / targets / directional trade labels.  
Do **not** call low ER “reversal,” “failed trend,” or “exhaustion.”

---

## Question

> Among ExpExit events with low `ER_60[te]`, does pre-event origin-episode history still explain the C/D destination difference?

Associative wording target:

> When an expansion exits into NORMAL at low transition ER, the origin C/D cells remain associated with different subsequent destination behavior…

Not: “we discovered the directional mechanism” / not a trade.

---

## Population (frozen)

1. Family = ExpExit (origin cells C, D).
2. Low transition ER: `te_er_60 ≤` the **already-frozen** Step 6 IS tercile cut  
   `step6_cuts_frozen.json → features.te_er_60.q33`.
3. Do **not** re-estimate the low-ER threshold after seeing destinations.
4. Join `te_er_60` from Step 6 components (or identical causal recompute at `te`).

Reference pooled contrast for this step: unmatched D−C among this **low-ER ExpExit** population at horizon 30m (not the all-ExpExit pooled).

---

## Primary history feature (frozen)

**Expansion duration before exit** (bars):

\[
\text{duration\_bars} = t_e - i_0 = \texttt{wait\_to\_event}
\]

Strictly pre-`te` (onset through last non-NORMAL bar before the event length).  
This is the **sole primary** stratification for the Step 7 verdict.

### Why primary = duration

Step 6 showed contemporaneous transition ER matters. The next natural question is whether two low-ER exits differ because one followed a **long/established** expansion episode vs a **short** one — history of the expansion, not another event-bar scalar.

---

## Secondary history descriptors (balance / descriptive only)

Computed on `[i0, te)` for composition and SMD tables. **Not** used to cherry-pick the primary classification:

| Feature | Definition |
| --- | --- |
| `excursion_atr` | `(max(high)−min(low)) / ATR_30[te−1]` |
| `pre_er` | `|close[te−1]−close[i0]| / Σ\|Δclose\|` over `[i0, te)` |
| `max_ext_atr` | `max_t |close[t]−close[i0]| / ATR_30[te−1]` for `t ∈ [i0, te)` |
| `late_share` | late half net / (early half net + late half net); NaN if path broken |

Internal state-transition counts are **out of scope** for this step (not frozen as primary).

---

## Binning

On **IS low-ER ExpExit events only**, freeze tercile cuts of `duration_bars` (33% / 67%).  
Apply frozen cuts to all splits.  
Eligible within-bin claims: both C and D have `n_valid ≥ 200` at horizon 30m.

---

## Endpoints

Unchanged:

- `P(return_to_origin_range)`, `P(reach_opposite_range)`
- Contrast **`D − C`**
- Primary horizon **30m**; secondary **60m**

Also report:

1. Composition of C vs D across duration bins (within low-ER).
2. Balance / SMD of secondary history descriptors (C vs D).
3. Within-duration-bin D−C destination contrasts.

---

## Predeclared interpretation (primary = duration)

| Result | Meaning |
| --- | --- |
| **HISTORY_RESIDUAL** | Within all eligible duration terciles, D−C asymmetry **remains** (same sign as low-ER pooled; not below half magnitude on both endpoints) | Low-ER C/D association is not simply explained by expansion age |
| **HISTORY_ACCOUNTS** | Within all eligible duration terciles, asymmetry **collapses** on both endpoints | Duration accounts for the residual association |
| **CONCENTRATED** | Remains in some duration regimes only | Association is concentrated in a particular expansion-age type |
| **PROGRESSIVE** | Eligible ordered bins show a **monotonic** change in D−C (return and opposite both monotonic in magnitude or signed effect across T1→T3) | Trajectory age conditions the association progressively |

`PROGRESSIVE` is checked only when not all-keep / all-lose; if monotonicity holds under `CONCENTRATED`, upgrade label to `PROGRESSIVE`.

---

## Forbidden

- Re-cutting low-ER after outcomes
- Testing all candidate histories and selecting the “best” for the verdict
- CompExit primary claims; new CEM / covariate fishing
- Trade construction; “exhaustion / reversal” language
- Post-`te` path features as history

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step7_population.parquet` | Low-ER ExpExit events + history features |
| `results/step7_cuts_frozen.json` | IS duration terciles (+ recorded low-ER cut) |
| `results/step7_balance.csv` | C vs D history SMDs |
| `results/step7_composition.csv` | Duration-bin composition |
| `results/step7_within_bin_contrasts.csv` | D−C by duration bin |
| `results/step7_verdict.json` | Classification |
| `results/step7_audit.json` | Scope audit |
| `STEP7_ORIGIN_HISTORY.md` | Report |

---

## Verdict format

**STEP 7 VERDICT** with the classifications above, then **NEXT RESEARCH QUESTION** (still not a trade).
