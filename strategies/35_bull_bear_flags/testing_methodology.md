# Testing Methodology: Strategy 35

## 1. Causality Card
```text
Information available at signal: completed 5-minute close T
Entry: open of minute bar T+1
Outcome: minute-by-minute tracking through 15:55 ET
Same-bar ambiguity: adverse (stop first)
Future information: strictly prohibited
```

## 2. Chronological Splits
- **In-Sample (Train)**: 2010-01-01 to 2021-12-31
- **Validation**: 2022-01-01 to 2024-12-31
- **Out-of-Sample (OOS)**: 2025-01-01 to 2026-08 (split 2025 and 2026)

## 3. Hostile Audit Verification
- Signal uses only $t \le T$
- Outcomes start at next open
- Thresholds frozen on IS only
- No grid search for promoted rule
- Val and OOS scored once after freeze
- 2025 / 2026 separated
- Multi-asset check: NQ and ES
- Baseline comparisons:
  - Bull Flags vs Bear Flags (directional asymmetry)
  - Flag Breakouts vs Unconditional session drift
  - Flag Breakouts vs Pure Impulse (C6 control)
- Failure mode documented in `conclusion.md`
