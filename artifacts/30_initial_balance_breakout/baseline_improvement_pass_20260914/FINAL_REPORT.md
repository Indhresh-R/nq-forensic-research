# NQ Initial Balance breakout — baseline improvement test

Research pass date: 2026-09-14. This is a completed, single-pass test under
`PREREGISTRATION.md`. No Validation or OOS data was used for ranking or selection.

## Locked data gates

| Gate | Date range |
|---|---|
| Train | 2010-01-01 to 2018-12-31 |
| Inner Validation | 2019-01-01 to 2021-12-31 |
| Validation | 2022-01-01 to 2024-12-31 |
| OOS | 2025-01-01 to 2026-12-31 (available data only) |

Instrument: continuous NQ one-minute OHLCV. Session: 09:30–15:55 ET, IB
09:30–10:29. Execution: first qualifying five-minute close, next one-minute
open, one trade/session, 15:55-open exit, stop first on same-bar collision.
Costs: 1.00 NQ index point round trip ($20/point/contract).

## Pre-registered candidates

1. Baseline control — opposite-IB stop, 1R target.
2. Half-IB stop — 0.50 × IB width from entry; 1R target.
3. 1.5R target — opposite-IB stop; 1.5R target.
4. Early-breakout filter — unchanged exits, signal close no later than 11:59 ET.
5. Half-IB stop + early-breakout filter — #2 and #4 only.

## Step 2 — Train + Inner Validation ranking

Selection rule, set before any later-gate result: highest combined Train +
Inner Validation profit factor, subject to at least 100 Train and 50 Inner
Validation trades; ties by combined average net points/trade then trade count.

| Rank | Candidate | Train: n / PF / avg pt | Inner: n / PF / avg pt | Combined: n / PF / avg pt |
|---:|---|---:|---:|---:|
| 1 | Baseline control | 1,441 / 0.8975 / -0.9917 | 677 / 1.1375 / 3.5358 | 2,118 / 1.0308 / 0.4555 |
| 2 | 1.5R target | 1,441 / 0.8941 / -1.0499 | 677 / 1.1310 / 3.4387 | 2,118 / 1.0254 / 0.3849 |
| 3 | Half-IB stop | 1,441 / 0.8830 / -0.8199 | 677 / 1.1144 / 2.1841 | 2,118 / 1.0129 / 0.1403 |
| 4 | Early-breakout filter | 1,115 / 0.8937 / -1.1164 | 527 / 1.0797 / 2.2865 | 1,642 / 0.9985 / -0.0242 |
| 5 | Half-IB stop + early filter | 1,115 / 0.9032 / -0.6996 | 527 / 1.0702 / 1.4208 | 1,642 / 0.9983 / -0.0190 |

All variants met the minimum sample rule. The baseline control was selected,
because its combined PF (1.0308) was highest. Consequently, none of the four
rule changes improved the control on the prespecified selection metric.

Using average net points/trade versus control as the simple per-gate directional
comparison, the changed candidates were: 1.5R target **no/no** (Train/Inner);
half-IB stop **yes/no**; early-breakout **no/no**; and half-IB + early **yes/no**.
Neither partial Train lift survived Inner Validation, and none outranked the
control on combined PF.

## Step 4 — Validation confirmation

The only selected variant, baseline control, was run once on Validation:

| Variant | Trades | Net points | Avg net points | PF | Max DD points | Improved vs baseline? |
|---|---:|---:|---:|---:|---:|---|
| Selected baseline control | 695 | 3,149.00 | 4.5309 | 1.1132 | -1,275.75 | **No** (identical control) |
| Frozen baseline reference | 695 | 3,149.00 | 4.5309 | 1.1132 | -1,275.75 | — |

It failed the preregistered strict-improvement criterion. The baseline control
is **rejected as an improvement candidate and will not be retested**. The four
unselected changed variants were not run on Validation; testing them would
violate the one-selection rule. They are rejected in this pass by Step 2 and
will not be retested here.

## Step 5 — OOS

Not run. The protocol permits an OOS run only after a Validation pass. Therefore
OOS improvement is **no (gate not reached after Validation failure)**, not an
unobserved positive result.

## Gate verdict and tradability

| Gate | Improved on baseline? |
|---|---|
| Train + Inner Validation | No — no changed variant beat the control on the locked ranking metric |
| Validation | No — selected control equalled, rather than exceeded, the baseline |
| OOS | No — prohibited after Validation failure |

No survivor exists, so no stress test or tradability determination is
permitted. For context only, the selected control's Validation average risk
was 151.47 points ($3,029.47 per contract) and maximum drawdown was 1,275.75
points ($25,515 per contract), reinforcing that it cannot be called tradable
from this pass merely because its raw Validation expectancy was positive.

**Improved on baseline: no. Ready for further testing: no.**
