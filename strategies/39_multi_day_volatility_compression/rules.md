# Strategy 39: Rules & Feature Engineering Specification

## 1. Information-First Protocol
- No trade execution, orders, entries, stops, or targets.
- The scan must strictly measure the conditional distribution of RTH session characteristics given prior volatility state.

## 2. Causality & Timestamp Guarantees
- Observation point: strictly at or before **09:29:59 ET** on session date $t$.
- All historical features use closed bars from session $t-1$ and prior ($t-2, t-3, \dots$).
- Target measurements use strictly RTH bars from session $t$ ($09:30:00 \to 15:55:00\text{ ET}$).

## 3. Mathematical Definitions

### Trailing Metrics
For each session date $t$, let:
- $\text{Range}_{t-1} = \text{High}_{RTH, t-1} - \text{Low}_{RTH, t-1}$
- $\text{ATR}_{20, t-1} = \frac{1}{20}\sum_{i=1}^{20} \text{Range}_{t-i}$
- $\text{Median}_{20, t-1} = \text{Median}(\text{Range}_{t-1}, \dots, \text{Range}_{t-20})$

### Feature Set
1. **$F_1, F_2, F_3$: Multi-Day Range Percentiles**:
   $$\text{RollingPercentile}_{252}\left(\frac{1}{K}\sum_{i=1}^K \text{Range}_{t-i}\right), \quad K \in \{3, 5, 10\}$$
   Quintile bins:
   - `Q1_DEEP_COMPRESSION`: $< 20\text{th percentile}$
   - `Q2_MILD_COMPRESSION`: $20\text{th} \to 40\text{th percentile}$
   - `Q3_NORMAL`: $40\text{th} \to 60\text{th percentile}$
   - `Q4_MILD_EXPANSION`: $60\text{th} \to 80\text{th percentile}$
   - `Q5_DEEP_EXPANSION`: $> 80\text{th percentile}$

2. **$F_4$: 20-Day ATR Percentile**:
   $$\text{RollingPercentile}_{252}(\text{ATR}_{20, t-1})$$
   Gauges macro volatility cycle.

3. **$F_5$: Narrow Range Structural Patterns**:
   - `NR4`: $\text{Range}_{t-1} < \min(\text{Range}_{t-2}, \text{Range}_{t-3}, \text{Range}_{t-4})$
   - `NR7`: $\text{Range}_{t-1} < \min(\text{Range}_{t-2}, \dots, \text{Range}_{t-7})$
   - `INSIDE_DAY`: $\text{High}_{t-1} \le \text{High}_{t-2} \;\text{and}\; \text{Low}_{t-1} \ge \text{Low}_{t-2}$
   - `ID_NR4`: `INSIDE_DAY` AND `NR4`
   - `ID_NR7`: `INSIDE_DAY` AND `NR7`

4. **$F_6$: Consecutive Contracting Days**:
   Count of consecutive prior days $k \ge 1$ where $\text{Range}_{t-i} < \text{Range}_{t-i-1}$ for all $1 \le i \le k$.
   Bins: 0, 1, 2, 3, $\ge 4$ days.

5. **$F_7$: Prior Range vs 20-Day Median Ratio**:
   $$\text{Ratio}_{t-1} = \frac{\text{Range}_{t-1}}{\text{Median}_{20, t-1}}$$
   - Tertiles: Deep Compression ($< 0.65$), Normal ($0.65 \to 1.20$), Expanded ($> 1.20$).

6. **$F_8$: Compression Duration**:
   Number of consecutive prior sessions where $\text{Range}_{t-i} < \text{Median}_{20, t-i}$.
   Bins: 0, 1, 2, 3, $\ge 4$ days.

### Target Measurements (Next RTH Session: 09:30 to 15:55 ET)
- **$Y_1$: Normalized Range**: $\text{Range}_{t} / \text{ATR}_{20, t-1}$
- **$Y_2$: Normalized Absolute Return**: $|Close_{RTH, t} - Open_{RTH, t}| / \text{ATR}_{20, t-1}$
- **$Y_3$: Directional Efficiency**: $|Close_{RTH, t} - Open_{RTH, t}| / \text{Range}_{t}$
- **$Y_4$: Clean Trend Day**: $\mathbb{I}(\text{Range}_{norm} \ge 1.0 \;\text{and}\; \text{Efficiency} \ge 0.60)$
- **$Y_5$: High-Conviction Trend Day**: $\mathbb{I}(\text{Range}_{norm} \ge 1.25 \;\text{and}\; \text{Efficiency} \ge 0.70)$
- **$Y_6$: Range Expansion Rate**: $\mathbb{I}(\text{Range}_{norm} \ge 1.25)$ and $\mathbb{I}(\text{Range}_{norm} \ge 1.50)$
- **$Y_7$: Maximum Unilateral Excursion**: $\max(\text{High}_t - \text{Open}_t, \text{Open}_t - \text{Low}_t) / \text{ATR}_{20, t-1}$
- **$Y_8$: Close-Location Pinning**: $\mathbb{I}\left(\frac{Close - Low}{Range} < 0.20 \;\text{or}\; > 0.80\right)$
