# Step 9 — Executable hypothesis test

**Status:** Complete (single frozen trade test).
**Scope:** One hypothesis. No optimization. No extra filters.

## Research question

Can the observed low-transition-ER ExpExit destination asymmetry be converted into positive net expectancy under a simple, fixed entry/exit rule and realistic NQ costs (1.0 pt RT)?

## Frozen hypothesis H1

Low-ER ExpExit D: fade toward P_mid; entry open[te+1]; exit close[te+15]; cost 1.0 pt RT; no SL/TP

- Primary arm: **D only** (promotion gate).
- Control arm: **C** with the identical fade-to-mid / 15m rule (diagnostic only).
- Population: frozen Step 7 low-ER ExpExit event ids.

## Leakage / freeze audit

```text
LOOKAHEAD_CHECK = PASS
EVENT_POPULATION_FROZEN = PASS
ENTRY_NEXT_OPEN_AFTER_TE = True
PARAMETER_OPTIMIZATION = False
EXTRA_FILTERS = False
COST_RT = 1.0
HOLD_MINUTES = 15
```

## Results — primary D arm

| split | n_trades | n_long | n_short | mean_gross | mean_net | median_net | hit_rate_net_gt_0 | eligible_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IS | 3496 | 1874 | 1622 | -0.1363 | -1.1363 | -1.0000 | 0.3947 | True |
| Validation | 818 | 402 | 416 | -0.2833 | -1.2833 | -1.2500 | 0.4609 | True |
| OOS | 506 | 282 | 224 | 1.8869 | 0.8869 | 0.2500 | 0.5059 | True |
| ALL | 4820 | 2558 | 2262 | 0.0511 | -0.9489 | -1.0000 | 0.4176 | True |


## Results — control C arm (not used for promotion)

| split | n_trades | mean_gross | mean_net | median_net | hit_rate_net_gt_0 |
| --- | --- | --- | --- | --- | --- |
| IS | 3320 | 0.4032 | -0.5968 | -1.0000 | 0.4018 |
| Validation | 741 | -0.3704 | -1.3704 | -2.7500 | 0.4399 |
| OOS | 413 | -2.6634 | -3.6634 | -2.0000 | 0.4600 |
| ALL | 4474 | -0.0080 | -1.0080 | -1.2500 | 0.4135 |


## Gate detail

- **IS:** n=3496, E_net=-1.1362986270022883, eligible=True, pass=False
- **Validation:** n=818, E_net=-1.2833129584352079, eligible=True, pass=False
- **OOS:** n=506, E_net=0.8868577075098815, eligible=True, pass=True

## STEP 9 VERDICT

**Classification:** `KILL`

**Decision:** `STOP_DO_NOT_BUILD_STRATEGY`

No — primary D arm fails the preregistered expectancy gate; kill.

Mechanism interest does not override this gate. **Stop. Do not build a strategy** from this hypothesis.
