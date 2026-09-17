# Strategy 43: Event-Based Compression → Range → Breakout → Pullback

**Status:** FROZEN BEFORE EXECUTION

## Objective

Test a sequential, clock-independent intraday state transition on continuous NQ 1-minute data: detect compression, fade a frozen range edge while it persists, disable fades after confirmed expansion, then trade only a pullback-plus-continuation in the breakout direction.

## Data and splits

- NQ 1m continuous history; RTH 09:30–15:55 America/New_York.
- Signals: 09:45–14:50; forced flat at 15:55.
- Selection subperiod: 2010–2018. IS confirmation: 2019–2021. Validation: 2022–2024. OOS: 2025–2026.
- Reported program IS is the full 2010–2021 union; selection never uses Validation or OOS.

## Frozen grid and selection

Only the compression detector varies: window `N ∈ {8,10,12,15}` and `range_N / ATR20 ∈ {2.5,3.5,4.5}`. Select the highest combined-net-expectancy cell on 2010–2018 only; report the entire surface and its immediate N-neighbours. All other parameters below are fixed.

## Causal state machine

1. At minute close `t`, calculate session-causal 20m ATR and the high/low of the preceding `N` completed minutes. If their width is at most the selected ATR multiple, freeze those boundaries and enter `RANGE` state.
2. In `RANGE`, one fade may be signalled at a lower/upper edge within `0.10 ATR`; entry is next minute open; stop is boundary ± `0.25 ATR`; target is the opposite boundary less/plus `0.10 ATR`.
3. A `BREAKOUT` is a close beyond the frozen boundary by `0.50 ATR`, with current true range at least `1.0 ATR`. Cancel any fade order and permanently disable fades for that range.
4. In the next 30 minutes, require a pullback that touches the broken boundary ± `0.10 ATR`. Then require a later one-minute continuation close beyond the prior minute high/low and at least `0.25 ATR` beyond the broken boundary. Enter next minute open in breakout direction.
5. Continuation stop: pullback extreme ± `0.25 ATR`; fixed target: `1.5R`. At most one active/pending trade, one fade per range, and one continuation per breakout. After expiry/closure, detection may seek a new range.

## Execution

- NQ round-trip friction: 1.0 point.
- Next-minute-open fills only. Stops/targets are tracked on subsequent minute bars; an open that gaps through a stop is filled at the open. If stop and target both occur in one bar, stop first.
- No trailing stops are tested in this baseline. No EMA/VWAP/RSI/MACD/volume/order-flow/candlestick filters are permitted.

## Promotion

ROBUST requires positive net expectancy in IS confirmation, Validation, and OOS; broad neighbouring grid support; positive yearly stability; and no single direction/regime dependence. Otherwise classify PROMISING, FRAGILE, or REJECTED and stop without adding filters.
