# Strategy 41: Testing Methodology -- Volatility Regime × Signal Economics

## 1. Dataset & Coverage
- Asset: Continuous E-mini Nasdaq-100 Futures (NQ) 1-minute data (`data/nq_1m_continuous.parquet`).
- Period: 2010 to 2026 (post 20-day ATR warmup, ~3,450 sessions).
- Transaction Friction: Fixed at 1.0 point round-trip ($20.00) per contract.

## 2. Chronological Partitions
1. **In-Sample (IS)**: 2011-01-01 to 2021-12-31 (~2,100 sessions)
2. **Validation (VAL)**: 2022-01-01 to 2024-12-31 (~750 sessions)
3. **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (split into 2025 and 2026)

## 3. Evaluation Protocol & Hostile Criteria
For each benchmark signal and across the signal-agnostic capacity scan:
1. **Capacity Criteria**: Does available price excursion scale faster than friction, lowering friction drag percentage from $> 4\%$ in low vol to $< 1.5\%$ in high vol?
2. **Economic Survivability Criteria**:
   - Does High/Extreme Volatility shift net expectancy from negative to positive ($E_{net} > 0$)?
   - Does Profit Factor net of friction exceed 1.15 in high volatility while remaining sub-1.0 in low volatility?
   - Does the net expectancy improvement persist across Validation (2022–2024) and Out-of-Sample (2025–2026)?

If net expectancy remains negative across all volatility tiers, or if higher volatility merely scales loss sizes proportionally with win sizes, **Strategy 41 is KILLED as an economic trade filter (Verdict C)**.
