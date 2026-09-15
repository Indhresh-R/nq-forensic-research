# Strategy 36: Unconditional NQ Long-Side Directional Bias -- Pre-Registration

**Pre-registration Date:** 2026-09-14  
**Status:** FROZEN BEFORE BACKTEST EXECUTION

This document locks all hypotheses, entry sampling rules, holding horizons, symmetric structures, cost models, and promotion gates before running backtests.

---

## 1. Core Hypothesis
Does NQ have a persistent long-side return advantage that remains positive and exploitable after realistic trading costs, without relying on bull flags, chart patterns, or selection filters?

### Null Hypotheses:
- $H_{0,1}$ (Symmetric Null): Unconditional Long returns equal Short returns ($\mathbb{E}[\Delta P_{long}] = \mathbb{E}[\Delta P_{short}]$).
- $H_{0,2}$ (Friction Null): Active long-side returns are completely eroded by realistic transaction friction ($\mathbb{E}[\Delta P_{net}] \le 0$).
- $H_{0,3}$ (Beta Equivalence Null): Active long-side trading is merely a high-friction, diluted capture of passive market drift, failing to outperform passive Buy-and-Hold on a risk-adjusted basis (Sharpe / Calmar).

---

## 2. Universe, Data, and Chronological Splits
- **Market**: Continuous E-mini Nasdaq-100 (NQ), tick size 0.25, point value $20.00.
- **Session**: Regular Trading Hours (RTH), 09:30--15:55 America/New_York.
- **Splits**:
  - In-Sample (IS): 2010-01-01 to 2021-12-31 (12 years)
  - Validation: 2022-01-01 to 2024-12-31 (3 years)
  - Out-of-Sample (OOS): 2025-01-01 to 2026-08 (reported separately as 2025 and 2026)

---

## 3. Entry Sampling Architecture

### Arm 1: Session Milestone Clocks
Systematic evaluation at four high-liquidity session timestamps:
1. **09:35 ET** (Market open auction settling)
2. **10:30 ET** (End of Initial Balance / morning flow)
3. **12:00 ET** (Midday liquidity trough)
4. **14:00 ET** (Afternoon session / European close)

### Arm 2: Systematic 15-Minute Continuous Sampling
Every completed 15-minute clock from 09:45 to 15:00 ET (22 daily intraday sample points), entry at the next 1-minute open.

---

## 4. Holding Horizons & Evaluation Modes

### Holding Horizons
For every entry at minute $T+1$:
- $H_1 = 5\text{ minutes}$
- $H_2 = 15\text{ minutes}$
- $H_3 = 30\text{ minutes}$
- $H_4 = 60\text{ minutes}$
- $H_5 = \text{Session Close}$ (flat at 15:55 ET close)

### Mode A: Pure Horizon Drift (Unconstrained Forward Return)
- Long: Buy at open of $T+1$; exit at close of $T+H$ (or 15:55 ET).
- Short: Sell short at open of $T+1$; exit at close of $T+H$ (or 15:55 ET).
- No stop-loss, no take-profit. Evaluates the unadulterated conditional forward return distribution.

### Mode B: Symmetric Stop/Target Active Trading
- Stop Loss: $1.0 \times \text{ATR}_{20}$ (computed on 5m bars).
- Variant B1 (1.0R): Target = $1.0 \times \text{ATR}_{20}$.
- Variant B2 (1.5R): Target = $1.5 \times \text{ATR}_{20}$.
- Max holding period: Horizon $H$ or 15:55 ET flat.
- Ambiguity Policy: Same-bar stop and target hit is strictly recorded as **STOP FIRST**.

---

## 5. Cost Model & Passive Benchmark

### Transaction Costs
- Baseline: **1.0 NQ index point** round-trip ($20.00 / contract).
- Sweeps: 0.0, 0.5, 1.0, 1.5, 2.0 points.

### Passive Benchmark (Beta Attribution)
- **RTH Buy-and-Hold**: Buy at 09:30 open, sell at 15:55 close (1 trade/day, paying 1.0 pt cost).
- **Continuous Buy-and-Hold**: Continuous 100% long exposure held overnight.
- Comparison metrics: Annualized Return, Volatility, Sharpe Ratio, Max Drawdown, Friction Drag Ratio ($\frac{\text{Total Costs Paid}}{\text{Gross PnL}}$).

---

## 6. Promotion / Kill Criteria
- **A (Validated Edge)**:
  1. Long net expectancy > 0 across IS, Validation, and OOS (including 2025 and 2026).
  2. Long net expectancy strictly beats Short net expectancy.
  3. Active long outperforms the passive benchmark on risk-adjusted metrics (Sharpe Ratio and Drawdown), proving genuine Alpha.
- **C (Kill)**:
  - If net expectancy is $\le 0$ after costs, or flips sign in OOS, or underperforms passive Buy-and-Hold after accounting for fee drag, the claim of an active edge is killed.
