# Research Pivot — External Information for Direction

**Date:** 2026-09-05  
**Status:** ACTIVE  
**Supersedes for direction search:** OHLC-only intrinsic families (terminal kill)

## What we concluded

At 1m resolution and the horizons tested, these **do not** survive hostile validation as short-horizon **directional** engines:

| Source | Result |
|--------|--------|
| Momentum / serial dependence | killed |
| Mean reversion / extremes | killed |
| Failed moves / exhaustion | killed |
| Expansion → retracement | killed |
| Levels / VWAP / OR / structure | killed |
| ES confirmation | killed |
| Volume | killed |
| Multi-scale OHLC | killed |

What **does** survive:

| Source | Role |
|--------|------|
| Frozen HIGH (`vol_expansion_high`) | **Opportunity / activity timing only** |

## Architecture (locked)

```text
EXTERNAL INFORMATION
        │
        ▼
 DIRECTIONAL EDGE?  (prove WITHOUT HIGH)
        │
  YES ──┴── NO → KILL mechanism
        │
        ▼
 FROZEN HIGH GATE  (timing enhancer only)
        │
 HIGH → ARM / LOW → WAIT
        │
        ▼
 EXECUTABLE TRADE (~1–2/day goal later)
```

Rules:

1. Direction must prove itself independently first.
2. Only then test whether frozen HIGH improves timing/economics.
3. Do **not** invent Family #6 as another NQ candle transform.
4. One external mechanism at a time. No shotgun of 20 variables.

## Candidate external mechanisms (queue)

1. **Options positioning / dealer hedging** ← first choice  
2. Scheduled information events (CPI, NFP, FOMC, …)  
3. Cross-market beyond ES (VIX, yields, DXY, SOX, …) — one at a time

## Options first — but with an honest data caveat

### Available in `d:\NQ` (prior work)

- QQQ options **daily EOD** chain (2011–2025), causal features already built  
  (`qqq_causal_options_features.parquet`, positioning-change features, GEX proxies)
- Prior hostile audits already exist under `d:\NQ\nq_data\research\`:
  - `options_volatility_regime` — EOD options **do not** forecast next-day NQ opportunity/vol beyond past NQ vol
  - `options_positioning_changes` — some **range/vol** associations; **no stable directional** edge on next-day return
  - `options_incremental_value_audit` — **Grade D**: no incremental value over price/vol baseline for vol forecasting

### Causality constraint (non-negotiable)

Daily EOD options (≈16:15 ET) are only legal for decisions **after** they become available — typically **next session** (overnight / next RTH), not same-day intraday clocks.

**We will not** use same-day EOD options fields as if they were known at 09:30–15:30.

### What is still worth testing under NQ-2 protocol

Not a blind redo of “options predict tomorrow’s range.”

Precise question for Family E1:

> **Does a causally available options-derived state (prior session EOD, or true intraday if OPRA permits) create an asymmetric NQ forward return distribution at our decision clocks — independent of HIGH?**

Pre-register before scoring:

- Information set known at T (lag rule written down)
- Small frozen feature set (e.g. prior-day GEX sign/tercile, PC OI imbalance extreme, OI buildup z) — no sweep
- Outcomes from T+1; horizons 5–60m; IS→Val→OOS→2025/2026
- Cont vs fade / long vs short as appropriate to the hypothesis
- Multi-clock + year stability required
- Kill if ~50% / unstable

If EOD-lagged options also fail **direction** under this protocol: kill options-EOD for direction; do **not** rescue with more feature engineering. Next queue item = scheduled events (or true intraday options if data quality allows).

## Frozen (unchanged)

- HIGH / ARM = `vol_expansion_high` (`artifacts/frozen_opportunity_gate.md`)
- Do not refit HIGH terciles

## Stop rules

- A = multi-clock year-stable directional asymmetry → only then HIGH timing test  
- B/C = kill mechanism; move to next external family  
- No combining dead mechanisms into a “stack”

## E1 result (2026-09-05)

Prior-day EOD options → next-day intraday direction: **C** (kill=True).

Kill EOD-options-for-direction. Next: scheduled information events.

## E2 result (2026-09-05)

Scheduled information events → intraday direction: **C** (kill=True).
ISM unavailable in calendar source.
