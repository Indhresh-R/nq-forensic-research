# Methodology — 24A Volatility-Scaled Position Sizing

## Causality card

```text
Information available at signal T:
  - NQ bars with timestamp <= T
  - Strategy-12 frozen IS terciles (rng_psr p66 / p33) — never refit
  - Realized vol from bars with timestamp <= T only

Entry / outcome start:
  next bar OPEN after T

Forbidden:
  - Using post-T bars for vol or HIGH
  - Choosing lookback / clips / HIGH multipliers by IS Sharpe
  - Directional side selection from state or vol
```

## Strategy-12 HIGH (frozen, reused)

- Thresholds: `artifacts/12_multi_session_opportunity/nq_multi_sess_opp_thresholds_IS.json`
- `HIGH` ⇔ `rng_psr >= p66` at session × decision offset
- `LOW` ⇔ `rng_psr <= p33`; else `MID`
- **non-HIGH** = LOW ∪ MID (primary contrast: HIGH vs non-HIGH)
- Sessions / clocks: ASIA, LONDON, NY_AM, NY_PM with `SESSION_DECISION_OFFSETS`

## Direction-agnostic entry (primary book)

```text
side = +1 if hash64(session_date, session, T_offset, seed=24) is even else -1
```

- Frozen PRNG key — reproducible, ~50/50, **no** information from price path sign
- PnL points = `side * (close_H - entry_open)` minus mid RT cost (1.0 pt) × |size|
- **Audit books:** identical sizing on always-long and always-short; require that any
  claimed risk improvement is not a one-sided directional artifact

## Realized vol at T (frozen formula — registered BEFORE performance look)

```text
W = 30   # bars ending at T (inclusive), same session preferred; pad from prior bars of day if needed
r_i = close_i - close_{i-1}   # point returns
rv_T = std(r_{T-W+1} … r_T, ddof=1)   # require finite, rv_T > 0

# IS-only reference (computed once on IS panel; frozen for Val/OOS):
rv_ref = median(rv_T | split=IS)

size_inv = clip(rv_ref / rv_T, 0.25, 4.0)
```

Vol is **not** `rng_psr` (that defines HIGH). Separate return-std avoids pure circularity
while remaining causal.

## Sizing policies (same trade set; compare risk metrics)

| Policy | Size rule |
|--------|-----------|
| `fixed` | `size = 1.0` |
| `invvol` | `size = size_inv` |
| `invvol_high_aware` | `size = size_inv * (0.70 if HIGH else 1.00)` |

Constants `0.70 / 1.00`, clips `0.25 / 4.0`, `W=30` are **frozen** — no IS grid search.

## Holding horizons

`H ∈ {30, 60}` minutes (multi-horizon). Primary report horizon: **H=30**.

## Clustering / trade set for risk metrics

Overlapping clocks inflate Sharpe degrees of freedom. For Sharpe / Sortino / max DD:

- **One trade per (session_date, session)** at the **earliest** eligible decision offset
  that has valid state + enough forward bars

MAE / MFE distributional tables may use all offsets (documented separately).

## Metrics (primary)

| Metric | Definition |
|--------|------------|
| Sharpe | Daily PnL series: `mean / std * sqrt(252)` (days with ≥1 trade) |
| Sortino | Daily: `mean / downside_std * sqrt(252)` (downside = std of min(pnl,0)) |
| Max DD | Peak-to-trough of cumulative daily PnL (points) |
| MAE / MFE | Per-trade adverse / favorable excursion in points (unsigned path), by regime |

Bootstrap: 2,000 resamples of **daily** PnL vectors; report 90% CI for ΔSharpe and ΔSortino
vs `fixed` (policy − fixed).

**Not primary:** win rate, raw total PnL (reported only as diagnostics).

## Baselines

1. Unconditional fixed size (`fixed`) — no regime awareness, no vol scaling
2. Unconditional inv-vol (`invvol`) — vol awareness without HIGH multiplier
3. HIGH-aware inv-vol (`invvol_high_aware`) — vol + regime

Also stratify each policy's trades into HIGH vs non-HIGH for distributional MAE/MFE.

## Splits / stage gate

```text
IS:  2010–2021   ← score and publish first
Val: 2022–2024   ← locked until explicit go-ahead
OOS: 2025–2026
```

Default CLI: `--stage IS`.

## Ambiguity

Time-exit only (no stop/target path) → no same-bar dual-touch ambiguity.
