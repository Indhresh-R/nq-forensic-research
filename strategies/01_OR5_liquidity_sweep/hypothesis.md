# Hypothesis — OR5 Liquidity Sweep Fade

## Market behavior under test

Opening-range (5m) liquidity sweeps reverse and produce a tradable fade.

## Economic / mechanical rationale

Stop runs beyond the opening range may exhaust short-term liquidity and reverse.

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
