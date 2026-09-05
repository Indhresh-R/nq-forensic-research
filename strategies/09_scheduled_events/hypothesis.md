# Hypothesis — Scheduled Macro Events

## Market behavior under test

CPI/NFP/FOMC/PPI/CLAIMS releases create persistent post-release directional asymmetry vs same-TOD non-event controls.

## Economic / mechanical rationale

Information discontinuities should reprice risk assets directionally, not only raise volatility.

## What would count as success

- Causal signal (information only through T; outcomes from T+1 / next open)
- IS → Validation → OOS persistence
- 2025 and 2026 checked separately where sample allows
- Multi-clock or multi-horizon stability (ignore isolated single-clock ~55–60% winners)
- No parameter mining / no rescue combinations of dead mechanisms

## What would count as failure

- Near-50% direction with no stable payoff asymmetry
- Effects that invert across Val/OOS/years
- Contamination (lookahead, same-bar ambiguity abused, end-of-day used intraday)
