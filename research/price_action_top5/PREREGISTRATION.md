# Internet-Sourced Price Action Top-5 Study

**Status:** frozen before backtest execution.

## Selection

The five patterns were selected as commonly documented price-action/candlestick setups, not because a web source claims they are profitable: pin bar, inside-bar breakout, engulfing reversal, inside fake-out (Hikkake-style), and three-bar reversal. Flags and generic S/R were excluded because they were already tested and closed in this program.

## Common test protocol

- Continuous NQ and ES futures, 5-minute RTH bars (09:30–15:55 New York), 2010–2026.
- Signal must complete by 14:50. Enter at the next available 1-minute open. Exit at the close of the twelfth later 5m bar (one hour). NQ cost: 1.0 point round trip; ES: 0.5.
- First qualifying long and first qualifying short per pattern/session only.
- IS 2010–2021; Validation 2022–2024; OOS 2025–2026. Report NQ and ES independently.
- Same-bar ambiguity does not arise: no stop or target is used. This is a deliberately fixed-horizon pattern payoff screen, not a parameter search.

## Frozen mechanical patterns

1. **Pin reversal:** bullish: green bar closes in upper third, lower wick >= twice body, and close below close three bars ago; bearish mirror.
2. **Inside-bar breakout:** an inside bar lies strictly within a mother bar; the following bar closes beyond the mother high/low.
3. **Body engulfing:** current opposite-color body fully covers the preceding body (bull/bear mirror).
4. **Inside fake-out:** mother then inside bar; following bar breaches mother high/low but closes back inside mother range. Trade opposite the failed breach.
5. **Three-bar reversal:** two same-direction closes followed by an opposite-color bar closing beyond the immediately prior bar’s high/low.

## Gate

A pattern requires positive net expectancy in NQ and ES across IS, Validation, and OOS, with >=30 OOS trades per market. Otherwise it is rejected; no post-hoc filter or execution tuning follows.
