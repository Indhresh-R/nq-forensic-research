# Code — 10_reactive_HIGH_capture

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/10_reactive_HIGH_capture/code/<script>.py
```

## Scripts

- `run_nq_roc.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
