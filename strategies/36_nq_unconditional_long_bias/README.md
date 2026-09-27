# Strategy 36: Unconditional NQ Long-Side Directional Bias

Forensic investigation into whether NQ possesses a persistent long-side return advantage during the US cash session that remains positive after realistic transaction costs and outperforms passive market holding.

## Layout
- `PREREGISTRATION.md`: Frozen candidate and horizon specifications.
- `hypothesis.md`: Research questions and null formulations.
- `rules.md`: Operational and causal constraints.
- `testing_methodology.md`: Causality card and passive benchmark rules.
- `code/`: Backtest engines and attribution scripts.
- `results/`: Performance matrices and reports.
- `conclusion.md`: Official verdict and forensic failure modes.

## How to Run
```powershell
python strategies/36_nq_unconditional_long_bias/code/run_preregistered_drift_pass.py
python strategies/36_nq_unconditional_long_bias/code/run_symmetric_trading_pass.py
python strategies/36_nq_unconditional_long_bias/code/run_passive_beta_attribution.py
```
