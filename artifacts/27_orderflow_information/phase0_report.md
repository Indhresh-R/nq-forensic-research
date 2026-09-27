# Strategy 27 — Phase 0 data audit

## Classification

**PROXY STUDY — NOT AN ORDER-FLOW STUDY.**

Local ES/NQ continuous 1m bars are OHLCV only. Phase 1 measures OHLCV-derived **volume-pressure proxies**. Never report results as “order flow predicts …”.

## Continuous series

Volume-based front-month continuous: per calendar date keep the single-contract symbol with maximum daily volume; drop spreads (symbols containing '-'); no back-adjustment of prices across rolls (see archive/legacy_scripts/build_continuous_data.py).

- Vendor: `Databento GLBX.MDP3 ohlcv-1m`
- Absent fields: `buy_volume, sell_volume, aggressor_side, trader_type, bid, ask, depth`

## Series audit

### ES

- Rows: **4,916,275** | 2010-06-06 18:00:00-04:00 -> 2026-08-26 19:59:00-04:00
- Symbols: 40 | switches: 66 | approx roll calendar days: 66
- Volume min/median/p99/max: 1 / 253 / 9471 / 6223210
- Volume==0: 0 (0.0000%)
- RTH rows: 1,387,354 | RTH gap>1m fraction: 0.002637
- Split rows Disc/Val/OOS: 3,269,926 / 1,062,135 / 584,214

### NQ

- Rows: **4,788,194** | 2010-06-06 18:00:00-04:00 -> 2026-08-07 16:59:00-04:00
- Symbols: 40 | switches: 66 | approx roll calendar days: 66
- Volume min/median/p99/max: 1 / 91 / 2721 / 828542
- Volume==0: 0 (0.0000%)
- RTH rows: 1,382,157 | RTH gap>1m fraction: 0.002712
- Split rows Disc/Val/OOS: 3,159,504 / 1,062,524 / 566,166

## Critical collinearity test (Discovery RTH)

Question: can `signed_vol_proxy` contain information beyond disguised return/range/vol?

| Proxy | vs | Spearman or R² | n |
|-------|----|----------------|---|
| `signed_vol_proxy` | `ret_1m` | 0.9316 | 927,123 |
| `signed_vol_proxy` | `absret_1m` | -0.0007 | 927,123 |
| `signed_vol_proxy` | `range_pct` | -0.0098 | 927,123 |
| `signed_vol_proxy` | `volume` | -0.0025 | 927,123 |
| `signed_vol_proxy` | `ret_per_vol` | 0.7946 | 927,123 |
| `signed_vol_proxy` | `absret_per_vol` | 0.0033 | 927,123 |
| `signed_vol_proxy` | `vol_x_range` | -0.0057 | 927,123 |
| `signed_vol_proxy_resid_ret_abs_range` | `volume` | 0.0428 | 927,123 |
| `signed_vol_proxy_resid_ret_abs_range` | `absret_1m` | 0.0199 | 927,123 |
| `signed_vol_proxy_resid_ret_abs_range` | `ret_1m` | 0.2556 | 927,123 |
| `abs_signed_vol_proxy` | `ols_r2_on_absret_1m` | 0.2235 | 927,123 |
| `abs_signed_vol_proxy` | `ols_r2_on_volume` | 0.8742 | 927,123 |

### Freeze interpretation

- Spearman(`signed_vol_proxy`, `ret_1m`) = **0.9316** (mechanical co-movement with signed return is expected).
- Spearman(`signed_vol_proxy`, `volume`) = **-0.0025**.
- R²(|signed_vol_proxy| ~ |ret|) = **0.2235**; R²(|signed_vol_proxy| ~ volume) = **0.8742**.

Phase 1 **must** report `signed_vol_proxy_resid` (orthogonal to ret, |ret|, range) alongside the raw proxy. If only the raw proxy associates with outcomes and the residual does not, treat the proxy as a **relabeled OHLCV transform**, not volume-pressure information.

## Frozen items

- Clocks, continuous construction, volume definition, proxy formulas, outcomes, splits: see `phase0_freeze.json`.
- Hard bans: no thresholds / optimization / costs / rules / delta-R2 until Phase 1 reviewed.

## Gate

**Phase 0 PASS — freeze locked. Proceed to Phase 1 descriptives only.**
