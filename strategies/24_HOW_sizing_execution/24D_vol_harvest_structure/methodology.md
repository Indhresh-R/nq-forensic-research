# Methodology — 24D Vol-Harvest Structure

## Causality card

```text
Information at T:
  - NQ bars <= T
  - Strategy-12 frozen rng_psr terciles
  - psr (prior session range) known from completed prior session

Entry:
  Anchor = next bar OPEN after T
  Breakout levels frozen at signal time from anchor + causal psr
  Side = first subsequent touch of upper or lower (path-determined, not predicted)

Forbidden:
  - Choosing side from HIGH / vol / prior return
  - Refitting BO_FRAC / R / width multipliers on Val/OOS
  - Same-bar dual touch counted as a clean win (skip / NaN)
```

## Frozen structure (registered BEFORE performance look)

```text
BO_FRAC   = 0.10          # breakout distance = BO_FRAC * psr
STOP_R    = 1.0           # stop distance = STOP_R * breakout_dist
TGT_R     = 1.5           # target distance = TGT_R * breakout_dist
WIDTH_HIGH = 1.50         # multiply stop+target distances when HIGH (regime_aware)
WIDTH_NON  = 1.00         # non-HIGH multiplier
MAX_HOLD   = 60           # bars after entry; time-stop at that bar's close
COST_RT    = 1.0          # mid points, applied once per filled trade
SIZE       = 1.0          # unit size (structure test; not 24A sizing)
```

Breakout search window: up to `MAX_HOLD` bars after anchor for a fill; if no touch, no trade.

## Policies (same breakout events; compare risk metrics)

| Policy | Who trades | Stop/target width |
|--------|------------|-------------------|
| `uncond_base` | All regimes | WIDTH = 1.00 |
| `uncond_wide` | All regimes | WIDTH = 1.50 (always) |
| `regime_width` | All regimes | WIDTH = 1.50 if HIGH else 1.00 |
| `high_only_base` | HIGH only | WIDTH = 1.00 |

Primary contrast: `regime_width` vs `uncond_base`. Secondary: `high_only_base` vs `uncond_base`
(participation filter). `uncond_wide` checks that any lift is not merely "always wider."

## Path rules

1. Upper = anchor + BO_FRAC*psr; lower = anchor − BO_FRAC*psr
2. Scan bars after anchor in order. First bar with `high >= upper` → long @ upper
   (if gap open above upper, fill at open). First with `low <= lower` → short @ lower.
3. Same bar both sides touched → **skip** (ambiguity)
4. After entry, bar-by-bar: stop and target. Same-bar both → **stop first** (hostile)
5. If neither by MAX_HOLD → exit at close of hold bar

## Metrics

Daily PnL Sharpe / Sortino / max DD (one trade per session_date × session = earliest
eligible offset that fills under the policy). Bootstrap 90% CI on ΔSharpe / ΔSortino vs
`uncond_base`. Also: win rate, E[pts], MAE/MFE by regime (diagnostic).

## Direction audit

Report fill counts and mean PnL separately for long-breakout vs short-breakout fills
under each policy. Promotion requires both sides participate with no exclusive one-sided
expectancy.

## Splits / stage gate

IS 2010–2021 first. Val/OOS locked until go-ahead. Default `--stage IS`.

## Clustering

Risk metrics: earliest eligible offset per session_date × session (among offsets that
produce a fill for that policy).
