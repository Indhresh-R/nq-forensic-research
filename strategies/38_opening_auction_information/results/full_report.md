# Strategy 38: Opening Auction Information → Remaining Session Persistence -- Full Report

**Date:** 2026-09-14  
**Verdict:** **C (KILL at Information Gate)**  
**Dataset:** Continuous NQ 1-minute futures (2010--2026, 3,466 complete RTH sessions)  
**Observation Checkpoints Evaluated:** 5m (09:35), 10m (09:40), and 15m (09:45)  

---

## 1. Executive Summary

Strategy 38 investigated the opening auction **information question**:
> **After the market opens, does the first 5 to 15 minutes of actual RTH price and volume behavior reveal whether the remaining session will become a persistent trend or two-sided rotational chop?**

We evaluated 4 core structural features across 3 opening checkpoints ($T_5, T_{10}, T_{15}$):
1. **Opening Range Ratio ($F_1$)**: $OR_T / \text{ATR}_{20}$ (Expanded, Normal, Compressed).
2. **Early Path Directional Efficiency ($F_2$)**: $|Close_T - Open_{09:30}| / OR_T$ (High $\ge 0.70$, Moderate, Low $< 0.35$).
3. **Early Volume Abnormality ($F_3$)**: Relative volume vs 20-day trailing clock mean.
4. **Early Displacement Sign ($F_4$)**: Bull Drive vs Bear Drive.

We measured the subsequent price action strictly from $T+1$ through the $15:55$ close ($Y_1$ remaining return, $Y_2$ remaining efficiency, $Y_3$ follow-through rate, $Y_4$ clean trend-day probability).

---

## 2. Definitive Empirical Findings

### 1. Early Path Efficiency Does NOT Condition Remaining-Session Persistence
A common chartist hypothesis is that an aggressive, high-efficiency opening drive signals institutional conviction that leads to a persistent trend day, whereas an early chop day stays choppy.

**The empirical data flatly rejects this claim:**
- At the 15-minute checkpoint across 3,466 sessions (ALL, 2010–2026):
  - **High Early Efficiency ($\ge 0.70$)**: Remaining Session Efficiency = **0.475** | Trend Day Rate = **27.2%**
  - **Moderate Early Efficiency ($0.35–0.70$)**: Remaining Session Efficiency = **0.466** | Trend Day Rate = **25.6%**
  - **Low Early Efficiency ($< 0.35$, Chop Open)**: Remaining Session Efficiency = **0.464** | Trend Day Rate = **25.2%**
  - **Unconditional Baseline**: Remaining Session Efficiency = **0.467** | Trend Day Rate = **25.9%**

The difference in remaining-session efficiency between a high-conviction opening drive and a two-sided opening chop is **less than 0.011** ($0.475$ vs $0.464$). The lift in clean trend-day likelihood is an insignificant **+1.3 percentage points** above baseline (27.2% vs 25.9%). The opening auction reveals virtually nothing about whether the remainder of the session will be trending or choppy.

---

### 2. Opening Range Expansion Does NOT Condition Persistence
Comparing sessions with large opening range expansions against compressed opening ranges:
- **Expanded Opening Range (> p66)**: Remaining Session Efficiency = **0.474** | Trend Day Rate = **27.5%**
- **Compressed Opening Range (< p33)**: Remaining Session Efficiency = **0.472** | Trend Day Rate = **24.2%**
- **Unconditional Baseline**: Remaining Session Efficiency = **0.467** | Trend Day Rate = **25.9%**

The directional efficiency of the remaining session after an expanded opening range is virtually identical to that of a compressed opening range (difference of **0.002**).

---

### 3. Early Drive Direction Yields Zero Net Follow-Through Alpha
- Directional follow-through rate:
  - **Bull Drive**: Follow-through rate = **57.3%**
  - **Bear Drive**: Follow-through rate = **46.7%**
  - **Overall Average**: **52.0%**
- This asymmetry is completely accounted for by the passive secular upward drift of NQ documented in Strategy 36, **not** by opening auction predictive power.
- Furthermore, for 15-minute High Efficiency open drives, the average gross remaining return across the full sample is only **+0.77 points** (IS $+1.28$, Val $-10.91$, OOS $+19.46$). After paying the standard 1.0 point round-trip friction, the net return is **negative (-0.23 pts)**!

---

## 3. Comprehensive Distribution Tables (15-Minute Checkpoint)

### Table 1: Early Path Efficiency ($F_2$) vs Remaining Session
| Split | Early Efficiency Bin | Sessions (N) | % of Days | Remaining Efficiency | Trend Day Rate % | Follow-Through % | Mean Remaining Return (pts) |
|:---|:---|---:|---:|:---:|:---:|:---:|---:|
| **IS** | HIGH_EFF ($\ge 0.70$) | 566 | 24.4% | 0.463 | 21.0% | 53.5% | +1.28 |
| | MODERATE_EFF | 948 | 40.8% | 0.457 | 20.0% | 50.7% | +0.94 |
| | LOW_EFF ($< 0.35$) | 808 | 34.8% | 0.460 | 19.1% | 49.2% | +3.06 |
| **Validation** | HIGH_EFF | 191 | 25.6% | 0.515 | 41.9% | 54.2% | **-10.91** |
| | MODERATE_EFF | 293 | 39.2% | 0.502 | 39.9% | 52.1% | +22.25 |
| | LOW_EFF | 263 | 35.2% | 0.471 | 38.0% | 57.0% | -15.27 |
| **OOS** | HIGH_EFF | 104 | 26.2% | 0.464 | 33.7% | 59.6% | +19.46 |
| | MODERATE_EFF | 154 | 38.8% | 0.451 | 32.5% | 58.4% | +22.26 |
| | LOW_EFF | 139 | 35.0% | 0.479 | 36.7 | 51.4% | -18.34 |
| **ALL** | **HIGH_EFF** | **861** | **24.8%** | **0.475** | **27.2%** | **54.4%** | **+0.77** |
| | **MODERATE_EFF** | **1,395** | **40.2%** | **0.466** | **25.6%** | **51.8%** | **+7.77** |
| | **LOW_EFF** | **1,210** | **34.9%** | **0.464** | **25.2%** | **51.2%** | **-3.39** |

---

### Table 2: Opening Range Ratio ($F_1$) vs Remaining Session
| Split | OR Bin | Sessions (N) | % of Days | Remaining Efficiency | Trend Day Rate % | Follow-Through % | Mean Remaining Return (pts) |
|:---|:---|---:|---:|:---:|:---:|:---:|---:|
| **IS** | EXPANDED_OR (> p66) | 776 | 33.4% | 0.469 | 23.6% | 51.2% | +0.58 |
| | NORMAL_OR | 773 | 33.3% | 0.442 | 18.1% | 51.8% | +2.26 |
| | COMPRESSED_OR (< p33) | 773 | 33.3% | 0.467 | 18.1% | 49.6% | +2.45 |
| **Validation** | EXPANDED_OR | 201 | 26.9% | 0.501 | 39.3% | 50.3% | **-7.06** |
| | NORMAL_OR | 271 | 36.3% | 0.494 | 43.9% | 55.4% | +2.09 |
| | COMPRESSED_OR | 275 | 36.8% | 0.489 | 36.0% | 56.4% | +4.63 |
| **OOS** | EXPANDED_OR | 136 | 34.3% | 0.460 | 32.4% | 58.1% | +47.89 |
| | NORMAL_OR | 134 | 33.8% | 0.467 | 35.1% | 54.1% | -45.22 |
| | COMPRESSED_OR | 127 | 32.0% | 0.466 | 35.4 | 56.7% | +19.28 |
| **ALL** | **EXPANDED_OR** | **1,113** | **32.1%** | **0.474** | **27.5%** | **51.9%** | **+4.98** |
| | **NORMAL_OR** | **1,178** | **34.0%** | **0.457** | **26.0%** | **52.9%** | **-3.18** |
| | **COMPRESSED_OR** | **1,175** | **33.9%** | **0.472** | **24.2%** | **52.0%** | **+4.78** |

---

## 4. Information Gate Verdict: C (KILL)

The opening auction does **not** reveal whether the remaining session will become a persistent trend or two-sided rotational chop:
1. Remaining session directional efficiency is invariant across early efficiency and range bins ($0.46$ to $0.48$).
2. Clean trend-day probability is practically unchanged (+1.3 pp lift for high efficiency).
3. Gross remaining return after an aggressive 15m drive (+0.77 pts) is entirely consumed by 1.0 pt round-trip trading friction.

In accordance with our pre-registered kill criteria, **Strategy 38 is killed at the Information Gate**.
