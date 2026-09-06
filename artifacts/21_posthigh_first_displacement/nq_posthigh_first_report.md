# Strategy 21 — First Post-HIGH Directional Displacement

## Freeze (locked before run)

- `bar1_follow`: first 1m bar after T; entry next open
- `bar5_follow`: first 5m block after T; entry next open
- Outcomes from entry: H30 / H60 / SESS_END
- Win-lift HIGH−ALL only; Strategy 12 untouched
- Residual-left tables are diagnostic — **not** used to pick 1m vs 5m
- Panel rows: **65,449**
- Soft: **0**
- Strong: **0**

## Scoreboard H30 (best IS win-lift clock per session -> median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `bar1_follow` | +1.9pp | +2.3pp | -1.3pp | 52.1% | 0 |
| `bar5_follow` | +1.0pp | -0.9pp | +1.9pp | 54.9% | 0 |

## Scoreboard H60 (best IS win-lift clock per session -> median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `bar1_follow` | +1.7pp | +0.1pp | -2.7pp | 53.2% | 0 |
| `bar5_follow` | +2.0pp | +0.3pp | -1.1pp | 54.1% | 0 |

## Scoreboard SESS_END (best IS win-lift clock per session -> median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `bar1_follow` | +1.6pp | -2.1pp | -0.4pp | 56.3% | 0 |
| `bar5_follow` | +1.7pp | +0.8pp | -1.7pp | 55.7% | 0 |

## Candidates

**None.**

## Residual left at revelation entry (HIGH, diagnostic)

| Resolver | Session | Split | n | Mean resid@T H30 | Mean resid@entry H30 | Mean burn | Mean resid/psr |
|----------|---------|-------|---|------------------|----------------------|-----------|----------------|
| `bar1_follow` | LONDON | IS | 3485 | 9.9 | 9.8 | 0.1 | 0.4 |
| `bar1_follow` | LONDON | Validation | 1574 | 25.3 | 25.1 | 0.2 | 0.4 |
| `bar1_follow` | LONDON | OOS | 369 | 39.3 | 39.0 | 0.4 | 0.4 |
| `bar1_follow` | NY_PM | IS | 3658 | 17.7 | 17.6 | 0.1 | 0.3 |
| `bar1_follow` | NY_PM | Validation | 1415 | 45.7 | 45.6 | 0.1 | 0.3 |
| `bar1_follow` | NY_PM | OOS | 673 | 71.2 | 70.4 | 0.8 | 0.3 |
| `bar1_follow` | NY_AM | IS | 2345 | 21.4 | 21.2 | 0.2 | 0.8 |
| `bar1_follow` | NY_AM | Validation | 664 | 69.9 | 69.4 | 0.5 | 0.8 |
| `bar1_follow` | NY_AM | OOS | 440 | 103.5 | 101.8 | 1.8 | 0.8 |
| `bar1_follow` | ASIA | IS | 3377 | 11.8 | 11.8 | -0.0 | 0.3 |
| `bar1_follow` | ASIA | Validation | 1078 | 23.2 | 23.1 | 0.1 | 0.3 |
| `bar1_follow` | ASIA | OOS | 1221 | 42.8 | 42.6 | 0.1 | 0.3 |
| `bar5_follow` | LONDON | IS | 3840 | 9.6 | 9.2 | 0.4 | 0.4 |
| `bar5_follow` | LONDON | Validation | 1599 | 25.4 | 24.6 | 0.8 | 0.4 |
| `bar5_follow` | LONDON | OOS | 371 | 39.1 | 37.7 | 1.4 | 0.3 |
| `bar5_follow` | NY_PM | IS | 3826 | 17.3 | 17.1 | 0.2 | 0.3 |
| `bar5_follow` | NY_PM | Validation | 1437 | 45.7 | 46.0 | -0.3 | 0.3 |
| `bar5_follow` | NY_PM | OOS | 681 | 71.0 | 69.9 | 1.1 | 0.3 |
| `bar5_follow` | NY_AM | IS | 2408 | 21.2 | 20.8 | 0.4 | 0.8 |
| `bar5_follow` | NY_AM | Validation | 668 | 70.1 | 67.6 | 2.5 | 0.7 |
| `bar5_follow` | NY_AM | OOS | 444 | 103.3 | 97.7 | 5.6 | 0.8 |
| `bar5_follow` | ASIA | IS | 3877 | 10.9 | 10.7 | 0.1 | 0.3 |
| `bar5_follow` | ASIA | Validation | 1106 | 23.1 | 22.3 | 0.8 | 0.3 |
| `bar5_follow` | ASIA | OOS | 1240 | 42.6 | 41.5 | 1.1 | 0.3 |

## Verdict

**`C`**

Kill 21. First post-HIGH bar displacement does not provide stable conditional direction on the remaining path.

### Discipline

- Revelation class: information only after HIGH.
- Residual tables did not select the window.
- Strategy 12 remains WHEN-only.

