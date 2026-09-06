# Testing Methodology — Multi-session opportunity

## Causality card

```text
Information available at signal: bars in session with t <= T
Entry / outcome start: next bar open after T
Outcome window: forward bars still inside the same session
Scale: psr known at session open (prior completed session range)
No future information: YES
No direction / targets / entries in Phase A
```

## Splits (frozen)

| Split | Years |
|-------|-------|
| IS | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

Year check: 2025 and 2026 separately when n >= 20.

## Robustness

- Multi-clock: promote only if soft/strong on >= 2 decision offsets for a (session, condition, H)
- Multi-horizon reported; primary scoring uses STRUCT_FRAC = 0.25
- HIGH−LOW discrimination pairs required for promotion narrative
- IS terciles frozen per (session, T_offset, feature); never refit on Val/OOS
