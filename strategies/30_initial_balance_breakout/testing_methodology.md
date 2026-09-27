# Testing methodology

## Causality card

```text
Information available at signal: completed five-minute close only
Entry: following one-minute open
Outcome: starts at entry
Same-bar ambiguity: adverse (stop first)
Future information: none
```

Chronological splits are frozen by repository standard: 2010–2021 discovery, 2022–2024 validation, 2025–2026 OOS. A positive discovery result is insufficient. The baseline must be positive after costs in both Validation and OOS before testing predeclared robustness variations.

## Phase 2 — risk geometry

The entry signal remains unchanged. The predeclared grid compares the opposite-IB stop with fixed stops of 0.25, 0.50, 0.75, and 1.00 × IB width, and targets of 0.75, 1.00, 1.50, and 2.00R. Selection is Discovery-only. Validation/OOS results are confirmation only.

## Phase 3 — standalone causal filters

The unchanged opposite-IB/1R baseline is filtered one condition at a time: risk caps, time of day, RTH-VWAP alignment, signal-candle strength, and IB width relative to the prior 20 sessions. Train is 2010–2018 and inner validation is 2019–2021. Later periods are not selection inputs; no filter combinations are searched.
