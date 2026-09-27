# Strategy 60 — Cost / Feasibility Reality Check

**Status:** FROZEN PREREG BEFORE COMPUTATION.  
**Namespace:** `strategies/60_cost_feasibility/`  
**Parent:** `strategies/RESEARCH_POSTMORTEM_52_59.md` (Frame A)  
**Not a trading strategy.** No new event. No retune of 52–59.

---

## Research question

> Under **cost = 1.0 NQ point RT** and the **simple execution class** used in 55–59 (fixed hold and/or single target vs adverse), what edge region is required for `mean_net > 0`, and do the **already frozen** 55–59 artifacts sit inside that region?

---

## What this uses (read-only)

| Source | Use |
| --- | --- |
| 55 `event_a_trade_summary.csv` | Empirical mean_gross / mean_net / hit_rate |
| 56 `event_b_trade_summary.csv` | Same |
| 57 `path_ladder_by_split.csv` | MFE vs MAE at 15m (IS) |
| 58 destination summary (report/verdict) | Wrong-sign Δ (context) |
| 59 `first_passage_by_split.csv` + `orb_events.parquet` | First-passage rates; R distribution for payoff math |
| Constants | `COST_RT = 1.0` only |

No re-extraction of events. No new P&L search.

---

## Analyses (frozen)

### A1. Break-even algebra (cost C = 1.0)

For a trade with win size `W`, loss size `L` (both > 0, points), win prob `p`:

```text
E[gross] = p·W − (1−p)·L
E[net]   = E[gross] − C
Break-even p* = (L + C) / (W + L)
```

Report p* for a grid of `(W, L)` relevant to NQ 1m (e.g. W,L ∈ {2,4,6,8,10,15,20}).

### A2. Symmetric-path implication

If MFE ≈ MAE and signed close progress ≈ 0 (as in 57), then for fixed-horizon holds:

```text
E[gross] ≈ 0  ⇒  E[net] ≈ −C = −1.0
```

Classify 55/56 empirical gross against this null.

### A3. First-passage payoff envelope (ORB-class)

Using Strategy 59 geometry **as a payoff model only** (not a retune):

- Approximate win = distance entry→target  
- Approximate loss = distance entry→adverse  
- Empirical `p_target_first` from 59  
- Required `p*` from A1 using median R and median distances from `orb_events` + first-passage paths if needed  

Compare required `p*` vs observed `p_target_first`.

### A4. Inventory table

One row per of 55, 56, 57 (path), 59 (fp): what failed, empirical gross or Δ_fp / MFE−MAE, distance to break-even.

---

## Verdict rules (preregistered)

| Verdict | Condition |
| --- | --- |
| `CLASS_STRUCTURALLY_UNDERWATER` | 55 & 56 both have \|IS mean_gross\| ≤ 0.25 **and** 57 IS med_mfe_15 within 10% of med_mae_15 **and** 59 IS p_target_first < p*_ORB (from A3) |
| `NARROW_FEASIBLE_REGION` | A3 shows some `(W,L)` with p* ≤ 0.55 **and** observed path class is not symmetric (57 fails the MFE≈MAE test) — should not trigger given known results; included for completeness |
| `MIXED` | Neither clean package |

**Action implication (written into report, not optional):**

- If `CLASS_STRUCTURALLY_UNDERWATER` → **moratorium** on new simple event→hold / event→1R-extension mechanisms until Frame B or C is explicitly chosen  
- Do **not** start Strategy 61 as another event

---

## Forbidden

- New event definitions  
- Re-running 55–59 trades with new exits  
- Declaring a strategy ADVANCE from this file  
- Using feasibility math to justify shopping horizons on killed ideas  

---

## Outputs

| Path | Role |
| --- | --- |
| `results/breakeven_grid.csv` | p* by W,L |
| `results/inventory_55_59.csv` | Empirical summary |
| `results/orb_payoff_envelope.json` | Required vs observed p |
| `results/verdict.json` | CLASS_* / MIXED |
| `results/FEASIBILITY_REPORT.md` | Report |

---

## Decision record

**Frame A chosen** over B/C because the interesting question is whether the hunt class is solvent under cost + observed path symmetry — before designing another mechanism.
