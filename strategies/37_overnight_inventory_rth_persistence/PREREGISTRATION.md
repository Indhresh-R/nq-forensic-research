# Strategy 37: Overnight Inventory → RTH Directional Persistence -- Pre-Registration

**Pre-registration Date:** 2026-09-14  
**Status:** FROZEN BEFORE INFORMATION SCAN EXECUTION

This document locks all definitions, feature representations, persistence metrics, statistical tests, and promotion/kill gates before executing the scan.

---

## 1. Core Research Question
Does structural overnight inventory (measured strictly prior to the 09:30 ET cash open) materially alter the probability and distribution of RTH directional persistence in continuous E-mini Nasdaq-100 (NQ) futures?

### Null Hypothesis ($H_0$):
The conditional distribution of RTH directional persistence given any pre-market overnight inventory state is identical to the unconditional RTH baseline distribution. Overnight inventory conveys zero predictive or conditioning information regarding RTH trendiness, continuation, or expansion.

---

## 2. Universe, Data, and Splits
- **Market**: Continuous E-mini Nasdaq-100 (NQ), tick size 0.25, point value $20.00.
- **Session Definitions**:
  - Globex Overnight Session: 18:00 ET (prior calendar date) to 09:29 ET.
  - Cash RTH Session: 09:30 ET to 15:55 ET.
- **Chronological Splits**:
  - In-Sample (IS): 2010-01-01 to 2021-12-31 (12 years)
  - Validation: 2022-01-01 to 2024-12-31 (3 years)
  - Out-of-Sample (OOS): 2025-01-01 to 2026-08 (split into 2025 and 2026)

---

## 3. Pre-Market Information Set (Available Strictly at $t \le 09:29$ ET)

1. **Gap ($G_1$)**:
   $$\text{Gap\_Pts} = Open_{09:30} - Close_{15:55, \text{prev}}$$
   $$\text{Gap\_Norm} = \frac{\text{Gap\_Pts}}{\text{ATR}_{20}}$$
   - Large Gap Up: $\text{Gap\_Norm} \ge +0.50$
   - Moderate Gap Up: $+0.15 \le \text{Gap\_Norm} < +0.50$
   - Neutral Gap: $-0.15 < \text{Gap\_Norm} < +0.15$
   - Moderate Gap Down: $-0.50 < \text{Gap\_Norm} \le -0.15$
   - Large Gap Down: $\text{Gap\_Norm} \le -0.50$

2. **Overnight Range Ratio ($G_2$)**:
   $$\text{ONR} = ON\_High - ON\_Low$$
   $$\text{ONR\_Ratio} = \frac{\text{ONR}}{\text{ATR}_{20}}$$
   - Compressed Overnight: $\text{ONR\_Ratio} < 0.40$
   - Normal Overnight: $0.40 \le \text{ONR\_Ratio} \le 0.80$
   - Expanded Overnight: $\text{ONR\_Ratio} > 0.80$

3. **Overnight Inventory Location ($G_3$)**:
   $$\text{Location} = \frac{Close_{09:29} - ON\_Low}{ON\_High - ON\_Low} \in [0.0, 1.0]$$
   - Pinned Long: $\text{Location} \ge 0.80$
   - Upper Middle: $0.60 \le \text{Location} < 0.80$
   - Balanced: $0.40 \le \text{Location} < 0.60$
   - Lower Middle: $0.20 < \text{Location} \le 0.40$
   - Pinned Short: $\text{Location} \le 0.20$

4. **Overnight Extension Regime ($G_4$)**:
   - `TRUE_GAP_UP`: $ON\_Low > RTH\_High_{\text{prev}}$
   - `EXTENSION_UP`: $ON\_High > RTH\_High_{\text{prev}}$ and $ON\_Low \le RTH\_High_{\text{prev}}$
   - `INSIDE_BALANCED`: $ON\_High \le RTH\_High_{\text{prev}}$ and $ON\_Low \ge RTH\_Low_{\text{prev}}$
   - `EXTENSION_DOWN`: $ON\_Low < RTH\_Low_{\text{prev}}$ and $ON\_High \ge RTH\_Low_{\text{prev}}$
   - `TRUE_GAP_DOWN`: $ON\_High < RTH\_Low_{\text{prev}}$

5. **Directional Confluence ($G_5$)**:
   $$\text{Confluence} = \text{Sign}(RTH\_Return_{\text{prev}}) \times \text{Sign}(\text{Gap\_Pts})$$
   - `PRO_TREND` ($+1$): Prior day direction aligns with overnight gap direction.
   - `COUNTER_TREND` ($-1$): Overnight gap opposes prior day direction.

---

## 4. Dependent Variables: RTH Directional Persistence Targets

For each session $09:30 \to 15:55$ ET:
1. **$Y_1$ (RTH Return)**: $Close_{15:55} - Open_{09:30}$
2. **$Y_2$ (Directional Efficiency)**: $\frac{|Close_{15:55} - Open_{09:30}|}{RTH\_High - RTH\_Low} \in [0.0, 1.0]$
3. **$Y_3$ (Gap Continuation Probability)**: $\mathbb{I}(\text{Sign}(Y_1) == \text{Sign}(\text{Gap\_Pts}))$
4. **$Y_4$ (Clean Trend Day Probability)**: $\mathbb{I}(RTH\_Range \ge \text{Median}(RTH\_Range) \text{ and } Y_2 \ge 0.60)$
5. **$Y_5$ (Asymmetry Excursion)**: $MFE - MAE$

---

## 5. Promotion / Kill Gates (Information Phase)
- **Promote to Phase 2 (Monetization)**:
  1. Statistically significant difference ($p < 0.01$) in RTH Directional Persistence ($Y_2, Y_3, Y_4$) between conditioning states and the unconditional baseline.
  2. The informational effect must hold its sign and rank order monotonically across In-Sample, Validation, and Out-of-Sample.
- **Kill Strategy 37 (C)**:
  - If conditional distributions do not differ significantly from baseline, or if conditional persistence flips across splits, Strategy 37 is killed immediately without attempting trade execution or parameter mining.
