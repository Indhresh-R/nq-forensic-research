# Hypothesis H03: Passive Liquidity Absorption

## 1. Core Question
When heavy aggressive volume impacts an inside price level but fails to displace the mid-price past that level, does this passive absorption contain forward predictive information signaling a mean-reversion?

## 2. Theoretical Rationale
Institutional market participants frequently use iceberg orders or rapid passive replenishment to accumulate or distribute inventory at specific price levels. When aggressive buyers fail to lift the offer despite extreme trade volume, exhaustion ensues, and the exhausted aggressive buyers become vulnerable to price reversal.

## 3. Mathematical Definitions
For rolling windows $w \in \{5s, 15s, 60s\}$:

* Let $\Delta P_w(t) = P_{\text{mid}}(t) - P_{\text{mid}}(t - w)$.
* Let $\Delta V_w(t) = V_{\text{buy}, w}(t) - V_{\text{sell}, w}(t)$.
* Let $Q_{\text{opp}}(t)$ be the resting depth on the opposing side at $t - w$.

* **Bearish Absorption (Buyers Absorbed by Passive Seller):**
  $$\text{Absorb}_{\text{bear}}(t) = \begin{cases} 
  \frac{V_{\text{buy}, w}(t)}{Q_a^1(t - w) + \epsilon} & \text{if } \Delta P_w(t) \le 0 \text{ and } V_{\text{buy}, w}(t) \ge \text{Percentile}_{90}(V_{\text{buy}, w}) \\
  0 & \text{otherwise}
  \end{cases}$$

* **Bullish Absorption (Sellers Absorbed by Passive Buyer):**
  $$\text{Absorb}_{\text{bull}}(t) = \begin{cases} 
  \frac{V_{\text{sell}, w}(t)}{Q_b^1(t - w) + \epsilon} & \text{if } \Delta P_w(t) \ge 0 \text{ and } V_{\text{sell}, w}(t) \ge \text{Percentile}_{90}(V_{\text{sell}, w}) \\
  0 & \text{otherwise}
  \end{cases}$$

* **Net Absorption Indicator ($NAI_w$):**
  $$NAI_w(t) = \text{Absorb}_{\text{bull}}(t) - \text{Absorb}_{\text{bear}}(t)$$

## 4. Null Hypothesis ($H_0$)
Passive absorption events have zero forward correlation with subsequent mid-price reversal:
$$H_0: \quad IC_\tau = \text{SpearmanCorr}(NAI_w(t), P_{\text{mid}}(t + \tau) - P_{\text{mid}}(t)) = 0$$
for all $w \in \{5s, 15s, 60s\}$ and $\tau \in \{5s, 15s, 60s, 300s\}$.

## 5. Kill Criteria (In-Sample)
H03 will be deemed **KILLED** if:
1. Mean Information Coefficient $|IC_\tau| < 0.02$ across all horizons in In-Sample, OR
2. Mean post-absorption return is not statistically distinct from unconditional return ($p > 0.05$).
