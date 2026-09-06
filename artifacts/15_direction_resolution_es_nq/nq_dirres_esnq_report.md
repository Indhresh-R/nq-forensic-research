# Strategy 15 — ES/NQ Direction Resolution (conditional lift)

## Question

> Conditional on Strategy-12 activity HIGH, does ES/NQ signed information
> resolve NQ direction **better than the same resolver unconditionally**?

## Freeze

- Activity: Strategy 12 `rng_psr` IS terciles (untouched)
- Resolvers: follow_es, rs_continue, agree_follow
- Primary H=30; cost stress mid=1.0 pt (reported in panel E_net)
- Sessions independent: LONDON → NY_PM → NY_AM → ASIA
- Panel rows: **195,058**
- Soft candidates: **8**
- Strong candidates: **0**

## Lift table (H30, best IS lift_win clock per session×resolver)

| Session | Resolver | T+ | HIGH IS win | ALL IS win | Lift IS | Lift Val | Lift OOS | HIGH OOS win |
|---------|----------|----|-------------|------------|---------|----------|----------|--------------|
| LONDON | follow_es | 15 | 48.0% | 47.2% | +0.8pp | +2.1pp | -2.7pp | 44.8% |
| LONDON | rs_continue | 30 | 50.2% | 48.5% | +1.7pp | -0.7pp | -0.5pp | 43.3% |
| LONDON | agree_follow | 15 | 48.1% | 47.2% | +0.9pp | +1.9pp | -2.7pp | 44.4% |
| NY_PM | follow_es | 15 | 48.0% | 48.2% | -0.2pp | +1.8pp | -0.5pp | 45.5% |
| NY_PM | rs_continue | 120 | 50.6% | 48.9% | +1.6pp | -3.5pp | +2.7pp | 51.8% |
| NY_PM | agree_follow | 120 | 50.4% | 50.1% | +0.3pp | -0.0pp | -0.5pp | 49.6% |
| NY_AM | follow_es | 15 | 53.5% | 50.3% | +3.2pp | -1.5pp | +0.7pp | 49.6% |
| NY_AM | rs_continue | 15 | 51.0% | 50.3% | +0.7pp | -0.8pp | +0.8pp | 51.0% |
| NY_AM | agree_follow | 15 | 53.6% | 50.2% | +3.4pp | -2.5pp | +0.4pp | 48.8% |
| ASIA | follow_es | 180 | 50.4% | 48.0% | +2.4pp | -5.3pp | +6.1pp | 56.1% |
| ASIA | rs_continue | 90 | 49.8% | 48.2% | +1.6pp | -3.0pp | +2.1pp | 52.0% |
| ASIA | agree_follow | 180 | 49.1% | 47.9% | +1.2pp | -6.4pp | +6.7pp | 56.0% |

## Multi-clock stability (candidates)

| Session | Resolver | H | Soft/strong clocks | Strong clocks | Med lift IS | Med lift OOS |
|---------|----------|---|--------------------|---------------|-------------|--------------|
| NY_PM | follow_es | 30 | 2 | 0 | -0.9pp | -1.8pp |
| NY_PM | agree_follow | 30 | 1 | 0 | -1.2pp | -2.8pp |
| NY_AM | rs_continue | 30 | 1 | 0 | -1.1pp | -0.0pp |
| NY_AM | follow_es | 15 | 1 | 0 | +0.8pp | +1.4pp |
| NY_AM | agree_follow | 15 | 1 | 0 | +0.8pp | +2.5pp |
| NY_PM | follow_es | 15 | 1 | 0 | -0.5pp | -1.1pp |
| NY_PM | agree_follow | 15 | 1 | 0 | -0.4pp | -1.1pp |

## Verdict

**`B`**

Each X independent. Soft/single-clock lift only → **B→kill** (not a trade).

### Research implication

First signed-information source (ES/NQ) fails stable conditional lift.
Next dossier needs a **different** sign source (trapped side, inventory,
options lag, etc.) — not more ES variants.

