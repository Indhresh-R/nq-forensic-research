# Frozen Opportunity Gate — DO NOT OPTIMIZE

**Status: FROZEN** as of opportunity-timing stage `A_opportunity_timing_found`.

This gate answers only:

> Is the market currently likely to produce a **structurally meaningful** move?

It does **not** answer direction. It does **not** authorize trades by itself.

---

## Definitions (locked)

### Structural opportunity (context only)

`max(MFE, MAE) ≥ 0.25 · ONR` within forward horizon H  
(frac = 0.25 pre-specified; not for re-tuning)

### Decision clocks

Every 5 minutes from **09:35–11:00 ET** (`T_offset` ∈ {5,10,…,90}).

State uses only bars with `ny_min ≤ T`.  
Any forward evaluation starts at **next bar open after T**.

### State thresholds

IS terciles frozen in `artifacts/ny_open_opp_timing_thresholds_IS.json`  
(`rng_onr`, `speed`, … per `T_offset`). **Never recompute.**

### LOW = WAIT

| ID | Rule |
|----|------|
| `vol_expansion_low` | `rng_onr ≤ IS_p33(T)` |
| `quiet_wait` | `vol_expansion_low` ∧ `abs_move_onr ≤ IS_p33(T)` |

### HIGH = ARM

| ID | Rule |
|----|------|
| `vol_expansion_high` | `rng_onr ≥ IS_p66(T)` | **PRIMARY ARM** |
| `fast_and_expanded` | `speed ≥ IS_p66(T)` ∧ `dir_sign ≠ 0` ∧ `vol_expansion_high` | secondary / stricter |

**Primary frozen ARM for subsequent research:** `vol_expansion_high`.

---

## Allowed use

1. **WAIT** when LOW (optional hard filter).
2. **ARM** only when PRIMARY HIGH is true at T.
3. Directional / entry research may run **only inside ARM**.
4. Compare every candidate X as: `HIGH + X` vs `HIGH alone`.

## Forbidden

- Re-fitting terciles, STRUCT_FRAC, clocks, or gate labels
- Combining multiple X mechanisms before each clears alone
- Treating HIGH as a long/short signal
- Optimizing gate parameters against directional PnL

## Evidence pointer

- `artifacts/ny_open_opp_timing_report.md`
- ONR-matched control: `artifacts/ny_open_opp_timing_onr_matched.csv`
