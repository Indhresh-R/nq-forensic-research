# Hypothesis — Prior-day midpoint location at the event

## Intuition

```text
I think the direction can be inferred from where price sits relative to the
prior Globex day's midpoint at the moment Strategy-12 HIGH fires, because
HTF context is location in yesterday's range — not yesterday's candle color.
When expansion begins above (below) that midpoint, the active move is more
likely to continue higher (lower).
```

```text
Prior Globex day range
        ↓
   Midpoint (known)
        ↓
Price at T vs midpoint
        ↓
Strategy-12 HIGH
        ↓
Does forward return prefer that side?
```

## Causal definition

- Prior day = completed previous `session_date` (18:00 ET Globex), same as 16A
- `prior_mid = (prior_high + prior_low) / 2`
- `side = sign(close_T − prior_mid)` (skip if flat / tiny vs prior range)
- Activity gate = Strategy 12 HIGH (frozen; do not retune)

## Success / failure

Same lift protocol as 16A: HIGH+loc vs ALL+loc, IS→Val→OOS, multi-clock.
Kill cleanly if no stable lift — do not add PDH/PDL variants in this pass.
