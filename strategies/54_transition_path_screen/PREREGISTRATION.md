# Strategy 54 — Transition Path Screen

**Status:** FROZEN BEFORE SCREENING.  
**Namespace:** `strategies/54_transition_path_screen/`  
**Parents:** Strategy 52 (frozen states) + Strategy 53 (COMPLETE: coarse state→family routing failed).

---

## Objective

> Among the state transitions observed in the census, which transitions show a **sufficiently distinct subsequent path geometry** to justify one simple executable test later?

This is a **path-difference screen only**.

- No entries as a strategy
- No P&L / expectancy gate
- No generic family mapping
- No 9-step mechanism decomposition
- Kill uninteresting transitions **before** building a trade

Architecture:

```text
STATE CENSUS (52)
      ↓
TRANSITION CENSUS (this step)
      ↓
PATH DIFFERENCE vs stay-in-origin baseline
      ↓
ONLY INTERESTING TRANSITIONS
      ↓
(later) ONE SIMPLE EXECUTION
```

---

## Research question

What state are we **leaving**, what state are we **entering**, and does price path geometry in the next 5/15/30 minutes differ from simply remaining in the origin state?

---

## Data / freeze

| Item | Freeze |
| --- | --- |
| States | Strategy 52 `market_states.parquet` (not re-fit) |
| Bars | `census_eligible` RTH |
| Splits | IS 2010–2021 / Val 2022–2024 / OOS 2025–2026 |
| Horizons | **5, 15, 30** minutes (fixed) |
| Path start | Strictly after event bar `t` (`t+1 … t+h`) |

---

## Two preregistered transition catalogs

### Catalog R — `range_state` transitions

States: `COMPRESSION`, `NORMAL_RANGE`, `EXPANSION`.  
Directed off-diagonal transitions only (6 possible).

**Rationale:** Strategy 52 Steps 1–2 found the interesting structure around range-state exits (especially expansion→normal), not around coarse composite→family routing.

### Catalog C — `composite_primary` transitions

States: the seven mutually exclusive Strategy 52 primary labels.  
Directed off-diagonal transitions (42 possible).

**Rationale:** Systematic census of the primary composite map without strategy cherry-picking.

---

## Event definition (both catalogs)

At bar `t` (census-eligible):

1. Same `session_date` and `segment_id` as `t−1`
2. `ny_min[t] == ny_min[t−1] + 1`
3. `state[t] != state[t−1]` for the catalog’s state column

Event time = `t` (first bar of the destination state).  
`from_state = state[t−1]`, `to_state = state[t]`.

---

## Stay-in-origin baseline

For each transition type `from → to`, the matched baseline is:

> Census-eligible bars with `state[t] == from_state` **and** `state[t+1] == from_state` (origin persists at least one more bar), same split.

Path for baseline uses the same horizons from that bar (strictly after `t`).

This answers: *is the path after leaving different from the path when staying?*

---

## Path measurements (no trade side)

Over bars `(t, t+h]` when the horizon path is contiguous:

| Metric | Definition |
| --- | --- |
| `hl_range` | max(high) − min(low) |
| `abs_net` | \|close[t+h] − close[t]\| |
| `net` | close[t+h] − close[t] (descriptive only; not a trade) |
| `abs_max_excursion` | max( max(high)−close[t], close[t]−min(low) ) |

Report medians for transition events and stay baselines; primary contrast metric = **median `hl_range` at 15m**.

Secondary: median `abs_net` at 15m; median `|net|` context.

---

## Eligibility

For a transition type to be classifiable:

| Split | Minimum transition events with valid 15m path |
| --- | --- |
| IS | ≥ 500 |
| Validation | ≥ 200 |
| OOS | ≥ 100 |

If IS ineligible → `THIN` (not INTERESTing; not enough to test).

---

## Classification (per transition type, independent)

Primary contrast at 15m:

\[
\Delta = \mathrm{median}(hl\_range \mid \text{transition}) - \mathrm{median}(hl\_range \mid \text{stay baseline})
\]

Relative gap:

\[
g = \Delta / \max(\mathrm{median}(hl\_range \mid \text{stay}), 1.0)
\]

| Class | Rule |
| --- | --- |
| **INTERESTING** | Eligible IS+Val; \|g_IS\| ≥ **0.25**; sign(Δ_IS) == sign(Δ_Val); \|g_Val\| ≥ **0.15** |
| **UNSTABLE** | Eligible IS+Val; \|g_IS\| ≥ 0.25 but Validation sign disagrees or \|g_Val\| < 0.15 |
| **THIN** | Fails IS sample floor |
| **KILL** | Eligible IS but \|g_IS\| < 0.25 (path not distinct from staying) |

OOS is reported for description; **not** required to award INTERESTING (avoids waiting on thin 2025–26 cells), but INTERESTING types with OOS sign flip are footnoted `OOS_CAUTION`.

No ranking of “best transition.” No strategy built here.

---

## Forbidden

- Building trades / costs / stops / targets
- Choosing transitions after seeing which would win a backtest
- Adding filters to rescue KILL/UNSTABLE types
- Multi-step mechanism decomposition
- Re-opening Strategy 53 cells

---

## Outputs

| Path | Role |
| --- | --- |
| `results/transitions_R.parquet` | range_state transition events |
| `results/transitions_C.parquet` | composite_primary transition events |
| `results/path_contrast_R.csv` | per-type path vs stay |
| `results/path_contrast_C.csv` | per-type path vs stay |
| `results/verdict.json` | classifications |
| `results/audit.json` | leakage audit |
| `results/TRANSITION_PATH_SCREEN.md` | report |

---

## Next step (only if INTERESTING survives)

For each INTERESTING transition: **one** separate, preregistered simple execution test (Strategy 55+), kill/advance quickly. Not another census tree.
