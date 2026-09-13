# Hypothesis

Publicly reconstructed SPX 0DTE dealer-gamma positioning (FirmTape measured net gamma, conventional OI gamma, volume-convention gamma, zero-gamma flip) changes the **conditional distribution** of subsequent S&P 500 / ES intraday returns, realized volatility, continuation, and reversal.

## Primary mechanism (to attack, not assume)

- **Positive dealer gamma**: dealers hedge by fading moves → lower subsequent RV, weaker persistence, more mean reversion.
- **Negative dealer gamma**: dealers hedge by reinforcing moves → higher subsequent RV, stronger momentum.

## Secondary

Any relationship must survive causal timing, costs, multiple-testing controls, hostile placebos, and chronological OOS (2025–2026). Transfer to NQ is tested separately.

## Non-goals

- Do not assume GEX predicts direction.
- Do not optimize thresholds / holds / filters after seeing OOS.
