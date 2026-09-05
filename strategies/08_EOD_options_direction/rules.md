# Rules — Prior-Day EOD Options -> Intraday Direction

Mechanical definitions only. No vague language.

## Instrument / clock

- Instrument: NQ continuous futures (1-minute)
- Decision information: `t <= signal_time`
- Entry / outcome start: **next bar open** after signal (unless a dossier explicitly states otherwise)

## Implementation source of truth

See `code/README.md` for scripts. Thresholds and frozen constants live in:

- `artifacts/06_HIGH_opportunity_state/frozen_opportunity_gate.json` (where applicable)
- script module constants at top of each `run_*.py`

## Frozen options rules

```text
Options EOD date D available only for session S with D < S
  (merge_asof backward, allow_exact_matches=False)
Features: net_gex_proxy, near2_pc_imb, delta_put_oi_z20
Extremes: IS |gex| p66, |pc_imb| p80, |put_z| >= 1.0
Mechanisms: follow and fade only — no sweep
```

## Forbidden in this dossier

- Refitting frozen HIGH terciles
- Combining dead mechanisms to rescue a fail
- Using EOD fields as same-day intraday signals
- Treating single-clock 55–60% prints as validation
