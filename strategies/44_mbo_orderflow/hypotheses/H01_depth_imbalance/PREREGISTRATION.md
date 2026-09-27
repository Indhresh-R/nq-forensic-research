# Hypothesis H01: Depth Imbalance (OBI)

## 1. Core Question
Does resting liquidity asymmetry between the bid and ask sides at the top of the limit order book predict directional displacement of the mid-price over subsequent horizons?

## 2. Theoretical Rationale
When resting bid quantity significantly exceeds resting ask quantity, an incoming random or Poisson-distributed stream of market orders is mathematically more likely to exhaust the smaller ask side than the larger bid side, forcing an upward mid-price adjustment (and vice-versa).

## 3. Mathematical Definitions
Let $Q_b^i(t)$ and $Q_a^i(t)$ denote resting quantities at the $i$-th price level from the inside market:

* **Level 1 (Top-of-Book) Imbalance:**
  $$OBI_1(t) = \frac{Q_b^1(t) - Q_a^1(t)}{Q_b^1(t) + Q_a^1(t)}$$

* **Level 5 Depth Imbalance:**
  $$OBI_5(t) = \frac{\sum_{i=1}^5 Q_b^i(t) - \sum_{i=1}^5 Q_a^i(t)}{\sum_{i=1}^5 Q_b^i(t) + \sum_{i=1}^5 Q_a^i(t)}$$

* **Decay-Weighted Level 5 Imbalance:**
  $$WOBI_5(t) = \frac{\sum_{i=1}^5 \frac{Q_b^i(t)}{i} - \sum_{i=1}^5 \frac{Q_a^i(t)}{i}}{\sum_{i=1}^5 \frac{Q_b^i(t)}{i} + \sum_{i=1}^5 \frac{Q_a^i(t)}{i}}$$

## 4. Null Hypothesis ($H_0$)
The resting order book imbalance has zero forward predictive correlation with mid-price changes:
$$H_0: \quad IC_\tau = \text{SpearmanCorr}(OBI(t), P_{\text{mid}}(t + \tau) - P_{\text{mid}}(t)) = 0$$
for all $\tau \in \{1s, 5s, 15s, 60s, 300s\}$.

## 5. Kill Criteria (In-Sample)
H01 will be deemed **KILLED** if:
1. Mean Information Coefficient $|IC_\tau| < 0.02$ across all horizons $\tau$ in the 26 In-Sample sessions, OR
2. The $t$-statistic on the mean daily IC is $< 2.0$ ($p > 0.05$), OR
3. Forward returns across quintiles fail the strict monotonicity condition ($Q_5 > Q_4 > Q_3 > Q_2 > Q_1$).

If killed, no trading strategy or execution simulation will be built.
