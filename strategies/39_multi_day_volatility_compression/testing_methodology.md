# Strategy 39: Testing Methodology -- Multi-Day Volatility Compression

## 1. Dataset & Coverage
- Asset: Continuous E-mini Nasdaq-100 Futures (NQ) 1-minute parquet (`data/nq_1m_continuous.parquet`).
- Period: 2010-01-01 through 2026-08 (16+ years).
- Evaluates all valid, complete RTH trading sessions (minimum 300 minutes between 09:30 and 15:55 ET).
- Warm-up period: Initial 252 sessions required for rolling percentile computations (analysis period starts from ~2011).

## 2. Chronological Partitions
To maintain absolute discipline against hindsight bias:
1. **In-Sample (IS)**: 2011-01-01 to 2021-12-31 (11 years, ~2,700 sessions)
2. **Validation (VAL)**: 2022-01-01 to 2024-12-31 (3 years, ~750 sessions)
3. **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (~400 sessions, tracked as 2025 and 2026)

## 3. Hostile Testing Protocol
The Information Gate operates on 6 strict requirements:
1. **Statistical Significance**: Shift in distribution between compressed states and normal/expanded states must show $p < 0.01$ (Mann-Whitney U-test / Permutation test) In-Sample.
2. **Temporal Stability**: Any positive lift observed In-Sample must survive across Validation (2022–2024).
3. **OOS Robustness**: Must maintain positive lift in Out-of-Sample (2025–2026).
4. **Economic Magnitude**: The effect must be materially distinct from noise (e.g. trend-day rate lift $\ge +10$ percentage points or normalized range $\ge 1.20\times$).
5. **Monotonicity Across Bins**: Progression across quintiles/tertiles must be monotonic or structurally coherent; single cherry-picked cutoff anomalies fail.
6. **Volatility Normalization**: Must be confirmed in ATR-normalized units to prove that it is not an artifact of entering a higher macro-volatility regime.

If any of these conditions fail, **Strategy 39 is KILLED at the Information Gate (Verdict C)**.
