# Step 4 Preregistration — Matched transition experiment

**Status:** FROZEN BEFORE MATCHED DESTINATION ANALYSIS.  
**Parent:** Strategy 52 Steps 0–3 (events, destinations, wait cuts frozen).  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Mechanism description only. **Not** a trading strategy.

No entries, exits, stops, targets, signed P&L, or optimization of the matching recipe after seeing matched outcomes.

---

## Question

If ExpExit (and CompExit) transitions are made **more comparable on observable pre-event geometry**, does the destination asymmetry remain?

We are testing composition vs independent information — **not** causality in a structural sense, and **not** a directional trade rule.

---

## Primary contrast

| Contrast | Treatment coding | Diff |
| --- | --- | --- |
| **ExpExit (primary)** | D vs C | `D − C` |
| CompExit (secondary) | B vs A | `B − A` |

## Endpoints (unchanged)

| Endpoint | Horizon |
| --- | --- |
| `P(return_to_origin_range)` | **30m primary**, 60m secondary |
| `P(reach_opposite_range)` | **30m primary**, 60m secondary |

---

## Pre-event covariates (all known at or before `te`)

Event bar = first NORMAL (`te`). Pre-event window = bars `[i0, te)` (onset through last origin-range bar).

| Covariate | Definition |
| --- | --- |
| `wait_stratum` | Step 3 frozen IS wait terciles (family-specific) |
| `volatility_state` | Step 0 label at `te` |
| `volume_state` | Step 0 label at `te` |
| `tod_block` | Step 3 TOD block at `te` |
| `origin_run_bars` | Contiguous origin-range bars ending at `te-1` (same session/segment); may extend before episode onset |
| `pre_range_atr` | `(max high − min low)` over `[i0, te)` / `ATR_30[te-1]` |
| `pre_er` | Path efficiency over `[i0, te)` using closes (same ER construction as Step 1) |
| `dist_mid_atr` | `|close[te-1] − mid([i0,te))| / ATR_30[te-1]` |
| `dist_edge_atr` | Distance from `close[te-1]` to nearest edge of `[i0,te)` high/low, / `ATR_30[te-1]` |

No post-`te` information enters matching.

Continuous geometry covariates are coarsened into **IS terciles within family** (frozen before matched destination claims).

---

## Matching method (frozen): Coarsened Exact Matching (CEM)

**Stratum key** = exact cross of:

```text
wait_stratum × volatility_state × volume_state × tod_block
  × origin_run_tercile × pre_range_atr_tercile × pre_er_tercile
  × dist_mid_atr_tercile
```

(`dist_edge_atr` is reported for balance only; not in the primary stratum key — avoids over-fragmentation while remaining available for diagnostics.)

**Retain** strata with both origin cells present and `min(n_cell_a, n_cell_b) ≥ 5`.

**Estimator:** within-stratum rate difference, aggregated with weights `w_s = n_a,s + n_b,s` (ATE-style common-support CEM).

Also report:

- unmatched pooled difference (Step 3 replication),
- matched difference,
- fraction of events retained on common support,
- covariate balance (SMD) before vs after matching.

---

## Predeclared interpretation

| Outcome | Meaning |
| --- | --- |
| **A** | Matched difference remains same sign and `|matched| ≥ 0.5 × |unmatched|` on primary endpoint(s) | Origin directionality still carries destination information after geometry matching |
| **B** | Matched difference shrinks below half unmatched **or** loses sign | Effect was largely compositional |
| **C** | Difference survives the full CEM key but collapses when a **single** continuous geometry factor is added in a leave-one-in diagnostic | That factor is the leading compositional channel |

Leave-one-in diagnostics (report only; not for retuning): CEM keys that drop one continuous tercile at a time.

---

## Forbidden

- Directional trade hypotheses (“continuation/reversal”)
- Rebuilding the match to maximize the residual difference
- Using post-event path features in the match
- Calling survival “proof of causality”

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step4_pre_event_features.parquet` | Pre-event geometry per event |
| `results/step4_tercile_cuts_frozen.json` | IS geometry terciles |
| `results/step4_matched_estimates.csv` | Unmatched vs CEM estimates |
| `results/step4_balance.csv` | SMD before/after |
| `results/step4_leave_one_in.csv` | Diagnostic CEM variants |
| `results/step4_verdict.json` | A/B/C classification |
| `results/step4_audit.json` | Scope audit |
| `STEP4_MATCHED_TRANSITIONS.md` | Report |

---

## Verdict format

**STEP 4 VERDICT** using outcomes A/B/C above, then **NEXT RESEARCH QUESTION** (still not a trade).
