# 07. Direction Inside HIGH + Intrinsic OHLC Families

**Verdict: C/B**

Multi-clock strong=**0**. Inside HIGH FOLLOW ~51–55%; single-clock spikes ≤~58%.

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
python strategies/07_direction_inside_and_without_HIGH/code/run_ny_open_high_directional.py
`

Artifacts land in rtifacts/.
