# Step 3 Preregistration — Destination asymmetry: stability + orthogonal conditioning

**Status:** FROZEN BEFORE DESTINATION CONDITIONING ANALYSIS.  
**Parent:** Strategy 52 Steps 0–2 (labels, cells, →NORMAL events, path metrics frozen).  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Mechanism description only. **Not** a trading strategy.

No entries, exits, stops, targets, signed P&L, win rates, or optimization.

---

## Question

Is the Step 2 **destination / recycling asymmetry** after →NORMAL events:

1. reasonably **persistent across chronological splits**,
2. **not merely a wait-to-NORMAL confound**,
3. still present after conditioning on **one** prespecified orthogonal covariate at the event bar?

We are **not** asking which covariate maximizes a difference.

---

## Primary endpoints (frozen)

For valid path horizons, destination indicators from Step 2:

| Endpoint | Column |
| --- | --- |
| Return to origin range | `returned_to_origin_range` |
| Reach opposite range | `reached_opposite_range` |

**Primary horizon:** **30 minutes**.  
**Secondary horizon:** **60 minutes** (reported; not used to retune anything).

Contrasts:

| Contrast | Events |
| --- | --- |
| CompExit | A→NORMAL vs B→NORMAL (`B − A`) |
| ExpExit | C→NORMAL vs D→NORMAL (`D − C`) |

Report for each: rates, difference, sample sizes, and uncertainty intervals.

---

## Chronological splits

Reuse `common.splits` / event `session_year`:

| Split | Years |
| --- | --- |
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 (partial) |

Persistence criterion (predeclared): the **sign** of the primary-horizon destination difference matches in IS, Validation, and OOS (when each split has enough events; see minimum-n rule). Approximate magnitude need not be identical.

---

## Wait-to-NORMAL stratification (confounder diagnostic)

**Freeze boundaries before inspecting destination contrasts by wait.**

Within each family (`CompExit`, `ExpExit`), on **IS events only**, compute wait-to-event tercile cuts (33% / 67%).

| Stratum | Rule |
| --- | --- |
| SHORT | wait ≤ IS q33 |
| MEDIUM | IS q33 < wait ≤ IS q67 |
| LONG | wait > IS q67 |

Apply the same frozen cuts to Validation / OOS.

Interpretation: if CompExit or ExpExit destination separation **changes sign or collapses toward zero in every wait stratum**, treat the pooled cell effect as potentially a **time-in-state** confound rather than origin-directionality.

---

## Orthogonal covariates (one at a time)

All measured at the **event bar** `te` only, using Step 0 frozen labels / TOD blocks. No future information. No crossed combinations in this step.

### Volatility (`volatility_state`)

`LOW_VOLATILITY` / `NORMAL_VOLATILITY` / `HIGH_VOLATILITY`

### Volume (`volume_state`)

`LOW_VOLUME` / `NORMAL_VOLUME` / `HIGH_VOLUME`

### Time-of-day (exclusive blocks)

| Block | `ny_min` |
| --- | --- |
| FIRST_30 | [09:30, 10:00) |
| 1000_1200 | [10:00, 12:00) |
| 1200_1400 | [12:00, 14:00) |
| 1400_1600 | [14:00, 16:00) |

For each covariate level, report the same A/B or C/D destination contrast **within that level**.

---

## Minimum-n rule (frozen)

A split- or stratum-level contrast is **eligible for persistence / conditioning claims** only if **both** origin cells have `n_valid ≥ 200` at the primary horizon.

Smaller cells may be shown descriptively but marked `UNDERPOWERED`.

---

## Uncertainty

For each rate: Wilson 95% interval.  
For each difference of rates: Newcombe–Wilson 95% interval for two independent proportions (unpaired).

Uncertainty is descriptive support, not a license to hunt alternatives.

---

## Predeclared “interesting” criteria

A destination asymmetry is treated as **interesting (mechanism-surviving)** only if:

1. Present in **pooled** primary-horizon data with the same sign as Step 2, and  
2. **Same sign** across IS / Validation / OOS among eligible splits, and  
3. Not confined to a single tiny / underpowered subgroup, and  
4. Not eliminated as a pure wait confound (separation does not vanish uniformly across SHORT/MEDIUM/LONG).

Failing these is also a useful result.

---

## Forbidden

- Building trades from destination asymmetries
- Searching covariate combinations
- Re-cutting wait terciles after seeing destinations
- Re-labeling Step 0 states
- Claiming profitability

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step3_wait_cuts_frozen.json` | IS wait terciles by family |
| `results/step3_split_stability.csv` | Destination contrasts by split |
| `results/step3_wait_strata.csv` | Contrasts by wait stratum |
| `results/step3_orthogonal.csv` | Contrasts by single covariate |
| `results/step3_verdict.json` | Machine-readable criteria checklist |
| `results/step3_audit.json` | Scope audit |
| `STEP3_DESTINATION_STABILITY.md` | Report |

---

## Verdict format

**STEP 3 VERDICT** against the predeclared criteria, then **NEXT RESEARCH QUESTION** (still not a trading rule).
