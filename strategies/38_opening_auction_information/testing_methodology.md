# Testing Methodology: Strategy 38

## Causality Card
```text
Information Available: Completed RTH prints from 09:30 through T
Observation Checkpoints: T = 09:34 (5m), 09:39 (10m), 09:44 (15m)
Dependent Window: Strictly T+1 to 15:55 ET
Lookahead: Strictly prohibited
Chronological Splits: IS (2010–2021), Validation (2022–2024), OOS (2025–2026)
```

## Statistical Metrics
1. **Directional Follow-Through ($Y_3$)**: Probability that remaining session return ($Close_{15:55} - Open_{T+1}$) shares the same sign as opening displacement ($Close_T - Open_{09:30}$).
2. **Remaining Efficiency ($Y_2$)**: Directional efficiency of the remaining day compared to unconditional baseline.
3. **Trend Day Likelihood ($Y_4$)**: Proportion of sessions producing high efficiency + large range after $T$.
4. **Stability Protocol**: Effects must maintain same sign and ordering across IS, Validation, and OOS.
