# Testing Methodology — Multi-session direction

## Causality card

```text
Information available at signal: t <= T (intra-session)
Entry: next bar open
Outcome: signed points to exit within same session
No future information: YES
```

## Splits

IS 2010–2021 / Validation 2022–2024 / OOS 2025–2026 (frozen).

## Baselines

- Unconditional same-TOD hold
- Blind follow / fade without HIGH gate
- Report Δ vs baseline; do not promote HIGH-only cells if blind is dead and HIGH was fit on direction

## Robustness

Multi-clock (≥2 offsets), multi-horizon report, year split 2025/2026, cost stress (round-trip ticks).
