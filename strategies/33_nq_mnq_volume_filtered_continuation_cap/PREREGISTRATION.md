# NQ/MNQ volume-filtered continuation -- hard-capped stop

Frozen 2026-09-14 before execution.  MNQ uses $2 per index point and a
**$2.00 round-trip cost** (the original report's fixed 1.0 NQ-index-point
round-trip cost, scaled from $20/point NQ to $2/point MNQ).  Signal timing,
one-trade-per-session, next-one-minute-open fills, 15:55 ET time exit, and
stop-first intrabar collisions are unchanged.

## Frozen entry signal (verbatim source rules)

- IB: 09:30–10:29 ET; first qualifying five-minute close starts at 10:34.
- Entry: next one-minute open. One trade maximum per session.

High relative-volume, early breakouts are the subset where the signal-bar
five-minute volume is at or above the upper Train (2010--2018) tertile of
`signal-bar volume / (IB volume / 12)`, and the completed signal bar closes
no later than 11:30 ET.  The underlying first breakout is the first completed
five-minute close at least one tick outside the IB: `>= IB high + 1 tick` for
a long or `<= IB low - 1 tick` for a short.  This is the exact frozen logic
implemented in strategy 30's `run_initial_balance_breakout.py` and
`run_phase6_continuation_matrix.py`; the threshold is computed only from
Train before any candidate is evaluated.

## Fixed candidates

1. Fixed 75-point ($150) stop and 1R target.
2. Fixed 75-point ($150) stop and 2R target.
3. Fixed 100-point ($200) stop and 1.5R target.
4. Fixed 100-point ($200) stop and 2R target.
5. Skip signals for which the original 0.50×IB-width stop exceeds 100
   points ($200); retained trades use that original 0.50×IB-width stop and
   its original 2R target.

No other variants are permitted.  Train (2010--2018), Inner Validation
(2019--2021), Validation (2022--2024), and OOS (2025--available 2026) are
fixed.  Selection uses only Train+Inner: at least 100/50 trades, stop at or
below $200, and win rate at least `(1 + 1500/(N*stop_dollars))/(k+1)`, ranked
by profit factor then lower best-day concentration.  Validation must pass
$600 daily loss, $1,000 EOD trailing drawdown, $1,500 profit, and 50%
single-day consistency; OOS runs only after that pass.
