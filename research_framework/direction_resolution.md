# Direction Resolution (Program Constraint)

**Status:** Strategies **13–22** locked failed (price/state). Strategy **12** preserved as WHEN (A\*).  
External family **23**: **CLOSED** (hard stop fired on 23D-ZN). **23D-ZB** remains UNTESTED (data gap — not a rescue).

Do **not** open Strategy 23 as another price/state resolver.

## Locked wording (13–22)

> Strategy 12 appears to be a robust detector of an elevated future
> activity/path regime, but the tested information does not provide a
> stable incremental sign resolver.

Narrower than “direction is unpredictable.” Defensible claim:

> Our tested observable information has failed to resolve direction robustly.

## Kill map (13–22)

| Layer | Tests | Result |
|-------|-------|--------|
| Before HIGH | 16A, 16B, 17, 20 | FAIL |
| At HIGH | 13, 15 (ES/NQ) | FAIL |
| After HIGH | 21 (first bar), 22 (0.25×psr ticket) | FAIL (`C`) |
| Longer horizon | 19 | FAIL |
| Residual econ | 14 | FAIL vs LOW |

## External family 23 — CLOSED

| Leg | Result | Failure mode (specific) |
|-----|--------|-------------------------|
| **23A** COT TFF | **C** | Incremental vs HIGH-long **monotonic** IS +2.5 → Val −7.4 → OOS −11.3pp |
| **23D-ES** overnight ES−NQ RS | **C** | IS-only; 0 strong / 24; all H30 clocks neg vs HIGH-long |
| **23D-ZN** overnight ZN−NQ RS | **C** | IS-only; 0 strong / 24; all H30 clocks neg vs HIGH-long |
| **23D-ZB** | **UNTESTED** | `ZB.FUT` never present (ZN dump duplicated). Not a null; **not** a rescue |

## Family-23 hard stop (pre-registered BEFORE bonds look — FIRED)

> If the available 23D-bonds leg(s) show **0 strong cells at IS**, or any
> **incremental sign-flip / worse-than-HIGH-long pattern** resembling 23A or 23D-ES,
> close the **entire external-source fork (Strategy 23 family)** as done.
> Do **not** open a 5th candidate (VIX, options skew, order flow, etc.) without a
> specific new argument for why COT / ES-overnight / bonds failing does **not**
> predict that the next external source will fail the same way.

**Fired 2026-09-06 on 23D-ZN IS** (0 strong; all H30 incremental neg). Family 23 done.

## Program outcome

```text
WHEN  -> A* (12)
WHICH WAY (13-22) -> locked failed
EXTERNAL (23) -> CLOSED (23A, 23D-ES, 23D-ZN = C; 23D-ZB untested, not rescue)
HOW -> not opened (next honest branch)
```

## Forbidden

- Strategy 23 as **another price/state resolver** (13–22 class)
- Retuning STRUCT_FRAC / windows against direction
- Claiming “direction is unpredictable” as proven
- Monetizing unsigned residual alone
- Treating **23D-ZB** as failed because ZN failed — or as a **rescue** after the hard stop
- 23B/23C COT retunes; 5th external without new argument
- “Just one more” external after hard stop

## Only re-open with

1. **HOW** — sizing / stops / holding conditional on Strategy 12 WHEN (activity), without claiming a new sign resolver.
2. Or a **fundamentally new** external information class with an explicit argument why COT+ES+ZN failure does not apply — frozen before look. (ZB alone is **not** that argument after the hard stop.)
