# Direction Resolution (Program Constraint)

**Status:** Strategies **13–22** locked failed (price/state). Strategy **12** preserved as WHEN (A\*).  
External family **23**: **CLOSED** (hard stop fired on 23D-ZN). **23D-ZB** remains UNTESTED (data gap — not a rescue).

**HOW (Strategy 24):** **OPENED**. **24A** sizing **C CLOSED**. **24D** HIGH-harvest **C**
(Val `VAL_WIDE_DOMINATES`; width helps unconditionally). **24B absorbed in 24D**.
**24C held** (distinct mechanism).

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

## HOW family 24 — OPENED

| Ticket | Question | Status |
|--------|----------|--------|
| **24A** vol-scaled sizing | Inv-vol ± HIGH-aware vs fixed, coin-flip book | **C CLOSED** |
| **24B** stop/target by regime | Same as 24D `regime_width` arm | **Absorbed / closed via 24D** (no separate dossier) |
| **24C** holding period by regime | Time-stop / hold length by HIGH | **Held** — unlock after 24D Val (done); await go-ahead |
| **24D** non-directional vol-harvest | Symmetric breakout + width policies | **C** on HIGH harvest — Val `VAL_WIDE_DOMINATES` |

**Decisive 24D cell:** `regime_width` − `uncond_wide` ΔSharpe IS −3.10 → Val **−2.79**
[−3.53, −2.12]. Best policy still E < 0.

**Locked HOW reading:** Strategy 12 activity is real but does not monetize via sizing,
width, or regime-filter of a direction-agnostic structure under costs; wider helps
unconditionally, not because of HIGH.

## Program outcome

```text
WHEN  -> A* (12)
WHICH WAY (13-22) -> locked failed
EXTERNAL (23) -> CLOSED (23A, 23D-ES, 23D-ZN = C; 23D-ZB untested, not rescue)
HOW -> opened, Strategy 24
       24A C CLOSED | 24B absorbed in 24D | 24D C (wide dominates) | 24C held
```

## Forbidden

- Strategy 23 as **another price/state resolver** (13–22 class)
- Retuning STRUCT_FRAC / windows against direction
- Claiming “direction is unpredictable” as proven
- Monetizing unsigned residual alone
- Treating **23D-ZB** as failed because ZN failed — or as a **rescue** after the hard stop
- 23B/23C COT retunes; 5th external without new argument
- “Just one more” external after hard stop
- Smuggling a directional claim into HOW tickets (24A–D)

## Only re-open with

1. **HOW** — sizing / stops / holding conditional on Strategy 12 WHEN (activity), without claiming a new sign resolver. *(opened as Strategy 24)*
2. Or a **fundamentally new** external information class with an explicit argument why COT+ES+ZN failure does not apply — frozen before look. (ZB alone is **not** that argument after the hard stop.)
