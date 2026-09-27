# Results — Strategy 27

## Phase 0

See `artifacts/27_orderflow_information/phase0_report.md`.

**PROXY STUDY locked.** `signed_vol_proxy` Spearman with `ret_1m` ≈ 0.93.

## Phase 1

| Artifact | Path |
|----------|------|
| ES panel | `artifacts/27_orderflow_information/phase1_panel_es.parquet` |
| NQ panel | `artifacts/27_orderflow_information/phase1_panel_nq.parquet` |
| Spearman | `phase1_spearman_{es,nq}.csv` |
| Terciles | `phase1_conditional_terciles_{es,nq}.csv` |
| Reports | `phase1_report_{es,nq}.md` |

### Direction check (ES, H=15, target=ret, Spearman)

| Feature | Disc | Val | OOS |
|---------|-----:|----:|----:|
| ret_1m | -0.023 | -0.002 | -0.004 |
| signed_vol_proxy | -0.020 | -0.004 | -0.003 |
| signed_vol_proxy_resid | -0.003 | -0.005 | +0.001 |

### Activity → future RV (ES, H=15, target=rv)

| Feature | Disc | Val | OOS |
|---------|-----:|----:|----:|
| absret_1m | 0.431 | 0.431 | 0.458 |
| volume | 0.542 | 0.548 | 0.614 |
| vol_z_tod | 0.458 | 0.456 | 0.476 |
| vol_x_range | 0.662 | 0.682 | 0.733 |
| signed_vol_proxy_resid | 0.026 | 0.018 | 0.016 |

No ΔR² / costs / rules in this phase.
