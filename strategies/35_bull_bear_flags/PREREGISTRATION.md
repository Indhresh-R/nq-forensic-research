# Strategy 35: Bull Flags and Bear Flags -- Pre-Registration

**Pre-registration Date:** 2026-09-14  
**Status:** FROZEN BEFORE BACKTEST EXECUTION

This document locks all definitions, candidates, parameters, execution rules, and evaluation gates before evaluating Validation or OOS data.

---

## 1. Core Hypothesis
Classical technical analysis asserts that Bull Flags and Bear Flags are high-probability continuation patterns. A directional impulse ("flagpole") followed by an orderly, shallow consolidation ("flag") with contracting volume is hypothesized to offer positive net expectancy upon breakout resumption after transaction costs.

Null Hypothesis ($H_0$): Flag breakouts have zero or negative net expectancy after transaction costs, do not outperform unconditional session drift, and fail to sustain positive performance across out-of-sample periods.

---

## 2. Universe, Data, and Splits

- **Markets**:
  - Continuous E-mini Nasdaq-100 (NQ), tick size 0.25, point value $20.00.
  - Continuous E-mini S&P 500 (ES), tick size 0.25, point value $50.00.
- **Session**: Regular Trading Hours (RTH), 09:30--15:55 America/New_York.
  - Signal evaluation window: 09:45--15:00 ET.
  - Session flat: 15:55 ET.
- **Chronological Splits** (Frozen Program Standard):
  - **In-Sample (IS)**: 2010-01-01 to 2021-12-31 (12 years).
  - **Validation**: 2022-01-01 to 2024-12-31 (3 years).
  - **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (reported separately as 2025 and 2026).

---

## 3. Causal Mechanical Definitions

### Timeframe
- Bar construction: 5-minute bars aggregated strictly from completed 1-minute prints within the session.
- Path resolution / trade tracking: 1-minute bars strictly starting at $T+1$.

### A. Flagpole (Impulse) Specification
- Window length: $N_{pole} = 4$ completed 5-minute bars (20 minutes).
- Height criterion: Net displacement $|Close_{end} - Open_{start}| \ge 1.5 \times \text{ATR}_{20}$ (where $\text{ATR}_{20}$ is the 20-bar 5-minute ATR).
- Directional Efficiency: $\frac{|Close_{end} - Open_{start}|}{\sum \text{Bar Range}} \ge 0.65$.
- Polarity:
  - Bull Pole: $Close_{end} > Open_{start}$.
  - Bear Pole: $Close_{end} < Open_{start}$.

### B. Flag (Consolidation) Specification
- Consolidation window: $k_{flag} \in [3, 8]$ completed 5-minute bars (15 to 40 minutes) following the flagpole.
- Retracement constraint:
  - Bull Flag: Lowest low of the flag $\ge Pole\_High - 0.50 \times Pole\_Height$ (max 50% retrace).
  - Bear Flag: Highest high of the flag $\le Pole\_Low + 0.50 \times Pole\_Height$ (max 50% retrace).
- Tightness constraint:
  - Flag range $(Flag\_High - Flag\_Low) \le 0.50 \times Pole\_Height$.
- Volume contraction constraint:
  - Mean 5m volume during flag $\le 1.0 \times$ Mean 5m volume during flagpole.

### C. Breakout Trigger & Causal Execution
- Breakout condition at completed 5-minute bar $T$:
  - Bull Flag: $Close[T] > Flag\_High$.
  - Bear Flag: $Close[T] < Flag\_Low$.
- Execution: Long/Short entry executed at the open of minute bar $T+1$.
- Stop Loss:
  - Bull Flag: $Flag\_Low$.
  - Bear Flag: $Flag\_High$.
  - Defined initial risk $R = |Entry - Stop|$.
- Maximum 1 trade per side/candidate per session (first signal wins).

---

## 4. Frozen Candidate Set

| Candidate | Strategy Arm | Profit Target | Invalidation Stop | Max Hold |
|-----------|--------------|---------------|-------------------|----------|
| **C1** | Measured Move | Entry $\pm 1.0 \times Pole\_Height$ | Flag Extreme | 15:55 ET |
| **C2** | 1.0R Fixed | Entry $\pm 1.0 \times R$ | Flag Extreme | 15:55 ET |
| **C3** | 1.5R Fixed | Entry $\pm 1.5 \times R$ | Flag Extreme | 15:55 ET |
| **C4** | 2.0R Fixed | Entry $\pm 2.0 \times R$ | Flag Extreme | 15:55 ET |
| **C5** | Session Drift (No Target) | None (15:55 close) | Flag Extreme | 15:55 ET |
| **C6** | Pure Impulse Control | 1.5R against Pole Extreme | Pole Extreme | 15:55 ET |

---

## 5. Execution Friction & Ambiguity Rules

- **Round-Trip Cost (Standard Baseline)**:
  - NQ: 1.0 index point ($20.00 per contract).
  - ES: 0.50 index point ($25.00 per contract).
- **Cost Sensitivity Tests**:
  - NQ: 0.50, 1.0, 2.0 points.
  - ES: 0.25, 0.50, 1.00 points.
- **Intrabar Ambiguity Policy**:
  - If both profit target and stop loss are touched within the same 1-minute bar, the outcome is recorded as a **STOP FIRST** (adverse assumption).

---

## 6. Promotion / Kill Criteria
To achieve an **A** verdict:
1. Positive net expectancy ($E_{net} > 0$) across IS, Validation, and OOS.
2. Consistent sign and statistical stability on both NQ and ES.
3. Outperforms both the unconditional session drift baseline and the pure impulse control (C6).
4. Survives cost stress testing.

If performance is negative or flips sign between IS and Validation/OOS, the family will receive a **C (Kill)** verdict with explicit documentation of its failure mode.
