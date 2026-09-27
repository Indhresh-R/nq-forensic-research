# Strategy 38: Opening Auction Information → Remaining Session Persistence

Forensic investigation into whether the first 5, 10, or 15 minutes of RTH trading reveal structural information about remaining-session directional persistence in continuous NQ futures (2010--2026).

## Layout
- `PREREGISTRATION.md`: Frozen opening checkpoints, feature definitions, and targets.
- `hypothesis.md`: Research questions.
- `rules.md`: Information boundaries.
- `testing_methodology.md`: Causality card and metrics.
- `code/`: Opening auction scan engine.
- `results/`: Empirical distribution tables and reports.
- `conclusion.md`: Official verdict on whether the opening auction reveals session persistence.

## Run Scan
```powershell
python strategies/38_opening_auction_information/code/run_opening_auction_scan.py
```
