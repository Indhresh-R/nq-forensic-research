# Baseline improvement test — pre-registration (2026-09-14)

This is a single-pass confirmatory test of the frozen NQ Initial Balance
breakout baseline.  This file was written before executing any candidate.
No Validation or OOS result may be used to select, replace, or reparameterize
a candidate.

## Step 0 — locked data gates

- **Train:** 2010-01-01 through 2018-12-31.
- **Inner Validation:** 2019-01-01 through 2021-12-31.
- **Validation:** 2022-01-01 through 2024-12-31.
- **OOS:** 2025-01-01 through 2026-12-31 (available data only; the supplied
  continuous series ends partway through 2026).
- **Instrument:** continuous NQ futures, one-minute OHLCV data supplied in
  `data/nq_1m_continuous.parquet`.
- **Session:** New York regular trading hours, 09:30–15:55 ET.  The IB is
  09:30–10:29. Incomplete sessions and early closes are excluded.
- **Execution and costs:** first qualifying 5-minute close, next 1-minute
  open entry, one trade per session, 15:55-open time exit, adverse stop-first
  resolution of same-minute stop/target collisions, and **1.00 NQ index point
  round-trip cost**.  Point value is $20 per index point per contract.

## Step 1 — fixed candidate list

All candidates retain the baseline signal: first 5-minute close at least one
tick beyond the IB high/low, from 10:34 through 15:29; next-minute-open entry;
one trade per day; and the locked execution assumptions above.

1. **Baseline control** — opposite-IB stop and 1R target, unchanged.
2. **Half-IB stop** — stop is 0.50 × IB width from entry in the adverse
   direction; target is 1.00 × that new stop distance (1R).
3. **1.5R target** — opposite-IB stop unchanged; target is 1.50 × actual
   entry-to-stop risk.
4. **Early-breakout filter** — opposite-IB stop and 1R target unchanged; take
   only signals whose completed 5-minute signal bar closes no later than 11:59
   ET.
5. **Half-IB stop + early-breakout filter** — exactly #2 plus exactly #4.

No other candidates, parameter values, filters, or combinations are permitted
in this pass.

## Step 3 — selection rule, fixed before Step 4

Rank all five variants by **combined Train + Inner Validation profit factor**,
provided each has at least 100 trades in Train and 50 in Inner Validation.
Break ties by combined average net points per trade, then by greater combined
trade count. Select exactly the highest-ranked eligible variant. If none is
eligible, select no candidate and end the pass.

## Step 4–5 confirmation rules, fixed before results

The selected variant improves the baseline at a confirmation gate only if its
average net points per trade is strictly greater than the baseline's at that
same gate, its profit factor is greater than 1.00, and its trade count is at
least 100 on Validation or 80 on OOS. A Validation failure rejects the variant
and stops the pass. OOS is run only after Validation passes; an OOS failure
rejects the variant and stops the pass. No rejected candidate will be retested
in this research pass.
