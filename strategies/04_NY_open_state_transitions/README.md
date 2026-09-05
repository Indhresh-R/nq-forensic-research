# 04. NY Open State Transitions

**Verdict: B**

Best OOS win **59.6%** but IS mean **-0.3** pts; 2025/2026 54.5%/69.7%. Lift only +3–6pp.

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
python strategies/04_NY_open_state_transitions/code/run_ny_open_state_transitions.py
`

Artifacts land in rtifacts/.
