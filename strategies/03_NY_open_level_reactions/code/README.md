# Code — 03_NY_open_level_reactions

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/03_NY_open_level_reactions/code/<script>.py
```

## Scripts

- `run_ny_open_behavioral_discovery.py`
- `run_ny_open_causal_retest.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
