# Strategy 35: Bull Flags and Bear Flags Forensic Investigation

Forensic evaluation of classical Bull Flag and Bear Flag continuation patterns on continuous NQ and ES futures data (2010--2026).

## Directory Structure
- `PREREGISTRATION.md`: Frozen candidate specifications and parameters.
- `hypothesis.md`: The empirical questions being tested.
- `rules.md`: Operational and causal constraints.
- `testing_methodology.md`: Causality card and split protocols.
- `code/`: Backtest engines and audit scripts.
- `results/`: Performance tables and analysis.
- `conclusion.md`: Official forensic verdict and failure modes.

## How to Reproduce
```powershell
python strategies/35_bull_bear_flags/code/run_preregistered_pass.py
python strategies/35_bull_bear_flags/code/run_breakdown_audit.py
python strategies/35_bull_bear_flags/code/run_cost_sensitivity.py
```
