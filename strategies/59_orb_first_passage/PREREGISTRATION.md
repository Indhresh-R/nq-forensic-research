# Strategy 59 — Opening Range Break First-Passage

**Status:** FROZEN PREREG BEFORE ANY OUTCOME COMPUTATION.  
**Namespace:** `strategies/59_orb_first_passage/`  
**Parent boundary:** `strategies/RESEARCH_LEDGER_52_54.md` (post–58 first-passage frame)

---

## What this is

One **executable mechanism** with **target and adverse barrier defined together** from the start.

Not Event D from the Strategy 55 menu. Not a rescue of 52–58. Not destination-first shopping.

---

## Why this mechanism

Opening-range break is inherently a first-passage object:

- Event = break of a frozen morning range  
- Target = measured extension beyond the broken side  
- Adverse = failure back through a frozen intra-range barrier  

The research question is which barrier is hit first — not whether some distant destination is eventually touched.

Also aligns with a short NY-AM book without silently assuming “15m = truth”: time-to-barrier is measured explicitly.

---

## Research question

> After the first break of a frozen opening range, is the **extension target** reached **before** the **adverse failure barrier**, with acceptable MAE and time — enough to justify one fixed execution?

---

## Hard discipline

```text
EVENT (ORB break)
  ↓
TARGET + ADVERSE (frozen together)
  ↓
Which is reached first?     (Step 1)
  ↓
MAE before target / path    (Step 2)
  ↓
Time to resolution          (Step 3 descriptive)
  ↓
ONE trade                   (only if Steps 1–2 ADVANCE)
```

- Maximum one mechanism  
- No horizon P&L shopping  
- No CVD / VWAP / TOD / state filters  
- No retune after outcomes  
- Fail → **KILL**

---

## Sample / continuity

Contiguous 1m NQ; same `session_date` / `segment_id` / unit `ny_min` rules as Strategies 55–58.  
Primary analysis uses RTH; `census_eligible` required at event bar.

`ny_min`: 09:30 ET = **570**.

---

## Mechanism definition (frozen)

### M1. Opening range (per session)

Let `W_or = 30` (minutes).

For each `session_date` with contiguous bars covering `[570, 570 + W_or)`:

- `OR_high = max(high)` over `ny_min ∈ [570, 570 + W_or)`  
- `OR_low = min(low)` over the same window  
- `R = OR_high − OR_low`  
- Require `R > 0` and finite  
- `OR_mid = 0.5 × (OR_high + OR_low)`

If the window is incomplete or non-contiguous → session has **no** ORB event that day.

### M2. Event = first break after OR complete

Search forward from the first bar with `ny_min ≥ 570 + W_or` through at most `H_wait = 90` contiguous bars same session/segment (until 11:00 ET class window end at `ny_min < 570 + W_or + H_wait`).

- **Up break** at first bar `t` with `close[t] > OR_high` and `census_eligible`  
- **Down break** at first bar `t` with `close[t] < OR_low` and `census_eligible`  
- Onset: prior bar close was **not** already outside the same OR on the same side  

If both sides could break on the same bar (gap through), prefer the side of `close` vs `OR_mid` (close ≥ mid → up; else down). If none within `H_wait` → no event that session.

**Event time = `t`.** Forward path starts strictly after `t`.  
`break_dir = +1` (up) or `−1` (down).

### M3. Target and adverse (defined together)

| Level | Definition |
| --- | --- |
| **Target** | Up: `OR_high + 1.0 × R`. Down: `OR_low − 1.0 × R`. |
| **Adverse** | Up: `OR_mid`. Down: `OR_mid`. |

(Failure = reclaim of opening-range midpoint after the break.)

No other targets or stops in diagnostics or trade.

---

## Step 1 — First-passage (primary)

Within forward path, horizon cap **`H_cap = 60`** contiguous bars after `t` (or end of contiguous segment / session, whichever first):

- `hit_target_first` = target touched **before** adverse (strict: first touch wins; same-bar both → **adverse wins** — conservative)  
- `hit_adverse_first` = adverse before target  
- `unresolved` = neither within `H_cap`

Primary rate (among events with valid path start):

> **`p_target_first = P(hit_target_first)`**  
> **`Δ_fp = P(hit_target_first) − P(hit_adverse_first)`**

### Gates (Step 1)

| Split | Rule |
| --- | --- |
| IS | `n ≥ 500`, `p_target_first ≥ 0.55`, `Δ_fp ≥ 0.10` |
| Validation | `n ≥ 200`, `p_target_first ≥ 0.52`, `Δ_fp ≥ 0.05`, same sign as IS (`Δ_fp > 0`) |
| OOS | `n ≥ 100`, `Δ_fp > 0`, `p_target_first ≥ 0.50` |

Fail → **KILL** (no MAE trade shopping).

---

## Step 2 — MAE before target (only if Step 1 ADVANCE)

Among events with `hit_target_first`:

- `mae_before_target` = adverse excursion from `close[t]` toward the **adverse** side, in points, over `(t, t_target]`  
- Also report `mae / R`

Require on IS, Val, OOS:

1. `n_hit_target_first` meets same min-n as Step 1 for that split  
2. **Median** `mae_before_target ≤ 0.50 × R`  
3. **Median** `mae_before_target ≤ 8.0` NQ points  

Fail → **KILL**.

(Secondary report only: MFE to target distance, distribution of `mae/R`.)

---

## Step 3 — Time (descriptive only)

Report percentiles of bars-to-resolution (`t_resolve − t`) for target-first and adverse-first. **Not a gate. Not a hold-time search.**

---

## Step 4 — One trade (only if Steps 1–2 ADVANCE)

| Element | Rule |
| --- | --- |
| Side | Break direction (`+1` long after up break; `−1` short after down) |
| Entry | `open[t+1]` |
| Exit | First touch of **target** or **adverse** (intrabar high/low), else `close[t + H_cap]` |
| Same-bar both | Exit at **adverse** (match Step 1 conservatism) |
| Cost | **1.0** pt RT |
| Promote | `mean_net > 0` on IS & Val & OOS; each `n_trades ≥ 200` |

Fail → **KILL**. No alternate exits. No second target.

---

## Splits

| Split | Years |
| --- | --- |
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

---

## Frozen constants (no search)

| Symbol | Value |
| --- | --- |
| `W_or` | 30 |
| `H_wait` | 90 |
| Target | `1.0 × R` beyond broken OR side |
| Adverse | `OR_mid` |
| `H_cap` | 60 |
| MAE median cap | `0.50 × R` and `8.0` pts |
| Cost | 1.0 |

---

## Forbidden

- Reopening Strategies 52–58  
- Event A/B/C combine or “fix”  
- Retuning `W_or`, target multiple, or adverse level after outcomes  
- Horizon / multiple shopping  
- TOD / VWAP / CVD / ATR filters  
- Declaring ADVANCE then adding a stop that was not this adverse barrier  

---

## Outputs (when executed later)

| Path | Role |
| --- | --- |
| `results/orb_events.parquet` | Event ledger |
| `results/first_passage_by_split.csv` | p_target_first / Δ_fp |
| `results/mae_before_target_by_split.csv` | MAE gates |
| `results/time_to_resolve.csv` | Descriptive timing |
| `results/trade_summary.csv` | Only if trade run |
| `results/verdict.json` | KILL / ADVANCE stages |
| `results/ORB_FIRST_PASSAGE_REPORT.md` | Report |
| `results/audit.json` | Freeze checks |

---

## Decision record

**Strategy 59 = Opening Range Break first-passage.**  
Chosen as a concrete executable mechanism under the post–58 frame: target and adverse barrier co-defined; first-passage is the primary claim — not another destination-menu event.
