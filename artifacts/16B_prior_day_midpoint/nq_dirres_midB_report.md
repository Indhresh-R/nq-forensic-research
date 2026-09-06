# Hypothesis 16B — Prior-Day Midpoint Location (resolver-only)

## Question

> Conditional on Strategy-12 HIGH, does sign(price_T - prior Globex day mid)
> resolve NQ direction better than the same rule unconditionally?

## Freeze

- Strategy 12 activity gate: **untouched** (WHEN only)
- `prior_mid = (prior_high + prior_low) / 2` of previous `session_date`
- Flat skip: `abs(close_T - mid) < max(0.25, 0.01 * prior_range)`
- H = [15, 30, 60, 90, 120] (pre-specified)
- No stops / targets / PDH-PDL variants
- Panel rows: **68,629**
- Soft candidates: **3**
- Strong candidates: **2**

## Primary contrast H=30 (best IS lift clock per session)

| Session | T+ | ALL+loc | HIGH+loc | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+loc OOS |
|---------|----|---------|----------|-----------|-------------|----------|----------|--------------|
| LONDON | 120 | 46.7% | 48.3% | 50.5% | +1.6pp | +0.7pp | -2.6pp | 43.8% |
| NY_PM | 120 | 50.0% | 50.1% | 53.7% | +0.1pp | +0.8pp | +0.7pp | 54.0% |
| NY_AM | 15 | 50.4% | 51.9% | 50.6% | +1.6pp | +4.4pp | +3.5pp | 52.1% |
| ASIA | 30 | 46.0% | 46.8% | 47.9% | +0.8pp | +3.2pp | -0.4pp | 47.7% |

## Primary contrast H=60 (best IS lift clock per session)

| Session | T+ | ALL+loc | HIGH+loc | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+loc OOS |
|---------|----|---------|----------|-----------|-------------|----------|----------|--------------|
| LONDON | 60 | 50.0% | 51.1% | 51.4% | +1.0pp | +0.9pp | +2.6pp | 52.9% |
| NY_PM | 120 | 51.2% | 53.5% | 56.0% | +2.3pp | -0.2pp | -3.0pp | 46.7% |
| NY_AM | 15 | 52.0% | 53.8% | 52.3% | +1.8pp | +0.8pp | +2.2pp | 53.5% |
| ASIA | 180 | 48.8% | 50.4% | 50.3% | +1.6pp | -3.9pp | -0.9pp | 52.1% |

## London lift vs ALL by H (best IS clock per H)

| H | T+ | HIGH+loc IS | ALL+loc IS | Lift IS | Lift Val | Lift OOS |
|---|----|-------------|------------|---------|----------|----------|
| 15 | 120 | 48.3% | 46.6% | +1.7pp | +1.8pp | -2.9pp |
| 30 | 120 | 48.3% | 46.7% | +1.6pp | +0.7pp | -2.6pp |
| 60 | 60 | 51.1% | 50.0% | +1.0pp | +0.9pp | +2.6pp |
| 90 | 120 | 50.0% | 48.0% | +2.0pp | -1.1pp | +2.4pp |
| 120 | 120 | 48.8% | 45.5% | +3.3pp | -1.8pp | +4.6pp |

## Multi-clock stability (candidates)

| Session | H | Soft/strong clocks | Strong clocks | Med lift IS | Med lift OOS |
|---------|---|--------------------|---------------|-------------|--------------|
| NY_AM | 60 | 1 | 1 | +1.8pp | +2.2pp |
| NY_AM | 90 | 1 | 1 | +1.2pp | +3.4pp |
| LONDON | 90 | 1 | 0 | +1.5pp | +1.1pp |
| LONDON | 120 | 1 | 0 | -0.3pp | +9.2pp |
| NY_AM | 120 | 1 | 0 | +2.2pp | +2.9pp |

## Verdict

**`B->kill`**

Soft/single-clock lift only. Do not promote. Do not expand to PDH/PDL variants to rescue this pass.

### Discipline

- Resolver-only (WHEN / WHICH WAY / HOW still separated).
- Strategy 12 remains a frozen opportunity regime detector.

