# Vilkov Phase 0 Audit — COMPLETE

## 1. Timestamp resolution
- `data_opt.parquet`: **1,369,301** rows, **1919** days, 2016-09-01 → 2024-05-01
- Unique `quote_time` counts: `{'16:00:00': 110230, '10:00:00': 107180, '11:00:00': 107118, '11:30:00': 107075, '10:30:00': 107035, '12:00:00': 106457, '12:30:00': 106398, '13:00:00': 105913, '13:30:00': 104112, '14:00:00': 103663, '14:30:00': 102910, '15:00:00': 101257, '15:30:00': 99953}`
- Unique times/day: median **12**, max **13** (example 2016-09-02: ['10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00'])
- **Verdict: `30MIN`** — not 1-minute; Cboe-style half-hour grid 10:00–16:00 ET (~12–13 stamps/day).
- `vix.parquet`: same 30-minute grid; median times/day=13
- `data_structures.parquet`: sparse clocks only — mainly 10:00 / 13:00 / 15:00 / 16:00 (strategy entry times), not full half-hour book
- `slopes.parquet`: full 30-minute grid like `data_opt`

## 2. Point-in-time safety
- `open_interest`: present; treat conservatively as start-of-day / lagged vs live tape.
- `trade_volume*` at timestamp T: treat as information as-of that bar only if documentation confirms; until then prefer OI-gamma / quote Greeks for PIT features and place volume-gamma in a lagged/sensitivity bucket.
- `payoff`, `reth`, `reth_und`: settlement outcomes — **never predictors**.
- `future_moments_SPX` (`SPX_lrv`, …): realized from t→16:00 — **targets only**, not features.

## 3. Option identity
- `option_type`: {'C': 692453, 'P': 676848}
- `mnes` in [98000, 102000], nunique=41
- Greeks: delta, gamma, theta, vega, implied_volatility
- mid, bas, bid_size, ask_size, trade_volume, open_interest, active_underlying_price
- No raw strike/expiry columns; 0DTE moneyness grid implied

## 4. What gamma fields mean
- In `data_opt`: `gamma`, `oi_gamma`, `oi_gamma_abs`, `oi_gamma_usd`, `trade_volume_gamma*` are **per moneyness node**, not a FirmTape-style full-chain minute dealer book.
- In `data_structures`: only mid/tv/payoff/reth/greeks — **no** shipped `g^{OI,n}` / `B^Γ` series.
- Null rates (sample fields): `{'gamma': 0.0, 'oi_gamma': 0.0, 'oi_gamma_abs': 0.0, 'oi_gamma_usd': 0.0, 'trade_volume': 0.0, 'open_interest': 0.0, 'trade_volume_gamma': 0.0, 'payoff': 0.0, 'reth': 0.0003980132929136837, 'reth_und': 0.0, 'mid': 0.0, 'delta': 0.0, 'implied_volatility': 0.0}`

## 5. Can we reconstruct our own gamma variables?
- Yes at each **30m** `data_opt` clock: aggregate across moneyness×CP → ATM gamma mass, signed `oi_gamma` balance, volume-gamma pressure, distance of peak gamma from spot.
- No true 1m dealer-gamma path from this file alone.
- Paper-style `g^{OI,n}` / `B^Γ` are **not** pre-shipped as a chain series; we build our aggregates from `data_opt` nodes.

## 6. Join to ES/NQ 1m
- Decision grid = `quote_date` + `quote_time` (30m). Map to America/New_York, join ES/NQ 1m at that minute.
- Forward +1/+5/+10/+15/+30/+60m outcomes are valid **from each 30m decision stamp** on our 1m underlyings (not from missing in-between option updates).
- Coverage ends **2024-05-01** on option panels (not Jan 2026 as the README marketing line suggests for all panels).

## Gate decision
**AUDIT PASS with hard constraints.** Usable **30-minute** SPXW surface for causal tests on ES/NQ 1m. Not a substitute for FirmTape 1m dealer book. No strategy run until feature rules are frozen to this clock.