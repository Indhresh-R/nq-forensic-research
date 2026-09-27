# Strategy 27 — Phase 1 summary

**PROXY STUDY — NOT ORDER FLOW.**

Phase 0 freeze + Phase 1 descriptives complete for ES and NQ.

## Locked finding

`signed_vol_proxy` is largely `sign(ret)*volume`. It tracks same-bar return (Spearman ~0.93) and does **not** survive as directional information once residualized against ret/|ret|/range.

## What *does* show up descriptively

Unsigned activity (`volume`, `vol_z_tod`, `vol_x_range`) associates with subsequent `|ret|` / RV — volatility/activity persistence. That is not signed order-flow information.

## Artifacts

- `phase0_report.md`, `phase0_freeze.json`, `phase0_proxy_vs_ohlcv.csv`
- `phase1_report_es.md`, `phase1_report_nq.md`
- panels + spearman + tercile CSVs

## Gate

No trading rules. Phase 2 only for an honest incremental-RV question (activity beyond recent |ret|/range/TOD), not an “order flow” claim.
