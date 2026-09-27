# Code

| Script | Role |
|--------|------|
| `audit_vilkov_panel.py` | Phase 0 schema/timestamp audit |
| `run_phase1_surface_panel.py` | Freeze 30m features, join ES/NQ outcomes, raw terciles/Spearman |
| `run_phase2_incremental_hostile.py` | Nested incremental R² + hostile placebos (no optimization) |
| `run_phase3_mechanism_audit.py` | Stability / mechanism audit (no trading search) |

```bash
set PYTHONPATH=d:\NQ-2
python strategies/26_vilkov_0dte_surface/code/audit_vilkov_panel.py
python strategies/26_vilkov_0dte_surface/code/run_phase1_surface_panel.py
python strategies/26_vilkov_0dte_surface/code/run_phase2_incremental_hostile.py
python strategies/26_vilkov_0dte_surface/code/run_phase3_mechanism_audit.py
```

Phase 1 reuses `artifacts/26_vilkov_0dte_surface/surface_features_30m.parquet` when present (delete that file to rebuild aggregates). Phase 3 requires `phase2_panel_with_prior_state.parquet` from Phase 2.
