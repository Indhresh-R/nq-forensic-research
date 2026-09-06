# Testing methodology — 22

1. Panel over frozen clocks; label HIGH/MID/LOW from Strategy 12 IS terciles.
2. For each row: scan up to 60 bars after T for structural ticket; record
   REVEALED / AMBIGUOUS / NONE; side and entry if revealed.
3. Outcomes from entry only; score only revealed rows.
4. Win-lift HIGH−ALL; multi-clock for promote.
5. Residual-left and reveal-rate tables are diagnostic.

Splits: IS 2010–2021 / Val 2022–24 / OOS 2025–26.
