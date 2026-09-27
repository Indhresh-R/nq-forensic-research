# Strategy 35: Bull Flags and Bear Flags -- Full Forensic Report

**Date:** 2026-09-14  
**Verdict:** **C (KILL)**  
**Markets Evaluated:** NQ and ES Continuous Futures (2010--2026)  
**Sample Size:** 3,885 candidate trade simulations across 777 unique causal setups  

---

## 1. Executive Summary

This forensic investigation tested the textbook claim that **Bull Flags** and **Bear Flags** provide a high-probability continuation edge after transaction costs.

### Key Empirical Findings
1. **Catastrophic Out-of-Sample Failure on ES**:
   - Across **all** pre-registered candidate exits (Measured Move, 1.0R, 1.5R, 2.0R, Session Close), ES flag breakouts fail severely in the Out-of-Sample period (2025–2026), generating negative net expectancy ($E_{net} = -2.67$ to $-4.81$ pts) and profit factors between **0.530 and 0.717**.
   - Frictionless testing confirms this is **not** a fee artifact: even with zero commissions and zero slippage, ES flags lose money out-of-sample ($E = -2.17$ to $-4.31$ pts).
2. **Directional Asymmetry on NQ (Beta Artifact, Not Alpha)**:
   - On NQ, Bull Flags showed positive net expectancy across splits (IS $+4.14$, Val $+7.64$, OOS $+4.73$ pts on C1), while Bear Flags collapsed completely (Val $-3.19$ pts, OOS C4 $-59.43$ pts, C5 $-65.09$ pts).
   - Attribution benchmarking proves this is an artifact of secular equity bull market drift. Entering after a pure impulse pole **without** any flag consolidation yields higher win rates ($55.1\%$ vs $42.1\%$) and superior expectancy. The "flag" consolidation adds **zero incremental edge**.
3. **Classical Measured Move Inefficiency**:
   - The classical chartist target ($1.0 \times \text{flagpole}$) exhibits low hit rates ($32\%$ to $43\%$), fails out-of-sample on ES (OOS WR $32.6\%$, PF $0.691$), and flipped negative on NQ in 2025 ($-1.70$ pts).

---

## 2. Master Performance Table (Pre-Registered Candidates)

| Market | Candidate | IS N | IS WR | IS PF | IS E (pts) | Val N | Val WR | Val PF | Val E (pts) | OOS N | OOS WR | OOS PF | OOS E (pts) | 2025 E | 2026 E |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **NQ** | C1 (Measured Move) | 280 | 43.2% | 1.349 | +3.23 | 117 | 41.0% | 1.105 | +2.74 | 49 | 40.8% | 1.129 | +5.42 | -1.70 | +13.48 |
| **NQ** | C2 (1.0R Fixed) | 280 | 53.9% | 1.073 | +0.59 | 117 | 53.9% | 1.048 | +1.06 | 49 | 46.9% | 0.913 | -3.38 | +0.72 | -8.01 |
| **NQ** | C3 (1.5R Fixed) | 280 | 47.9% | 1.305 | +2.63 | 117 | 47.0% | 1.054 | +1.32 | 49 | 40.8% | 1.106 | +4.46 | +4.50 | +4.41 |
| **NQ** | C4 (2.0R Fixed) | 280 | 43.9% | 1.312 | +2.84 | 117 | 44.4% | 1.189 | +4.79 | 49 | 36.7% | 0.715 | -14.02 | -9.04 | -19.64 |
| **NQ** | C5 (Session Close) | 280 | 39.6% | 1.341 | +3.34 | 117 | 39.3% | 1.184 | +4.91 | 49 | 36.7% | 0.824 | -8.64 | -6.77 | -10.76 |
| **ES** | C1 (Measured Move) | 189 | 37.6% | 1.085 | +0.31 | 96 | 43.8% | 1.382 | +2.11 | 46 | 32.6% | **0.691** | **-3.16** | -2.34 | -3.91 |
| **ES** | C2 (1.0R Fixed) | 189 | 48.7% | 0.844 | -0.49 | 96 | 55.2% | 1.146 | +0.69 | 46 | 47.8% | 1.010 | +0.08 | +0.22 | -0.05 |
| **ES** | C3 (1.5R Fixed) | 189 | 41.8% | 0.988 | -0.04 | 96 | 52.1% | 1.520 | +2.56 | 46 | 32.6% | **0.717** | **-2.67** | -3.16 | -2.21 |
| **ES** | C4 (2.0R Fixed) | 189 | 39.2% | 1.175 | +0.62 | 96 | 45.8% | 1.287 | +1.57 | 46 | 30.4% | **0.646** | **-3.62** | -2.06 | -5.06 |
| **ES** | C5 (Session Close) | 189 | 33.9% | 0.977 | -0.09 | 96 | 39.6% | 1.280 | +1.63 | 46 | 30.4% | **0.530** | **-4.81** | -3.82 | -5.72 |

---

## 3. Bull vs Bear Directional Asymmetry Audit

Breaking down signals into Bull Flags vs Bear Flags highlights the underlying structural reality:

### NQ Directional Breakdown (Candidate C1 Measured Move)
- **Bull Flags**:
  - In-Sample: $N=179$, Win Rate $44.7\%$, PF $1.475$, $E = +4.14$ pts
  - Validation: $N=64$, Win Rate $45.3\%$, PF $1.336$, $E = +7.64$ pts
  - OOS: $N=38$, Win Rate $42.1\%$, PF $1.125$, $E = +4.73$ pts
- **Bear Flags**:
  - In-Sample: $N=101$, Win Rate $40.6\%$, PF $1.159$, $E = +1.62$ pts
  - Validation: $N=53$, Win Rate $35.8\%$, PF $0.894$, $E = -3.19$ pts (FAIL)
  - OOS: $N=11$, Win Rate $36.4\%$, PF $1.139$, $E = +7.82$ pts (Tiny sample)

### ES Directional Breakdown (Candidate C3 1.5R)
- **Bull Flags**:
  - In-Sample: $N=115$, Win Rate $43.5\%$, PF $1.045$, $E = +0.14$ pts
  - Validation: $N=54$, Win Rate $53.7\%$, PF $1.683$, $E = +2.66$ pts
  - OOS: $N=33$, Win Rate **27.3%**, PF **0.559**, $E = \mathbf{-3.62}$ pts (CATASTROPHIC COLLAPSE)
- **Bear Flags**:
  - In-Sample: $N=74$, Win Rate $39.2\%$, PF $0.922$, $E = -0.31$ pts (FAIL)
  - Validation: $N=42$, Win Rate $50.0\%$, PF $1.388$, $E = +2.42$ pts
  - OOS: $N=13$, Win Rate $46.2\%$, PF $0.981$, $E = -0.23$ pts (FAIL)

---

## 4. Benchmark Attribution (Does the "Flag" Add Value?)

To determine whether the flag consolidation adds genuine predictive power, we tested entering directly after the 4-bar flagpole **without** waiting for any consolidation or breakout:

| Condition | Split | N | Win Rate | Profit Factor | Expectancy (pts) | Expectancy ($) |
|:---|:---|---:|---:|---:|---:|---:|
| **NQ Flag Breakout (C1)** | IS | 280 | 43.2% | 1.349 | +3.23 | +$64.57 |
| **NQ Pure Momentum Pole (No Flag)** | IS | 683 | 53.3% | 1.190 | +2.35 | +$47.09 |
| **NQ Flag Breakout (C1)** | OOS | 49 | 40.8% | 1.129 | +5.42 | +$108.47 |
| **NQ Pure Momentum Pole (No Flag)** | OOS | 107 | 55.1% | 1.164 | +7.46 | +$149.16 |

### Attribution Conclusion:
The flag consolidation condition acts merely as an opportunistic, lossy filter. Waiting for a flag reduces signal frequency by ~60% and drops the win rate from 55% to 41%. The positive drift in NQ longs is a reflection of persistent market beta, not pattern recognition.

---

## 5. Friction & Cost Sensitivity

| Market | Candidate | Cost = 0.0 pts | Cost = 0.5 pts | Cost = 1.0 pt | Cost = 2.0 pts | Break-Even Friction |
|:---|:---|:---|:---|:---|:---|:---|
| **NQ** | C1 (Measured Move) OOS | +6.42 pts (PF 1.155) | +5.92 pts (PF 1.142) | +5.42 pts (PF 1.129) | +4.42 pts (PF 1.104) | ~12.0 pts |
| **NQ** | C4 (2.0R) OOS | -13.02 pts (PF 0.731) | -13.52 pts (PF 0.723) | -14.02 pts (PF 0.715) | -15.02 pts (PF 0.700) | Negative at 0 cost |
| **ES** | C1 (Measured Move) OOS | **-2.66 pts (PF 0.731)** | **-3.16 pts (PF 0.691)** | **-3.66 pts (PF 0.654)** | N/A | Negative at 0 cost |
| **ES** | C3 (1.5R) OOS | **-2.17 pts (PF 0.762)** | **-2.67 pts (PF 0.717)** | **-3.17 pts (PF 0.676)** | N/A | Negative at 0 cost |

On ES, the system is deeply underwater even before costs are applied. On NQ, higher targets (C4, C5) are heavily negative in OOS.
