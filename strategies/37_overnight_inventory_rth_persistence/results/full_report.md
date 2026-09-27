# Strategy 37: Overnight Inventory → RTH Directional Persistence -- Full Report

**Date:** 2026-09-14  
**Verdict:** **C (KILL at Information Gate)**  
**Dataset:** Continuous NQ 1-minute futures (2010--2026, 3,470 complete paired Overnight-RTH sessions)  

---

## 1. Executive Summary

Strategy 37 investigated the pre-market **information question**:
> **Does structural overnight/Globex inventory (known strictly at $t \le 09:29$ ET) contain statistically robust conditioning information that alters subsequent RTH directional persistence?**

We evaluated 5 structural overnight features across 16 years of continuous data:
1. **Gap Size Norm ($G_1$)**: Normalized gap relative to 20-day ATR.
2. **Overnight Range Ratio ($G_2$)**: Compression vs expansion of the overnight range.
3. **Inventory Location Pinning ($G_3$)**: Where Globex settled within its range (pinned long, balanced, pinned short).
4. **Extension Regimes ($G_4$)**: True gap up/down vs inside days vs extensions.
5. **Directional Confluence ($G_5$)**: Prior RTH trend alignment with overnight gap.

### Definitive Conclusion:
**Overnight inventory does NOT contain stable, exploitable conditioning information about RTH directional persistence.**
- **Gap Continuation is a Pure Coin Flip**: Across 3,470 sessions, RTH moves in the direction of the overnight gap exactly **50.8%** of the time (IS $51.3\%$, Val $50.7\%$, OOS $48.0\%$).
- **Directional Efficiency is Invariant**: RTH directional efficiency ($|Close - Open| / Range$) hovers tightly between **0.46 and 0.50** across all inventory regimes. Pinned long inventory (0.493) is indistinguishable from balanced inventory (0.472).
- **Extreme Regimes Suffer Catastrophic Tail Flips**:
  - `LARGE_GAP_UP`: RTH return starts positive In-Sample ($+5.79$ pts), degrades in Validation ($-7.97$ pts), and turns into a massive sell-off in OOS (**-23.60 pts**).
  - `TRUE_GAP_DOWN`: In Validation, true gap downs suffered severe follow-through selling (**-135.25 pts/session**); in OOS, they produced massive violent mean-reversion squeezes (**+175.92 pts/session**).

Because the pre-market state does not reliably condition RTH persistence across chronological splits, attempting to monetize it into active trading rules would be pure curve-fitting on noise. The strategy is killed at the Information Gate.

---

## 2. Unconditional Population Baseline (2010–2026)

| Split | Sessions (N) | Mean Directional Efficiency | Clean Trend Day % | Gap Continuation % | Mean RTH Return (pts) |
|:---|---:|:---:|:---:|:---:|:---:|
| **In-Sample (2010–2021)** | 2,326 | 0.464 | 12.3% | 51.3% | +2.21 |
| **Validation (2022–2024)** | 747 | 0.497 | 39.5% | 50.7% | -0.18 |
| **Out-of-Sample (2025–2026)** | 397 | 0.489 | 35.8% | 48.0% | +5.58 |
| **ALL (2010–2026)** | **3,470** | **0.474** | **20.9%** | **50.8%** | **+2.08** |

---

## 3. Empirical Scan: Overnight Extension Regimes ($G_4$)

*Classification relative to prior day's RTH High and Low:*

| Extension Regime | Split | Sessions (N) | % of Days | Mean Efficiency | Trend Day % | Gap Continuation % | Mean RTH Return (pts) |
|:---|:---|---:|---:|:---:|:---:|:---:|---:|
| **TRUE_GAP_UP** | IS | 132 | 5.7% | 0.492 | 7.6% | 52.3% | -2.50 |
| | Validation | 26 | 3.5% | 0.575 | 50.0% | 57.7% | +1.20 |
| | OOS | 22 | 5.5% | 0.499 | 36.4% | 40.9% | **-29.43** |
| | **ALL** | **180** | **5.2%** | **0.505** | **17.2%** | **51.7%** | **-5.26** |
| **EXTENSION_UP** | IS | 986 | 42.4% | 0.465 | 12.8% | 53.0% | -0.56 |
| | Validation | 281 | 37.6% | 0.513 | 41.6% | 52.9% | +4.13 |
| | OOS | 175 | 44.1% | 0.488 | 34.9% | 47.7% | -8.87 |
| | **ALL** | **1,442** | **41.6%** | **0.477** | **21.1%** | **52.3%** | **-0.66** |
| **INSIDE_BALANCED** | IS | 564 | 24.2% | 0.451 | 10.5% | 51.6% | +2.73 |
| | Validation | 211 | 28.2% | 0.484 | 35.5% | 45.7% | -3.34 |
| | OOS | 77 | 19.4% | 0.511 | 37.7% | 49.4% | -32.16 |
| | **ALL** | **852** | **24.6%** | **0.465** | **19.1%** | **49.9%** | **-1.93** |
| **EXTENSION_DOWN** | IS | 575 | 24.7% | 0.461 | 14.3% | 48.8% | +6.19 |
| | Validation | 214 | 28.6% | 0.478 | 38.3% | 50.2% | +6.59 |
| | OOS | 113 | 28.5% | 0.471 | 37.2 | 50.4% | +45.41 |
| | **ALL** | **902** | **26.0%** | **0.466** | **22.8%** | **49.3%** | **+11.20** |
| **TRUE_GAP_DOWN** | IS | 69 | 3.0% | 0.513 | 14.5% | 44.9% | +13.47 |
| | Validation | 15 | 2.0% | 0.532 | 53.3% | 73.3% | **-135.25** |
| | OOS | 10 | 2.5% | 0.498 | 20.0% | 30.0% | **+175.92** |
| | **ALL** | **94** | **2.7%** | **0.514** | **21.3%** | **47.9%** | **+7.02** |

---

## 4. Empirical Scan: Inventory Location Pinning ($G_3$)

*Settlement location of Globex within its overnight range:*

| Location Bin | IS Return (pts) | Val Return (pts) | OOS Return (pts) | ALL Return (pts) | ALL Mean Efficiency | ALL Trend Day % |
|:---|---:|---:|---:|---:|:---:|:---:|
| **PINNED_SHORT ($\le 0.20$)** | +2.81 | -10.67 | +20.86 | +0.91 | 0.480 | 23.4% |
| **LOWER_MID ($0.20–0.40$)** | +0.57 | -1.35 | -16.77 | -1.79 | 0.460 | 20.3% |
| **BALANCED ($0.40–0.60$)** | -0.58 | +6.73 | -7.24 | +0.07 | 0.472 | 18.8% |
| **UPPER_MID ($0.60–0.80$)** | +1.79 | +18.84 | +33.24 | +8.92 | 0.459 | 19.0% |
| **PINNED_LONG ($\ge 0.80$)** | +5.30 | **-8.43** | **-4.17** | +1.29 | 0.493 | 22.6% |

- Pinned Long inventory flips from $+5.30$ pts In-Sample to negative in Validation ($-8.43$ pts) and OOS ($-4.17$ pts).
- Trend Day percentage across all location bins is virtually flat (ranging narrowly from $18.8\%$ to $23.4\%$).

---

## 5. Information Gate Conclusion

The pre-market overnight inventory features do not possess predictive or conditioning alpha. 
- Gap continuation is unforecastable from overnight inventory ($50.8\%$ unconditional rate).
- Directional persistence and trend-day likelihood are not gated by overnight structure.
- In accordance with our hostile research framework, **Strategy 37 is killed at the Information Gate**. We do not proceed to monetization or rule optimization.
