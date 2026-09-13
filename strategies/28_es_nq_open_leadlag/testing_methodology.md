# Testing methodology — Strategy 28

## Phase 0 — Sync audit

Build inner-joined ES/NQ 1m panel on (`session_date`, `ny_min`). Report coverage,
gap rate, open-window row counts by split.

```bash
set PYTHONPATH=d:\NQ-2
python strategies/28_es_nq_open_leadlag/code/run_phase0_sync_audit.py
```

## Phase 1 — Descriptives (lead/lag)

Spearman / hit-rate of signed lead by TOD window × horizon. Contemporaneous
correlation reported as contamination baseline.

```bash
python strategies/28_es_nq_open_leadlag/code/run_phase1_leadlag_open.py
```

**Gate:** If lag-1 (and H=5/15) Spearman is ≈0 or open windows ≤ MID control
across Val+OOS → do not treat Phase 2 as a rescue; still run Phase 2 for
documentation then close.

## Phase 2 — Frozen scalp probe

Pre-registered grid only (see `rules.md`). Report n, win%, E_gross, E_net,
target-hit%, stop-hit%, time-exit% by Discovery / Validation / OOS.

```bash
python strategies/28_es_nq_open_leadlag/code/run_phase2_scalp_probe.py
```

**Promotion bar:** same-sign E_net > 0 on Validation **and** OOS for at least one
cell; Discovery not required to be best; year break 2025 vs 2026 reported.

## Failure routing

Close 28 as `C` / `B→kill`. Do **not** open ORB/open-fade families next.
Optional later: true MBO lead-lag only with a new data argument.
