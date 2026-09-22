# ORB First-Passage Report — Strategy 59

**Target + adverse co-defined.** Not Event D. No 52–58 reopen. No horizon shopping.

## Funnel

- n_sessions_seen: 3604
- n_or_ok: 3594
- n_events: 3319
- n_no_break: 275
- n_or_incomplete: 10

## Freeze / audit

```text
LOOKAHEAD_CHECK = PASS
TARGET_ADVERSE_CO_DEFINED = True
NO_PARAMETER_RETUNE = True
NO_52_58_REOPEN = True
```

## Step 1 — First-passage

| split | n | p_target_first | p_adverse_first | p_unresolved | delta_fp |
| --- | --- | --- | --- | --- | --- |
| IS | 2203 | 0.1575 | 0.3677 | 0.4748 | -0.2102 |
| Validation | 727 | 0.1788 | 0.3741 | 0.4470 | -0.1953 |
| OOS | 389 | 0.1311 | 0.3805 | 0.4884 | -0.2494 |
| ALL | 3319 | 0.1591 | 0.3706 | 0.4703 | -0.2115 |

- **Classification:** `KILL`
- **Reason:** `IS_first_passage`

## Step 2 — MAE

Not run (Step 1 did not advance).

## Step 3 — Time to resolve (descriptive)

| split | outcome | n | med_bars | p25 | p75 |
| --- | --- | --- | --- | --- | --- |
| IS | target_first | 347 | 29.0 | 15.0 | 42.0 |
| IS | adverse_first | 810 | 22.0 | 13.0 | 38.0 |
| IS | unresolved | 1046 | 60.0 | 60.0 | 60.0 |
| Validation | target_first | 130 | 30.0 | 15.0 | 43.0 |
| Validation | adverse_first | 272 | 21.0 | 11.0 | 32.2 |
| Validation | unresolved | 325 | 60.0 | 60.0 | 60.0 |
| OOS | target_first | 51 | 28.0 | 15.5 | 45.0 |
| OOS | adverse_first | 148 | 22.5 | 12.0 | 32.2 |
| OOS | unresolved | 190 | 60.0 | 60.0 | 60.0 |
| ALL | target_first | 528 | 29.0 | 15.0 | 42.2 |
| ALL | adverse_first | 1230 | 22.0 | 13.0 | 36.0 |
| ALL | unresolved | 1561 | 60.0 | 60.0 | 60.0 |

## Step 4 — Trade

Not run.

## STRATEGY 59 FINAL

**KILL**. Do not retune W_or / target / adverse. Do not reopen 52–58.
