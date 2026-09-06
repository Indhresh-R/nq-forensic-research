# Strategy 24 — HOW: Sizing / Stops / Holding Conditional on Strategy-12 HIGH

**Program branch:** HOW (opened after family 23 hard stop).  
**Not a sign resolver.** Strategy 12 remains WHEN (A\*).

```text
WHEN (12) -> A* activity/path regime
HOW  (24) -> Strategy 12 activity does NOT monetize via sizing / width / HIGH-filter
            under tested direction-agnostic structures + realistic costs
            (24C holding-period still held as distinct mechanism)
```

## Sub-hypotheses

| Ticket | Question | Status |
|--------|----------|--------|
| **24A** | Vol-scaled sizing vs fixed | **C CLOSED** |
| **24B** | Stop/target distance conditional on regime | **Absorbed in 24D** (`regime_width` arm) — no separate dossier |
| **24C** | Holding period / time-stop conditional on regime | **Held** (only remaining distinct mechanism) |
| **24D** | Symmetric breakout / vol-harvest structure | **C** on HIGH harvest (Val `VAL_WIDE_DOMINATES`) |

## Locked HOW reading (24A+24D)

> Strategy 12's activity/expansion signal, while real, does not translate into
> monetizable value through sizing, width, or regime-filtering of a direction-agnostic
> structure under realistic costs. Wider stops help unconditionally (execution parameter),
> not because of HIGH.

Constraint: [`research_framework/direction_resolution.md`](../../research_framework/direction_resolution.md).
