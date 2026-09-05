# Code — 05_NY_open_path_asymmetry

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/05_NY_open_path_asymmetry/code/<script>.py
# or legacy shim from repo root:
python <script>.py
```

## Scripts

- `run_ny_open_path_asymmetry.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
