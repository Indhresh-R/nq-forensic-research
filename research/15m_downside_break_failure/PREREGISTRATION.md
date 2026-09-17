# 15m Downside Break Failure Study

**Status:** frozen before outcome review. This is an explanatory event study, not a trading strategy.

## Question

Do confirmed 15m breaks below 20-bar support subsequently fail in a way that is distinct from ordinary 15m downward moves of comparable, pre-event-normalized size?

## Frozen event and control definitions

- Markets/splits: continuous NQ and ES futures, Globex sessions, IS 2010–2021, Validation 2022–2024, OOS 2025–2026.
- Build complete 15m bars from 18:00 New York and calculate a causal 20-bar ATR using only prior bars.
- **Break event:** prior 15m close is at/above the prior 20-bar support and current close is below it. Use the first such event per session.
- **Control event:** a 15m down-close that does not break the prior 20-bar support. Use the first qualifying control per session and normalized move band.
- Normalized down move: `(open - close) / prior_20_bar_ATR`; bands are fixed: `[0, .5)`, `[.5, 1)`, `[1, 1.5)`, `[1.5, infinity)`.
- All forward measurements begin at the next available 1m open. The same 60m path is used for breaks and controls.

## Frozen measurements

For a hypothetical long fade, at 1/5/15/30/60m measure return, MFE, and MAE. For break events also measure time to first 1m close back above broken support, fraction of the first 60 minutes spent below support, maximum recovery above support, and the return distribution (median, 10th/90th percentiles, probability positive).

## Decision gate

The failure observation is retained only if its positive fade return and/or recovery behavior exceeds same-band controls in both NQ and ES with stable IS/Validation/OOS signs. This study cannot authorize an execution rule; any subsequent fade trade requires a separate preregistration with cost, entry, risk, and exit frozen before testing.
