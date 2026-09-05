# 02. AM Trades (Manipulation / Continuation)

**Verdict: C**

IS n=730 WR=34.0% PF=**0.894** E=**-1.42** pts. OOS PF 1.015; 2025/2026 PF 1.16/0.85.

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
python strategies/02_AM_Trades/code/run_am_trades_hypothesis.py
`

Artifacts land in rtifacts/.
