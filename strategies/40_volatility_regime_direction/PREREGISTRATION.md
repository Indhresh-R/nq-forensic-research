# PREREGISTRATION: Strategy 40 -- Volatility Persistence → Directional Distribution

**Registration Date:** 2026-09-14  
**Status:** FROZEN  
**Target Asset:** Continuous E-mini Nasdaq-100 Futures (NQ) 1-Minute Bars (2010--2026)  
**Primary Question:** When NQ enters a high-volatility or low-volatility regime, does that regime systematically alter the conditional distribution of subsequent RTH direction, directional polarity, or continuation of prior momentum?

---

## 1. Research Philosophy & Information Protocol
1. **Decoupling Volatility from Direction**: Strategy 39 proved that volatility clusters (high vol follows high vol, low vol follows low vol). We now evaluate whether this confirmed "WHEN" conditions "WHICH WAY".
2. **Information-First Protocol**: Strictly an informational and distributional inquiry. **No trade execution, stops, targets, or monetization rules are tested.**
3. **Hypothesis Under Test**:
   - **Hypothesis A (Momentum)**: High-expansion sessions persist in the same direction ($P(\text{same sign}) > 53\%$).
   - **Hypothesis B (Reversal / Exhaustion)**: High-expansion sessions exhaust momentum, causing mean reversion ($P(\text{same sign}) < 47\%$).
   - **Hypothesis C (Symmetric Volatility Null)**: High-expansion sessions expand volatility symmetrically without altering directional odds ($P(\text{same sign}) \approx 50\%$, $P(\text{up}) \approx 50\%$).

---

## 2. Pre-Open Feature Definitions (Strictly Known at $t \le 09:29\text{ ET}$)
All features use historical RTH bars up through session $t-1$:

1. **Prior Volatility State ($V_{t-1}$)**:
   - Prior Day Range vs 20-Day Median: $\text{Ratio}_{t-1} = \text{Range}_{t-1} / \text{Median}_{20}(\text{Range})$
     - `DEEP_COMP` ($< 0.65$), `NORMAL` ($0.65 \to 1.20$), `HIGH_EXP` ($> 1.20$).
   - Prior Normalized Range: $\text{NormRange}_{t-1} = \text{Range}_{t-1} / \text{ATR}_{20, t-1}$
     - `LOW_VOL` ($< 0.75$), `NORMAL_VOL` ($0.75 \to 1.25$), `HIGH_VOL` ($> 1.25$), `EXTREME_VOL` ($> 1.50$).
   - Trailing 5-Day Realized Range Quintile: $Q_1$ to $Q_5$.
2. **Prior Directional Displacement ($D_{t-1}$)**:
   - Normalized return: $\text{NormReturn}_{t-1} = (Close_{RTH, t-1} - Open_{RTH, t-1}) / \text{ATR}_{20, t-1}$
     - `LARGE_UP` ($\ge +0.75$), `MILD_UP` ($+0.20 \to +0.75$), `FLAT` ($-0.20 \to +0.20$), `MILD_DOWN` ($-0.75 \to -0.20$), `LARGE_DOWN` ($\le -0.75$).
3. **Crossed Regimes ($VD_{t-1}$)**:
   - `EXPANSION_UP`: $\text{NormRange}_{t-1} \ge 1.25$ AND $\text{Return}_{t-1} > 0$
   - `EXPANSION_DOWN`: $\text{NormRange}_{t-1} \ge 1.25$ AND $\text{Return}_{t-1} < 0$
   - `COMPRESSION_UP`: $\text{NormRange}_{t-1} < 0.75$ AND $\text{Return}_{t-1} > 0$
   - `COMPRESSION_DOWN`: $\text{NormRange}_{t-1} < 0.75$ AND $\text{Return}_{t-1} < 0$
   - `NORMAL`: $0.75 \le \text{NormRange}_{t-1} < 1.25$

---

## 3. Dependent Targets (Next RTH Session: 09:30 to 15:55 ET)
1. **RTH Return ($Y_1$)**:
   - Nominal points: $\text{Return}_{pts} = Close_{RTH, t} - Open_{RTH, t}$
   - ATR-normalized return: $\text{Return}_{norm} = \text{Return}_{pts} / \text{ATR}_{20, t-1}$
2. **Directional Polarity ($Y_2$)**:
   - $P(Close_{RTH, t} > Open_{RTH, t})$
3. **Directional Continuation Rate ($Y_3$)**:
   - $\mathbb{I}\left(\text{Sign}(\text{Return}_t) == \text{Sign}(\text{Return}_{t-1})\right)$
4. **Tail Expansion Asymmetry ($Y_4$)**:
   - Large Up Move: $P(\text{Return}_{norm} \ge +1.0)$ and $P(\text{Return}_{norm} \ge +1.5)$
   - Large Down Move: $P(\text{Return}_{norm} \le -1.0)$ and $P(\text{Return}_{norm} \le -1.5)$
   - Tail Asymmetry: $P(\text{Large Up}) - P(\text{Large Down})$
5. **Unilateral Excursion Net Bias ($Y_5$)**:
   - Normalized Upside: $(High_t - Open_t) / \text{ATR}_{20, t-1}$
   - Normalized Downside: $(Open_t - Low_t) / \text{ATR}_{20, t-1}$
   - Excursion Net Spread: $\text{Mean(Upside)} - \text{Mean(Downside)}$
6. **Close-Location Pinning ($Y_6$)**:
   - Bullish Pin Rate: $P((Close - Low)/Range \ge 0.80)$
   - Bearish Pin Rate: $P((Close - Low)/Range \le 0.20)$
7. **Clean Bull vs Bear Trend Day Rates ($Y_7$)**:
   - Bull Trend: $Range_{norm} \ge 1.0$ AND $Efficiency \ge 0.60$ AND $Return > 0$
   - Bear Trend: $Range_{norm} \ge 1.0$ AND $Efficiency \ge 0.60$ AND $Return < 0$

---

## 4. Chronological Splits
- **In-Sample (IS)**: 2011-01-01 to 2021-12-31 (~2,100 sessions post-warmup)
- **Validation**: 2022-01-01 to 2024-12-31 (~750 sessions)
- **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (split into 2025 and 2026)

---

## 5. Hostile Kill / Promotion Criteria
1. **Promotion (Directional Alpha)**:
   - High-volatility states alter directional continuation rate or win rate by $\ge \pm 5$ percentage points from baseline (continuation $\ge 56\%$ or $\le 44\%$, or tail asymmetry spread $\ge 10\%$).
   - Must hold in IS ($p < 0.01$), survive Validation, and survive OOS (2025–2026).
2. **Scientific Null (Verdict C - Boundary Established)**:
   - Volatility expands ($Range \approx 1.2\times$ ATR), but continuation rate hovers tightly around 48%–52% (random coin flip), and tail moves expand symmetrically up and down.
   - Formally records: **"Volatility is predictable; Direction is NOT."** Strategy 40 is killed as a directional signal.
3. **Instability (Verdict C)**:
   - Tendencies flip signs across splits (e.g. positive continuation in IS flips to negative in OOS).
