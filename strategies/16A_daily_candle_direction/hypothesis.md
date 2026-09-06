# Hypothesis — Prior daily candle as direction resolver

## Market behavior under test

Strategy 12 flags when an unusually active move is more likely. The completed
**previous Globex daily candle** may carry signed information about which way
that activity tends to resolve.

```text
Previous Daily Candle → Daily Bias → Strategy-12 HIGH
        → Does NQ's next H-minute return prefer the bias direction?
```

## Daily candle definition (frozen, causal)

- **Globex / `session_date` day:** bars with the same `session_date`
  (rolls at **18:00 America/New_York**, matching `SESSION_START`).
- **Prior day** for any event on `session_date = S`: full OHLC of
  `session_date = S_prev` (completed at or before 18:00 when S begins).
- **Available before every T on S** — no cash-day / TradingView daily, no
  same-day incomplete candle.

## Bias A (only)

```text
prior close > prior open  → side = +1 (LONG bias)
prior close < prior open  → side = −1 (SHORT bias)
prior close = prior open  → skip
```

## Success / failure

### Success

- HIGH+bias win (or E) beats ALL+bias on IS with material lift
- Same-sign lift Val + OOS; year check where n allows
- Multi-clock stability (≥2 offsets)
- HIGH alone (no bias) does not already explain the result

### Failure

- HIGH+bias ≈ 50% / ≈ ALL+bias (no conditional lift)
- Soft single-clock only / year flips
- Do **not** rescue with Bias B/C/D in the same pass
