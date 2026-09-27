# Strategy 63 — COMPLETE (DESCRIPTIVE_ONLY → Step-2 KILL)

**Status:** Step-1 DESCRIPTIVE_ONLY; Step-2 distance-matched null → **`KILL`**.  
**No promote. No trade. No IS/Val/OOS. TPO deferred.**

## Step 1 headline (strict primary)

| Metric | Value |
| --- | --- |
| n onsets (post-dedup) | **338** (70 sessions) |
| p_into / p_away / unresolved | 0.201 / 0.438 / 0.361 |
| Δ (into−away) | **−0.237** |
| med dist_ratio | **2.09** |

## Step 2 — distance-matched null

| Metric | Value |
| --- | --- |
| Null | zero-drift BM; causal pre-event σ; N_SIM=10000; SEED=20260923; DT=15s |
| null mean Δ | **−0.213** |
| null 95% | [−0.299, −0.127] |
| empirical p (two-sided) | **0.60** |
| **Verdict** | **`KILL`** — asymmetry explained by barrier geometry |

Terciles all null-consistent (p ≥ 0.17). Full write-up: `results/STEP2_DISTANCE_MATCHED_NULL_REPORT.md`.

## Artifacts

| Path | Role |
| --- | --- |
| `results/events_strict_va.parquet` | Step-1 onsets + outcomes |
| `results/FIRST_PASSAGE_REPORT.md` | Step-1 report |
| `results/STEP2_DISTANCE_MATCHED_NULL_REPORT.md` | Step-2 null + verdict |
| `results/step2_null_summary.json` | Machine summary |
| `results/step2_null_deltas.parquet` | Per-sim Δ |
| `results/step2_event_sigma.parquet` | Locked causal σ_i |
| `results/step2_audit.json` | Audit |

## Next

Do not retune barriers or hunt a tercile. Any further Patrick work needs a **new** frozen charter item (not a rescue of this Δ).
