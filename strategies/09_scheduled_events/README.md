# 09. Scheduled Macro Events

**Verdict: C**

Survivors **0**. Best IS med win **53.0%** (PPI impulse_cont n=100).

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
python strategies/09_scheduled_events/code/run_nq_e2_scheduled_events.py
`

Artifacts land in rtifacts/.
