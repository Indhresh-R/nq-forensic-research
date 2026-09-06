# Hypothesis — Multi-session direction

## Market behavior under test

Conditional on a causal HIGH (or LOW) activity state from strategy 12, does
price **continue** the session-open move, **fade** it, or show no signed edge
over the next H minutes — inside the same session?

## Economic / mechanical rationale

Opportunity timing (A*) can coexist with zero directional edge (as in NY-open
06→07). Each promoted session must be tested independently. Blind session-open
follow/fade is the baseline; HIGH-gated variants are secondary and cannot
rescue a dead baseline by mining.

## Success / failure criteria

### Success

- Causal entry: next open after T
- IS → Val → OOS same-sign E[R] or win-rate with material payoff
- Multi-clock stability; 2025/2026 check
- Survives simple cost stress

### Failure

- ~50% / year flips / single-clock spikes
- Edge only appears after fitting stops/targets on IS outcomes
- HIGH gate used as a direction label
