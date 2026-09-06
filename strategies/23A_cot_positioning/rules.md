# Rules — 23A (frozen)

1. TFF Futures-Only Nasdaq-100 only (`market_and_exchange_names` like NASDAQ-100).
2. Lag: usable only from **next session after Friday ~15:30 ET** release.
3. Extremes: trailing **104**-week z, then top/bottom **decile** of trailing z — no alternatives.
4. Sides: `lev_fade`, `am_follow` only.
5. HIGH = Strategy-12 frozen `rng_psr` p66; do not refit.
6. Splits: IS 2010–2021 / Val 2022–2024 / OOS 2025–2026.
7. Kill family on clean fail — no 23B/23C rescue without updating `direction_resolution.md`.
