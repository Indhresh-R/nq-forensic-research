# Code — 07_direction_inside_and_without_HIGH

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/07_direction_inside_and_without_HIGH/code/<script>.py
# or legacy shim from repo root:
python <script>.py
```

## Scripts

- `run_ny_open_high_directional.py`
- `run_ny_open_high_cross_asset.py`
- `run_ny_open_high_volume.py`
- `run_ny_open_high_multiscale.py`
- `run_nq_serial_dependence.py`
- `run_nq_extreme_asymmetry.py`
- `run_nq_failed_movement.py`
- `run_nq_exp_retrace.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
