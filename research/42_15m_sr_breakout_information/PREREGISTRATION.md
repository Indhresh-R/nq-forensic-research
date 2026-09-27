# 15m S/R Breakout Information Study

**Status:** frozen before examination of forward-path results. This is an information study, not Strategy 43 and not an execution search.

## Question

Does a confirmed break of a causal 20-bar, 15-minute support/resistance level contain information about the next 1–60 minutes of the 1-minute path?

## Event definition

- Markets: continuous NQ and ES futures, full Globex sessions, 2010–2026.
- Build completed 15-minute bars aligned from 18:00 America/New_York; retain only fully observed bars.
- Resistance/support at completed bar `T`: highest high / lowest low of the prior 20 completed 15m bars.
- Long event: prior close is at or below resistance and `close[T] > resistance`. Short event mirrors this at support.
- At most one long and one short event per Globex session (first qualifying event).
- Event is known only after `T` completes. The forward path begins at the next available 1-minute bar open.

## Frozen measurements

At 1, 5, 15, 30 and 60 forward minutes, separately for long and short events:

1. Direction-signed forward return from next-minute open to horizon close.
2. Direction-signed MFE and MAE from next-minute open using subsequent 1m highs/lows.
3. Probability the horizon close remains beyond the broken level.
4. Probability of a close back through the broken level at any point in the horizon (failure).

Report NQ and ES independently in IS (2010–2021), Validation (2022–2024), and OOS (2025–2026). No costs, stop, target, entry selection, or parameter ranking is used: this is descriptive information measurement only.

## Gate

Potential information must show same-signed, economically material forward-return / level-retention evidence in NQ and ES across all three splits. Otherwise no execution mechanism is tested.
