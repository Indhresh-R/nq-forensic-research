# Step 6 Preregistration — Directionality mechanism decomposition (ExpExit)

**Status:** FROZEN BEFORE DECOMPOSITION ANALYSIS.  
**Parent:** Strategy 52 Steps 0–5.  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Mechanism decomposition audit only. **Not** a trading strategy.

Scope: **ExpExit only** (origin cells C vs D). No CompExit primary claims. No CEM expansion. No P&L / entries / stops / targets / continuation-reversal labels.

---

## Question

> What observable information distinguishes C from D **at the expansion→NORMAL transition**, and does the destination asymmetry track those underlying directionality *components* rather than only the composite origin label?

Wording target (associative only):

> ExpExit origin cell remains associated with subsequent destination behavior after controls…

Not: “we discovered the directional mechanism.”

---

## Important construction note (frozen)

Qualifying ExpExit episodes keep the same four-cell label until NORMAL. Therefore:

- At every bar in `[i0, te)`, C has `HIGH_DIRECTIONALITY` and D has `LOW_DIRECTIONALITY`.
- Continuous `ER_60` on `[i0, te)` **cannot overlap** across C vs D (HIGH is above the IS q67 cut; LOW is at/below q33).

So Step 6’s primary measurements are taken at the **event bar `te`** (first NORMAL), where directionality is *not* constrained by the origin cell definition and C/D can share overlapping component values.

Secondary diagnostics use `te-1` only to document the non-overlap fact.

---

## Components at `te` (causal)

From the Step 0 feature panel / contiguous 1m history ending at `te`:

| Component | Definition |
| --- | --- |
| `er_30`, `er_60`, `er_120` | Efficiency ratios at `te` |
| `signed_net_60` | `close[te] − close[te−60]` (segment-safe; NaN if broken) |
| `abs_net_60` | `|signed_net_60|` |
| `path_60` | \(\sum |Δclose|\) over the same 60 steps |
| `er_60_check` | `abs_net_60 / path_60` (must match `er_60` within tolerance when finite) |
| `er_60_change` | `er_60[te] − er_60[te−1]` |
| `signed_net_change_5` | `(close[te]−close[te−5])` (short transition impulse) |
| `directionality_state_te` | Step 0 label at `te` |

Primary stratification feature: **`er_60` at `te`**.  
One-at-a-time secondary: `path_60`, `|signed_net_60|`, `er_60_change` (each separately).

---

## Binning

IS ExpExit events only: tercile cuts (33%/67%) for each continuous component used in stratification. Apply frozen cuts to all splits.

Minimum-n for eligible within-bin claims: both C and D have `n_valid ≥ 200` at horizon 30m.

---

## Endpoints

Unchanged:

- `P(return_to_origin_range)`, `P(reach_opposite_range)`
- Contrast **`D − C`**
- Primary horizon **30m**; secondary **60m**

Also report:

1. **Balance / separation** of components at `te` (and `te−1` sanity) between C and D (means + SMD).
2. **Within-bin D−C** destination contrasts for each frozen stratification.
3. Whether destination rates are **monotonic** in the continuous component within C and within D separately (descriptive).

---

## Predeclared interpretation

| Result | Meaning |
| --- | --- |
| **LABEL_RESIDUAL** | Within eligible `er_60[te]` terciles, D−C destination asymmetry **remains** (same sign as pooled; not collapsed below half magnitude on both endpoints) | Origin cell still associates with destination beyond contemporaneous ER at `te` |
| **COMPONENT_ACCOUNTS** | Within eligible `er_60[te]` terciles, asymmetry **disappears/collapses** on both endpoints | Residual association is largely the ER level *at the transition*, not an extra C/D label effect |
| **CONDITIONAL** | Remains in some component regions only | Destination link is conditional on the transition ER (or other component) regime |
| **PATH_OR_NET** | `er_60[te]` does not account for it, but `path_60` or `|signed_net_60|` strata do | Points to a specific ER numerator/denominator channel |

---

## Forbidden

- Re-optimizing matches / adding covariate fishing
- CompExit as a primary claim
- Trade construction; calling results a proven causal mechanism
- Using post-`te` path features as “components”

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step6_components.parquet` | Per-event components at te / te-1 |
| `results/step6_cuts_frozen.json` | IS tercile cuts |
| `results/step6_balance.csv` | C vs D component SMDs |
| `results/step6_within_bin_contrasts.csv` | D−C by component bin |
| `results/step6_monotonicity.csv` | Within-cell destination vs component |
| `results/step6_verdict.json` | Classification |
| `results/step6_audit.json` | Scope audit |
| `STEP6_DIRECTIONALITY_DECOMPOSITION.md` | Report |

---

## Verdict format

**STEP 6 VERDICT** with the classifications above, then **NEXT RESEARCH QUESTION** (still not a trade).
