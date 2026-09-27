# Testing methodology

## Phase −1 — Literature

Done (`LITERATURE.md`).

## Phase 0 — Data audit + freeze

**Done.** Artifacts:

- `artifacts/27_orderflow_information/phase0_freeze.json`
- `artifacts/27_orderflow_information/phase0_report.md`
- `artifacts/27_orderflow_information/phase0_proxy_vs_ohlcv.csv`

Locked: clocks, continuous construction, volume, proxies (incl. exact `signed_vol_proxy` + resid), outcomes 1/5/15/30/60, splits 2010–21 / 2022–24 / 2025–26, bans on thresholds/optimization/costs/rules.

**Key audit result:** `signed_vol_proxy` Spearman with same-bar `ret_1m` ≈ 0.93 (ES). Phase 1 must compare residual vs raw proxy.

## Phase 1 — Descriptives only (current)

RTH panel per instrument. Terciles + Spearman. **No ΔR².**

```bash
set PYTHONPATH=d:\NQ-2
python strategies/27_orderflow_information/code/run_phase1_proxy_panel.py
```

Interpretation gate: if raw proxy mimics `ret_1m` and `signed_vol_proxy_resid` collapses, treat as relabeled OHLCV — not volume-pressure information.

## Phase 2 — Incremental information (blocked)

Only if Phase 1 shows non-trivial residual / unsigned-activity descriptive signal beyond raw return/range.

## Failure routing

Phase 1/2 fail → close 27 → Strategy 28 cross-market lead/lag (not another candle/ORB family).
