# PREREGISTRATION: Strategy 41 -- Volatility Regime → Transaction-Cost Capacity & Opportunity Quality

**Registration Date:** 2026-09-14  
**Status:** FROZEN  
**Target Asset:** Continuous E-mini Nasdaq-100 Futures (NQ) 1-Minute Bars (2010--2026)  
**Primary Question:** Does predictable volatility persistence (Strategy 39) make trading signals more economically viable after transaction costs by expanding available price excursion relative to fixed friction?

---

## 1. Research Philosophy & Protocol
1. **Friction Decomposition**: Round-trip transaction friction is fixed at 1.0 point ($20.00). If market movement scales with volatility while friction remains fixed, the economic drag ratio ($\text{Friction} / \text{Excursion}$) decreases.
2. **Two-Layer Architecture**:
   - **Layer 1 (Signal-Agnostic)**: Evaluates the theoretical movement capacity (RTH range, 60m excursion, unilateral open-to-extreme excursion) across pre-open volatility tiers.
   - **Layer 2 (Friction Stratification)**: Stratifies pre-existing, frozen benchmark directional signals (Strategies 30, 38, 36) across Strategy-39 volatility tiers without creating circular signals.
3. **Information-First**: No curve-fitting of stops or targets. Fixed friction is applied strictly to gross trade returns ($E_{net} = E_{gross} - 1.0$ pt).

---

## 2. Pre-Open Volatility Conditioning States ($t-1$, strictly known at $t \le 09:29\text{ ET}$)
All tiers are established strictly from session $t-1$ RTH data and trailing 20-day ATR:
- $\text{NormRange}_{t-1} = \text{Range}_{t-1} / \text{ATR}_{20, t-1}$
- Volatility Tiers:
  - `LOW_VOL`: $\text{NormRange}_{t-1} < 0.75$
  - `NORMAL_VOL`: $0.75 \le \text{NormRange}_{t-1} \le 1.25$
  - `HIGH_VOL`: $1.25 < \text{NormRange}_{t-1} \le 1.50$
  - `EXTREME_VOL`: $\text{NormRange}_{t-1} > 1.50$
- Range-to-Median Ratio:
  - `COMPRESSED`: $< 0.65$
  - `NORMAL`: $0.65 \to 1.20$
  - `EXPANDED`: $> 1.20$

---

## 3. Layer 1: Signal-Agnostic Capacity Metrics (Session $t$)
1. **Full RTH Range**: $\text{High}_{RTH} - \text{Low}_{RTH}$ (points).
2. **Unilateral Excursion from 09:30 Open**: $\max(\text{High} - \text{Open}, \text{Open} - \text{Low})$.
3. **60-Minute Excursion from 09:35 Open**: $\max(\text{High}_{60} - \text{Open}_{09:35}, \text{Open}_{09:35} - \text{Low}_{60})$.
4. **Friction Drag Ratio**: $\frac{1.0\text{ pt}}{\text{Available Excursion (pts)}} \times 100\%$.
5. **Excursion Reach Probabilities**: $P(\text{Excursion} \ge 20\text{ pts})$, $P(\ge 40\text{ pts})$, $P(\ge 80\text{ pts})$, $P(\ge 120\text{ pts})$.

---

## 4. Layer 2: Frozen Pre-Existing Benchmark Signals Evaluated
1. **Signal A (Strategy 30 Initial Balance Breakout)**:
   - 30-minute opening range ($09:30 \to 10:00$).
   - Buy on first bar close $> High_{30}$; Sell on first bar close $< Low_{30}$.
   - Exit at 15:55 close.
2. **Signal B (Strategy 38 15-Minute Opening Drive Momentum)**:
   - Direction of displacement from 09:30 to 09:45 ($Close_{09:45} - Open_{09:30}$).
   - Enter at 09:45 open in direction of drive.
   - Exits: 60-minute holding period and 15:55 close.
3. **Signal C (Strategy 36 Fixed-Clock Intraday)**:
   - Enter at 09:35 in direction of prior session close.
   - Exit: 60-minute holding period.

---

## 5. Chronological Partitions & Hostile Criteria
- **In-Sample (IS)**: 2011-01-01 to 2021-12-31
- **Validation**: 2022-01-01 to 2024-12-31
- **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (split into 2025 and 2026)

### Hostile Decision Tree
- **Promotion (Valid Economic Filter)**:
  - High/Extreme volatility regimes convert negative net expectancy in low-vol regimes ($E_{net} < 0$) into **positive, robust net expectancy ($E_{net} > 0$, $PF_{net} > 1.15$)** consistently across IS, Validation, and OOS.
  - Signal-agnostic friction drag ratio must drop by $\ge 50\%$ in high vs low volatility.
- **Null / Kill (Verdict C)**:
  - Higher volatility expands gross returns, but adverse excursion (MAE / stop losses) expands in equal proportion, leaving net expectancy negative or unstable across splits.
  - If confirmed, volatility expansion is merely variance scaling, not an economic edge filter. Strategy 41 is killed.
