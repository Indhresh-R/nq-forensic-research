# Rules (frozen)

## Data

- FirmTape finished sessions: `https://firmtape.com/snapshots/YYYY-MM-DD.json` (raw preserved under `data/firmtape/raw/`).
- Underlying: local `es_1m_continuous.parquet` (S&P proxy) and `nq_1m_continuous.parquet`.
- Timezone: `America/New_York`.

## Causality

- Minute label `HH:MM` treated as **end-of-minute** gamma snapshot.
- At bar `t`, use only **lagged** gamma features `g[t-1]` (1-minute lag).
- Forward outcomes: `close[t] → close[t+h]`.
- Primary gamma field: `ngv_meas` (tape-measured). `ngv_conv` may include post-session OI backfill — secondary only.

## Regimes (Discovery-only quintiles of lagged `ngv_meas`)

| Regime | Meaning |
|--------|---------|
| A | Strong positive (top quintile) |
| B | Weak positive |
| C | Near zero |
| D | Weak negative |
| E | Strong negative |

Identical cutpoints applied to Validation and OOS.

## Distance-to-flip bins (predefined fractions of spot)

`far_below / mod_below / near / mod_above / far_above` at ±0.15% / ±0.40%.

## Chronological splits

| Split | Years |
|-------|-------|
| Discovery | 2022–2023 |
| Validation | 2024 |
| OOS | 2025–2026 |

## Economic rules (illustrative, not optimized)

1. Fade prior 5m sign in regime A; hold 5m.
2. Follow prior 5m sign in regime E; hold 5m.
Costs: ES 0.50 pt RT, NQ 1.00 pt RT (point proxies).
