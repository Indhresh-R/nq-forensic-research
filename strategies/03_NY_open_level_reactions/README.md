# 03. NY Open Level Acceptance / Rejection

**Verdict: C**

Strict survivors=0. Best soft IS win **52.2%** (~0.02 ONR). Stress E[R]=**-0.127**, PF 0.90.

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
python strategies/03_NY_open_level_reactions/code/run_ny_open_behavioral_discovery.py
`

Artifacts land in rtifacts/.
