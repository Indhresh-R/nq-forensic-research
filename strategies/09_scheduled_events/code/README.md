# Code — 09_scheduled_events

Run from **repository root** (so `artifacts/` and `data/` resolve):

```bash
python strategies/09_scheduled_events/code/<script>.py
# or legacy shim from repo root:
python <script>.py
```

## Scripts

- `run_nq_e2_scheduled_events.py`

Shared loaders: `common.nq_session` (`load_nq`, `state_at_T`, `build_day_context`).
Sibling imports within this folder (e.g. HIGH directional helpers) stay local.
