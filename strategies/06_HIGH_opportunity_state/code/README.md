# Code — 06_HIGH_opportunity_state

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/06_HIGH_opportunity_state/code/<script>.py
```

## Scripts

- `run_ny_open_opportunity_timing.py`
- `run_nq_high_mech_decomp.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
