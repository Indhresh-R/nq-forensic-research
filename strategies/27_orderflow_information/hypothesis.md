# Hypothesis

## Market behavior under test

When **abnormal volume-pressure proxies** (OHLCV-derived; **not** observed order flow) appear on ES (then NQ), short-horizon returns / RV over the next **1–60 minutes** may change conditionally beyond ordinary volatility, TOD, and recent return.

## Economic / mechanical rationale

Literature links true order flow to short-run price impact. We only have OHLCV. Phase 0–1 therefore test whether **cheap proxies** carry any information — with mandatory checks that proxies are not merely relabeled returns.

## Primary research question

> Do abnormal **volume-pressure proxies** contain incremental information about the next 1–60 minutes after controlling for volatility, TOD, and recent return — and after orthogonalizing signed proxies to contemporaneous return/range?

## Explicit non-goals / naming

- No strategy, thresholds, optimization, Sharpe hunting in Phase 0–1.
- **Do not** call OHLCV proxies “order flow.”
- No Level-3 until cheap proxies fail for a documented missing-data reason.

## Success / failure criteria

| Result | Path |
|--------|------|
| Residual signed proxy or unsigned activity shows stable descriptive signal beyond raw OHLCV | Consider narrow Phase 2 ΔR² |
| Signed proxy collapses to return transform; activity only = vol clustering | Do not claim order-flow edge; optional RV incremental test or close → Strategy 28 |
