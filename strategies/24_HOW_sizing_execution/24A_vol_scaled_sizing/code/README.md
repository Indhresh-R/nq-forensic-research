# Code — 24A Vol-Scaled Sizing

```bash
# IS-only panel + risk metrics (default; Val/OOS gated)
python strategies/24_HOW_sizing_execution/24A_vol_scaled_sizing/code/run_24a_test.py --stage IS
```

Artifacts via `common.paths.art` → `artifacts/24A_vol_scaled_sizing/`.

Requires:
- `data/nq_1m_continuous.parquet`
- `artifacts/12_multi_session_opportunity/nq_multi_sess_opp_thresholds_IS.json`
