# Strategy 17 — Session Extreme Trap (resolver-only)

## Question

> Conditional on Strategy-12 HIGH, does fading a recent session-extreme
> tag-and-fail (trapped side) resolve NQ direction better than unconditionally?

## Freeze

- W=15m; thr=max(0.50, 0.05*psr)
- Buyers trapped -> short; sellers trapped -> long
- Strategy 12 untouched
- H=[15, 30, 60, 90, 120]
- Panel rows: **25,201**
- Soft: **3**
- Strong: **1**

## Trap mix (panel)

- `sellers_trapped`: 50.9%
- `buyers_trapped`: 49.1%

## Primary contrast H=30 (best IS lift clock per session)

| Session | T+ | ALL+trap | HIGH+trap | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+trap OOS |
|---------|----|----------|-----------|-----------|-------------|----------|----------|----------------|
| LONDON | 30 | 50.5% | 53.1% | 49.4% | +2.6pp | -1.1pp | +8.6pp | 62.8% |
| NY_PM | 30 | 53.5% | 56.1% | 53.4% | +2.6pp | +3.3pp | -0.4pp | 48.8% |
| NY_AM | 60 | 48.2% | 50.5% | 53.9% | +2.3pp | -6.7pp | +1.1pp | 49.4% |
| ASIA | 120 | 45.4% | 51.0% | 55.5% | +5.6pp | -2.1pp | +7.6pp | 63.4% |

## Primary contrast H=60 (best IS lift clock per session)

| Session | T+ | ALL+trap | HIGH+trap | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+trap OOS |
|---------|----|----------|-----------|-----------|-------------|----------|----------|----------------|
| LONDON | 15 | 49.1% | 51.5% | 50.7% | +2.4pp | -0.3pp | -1.8pp | 51.4% |
| NY_PM | 90 | 49.8% | 50.3% | 55.3% | +0.5pp | -1.3pp | +6.3pp | 57.6% |
| NY_AM | 60 | 48.5% | 52.2% | 54.1% | +3.6pp | -8.6pp | -8.0pp | 38.0% |
| ASIA | 30 | 52.7% | 57.7% | 49.3% | +5.0pp | -3.7pp | +1.7pp | 41.4% |

## London lift vs ALL by H (best IS clock per H)

| H | T+ | HIGH+trap IS | ALL+trap IS | Lift IS | Lift Val | Lift OOS |
|---|----|--------------|-------------|---------|----------|----------|
| 15 | 15 | 54.5% | 50.7% | +3.7pp | -2.6pp | +8.1pp |
| 30 | 30 | 53.1% | 50.5% | +2.6pp | -1.1pp | +8.6pp |
| 60 | 15 | 51.5% | 49.1% | +2.4pp | -0.3pp | -1.8pp |
| 90 | 15 | 54.7% | 50.0% | +4.7pp | -4.0pp | -4.1pp |
| 120 | 15 | 52.8% | 50.4% | +2.4pp | -4.0pp | -2.7pp |

## Multi-clock stability (candidates)

| Session | H | Soft/strong clocks | Strong clocks | Med lift IS | Med lift OOS |
|---------|---|--------------------|---------------|-------------|--------------|
| ASIA | 120 | 1 | 1 | +1.6pp | +5.4pp |
| ASIA | 15 | 2 | 0 | +2.6pp | +3.8pp |
| LONDON | 15 | 1 | 0 | +3.0pp | +11.9pp |

## Verdict

**`B->kill`**

Soft or single-clock only. Do not promote. Do not retune W/thr to rescue.

### Discipline

- Vulnerability class first test; 16A/16B stay dead.
- Strategy 12 remains WHEN-only.

