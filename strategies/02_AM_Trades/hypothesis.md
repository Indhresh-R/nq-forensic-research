# Hypothesis — AM Trades (Manipulation / Continuation)

## Market behavior under test

Named AM-trade patterns (manipulation then continuation) identify NQ direction at the NY open.

## Economic / mechanical rationale

Intraday narrative patterns may encode informed flow after the cash open.

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
