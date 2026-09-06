# Rules — 22 (FROZEN BEFORE RUN)

## Gate

- Strategy 12 HIGH: `rng_psr >= IS p66`. Untouched.
- Clocks: frozen `SESSION_DECISION_OFFSETS`.

## Revelation (single resolver: `struct_ticket`)

| Parameter | Frozen value |
|-----------|--------------|
| Reference | `close` at decision bar T |
| Ticket | **`0.25 × psr`** (Strategy 12 STRUCT_FRAC primary) |
| Observation horizon | **60** completed 1m bars after T |
| Up trigger | bar `high >= close_T + ticket` |
| Down trigger | bar `low <= close_T - ticket` |
| Same-bar both | **AMBIGUOUS** → skip (no invented OHLC order) |
| Neither in horizon | **NO_REVELATION** → skip |
| Entry | open of the **next** 1m bar after the trigger bar |

## Outcomes (from entry)

- Signed `side * (px − entry)` for **H30**, **H60**, **SESS_END**
- Residual left at entry: diagnostic only

## Contrasts

- HIGH+revelation vs ALL+revelation (same rule)
- Win-lift gates only; soft/strong/multi-clock as 16A–21

## Forbidden

- Retuning 0.25 or 60m from Val/OOS
- Stops / targets / RR
- Judging from raw HIGH win rate alone
- Rescuing with bar-length or frac grids
