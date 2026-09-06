# Hypothesis 16A — Prior Globex Daily Bias A (resolver-only)

## Question

> Does previous completed Globex daily candle direction resolve NQ forward
> sign **better inside Strategy-12 HIGH** than unconditionally?

## Freeze

- Daily = `session_date` Globex day (18:00 ET roll)
- Bias A = sign(prior close − prior open) only
- H = [15, 30, 60, 90, 120] (pre-specified)
- No stops / targets / RR / Bias B–D
- Panel rows: **69,373**
- Soft candidates: **4**
- Strong candidates: **0**

## Primary contrast H=30 (best IS lift clock per session)

| Session | T+ | ALL+bias | HIGH+bias | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+bias OOS |
|---------|----|----------|-----------|-----------|-------------|----------|----------|---------------|
| LONDON | 60 | 49.7% | 51.8% | 49.0% | +2.1pp | -2.1pp | +0.5pp | 52.8% |
| NY_PM | 60 | 50.0% | 51.3% | 53.5% | +1.3pp | +5.7pp | -1.6pp | 45.8% |
| NY_AM | 90 | 50.1% | 50.5% | 56.0% | +0.4pp | -0.7pp | +0.9pp | 53.3% |
| ASIA | 30 | 48.5% | 49.5% | 47.9% | +1.1pp | +1.8pp | +0.3pp | 51.8% |

## Primary contrast H=60 (best IS lift clock per session)

| Session | T+ | ALL+bias | HIGH+bias | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+bias OOS |
|---------|----|----------|-----------|-----------|-------------|----------|----------|---------------|
| LONDON | 120 | 49.2% | 51.3% | 48.2% | +2.0pp | +0.7pp | -7.9pp | 42.2% |
| NY_PM | 120 | 50.9% | 54.0% | 56.3% | +3.0pp | -2.7pp | -1.9pp | 46.0% |
| NY_AM | 15 | 50.8% | 51.7% | 52.4% | +0.8pp | +1.0pp | -2.7pp | 47.6% |
| ASIA | 120 | 47.0% | 47.5% | 52.0% | +0.5pp | +0.8pp | -0.6pp | 47.4% |

## London lift vs ALL by H (best IS clock per H)

| H | T+ | HIGH+bias IS | ALL+bias IS | Lift IS | Lift Val | Lift OOS |
|---|----|--------------|-------------|---------|----------|----------|
| 15 | 120 | 52.9% | 49.4% | +3.5pp | -1.6pp | -5.2pp |
| 30 | 60 | 51.8% | 49.7% | +2.1pp | -2.1pp | +0.5pp |
| 60 | 120 | 51.3% | 49.2% | +2.0pp | +0.7pp | -7.9pp |
| 90 | 120 | 52.0% | 48.8% | +3.3pp | +1.6pp | +1.5pp |
| 120 | 120 | 51.8% | 48.1% | +3.7pp | +2.9pp | +0.0pp |

## Multi-clock stability (candidates)

| Session | H | Soft/strong clocks | Strong clocks | Med lift IS | Med lift OOS |
|---------|---|--------------------|---------------|-------------|--------------|
| ASIA | 120 | 1 | 0 | +3.5pp | -0.2pp |
| LONDON | 90 | 1 | 0 | +3.3pp | +1.5pp |
| LONDON | 120 | 1 | 0 | +3.7pp | +0.0pp |
| NY_PM | 120 | 1 | 0 | +0.7pp | +1.8pp |

## Verdict

**`B→kill`**

Soft/single-clock lift only. Do not promote. Do not open Bias B/C/D to rescue.

### Discipline

- This pass is **resolver-only** (no trade card).
- If killed: next is **16B as a separate dossier**, not a parameter rescue.

