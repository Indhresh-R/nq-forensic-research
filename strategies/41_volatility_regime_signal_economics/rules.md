# Strategy 41: Rules & Feature Engineering Specification

## 1. Causality & Timestamp Guarantees
- All volatility regime labels (`LOW_VOL`, `NORMAL_VOL`, `HIGH_VOL`, `EXTREME_VOL`) are calculated strictly using data up through session $t-1$ (known prior to 09:30 ET).
- Signal entries and exits execute strictly on next-bar opens ($t+1$).
- Fixed friction of 1.0 point round-trip is deducted from every trade.

## 2. Mathematical Definitions

### Conditioning Regimes ($t-1$)
- $\text{Range}_{t-1} = High_{RTH, t-1} - Low_{RTH, t-1}$
- $\text{ATR}_{20, t-1} = \frac{1}{20}\sum_{i=1}^{20} \text{Range}_{t-i}$
- $\text{NormRange}_{t-1} = \text{Range}_{t-1} / \text{ATR}_{20, t-1}$
  - `LOW_VOL`: $\text{NormRange}_{t-1} < 0.75$
  - `NORMAL_VOL`: $0.75 \le \text{NormRange}_{t-1} \le 1.25$
  - `HIGH_VOL`: $1.25 < \text{NormRange}_{t-1} \le 1.50$
  - `EXTREME_VOL`: $\text{NormRange}_{t-1} > 1.50$

### Layer 1: Movement Capacity Metrics (Session $t$)
- $\text{RTH\_Range} = High_{RTH, t} - Low_{RTH, t}$
- $\text{Excursion}_{open} = \max(High_{RTH, t} - Open_{09:30, t}, Open_{09:30, t} - Low_{RTH, t})$
- $\text{Excursion}_{60m} = \max(High_{09:35 \to 10:35, t} - Open_{09:35, t}, Open_{09:35, t} - Low_{09:35 \to 10:35, t})$
- $\text{Friction\_Drag}_{open} = 1.0 / \text{Excursion}_{open} \times 100\%$
- $\text{Friction\_Drag}_{60m} = 1.0 / \text{Excursion}_{60m} \times 100\%$

### Layer 2: Benchmark Signal Execution Rules
1. **Signal A (IB Breakout, Strategy 30)**:
   - Initial Balance window: $09:30 \to 10:00$ ET ($OR_{30}$).
   - Entry: First bar after 10:00 ET closing $> High(OR_{30})$ enters Long at next open; first bar closing $< Low(OR_{30})$ enters Short at next open.
   - Max 1 entry per session. Exit: 15:55 close.
2. **Signal B (15m Opening Drive, Strategy 38)**:
   - Evaluated at 09:45 open.
   - If $Close_{09:44} > Open_{09:30}$, enter Long at 09:45 open.
   - If $Close_{09:44} < Open_{09:30}$, enter Short at 09:45 open.
   - Exit variants: 60-minute holding period (10:45 ET) and session close (15:55 ET).
3. **Signal C (Fixed-Clock Intraday Momentum, Strategy 36)**:
   - Evaluated at 09:35 open.
   - If $Close_{t-1} > Open_{t-1}$, enter Long at 09:35 open.
   - If $Close_{t-1} < Open_{t-1}$, enter Short at 09:35 open.
   - Exit: 60-minute holding period (10:35 ET).
