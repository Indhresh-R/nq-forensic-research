# Research tree — activity + direction resolution

**Updated:** 2026-09-06  
**Status:** 13–22 locked failed. **Family 23 CLOSED** (hard stop on 23D-ZN).  
Strategy 12 WHEN preserved. HOW not opened.

```text
                STRATEGY 12
                    |
              HIGH = travel (A*)
                    |
       +------------+------------+
       |                         |
 PRICE/STATE (13-22)        EXTERNAL (23) CLOSED
 FAIL locked                23A COT -> C (monotonic)
                            23D-ES -> C (IS kill)
                            23D-ZN -> C (IS kill, hard stop)
                            23D-ZB -> UNTESTED (not rescue)
```

## Program outcome

| Stage | Status |
|-------|--------|
| **WHEN** (12) | **A\* VALIDATED** |
| **WHICH WAY** (13–22) | **LOCKED FAILED** |
| **EXTERNAL** (23) | **CLOSED** |
| **HOW** | **Not opened** |

## Locked wording

> Strategy 12 appears to be a robust detector of an elevated future
> activity/path regime, but the tested information does not provide a
> stable incremental sign resolver.

**23A shape:** incremental +2.5 → −7.4 → −11.3pp (IS→Val→OOS).

**Stop:** no 5th external without a new argument. Next: HOW or stop.
