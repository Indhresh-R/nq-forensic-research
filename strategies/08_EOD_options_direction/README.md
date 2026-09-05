# 08. Prior-Day EOD Options → Intraday Direction

**Verdict: C**

Survivors **0**. Best IS med win **51.1%** (putz_follow n=268).

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
python strategies/08_EOD_options_direction/code/run_nq_e1_options_direction.py
`

Artifacts land in rtifacts/.
