# Hypothesis — Session extreme tag-and-fail (trapped side)

## Intuition

```text
I think direction can be inferred from which side just failed at a session
extreme before Strategy-12 HIGH, because the expansion is more likely to
resolve against the trapped side (failed buyers at highs / failed sellers
at lows) than from a static daily bias.
```

```text
Strategy 12: expansion likely
        |
Recent tag of session high or low
        |
Close fails to hold that extreme
        |
Trapped side = the failed side
        |
Forward move prefers against them?
```

## Frozen mechanical rule (a priori)

At decision T, using only session bars `<= T`:

- `SH` = session high so far; `SL` = session low so far
- Lookback **W = 15** minutes
- Threshold **thr = max(0.50 pts, 0.05 × psr)**
- **Buyers trapped** if recent window high reaches SH and `close_T <= SH - thr` → `side = −1`
- **Sellers trapped** if recent window low reaches SL and `close_T >= SL + thr` → `side = +1`
- Skip if both, neither, or flat/ambiguous

## Success / failure

Same conditional-lift protocol as 15/16: HIGH+trap vs ALL+trap, IS→Val→OOS,
multi-clock. Kill cleanly — do not retune W/thr or reopen 16A/16B.
