# 27. ES/NQ Volume-Pressure Proxy Information

**Verdict: Phase 0 = `PASS` (freeze locked). Phase 1 = `DONE`. PROXY STUDY — not order flow.**

> Do OHLCV-derived **volume-pressure proxies** on ES (then NQ) show any descriptive association with the next 1–60 minutes after we account for the fact that `signed_vol_proxy` is largely signed return × volume?

Not: “Does order flow predict price?” — we do not observe order flow.

## Status gate

| Gate | Status |
|------|--------|
| Literature map | Done |
| Phase 0 data audit + freeze | **Done** |
| Naming: proxy ≠ order flow | **Locked** |
| Phase 1 descriptives (terciles/Spearman) | **Done** |
| Phase 2 incremental ΔR² | **Blocked** — review Phase 1 first |
| Trading rules | **Hard blocked** |

## Run

```bash
set PYTHONPATH=d:\NQ-2
python strategies/27_orderflow_information/code/run_phase0_data_audit.py
python strategies/27_orderflow_information/code/run_phase1_proxy_panel.py
```

Artifacts: `artifacts/27_orderflow_information/`.

## Documents

| File | Purpose |
|------|---------|
| LITERATURE.md | Published phenomena vs affordable data |
| hypothesis.md | Research question |
| rules.md | **Frozen** definitions |
| DATA_NOTES.md | Schema + collinearity warning |
| testing_methodology.md | Phase gates |
| conclusion.md | Current verdict |
