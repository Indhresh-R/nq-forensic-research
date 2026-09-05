# Code — 04_NY_open_state_transitions

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/04_NY_open_state_transitions/code/<script>.py
# or legacy shim from repo root:
python <script>.py
```

## Scripts

- `run_ny_open_state_transitions.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
