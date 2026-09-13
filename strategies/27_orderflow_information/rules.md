# Rules — Strategy 27 (FROZEN after Phase 0)

**PROXY STUDY — NOT AN ORDER-FLOW STUDY.**

No optimization. No trading rules. No costs. No ΔR² until Phase 1 descriptives are reviewed.

## Study classification

| Claim language | Allowed? |
|----------------|----------|
| "`signed_vol_proxy` / volume-pressure proxy associates with …" | Yes |
| "`order flow` predicts …" based on these fields | **No** |
| True aggressor / customer flow | **Unavailable** in local data |

## Source / continuous series

- Vendor: Databento GLBX.MDP3 `ohlcv-1m`
- Files: `data/es_1m_continuous.parquet`, `data/nq_1m_continuous.parquet`
- Construction: per calendar date, keep single-contract symbol with **max daily volume**; drop spreads (`-` in symbol); **no** back-adjustment across rolls (`archive/legacy_scripts/build_continuous_data.py`)
- Columns present: `ts_event, open, high, low, close, volume, symbol`
- Absent: buy/sell volume, aggressor, trader type, BBO, depth

## Clocks

- `ts_event` = bar **open** (start of 1-minute bucket), stored UTC
- Session logic timezone: `America/New_York`
- `session_date` rolls at **18:00 ET** (`SESSION_START`)
- RTH research window: bar open `ny_min ∈ [09:30, 16:00)`
- Decision at end of completed bar `t`: features from bar `t` (+ history); outcomes from `close[t+h]/close[t]`

## Causality card

```text
Features at T: OHLCV of completed bar ending at T (and lags)
Outcomes: close[T+h]/close[T], path on bars t+1..t+h
Same-bar ret enters signed_vol_proxy by construction (feature only)
No future bars in features: YES
```

## Volume

- Unsigned contract volume for the selected front-month symbol in that minute
- Audit: volume_min = 1; **zero zeros** in continuous series
- If volume were 0: impact ratios → NaN; `signed_vol_proxy` → 0 when ret finite

## Missing / gaps / rolls

- `ret_1m` = NaN when prior gap > 1.01 minutes (no price ffill)
- Forward outcomes require exact h-minute clock span within `session_date`
- Roll days retained; gap rule NaNs returns across discontinuities

## Frozen proxies

| Name | Definition |
|------|------------|
| `ret_1m` | `close_t/close_{t-1}-1` if gap≤1m else NaN |
| `absret_1m` | `|ret_1m|` |
| `range_pct` | `(high-low)/close` |
| `volume` | unsigned 1m volume |
| `d_volume` | `volume_t - volume_{t-1}` |
| `vol_accel` | `d_volume_t - d_volume_{t-1}` |
| `vol_z_tod` | `(volume - μ_Disc(ny_min)) / σ_Disc(ny_min)`; RTH; Discovery moments only |
| `signed_vol_proxy` | `sign(ret_1m)*volume`; `sign(0)=0`; NaN if ret NaN. **Not aggressor flow.** |
| `signed_vol_proxy_sum_5` | sum of `signed_vol_proxy` over t-4..t (5 finite, same session) |
| `signed_vol_proxy_resid` | residual of `signed_vol_proxy ~ ret_1m + absret_1m + range_pct` (+intercept); **Discovery RTH OLS coeffs**, applied to all splits |
| `ret_per_vol` | `ret_1m/volume` if volume>0 |
| `absret_per_vol` | `|ret_1m|/volume` if volume>0 |
| `range_per_vol` | `range_pct/volume` if volume>0 |
| `vol_x_range` | `volume * range_pct` |

### Phase 0 collinearity lock (ES Discovery RTH)

- Spearman(`signed_vol_proxy`, `ret_1m`) ≈ **0.93** → largely a signed-return transform scaled by volume
- R²(`|signed_vol_proxy|` ~ volume) ≈ **0.87**; R²(~ `|ret|`) ≈ **0.22**
- Phase 1 **must** show `signed_vol_proxy_resid` next to raw proxy

## Outcomes (fixed)

Horizons: **1, 5, 15, 30, 60** minutes

| Name | Definition |
|------|------------|
| `ret_h` | `close[t+h]/close[t]-1` |
| `absret_h` | `|ret_h|` |
| `rv_h` | `std(ret_1m on t+1..t+h)*sqrt(n)`, n≥3 |
| `mfe_h` | `max(high[t+1..t+h])/close[t]-1` |
| `mae_h` | `min(low[t+1..t+h])/close[t]-1` |

## Splits

| Split | Years |
|-------|-------|
| Discovery | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

Tercile cuts: Discovery RTH equal-frequency only; applied unchanged.

## Instrument priority

1. ES panel  
2. NQ panel (identical protocol)  
3. Cross ES/NQ lead-lag → Strategy 28 if 27 fails (not expanded here)

## Hard bans

- No strategy thresholds / optimization / costs / rule construction
- No ΔR² until Phase 1 reviewed
- No ORB / EMA / candle / sweep / Fib / gamma features
- No claiming “order flow” for OHLCV proxies
