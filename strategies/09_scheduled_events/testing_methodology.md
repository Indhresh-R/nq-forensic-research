# Testing Methodology — Scheduled Macro Events

## Causality card

```text
Information available at signal:
  t <= signal_time

Entry / measurement start:
  next bar open after signal (standard)

Outcome measurement:
  starts after entry

No future information:
  YES (audited in script design)

HIGH usage:
  Not used / independent of HIGH where stated
```

## Dataset

```text
Instrument: NQ futures (continuous 1m)
Source: Databento GLBX.MDP3 / project continuous parquet
Period: ~2010–2026 (see script loaders)

IS:         2010–2021
Validation: 2022–2024
OOS:        2025–2026 (report 2025 and 2026 separately when n allows)
```

## Hostile gates (program standard)

1. Pre-register / freeze definitions before scoring
2. No parameter sweep for promotion
3. Compare vs 50% and/or same-TOD unconditional baseline where relevant
4. Require multi-clock or multi-horizon stability for promotion
5. Year stability (2025/2026) when sample permits
6. Kill family on fail — no rescue stack

## Robustness checklist

- [ ] Alternate horizons
- [ ] Multiple clocks / years
- [ ] Costs / slippage (where economics claimed)
- [ ] Sample size floors
- [ ] Ambiguity / same-bar both-touch handling
- [ ] Overlap / clustering (especially HIGH clocks)
- [ ] Lookahead audit
