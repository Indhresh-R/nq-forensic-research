# Rules — 21 (FROZEN BEFORE RUN)

## Gate

- Strategy 12 HIGH: `rng_psr >= IS p66` (frozen thresholds). Untouched.
- Clocks: frozen `SESSION_DECISION_OFFSETS` only.

## Resolvers (both declared before any result)

| ID | Revelation bar | Side | Entry |
|----|----------------|------|-------|
| `bar1_follow` | First completed **1m** bar with time **strictly after** T | `sign(close−open)`; skip 0 | Open of the **next** 1m bar |
| `bar5_follow` | First completed **5m** block: open = open of bar T+1; close = close of bar T+5 | `sign(close−open)`; skip 0 | Open of the **next** 1m bar after that block (bar T+6) |

No other windows. No choosing 1 vs 5 from OOS residual size.

## Outcomes (from entry; resolver-only)

- Signed: `side * (px − entry)` for **H30**, **H60**, **SESS_END**
- Residual left (descriptive): `max(MFE, MAE)` over H30/H45 from entry (unsigned)
- Also report residual burned waiting: residual from T-entry vs from revelation-entry

## Contrasts

- **HIGH+resolver** vs **ALL+resolver** (same clocks, same revelation rule)
- Lift = win_HIGH − win_ALL; win-lift gates only (no E-lift rescue)
- Soft / strong / multi-clock same spirit as 16A–20

## Forbidden

- Stops, targets, RR, cost grids
- Retuning bar length / delay from Val or OOS
- Using NY_AM vs London residual magnitudes to pick the window
- Reopening Strategies 13–20
