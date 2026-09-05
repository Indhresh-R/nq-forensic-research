# NQ Forensic Strategy Research

This repository is a **forensic research library**, not a showcase of profitable NQ systems.

Goal:

```text
Hypothesis → Mechanical definition → Causal test → Stress / OOS → Verdict
```

Failed strategies are first-class citizens. They stop others from rediscovering the same false edges.

## Start here

| Doc | Purpose |
|-----|---------|
| [`reports/master_research_log.md`](reports/master_research_log.md) | Chronological program log |
| [`reports/strategy_summary.md`](reports/strategy_summary.md) | Master verdict table |
| [`reports/rejected_hypotheses.md`](reports/rejected_hypotheses.md) | Why things died |
| [`research_framework/`](research_framework/) | Causal rules, splits, audit checklist |
| [`strategies/`](strategies/) | One dossier per hypothesis family |

## Headline conclusion (2026-09)

| Class | Result |
|-------|--------|
| Predictive short-horizon **direction** (OHLC, ES, volume, options, events, reactive) | **Failed** |
| **HIGH** activity / opportunity state (`vol_expansion_high`) | **Statistically valid** as a **late persistence detector** |
| HIGH as **executable standalone trade signal** (directional or direction-neutral) | **Failed** |

Footnote: **A\*** on HIGH means validated *state detection*, not a license to trade.

## Layout

```text
research_framework/     # how we test
strategies/<id>/        # dossier: hypothesis, rules, methodology, conclusion, code/, results/
common/                 # shared loaders (nq_session, paths, splits)
artifacts/<id>/         # reports grouped by family (parquet panels gitignored)
reports/                # master tables
archive/legacy_scripts/ # pre-library engines needed by OR5 forensics
```

## Data (not in this repo)

Place locally under `data/`:

- `nq_1m_continuous.parquet`
- `es_1m_continuous.parquet`
- `session_cached.parquet` (OR5 only)

## Reproduce a dossier

```bash
cd NQ-2
python strategies/06_HIGH_opportunity_state/code/run_ny_open_opportunity_timing.py
```

Shared primitives: `from common.nq_session import load_nq, state_at_T, build_day_context`.
Artifacts: `from common.paths import art` → `art("ny_open_opp_timing_report.md")`.

## License

See `LICENSE`.
