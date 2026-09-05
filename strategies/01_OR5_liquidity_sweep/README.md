# 01. OR5 Liquidity Sweep Fade

**Verdict: D**

Reject-through OOS ORB PF **0.80** (headline was 6.17). Through-stop = 59.6% of trades / 99.6% of PnL.

See 
esults/full_report.md and conclusion.md for full tables (IS / Val / OOS / 2025 / 2026).

## Documents in this folder

| File | Purpose |
|------|---------|
| hypothesis.md | What we tested and why it might exist |
| 
ules.md | Mechanical / frozen definitions |
| 	esting_methodology.md | Causality, splits, gates |
| conclusion.md | Verdict + failure mode **with numbers** |
| code/README.md | Reproducible scripts |
| 
esults/full_report.md | Numeric results tables |
| 
esults/IS.md / alidation.md / OOS.md | Split slices |

## Reproduce

`ash
python strategies/01_OR5_liquidity_sweep/code/run_orb_vwap_smt_edge_report.py
`

Artifacts land in rtifacts/.
