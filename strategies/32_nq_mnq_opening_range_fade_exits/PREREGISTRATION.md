# NQ/MNQ opening-range fade -- exit-structure follow-up

Frozen 2026-09-14, before this pass was run.  This is a separately dated
follow-up to strategy 31.  It reuses that strategy's opening-range entry
unchanged; only the exit structure varies.  Cost is **$2.00 round trip per
1 MNQ** and all account gates, dates, session hours, fill convention and
one-trade-per-session convention are inherited from strategy 31.

## Frozen entry signal (verbatim from strategy 31)

| Opening range | OR is 09:30--09:59 high/low. First close back inside it within 10 minutes after a close outside it; fade toward midpoint at next open. Stop 87.5 points; target is the smaller of midpoint distance and 87.5 points. |

The quoted entry definition above is character-for-character the Opening
range rule from `strategies/31_nq_mnq_mean_reversion_fade/PREREGISTRATION.md`.
For this follow-up, the final target clause is superseded only by the five
pre-registered exits below.  The frozen stop remains 87.5 MNQ points ($175).

## Fixed exits

1. Fixed 1R: target 87.5 points ($175), no midpoint cap.
2. Fixed 1.5R: target 131.25 points ($262.50), no midpoint cap.  Prices and
   levels are retained as decimal points; no tick rounding is applied because
   131.25 is exactly on the MNQ 0.25-point tick grid.
3. Fixed 2R: target 175 points ($350), no midpoint cap.
4. Partial: economically split one MNQ into two 0.5-MNQ legs: one exits at
   the original OR midpoint and one at 1.5R.  This is an analytical fractional
   execution convention solely to express the requested 50/50 exit; it is not
   directly executable with a single indivisible MNQ contract.
5. Time-boxed 1R: target 87.5 points; if neither stop nor target is reached
   in **30 minutes** from the entry bar, exit at that 30th bar's close.

No trailing stops, re-entries, exit substitutions, or parameter changes are
permitted.  Intrabar stop/target collisions are stop-first.  A midpoint that
is already on the adverse side of entry is treated as an immediate midpoint
leg exit at entry, preventing a hindsight fill at a previously crossed level.

## Selection and account gates

Train: 2010--2018; Inner Validation: 2019--2021; Validation: 2022--2024;
OOS: 2025--2026.  Each candidate requires at least 100 Train and 50 Inner
Validation trades, a maximum realized stop no greater than $200, and realized
win rate at least `(1 + 1500/(N*175)) / (k+1)`, where `N` is combined
Train+Inner trade count and `k` is its realized net payoff ratio.  Eligible
candidates are ranked by combined profit factor, then lower single-best-day
profit concentration.  Validation account gates are $600 daily loss, $1,000
EOD trailing loss, $1,500 profit target, and no single day over 50% of final
Validation profit.  OOS is evaluated only after a Validation pass.
