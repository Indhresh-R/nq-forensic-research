# Strategy 39: Hypothesis -- Multi-Day Volatility Compression

## 1. Context & Motivation
Following the systematic invalidation of:
1. **Micro-Pattern Consolidation (Strategy 35)**: Bull and Bear Flag consolidation patterns do not possess alpha; they are merely proxies for underlying drift or post-impulse continuation.
2. **Unconditional Directional Long Drift (Strategy 36)**: Intraday timing bleeds transaction friction; passive exposure strictly dominates active timing.
3. **Pre-Market Overnight Inventory (Strategy 37)**: Overnight inventory positioning and gap extensions fail to predict subsequent RTH directional continuation (50.8% continuation, completely random).
4. **Opening Auction Behavior (Strategy 38)**: The first 15 minutes of RTH price action (early efficiency and range) fail to separate trend days from chop days (spread of +0.011 in remaining efficiency).

These results confirm that **local price structure has virtually zero predictive information about upcoming RTH persistence**.

## 2. The Slow-Moving Volatility State Hypothesis
Instead of looking at local candle structure or intraday inventory, Strategy 39 investigates **slow-moving multi-day volatility compression**.

Markets are known to alternate between periods of low volatility (compression/consolidation) and high volatility (expansion/trend). Classical technical literature posits that multi-day compression (e.g., NR7, multi-day contraction) builds energy that resolves in large directional trend days.

### The Formal Hypothesis:
> Prior multi-day range compression (measured by trailing range percentiles, NR4/NR7 patterns, contracting day runs, and compression duration known prior to 09:30 ET) alters the probability distribution of the subsequent RTH session by increasing the likelihood of range expansion ($\text{Range} / \text{ATR}_{20} > 1.25$) and directional persistence ($\text{Efficiency} \ge 0.60$).

## 3. Decoupling "WHEN" from "WHICH WAY"
Volatility compression is inherently non-directional. A multi-day squeeze does not dictate whether the breakout will occur to the upside or downside. Therefore, Strategy 39 evaluates the **expansion and persistence distribution** ("WHEN"), completely separate from directional polarity ("WHICH WAY").
