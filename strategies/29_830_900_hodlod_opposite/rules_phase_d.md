# Rules addendum — Phase D (CORRECTED causal reading)

Supersedes Phase C proxies for the live idea. Phase B EOD-oracle remains an
upper-bound footnote only.

## User-corrected market story (causal)

1. **Before 09:30** we only need: 08:30–09:00 printed the **high or low of the
   day so far** (session from 18:00 roll through end of W / through 09:29) —
   **not** the end-of-day extreme.
2. Price has **already started reversing** off that extreme before the cash open.
3. If **09:30 is still that high/low of day-so-far** → **skip** (not the setup).
4. At the open: wait for price to move in the **trade direction** (away from the
   extreme / opposite side of the extreme), then a **pullback**, then enter.
5. Entry/exit distances are **unknown a priori** → small frozen probe grid only;
   no free search after look.

## Day-so-far definitions (no lookahead)

As of clock **T_pre = 09:00** (last minute of W ends; decision uses completed bars
with `ny_min < 09:00` for W, and `ny_min < 09:00` for so-far through W end).

Also confirm structure at **T_open− = 09:29** (last bar before cash open):

| Symbol | Definition |
|--------|------------|
| `pre` | bars on `session_date` with `ny_min < 09:30` (18:00→09:29) |
| `W` | `ny_min ∈ [08:30, 09:00)` |
| `so_far_hi_0900` | max high on session with `ny_min < 09:00` |
| `so_far_lo_0900` | min low on session with `ny_min < 09:00` |
| `W_hi` / `W_lo` | max/min in W |

### Eligibility at 09:00

| Label | Condition |
|-------|-----------|
| `LOD_SO_FAR` | `W_lo == so_far_lo_0900` and not (`W_hi == so_far_hi_0900`) |
| `HOD_SO_FAR` | `W_hi == so_far_hi_0900` and not (`W_lo == so_far_lo_0900`) |
| else | skip day |

### Reversal started (must hold by 09:29 close)

Frozen buffer `rev_pts ∈ {5, 10}` (probe):

- `LOD_SO_FAR`: `close_0929 >= W_lo + rev_pts`
- `HOD_SO_FAR`: `close_0929 <= W_hi - rev_pts`

### Skip if 09:30 still the extreme

Let `O` = 09:30 bar **open**. Let `so_far_hi_0929` / `so_far_lo_0929` = extremes on
`ny_min < 09:30`.

Skip if:

- `LOD_SO_FAR` and `O <= so_far_lo_0929 + 1e-8` (still at/through the low)
- `HOD_SO_FAR` and `O >= so_far_hi_0929 - 1e-8` (still at/through the high)

Optional hostile twin (reported): also skip if 09:30 bar **low/high** extends
so-far extreme (open not enough).

### Trade side

| Label | Side | Meaning |
|-------|------|---------|
| `LOD_SO_FAR` | **+1 long** | extreme was low → trade opposite (up) |
| `HOD_SO_FAR` | **−1 short** | extreme was high → trade opposite (down) |

## Entry probe grid (frozen)

Search `ny_min ∈ [09:30, 10:30)`.

**Impulse then pullback then resume** (`impulse_pb`):

1. From `O`, wait until price moves `impulse_pts` in trade direction
   (`impulse_pts ∈ {10, 15, 20}`)
2. Then wait for pullback `pb_pts` against trade direction
   (`pb_pts ∈ {5, 10}`)
3. Entry = next bar open after a bar that **resumes** (close back through the
   pullback extreme by 1 pt in trade direction)
4. Stop = beyond pullback extreme by **1 pt**

**Open reclaim after adverse dip** (`reclaim_O`) — secondary:

1. Adverse dip `dip_pts ∈ {5, 10}` from `O` (against side)
2. Recovery: close back through `O`
3. Entry next open; stop beyond dip −/+ 1

## Exit probe grid (frozen)

| Mode | Values |
|------|--------|
| Fixed target | **20, 25, 30** NQ pts |
| Stop | structural (from entry rule) — natural R varies |
| Time stop | **30** minutes after entry |
| Cost | **1.0** pt RT |
| Same-bar | stop before target |

Also report **R-multiple** using stop distance (E in R) for comparability.

## Splits / promotion

Discovery / Validation / OOS standard.  
Promote only if a **causal** cell has Val+OOS E_net>0 (or E_R>0), n≥30 each,
same sign. Discovery may pick among the frozen grid **only** as ranking, not
expansion.
