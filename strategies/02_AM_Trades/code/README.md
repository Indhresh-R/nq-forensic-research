# Code — 02_AM_Trades

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/02_AM_Trades/code/<script>.py
```

## Scripts

- `run_am_trades_hypothesis.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
