# Testing methodology

## Phase 0 — Schema audit

Done. `data_opt` is 30-minute SPXW surface (10:00–16:00 ET), not dealer GEX.

## Phase 1 — Feature panel

Frozen 30m surface aggregates + causal ES/NQ forward outcomes. Descriptives only (terciles/Spearman). No optimization.

## Phase 2 — Incremental information

1. Attach causal prior RV/range from ES/NQ 1m over `[T-30m, T)`
2. Nested OLS: Baseline A vs B / C / ATM-share-only
3. Score **out-of-sample R²** (fit earlier → score later)
4. Hostile placebos: permute, time-shift, wrong-day
5. ES vs NQ, horizons 5–120m, year table 2016–2024
6. **Stop** — class **C** (research signal, not trading edge); no trading rules

```bash
set PYTHONPATH=d:\NQ-2
python strategies/26_vilkov_0dte_surface/code/run_phase2_incremental_hostile.py
```

## Phase 3 — Stability / mechanism audit (current)

Still **no** threshold search, entry/exit rules, optimization, or Sharpe hunting.

Ask *why* the residual ES effect exists:

1. Gamma concentration × IV regime
2. Gamma concentration × market volatility regime
3. Gamma concentration × distance from ATM / surface-part probes
4. ES lead → NQ response (and gamma residual after ES RV control)
5. Time-of-day decomposition
6. Temporal stability across chronological blocks
7. Mechanism falsification (IV/TOD-matched scramble, residual permute, moment-matched synthetic)

If Phase 3 shows a coherent mechanism **and** stable conditional relationship, *then* decide whether a trading-rule phase is justified. Otherwise archive Strategy 26 as a well-tested research hypothesis.

```bash
set PYTHONPATH=d:\NQ-2
python strategies/26_vilkov_0dte_surface/code/run_phase3_mechanism_audit.py
```
