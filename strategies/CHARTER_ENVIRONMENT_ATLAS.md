# Charter — Morning Environment Atlas (descriptive)

**Status:** EXECUTED (build under go-ahead). Definitions remain frozen.  
**Namespace:** `strategies/64_environment_atlas/`  
**Date:** 2026-09-27  
**Class:** Descriptive catalog. **NO TRADE. NO P&L. NO promote. NO trailing/risk rules.**

**Parent constraints:** `BRANCH_CLOSED_USE_ATLAS.md` (R1–R6). This is a **new charter**, not a rescue of 52–63 entries.

---

## Why this exists

Killed stacks showed: no universal fixed rule across all NQ conditions.  
Next object is not another entry — it is an **observable environment catalog** so any later sleeve can be gated by character *known before entry*.

---

## Objective

For the morning window, measure:

1. How often each **frozen character** appears  
2. How long it tends to persist (within the window)  
3. What structural footprint it leaves (range, ER, location) — **not** directional edge

Success = a usable atlas. Failure = characters that are only recognizable after the fact, or that collapse into one mushy bin.

---

## Frozen study window

| Item | Value |
| --- | --- |
| Clock | **America/New_York** |
| Window | **08:00 → 12:00** ET (end exclusive) |
| Session roll | Existing Globex **18:00** ET (unchanged) |
| Cash open marker | **09:30** ET (reference only; not an ORB trade) |
| Bar source | `data/nq_1m_continuous.parquet` (same as 52 feature path) |
| Prior VA source | **1m bar proxy v1** — `64_environment_atlas/results/p1_1m_va_proxy.parquet` (see `CHARTER_ENVIRONMENT_ATLAS_1M_VA_PROXY.md`). Trade P1 (Strategy 62) is overlap diagnostic only. |

**Not** studying overnight Globex as primary here. Overnight may appear only as **prior-session location** context.

---

## Decision clocks (causal labeling times)

Characters are assigned only at these clocks, using data **strictly before** the clock:

| Clock `t*` | Role |
| --- | --- |
| **08:30** | Early Globex-morning read (pre-cash) |
| **09:30** | Cash open (classify using `[08:00, 09:30)` only) |
| **10:30** | Mid-morning update (using `[08:00, 10:30)`) |
| **11:30** | Late-morning update (using `[08:00, 11:30)`) |

No label may use any bar at or after `t*`.  
Persistence = whether the character at `t*` still matches the character at the next clock (same definitions on the longer prefix).

---

## Frozen axes (building blocks)

Three axes. Each is observable at `t*` from past data only.  
**Do not retune cuts after seeing atlas frequencies.**

### Axis L — Location vs prior session VA

Using prior Globex session profile (`poc`, `vah`, `val`) and last price in `[08:00, t*)`:

| Code | Rule |
| --- | --- |
| `L_ABOVE` | last ≤ t* price `> prior_vah` |
| `L_INSIDE` | `prior_val ≤` last ≤ `prior_vah` |
| `L_BELOW` | last `< prior_val` |

If prior profile incomplete / missing → session **excluded** from atlas rows (do not impute).

### Axis V — Realized volatility regime

`RV` = std of 1-minute log returns on `[08:00, t*)` (need ≥ 20 returns; else exclude).

Compare to the distribution of the **same clock’s** RV over the prior **60** eligible sessions (trailing, causal):

| Code | Rule |
| --- | --- |
| `V_HIGH` | RV ≥ trailing q67 |
| `V_MID` | trailing q33 ≤ RV < q67 |
| `V_LOW` | RV < trailing q33 |

Cuts are **clock-specific** (08:30 cuts ≠ 10:30 cuts). Frozen once from the build’s trailing rule — no hand retune.

### Axis D — Drive vs balance (efficiency)

`ER` = `|close−open| / (high−low)` on the prefix bar range `[08:00, t*)`  
(open = first 1m open ≥ 08:00; high/low/close = extrema / last in prefix).  
If prefix range `< 4 ticks (1.0 pt)` → `D_FLAT` (separate, not forced into drive/balance).

Else vs trailing 60-session distribution of ER at the same clock:

| Code | Rule |
| --- | --- |
| `D_DRIVE` | ER ≥ trailing q67 |
| `D_MID` | q33 ≤ ER < q67 |
| `D_BALANCE` | ER < q33 |

---

## Frozen characters (named environments)

A **character** is the triple `(L, V, D)` collapsed into **five** operator-facing labels.  
Residual mass stays explicit — do not force every morning into a story.

| Character | Definition (at `t*`) | Intent |
| --- | --- | --- |
| **C1_DRIVE_EXT** | `D_DRIVE` ∧ (`L_ABOVE` ∨ `L_BELOW`) | Directional morning already outside prior value |
| **C2_DRIVE_INSIDE** | `D_DRIVE` ∧ `L_INSIDE` | Drive while still inside prior VA |
| **C3_BALANCE_INSIDE** | `D_BALANCE` ∧ `L_INSIDE` | Classic balance / acceptance inside value |
| **C4_BALANCE_OUTSIDE** | `D_BALANCE` ∧ (`L_ABOVE` ∨ `L_BELOW`) | Outside value but not driving (probe / limp) |
| **C5_OTHER** | everything else (incl. `D_MID`, `D_FLAT`, `V_*` unused in name) | Explicit residual — do not trade-design off this |

**Note:** Axis `V` is **recorded on every row** for the atlas tables, but the five names above are intentionally driven by **L×D** so the catalog stays small. Vol is a **covariate**, not a sixth character, in v1.

---

## What the atlas reports (when built)

Per decision clock, and pooled:

| Output | Content |
| --- | --- |
| Frequency | P(character), P(L), P(V), P(D) |
| Co-occurrence | L×D and L×V×D counts (n floors) |
| Persistence | P(same character at next clock ‖ character at `t*`) |
| Footprint | median prefix range, median ER, median RV by character |
| Year stability | frequency by calendar year (descriptive split only — **not** IS/OOS promote) |

**Minimum cell size to discuss a character at a clock:** n ≥ 50. Below that → “thin — do not interpret.”

---

## Explicit non-goals

- No trade / P&L / cost gate / trailing stop / runner logic  
- No ORB breakout test (R1 / R6)  
- No routing “if C1 then long” (that would violate R5 spirit until a **separate** sleeve charter)  
- No reopen of Patrick VA first-passage / Event A–D / 52 transition edge claims  
- No retune of q33/q67 after seeing which character “looks good”  
- No paid DOM  
- No claiming a character is an edge

---

## Refusal-map gate

Before any later sleeve that uses this atlas:

| Check | Rule |
| --- | --- |
| R1–R6 | Still in force |
| Character known at entry | Must equal label at a frozen `t*` ≤ entry time |
| New sleeve | Needs its **own** prereg; atlas alone ≠ strategy |

---

## Build plan (code only after go-ahead)

1. Label each eligible session at 08:30 / 09:30 / 10:30 / 11:30  
2. Write frequency + persistence + footprint tables  
3. `ENVIRONMENT_ATLAS_REPORT.md` + `verdict.json` with  
   `classification: DESCRIPTIVE_ATLAS` / `promote: false`

---

## Decision record

| Choice | Value |
| --- | --- |
| Scope | Morning 08:00–12:00 ET catalog |
| Characters | 5 named from L×D; V as covariate |
| Cuts | Trailing 60-session q33/q67 per clock |
| Trade | Impossible under this charter |
| Relation to 52 | May reuse 1m continuous + ER/RV *ideas*; **not** a reopen of 52 routing claims |

Ready for implementation only after explicit go-ahead.
