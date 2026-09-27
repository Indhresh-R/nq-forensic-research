# Strategy 53 — Regime-Conditioned Strategy Family Screening

**Status:** FROZEN BEFORE SCREENING EXECUTION.  
**Namespace:** `strategies/53_regime_strategy_screen/`  
**Parent:** Strategy 52 Market State Census (labels/thresholds frozen; not re-fit).

---

## Objective

> Market state is a **routing / regime variable**, not a trading strategy.

Screen whether simple strategy families show positive path/expectancy **only inside** the market condition where their mechanism should plausibly operate.

This is **not** a final strategy study. No parameter search. No rescue filters.

---

## Data

| Item | Freeze |
| --- | --- |
| Instrument | Continuous NQ 1m (`data/nq_1m_continuous.parquet` via Strategy 52 feature/state panels) |
| States | Strategy 52 `results/market_states.parquet` + `market_state_features.parquet` |
| Routing labels | Strategy 52 **independent flags** (not re-cut): `flag_trending`, `flag_chop`, `flag_compression`, `flag_expansion` |
| Analysis bars | `census_eligible` (RTH 09:30–16:00 ET, as in Strategy 52) |
| Cost | **1.0 NQ point** round-trip |
| Splits | IS 2010–2021 / Validation 2022–2024 / OOS 2025–2026 |

States are an **exogenous routing condition**. Do not choose the state after seeing P&L.

---

## Four primary cells (exactly these)

| Cell ID | Routing state (Strategy 52 flag) | Family | Representative rule |
| --- | --- | --- | --- |
| A | `flag_trending` (HIGH_DIRECTIONALITY) | continuation | Close vs open direction → hold 15m |
| B | `flag_chop` (LOW_DIRECTIONALITY / CHOP_RANGE flag) | mean reversion | Fade 60m mid when \|disp\| ≥ 0.5×ATR30 |
| C | `flag_compression` | breakout | Break prior 20m high/low |
| D | `flag_expansion` | exhaustion / reversal | Fade when \|move_5\| > 1.0×ATR30 |

Exact formulas are in §Frozen rules below. **No other variants.**

---

## Frozen rules

Common execution for all cells:

- Signal on completed bar `t` (causal features/states at `t` only)
- Entry: `open[t+1]` (skip if path/session/segment breaks)
- Exit: `close[t+15]` (or last contiguous bar before break)
- No stop, no target
- Gross = `side × (exit − entry)`; Net = gross − 1.0

### A — TRENDING / continuation

- Condition: `flag_trending[t]`
- Long if `close[t] > open[t]`; short if `close[t] < open[t]`; skip equals

### B — CHOP_RANGE / mean reversion

- Condition: `flag_chop[t]`
- `mid_60 = (HH_60 + LL_60) / 2` over bars `[t−59, t]` (segment-safe; require 60 bars)
- Require `|close[t] − mid_60| ≥ 0.5 × ATR_30[t]`
- Short if `close > mid_60`; long if `close < mid_60`

### C — COMPRESSION / breakout

- Condition: `flag_compression[t]`
- Long if `close[t] > max(high[t−20:t−1])`; short if `close[t] < min(low[t−20:t−1])`
- Require 20 prior contiguous bars in segment

### D — EXPANSION / exhaustion

- Condition: `flag_expansion[t]`
- `move_5 = close[t] − close[t−5]`
- Long if `move_5 < −1.0 × ATR_30[t]`; short if `move_5 > +1.0 × ATR_30[t]`
- Do **not** reuse Strategy 52 Step 9 ExpExit fade

---

## Baselines (diagnostic; not for optimization)

1. **Shuffle-side:** same signal timestamps; sides randomly permuted (seed **53**); same exits.
2. **All-bars long / all-bars short:** every census-eligible bar in the routing state; same 15m horizon; report mean net separately for forced long and forced short.

---

## Path metrics

Per trade, with side-aware definition from entry:

- MFE_5 / MFE_15: max favorable excursion over bars from entry through `t+5` / `t+15`
- MAE_5 / MAE_15: max adverse excursion over the same windows

---

## Classification (per cell, independent — no ranking)

| Class | Rule |
| --- | --- |
| **PROMISING** | Primary arm `mean_net > 0` on IS, Validation, and OOS; each split `n ≥ 200` |
| **REJECTED** | `mean_net ≤ 0` on **both** IS and Validation |
| **PATH-ONLY** | Not PROMISING; IS `mean_net ≤ 0`; median MFE_15 ≥ **5.0** pts and median MFE_15 ≥ **2 × \|mean_net\|** on IS |
| **INCONCLUSIVE** | Anything else (unstable signs, thin sample, etc.) |

Priority if multiple could apply: PROMISING → PATH-ONLY → REJECTED → INCONCLUSIVE.

---

## Forbidden

Parameter search; extra filters; VWAP/CVD/MBO/SMT; changing cost/horizon/thresholds after results; ranking cells as best/worst; treating state itself as the trade; continuing Strategy 52 mechanism decomposition here.

---

## Outputs

| Path | Role |
| --- | --- |
| `results/trades.parquet` | Trade ledger (all cells) |
| `results/summary_by_split.csv` | Cell × split metrics |
| `results/summary_by_year.csv` | Cell × year net |
| `results/baselines.csv` | Shuffle + all-bars baselines |
| `results/path_metrics.csv` | MFE/MAE summaries |
| `results/verdict.json` | Per-cell classification |
| `results/audit.json` | Leakage audit |
| `results/REGIME_STRATEGY_SCREEN.md` | Report |

---

## Final question

> Does routing simple, mechanically representative strategy families into the market conditions for which they are theoretically appropriate produce enough evidence to justify deeper research?
