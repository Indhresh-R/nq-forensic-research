# Code — 11_HIGH_residual_economics

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/11_HIGH_residual_economics/code/<script>.py
# or legacy shim from repo root:
python <script>.py
```

## Scripts

- `run_nq_high_resid_econ.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
