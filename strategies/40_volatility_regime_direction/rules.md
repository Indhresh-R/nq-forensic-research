# Strategy 40: Rules & Feature Engineering Specification

## 1. Information-First Protocol
- Strictly no trading rules, execution logic, stops, or profit targets.
- Measures the empirical conditional distribution of subsequent RTH directional behavior.

## 2. Causality Guarantees
- Observation point: strictly at or before **09:29:59 ET** on session date $t$.
- All conditioning metrics are computed from closed RTH sessions $t-1, t-2, \dots$
- All target metrics are computed strictly from RTH session $t$ ($09:30:00 \to 15:55:00\text{ ET}$).

## 3. Mathematical Definitions

### Conditioning Metrics ($t-1$)
1. **Prior Normalized Range**:
   $$\text{NormRange}_{t-1} = \frac{\text{High}_{RTH, t-1} - \text{Low}_{RTH, t-1}}{\text{ATR}_{20, t-1}}$$
   - `LOW_VOL`: $< 0.75$
   - `NORMAL_VOL`: $0.75 \to 1.25$
   - `HIGH_VOL`: $1.25 \to 1.50$
   - `EXTREME_VOL`: $> 1.50$

2. **Prior Range vs 20-Day Median**:
   $$\text{Ratio}_{t-1} = \frac{\text{Range}_{t-1}}{\text{Median}_{20, t-1}(\text{Range})}$$
   - `COMPRESSED`: $< 0.65$
   - `NORMAL`: $0.65 \to 1.20$
   - `EXPANDED`: $> 1.20$

3. **Prior Normalized Return**:
   $$\text{NormReturn}_{t-1} = \frac{Close_{RTH, t-1} - Open_{RTH, t-1}}{\text{ATR}_{20, t-1}}$$
   - `LARGE_UP`: $\ge +0.75$
   - `MILD_UP`: $+0.20 \to +0.75$
   - `FLAT`: $-0.20 \to +0.20$
   - `MILD_DOWN`: $-0.75 \to -0.20$
   - `LARGE_DOWN`: $\le -0.75$

4. **Vol $\times$ Direction Crossed States**:
   - `HIGH_VOL_UP`: $\text{NormRange}_{t-1} \ge 1.25$ AND $\text{NormReturn}_{t-1} > 0$
   - `HIGH_VOL_DOWN`: $\text{NormRange}_{t-1} \ge 1.25$ AND $\text{NormReturn}_{t-1} < 0$
   - `LOW_VOL_UP`: $\text{NormRange}_{t-1} < 0.75$ AND $\text{NormReturn}_{t-1} > 0$
   - `LOW_VOL_DOWN`: $\text{NormRange}_{t-1} < 0.75$ AND $\text{NormReturn}_{t-1} < 0$
   - `NORMAL`: $0.75 \le \text{NormRange}_{t-1} < 1.25$

### Target Measurements (Session $t$: 09:30 to 15:55 ET)
- **$Y_1$: Normalized Return**: $(Close_{RTH, t} - Open_{RTH, t}) / \text{ATR}_{20, t-1}$
- **$Y_2$: Positive Day Indicator**: $\mathbb{I}(Close_{RTH, t} > Open_{RTH, t})$
- **$Y_3$: Directional Continuation**: $\mathbb{I}\left(\text{Sign}(\text{Return}_t) == \text{Sign}(\text{Return}_{t-1})\right)$
- **$Y_4$: Large Up Move ($\ge 1.0$ ATR)**: $\mathbb{I}(\text{Return}_{norm, t} \ge +1.0)$
- **$Y_5$: Large Down Move ($\le -1.0$ ATR)**: $\mathbb{I}(\text{Return}_{norm, t} \le -1.0)$
- **$Y_6$: Upside Excursion**: $(High_{RTH, t} - Open_{RTH, t}) / \text{ATR}_{20, t-1}$
- **$Y_7$: Downside Excursion**: $(Open_{RTH, t} - Low_{RTH, t}) / \text{ATR}_{20, t-1}$
- **$Y_8$: Close-Location**: $(Close_{RTH, t} - Low_{RTH, t}) / \text{Range}_{RTH, t}$
- **$Y_9$: Bull Trend Day**: $\text{NormRange}_t \ge 1.0 \;\&\; \text{Efficiency}_t \ge 0.60 \;\&\; \text{Return}_t > 0$
- **$Y_{10}$: Bear Trend Day**: $\text{NormRange}_t \ge 1.0 \;\&\; \text{Efficiency}_t \ge 0.60 \;\&\; \text{Return}_t < 0$
