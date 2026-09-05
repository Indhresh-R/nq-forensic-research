# 05. NY Open Path Asymmetry

**Verdict: B**

Strong year-stable cells=**0**. Soft leftovers flip (e.g. 2025 75% / 2026 50%).

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
python strategies/05_NY_open_path_asymmetry/code/run_ny_open_path_asymmetry.py
`

Artifacts land in rtifacts/.
