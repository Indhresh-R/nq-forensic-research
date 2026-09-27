# Verdict — Volume-profile mechanism branch (Steps 1–5)

Date frozen: 2026-09-21.

This file closes the Step 1–5 research branch. Do not retune any cut in this branch against a later return, and do not add ATR, direction, time-of-day, POC-distance, day-of-week, or volatility filters to rescue the LVN object.

## Final status

| Object | Status |
| --- | --- |
| P / b / D / B as primary representation | **Rejected** |
| Accepted HVN regions (descriptive) | **Useful** |
| Prior HVN–LVN–HVN boundary as an interaction object | **Frequently touched** (Step 3) |
| HVN → LVN → opposite HVN **traversal** | **Killed** (Step 4; at or below geometric null) |
| HVN → LVN → **rejection** | **Killed** after null calibration (Step 5) |

## Why Step 5 closes rejection

Raw rejection counts look large (H60: 19/34 = 55.9%). The geometric null already expects ~83.5%. Observed − null is **−27.6 pp** unconditionally. Removing touch-bar approach-HVN hits makes the gap worse (Null D: −38.0 pp). About 8/19 H60 rejects are same-minute with the LVN touch. Most rejects never clear the far LVN edge (`band_only`).

So:

> The observed rejection frequency is **lower** than what the geometric setup itself predicts.

The classic trap — “price rejected the LVN ~60% of the time, therefore LVNs are support/resistance” — is exactly what the null rules out on this sample.

## What this branch established

1. Textbook letter shapes are the wrong primary abstraction for these NQ profiles.
2. Multi-node volume structure is common; accepted-region description is workable.
3. A material spatial separation creates a prior boundary that the next session often prints into.
4. That boundary does **not** support a preferential traverse or a null-beating short-horizon rejection under the frozen definitions.

Volume profile is not shown to be useless. The intuitive **separated HVN → LVN boundary → reaction/traversal** story is not supported here.

## Branch rule

**No Step 6 that re-tests this same LVN object with filters.**

Any later return test that assumes LVN traverse or LVN rejection as the typical path would be testing a killed mechanism.

## Next research direction (separate branch)

Ask a different question about the same prior volume field:

> Does prior-session **volume concentration / location** inform where the next session trades, rather than whether price reacts at an LVN?

That is volume **acceptance / location**, not support/resistance on a low-volume band. Definitions for that branch live in `STEP6_PREREGISTRATION.md` and must be frozen before any next-session location table is computed.
