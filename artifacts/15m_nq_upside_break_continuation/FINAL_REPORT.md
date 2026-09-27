# NQ 15m Upside Break Continuation Information Study

**Verdict: C — resistance-break status adds no stable continuation information beyond a matched ordinary NQ up move. The 15m S/R branch is closed.**

## Result

The apparent NQ-only 30–60 minute continuation in the unconditional event study does not survive the frozen same-sized-up-move baseline. The required stable positive break-minus-control return at both 30m and 60m across IS, Validation, and OOS is absent.

The OOS appearance is heterogeneous rather than robust:

- In the `0.5–1.0 ATR` move band, break-minus-control is positive at 30/60m (+3.64/+5.91 points).
- In the `1.0–1.5 ATR` band, it is strongly negative at 30/60m (-9.48/-3.73 points).
- Validation is negative at 30/60m in both of those bands (-0.44/-1.25 and -1.67/-5.11 points).

No rule can be selected from these cells: they are exactly the instability that the matched-control and chronological-split design was intended to expose.

## Interpretation

NQ has an upward long-run drift and ordinary 15m up moves can themselves be followed by further gains. A resistance-break label does not demonstrate incremental information once the size of the preceding move is held comparable. The prior unconditional long result therefore cannot justify an immediate, retest, or continuation entry test.

## Decision

Close the complete 15m generic S/R branch:

- **Strategy 42:** killed — generic timeframe/S/R continuation has no validated edge.
- **Downside break-failure lead:** retired — no advantage versus matched down moves.
- **NQ upside-break continuation lead:** retired — no stable advantage versus matched up moves.

No trade strategy, parameter search, or execution optimization follows from this study.

## Audit files

- `events.csv` — break/control event paths.
- `summary.csv` — returns, excursions, retention, and failure diagnostics.
- `break_minus_control.csv` — matched band differences used for the decision.
- `research/15m_nq_upside_break_continuation/PREREGISTRATION.md` — frozen design.
