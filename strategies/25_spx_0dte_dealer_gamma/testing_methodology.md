# Testing methodology

1. **Data audit** before any strategy claim (coverage, duplicates, timing).
2. **Descriptives** by regime: forward returns, RV, directional efficiency.
3. **Theory tests**: pos vs neg gamma on forward RV; momentum vs reversal by regime.
4. **Flip tests**: cross events and distance bins (predefined).
5. **Interactions**: extreme |gamma| × near-flip × expanding RV (predefined abs q80).
6. **TOD slices** (predefined buckets).
7. **Book compare**: measured vs conventional vs volume-convention (sign).
8. **Incremental R²**: price/vol/TOD/OR/VWAP baseline vs +gamma features.
9. **NQ transmission**: same regime labels from SPX gamma → NQ outcomes.
10. **Hostile**: future/past time shifts, within-day shuffle, wrong-day gamma, year stability.
11. **Multiple testing**: Benjamini–Hochberg on all recorded p-values.
12. **Economic**: frozen fade/follow rules after costs.

No random train/test splits. No post-hoc day exclusion.
