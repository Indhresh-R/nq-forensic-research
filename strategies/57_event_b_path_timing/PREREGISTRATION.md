# Strategy 57 — Event B Path / Timing Diagnostic

**Status:** FROZEN PREREG BEFORE ANY PATH METRIC OR P&L COMPUTATION.  
**Namespace:** `strategies/57_event_b_path_timing/`  
**Parent boundary:** `strategies/RESEARCH_LEDGER_52_54.md`  
**Upstream (frozen, do not retune):** Strategy 56 Event B

---

## What this is

A **path / timing** study on the **already frozen** Event B object.

It answers research question **#2** from the ledger lesson (destination ≠ path ≠ monetization).

It does **not** reopen Event B’s 15m trade. It does **not** shop exit horizons for P&L.

---

## What this is not

- Not a rescue of Event A or Event B monetization
- Not Family 3 / 4
- Not horizon optimization (`try H ∈ {5…60}` and pick best expectancy)
- Not a new event definition
- Not CVD / VWAP / ATR / TOD / state filters

---

## Research question (single)

> After Event B, does price produce a **monotonic directional path** toward its **already predicted** destination over the frozen ladder `5 → 15 → 30 → 60` minutes?

Those four horizons are **path diagnostics**, not four trade candidates.

---

## Upstream freeze (inherited, immutable)

| Item | Source | Value |
| --- | --- | --- |
| Event definition | Strategy 56 `PREREGISTRATION.md` | Range break → failed return (`W=60`, `H_wait=60`, return rule as written) |
| Destinations | Strategy 56 | `reach_opposite`, `reach_mid`, `rebreak_outside` (`0.25×R`) |
| Predicted destination | Strategy 56 IS sign of Δ | **`toward_rebreak`** (`trade_side_rule` frozen in `event_b_verdict.json`) |
| Predicted side | Strategy 56 | Up-break → long; down-break → short |
| Event ledger | Prefer reuse | `56_range_break_failed_return/results/event_b_events.parquet` if present and schema-compatible; else rebuild with **identical** constants |

Do **not** change `W`, `H_wait`, rebreak buffer, return rule, or predicted side after this file is frozen.

---

## Sample / continuity

Same as Strategy 56: contiguous 1m NQ; `session_date` / `segment_id` / `ny_min` continuity; event bars `census_eligible` (RTH 09:30–16:00 ET). Forward path bars must remain contiguous within segment; else censor that path for affected horizons.

---

## Splits

| Split | Years |
| --- | --- |
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

---

## Path metrics (frozen — no P&L)

Reference at event bar `t`:

- `c0 = close[t]`
- `R` = event range width (from Strategy 56)
- `side = +1` (toward rebreak / long after up-break) or `−1` (short after down-break)

Ladder: **`H ∈ {5, 15, 30, 60}`** exactly.

### Primary series (one number per event × H)

**Signed close progress** (range-normalized):

```text
prog_close[H] = side × (close[t+H] − c0) / R
```

Require finite `R > 0` and contiguous path through `t+H`; else missing for that H.

### Secondary (report only — not gates)

| Metric | Definition |
| --- | --- |
| `mfe_dir[H]` | `side × (best favorable extreme − c0) / R` over `(t, t+H]` (up-side: max high; down-side: min low) |
| `mae_dir[H]` | adverse excursion / R over same window (positive = against predicted side) |
| `hit_rebreak[H]` | 1 if `rebreak_outside` touched by H (Strategy 56 definition) |
| `first_rebreak_bars` | bars from `t` to first rebreak touch; null if none by 60 |

Secondary tables may include split × H rates already implied by destination math; they are descriptive.

---

## Aggregates per split

For each split and each `H` in the ladder, compute on valid `prog_close[H]`:

| Aggregate | Symbol |
| --- | --- |
| Count | `n[H]` |
| Median | `med[H]` |
| Mean | `mean[H]` |
| Fraction `prog_close[H] > 0` | `p_pos[H]` |

**Monotonicity score (IS primary claim object):**

```text
mono = (med[5] ≤ med[15]) ∧ (med[15] ≤ med[30]) ∧ (med[30] ≤ med[60])
```

Strict equality allowed (non-decreasing). Missing any of the four medians → fail that split’s mono test.

---

## Gates (path only — no trade)

### Step 1 — IS directional + monotonic

Require all of:

1. `n[H] ≥ 500` for every `H ∈ {5,15,30,60}`
2. **Directional end:** `med[60] > 0`
3. **Monotonic ladder:** `mono == True` on IS medians
4. **Not only terminal:** `med[15] > 0` **or** `med[30] > 0`  
   (blocks “flat/negative until a single late jump” from counting as a clean path without mid-ladder support)

Else → **`PATH_KILL`**.

### Step 2 — Val / OOS stability

Require for **Validation** and **OOS** separately:

1. `n[H] ≥ 200` (Val) / `≥ 100` (OOS) at every H
2. `med[60] > 0`
3. `mono == True`

If either Val or OOS fails → **`PATH_KILL`**.  
If both pass → **`PATH_ADVANCE`**.

No other subgroup cuts. No horizon dropping. No redefinition of `side`.

---

## Explicit non-goals in this run

| Forbidden here | Why |
| --- | --- |
| Any trade / expectancy / hit-rate P&L | Monetization is question #3; requires a **new** prereg after path verdict |
| Choosing “best H” from `mean[H]` or `p_pos[H]` | Horizon optimization |
| Retuning Event B or predicted side | Rescue |
| Declaring prop suitability | Separate constraint; see below |

---

## Prop / session constraint (declared, not tested here)

A path that concentrates progress at **45–60m** may be real and still poorly suited to a **short NY-AM** book. That is an **explicit monetization design choice**, not something inferred by shopping hold times in this diagnostic.

If and only if `PATH_ADVANCE`, a **future** monetization prereg may pick **one** of:

- short-hold rule matched to early-ladder progress, **or**
- longer-hold rule matched to late-ladder progress, **or**
- kill for prop-timing mismatch without a trade test

…written **before** P&L. Not in Strategy 57.

---

## Discipline flowchart

```text
Strategy 56 Event B (destination frozen; 15m trade KILL)
        ↓
Strategy 57 prereg (this file) — NO outcomes yet
        ↓
Compute prog_close ladder + mono (IS → Val → OOS)
        ↓
PATH_KILL  or  PATH_ADVANCE
        ↓
If ADVANCE: stop. Write separate monetization prereg later.
If KILL: stop. Do not shop H. Do not open Family 3/4 as rescue.
```

---

## Outputs (when executed later)

| Path | Role |
| --- | --- |
| `results/path_progress.parquet` | event_id × H progress / MFE / MAE / hit flags |
| `results/path_ladder_by_split.csv` | n / med / mean / p_pos by split × H |
| `results/path_verdict.json` | PATH_KILL / PATH_ADVANCE + gate detail |
| `results/PATH_TIMING_REPORT.md` | Report |
| `results/audit.json` | Freeze / leakage checks |

---

## Decision record

**Strategy 57 = Event B path/timing diagnostic only.**  
Chosen because Event B already demonstrated stable destination asymmetry (#1) while fixed 15m monetization (#3) failed — the open scientific gap is path (#2), not a new event family.
