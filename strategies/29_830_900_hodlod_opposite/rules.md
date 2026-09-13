# Rules — Strategy 29 (FROZEN before look)

## Instrument / clock

- Primary: **NQ** 1m continuous (`load_nq`). ES reported as twin if cheap.
- Timezone: America/New_York
- Window **W**: bar opens `ny_min ∈ [08:30, 09:00)` → 30 one-minute bars
- RTH: `[09:30, 16:00)`
- Premarket reference (causal): `[18:00 prior session roll, 08:30)` same `session_date`

## Day extremes (Phase A / oracle label)

On `session_date`, using bars with `ny_min ∈ [08:30, 16:00)` (window + RTH):

- `day_hi` = max high, `day_lo` = min low
- `W_hi` / `W_lo` = max/min in W
- `is_hod` = (`W_hi` == `day_hi`) within 1e-8
- `is_lod` = (`W_lo` == `day_lo`)
- Labels: `HOD_ONLY`, `LOD_ONLY`, `BOTH`, `NEITHER`

Control windows (same length 30m): `07:30–08:00`, `09:00–09:30`, `10:00–10:30`
— compare HOD/LOD hit rates (Discovery descriptives).

## Oracle side (Phase B — not tradable)

| Label | Side |
|-------|------|
| `HOD_ONLY` | **short** (−1) |
| `LOD_ONLY` | **long** (+1) |
| `BOTH` / `NEITHER` | **skip** |

## Causal proxies (Phase C — tradable)

Decided at end of W (09:00), no future:

| ID | Rule |
|----|------|
| `fade_raid` | Took overnight high only → short; overnight low only → long; else skip |
| `fade_extent` | If `(W_hi − W_open) > (W_open − W_lo)` → short; elif reverse → long; else skip |
| `fade_last_touch` | Whichever of W_hi/W_lo printed later in W → fade that side |

Overnight high/low: max/min on same `session_date` with `ny_min < 08:30` (includes prior evening after 18:00 roll).

## Dip-and-recovery entry (frozen)

Search window after cash open: bar opens `ny_min ∈ [09:30, 10:30)` (60 minutes max to arm).

**Long (+1):**

1. From 09:30 open `O`, wait until some bar low `L ≤ O − dip_pts`
2. `dip_pts` frozen ∈ **{5, 10}** NQ points (two cells, not a mine)
3. After that dip bar, **recovery** = first later bar whose **close ≥ O** (reclaim open)
4. Entry = **next bar open** after recovery bar
5. Stop = `L − 1` point buffer
6. Targets (separate cells): **fixed +20 / +25 / +30**, and **opposite `W_hi`** (range target)

**Short (−1):** mirror (`H ≥ O + dip_pts`, recovery close ≤ O, stop `H+1`, targets −20/25/30 or `W_lo`).

Path rule: hostile **stop before target** if same bar. Time stop: **end of search+hold** =
entry + **30** minutes or 11:00 ET, whichever first — frozen **H=30** path after entry.

Cost: **1.0** NQ pt RT deducted.

## Splits

Discovery 2010–2021 / Validation 2022–2024 / OOS 2025–2026.

## Hard bans

- No using HOD/LOD label in Phase C
- No ORB/EMA/Fib stacks
- No expanding dip_pts / targets after look
- Do not promote oracle results as a live strategy
