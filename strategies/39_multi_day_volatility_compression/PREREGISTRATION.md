# PREREGISTRATION: Strategy 39 -- Multi-Day Volatility Compression → RTH Expansion & Persistence

**Registration Date:** 2026-09-14  
**Status:** FROZEN  
**Target Asset:** Continuous E-mini Nasdaq-100 Futures (NQ) 1-Minute Bars (2010--2026)  
**Primary Question:** Does multi-day volatility compression known before the RTH open change the probability or magnitude of subsequent RTH range expansion or directional persistence?

---

## 1. Information-First Protocol
1. **No Trade Execution / Monetization**: This is strictly an information discovery scan. No stops, targets, or trading rules are implemented.
2. **Decoupled "WHEN" from "WHICH WAY"**: Volatility compression is investigated purely as an expansion gate ("WHEN"), without requiring or assuming directional polarity ("WHICH WAY").
3. **No Threshold Mining**: Analysis evaluates predetermined quantile bins (quintiles, tertiles) and established structural patterns (NR4, NR7) across the entire 16-year history.

---

## 2. Pre-Open Feature Definitions (Strictly Known at $t \le 09:29\text{ ET}$)
All features use historical RTH and full-day bars up through session $t-1$:

1. **3-Day Realized Range Percentile ($F_1$)**: Trailing 252-day percentile rank of the 3-day average RTH range.
2. **5-Day Realized Range Percentile ($F_2$)**: Trailing 252-day percentile rank of the 5-day average RTH range.
3. **10-Day Realized Range Percentile ($F_3$)**: Trailing 252-day percentile rank of the 10-day average RTH range.
4. **20-Day ATR Percentile ($F_4$)**: Trailing 252-day percentile rank of the 20-day ATR.
5. **Narrow Range Patterns ($F_5$)**:
   - `NR4`: $\text{Range}_{t-1} < \min_{i=2..4} \text{Range}_{t-i}$
   - `NR7`: $\text{Range}_{t-1} < \min_{i=2..7} \text{Range}_{t-i}$
   - `ID_NR4`: Inside Day AND NR4
   - `ID_NR7`: Inside Day AND NR7
6. **Consecutive Contracting Days ($F_6$)**: Number of consecutive days of strictly decreasing daily range ($\text{Range}_{t-1} < \text{Range}_{t-2} < \dots$).
7. **Current Range to 20-Day Median Ratio ($F_7$)**: $\text{Range}_{t-1} / \text{Median}_{20}(\text{Range})$.
8. **Compression Duration ($F_8$)**: Consecutive days where daily range was below the 20-day median range.

---

## 3. Dependent Targets (Next RTH Session: 09:30 to 15:55 ET)
1. **Normalized Range ($Y_1$)**: $\text{Range}_{norm} = (\text{High}_{RTH} - \text{Low}_{RTH}) / \text{ATR}_{20}$.
2. **Normalized Absolute Return ($Y_2$)**: $|Close_{RTH} - Open_{RTH}| / \text{ATR}_{20}$.
3. **Directional Efficiency ($Y_3$)**: $|Close_{RTH} - Open_{RTH}| / \text{Range}_{RTH} \in [0.0, 1.0]$.
4. **Clean Trend Day Probability ($Y_4$)**: Fraction of sessions where $\text{Range}_{norm} \ge 1.0$ AND $\text{Efficiency} \ge 0.60$.
5. **Extreme Expansion Probability ($Y_5$)**: Fraction of sessions where $\text{Range}_{norm} \ge 1.25$ and $\ge 1.50$.
6. **Maximum Excursion ($Y_6$)**: $\max(\text{High} - \text{Open}, \text{Open} - \text{Low}) / \text{ATR}_{20}$.
7. **Close-Location Pinning ($Y_7$)**: Rate of $(Close - Low) / Range$ falling $< 0.20$ or $> 0.80$.

---

## 4. Chronological Splits
- **In-Sample (IS)**: 2010-01-01 to 2021-12-31 (12 years)
- **Validation (VAL)**: 2022-01-01 to 2024-12-31 (3 years)
- **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (split into 2025 and 2026)

---

## 5. Hostile Kill Criteria
A compression regime passes only if:
1. **In-Sample Effect**: Statistically significant increase ($p < 0.01$) in $\text{Range}_{norm}$ or clean trend-day rate over unconditional baseline.
2. **Validation Survival**: Direction and magnitude persist across 2022–2024.
3. **OOS Survival**: Effect holds in 2025–2026.
4. **Economic Magnitude**: Substantial lift (e.g. trend-day rate $\ge 35\%$ vs 25% baseline, or range expansion $\ge 1.20\times$ baseline).
5. **Monotonicity**: Effect cannot be isolated to an arbitrary cutoff.
6. **Normalization Control**: Confirmed in ATR-normalized units to reject macro vol confounds.

If these conditions are not met, **Strategy 39 is KILLED at the Information Gate (Verdict C)**.
