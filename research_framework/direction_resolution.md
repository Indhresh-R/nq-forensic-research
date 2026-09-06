# Direction Resolution (Program Constraint)

**Status: CLOSED** — Strategies **13–22** locked failed. Strategy **12** preserved as WHEN (A\*).  
Do **not** open Strategy 23 as another price/state resolver.

## Locked wording

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

Strategy 22: revelation often fires; residual remains; incremental lift fails Val;
soft/strong **0**.

## Program outcome

```text
WHEN  -> A* (12)
WHICH WAY -> locked failed (13-22)
HOW -> not opened
```

A real, reproducible activity/path phenomenon can exist without being
monetizable in the obvious direction-prediction framework.

## Forbidden

- Strategy 23 “one more resolver”
- Retuning STRUCT_FRAC / windows against direction
- Claiming “direction is unpredictable” as proven
- Monetizing unsigned residual alone

## Only re-open with

An **external causal information source** (fundamentally different branch),
frozen before any directional look — not another technical-price encoding.
