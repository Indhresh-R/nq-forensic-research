# Rules — Multi-session direction (Phase B)

## Frozen trade card

| Item | Value |
|------|-------|
| Sessions | ASIA, LONDON, NY_AM, NY_PM (independent; report LONDON→NY_PM→NY_AM→ASIA) |
| HIGH | `rng_psr >= IS_p66` from strategy 12 thresholds |
| Follow | `side = sign(close_T - session_open)` |
| Fade | opposite |
| Entry | next bar open after T; stress = +1 bar delay |
| Stop | `0.25 * psr` |
| Target | `0.25 * psr` (1R) |
| Max hold | 15 / 30 / 45 (primary 30) |
| Same-bar | stop first |
| Costs RT | tight 0.50 / mid 1.00 / wide 2.00 pts |

## Forbidden

- Retuning terciles, stops, targets, or holds on outcomes
- Combining sessions into one book before each clears the gate
- Reusing NY-open ONR thresholds
