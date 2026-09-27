# PREREGISTRATION: Strategy 44 — Level 3 (MBO) Order Flow Information

This document formally pre-registers the forensic rules, causal horizons, partition splits, and scientific promotion gates for Strategy 44 before running information tests.

---

## 1. Core Principles & Safeguards

1. **Infrastructure Freeze:**
   - [`d:\NQ-2\common\order_book.py`](file:///d:/NQ-2/common/order_book.py) is frozen read-only infrastructure. Strategy 44 consumes book state but never modifies the reconstruction engine.
2. **Strict Causal Event Horizon:**
   - For any decision timestamp $T$, features are calculated strictly using events where $\text{ts\_event} \le T$.
   - Forward returns are evaluated strictly on events occurring at or after $T + \tau$. No event occurring at $T$ may contribute to both feature value and outcome evaluation.
3. **Information-First Gate:**
   - No trading strategy, backtest, entry/exit rules, or parameter optimization will be constructed unless a hypothesis first demonstrates statistically significant predictive information in the In-Sample split.

---

## 2. Chronological Data Partitions (50 MBO Sessions)

The 50 audited sessions (`2026-07-08` through `2026-09-16`) are strictly partitioned chronologically:

| Split | Sessions | Date Range | Usage Policy |
| :--- | :--- | :--- | :--- |
| **In-Sample (IS)** | **26 sessions** | `2026-07-08` to `2026-08-12` | Feature calibration, distribution analysis, information testing |
| **Validation** | **12 sessions** | `2026-08-13` to `2026-08-28` | One-shot confirmation of surviving features |
| **Out-of-Sample (OOS)** | **12 sessions** | `2026-08-31` to `2026-09-16` | Final evaluation (contains September quarterly roll) |

---

## 3. Forward Horizons & Target Variables

Predictions are evaluated against mid-price changes:

$$\Delta P_{t, \tau} = P_{\text{mid}}(t + \tau) - P_{\text{mid}}(t)$$

Where:
$$P_{\text{mid}}(t) = \frac{\text{BestBid}(t) + \text{BestAsk}(t)}{2}$$

Evaluation Horizons:
* $\tau_1 = 1\text{ second}$ (Ultra-short latency edge)
* $\tau_2 = 5\text{ seconds}$ (Queue depletion horizon)
* $\tau_3 = 15\text{ seconds}$ (Microstructure displacement)
* $\tau_4 = 60\text{ seconds}$ (Short-term trend initiation)
* $\tau_5 = 300\text{ seconds}$ (5-minute structural follow-through)

Sampling Grid:
* Decision timestamps sampled every $1.0\text{ second}$ during active market hours:
  * Primary Window: **09:30:00 to 12:00:00 EDT** (13:30:00 to 16:00:00 UTC)

---

## 4. The Four Independent Hypotheses

### Hypothesis H01: Depth Imbalance (OBI)
* **Question:** Does resting liquidity asymmetry at the top of the book predict directional mid-price pressure?
* **Feature:**
  $$OBI_1(t) = \frac{Q_b^1(t) - Q_a^1(t)}{Q_b^1(t) + Q_a^1(t)}$$
  $$OBI_5(t) = \frac{\sum_{i=1}^5 Q_b^i(t) - \sum_{i=1}^5 Q_a^i(t)}{\sum_{i=1}^5 Q_b^i(t) + \sum_{i=1}^5 Q_a^i(t)}$$

### Hypothesis H02: Aggressive Order Flow Delta & Microstructure Dynamics
* **Question:** Does aggressive order flow (hitting bid / lifting ask) predict directional displacement, and does Level 3 (MBO) order flow provide incremental predictive power beyond trade-only tape?
* **Sub-Hypotheses:**
  - **H02-A (Generic CVD):** Unconditional rank correlation of $CVD_w$ across horizons $\tau \in \{1s, 5s, 15s, 60s, 300s\}$.
  - **H02-B (Range-Conditioned):** Incremental information of CVD conditional on 15m range location ($Loc_{15m}$).
  - **H02-C (Flow Divergence):** Price/CVD divergence at local price extremes predicting mean-reversion.
  - **H02-D (Passive Absorption):** Extreme volume with price stagnation and L3 resting replenishment ($Adds \ge Fills$).
* **Safeguards:** Zero-lookahead causal rolling percentiles (trailing 1800s), event de-duplication with 30s cooldown, Benjamini-Hochberg FDR correction, and incremental information gating ($\Delta IC \ge +0.015$).

### Hypothesis H03: Liquidity Absorption (Integrated with H02-D)
* Focuses on deep queue dynamics and iceberg detection under heavy flow.

### Hypothesis H04: Queue Dynamics (Cancel / Add Ratios)
* **Question:** Do sudden spikes in cancel-to-add rates or asymmetric depth replenishment predict queue collapse?
* **Feature:** Net order arrival velocity and cancellation ratio over rolling 1s and 5s windows.

---

## 5. Promotion & Kill Gates

For each hypothesis $H_i$, the following metrics are computed across all In-Sample decision points:

1. **Information Coefficient (Spearman Rank Correlation):**
   $$IC_\tau = \text{SpearmanCorr}(F(t), \Delta P_{t, \tau})$$
2. **Multiple-Testing Corrected Significance:**
   Raw $p$-values adjusted via Benjamini-Hochberg (FDR $q = 0.05$) and Holm-Bonferroni.
3. **Incremental Information Gate (for conditioned hypotheses):**
   $$\Delta IC = IC(\text{State} + \text{Flow}) - IC(\text{State}) \ge +0.015 \quad (p_{\text{adj}} < 0.01)$$
4. **Monotonicity Across Quintiles:**
   Mean forward return across quintiles must be strictly monotonic.
5. **Execution Feasibility:**
   Mid-price theoretical return must withstand realistic taker spread-crossing and friction.

### The Kill Rule (Hard Stop)
* A sub-hypothesis is **KILLED** in In-Sample if it fails its preregistered primary gate, exhibits $|IC| < 0.02$ (or $\Delta IC < 0.015$), fails monotonicity, or has $p_{\text{adj}} > 0.01$.
* **Killed hypotheses are frozen immediately.** No execution rules, backtests, or secondary feature combinations will be attempted.
