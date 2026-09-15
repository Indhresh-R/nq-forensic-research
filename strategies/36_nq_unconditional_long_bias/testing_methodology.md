# Testing Methodology: Strategy 36

## Causality Card
```text
Information available at signal: Time of Day clock only (no price-level filter)
Entry: Open of minute bar T+1
Exit: Close of minute bar T+H or 15:55 ET
Same-bar ambiguity: Adverse (stop first for Mode B)
Lookahead: Strictly prohibited
```

## Methodology & Attribution Framework
1. **Directional Comparison**: Evaluate Long vs Short pairwise at each horizon (5m, 15m, 30m, 60m, Session Close) and clock.
2. **Cost Sensitivity**: Measure net points across 0.0 to 2.0 point friction to determine the break-even friction threshold.
3. **Passive Benchmark Attribution**:
   - Compare active Long equity curve against passive RTH Buy-and-Hold and continuous 24-hour holding.
   - Compute Annualized Sharpe Ratio, Max Drawdown, and Cumulative Fee Drag.
   - Verify whether the active strategy generates Alpha or merely captures diluted Beta while paying excessive fees.
