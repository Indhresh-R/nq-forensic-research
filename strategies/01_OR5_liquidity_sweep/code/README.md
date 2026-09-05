# Code — 01_OR5_liquidity_sweep

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/01_OR5_liquidity_sweep/code/<script>.py
# or legacy shim from repo root:
python <script>.py
```

## Scripts

- `run_orb_vwap_smt_edge_report.py`
- `run_exact_sequence_test.py`
- `run_gap_through_forensic.py`
- `run_through_stop_stress.py`
- `run_target_inset_sensitivity.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
