# Strategy 20 — Pre-HIGH Unusual Displacement

## Freeze

- W=30m into T; unusual = IS p66 of |metric|/psr
- Resolvers: `disp_follow`, `path_follow` (skip if not unusual)
- Outcomes: ['H30', 'H60', 'SESS_END']
- Win-lift gates only; Strategy 12 untouched
- Panel rows: **41,159**
- Soft: **2**
- Strong: **0**

## Scoreboard H30 (best IS win-lift → median across sessions)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `disp_follow` | +1.3pp | -0.2pp | -4.7pp | 58.6% | 0 |
| `path_follow` | +1.3pp | -0.2pp | -4.7pp | 58.6% | 0 |

## Scoreboard H60 (best IS win-lift → median across sessions)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `disp_follow` | +1.0pp | +1.5pp | +0.6pp | 57.6% | 0 |
| `path_follow` | +1.0pp | +1.5pp | +0.6pp | 57.6% | 0 |

## Scoreboard SESS_END (best IS win-lift → median across sessions)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |
|----------|-------------|--------------|--------------|---------------|-------|
| `disp_follow` | +2.1pp | +2.0pp | +2.4pp | 58.3% | 1 |
| `path_follow` | +2.1pp | +2.0pp | +2.4pp | 58.3% | 1 |

## Candidates

| Tier | Resolver | Session | Outcome | T+ | Lift IS | Lift Val | Lift OOS | HIGH OOS |
|------|----------|---------|---------|----|---------|----------|----------|----------|
| soft | `disp_follow` | NY_PM | SESS_END | 60 | +3.4pp | +2.8pp | +6.1pp | 54.0% |
| soft | `path_follow` | NY_PM | SESS_END | 60 | +3.4pp | +2.8pp | +6.1pp | 54.0% |

## Verdict

**`B->kill`**

Soft/strong=2 without multi-clock strength. Do not retune W/p66. Do not fall back to ordinary mom follow.

### Discipline

- This is initiative-*unusual*, not generic follow.
- Strategy 12 remains WHEN-only.

