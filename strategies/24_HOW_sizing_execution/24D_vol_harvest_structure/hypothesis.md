# Hypothesis — 24D Non-Directional Vol-Harvest Structure

## Market behavior under test

Strategy 12's `HIGH` anticipates **larger subsequent unsigned moves**. A genuinely
direction-agnostic structure — first breakout either side, with **symmetric** stop and
target — may monetize that activity differential via **stop/target width** (and optional
HIGH-only participation), without resolving sign.

```text
Strategy-12 HIGH at T (causal)
  → next open = anchor
  → symmetric breakout ± BO_FRAC * psr
  → first touch sets side (long or short)
  → symmetric stop / target (width may depend on HIGH vs non-HIGH)
  → Does regime-aware width (or HIGH-only filter) beat unconditional width
     on expectancy / Sharpe / Sortino / DD?
```

## Why this is not 24A

24A asked whether **position sizing** helps a **coin-flip** book. Null there is nearly
mechanical under proportional costs. 24D asks whether a **payoff structure that can
capture larger excursions** (wider targets / less premature stop-out during expected
expansion) harvests HIGH's known activity signal. Separate mechanism; 24A null does
**not** imply 24D null.

## Out of scope

- Predicting which side breaks first
- Promoting any net directional bet
- Mining BO_FRAC / R-multiples / HIGH width on forward Sharpe

## Frozen economic rationale

1. After a small symmetric breakout, continuation path length is larger in HIGH on average
   (Strategy 12 activity claim).
2. Wider stop+target in HIGH reduces noise stop-outs and lets targets sit where expansion
   actually reaches; tighter in non-HIGH matches quieter paths.
3. Success = positive risk-adjusted expectancy vs unconditional width baseline, with
   long-breakout and short-breakout books both contributing (no one-sided smuggle).

## Success / failure (graduated)

| Grade | Meaning |
|-------|---------|
| Strong IS | Regime-aware (or HIGH-only) beats unconditional on Sharpe **and** Sortino; bootstrap CI excludes 0; multi-session or multi-H; both sides participate |
| Partial | DD or hit-rate structure improves; Sharpe soft / CI includes 0 |
| Null | No monetizable structure from HIGH-aware width / filter under freeze |

## Failure modes

- Breakout+symmetric R ≈ cost-drag / random-walk null in all regimes
- HIGH-aware width worse than fixed width
- Only one breakout side carries the book → directional smuggle → flag, not promote
- Lookahead in HIGH or breakout levels → **D**
