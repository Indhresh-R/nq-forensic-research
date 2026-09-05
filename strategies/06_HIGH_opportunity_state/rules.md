# Rules — HIGH Opportunity / Activity State

Mechanical definitions only. No vague language.

## Instrument / clock

- Instrument: NQ continuous futures (1-minute)
- Decision information: `t <= signal_time`
- Entry / outcome start: **next bar open** after signal (unless a dossier explicitly states otherwise)

## Implementation source of truth

See `code/README.md` for scripts. Thresholds and frozen constants live in:

- `artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.json` (where applicable)
- script module constants at top of each `run_*.py`

## Frozen HIGH (do not retune)

Primary ARM: `vol_expansion_high`

```text
rng_onr >= IS_p66[T_offset]
T_offset in {5,10,...,90}  # 09:35–11:00 ET
State uses bars with ny_min <= T only
Forward evaluation starts at next bar open after T
Structural opportunity context: max(MFE,MAE) >= 0.25 * ONR within H
```

Thresholds: `artifacts/06_HIGH_opportunity_state/ny_open_opp_timing_thresholds_IS.json`  
Gate card: `artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.md`

## Forbidden in this dossier

- Refitting frozen HIGH terciles
- Combining dead mechanisms to rescue a fail
- Using EOD fields as same-day intraday signals
- Treating single-clock 55–60% prints as validation
