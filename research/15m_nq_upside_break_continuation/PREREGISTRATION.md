# NQ 15m Upside Break Continuation Information Study

**Status:** frozen before outcome review. NQ-only information study; not a trading strategy.

## Question

Do NQ confirmed 15m breaks above 20-bar resistance contain forward continuation information beyond ordinary 15m upward moves of comparable causal normalized size?

## Frozen design

- Universe: continuous NQ futures, complete Globex 15m bars aligned at 18:00 New York; IS 2010–2021, Validation 2022–2024, OOS 2025–2026.
- Break: prior close is at/below the prior 20-bar resistance and current close is above it; first break per session only.
- Control: first 15m up-close per session and causal normalized-move band which does not break prior 20-bar resistance.
- Normalized move `(close-open)/prior_20_bar_ATR`; fixed bands `<0.5`, `0.5–1.0`, `1.0–1.5`, `1.5+`.
- Forward path begins at next available 1m open. At 1/5/15/30/60m calculate long return, MFE, MAE, retention above resistance, and failure back below resistance.

## Gate

The break must exceed its same-band control with positive, stable 30m and 60m NQ returns in IS, Validation, and OOS. Otherwise the 15m S/R branch is closed without testing entries.
