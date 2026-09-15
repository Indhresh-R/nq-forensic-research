# Testing Methodology: Strategy 37

## Causality Card
```text
Information Available: Completed Globex prints up to 09:29 ET
Targets: Full RTH Session 09:30 to 15:55 ET
Lookahead: Strictly zero
Splits: IS (2010–2021), Validation (2022–2024), OOS (2025–2026)
```

## Statistical Evaluation
1. **Continuation vs Mean Reversion Rate**: Compare the percentage of sessions where RTH moves in the direction of the overnight gap against the 50% null.
2. **Directional Efficiency**: Compare the mean RTH directional efficiency ($|Close - Open| / (High - Low)$) for each overnight category against the unconditional population mean.
3. **Clean Trend Day Likelihood**: Compare the probability of experiencing a top-quartile range + high efficiency trend day across extension regimes (e.g. True Gap Up vs Inside Day).
4. **Monotonicity & Stability**: Verify whether any observed lift persists monotonically across IS, Validation, and OOS.
