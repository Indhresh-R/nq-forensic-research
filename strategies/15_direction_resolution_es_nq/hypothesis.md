# Hypothesis — ES/NQ direction resolution under activity

## Market behavior under test

When NQ enters a validated quiet→vol-expansion activity state, the shock has a
sign. ES (broader beta) and NQ−ES relative strength are observables that can
carry **signed** content about that shock — unlike unsigned volatility itself.

## Causal story

Volatility expansion ≈ information / repricing in progress. ES move and
NQ-vs-ES divergence are proxies for *which book is leading* the shock. If that
is real, the same resolver should show **conditional lift inside ACTIVITY**
versus the same clock unconditional market (and versus QUIET).

## Success / failure

### Success

- Resolver R: causal at T, next-bar NQ outcomes
- Inside HIGH: material signed edge IS→Val→OOS (+ year check)
- **Lift:** HIGH performance − unconditional performance same-sign and material on Val+OOS
- Not explained by QUIET matching HIGH

### Failure

- Absolute edge inside HIGH but **no lift** vs unconditional (Strategy 14 lesson)
- Lift IS-only / year flip
- Rehash of Strategy 07 “inside HIGH only” without the interaction test
