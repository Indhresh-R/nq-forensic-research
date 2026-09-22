# Step 1 Preregistration — State-transition / path-geometry mechanics

**Status:** FROZEN BEFORE PATH ANALYSIS.  
**Parent:** Strategy 52 Step 0 market-state census (labels and thresholds remain frozen).  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Mechanism description only. **Not** a trading strategy.

No entries, exits, stops, targets, signed trade P&L, win rates, or parameter optimization are allowed in this step.

---

## Question

Given the Step 0 census, **what path geometry tends to follow** each of four observable state combinations — without choosing a trade direction?

This replaces the narrower “only A → path” proposal with a **four-cell contrast**.

---

## Frozen state cells (from Step 0 labels)

| Cell | Range state | Directionality state |
| --- | --- | --- |
| **A** | `COMPRESSION` | `LOW_DIRECTIONALITY` |
| **B** | `COMPRESSION` | `MID_DIRECTIONALITY` **or** `HIGH_DIRECTIONALITY` |
| **C** | `EXPANSION` | `HIGH_DIRECTIONALITY` |
| **D** | `EXPANSION` | `LOW_DIRECTIONALITY` |

Labels use the Step 0 IS-frozen terciles. No re-thresholding.

Bars that are expansion + mid directionality (or compression/expansion with missing labels) are **out of the four-cell sample**; their prevalence is reported only as a residual count.

---

## Event unit

**Episode onset** within a `session_date`:

- Sort eligible RTH bars by time.
- A new episode starts when the four-cell label at bar `t` differs from the label at `t-1` (or `t` is the first eligible bar of the session).
- Only onsets whose cell ∈ {A, B, C, D} are events.

Rationale: using every minute would overweight long-lived episodes and induce dependence. Episode onsets describe **state starts**.

---

## Forward path rules (causal)

Horizons **H ∈ {5, 15, 30, 60}** minutes.

For an onset at index `t0` with close `C0`, high/low path uses bars **`t0+1 … t0+H`** (strictly subsequent).

A horizon is **valid** only if:

1. All H subsequent bars exist in the same `session_date`
2. `ny_min` increases by exactly 1 each step (no gap)
3. Same `segment_id` as `t0` (contiguous 1m segment)

Invalid horizons are excluded from that H’s metrics (not imputed).

---

## Frozen metrics (all unsigned / two-sided; no long/short)

Let path bars be `i = t0+1 … t0+H`.

| Metric | Definition |
| --- | --- |
| `net_move` | `Close[t0+H] − C0` |
| `abs_net` | `|net_move|` |
| `abs_net_atr` | `abs_net / ATR_30[t0]` |
| `max_up` | `max(High[i]) − C0` |
| `max_down` | `C0 − min(Low[i])` |
| `max_range` | `max(High[i]) − min(Low[i])` |
| `max_range_atr` | `max_range / ATR_30[t0]` |
| `er_forward` | `|Close[t0+H]−C0| / sum_{i=t0+1…t0+H} |Close[i]−Close[i−1]|` |
| `terminal_range_state` | `range_state` at `t0+H` |
| `terminal_dir_state` | `directionality_state` at `t0+H` |
| `still_compressed` | terminal range == COMPRESSION |
| `reached_normal` | any bar in path has NORMAL_RANGE |
| `reached_expansion` | any bar in path has EXPANSION |
| `still_expanded` | terminal range == EXPANSION |
| `left_expansion` | any bar in path has range ≠ EXPANSION (cells C/D) |
| `time_to_normal` | minutes to first NORMAL_RANGE in path; NaN if never |
| `time_to_expansion` | minutes to first EXPANSION in path; NaN if never |
| `time_to_leave_compression` | minutes to first non-COMPRESSION; NaN if never |
| `time_to_leave_expansion` | minutes to first non-EXPANSION; NaN if never |
| `expansion_is_directional` | if `reached_expansion`, directionality at **first** expansion bar is HIGH; else NaN |
| `expansion_is_two_sided` | if `reached_expansion`, directionality at first expansion bar is LOW; else NaN |

“Favorable / adverse” without a trade side are reported only as **`max_up`** and **`max_down`** (two-sided envelope). No signed edge claim.

---

## Contrasts (descriptive)

Primary:

1. **A vs B** — compression with low vs mid/high directionality  
2. **C vs D** — expansion with high vs low directionality  

Report counts, medians/means, and proportions by cell and horizon. Optionally stratify by IS / Validation / OOS **without** retuning.

---

## Forbidden

- Long/short rules, stops, targets, friction
- Selecting horizons or cells because a contrast “looks tradeable”
- Re-labeling Step 0 states
- Calling any cell an edge

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step1_episodes.parquet` | Episode onsets + cell |
| `results/step1_path_metrics.parquet` | Per-episode × horizon metrics |
| `results/step1_cell_summary.csv` | Aggregate tables |
| `results/step1_contrasts.json` | A vs B, C vs D summaries |
| `results/step1_audit.json` | Leakage / scope audit |
| `STEP1_PATH_GEOMETRY.md` | Report |

---

## Verdict format

End with **STEP 1 VERDICT** (which contrasts show different path geometry) and **NEXT RESEARCH QUESTION** (still not a trading rule).
