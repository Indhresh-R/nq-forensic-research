# Rules — OR5 Liquidity Sweep Fade

Mechanical definitions only. No vague language.

## Instrument / clock

- Instrument: NQ continuous futures (1-minute)
- Decision information: `t <= signal_time`
- Entry / outcome start: **next bar open** after signal (unless a dossier explicitly states otherwise)

## Implementation source of truth

See `code/README.md` for scripts. Thresholds and frozen constants live in:

- `artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.json` (where applicable)
- script module constants at top of each `run_*.py`

## Forbidden in this dossier

- Refitting frozen HIGH terciles
- Combining dead mechanisms to rescue a fail
- Using EOD fields as same-day intraday signals
- Treating single-clock 55–60% prints as validation
