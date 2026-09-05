# Hypothesis — NY Open State Transitions

## Market behavior under test

Simple morning state transitions map to next-bar directional returns.

## Economic / mechanical rationale

Discrete regime labels at the open might compress path information into a tradable state.

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
