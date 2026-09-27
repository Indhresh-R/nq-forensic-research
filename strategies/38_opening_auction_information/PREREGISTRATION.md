# Strategy 38: Opening Auction Information → Remaining Session Persistence -- Pre-Registration

**Pre-registration Date:** 2026-09-14  
**Status:** FROZEN BEFORE SCAN EXECUTION

This document locks all definitions, observation checkpoints, feature metrics, target variables, and promotion/kill gates before evaluating the data.

---

## 1. Core Research Question
After the market opens, does the first 5 to 15 minutes of actual RTH price and volume behavior reveal whether the remaining session will become a persistent trend or two-sided rotational chop in continuous E-mini Nasdaq-100 (NQ) futures?

### Null Hypothesis ($H_0$):
The conditional distribution of remaining-session directional persistence ($T+1 \to 15:55\text{ ET}$) given any opening auction state (range ratio, path efficiency, relative volume, displacement) is identical to the unconditional baseline. Early auction behavior conveys zero predictive or conditioning information about the remainder of the trading day.

---

## 2. Universe, Data, and Splits
- **Market**: Continuous E-mini Nasdaq-100 (NQ), tick size 0.25, point value $20.00.
- **Session**: Regular Trading Hours (RTH), 09:30--15:55 America/New_York.
- **Chronological Splits**:
  - In-Sample (IS): 2010-01-01 to 2021-12-31 (12 years)
  - Validation: 2022-01-01 to 2024-12-31 (3 years)
  - Out-of-Sample (OOS): 2025-01-01 to 2026-08 (split into 2025 and 2026)

---

## 3. Early Observation Checkpoints & Feature Metrics

Three checkpoints evaluated at completed minute prints:
- **5-Minute Checkpoint ($T_5 = 09:34\text{ close}$ / known at $09:35\text{ open}$)**
- **10-Minute Checkpoint ($T_{10} = 09:39\text{ close}$ / known at $09:40\text{ open}$)**
- **15-Minute Checkpoint ($T_{15} = 09:44\text{ close}$ / known at $09:45\text{ open}$)**

At each checkpoint $T \in \{T_5, T_{10}, T_{15}\}$:
1. **Opening Range Ratio ($F_1$)**:
   $$OR_T = High_{09:30 \to T} - Low_{09:30 \to T}$$
   $$OR\_Ratio_T = \frac{OR_T}{\text{ATR}_{20}}$$
   - Tertiles computed on In-Sample: `COMPRESSED_OR` (< p33), `NORMAL_OR` (p33–p66), `EXPANDED_OR` (> p66).

2. **Early Path Directional Efficiency ($F_2$)**:
   $$Efficiency_T = \frac{|Close_T - Open_{09:30}|}{OR_T} \in [0.0, 1.0]$$
   - Binned into:
     - `HIGH_EFF` ($\ge 0.70$): Unidirectional opening thrust.
     - `MODERATE_EFF` ($0.35 \le Efficiency_T < 0.70$).
     - `LOW_EFF` ($< 0.35$): Two-sided rotational opening chop.

3. **Early Volume Abnormality ($F_3$)**:
   $$RVol_T = \frac{\sum_{t=09:30}^{T} Volume_t}{\text{Baseline}_{20}(\sum_{t=09:30}^{T} Volume_t)}$$
   - High Volume (`HIGH_RVOL` $\ge 1.30$), Normal Volume (`NORMAL_RVOL` $0.80–1.30$), Low Volume (`LOW_RVOL` $< 0.80$).

4. **Early Directional Displacement ($F_4$)**:
   $$Displacement_T = Close_T - Open_{09:30}$$
   - `BULL_DRIVE` ($Displacement_T > 0$) vs `BEAR_DRIVE` ($Displacement_T < 0$).

---

## 4. Dependent Targets: Remaining-Session Persistence ($T+1 \to 15:55\text{ ET}$)

Measured strictly from the open of minute bar $T+1$ through the $15:55$ close:
1. **Remaining-Session Net Return ($Y_1$)**:
   $$Return_{rem} = Close_{15:55} - Open_{T+1}$$
2. **Remaining-Session Directional Efficiency ($Y_2$)**:
   $$Efficiency_{rem} = \frac{|Close_{15:55} - Open_{T+1}|}{High_{rem} - Low_{rem}} \in [0.0, 1.0]$$
3. **Directional Follow-Through Rate ($Y_3$)**:
   $$FollowThrough = \mathbb{I}\left(\text{Sign}(Return_{rem}) == \text{Sign}(Displacement_T)\right)$$
4. **Remaining-Session Clean Trend Day ($Y_4$)**:
   $$\text{Trend\_Day}_{rem} = \mathbb{I}\left(Range_{rem} \ge \text{Median}(Range_{rem}) \;\text{AND}\; Efficiency_{rem} \ge 0.60\right)$$

---

## 5. Promotion / Kill Criteria
- **Promote to Phase 2 (Monetization)**:
  1. Statistically significant increase in remaining-session efficiency ($Y_2$) or clean trend-day likelihood ($Y_4$) for high-efficiency / high-volume opening states relative to the unconditional baseline.
  2. Directional follow-through rate ($Y_3$) consistently and stably exceeds $53\%$ across IS, Validation, and OOS.
- **Kill Strategy 38 (C)**:
  - If early auction features do not reliably condition remaining session persistence, or if effects flip between IS, Validation, and OOS, the family is killed immediately at the Information Gate without attempting trade execution or parameter mining.
