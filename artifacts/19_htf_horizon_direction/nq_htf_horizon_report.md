# Strategy 19 — Longer-Horizon Direction under Strategy-12 HIGH

## HIGH forward skew (no resolver)

| Session | Outcome | Split | n | P(up) | E[pts] |
|---------|---------|-------|---|-------|--------|
| LONDON | H240 | IS | 3268 | 54.8% | +0.72 |
| LONDON | H240 | Validation | 1315 | 49.7% | -1.20 |
| LONDON | H240 | OOS | 318 | 57.9% | +2.72 |
| LONDON | SESS_END | IS | 3274 | 53.4% | +0.85 |
| LONDON | SESS_END | Validation | 1315 | 48.7% | -3.31 |
| LONDON | SESS_END | OOS | 318 | 53.8% | +5.28 |
| NY_PM | SESS_END | IS | 3215 | 53.8% | -0.07 |
| NY_PM | SESS_END | Validation | 1174 | 54.0% | +2.11 |
| NY_PM | SESS_END | OOS | 560 | 56.8% | +12.84 |
| NY_AM | SESS_END | IS | 2459 | 54.9% | +0.81 |
| NY_AM | SESS_END | Validation | 703 | 54.1% | +0.27 |
| NY_AM | SESS_END | OOS | 437 | 54.5% | -2.30 |
| ASIA | H240 | IS | 3387 | 53.9% | +1.41 |
| ASIA | H240 | Validation | 904 | 53.4% | +7.89 |
| ASIA | H240 | OOS | 1021 | 51.0% | -4.53 |
| ASIA | SESS_END | IS | 3493 | 55.3% | +3.14 |
| ASIA | SESS_END | Validation | 904 | 55.8% | +7.66 |
| ASIA | SESS_END | OOS | 1026 | 52.4% | -3.21 |

## Scoreboard — SESS_END (best IS win-lift clock per session, then median)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Gate cells |
|----------|-------------|--------------|--------------|---------------|------------|
| `gap_follow` | +0.8pp | +2.3pp | +2.0pp | 54.2% | 1 |
| `prior_day_color` | +2.2pp | +2.5pp | +0.6pp | 54.6% | 0 |
| `prior_sess_mid` | +0.1pp | -0.1pp | +0.9pp | 60.8% | 0 |
| `sess_open_follow` | -0.8pp | -1.4pp | +2.3pp | 61.4% | 0 |
| `vwap_follow` | +0.1pp | -0.3pp | +4.9pp | 58.2% | 0 |
| `mom15_follow` | +1.1pp | +1.2pp | +3.4pp | 60.0% | 0 |

## Scoreboard — H240 (same)

| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Gate cells |
|----------|-------------|--------------|--------------|---------------|------------|
| `gap_follow` | +0.5pp | -0.4pp | +1.8pp | 56.7% | 0 |
| `prior_day_color` | +1.7pp | +1.1pp | -1.7pp | 51.5% | 0 |
| `prior_sess_mid` | +1.0pp | -0.9pp | -1.7pp | 53.5% | 0 |
| `sess_open_follow` | +1.6pp | +0.6pp | -1.7pp | 56.6% | 0 |
| `vwap_follow` | +1.3pp | +2.1pp | -1.5pp | 54.5% | 0 |
| `mom15_follow` | +2.2pp | +1.4pp | +2.1pp | 58.8% | 0 |

## Candidates (win-lift gate only)

| Tier | Resolver | Session | Outcome | T+ | Lift IS | Lift Val | Lift OOS | HIGH OOS |
|------|----------|---------|---------|----|---------|----------|----------|----------|
| soft | `gap_follow` | NY_AM | SESS_END | 30 | +3.3pp | +3.7pp | +4.9pp | 53.7% |

## Verdict

**`B->kill`**

Soft/strong cells=1 without multi-clock strength. Do not promote.

### Discipline

- Win-lift gates only (no E-lift rescue).
- Strategy 12 untouched.

