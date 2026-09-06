# Hypothesis — COT Positioning under Strategy-12 HIGH

## Market behavior under test

Weekly CFTC Traders-in-Financial-Futures (TFF) **net positioning** for Nasdaq-100
futures — especially Leveraged Funds and Asset Managers — at **statistical
extremes**, once publicly released, carries incremental signed information about
NQ forward returns **inside** Strategy 12's elevated activity regime (`HIGH`).

```text
COT Tuesday snapshot → Friday public release → next session+
        → extreme net z (lev / asset-mgr)
        → Strategy-12 HIGH clocks
        → Does NQ forward sign prefer the pre-registered side?
```

## Why this is allowed under direction_resolution.md

Strategies 13–22 killed **price/state** resolvers. This dossier uses an
**external causal information source** (CFTC positioning), the only re-open path
listed in `research_framework/direction_resolution.md`.

## Economic / mechanical rationale (pre-registered sides)

| Signal | Side rule (frozen) | Rationale |
|--------|--------------------|-----------|
| `lev_fade` | Extreme lev **long** → short NQ; extreme lev **short** → long NQ | Crowded speculative leverage mean-reverts |
| `am_follow` | Extreme AM **long** → long NQ; extreme AM **short** → short NQ | Asset managers treated as slower “real-money” flow |

No other mappings. No IS Sharpe / PF maximization to pick thresholds or sides.

## What would count as success

- Causal lag respected (no Tue–Fri lookahead)
- Frozen decile extremes only
- **Incremental lift** of HIGH+COT vs (1) unconditional same-clock and (2) HIGH alone
- Same-sign lift IS → Val → OOS; multi-clock stability; 2025/2026 when n allows
- Verdict per `verdict_rubric.md` (A vs A\* check before any executable claim)

## What would count as failure

- HIGH+COT ≈ 50% / ≈ ALL+COT / ≈ HIGH-long (no incremental lift)
- Soft single-clock only / Val or OOS flips
- Contamination of the Friday-lag rule → **D**
- Family multi-comparison: one soft hit in 23A alone does not promote family 23
