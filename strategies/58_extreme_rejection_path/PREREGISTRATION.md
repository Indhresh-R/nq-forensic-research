# Strategy 58 — Extreme Excursion → Rejection (path-first)

**Status:** FROZEN CONTRACT + EVENT C PREREG BEFORE ANY OUTCOME COMPUTATION.  
**Namespace:** `strategies/58_extreme_rejection_path/`  
**Parent boundary:** `strategies/RESEARCH_LEDGER_52_54.md` (hierarchy after 57)  
**Family:** **4 — Extreme excursion → rejection** (exactly one). Families 1–3 not reopened; Event A/B closed.

---

## Why this event (selection rule)

Chosen for **path structure**, not destination curiosity.

After an extreme excursion is **rejected**, the structural claim is an ordered return toward the pre-excursion anchor — a holding path hypothesis, not merely “we eventually touch somewhere.”

Not a rescue of Event A (displacement→50% retrace) or Event B (range break→failed return).

---

## Research question

> After an objectively defined extreme excursion is rejected, does price show (i) destination asymmetry toward the anchor, (ii) a directional / first-passage path with MFE dominating MAE, and (iii) only then — can one fixed execution capture it?

---

## Hard discipline (mature hierarchy)

```text
1. EVENT C (this freeze)
2. DESTINATION ASYMMETRY
3. PATH / FIRST-PASSAGE
4. MAE vs MFE
5. TIME TO DESTINATION (descriptive)
6. ONE EXECUTION   ← only if 2–4 ADVANCE
```

- Maximum **one** event
- No horizon P&L shopping
- No CVD / VWAP / TOD / state filters
- ATR appears only inside the **frozen event magnitude** (same role as Event A), not as a post-hoc trade filter
- If path fails → **KILL** (do not jump to trade; do not retune)

---

## Event C definition (objective)

Working sample: contiguous 1m NQ; same `session_date` / `segment_id` / unit `ny_min` continuity as Strategies 55–56.  
Event bars restricted to RTH analysis window **09:30–16:00 ET** (`census_eligible`). Rolling lookbacks may use pre-09:30 within segment.

### C1. Excursion bar `t_e`

Let `W = 30`. Require contiguous window so `ny_min[t_e] = ny_min[t_e − W] + W`.

- `anchor = close[t_e − W]`
- `ATR = atr_30[t_e]` (Strategy 52 feature panel; causal)
- Require `ATR` finite and `ATR > 0`
- `excursion = close[t_e] − anchor`
- Require `|excursion| ≥ K × ATR` with **`K = 2.0`**
- `ext_dir = +1` if `excursion > 0`, else `−1` (skip if 0)

**Onset:** accept `t_e` only if the same threshold was **not** already met at `t_e − 1` with the same `W`:

- `|close[t_e−1] − close[t_e−1−W]| < K × atr_30[t_e−1]`  
  (if ATR at `t_e−1` invalid, treat as onset-eligible)

Require `t_e` is `census_eligible`.

### C2. Geometry frozen at `t_e`

- `extreme = close[t_e]`
- `span = |extreme − anchor|`
- Rejection level (50% giveback toward anchor):

```text
L = extreme − 0.5 × (extreme − anchor)
```

(midpoint between `anchor` and `extreme`)

### C3. Rejection = **Event C bar `t`**

Search forward from `t_e + 1` through at most `H_wait = 60` contiguous bars.

- If `ext_dir = +1`: first `t` with `low[t] ≤ L`
- If `ext_dir = −1`: first `t` with `high[t] ≥ L`

If none within `H_wait` → censored (not Event C).  
Require event bar `t` is `census_eligible`.

**Event time = `t`.** Forward paths start strictly after `t`.

**Predicted path direction after `t`:** toward **anchor**  
(`side = −ext_dir`: up-excursion rejection → short toward anchor; down-excursion rejection → long toward anchor).

---

## Destinations (frozen)

| Name | Definition |
| --- | --- |
| `reach_anchor` | Up-ext: path `low ≤ anchor`. Down-ext: path `high ≥ anchor`. |
| `reach_extreme` | Up-ext: path `high ≥ extreme`. Down-ext: path `low ≤ extreme`. |
| `reach_through` | Path reaches `anchor − ext_dir × 0.25 × span` (through anchor by 25% of span) |

Primary contrast:

> **`Δ = P(reach_anchor) − P(reach_extreme)`** at horizon **15m** (report 5/30/60).

Secondary (report only): `P(reach_through)`.

---

## Path / first-passage metrics (frozen — before any P&L)

Reference: `c0 = close[t]`, normalize by `span`.

Ladder **`H ∈ {5, 15, 30, 60}`**:

```text
prog_close[H] = side × (close[t+H] − c0) / span
```

Secondary (not destination gates; used in path gates / report):

| Metric | Definition |
| --- | --- |
| `mfe_dir[H]` | favorable excursion / span over `(t, t+H]` |
| `mae_dir[H]` | adverse excursion / span over same window |
| `hit_anchor[H]` | 1 if `reach_anchor` by H |
| `first_anchor_bars` | bars from `t` to first anchor touch; null if none by 60 |

**Monotonicity (per split):**

```text
mono = med[5] ≤ med[15] ≤ med[30] ≤ med[60]
```

---

## Splits

| Split | Years |
| --- | --- |
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

---

## Gates

### Step 1 — Destination (IS, 15m)

Material if `n_valid ≥ 500` and `|Δ| ≥ 0.05`.  
Sign must match predicted path: require **`Δ > 0`** (anchor preferred over re-extreme). Else **KILL**.

### Step 2 — Destination stability

- Val: `n ≥ 200`, `Δ_Val > 0`, `|Δ_Val| ≥ 0.025`
- OOS: `n ≥ 100`, `Δ_OOS > 0`  
Else **KILL**.

### Step 3 — Path / MFE–MAE (only if Steps 1–2 pass)

On IS, then Val & OOS:

1. `n[H] ≥` 500 / 200 / 100 at every ladder H  
2. `med[60] > 0` and `mono == True`  
3. Mid-ladder: `med[15] > 0` **or** `med[30] > 0`  
4. **MFE vs MAE at 15m:** `med(mfe_dir[15]) > med(mae_dir[15])` on IS; same inequality on Val and OOS  

Fail → **`PATH_KILL`** (no trade).  
Pass all → **`PATH_ADVANCE`**.

Time-to-anchor percentiles: report only (step 5 descriptive).

### Step 6 — One trade (only if `PATH_ADVANCE`)

| Element | Rule |
| --- | --- |
| Side | Toward anchor (`side = −ext_dir`) — frozen; not re-derived from Δ sign |
| Entry | `open[t+1]` |
| Exit | `close[t+15]` |
| SL/TP | None |
| Cost | **1.0** pt RT |
| Promote | `mean_net > 0` on IS & Val & OOS; each `n_trades ≥ 200` |

Fail → **KILL**. No fixes. No alternate holds.

---

## Frozen constants (no search)

| Symbol | Value |
| --- | --- |
| `W` | 30 |
| `K` | 2.0 |
| Rejection | 50% giveback to `L` |
| `H_wait` | 60 |
| Through buffer | `0.25 × span` |
| Primary destination H | 15 |
| Path ladder | 5, 15, 30, 60 |
| Cost | 1.0 |

---

## Forbidden

- Reopening / combining Event A or B
- Retuning after outcomes
- Horizon P&L shopping
- State / VWAP / CVD / volume / TOD filters
- Starting Family 3 in parallel
- Declaring prop suitability without a separate written constraint in a future monetization note (if ever needed)

---

## Outputs (when executed later)

| Path | Role |
| --- | --- |
| `results/event_c_events.parquet` | Event ledger |
| `results/event_c_destinations.csv` | Rates / Δ by split × horizon |
| `results/path_ladder_by_split.csv` | prog / MFE / MAE ladder |
| `results/event_c_verdict.json` | Stage kills / PATH_ADVANCE / trade |
| `results/EVENT_C_REPORT.md` | Report |
| `results/audit.json` | Freeze checks |

---

## Decision record

**Event C = Extreme excursion → rejection (Family 4).**  
Selected because the hypothesis is inherently a **return path after rejection**, matching the post-57 rule: search events for path structure, not destination-only interest.
