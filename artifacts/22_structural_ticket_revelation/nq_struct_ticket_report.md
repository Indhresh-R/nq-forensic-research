# Strategy 22 — Structural-Ticket Direction Revelation

## Freeze (locked before run)

- Ticket = **0.25 × psr** (Strategy 12 STRUCT_FRAC)
- Observation horizon = **60** bars after T
- Same-bar both hits -> AMBIGUOUS (skip)
- Neither in horizon -> NO_REVELATION (skip)
- Entry = next open after trigger bar
- Win-lift HIGH−ALL only; no stops/targets; do not retune 0.25 or 60
- Panel rows: **61,736**
- Soft: **0**
- Strong: **0**

## Reveal rates (HIGH)

| Session | Split | n | Reveal% | Ambig% | None% | Med wait | Mean resid@entry H30 |
|---------|-------|---|---------|--------|-------|----------|----------------------|
| LONDON | IS | 4092 | 88.0% | 0.0% | 12.0% | 14.0 | 8.9 |
| LONDON | Validation | 1618 | 89.4% | 0.0% | 10.6% | 14.0 | 24.6 |
| LONDON | OOS | 376 | 83.2% | 0.0% | 16.8% | 15.0 | 38.3 |
| NY_PM | IS | 3970 | 76.8% | 0.1% | 23.1% | 21.0 | 17.8 |
| NY_PM | Validation | 1446 | 79.1% | 0.2% | 20.7% | 22.0 | 47.6 |
| NY_PM | OOS | 685 | 72.4% | 0.0% | 27.6% | 20.0 | 78.6 |
| NY_AM | IS | 1641 | 99.9% | 0.0% | 0.1% | 3.0 | 21.6 |
| NY_AM | Validation | 433 | 99.5% | 0.5% | 0.0% | 4.0 | 71.0 |
| NY_AM | OOS | 292 | 100.0% | 0.0% | 0.0% | 3.0 | 106.7 |
| ASIA | IS | 4159 | 52.1% | 0.6% | 47.3% | 24.0 | 12.1 |
| ASIA | Validation | 1122 | 42.3% | 0.1% | 57.6% | 22.0 | 25.2 |
| ASIA | OOS | 1252 | 61.4% | 0.2% | 38.3% | 20.0 | 49.8 |

## Scoreboard H30 (best IS win-lift clock per session -> median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `struct_ticket` | +1.6pp | -1.0pp | +2.9pp | 55.4% | 0 |

## Scoreboard H60 (best IS win-lift clock per session -> median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `struct_ticket` | +1.9pp | -2.3pp | +3.6pp | 55.7% | 0 |

## Scoreboard SESS_END (best IS win-lift clock per session -> median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `struct_ticket` | +0.9pp | +1.5pp | +3.1pp | 58.6% | 0 |

## Candidates

**None.**

## Verdict

**`C`**

Kill 22. Structural-ticket revelation does not provide stable incremental direction. Stronger call: under tested information, Strategy 12 behaves as an unsigned activity detector.

### Discipline

- Ticket and horizon were frozen before results.
- Ambiguous same-bar both = skip.
- Strategy 12 remains WHEN-only.

