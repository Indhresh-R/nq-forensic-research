# Strategy 56 — Range Break → Failed Return

**Status:** FROZEN CONTRACT + EVENT B PREREG BEFORE ANY OUTCOME COMPUTATION.  
**Namespace:** `strategies/56_range_break_failed_return/`  
**Parent boundary:** `strategies/RESEARCH_LEDGER_52_54.md` + Strategy 55 contract discipline.

---

## What this is

Exactly **one** new price-path event (Family 2 from the Strategy 55 menu).

Not a rescue of Event A. Not Strategies 52–54. Not CVD/VWAP/ATR/TOD filters. Not combining Event A + B.

---

## Research question

> After price breaks a defined prior range and then **returns inside** that range, where does price go next — and can one simple fixed execution capture a stable destination asymmetry?

---

## Hard discipline

```text
EVENT B prereg (this file)
        ↓
Step 1: destination asymmetry (IS materiality)
        ↓
Step 2: IS / Val / OOS stability
        ↓
Optional Step 3: path feasibility
        ↓
ONE fixed execution
        ↓
KILL / ADVANCE
```

- **Maximum one new event at a time**
- If Steps 1–2 fail → **KILL Event B** (do not retune)
- If trade fails → **KILL** (do not “fix” Event A or Event B)
- No Family 3/4 in parallel

---

## Event B definition (objective)

Working sample: contiguous 1m NQ; same `session_date` / `segment_id` / unit `ny_min` continuity as Strategy 55.  
Event bars restricted to RTH analysis window **09:30–16:00 ET** (`census_eligible` from Strategy 52 panel). Rolling lookbacks may use pre-09:30 within segment.

### B1. Range freeze at bar `t_r`

Let `W = 60` (minutes).

Require contiguous window `[t_r − W, t_r)` (W bars ending **before** `t_r`):

- `R_high = max(high[t_r − W : t_r])`  // python slice end-exclusive → bars t_r−W … t_r−1
- `R_low = min(low[t_r − W : t_r])`
- `R = R_high − R_low`
- Require `R > 0` and finite

`t_r` itself is the first bar **after** the range window (candidate break bar).  
`mid = 0.5 × (R_high + R_low)`.

### B2. Break at bar `t_b = t_r`

- **Up break:** `close[t_b] > R_high`
- **Down break:** `close[t_b] < R_low`
- Skip if close inside `[R_low, R_high]`
- `break_dir = +1` (up) or `−1` (down)
- Require `t_b` is `census_eligible`

**Onset:** accept only if the prior bar did **not** already satisfy the same break vs the range frozen from window ending at `t_b − 1` with the same `W` (i.e. first break bar of this style). Practical freeze:

- Compute range from `[t_b−1−W, t_b−1)` and require prior close was **not** already outside that prior range in the same direction  
  **OR** simpler equivalent used here: prior close was inside **this** event’s `[R_low, R_high]` (the range from `[t_b−W, t_b)`):

  - Up break onset: `close[t_b − 1] ≤ R_high`
  - Down break onset: `close[t_b − 1] ≥ R_low`

(If `t_b−1` not contiguous, discard.)

### B3. Failed return = **Event B bar `t`**

Search forward from `t_b + 1` through at most `H_wait = 60` contiguous bars.

**Return inside** (first touch):

- After **up** break: first `t` with `low[t] ≤ R_high` **and** `low[t] ≥ R_low`  
  (touches back through the broken top into the range body; if `low < R_low` on same bar, still counts as returned inside/through)
- After **down** break: first `t` with `high[t] ≥ R_low` **and** `high[t] ≤ R_high`  
  (symmetric; if `high > R_high` on same bar, still counts)

Simpler unified rule (frozen):

- Up break failed return: first `t` with `low[t] ≤ R_high`
- Down break failed return: first `t` with `high[t] ≥ R_low`

If no such bar within `H_wait`, censored (not Event B).  
Require Event bar `t` is `census_eligible`.

**Event time = `t`.** Forward paths start strictly after `t`.

---

## Destinations (frozen)

From event `t`, impulse/break direction `d = break_dir`:

| Name | Definition |
| --- | --- |
| `reach_opposite` | Up break: path `low ≤ R_low`. Down break: path `high ≥ R_high`. |
| `reach_mid` | Path touches `mid` (up: `low ≤ mid`; down: `high ≥ mid`) |
| `rebreak_outside` | Up: path `high ≥ R_high + 0.25×R` (re-extension beyond prior high). Down: path `low ≤ R_low − 0.25×R`. |

Primary contrast (preregistered):

> **`Δ = P(reach_opposite) − P(rebreak_outside)`** at horizon **15m**

Secondary (report only): `P(reach_mid)`.

---

## Horizons

Exactly **5, 15, 30, 60** minutes after `t`.  
Primary claims: **15m**.

---

## Splits

| Split | Years |
| --- | --- |
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

---

## Gates

### Step 1 (IS, 15m)

Material if `n_valid ≥ 500` and `|Δ| ≥ 0.05`. Else **KILL**.

### Step 2

- Val: `n ≥ 200`, `sign(Δ_Val)==sign(Δ_IS)`, `|Δ_Val| ≥ 0.025`
- OOS: `n ≥ 100`, same sign as IS — required to **ADVANCE_TO_TRADE**; sign flip → **KILL**

### Trade (only if ADVANCE_TO_TRADE)

| Element | Rule |
| --- | --- |
| Side | From **IS sign of Δ only**: if `Δ > 0`, trade toward opposite (up-break → short; down-break → long). If `Δ < 0`, trade toward rebreak (up-break → long; down-break → short). |
| Entry | `open[t+1]` |
| Exit | `close[t+15]` |
| SL/TP | None |
| Cost | **1.0** pt RT |
| Promote | `mean_net > 0` on IS & Val & OOS; each `n_trades ≥ 200` |

Fail → **KILL**. No fixes.

---

## Frozen constants (no search)

| Symbol | Value |
| --- | --- |
| `W` | 60 |
| `H_wait` | 60 |
| Rebreak buffer | `0.25 × R` |
| Primary horizon | 15 |
| Cost | 1.0 |

---

## Forbidden

- Combining with Event A
- Retuning after outcomes
- State / VWAP / CVD / volume / TOD / ATR filters
- Starting Family 3/4 before Event B is killed or advanced
- “Fixing” the Event A 15m fade

---

## Outputs (when executed later)

| Path | Role |
| --- | --- |
| `results/event_b_events.parquet` | Event ledger |
| `results/event_b_destinations.csv` | Rates / Δ by split × horizon |
| `results/event_b_verdict.json` | KILL / ADVANCE |
| `results/EVENT_B_REPORT.md` | Report |

---

## Decision record

**Event B = Range break → failed return (Family 2).**  
Chosen to test a **failure** geometry with structural destinations, independent of Event A’s displacement→50% retrace object.
