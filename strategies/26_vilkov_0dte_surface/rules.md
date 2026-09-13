# Rules — Phase 1 frozen (2026-09-08)

No optimization. No strategy search. Descriptives only.

## Clocks

- Feature stamps: `data_opt` only at ET times
  `10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00`
- Timezone: `America/New_York`
- Moneyness: Vilkov grid only — `mnes_rel ∈ [0.98, 1.02]` (do not expand)

## Causality

- At decision `T`, features use only `data_opt` rows with that `quote_date` + `quote_time`
- Underlying price: last ES/NQ **1m bar open strictly before T**; use that bar’s **close** as `px`
- Forward path: bars with `T <= bar_open < T+h` for RV/excursion; terminal price = close of last bar with `bar_open < T+h`
- Banned as features: `payoff`, `reth`, `reth_und`, `intrinsic`, all `future_moments_SPX` / `SPX_lrv*` fields
- `data_structures`: only if same stamp exists; **no** forward-fill from later stamps (Phase 1 default: **unused**)

## Naming

- Aggregates from `oi_gamma*` / `trade_volume_gamma*` are labeled **surface OI-gamma / volume-gamma**
- Do **not** call them dealer gamma / dealer positioning

## Volume-gamma

- Included as contemporaneous surface fields with a `volg_` prefix
- Report separately from OI-gamma in case bar volume timing is ambiguous

## Splits (chronological)

| Split | Years |
|-------|-------|
| Discovery | 2016–2021 |
| Validation | 2022–2023 |
| OOS | 2024 (through panel end 2024-05-01) |

Tercile bins for conditional tables: **Discovery equal-frequency cuts only**, applied unchanged to Val/OOS.

## Horizons (fixed)

`5, 15, 30, 60, 120` minutes on ES and NQ:

- signed return
- absolute return
- realized vol of 1m returns
- max favorable / adverse excursion vs `px` (path high/low)
- continuation vs reversal vs prior 30m underlying move (descriptive)

## Phase 2 — Incremental R² (frozen; no optimization)

**Question:** Does the surface add information about future ES/NQ returns/vol **not already in ordinary market info?**

### Nested baselines

| Model | Features |
|-------|----------|
| **A** | TOD (sin/cos), prior 30m return, prior 30m RV, prior 30m range, `surf_iv_atm` |
| **B** | A + surface **OI-gamma** family (concentration, balance, PC asym, slope, peak dist, d30_*) |
| **C** | A + **volume-gamma** + **IV skew / surface-shape** |
| **atm_share_only** | A + `surf_atm_oi_gamma_abs_share` only (key probe) |

Coefficients fit on earlier splits only; **R² scored on later splits**.

Protocols: Discovery→Validation, Discovery→OOS, Discovery+Validation→OOS.

### Hostile placebos (surface extras scrambled; baseline A untouched)

1. Feature row permutation
2. Within-session timestamp shift ±1 / ±2 stamps
3. Wrong-day remap (same TOD, different session)

Also: ES vs NQ, horizon grid, feature-family ΔR², year-by-year (panel ends 2024 — **no 2025–26**).

**No threshold search. No trading rules.**

## Phase 2 classification (locked)

**C — Research signal, not trading edge.**

Residual ATM OI-gamma info vs subsequent ES RV is small, horizon-dependent, and does not transfer cleanly to NQ. Do **not** open a trading-rule search from Phase 2 alone.

## Phase 3 — Stability / mechanism audit (frozen; no optimization)

**Question:** Why does the residual ES effect exist, and is it coherent/stable?

| Probe | Design |
|-------|--------|
| IV regime | Discovery IV-ATM terciles; within-regime DiscVal→OOS ΔR²; atm×z(IV) interaction |
| Vol regime | Discovery prior-RV terciles + vs day-median prior RV |
| Surface part | Frozen single probes: atm / near / peak_dist / centroid / slope / pc_asym |
| ES→NQ | Spearman lead-lag; NQ ΔR² of atm after A_nq+es_rv; ES symmetry check |
| Time-of-day | Per half-hour stamp DiscVal→OOS ΔR² |
| Chrono blocks | 2016–18 / 2019–21 / 2022–23 / 2024 fit-earlier→score-block |
| Falsification | Identity vs global/IV/TOD permute, residual permute, Gaussian moment match |

**Hard rule:** no thresholds, no entry/exit, no Sharpe hunting. Archive if Phase 3 is unstable.
