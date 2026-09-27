# Strategy 62 — COMPLETE (fields built)

**Status:** Build finished under `PATRICK_BUILD_FIELDS_PREREGISTRATION.md`.  
**Not a strategy. No trade. No continuation/fade.**

## Artifacts

| Path | Role |
| --- | --- |
| `results/p1_session_profiles.parquet` | Reused VP session profiles |
| `results/p2_tpo_cells.parquet` | Full-Globex 30m TPO cells |
| `results/p2_tpo_session_meta.parquet` | Includes `globex_open_60m_*` (not IB) |
| `results/p6a_print_flags.parquet` | Flagged big prints only |
| `results/p6a_session_stats.csv` | Per-session flag rate + tie mass |
| `results/p7_prints_at_prior_levels.parquet` | **Causal** joins to prior POC/VAH/VAL |
| `results/build_audit.json` | Freeze + diagnostics |
| `results/BUILD_FIELDS_REPORT.md` | Report |

## Headline diagnostics (human judgment — do not retune `(q,N)`)

| Metric | Value |
| --- | --- |
| `(q, N)` | 0.99 / 5000 prints, roll reset |
| Mean P6a flag rate | **~1.53%** (slightly above 1%) |
| Mean tie mass at threshold | **~0.49** (half of flags have `size == t`) |
| Median threshold (session medians) | often **5.0** (round lot) |
| P7 joins | ~2135 prints / 79 sessions |
| P2 mean periods | ~45 (full Globex, as expected) |

**Follow-up:** tie vs strict stratified — see `results/INSPECT_TIE_STRICT.md`.  
**Decision:** `P6A_SUBGROUP_DECISION.md` recommends **strict-only primary** before any continuation/fade prereg.

