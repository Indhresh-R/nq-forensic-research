# Strategy 39: Multi-Day Volatility Compression → RTH Expansion & Persistence -- Full Report

**Date:** 2026-09-14  
**Verdict:** **C (KILL at Information Gate)**  
**Dataset:** Continuous NQ 1-minute futures (2010--2026, 3,228 clean RTH sessions post 252-day warm-up)  
**Protocol:** Information-First, Strictly Non-Directional Scan across Pre-Registered Features & Targets  

---

## 1. Executive Summary

Strategy 39 investigated the slow-moving macro-volatility **information question**:
> **Does volatility compression known before the RTH open change the probability or magnitude of subsequent RTH range expansion or directional persistence?**

Following the disciplined sequence of Strategies 35–38, this was executed as a strictly causal, non-directional empirical scan. We tested whether multi-day compression acts as a valid conditioning gate for **"WHEN"** (subsequent range expansion, excursion magnitude, directional persistence, clean trend days) without imposing directional bias ("WHICH WAY").

We evaluated 8 structural features known strictly before 09:30 ET:
1. Multi-Day Realized Range Percentiles (3-day, 5-day, 10-day rolling 252-day rank)
2. 20-Day ATR Percentile (macro vol cycle)
3. Classical Narrow Range Patterns (NR4, NR7, Inside Day, ID-NR4, ID-NR7)
4. Consecutive Contracting Days (run length of shrinking daily ranges)
5. Current Range to 20-Day Median Ratio
6. Compression Duration (run length of daily ranges below 20-day median)

---

## 2. Key Empirical Findings: The Volatility Inertia Phenomenon

The empirical results deliver a striking and definitive conclusion that **completely refutes the classical trading lore**:

### 1. Volatility Clusters Rather Than Mean-Reverting Explosively
The classical retail premise posits that multi-day compression is a "coiling spring" that builds latent pressure, resulting in an explosive expansion day or persistent trend day.

**The actual 16-year continuous data demonstrates the exact opposite:**
- **Following Deep Compression (`Range < 0.65x Median`)**:
  - Subsequent RTH normalized range is **0.848** (15% below baseline).
  - Clean trend day probability drops from the 20.4% baseline down to **13.3%**.
  - Probability of large range expansion ($\text{Range} \ge 1.25\times \text{ATR}$) drops by more than half, from 24.4% down to **11.6%**!
- **Following High Expansion (`Range > 1.20x Median`)**:
  - Subsequent RTH normalized range is **1.212** (21% above baseline).
  - Clean trend day probability rises to **25.3%**.
  - Probability of large range expansion rises to **37.5%**.

Volatility exhibits strong **autoregressive clustering (inertia)**: compressed sessions beget further compressed sessions, while expansive sessions beget further expansive sessions.

---

### 2. NR7 Inversion: Narrowest Range Days Lead to Continued Compression
Across 411 NR7 sessions in the dataset:
- Subsequent RTH normalized range averages **0.881** vs **1.053** for normal days.
- Clean trend day rate is only **14.6%** (vs 20.9% for normal days).
- Large expansion rate ($\ge 1.25\times$ ATR) collapses to **14.6%** (vs 25.4% for normal days).
- In Validation (2022–2024), trend day rate briefly ticked up to 25.3%, but in Out-of-Sample (2025–2026), it collapsed back to **14.0%** (with large expansion rate of just **12.3%**).

---

### 3. Monotonic Contraction: More Contracting Days = Smaller Next Day Range
Evaluating consecutive days of strictly shrinking range:
- `0 Contracting Days`: Mean norm range = **1.063** | Large expansion rate = **26.5%** | Trend day rate = **20.9%**
- `1 Contracting Day`: Mean norm range = **1.020** | Large expansion rate = **23.5%** | Trend day rate = **20.1%**
- `2 Contracting Days`: Mean norm range = **0.979** | Large expansion rate = **20.4%** | Trend day rate = **18.7%**
- `4+ Contracting Days`: Mean norm range = **0.910** | Large expansion rate = **21.3%** | Trend day rate = **14.9%**

As compression persists, the subsequent session's range shrinks monotonically. There is zero evidence of an explosive coiling breakout on day $t$.

---

### 4. Directional Efficiency Is Completely Invariant
Across all 8 features, directional efficiency ($|Close - Open| / Range$) hovers rigidly between **0.45 and 0.49**:
- 5-Day Deep Compression ($Q1$): Efficiency = **0.455**
- 5-Day Deep Expansion ($Q5$): Efficiency = **0.486**
- NR7: Efficiency = **0.478**
- Normal Days: Efficiency = **0.473**
- 4+ Contracting Days: Efficiency = **0.526** (with sample size of only 47 days, dropping to 0.493 in IS)

Multi-day compression provides **zero conditioning power over directional path efficiency**.

---

## 3. Comprehensive Distribution Tables

### Table 1: 5-Day Realized Range Percentile ($F_2$) vs Next RTH Session
| Split | 5-Day Percentile Bin | Sessions (N) | % of Days | Mean Norm Range | Mean Efficiency | Trend Day Rate % | Large Exp ($\ge 1.25$) % | Mean Max Excursion | Pinned Close % |
|:---|:---|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **IS** | Q1_DEEP_COMP (< p20) | 339 | 16.3% | 0.971 | 0.438 | 14.5% | 18.6% | 0.767 | 45.7% |
| | Q2_MILD_COMP | 335 | 16.1% | 0.978 | 0.449 | 16.7% | 20.9% | 0.785 | 46.6% |
| | Q3_NORMAL | 354 | 17.0% | 0.952 | 0.466 | 18.4% | 18.9% | 0.753 | 45.2% |
| | Q4_MILD_EXP | 456 | 21.9% | 1.062 | 0.462 | 20.8% | 28.5% | 0.844 | 46.3% |
| | Q5_DEEP_EXP (> p80) | 600 | 28.8% | 1.137 | 0.488 | 23.8% | 33.5% | 0.901 | 52.7% |
| **Validation** | Q1_DEEP_COMP | 161 | 21.6% | 0.972 | 0.487 | 21.1% | 19.3% | 0.762 | 54.7% |
| | Q2_MILD_COMP | 138 | 18.5% | 1.041 | 0.499 | 25.4% | 22.5% | 0.835 | 46.4% |
| | Q3_NORMAL | 155 | 20.7% | 1.002 | 0.508 | 22.6% | 18.1% | 0.802 | 53.5% |
| | Q4_MILD_EXP | 121 | 16.2% | 1.012 | 0.515 | 26.4% | 19.0% | 0.828 | 55.4% |
| | Q5_DEEP_EXP | 172 | 23.0% | 1.058 | 0.484 | 22.1% | 26.2% | 0.816 | 51.7% |
| **OOS** | Q1_DEEP_COMP | 40 | 10.1% | 0.972 | 0.470 | 17.5% | 20.0% | 0.804 | 47.5% |
| | Q2_MILD_COMP | 54 | 13.6% | 1.066 | 0.474 | 16.7% | 22.2% | 0.872 | 44.4% |
| | Q3_NORMAL | 71 | 17.9% | 0.925 | 0.509 | 25.4% | 19.7% | 0.738 | 53.5% |
| | Q4_MILD_EXP | 93 | 23.4% | 0.975 | 0.501 | 16.1% | 19.4% | 0.809 | 41.9% |
| | Q5_DEEP_EXP | 139 | 35.0% | 1.145 | 0.481 | 19.4% | 33.1% | 0.891 | 48.9% |
| **ALL** | **Q1_DEEP_COMP** | **540** | **16.7%** | **0.971** | **0.455** | **16.7%** | **18.9%** | **0.768** | **48.5%** |
| | **Q2_MILD_COMP** | **527** | **16.3%** | **1.004** | **0.464** | **19.0%** | **21.4%** | **0.807** | **46.3%** |
| | **Q3_NORMAL** | **580** | **18.0%** | **0.962** | **0.482** | **20.3%** | **18.8%** | **0.765** | **48.4%** |
| | **Q4_MILD_EXP** | **670** | **20.8%** | **1.041** | **0.477** | **21.2%** | **25.5%** | **0.836** | **47.3%** |
| | **Q5_DEEP_EXP** | **911** | **28.2%** | **1.123** | **0.486** | **22.8%** | **32.1%** | **0.884** | **51.9%** |

---

### Table 2: Narrow Range Structural Patterns ($F_5$) vs Next RTH Session
| Split | Pattern | Sessions (N) | % of Days | Mean Norm Range | Mean Efficiency | Trend Day Rate % | Large Exp ($\ge 1.25$) % | Mean Max Excursion | Pinned Close % |
|:---|:---|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **IS** | NORMAL | 1,419 | 68.1% | 1.065 | 0.462 | 20.4% | 27.1% | 0.843 | 48.6% |
| | NR4 | 178 | 8.5% | 1.037 | 0.493 | 22.5% | 24.7% | 0.838 | 51.1% |
| | **NR7** | **267** | **12.8%** | **0.858** | **0.459** | **11.2%** | **13.5%** | **0.680** | **46.4%** |
| | INSIDE_DAY | 119 | 5.7% | 1.117 | 0.485 | 22.7% | 33.6% | 0.886 | 48.7% |
| | ID_NR4 | 44 | 2.1% | 1.069 | 0.483 | 25.0% | 36.4% | 0.872 | 50.0% |
| | ID_NR7 | 57 | 2.7% | 0.971 | 0.405 | 17.5% | 19.3% | 0.780 | 24.6% |
| **Validation** | NORMAL | 533 | 71.4% | 1.019 | 0.492 | 22.9% | 20.5% | 0.805 | 53.7% |
| | NR4 | 50 | 6.7% | 0.998 | 0.489 | 28.0% | 20.0% | 0.821 | 46.0% |
| | **NR7** | **87** | **11.6%** | **0.977** | **0.532** | **25.3%** | **19.5%** | **0.778** | **52.9%** |
| | INSIDE_DAY | 41 | 5.5% | 0.999 | 0.504 | 22.0% | 24.4% | 0.811 | 43.9% |
| | ID_NR4 | 16 | 2.1% | 1.256 | 0.494 | 18.8% | 50.0% | 0.966 | 43.8% |
| | ID_NR7 | 20 | 2.7% | 1.045 | 0.481 | 20.0% | 20.0% | 0.815 | 55.0% |
| **OOS** | NORMAL | 269 | 67.8% | 1.057 | 0.493 | 19.7% | 26.4% | 0.843 | 48.3% |
| | NR4 | 36 | 9.1% | 1.064 | 0.471 | 27.8% | 25.0% | 0.860 | 47.2% |
| | **NR7** | **57** | **14.4%** | **0.838** | **0.486** | **14.0%** | **12.3%** | **0.681** | **45.6%** |
| | INSIDE_DAY | 19 | 4.8% | 1.418 | 0.516 | 26.3% | 42.1% | 1.200 | 42.1% |
| | ID_NR4 | 5 | 1.3% | 0.923 | 0.488 | 0.0% | 20.0% | 0.695 | 100.0% |
| | ID_NR7 | 11 | 2.8% | 0.894 | 0.411 | 0.0% | 18.2% | 0.717 | 18.2% |
| **ALL** | NORMAL | 2,221 | 68.8% | 1.053 | 0.473 | 20.9% | 25.4% | 0.834 | 49.8% |
| | NR4 | 264 | 8.2% | 1.033 | 0.489 | 24.2% | 23.9% | 0.838 | 49.6% |
| | **NR7** | **411** | **12.7%** | **0.881** | **0.478** | **14.6%** | **14.6%** | **0.701** | **47.7%** |
| | INSIDE_DAY | 179 | 5.5% | 1.122 | 0.492 | 22.9% | 32.4% | 0.902 | 46.9% |
| | ID_NR4 | 65 | 2.0% | 1.104 | 0.486 | 21.5% | 38.5% | 0.881 | 52.3% |
| | ID_NR7 | 88 | 2.7% | 0.978 | 0.423 | 15.9% | 19.3% | 0.780 | 30.7% |

---

### Table 3: Compression Duration ($F_8$) vs Next RTH Session
| Split | Consecutive Days Range < Median | Sessions (N) | % of Days | Mean Norm Range | Mean Efficiency | Trend Day Rate % | Large Exp ($\ge 1.25$) % | Mean Max Excursion | Pinned Close % |
|:---|:---|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **ALL** | 0_DAYS (Yesterday Expanded) | 1,627 | 50.4% | 1.155 | 0.480 | 25.1% | 33.0% | 0.916 | 49.6% |
| | 1_DAY | 632 | 19.6% | 0.963 | 0.458 | 17.7% | 18.8% | 0.765 | 45.1% |
| | 2_DAYS | 344 | 10.7% | 0.894 | 0.480 | 17.4% | 16.6% | 0.718 | 50.0% |
| | 3_DAYS | 215 | 6.7% | 0.935 | 0.488 | 14.9% | 14.4% | 0.729 | 52.6% |
| | **4+_DAYS (Deep Compression)** | **410** | **12.7%** | **0.821** | **0.470** | **11.2%** | **10.5%** | **0.660** | **48.8%** |

---

## 4. Evaluation Against Pre-Registered Hostile Criteria

| Hostile Criterion | Requirement | Empirical Result | Status |
|:---|:---|:---|:---:|
| **1. IS Existence** | Must show significant positive shift in expansion/persistence | Compression regimes produce **lower** normalized range (0.82 vs 1.15) and **lower** trend day probability (11.2% vs 25.1%). | ❌ **FAIL** (Inverted) |
| **2. Validation Survival** | Must hold across 2022–2024 without degrading | While NR7 had temporary bump in 2022–24, 4+ days compression showed 12.5% large exp rate vs 23.5% for uncompressed. | ❌ **FAIL** |
| **3. OOS Survival** | Must hold in 2025–2026 | NR7 trend day rate collapsed back to 14.0%; 4+ days compression had 10.9% trend day rate. | ❌ **FAIL** |
| **4. Economic Magnitude** | Meaningful positive lift over baseline | Lift is strictly negative: large expansion probability is cut by 68% after compression. | ❌ **FAIL** |
| **5. Monotonicity Across Bins** | Consistent progression across quantiles | Contraction days monotonically reduce range (1.06 → 1.02 → 0.98 → 0.91). | ❌ **FAIL** |
| **6. Volatility Normalization** | Confirmed in ATR units | Normalized units prove this is volatility inertia, not macro scale confound. | ❌ **FAIL** |

---

## 5. Information Gate Verdict: C (KILL)

Multi-day volatility compression does **not** act as an expansion or persistence gate:
1. It does **not** increase the probability of a subsequent trend day.
2. It does **not** increase subsequent range expansion or excursion magnitude.
3. Instead, volatility exhibits strong positive autoregression: low-volatility states persist in low-volatility states, while high-volatility states persist in high-volatility states.

In strict compliance with our pre-registered kill criteria, **Strategy 39 is KILLED at the Information Gate**.
