# Rules — 24A (frozen)

1. HIGH = Strategy-12 frozen `rng_psr` p66 at session × offset; do not refit.
2. Vol lookback **W = 30** bars; `rv = std(Δclose)`; `size_inv = clip(rv_ref/rv, 0.25, 4.0)`.
3. `rv_ref` = IS median of `rv` only; freeze for later stages.
4. HIGH-aware multiplier: **0.70** if HIGH else **1.00** — no alternatives.
5. Primary book: coin-flip side from frozen hash; audit long-only and short-only.
6. Cost: mid **1.0** pt round-trip × |size| (execution_assumptions).
7. Risk metrics on **one trade per session_date × session** (earliest eligible offset).
8. Splits: IS 2010–2021 / Val 2022–2024 / OOS 2025–2026; stage-gate IS first.
9. No directional claim; no 24B–D until 24A IS reviewed.
