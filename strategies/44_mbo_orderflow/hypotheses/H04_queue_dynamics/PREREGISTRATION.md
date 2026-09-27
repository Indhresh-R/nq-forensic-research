# Hypothesis H04: Queue Dynamics & Cancellation Velocity

## 1. Core Question
Do rapid changes in order cancellation rates, queue depletion velocity, or asymmetric order additions at the inside market predict impending queue collapse and mid-price displacement?

## 2. Theoretical Rationale
High-frequency market makers and informed traders rapidly cancel resting liquidity when they perceive toxic flow or adverse selection risk. A sudden asymmetric surge in cancellations on one side of the book often precedes quotes being swept or repriced.

## 3. Mathematical Definitions
For rolling time windows $w \in \{1s, 5s, 15s\}$:

* Let $C_b,w(t)$ be the total quantity of resting bid orders cancelled (`action == 'C'`) in $(t - w, t]$.
* Let $C_a,w(t)$ be the total quantity of resting ask orders cancelled in $(t - w, t]$.
* Let $A_b,w(t)$ and $A_a,w(t)$ be total new resting orders added (`action == 'A'`).

* **Cancellation Imbalance Ratio ($CIR_w$):**
  $$CIR_w(t) = \frac{C_a,w(t) - C_b,w(t)}{C_a,w(t) + C_b,w(t) + \epsilon}$$
  *(Positive when asks are being cancelled faster than bids, indicating bullish vulnerability).*

* **Net Queue Flow Velocity ($NQV_w$):**
  $$NQV_w(t) = (A_b,w(t) - C_b,w(t)) - (A_a,w(t) - C_a,w(t))$$

## 4. Null Hypothesis ($H_0$)
Cancellation velocity and queue dynamics have zero forward predictive correlation with mid-price changes:
$$H_0: \quad IC_\tau = \text{SpearmanCorr}(CIR_w(t), P_{\text{mid}}(t + \tau) - P_{\text{mid}}(t)) = 0$$
for all $w \in \{1s, 5s, 15s\}$ and $\tau \in \{1s, 5s, 15s, 60s, 300s\}$.

## 5. Kill Criteria (In-Sample)
H04 will be deemed **KILLED** if:
1. Mean Information Coefficient $|IC_\tau| < 0.02$ across all combinations of $(w, \tau)$ in In-Sample, OR
2. The $t$-statistic on mean session IC is $< 2.0$ ($p > 0.05$), OR
3. Quintile forward return profiles fail monotonicity.
