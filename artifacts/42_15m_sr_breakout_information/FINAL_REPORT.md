# 15m S/R Breakout Information Study

**Verdict: no stable positive continuation information. One directional failure pattern is retained as an observation, not a trade.**

This study used the exact causal 15m, 20-prior-bar support/resistance event from Strategy 42, but removed the fixed five-bar trade exit. It measured the subsequent 1m path at 1/5/15/30/60 minutes, separately by side, market, and frozen chronological split. No execution parameter, cost, stop, or target was tested.

## Continuation gate: failed

There is no horizon at which confirmed breaks show positive, same-signed forward continuation in both NQ and ES across IS, Validation, and OOS.

- **Long breaks:** NQ is positive at 30/60m in IS and OOS (+0.39/+0.42 and +2.45/+3.59 points), but ES is negative in IS and Validation (60m -0.16/-0.75). This is not cross-market stable.
- **Short breaks:** the direction-signed returns are negative at 30m and 60m in both markets and every split. A short break therefore tended to move *against* the short breakout direction, rather than continue.

| Short-break forward return, points | IS | Validation | OOS |
| --- | ---: | ---: | ---: |
| NQ, 30m | -0.43 | -2.21 | -0.71 |
| NQ, 60m | -0.71 | -3.79 | -2.83 |
| ES, 30m | -0.07 | -0.28 | -0.92 |
| ES, 60m | -0.16 | -0.36 | -0.29 |

This is evidence against short-breakout continuation. It is **not yet evidence for a tradeable fade**: the adverse/excursion ranges are large and the study deliberately has not specified a causal fade entry, stop, or exit.

## Level retention/failure

At one minute, 86–90% of events still close beyond their broken level. This is mostly mechanical given the event definition and is not predictive evidence. Retention decays materially with time: by 60m it is roughly 57–70%, while a close back through the broken level has occurred in roughly 59–71% of events. The broken level is therefore not reliably defended over the next hour.

## Decision

Do **not** test the proposed immediate, retest, or continuation long-break mechanisms: the prerequisite positive-continuation information did not survive the cross-market/split gate.

If desired, the only scientifically distinct follow-up is a new, separately preregistered **downside-break failure/fade** hypothesis. It must define its entry, risk, cost, and exit before any outcome review; it cannot be framed as rescuing Strategy 42.

## Audit files

- `events.csv` — every event × horizon observation.
- `summary.csv` — NQ/ES × split × side × horizon path statistics.
- `research/42_15m_sr_breakout_information/PREREGISTRATION.md` — frozen definitions.
