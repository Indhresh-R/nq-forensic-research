# Testing Methodology — 16A

## Causality card

```text
Prior daily OHLC: completed session_date < current session_date
Activity + path: NQ bars <= T
Entry: next NQ open after T
Outcome: signed points to close at H (same session if enough bars)
No future information: YES
Resolver-only: NO stops/targets
```

## Contrasts

| Label | Definition |
|-------|------------|
| ALL + bias | Follow Bias A at all regimes |
| HIGH + bias | Bias A only when HIGH |
| LOW + bias | Bias A only when LOW |
| HIGH long | Always long when HIGH (no daily filter) |

**Critical:** lift = metric(HIGH+bias) − metric(ALL+bias).

## Splits

IS 2010–2021 / Val 2022–2024 / OOS 2025–2026; Y2025 / Y2026.

## Promotion

Same spirit as Strategy 15 lift bars. Kill cleanly if no lift — do not open 16B in the same run.
