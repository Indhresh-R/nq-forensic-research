# Patrick VA Step 2 — Distance-Matched First-Passage Null

**Status:** EXECUTED — verdict `KILL` (code A).  
**Parent:** Strategy 63 Step-1 strict VA first-passage (v2).  
**Class:** Mechanism diagnostic only. **NO TRADE. NO P&L. NO promote.**

---

## Objective

Determine whether the observed strict-primary first-passage asymmetry (Δ) contains information beyond the mechanical effect of unequal barrier distances.

---

## Frozen from Step 1 (immutable)

| Item | Value |
| --- | --- |
| Event file | `63_patrick_strict_va_first_passage/results/events_strict_va.parquet` |
| Subgroup | `strict_primary` only (`subgroup == "strict"`) |
| n | **338** (must match audit) |
| Levels | prev_VAH / prev_VAL |
| Stack | VP + size; **TPO = false** |
| Resolution | trade_level (observed labels already fixed) |
| H_CAP | 60 minutes |
| Barriers | each event keeps its Step-1 `dist_into`, `dist_away` |
| Timestamps | Step-1 `ts_event` unchanged |
| Terciles | **reuse** Step-1 `pd.qcut(dist_ratio, 3 → T1_low, T2_mid, T3_high)` — do not redefine |
| same_print_both | must remain 0 on strict |

Do **not** rebuild onsets, retune `(q,N)`, change away frac, or alter outcomes.

---

## Null construction (frozen)

### Claim the null represents

A **directionally symmetric** (zero-drift) continuous price path, conditional on each event’s own `(dist_into, dist_away)` and the same **H_CAP = 60m** horizon.

Not 50/50. Not a pooled coin flip. Not a null that edits barrier distances.

### Process model

For event \(i\), map onset price to 0:

- **Into** barrier at \(-d^{\mathrm{into}}_i\)
- **Away** barrier at \(+d^{\mathrm{away}}_i\)
- \(dX_t = \sigma_i \, dW_t\) (arithmetic BM, **drift = 0**)
- Absorb on first hit of either barrier
- If no hit by \(T = 3600\)s → `unresolved`

Orientation matches Step-1 semantics (into = toward prior POC; away = exterior). Signs are a coordinate choice; distances are the Step-1 magnitudes.

### Volatility \(\sigma_i\) (causal, not tuned to Δ)

| Rule | Value |
| --- | --- |
| Window | \([t_0 - 30\mathrm{m},\, t_0)\) — **pre-event only** |
| Estimator | Std of consecutive 1-second last-trade price differences in that window (points / √s) |
| Floor | `max(σ̂, TICK)` with `TICK = 0.25` |
| Missing / thin window (< 30 one-second diffs) | fill with **median** of finite event-level \(\sigmâ\) on the strict sample (computed once, then locked for all sims) |
| Forbidden | any price at or after \(t_0\); any calibration to match observed Δ or unresolved rate |

\(\sigma\) is a **nuisance** for finite-horizon unresolved mass. It is **not** optimized after seeing Δ.

### Monte Carlo

| Parameter | Frozen value |
| --- | --- |
| `SEED` | `20260923` |
| `N_SIM` | `10_000` |
| `DT_SEC` | `15.0` (Euler–Maruyama; frozen for tractability — not tuned to Δ) |
| `H_CAP_SEC` | `3600` |
| Same-step both barriers | assign `away_first` (matches Step-1 same-print → away) |

For each simulation \(s = 1..N_{\mathrm{SIM}}\):

1. For every strict event \(i\), simulate one path under \((\sigma_i, d^{\mathrm{into}}_i, d^{\mathrm{away}}_i, T)\).
2. Record null outcome ∈ {`into_first`, `away_first`, `unresolved`}.
3. Compute \(\Delta^{(s)} = \hat p_{\mathrm{into}}^{(s)} - \hat p_{\mathrm{away}}^{(s)}\) on the full n=338 sample.

Observed labels are **never** overwritten; null outcomes live only in simulation arrays.

### Primary statistic

\[
\Delta = P(\texttt{into\_first}) - P(\texttt{away\_first})
\]

Compare **observed Δ** to \(\{\Delta^{(s)}\}\).

Report: null mean, 2.5% / 97.5% percentiles (95% interval), empirical two-sided p-value

\[
p = 2 \min\bigl( \tfrac{1}{N}\#\{\Delta^{(s)} \le \Delta_{\mathrm{obs}}\},\;
\tfrac{1}{N}\#\{\Delta^{(s)} \ge \Delta_{\mathrm{obs}}\},\; 0.5 \bigr).
\]

Repeat the same observed-vs-null comparison **within** each frozen dist_ratio tercile (separate null Δ distribution using only events in that tercile; same paths / same seed stream discipline: simulate full sample once, slice by tercile).

---

## Interpretation (frozen)

| Code | Rule |
| --- | --- |
| **A — KILL** | Observed Δ statistically consistent with the distance-matched null (two-sided p ≥ 0.05 **or** Δ_obs inside null 95% interval). Pooled asymmetry explainable by barrier geometry. |
| **B — ADVANCE_TO_STEP_3** | Observed Δ **significantly more negative** than the null (Δ_obs < null 2.5% percentile) **and** the excess-away direction is **coherent** in preregistered terciles: at least **2 of 3** terciles have Δ_obs < null mean for that tercile, and **no** tercile has Δ_obs significantly *more positive* than its null (Δ_obs > null 97.5%). |
| **C — INCONCLUSIVE** | Only one tercile is extreme while others are null-consistent / opposite; do not select that tercile. |

If A and B predicates both fail but the pattern is messy → **C**.

No trade test under any outcome.

---

## Audit checklist

- [ ] n_strict = 338
- [ ] Event timestamps unchanged vs Step-1 file
- [ ] `dist_into` / `dist_away` unchanged vs Step-1 file
- [ ] `same_print_both` count = 0
- [ ] No post-event prices enter σ
- [ ] Null simulation does not alter observed labels or sample selection
- [ ] Tercile edges not redefined

---

## Outputs

| Path | Role |
| --- | --- |
| `results/STEP2_DISTANCE_MATCHED_NULL_REPORT.md` | Full report + verdict |
| `results/step2_null_summary.json` | Machine summary |
| `results/step2_null_deltas.parquet` | Per-sim Δ (pooled + terciles) |
| `results/step2_audit.json` | Audit flags |
| `results/step2_event_sigma.parquet` | Locked causal σ_i used |

---

## Explicit non-goals

- No trade / P&L / cost gate  
- No TPO  
- No new VA definitions  
- No subgroup discovery beyond frozen terciles  
- No retune of Step-1 barriers or H_CAP  
- No 50/50 null as primary  
