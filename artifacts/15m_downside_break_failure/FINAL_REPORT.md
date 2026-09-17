# 15m Downside Break Failure Study

**Verdict: C — the apparent downside-break failure does not survive the matched-move baseline. No fade strategy is authorized.**

## What was tested

This explanatory study retained the causal 15m first support-break event and compared its subsequent 1m path with first-in-session ordinary 15m down-closes that did **not** break 20-bar support. Both were stratified by the frozen causal displacement-to-prior-20-bar-ATR bands. It measured hypothetical long-fade returns, distributions, excursions, and recovery behavior—without a trading rule, costs, stop, or target.

## Baseline result

The original information study correctly found that short-break direction-signed returns were negative: prices often rose after a support break. But that observation alone does not establish S/R-specific reversal information.

After matching the size of the preceding downward 15m move, the break-minus-control fade-return advantage was not stable by market, split, or magnitude band. It changes sign repeatedly. In particular, NQ OOS results that look favorable in the unconditional aggregate are frequently no better than ordinary same-sized down moves:

| NQ OOS, hypothetical long fade | Break | Control | Break − control |
| --- | ---: | ---: | ---: |
| 30m, all bands pooled | +0.71 | +1.38 | -0.67 |
| 60m, all bands pooled | +2.83 | +2.79 | +0.05 |

The pooled values are descriptive; the decision uses the frozen banded comparison. Those banded cells do not retain a same-signed NQ+ES IS/Validation/OOS advantage.

## Path/risk reading

Break events do recover above broken support, but not cleanly enough to imply a trade:

- First close back above support occurs after about **12.6–15.2 minutes** on average across market/split cells.
- Price remains below support for roughly **65–70%** of the first hour after a break.
- At 60m, fade MFE and MAE are of similar magnitude (for example NQ OOS: +43.28 MFE vs -47.46 MAE). The average bounce conceals a wide, adverse distribution.

That supports the alternative explanation: the observed bounce is largely ordinary post-down-move mean reversion and volatile path dispersion, not a confirmed support-break failure effect with standalone economics.

## Decision

Retire the lead. Strategy 42 remains **KILLED — generic timeframe/S/R continuation**. The proposed downside-break-fade mechanism fails at the information/baseline gate, so no entry-rule optimization or strategy backtest will be run.

## Audit files

- `events.csv` — every break/control event × horizon.
- `summary.csv` — distribution, excursion, and recovery metrics.
- `break_minus_control.csv` — matched band differences used for the decision.
- `research/15m_downside_break_failure/PREREGISTRATION.md` — frozen design.
