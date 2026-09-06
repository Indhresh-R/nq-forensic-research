# Hypothesis — 24A Volatility-Scaled Position Sizing

## Market behavior under test

Strategy 12 detects an elevated future **activity/path** regime (`HIGH`) without resolving sign.
Given that, does **position sizing** — inverse to causal realized vol at entry, optionally
scaled further by HIGH vs non-HIGH — improve **risk-adjusted** outcomes (Sharpe, Sortino,
max drawdown) versus fixed unit size, for a **direction-agnostic** baseline entry?

```text
Strategy-12 state at T (causal) → HIGH / non-HIGH
        → next-bar open entry
        → coin-flip side (frozen PRNG; no sign claim)
        → hold H minutes
        → size = f(realized_vol_T [, regime])
        → better Sharpe/Sortino/DD than size=1?
```

## Why this is allowed

`direction_resolution.md` lists **HOW** (sizing / stops / holding conditional on Strategy 12
WHEN) as the next honest branch after external family 23 closed. This ticket does **not**
attempt WHICH-WAY.

## What is explicitly out of scope

- Predicting long vs short from HIGH, vol, or any other feature
- Promoting a directional edge from a one-sided book
- Mining size caps / lookbacks / HIGH multipliers on forward Sharpe

## Frozen economic rationale (pre-registered)

1. Inverse-vol sizing is a standard risk-equalization rule: smaller size when local realized
   vol is high, larger when quiet — independent of sign.
2. HIGH anticipates **larger subsequent unsigned moves**. A HIGH-aware downsize
   (`s_HIGH < s_nonHIGH`) may further stabilize risk if inv-vol alone under-reacts to the
   regime label.
3. Success is risk-adjustment / drawdown control under a zero-edge entry — **not** raw PnL
   or win rate.

## What would count as success (graduated; not binary promote/kill)

| Grade | Meaning for 24A |
|-------|-----------------|
| Strong IS support | Inv-vol and/or HIGH-aware sizing beat fixed on Sharpe **and** Sortino with bootstrap CI excluding 0; same-sign in long-only and short-only audit books; multi-session or multi-H stability |
| Partial / B-like | Improvement on DD or one risk metric only; unstable across sessions; CI includes 0 |
| Null | No reliable risk-metric lift vs fixed; sizing irrelevant under this entry |

Even a partial result is useful: document gradations; do not force a tradeable promote.

## What would count as failure / contamination

- Any rule that sizes by predicted sign → out of scope (**flag**, do not build)
- Lookahead in vol or HIGH (must use Strategy-12 frozen `rng_psr` p66 at `t <= T`)
- Refitting vol lookback / clips / HIGH multipliers on Val/OOS
- Claiming direction from coin-flip or one-sided leftover
