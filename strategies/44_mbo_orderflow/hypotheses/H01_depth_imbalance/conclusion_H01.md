# Hypothesis H01: Depth Imbalance (OBI) — Forensic Verdict

## Formal Status: KILLED AT INFORMATION GATE ❌

### 1. In-Sample Diagnostic Surface (26 Sessions / 234,000 Observations)

| Feature | Horizon ($\tau$) | Mean Rank IC | Std IC | $t$-Statistic | $p$-Value | Monotonic? | $Q_1$ Return | $Q_5$ Return | $Q_5 - Q_1$ Spread | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$OBI_1$** | **1s** | **+0.0162** | 0.0140 | 5.91 | $3.63 \times 10^{-6}$ | False | -0.044 pts | +0.041 pts | +0.086 pts | **FAIL** ($IC < 0.02$) |
| **$OBI_1$** | **5s** | **+0.0083** | 0.0109 | 3.88 | $6.74 \times 10^{-4}$ | False | -0.086 pts | +0.037 pts | +0.124 pts | **FAIL** ($IC < 0.02$) |
| **$OBI_1$** | **15s** | **+0.0077** | 0.0106 | 3.72 | $1.01 \times 10^{-3}$ | False | -0.124 pts | +0.084 pts | +0.208 pts | **FAIL** ($IC < 0.02$) |
| **$OBI_1$** | **60s** | **+0.0076** | 0.0114 | 3.38 | $2.40 \times 10^{-3}$ | False | -0.331 pts | +0.139 pts | +0.470 pts | **FAIL** ($IC < 0.02$) |
| **$OBI_1$** | **300s** | **+0.0037** | 0.0124 | 1.52 | $0.140$ | False | -0.599 pts | +0.357 pts | +0.956 pts | **FAIL** ($IC < 0.02$) |
| **$OBI_5$** | **1s** | **+0.0100** | 0.0135 | 3.79 | $8.40 \times 10^{-4}$ | False | -0.013 pts | +0.009 pts | +0.022 pts | **FAIL** ($IC < 0.02$) |
| **$OBI_5$** | **5s** | **+0.0038** | 0.0147 | 1.33 | $0.196$ | False | -0.006 pts | -0.001 pts | +0.005 pts | **FAIL** ($IC < 0.02$) |
| **$OBI_5$** | **15s** | **-0.0009** | 0.0163 | -0.28 | $0.783$ | False | +0.048 pts | -0.079 pts | -0.127 pts | **FAIL** ($IC \approx 0$) |
| **$OBI_5$** | **60s** | **+0.0004** | 0.0193 | 0.11 | $0.916$ | False | +0.056 pts | -0.088 pts | -0.144 pts | **FAIL** ($IC \approx 0$) |
| **$OBI_5$** | **300s** | **-0.0077** | 0.0306 | -1.28 | $0.211$ | False | +0.403 pts | -0.915 pts | -1.318 pts | **FAIL** ($IC \approx 0$) |

---

### 2. Forensic Analysis & Key Findings

1. **Weak Mechanical Signal Below Threshold:**
   * $OBI_1$ exhibits a statistically significant positive rank correlation at ultra-short horizons ($t = 5.91$ at 1s, $t = 3.88$ at 5s). This confirms that resting quote asymmetry exerts real physical queue pressure on the inside market.
   * However, the peak Information Coefficient is **$0.0162$ at 1 second**, which fails the preregistered minimum bar of $|IC| \ge 0.02$. By 5 seconds, it decays by 50% to **$0.0083$**.
2. **Economic Reality vs. Friction:**
   * At 1 second, the gross point difference between the highest imbalance quintile ($Q_5$) and lowest ($Q_1$) is only **$+0.086$ points ($1.72 per contract)**.
   * At 5 seconds, the gross spread is **$+0.124$ points ($2.48 per contract)**.
   * At 15 seconds, the gross spread is **$+0.208$ points ($4.16 per contract)**.
   * In continuous E-mini NQ futures, one single tick is **$0.25$ points ($5.00)**, and baseline round-trip transaction costs (slippage, exchange fees, clearing) are at least **$1.00$ point ($20.00)**.
   * An edge of $+0.08$ to $+0.20$ points is **completely submerged by bid-ask friction** before latency or queue position can even be addressed.
3. **Deep Book Imbalance ($OBI_5$) Adds Zero Information:**
   * Beyond Level 1, $OBI_5$ collapses to noise immediately ($IC = 0.0038$ at 5s, $IC = -0.0009$ at 15s). Resting depth 2 to 5 levels away contains no directional predictive power for NQ mid-price changes.

---

### 3. Conclusion & Next Action
In accordance with [`PREREGISTRATION.md`](../../PREREGISTRATION.md):
* **Hypothesis H01 is permanently KILLED.**
* **No trading strategy, parameter optimization, or execution rules will be built for H01.**
* The research track cleanly advances to **Hypothesis H02: Aggressive Order Flow Delta**.
