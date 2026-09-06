# Conclusion — 24A Vol-Scaled Sizing

## Verdict

**`C` CLOSED** (sizing claim only). Documentation triple: IS `IS_NULL` → Val `VAL_CONFIRMS_NULL` → OOS `OOS_NULL`.

Inverse-vol / HIGH-aware inv-vol do **not** improve risk-adjusted outcomes vs fixed size
on a direction-agnostic coin-flip book. Failure is mechanical (cost × |size|), not a soft
statistical leftover.

## Triple (coin-flip H=30, freeze unchanged)

| Split | fixed Sharpe | invvol ΔSharpe [90% CI] | HIGH-aware ΔSharpe [90% CI] |
|-------|--------------|-------------------------|------------------------------|
| IS | −1.90 | −3.27 [−3.60, −2.92] | −3.23 [−3.57, −2.85] |
| Val | −0.73 | −0.36 [−0.57, −0.15] | −0.31 [−0.57, −0.07] |
| OOS | +0.22 | −0.18 [−0.30, −0.06] | −0.18 [−0.43, +0.08] |

OOS absolute Sharpe noise-positive on fixed; **deltas** still favor fixed (invvol CI below 0).

## Failure mode

Zero-edge entry ⇒ E[PnL] ≈ −cost × |size|. Inv-vol upsizes quiet clocks → more cost drag.
HIGH-aware 0.70 trim softens but does not beat fixed. Long/short audit same pattern.

## What this does **not** kill

**24D** (symmetric breakout + regime-aware stop/target width) is a different mechanism:
whether HIGH's larger-move anticipation is monetizable via **structure**, not via sizing a
coin-flip. Closing 24D on 24A's null would be over-generalization.

## Next

24B/24C deferred. **24D** is the next ticket.
