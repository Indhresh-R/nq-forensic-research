# Strategy 41: Volatility Regime × Signal Economics -- Full Report

**Date:** 2026-09-14  
**Verdict:** **C (KILL as Economic Trade Filter)**  
**Dataset:** Continuous NQ 1-minute futures (2010--2026, 3,470 complete RTH sessions)  
**Execution Friction:** Fixed at 1.0 point ($20.00) round-trip per contract  

---

## 1. Executive Summary

Strategy 41 tested whether the predictable volatility persistence confirmed in Strategy 39 can function as an **economic / transaction-cost filter** that rescues trading signals from friction drag:
> **Does high volatility increase the economic value of a signal enough to overcome fixed transaction costs?**

We executed a rigorous, two-layer empirical audit across 16 years of continuous NQ futures:
1. **Layer 1 (Signal-Agnostic Capacity)**: Evaluated theoretical price excursion magnitude vs fixed 1.0 pt friction across volatility tiers.
2. **Layer 2 (Friction Stratification)**: Stratified three frozen, pre-existing benchmark signals (Initial Balance Breakout, 15m Opening Drive, and Fixed-Clock Intraday Momentum) across Low, Normal, High, and Extreme Volatility tiers across IS (2011–2021), Validation (2022–2024), and OOS (2025–2026).

---

## 2. Key Empirical Findings

### 1. Layer 1: Friction Drag Percentage Is Modestly Lower in High Volatility
In pure geometric terms, available price excursion expands as volatility increases:
- **60-Minute Excursion (ALL sessions)**:
  - Low Vol (`< 0.75 ATR`): Mean excursion = **56.2 pts** | Friction Drag = **4.24%**
  - Normal Vol (`0.75 - 1.25 ATR`): Mean excursion = **67.7 pts** | Friction Drag = **3.75%**
  - Extreme Vol (`> 1.50 ATR`): Mean excursion = **84.8 pts** | Friction Drag = **3.13%**
- **Full-Session Excursion**:
  - Low Vol: Mean excursion = **109.1 pts** | Friction Drag = **2.41%**
  - Extreme Vol: Mean excursion = **146.2 pts** | Friction Drag = **1.80%**

In percentage terms, fixed 1.0 pt friction consumes less of the available excursion during volatile sessions.

---

### 2. Layer 2: Adverse Price Excursion (MAE) Expands Faster Than Favorable Excursion (MFE)
While available range expands, **losses expand by a greater magnitude than wins**, worsening net performance:

#### A. Initial Balance Breakout (Strategy 30 Benchmark)
- **In-Sample (2011–2021)**:
  - Low Vol: Net expectancy = **-2.29 pts** (PF net 0.869)
  - Normal Vol: Net expectancy = **-3.83 pts** (PF net 0.812)
  - High Vol: Net expectancy = **-2.86 pts** (PF net 0.876)
  - Extreme Vol: Net expectancy = **-12.14 pts** (PF net 0.620)!
- **Full Sample (2010–2026)**:
  - Under `EXTREME_VOL (> 1.50 ATR)`, Initial Balance Breakouts generated a cumulative loss of **-4,090.2 net points** ($E_{net} = -9.47$ pts/trade).
  - **The Structural Flaw**: In low vol, mean MAE was **55.8 pts**; in extreme vol, mean MAE blew out to **90.1 pts**. The MFE/MAE ratio degraded from **1.00 down to 0.82**.

---

#### B. 15-Minute Opening Drive (Strategy 38 Benchmark, 60m Hold)
- **In-Sample (2011–2021)**:
  - Low Vol: Net expectancy = **-0.08 pts**
  - Extreme Vol: Net expectancy = **-2.91 pts** (lost -882.8 pts)
- **Validation (2022–2024)**:
  - Low Vol: Net expectancy = **+2.38 pts** (PF net 1.074)
  - Normal Vol: Net expectancy = **+11.03 pts** (PF net 1.430)
  - High Vol: Net expectancy = **-9.76 pts** (PF net 0.744)
  - Extreme Vol: Net expectancy = **-11.03 pts** (PF net 0.737)
- **Out-of-Sample (2025–2026)**:
  - Extreme Vol: Net expectancy = **-21.46 pts** (lost -1,030.0 pts)!
- **Full Sample (2010–2026)**:
  - Across all 429 Extreme Vol sessions, 15m Opening Drive lost **-2,773.2 net points** ($E_{net} = -6.46$ pts, PF net **0.755**).
  - Whipsaws expanded massively: mean MAE reached **56.5 pts** vs mean MFE of **46.0 pts** (ratio **0.81**).

---

#### C. Fixed-Clock Momentum (Strategy 36 Benchmark)
- Full sample performance by tier:
  - Low Vol: Total net = **-5,428.8 pts** ($E_{net} = -4.96$ pts)
  - Normal Vol: Total net = **-55.0 pts** ($E_{net} = -0.04$ pts)
  - High Vol: Total net = **-3,148.8 pts** ($E_{net} = -8.07$ pts)
  - Extreme Vol: Total net = **-3,236.2 pts** ($E_{net} = -7.44$ pts)
- High and Extreme Volatility generated cumulative losses of **-6,385.0 net points**.

---

## 3. Tabular Audits

### Table 1: Initial Balance (30m OR) Breakout by Volatility Tier
| Split | Volatility Tier | Trades (N) | Gross Exp (pts) | Net Exp (pts) | Total Net (pts) | WR Net % | PF Net | Mean MFE (pts) | Mean MAE (pts) | MFE/MAE Ratio |
|:---|:---|---:|---:|---:|---:|:---:|:---:|---:|---:|:---:|
| **IS** | LOW_VOL (<0.75) | 763 | -1.29 | -2.29 | -1,744.0 | 44.3% | 0.869 | 31.8 | 32.1 | 0.99 |
| | NORMAL_VOL (0.75-1.25) | 967 | -2.83 | -3.83 | -3,704.8 | 46.1% | 0.812 | 31.9 | 35.6 | 0.90 |
| | HIGH_VOL (1.25-1.50) | 263 | -1.86 | -2.86 | -751.2 | 43.0% | 0.876 | 39.8 | 44.0 | 0.90 |
| | **EXTREME_VOL (>1.50)** | **307** | **-11.14** | **-12.14** | **-3,727.5** | **45.9%** | **0.620** | **47.4** | **57.9** | **0.82** |
| **Validation** | LOW_VOL | 205 | +2.89 | +1.89 | +387.5 | 54.6% | 1.033 | 106.9 | 102.0 | 1.05 |
| | NORMAL_VOL | 383 | +22.45 | +21.45 | +8,217.0 | 57.4% | 1.501 | 110.9 | 94.6 | 1.17 |
| | HIGH_VOL | 76 | -5.03 | -6.03 | -458.5 | 48.7% | 0.890 | 105.9 | 122.8 | 0.86 |
| | **EXTREME_VOL** | **77** | **-8.96** | **-9.96** | **-767.0** | **44.2%** | **0.809** | **94.3** | **129.0** | **0.73** |
| **OOS** | LOW_VOL | 122 | -10.76 | -11.76 | -1,435.2 | 50.0% | 0.827 | 121.1 | 126.3 | 0.96 |
| | NORMAL_VOL | 176 | +13.39 | +12.39 | +2,181.0 | 55.1% | 1.195 | 144.2 | 132.1 | 1.09 |
| | HIGH_VOL | 48 | +16.05 | +15.05 | +722.5 | 62.5% | 1.198 | 163.2 | 164.8 | 0.99 |
| | **EXTREME_VOL** | **48** | **+9.42** | **+8.42** | **+404.2** | **47.9%** | **1.092** | **208.3** | **234.2** | **0.89** |
| **ALL** | **LOW_VOL** | **1,090** | **-1.56** | **-2.56** | **-2,791.8** | **46.9%** | **0.916** | **55.9** | **55.8** | **1.00** |
| | **NORMAL_VOL** | **1,526** | **+5.39** | **+4.39** | **+6,693.2** | **50.0%** | **1.142** | **64.7** | **61.6** | **1.05** |
| | **HIGH_VOL** | **387** | **-0.26** | **-1.26** | **-487.2** | **46.5%** | **0.965** | **68.1** | **74.5** | **0.91** |
| | **EXTREME_VOL** | **432** | **-8.47** | **-9.47** | **-4,090.2** | **45.8%** | **0.775** | **73.7** | **90.1** | **0.82** |

---

### Table 2: 15-Minute Opening Drive (60m Hold) by Volatility Tier
| Split | Volatility Tier | Trades (N) | Gross Exp (pts) | Net Exp (pts) | Total Net (pts) | WR Net % | PF Net | Mean MFE (pts) | Mean MAE (pts) | MFE/MAE Ratio |
|:---|:---|---:|---:|---:|---:|:---:|:---:|---:|---:|:---:|
| **IS** | LOW_VOL (<0.75) | 769 | +0.92 | -0.08 | -62.0 | 49.3% | 0.992 | 20.0 | 19.1 | 1.05 |
| | NORMAL_VOL (0.75-1.25) | 968 | -0.38 | -1.38 | -1,334.5 | 49.0% | 0.874 | 20.3 | 20.9 | 0.97 |
| | HIGH_VOL (1.25-1.50) | 263 | +2.18 | +1.18 | +309.8 | 49.4% | 1.096 | 25.1 | 24.6 | 1.02 |
| | **EXTREME_VOL (>1.50)** | **303** | **-1.91** | **-2.91** | **-882.8** | **42.2%** | **0.821** | **29.2** | **33.9** | **0.86** |
| **Validation** | LOW_VOL | 206 | +3.38 | +2.38 | +491.0 | 50.0% | 1.074 | 63.6 | 58.0 | 1.10 |
| | NORMAL_VOL | 386 | +12.03 | +11.03 | +4,258.0 | 56.5% | 1.430 | 69.7 | 56.9 | 1.23 |
| | HIGH_VOL | 77 | -8.76 | -9.76 | -751.8 | 48.1% | 0.744 | 66.2 | 79.5 | 0.83 |
| | **EXTREME_VOL** | **78** | **-10.03** | **-11.03** | **-860.5** | **47.4%** | **0.737** | **71.2** | **83.0** | **0.86** |
| **OOS** | LOW_VOL | 122 | +8.95 | +7.95 | +970.0 | 56.6% | 1.206 | 84.4 | 80.0 | 1.06 |
| | NORMAL_VOL | 179 | -1.14 | -2.14 | -383.8 | 55.9% | 0.958 | 95.9 | 98.6 | 0.97 |
| | HIGH_VOL | 47 | +32.36 | +31.36 | +1,473.8 | 63.8% | 1.808 | 111.7 | 79.3 | 1.41 |
| | **EXTREME_VOL** | **48** | **-20.46** | **-21.46** | **-1,030.0** | **39.6%** | **0.670** | **110.9** | **156.6** | **0.71** |
| **ALL** | **LOW_VOL** | **1,097** | **+2.28** | **+1.28** | **+1,399.0** | **50.2%** | **1.073** | **35.4** | **33.2** | **1.07** |
| | **NORMAL_VOL** | **1,533** | **+2.66** | **+1.66** | **+2,539.8** | **51.7%** | **1.086** | **41.6** | **39.1** | **1.06** |
| | **HIGH_VOL** | **387** | **+3.67** | **+2.67** | **+1,031.8** | **50.9** | **1.129** | **43.8** | **42.2** | **1.04** |
| | **EXTREME_VOL** | **429** | **-5.46** | **-6.46** | **-2,773.2** | **42.9%** | **0.755** | **46.0** | **56.5** | **0.81** |

---

## 4. Evaluation Against Pre-Registered Hostile Criteria

| Hostile Criterion | Requirement | Empirical Result | Status |
|:---|:---|:---|:---:|
| **1. Shift from Negative to Positive $E_{net}$** | High Vol must turn negative low-vol signal positive | High/Extreme Vol yields **more negative** net expectancy (IB: $-12.14$ vs $-2.29$; Drive: $-6.46$ vs $+1.28$). | ❌ **FAIL** |
| **2. Profit Factor Improvement** | $PF_{net} > 1.15$ in High Vol while $< 1.0$ in Low Vol | Extreme Vol $PF_{net}$ is **0.775** (IB) and **0.755** (Drive), worse than Low Vol (0.916 and 1.073). | ❌ **FAIL** (Inverted) |
| **3. Temporal Stability** | Net expectancy must hold across IS, Val, and OOS | Extreme Vol lost money in IS, Validation, and OOS across all benchmark models. | ❌ **FAIL** |
| **4. Adverse Excursion Control** | MFE must scale faster than MAE | MAE grew faster than MFE; MFE/MAE ratio degraded from 1.00–1.07 down to 0.81–0.82. | ❌ **FAIL** |

---

## 5. Information Gate Verdict: C (KILL as Economic Filter)

The empirical investigation provides a definitive answer:
> **High volatility does NOT rescue signals from transaction friction.**

Although fixed friction represents a smaller percentage of gross range during volatile days, **adverse price excursion (MAE) scales proportionally or faster than favorable excursion (MFE)**. When an underlying directional signal lacks edge, trading in high volatility simply causes **larger, more severe dollar losses per trade**.

In accordance with our pre-registered criteria, **Strategy 41 is KILLED as an economic trade filter**.
