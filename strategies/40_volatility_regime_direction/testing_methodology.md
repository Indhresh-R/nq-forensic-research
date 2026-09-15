# Strategy 40: Testing Methodology -- Volatility Persistence → Directional Distribution

## 1. Dataset & Partitions
- **Asset**: Continuous E-mini Nasdaq-100 Futures (NQ) 1-minute data (`data/nq_1m_continuous.parquet`).
- **Coverage**: 2010 to 2026 (post 20-day ATR warmup, ~3,450 complete sessions).
- **Frozen Partitions**:
  - **In-Sample (IS)**: 2010-01-01 to 2021-12-31 (~2,300 sessions)
  - **Validation**: 2022-01-01 to 2024-12-31 (~750 sessions)
  - **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (split into 2025 and 2026)

## 2. Statistical Protocol
We measure whether high-volatility states condition directional odds away from the baseline:
1. **Directional Polarity**: Is $P(\text{Up Day})$ significantly different from unconditional baseline ($p < 0.01$ binomial test)?
2. **Continuation Rate**: Is $P(\text{Same Sign})$ significantly different from 50.0%?
3. **Tail Asymmetry**: Does $P(\text{Large Up Move}) - P(\text{Large Down Move})$ deviate significantly from zero?
4. **Excursion Asymmetry**: Does $\text{Mean(Upside Excursion)} - \text{Mean(Downside Excursion)}$ deviate from baseline?

## 3. Hostile Gates
- **Directional Alpha Gate**: Requires $\ge \pm 5$ percentage points departure in continuation rate or $\ge 10$ percentage points in tail asymmetry, consistent across IS, Validation, and OOS.
- **Scientific Null Verdict**: If continuation rate remains between 48% and 52% and tail expansion is symmetric, Strategy 40 is killed as a directional signal, and the result is recorded as: **"Volatility is predictable; Direction is not."**
