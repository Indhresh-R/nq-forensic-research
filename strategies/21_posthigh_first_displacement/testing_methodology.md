# Testing methodology — 21

1. Build panel over frozen session clocks; label HIGH/MID/LOW from Strategy 12 IS terciles.
2. For each row, compute `bar1_follow` and `bar5_follow` causally after T.
3. Entry = next open after revelation bar completes; outcomes from entry only.
4. Score win/E by session × offset × outcome × regime × resolver × split.
5. Candidates: win-lift gates; require multi-clock for promote.
6. Residual-left tables are **diagnostic only** — never used to select the resolver.

Splits: IS 2010–2021 / Val 2022–24 / OOS 2025–26.
