# Rules — HIGH Residual Opportunity Economics (Direction-Neutral)

Mechanical definitions only. No vague language.

## Instrument / clock

- Instrument: NQ continuous futures (1-minute)
- Decision information: `t <= signal_time`
- Entry / outcome start: **next bar open** after signal (unless a dossier explicitly states otherwise)

## Implementation source of truth

See `code/README.md` for scripts. Thresholds and frozen constants live in:

- `artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.json` (where applicable)
- script module constants at top of each `run_*.py`

## Frozen residual economics rules

```text
Residual = max(high-entry, entry-low) from next open after T
Horizons: 5/10/15/30/60
Costs (NQ pts, pre-specified): tight=0.50, mid=1.00, wide=2.00
Direction: NONE
Compare HIGH vs LOW coverage and ONR-normalized residual
Frequency + clustering of HIGH clocks
```

## Forbidden in this dossier

- Refitting frozen HIGH terciles
- Combining dead mechanisms to rescue a fail
- Using EOD fields as same-day intraday signals
- Treating single-clock 55–60% prints as validation
