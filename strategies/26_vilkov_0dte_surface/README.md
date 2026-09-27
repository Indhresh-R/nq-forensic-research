# 26. Vilkov 0DTE Surface → ES/NQ Response

**Verdict: Phase 2 = C (research signal, not trading edge). Phase 3 = `MIXED_MECHANISM` — do not open trading search.**

> Does the 30-minute SPX options surface contain information that predicts the distribution of the next short-horizon ES/NQ move?

Not: “Can we find a profitable gamma strategy?”

## Branch

`research/26_vilkov_0dte_surface`

## Status gate

| Gate | Status |
|------|--------|
| Separate git branch | Done |
| Schema / timestamp audit | Done — 30m clocks 10:00–16:00 ET |
| Frozen 30m features + ES/NQ join | **Done** |
| Raw conditionals / Spearman (no optimize) | **Done** |
| Incremental info vs IV/price/TOD | **Done** — `WEAK_OR_UNSTABLE` → class **C** |
| Hostile placebos | **Done** |
| Phase 3 mechanism / stability audit | **Done** — `MIXED_MECHANISM` |
| Trading rules / threshold search | **Blocked / not justified** |

## Run

```bash
set PYTHONPATH=d:\NQ-2
python strategies/26_vilkov_0dte_surface/code/audit_vilkov_panel.py
python strategies/26_vilkov_0dte_surface/code/run_phase1_surface_panel.py
python strategies/26_vilkov_0dte_surface/code/run_phase2_incremental_hostile.py
python strategies/26_vilkov_0dte_surface/code/run_phase3_mechanism_audit.py
```

Data: `data/vilkov/` (gitignored). Reuses `artifacts/.../surface_features_30m.parquet` and `phase2_panel_with_prior_state.parquet` if present.

## Naming discipline

Aggregates from `oi_gamma*` / `trade_volume_gamma*` are **surface OI-gamma / volume-gamma** — not dealer positioning.

## Documents

| File | Purpose |
|------|---------|
| hypothesis.md | Research question |
| rules.md | Frozen causality + phase gates |
| testing_methodology.md | Audit → features → hostile → mechanism |
| conclusion.md | Current verdict |
| DATA_NOTES.md | Provenance / pitfalls |
| `artifacts/26_vilkov_0dte_surface/` | Audit + Phase 1–3 tables |
