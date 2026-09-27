# Strategy 40: Volatility Persistence → Directional Distribution -- Full Report

**Date:** 2026-09-14  
**Verdict:** **C (Scientific Boundary Established: Volatility Is Predictable, Direction Is NOT)**  
**Dataset:** Continuous NQ 1-minute futures (2010--2026, 3,470 complete RTH sessions)  
**Protocol:** Information-First, Strictly Decoupled Volatility Magnitude vs Directional Polarity  

---

## 1. Executive Summary

Strategy 39 established that **volatility exhibits powerful persistence (clustering)** in continuous NQ futures: high-volatility sessions precede high-volatility sessions ($1.21\times$ baseline range), and low-volatility sessions precede low-volatility sessions ($0.85\times$ baseline range).

Strategy 40 investigated the critical following question:
> **When NQ enters a high-volatility regime, does that regime systematically alter the conditional distribution of direction, directional polarity, or continuation of prior momentum?**

We evaluated 3,470 complete RTH sessions across 16 years of continuous NQ 1-minute data (2010–2026), testing:
1. Directional continuation ($P(\text{same sign})$) across volatility tiers.
2. Large move asymmetry ($P(\text{Large Up Move}) - P(\text{Large Down Move})$).
3. Upside vs downside excursion reach.
4. Volatility $\times$ Direction interactions (momentum vs mean reversion).

---

## 2. Key Empirical Findings: The Symmetric Volatility Expansion Reality

The empirical data establishes a definitive, foundational scientific truth:

### 1. Directional Continuation Is a 50/50 Coin Flip Across All Volatility Regimes
Across the entire 16-year sample:
- Following **Low Volatility (`< 0.75 ATR`)**: Continuation rate = **47.9%**
- Following **Normal Volatility (`0.75 - 1.25 ATR`)**: Continuation rate = **49.8%**
- Following **High Volatility (`1.25 - 1.50 ATR`)**: Continuation rate = **45.3%**
- Following **Extreme Volatility (`> 1.50 ATR`)**: Continuation rate = **44.8%**

High volatility does **not** create directional momentum ($P > 53\%$). If anything, continuation drops slightly to 45% (a slight mean-reverting drag), but it is statistically and economically indistinguishable from a two-sided random process.

---

### 2. Tail Variance Expands Symmetrically
A common chartist hypothesis is that entering high volatility skews the probability distribution toward large unilateral moves (e.g. violent trend breaks in a single direction).

**The actual data shows near-perfect symmetry:**
- Under **Extreme Volatility (`> 1.50 ATR`, N=435 sessions)**:
  - Probability of Large Up Move ($\ge 1.0\times$ ATR): **9.9%**
  - Probability of Large Down Move ($\le -1.0\times$ ATR): **9.4%**
  - **Tail Asymmetry Spread**: **+0.5%**
- Mean Normalized Excursions:
  - Mean Upside Excursion: **0.653** ATR
  - Mean Downside Excursion: **0.651** ATR
  - **Excursion Spread**: **+0.002** ATR

Variance expands massively, but it expands **symmetrically in both directions**. High-volatility states increase the *magnitude* of the daily swings without biasing *which way* the market travels.

---

### 3. Volatility $\times$ Direction Interaction: Violent Temporal Sign Flips
Examining sessions following high-volatility up days (`HIGH_VOL_UP`):
- **In-Sample (2010–2021)**: Return = **-10.51 pts** (norm return -0.039), continuation rate = **53.5%**.
- **Validation (2022–2024)**: Return = **-18.17 pts** (norm return -0.069), continuation rate = **50.8%**.
- **OOS 2025**: Return = **-151.19 pts** (norm return -0.400), continuation rate = **35.0%** (reversed 65% of the time).
- **OOS 2026**: Return = **+132.20 pts** (norm return +0.295), continuation rate = **73.3%** (followed through 73% of the time).

The directional polarity of high-volatility up days flips violently from **-151 points** in 2025 to **+132 points** in 2026, demonstrating that directional follow-through after high volatility is unstable market noise.

---

### 4. Post-Drop Bounces Are Simply Macro Equity Beta
Following high-volatility down days (`HIGH_VOL_DOWN`), the next day closes positive **60.5%** of the time across the full sample (IS 58.6%, Val 62.5%, OOS 67.7%).

However, this is not an active alpha anomaly:
- Following **mild down days**, the up-day rate is **57.3%**.
- The unconditional up-day rate of continuous NQ across the dataset is ~54.5%.
- As established in Strategy 36, equity index drift is driven by passive macro risk premium; active attempts to trade post-drop bounces bleed transaction friction and fail symmetric barrier tests.

---

## 3. Comprehensive Distribution Tables

### Table 1: Prior Volatility Regime ($V_{t-1}$) vs Next RTH Directional Distribution
| Split | Prior Vol Regime | Sessions (N) | % Days | Mean Ret (pts) | Up Day % | Continuation % | Large Up % | Large Down % | Tail Spread % | Mean Up Exc | Mean Down Exc | Exc Spread | Bull Trend % | Bear Trend % |
|:---|:---|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **IS** | LOW_VOL (<0.75) | 775 | 33.3% | +0.63 | 50.3% | 47.4% | 3.1% | 4.6% | -1.5% | 0.398 | 0.466 | -0.067 | 6.2% | 6.2% |
| | NORMAL_VOL (0.75-1.25) | 976 | 42.0% | +4.35 | 56.5% | 46.7% | 6.9% | 7.9% | -1.0% | 0.498 | 0.534 | -0.036 | 11.4% | 10.3% |
| | HIGH_VOL (1.25-1.50) | 266 | 11.4% | -3.31 | 54.9% | 47.7% | 4.9% | 10.9% | -6.0% | 0.522 | 0.639 | -0.117 | 12.0% | 13.9% |
| | EXTREME_VOL (>1.50) | 309 | 13.3% | +4.17 | 57.6% | 46.0% | 12.0% | 10.7% | +1.3% | 0.678 | 0.683 | -0.005 | 17.2% | 10.7% |
| **Validation** | LOW_VOL | 206 | 27.6% | -10.49 | 50.0% | 46.1% | 4.9% | 8.7% | -3.9% | 0.446 | 0.544 | -0.098 | 8.7% | 15.0% |
| | NORMAL_VOL | 386 | 51.7% | +0.35 | 53.4% | 54.9% | 6.2% | 7.3% | -1.0% | 0.505 | 0.517 | -0.012 | 12.7% | 11.9% |
| | HIGH_VOL | 77 | 10.3% | +38.66 | 61.0% | 39.0% | 5.2% | 5.2% | 0.0% | 0.553 | 0.484 | +0.069 | 10.4% | 7.8% |
| | EXTREME_VOL | 78 | 10.4% | -13.90 | 55.1% | 46.2% | 1.3% | 6.4% | -5.1% | 0.494 | 0.558 | -0.064 | 7.7% | 12.8% |
| **OOS** | LOW_VOL | 122 | 30.7% | +0.15 | 54.9% | 54.1% | 0.8% | 3.3% | -2.5% | 0.372 | 0.470 | -0.098 | 5.7% | 6.6% |
| | NORMAL_VOL | 179 | 45.1% | -21.80 | 52.0% | 55.3% | 4.5% | 7.8% | -3.4% | 0.433 | 0.593 | -0.160 | 8.4% | 11.2% |
| | HIGH_VOL | 48 | 12.1% | +52.18 | 64.6% | 41.7% | 14.6% | 10.4% | +4.2% | 0.635 | 0.642 | -0.008 | 16.7% | 14.6% |
| | EXTREME_VOL | 48 | 12.1% | +74.90 | 60.4% | 35.4% | 10.4% | 6.2% | +4.2% | 0.748 | 0.594 | +0.154 | 16.7% | 6.2% |
| **ALL** | **LOW_VOL** | **1,103** | **31.8%** | **-1.50** | **50.8%** | **47.9%** | **3.2%** | **5.3%** | **-2.1%** | **0.404** | **0.481** | **-0.077** | **6.6%** | **7.9%** |
| | **NORMAL_VOL** | **1,541** | **44.4%** | **+0.31** | **55.2%** | **49.8%** | **6.4%** | **7.7%** | **-1.3%** | **0.492** | **0.537** | **-0.045** | **11.4%** | **10.8%** |
| | **HIGH_VOL** | **391** | **11.3%** | **+11.77** | **57.3%** | **45.3%** | **6.1%** | **9.7%** | **-3.6%** | **0.542** | **0.609** | **-0.067** | **12.3%** | **12.8%** |
| | **EXTREME_VOL** | **435** | **12.5%** | **+8.74** | **57.5%** | **44.8%** | **9.9%** | **9.4%** | **+0.5%** | **0.653** | **0.651** | **+0.002** | **15.4%** | **10.6%** |

---

### Table 2: Volatility $\times$ Direction Interaction ($VD_{t-1}$) vs Next RTH
| Split | Interaction Bin | Sessions (N) | % Days | Mean Ret (pts) | Up Day % | Continuation % | Large Up % | Large Down % | Tail Spread % | Mean Up Exc | Mean Down Exc | Bull Trend % | Bear Trend % |
|:---|:---|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **IS** | HIGH_VOL_DOWN | 321 | 13.8% | +9.59 | 58.6% | 41.4% | 10.6% | 9.7% | +0.9% | 0.673 | 0.682 | 18.1% | 11.2% |
| | HIGH_VOL_UP | 254 | 10.9% | -10.51 | 53.5% | 53.5% | 6.3% | 12.2% | -5.9% | 0.521 | 0.638 | 10.6% | 13.4% |
| | LOW_VOL_DOWN | 322 | 13.8% | +3.61 | 52.5% | 45.3% | 5.3% | 5.6% | -0.3% | 0.440 | 0.463 | 8.1% | 5.9% |
| | LOW_VOL_UP | 453 | 19.5% | -1.49 | 48.8% | 48.8% | 1.5% | 4.0% | -2.4% | 0.369 | 0.467 | 4.9% | 6.4% |
| **Validation** | HIGH_VOL_DOWN | 96 | 12.9% | +30.88 | 62.5% | 37.5% | 2.1% | 4.2% | -2.1% | 0.573 | 0.496 | 7.3% | 9.4% |
| | HIGH_VOL_UP | 59 | 7.9% | -18.17 | 50.8% | 50.8% | 5.1% | 8.5% | -3.4% | 0.443 | 0.561 | 11.9% | 11.9% |
| | LOW_VOL_DOWN | 86 | 11.5% | +6.51 | 54.7% | 45.3% | 5.8% | 7.0% | -1.2% | 0.486 | 0.525 | 11.6% | 12.8% |
| | LOW_VOL_UP | 120 | 16.1% | -22.68 | 46.7% | 46.7% | 4.2% | 10.0% | -5.8% | 0.417 | 0.558 | 6.7% | 16.7% |
| **OOS** | HIGH_VOL_DOWN | 62 | 15.6% | +110.02 | 67.7% | 32.3% | 16.1% | 4.8% | +11.3% | 0.768 | 0.565 | 19.4% | 9.7% |
| | HIGH_VOL_UP | 35 | 8.8% | -29.74 | 51.4% | 51.4% | 5.7% | 14.3% | -8.6% | 0.536 | 0.724 | 11.4% | 14.3% |
| | LOW_VOL_DOWN | 37 | 9.3% | -21.94 | 51.4% | 48.6% | 0.0% | 2.7% | -2.7% | 0.375 | 0.543 | 5.4% | 8.1% |
| | LOW_VOL_UP | 85 | 21.4% | +9.77 | 56.5% | 56.5% | 1.2% | 3.5% | -2.4% | 0.370 | 0.438 | 5.9% | 5.9% |
| **ALL** | **HIGH_VOL_DOWN** | **479** | **13.8%** | **+26.86** | **60.5%** | **39.5%** | **9.6%** | **7.9%** | **+1.7%** | **0.665** | **0.629** | **16.1%** | **10.6%** |
| | **HIGH_VOL_UP** | **348** | **10.0%** | **-13.74** | **52.9%** | **52.9%** | **6.0%** | **11.8%** | **-5.7%** | **0.509** | **0.634** | **10.9%** | **13.2%** |
| | **LOW_VOL_DOWN** | **445** | **12.8%** | **+2.05** | **52.8%** | **45.6%** | **4.9%** | **5.6%** | **-0.7%** | **0.443** | **0.482** | **8.5%** | **7.4%** |
| | **LOW_VOL_UP** | **658** | **19.0%** | **-3.90** | **49.4%** | **49.4%** | **2.0%** | **5.0%** | **-3.0%** | **0.378** | **0.480** | **5.3%** | **8.2%** |
| | **NORMAL_VOL** | **1,540** | **44.4%** | **+0.52** | **55.2%** | **49.7%** | **6.4%** | **7.7%** | **-1.3%** | **0.492** | **0.536** | **11.4%** | **10.8%** |

---

## 4. Synthesis & Scientific Boundary

The empirical evidence directly answers the research inquiry:

| Core Question | Empirical Result | Scientific Conclusion |
|:---|:---|:---|
| **Does high volatility predict direction?** | Continuation rate is 45.3% (high vol) and 44.8% (extreme vol). | **NO**. Prior direction does not persist into the next session. |
| **Does variance expand asymmetrically?** | Under extreme vol, Large Up is 9.9% vs Large Down 9.4% (+0.5% spread). | **NO**. Variance expands with near-perfect symmetry. |
| **Is excursion biased?** | Upside excursion is 0.653 ATR vs Downside excursion 0.651 ATR. | **NO**. Reach expands equally to both extremes. |
| **Is directional momentum stable?** | `HIGH_VOL_UP` was -151 pts in 2025, but +132 pts in 2026. | **NO**. Directional follow-through is unstable noise. |

### The Core Boundary:
> **Volatility is predictable; Direction is NOT.**
> The market provides a statistically robust, causal **WHEN** (volatility clustering), but provides **ZERO UNCONDITIONAL "WHICH WAY"**.

In accordance with our pre-registered hostile criteria, **Strategy 40 is KILLED as a directional trading signal**, establishing this foundational boundary for all subsequent research.
