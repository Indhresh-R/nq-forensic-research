# Testing Methodology — 16B

Identical hostile lift protocol to 16A
(`strategies/16A_daily_candle_direction/testing_methodology.md`):

- Causality: prior day completed; state/price `<= T`; entry next open
- Critical: lift = HIGH+loc − ALL+loc
- Splits: IS / Val / OOS + Y2025 / Y2026
- Multi-clock ≥2 for promotion interest
