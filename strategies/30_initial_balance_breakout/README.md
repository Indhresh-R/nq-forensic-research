# 30. Initial Balance Breakout

Frozen first mechanical test of the standard 09:30–10:30 ET Initial Balance for NQ and ES. It is a baseline research object, not a trading recommendation or a prop-firm pass plan.

## Run

```powershell
python strategies/30_initial_balance_breakout/code/run_initial_balance_breakout.py --market nq
python strategies/30_initial_balance_breakout/code/run_initial_balance_breakout.py --market es
```

Use `--cost-points` to replace the deliberately explicit default cost assumption with the fill and fee model appropriate to the account/instrument.
