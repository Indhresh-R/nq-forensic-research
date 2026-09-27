# Event A Preregistration — Displacement → Retracement

**Status:** FROZEN BEFORE ANY OUTCOME COMPUTATION.  
**Parent contract:** `PREREGISTRATION.md` (Strategy 55).  
**Family selected:** **1 — Displacement → retracement** (exactly one; Families 2–4 not run in parallel).

No ATR/CVD/VWAP/state filter may be added after this freeze.  
Market-state columns may be attached as **context only** in reports; they do not enter the event or destination definitions.

---

## Research question

> After a large directional displacement followed by a first fixed-fraction retracement, where does price go next — and is that destination asymmetry stable enough to justify one simple execution test?

---

## Event definition (objective)

All features at bar `t` use information at or before `t` only.  
Working sample: contiguous 1-minute NQ bars; require same `session_date` and `segment_id` and unit `ny_min` steps for any window (same continuity rules as Strategy 52 census-eligible RTH analysis window **09:30–16:00 ET** for *event bars*; rolling windows may look back into pre-09:30 within the segment).

### A1. Displacement (impulse) candidate at bar `t0`

Let `W = 30` (minutes/bars).

- `P0 = close[t0 − W]`
- `P1 = close[t0]`
- `ATR = ATR_30[t0]` (Strategy 52 / feature panel definition; causal)
- Require `ATR` finite and `ATR > 0`
- `impulse_net = P1 − P0`
- Require `|impulse_net| ≥ 1.5 × ATR`
- `direction = +1` if `impulse_net > 0`, else `−1` (skip if `impulse_net == 0`)

**Onset rule (no overlap spam):** accept `t0` only if the same threshold was **not** already met at `t0 − 1` with the same `W` window ending at `t0 − 1`:

- `|close[t0−1] − close[t0−1−W]| < 1.5 × ATR_30[t0−1]`  
  (if ATR at `t0−1` invalid, treat as onset-eligible)

### A2. Impulse geometry (frozen at `t0`)

- `origin = P0`
- `impulse_end = P1`
- `impulse_span = |P1 − P0|` (same as `|impulse_net|`)
- Retracement level (50% of close-to-close impulse toward origin):

\[
L = P1 - 0.5 \times (P1 - P0)
\]

(equivalently: midpoint between `P0` and `P1`)

### A3. Retracement confirmation = **Event A bar `t`**

Search forward from `t0 + 1` through at most `H_wait = 60` bars (contiguous).

- If `direction = +1` (up impulse): event at first bar `t` with `low[t] ≤ L`
- If `direction = −1` (down impulse): event at first bar `t` with `high[t] ≥ L`

If no touch within `H_wait`, the displacement is **censored** (not an Event A).

**Event time = `t` (retracement touch).** Forward path measurements start strictly after `t`.

---

## Destinations (frozen)

Measured on the forward path after `t` using highs/lows (touch), horizons below.

Signed in impulse direction (`d = direction`):

| Name | Definition |
| --- | --- |
| `reach_origin` | Path touches `origin` (for `d=+1`: `low ≤ origin`; for `d=−1`: `high ≥ origin`) |
| `reach_impulse_end` | Path re-touches `impulse_end` (for `d=+1`: `high ≥ impulse_end`; for `d=−1`: `low ≤ impulse_end`) |
| `reach_extension` | Path reaches `impulse_end + d × 0.5 × impulse_span` (50% extension beyond impulse end) |

Primary asymmetry contrast (preregistered):

> **`P(reach_extension) − P(reach_origin)`**  
> at each horizon, among valid Event A paths.

Secondary (report only): `P(reach_impulse_end)`.

No long/short trade labels in Steps 1–2.

---

## Horizons (frozen)

Exactly: **5, 15, 30, 60** minutes after `t`.  
Valid path: contiguous session/segment through `t+h`.

Primary horizon for Step 1/2 claims: **15m**.  
Secondary: 5 / 30 / 60.

---

## Chronological splits

| Split | Years |
| --- | --- |
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

---

## Step budget (hard)

| Step | Content | Stop rule |
| --- | --- | --- |
| **1** | Destination rates + primary contrast at 15m (and report other horizons) | If no material asymmetry on IS (see gate), **KILL Event A** |
| **2** | Same contrast on Validation and OOS | If IS and Val disagree in sign, **KILL** |
| **3** (optional) | Path feasibility (median \|excursion\| / timing vs 1.0 pt cost scale) | Descriptive only; does not rescue Step 1/2 |
| **Then** | One fixed execution (below) | Fail gate → **KILL**; no filters |

### Step 1 materiality gate (IS, horizon 15m)

Let `Δ = P(reach_extension) − P(reach_origin)`.

**Material** if:

- `n_valid ≥ 500` on IS, and
- `|Δ| ≥ 0.05` (5 percentage points)

Otherwise **KILL** (do not redefine `W`, `1.5`, `0.5`, or `H_wait`).

### Step 2 stability gate

- Validation: `n_valid ≥ 200` and `sign(Δ_Val) == sign(Δ_IS)` and `|Δ_Val| ≥ 0.025`
- OOS: report; require `n_valid ≥ 100` and same sign for **ADVANCE to trade test**; if OOS sign flips → **KILL** before trade

---

## One fixed execution (only if Steps 1–2 pass)

Frozen **before** P&L:

| Element | Rule |
| --- | --- |
| Side | If Step 1–2 find `Δ > 0` (extension more likely than origin): trade **with** impulse `direction`. If `Δ < 0`: trade **against** impulse `direction` (toward origin). Side is taken from the **IS sign of Δ only** (not re-picked on Val/OOS). |
| Entry | `open[t+1]` |
| Exit | `close[t+15]` |
| Stops/targets | None |
| Cost | **1.0** NQ point RT |
| Promotion | `mean_net > 0` on IS, Validation, and OOS; each split `n_trades ≥ 200` |

If trade fails → **KILL Event A**. No VWAP/CVD/volume/ATR/TOD/second target/state routing.

---

## Explicitly frozen constants (no search)

| Symbol | Value |
| --- | --- |
| `W` | 30 |
| Displacement threshold | `1.5 × ATR_30` |
| Retrace fraction | `0.50` |
| `H_wait` | 60 |
| Extension fraction | `0.50 × impulse_span` beyond `impulse_end` |
| Primary horizon | 15 |
| Cost | 1.0 |

---

## Forbidden

- Switching to Family 2/3/4 after seeing Event A outcomes
- Re-cutting thresholds after outcomes
- Adding state / VWAP / CVD / volume / TOD filters
- Continuing diagnostics past kill
- Reopening Strategies 52–54

---

## Outputs (when executed later)

| Path | Role |
| --- | --- |
| `results/event_a_events.parquet` | Event ledger |
| `results/event_a_destinations.csv` | Rates / contrasts by split × horizon |
| `results/event_a_step1_2_verdict.json` | KILL / ADVANCE_TO_TRADE |
| `results/event_a_trades.parquet` | Only if trade step runs |
| `results/EVENT_A_REPORT.md` | Report |

---

## Decision record

**Event A family = Displacement → retracement (Family 1).**  
Chosen for: pure price-path object; no census-state routing; furthest from Strategy 53/54 failures; destination question matches the Strategy 55 contract.
