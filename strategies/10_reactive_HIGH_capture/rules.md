# Rules — Reactive Opportunity Capture (HIGH -> Displacement -> Enter)

Mechanical definitions only. No vague language.

## Instrument / clock

- Instrument: NQ continuous futures (1-minute)
- Decision information: `t <= signal_time`
- Entry / outcome start: **next bar open** after signal (unless a dossier explicitly states otherwise)

## Implementation source of truth

See `code/README.md` for scripts. Thresholds and frozen constants live in:

- `artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.json` (where applicable)
- script module constants at top of each `run_*.py`

## Frozen reactive rules

```text
First HIGH in 09:35–11:00
BLIND: next open after T0, direction = sign(close_T0 - open_930)
REACTIVE: wait until |excursion from close_T0| >= 0.15 * ONR (max 30m)
          enter next bar in revealed direction
Compare paired paths; no direction family rescue
```

## Forbidden in this dossier

- Refitting frozen HIGH terciles
- Combining dead mechanisms to rescue a fail
- Using EOD fields as same-day intraday signals
- Treating single-clock 55–60% prints as validation
