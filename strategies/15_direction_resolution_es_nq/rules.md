# Rules — ES/NQ direction resolution

## Frozen activity gate (do not retune)

- Source: Strategy 12 `nq_multi_sess_opp_thresholds_IS.json`
- HIGH: `rng_psr >= IS_p66` at (session, T_offset)
- LOW: `rng_psr <= IS_p33`
- Sessions independent; report order LONDON → NY_PM → NY_AM → ASIA

## Resolvers R (independent, pre-specified — not a mining grid)

From session open → T (%-returns), ES bar aligned at same `ny_min`:

| ID | Side for NQ |
|----|-------------|
| `follow_es` | sign(ES open→T) |
| `rs_continue` | sign(NQ% − ES%) |
| `agree_follow` | sign(NQ%) only if sign(NQ%)==sign(ES%); else skip |

Skip flat signs.

## Outcome

- Entry: NQ next bar open after T
- Horizon H ∈ {15, 30} (primary 30)
- `pnl = side * (close_{T+H} - entry)` in NQ points
- Cost stress: mid 1.0 pt RT deducted for net metrics (not optimized)

## Critical contrasts

For each R × session × T × H:

1. Universe ALL (unconditional)
2. Universe HIGH
3. Universe LOW
4. Lift = metric(HIGH) − metric(ALL)

## Forbidden

- Retuning activity terciles
- Combining resolvers
- Stop/target mining
- Claiming success from HIGH-only prints without lift
