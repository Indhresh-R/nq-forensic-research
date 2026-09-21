# PREREGISTRATION: Hypothesis H02 — Aggressive Order Flow Delta & Microstructure Dynamics

This document establishes the frozen scientific protocol for Hypothesis H02 before running In-Sample evaluation on the 26 audited sessions (`2026-07-08` through `2026-08-12`).

---

## 1. Core Question & Sub-Hypotheses

Does aggressive order flow (trades hitting the bid or lifting the ask) contain forward predictive information for CME Globex E-mini NQ futures, and does Level 3 (MBO) order flow provide incremental value beyond standard trade tape prints?

To prevent hindsight strategy selection, H02 is decomposed into four pre-registered sub-hypotheses:

| Sub-Hypothesis | Research Question | Nature of Test | Primary Horizon |
| :--- | :--- | :--- | :--- |
| **H02-A (Generic CVD)** | Does aggressive volume delta contain unconditional directional continuation information? | Primary Unconditional | $\tau \in \{1s, 5s, 15s, 60s, 300s\}$ |
| **H02-B (Range-Conditioned)** | Does CVD contain incremental predictive information conditional on market range location? | Secondary Conditioned | $\tau \in \{5s, 15s, 60s\}$ |
| **H02-C (Flow Divergence)** | Does price/CVD disagreement at local price extremes predict subsequent mean-reversion? | Conditioned Anomaly | $\tau \in \{15s, 60s, 300s\}$ |
| **H02-D (Passive Absorption)** | Does extreme aggressive flow with price stagnation predict reversal, and does L3 depth confirm it? | Microstructure Anomaly | $\tau \in \{15s, 60s, 300s\}$ |

---

## 2. Mathematical Definitions & Feature Formulations

Let $\mathcal{T}_w(t)$ be the set of continuous aggressive trades occurring in the window $(t - w, t]$, with lookbacks $w \in \{1s, 5s, 15s, 60s\}$.

### 2.1 H02-A: Generic Cumulative Volume Delta
* **Aggressive Volume Delta ($CVD_w$):**
  $$CVD_w(t) = \sum_{k \in \mathcal{T}_w(t), \text{side}_k = 'B'} \text{size}_k - \sum_{k \in \mathcal{T}_w(t), \text{side}_k = 'A'} \text{size}_k$$
* **Normalized Flow Ratio ($NFR_w$):**
  $$NFR_w(t) = \frac{V_{\text{buy}, w}(t) - V_{\text{sell}, w}(t)}{V_{\text{buy}, w}(t) + V_{\text{sell}, w}(t) + \epsilon}$$
* **Aggressive Trade Count Delta ($TCD_w$):**
  $$TCD_w(t) = N_{\text{buy}, w}(t) - N_{\text{sell}, w}(t)$$

### 2.2 H02-B: Range-Conditioned Flow Delta
* **Causal Range Location ($Loc_{15m}(t)$):**
  $$Loc_{15m}(t) = \frac{P_{\text{mid}}(t) - \min_{s \in [t - 900s, t]} P_{\text{mid}}(s)}{\max_{s \in [t - 900s, t]} P_{\text{mid}}(s) - \min_{s \in [t - 900s, t]} P_{\text{mid}}(s) + \epsilon} \in [0, 1]$$
* **Conditioned Regimes:**
  - High Extreme: $Loc_{15m}(t) \ge 0.90$
  - Low Extreme: $Loc_{15m}(t) \le 0.10$
  - Value Area: $0.30 \le Loc_{15m}(t) \le 0.70$

### 2.3 H02-C: Price-Flow Divergence
* Let $\Delta P_w(t) = P_{\text{mid}}(t) - P_{\text{mid}}(t - w)$ and $\sigma_P(t)$ be the rolling 15-minute standard deviation of 5s price changes.
* **Bearish Divergence**: $\Delta P_w(t) \ge +1.5 \sigma_P(t)$ while $CVD_w(t) \le 0$.
* **Bullish Divergence**: $\Delta P_w(t) \le -1.5 \sigma_P(t)$ while $CVD_w(t) \ge 0$.

### 2.4 H02-D: Passive Absorption (Trade-Only vs. L3 MBO)
* **Causal Extreme Volume ($V_{w, 90}^{\text{causal}}(t)$):**
  90th percentile of total trade volume $V_w(t) = V_{\text{buy}, w}(t) + V_{\text{sell}, w}(t)$ calculated strictly over the trailing 1800 seconds (30 minutes) before timestamp $t$. (Cold-start 09:30–09:45 uses frozen baseline from training sessions).
* **Price Stagnation:** $|\Delta P_w(t)| \le 1\text{ tick } (0.25\text{ pts})$.
* **Trade-Only Absorption:**
  - Bearish: $V_{\text{buy}, w}(t) \ge V_{w, 90}^{\text{causal}}(t)$ and $\Delta P_w(t) \le 0$.
  - Bullish: $V_{\text{sell}, w}(t) \ge V_{w, 90}^{\text{causal}}(t)$ and $\Delta P_w(t) \ge 0$.
* **L3 MBO-Confirmed Absorption:**
  - In addition to Trade-Only condition, resting order additions at the opposing inside level exceed fills ($Adds_{\text{opp}, w}(t) \ge Fills_{\text{opp}, w}(t)$), proving passive replenishment rather than just queue starvation.

---

## 3. Strict Causal Safeguards & Event Cooldown

1. **Zero Lookahead:** All features, volatility estimates, range bounds, and volume percentiles are causally computed using only data available at $T \le t$.
2. **Event De-duplication & Cooldown:**
   - When a discrete event condition triggers (in H02-B extreme, H02-C divergence, or H02-D absorption), a refractory period of $\tau_{\text{cooldown}} = 30\text{ seconds}$ is enforced.
   - Consecutive seconds satisfying the condition within this cooldown window are merged into a single event observation to prevent inflated sample size ($N$) and spurious statistical significance.

---

## 4. Incremental Information Framework ($\Delta IC$)

To ensure that flow features provide real alpha rather than piggybacking on price/range state:
$$\text{Model A (State Baseline):} \quad R_{t, \tau} \sim Loc_{15m}(t) + \Delta P_{60s}(t) + \sigma_{\text{vol}}(t)$$
$$\text{Model B (Full Model):} \quad R_{t, \tau} \sim Loc_{15m}(t) + \Delta P_{60s}(t) + \sigma_{\text{vol}}(t) + F_{\text{flow}}(t)$$

Incremental Information Coefficient:
$$\Delta IC = IC(\text{Model B}) - IC(\text{Model A})$$
Survives only if $\Delta IC \ge +0.015$ with adjusted $p < 0.01$.

---

## 5. Multiple-Testing Correction & Kill Gates

Across all tested combinations of lookbacks, horizons, and sub-hypotheses:
- Benjamini-Hochberg (BH) False Discovery Rate ($q = 0.05$).
- Holm-Bonferroni Family-Wise Error Rate ($\alpha = 0.05$).

### Pre-Registered Kill Gates:

1. **H02-A Kill Gate:**
   - $|IC_{\tau}| < 0.02$ across all $\tau \in \{1s, 5s, 15s, 60s, 300s\}$, OR
   - BH-adjusted $p > 0.01$, OR
   - Non-monotonic quintile return spread $\implies$ **H02-A KILLED**.

2. **H02-B Kill Gate:**
   - Incremental $\Delta IC < +0.015$ over range location alone, OR
   - Conditioned IC not statistically significant ($p_{\text{adj}} > 0.01$) $\implies$ **H02-B KILLED**.

3. **H02-C Kill Gate:**
   - Event-level forward return spread $\le 0$ after friction, OR
   - Incremental $\Delta IC < +0.015$ over price excursion alone $\implies$ **H02-C KILLED**.

4. **H02-D Kill Gate:**
   - Number of independent de-duplicated events $< 100$, OR
   - Post-absorption reversal return fails execution friction gate ($< 0.50\text{ pts}$), OR
   - L3 MBO-confirmed absorption does not outperform Trade-Only absorption ($p > 0.05$) $\implies$ **H02-D KILLED**.
