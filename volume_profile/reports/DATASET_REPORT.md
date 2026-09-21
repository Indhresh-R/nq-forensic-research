# Dataset report

## Input

- Files expected: 126
- Files in audit: 126
- Failed files: 0
- File dates: 2026-03-25 through 2026-09-16
- Total trades: 46124658
- Total volume: 64588074
- Timestamp coverage: 2026-03-25 00:00:00.150031609+00:00 to 2026-09-16 23:59:55.141796351+00:00

## CME session construction

- Timezone: America/New_York, via the standard zone database. EST/EDT offsets are not hardcoded.
- If New York time is at or after 18:00, session_date is that New York calendar date.
- Otherwise session_date is the previous New York calendar date.
- The session window used for events is [18:00, next 18:00). The economic close is 17:00. The maintenance break is the empty interval before 18:00.
- Sessions created: 127
- Session dates: 2026-03-24 through 2026-09-16
- Complete sessions (first trade within 30 minutes of 18:00 and last trade within 30 minutes of 17:00): 96

## Profile construction

- Tick size: 0.25 index points. Price ticks = round(price / tick_size). Databento fixed-point prices are divided by 1000000000 when they are still scaled.
- POC: traded price with the most volume. Equal volume resolves to the lower price.
- Value area: 70% of total session volume, expanded from the POC across traded prices only.
- Tie-break: if the next higher and next lower traded prices have equal volume, expand to the lower price.
- Profiles use trade prints. Bars are not used.

## Roll handling

- Primary detector: `instrument_id` changes from the previous session, or more than one instrument_id prints inside the session.
- Fallback, also predeclared: absolute gap between the previous session's last trade and this session's first trade of at least 150.0 points.
- The first session is not a roll unless it contains two instrument ids. There is no prior contract in this file set to compare against.
- Sessions flagged: 13
- Flagged dates: 2026-04-12, 2026-04-19, 2026-05-24, 2026-06-07, 2026-06-14, 2026-06-18, 2026-06-21, 2026-06-28, 2026-07-12, 2026-07-26, 2026-08-02, 2026-08-30, 2026-09-13
- Of which instrument-id changes: 1
- Of which price-gap flags: 13
- Flagged sessions stay in the profile tables. A mechanism row is excluded when the session or its previous session is flagged, because the prices are not comparable.

## Validation

- session_assignment: pass
- no_lookahead: pass
- volume_conservation: pass
- poc_correctness: pass
- value_area_correctness: pass
- tick_alignment: pass
- determinism: pass
- partition_equivalence: pass
- event_timestamp_integrity: pass
- same_event_contamination: pass

## Ordering limitation

Trades are ordered by `ts_event`, then Databento `sequence`. That is the finest order this schema supports. Approach direction does not use a later sequence at the same timestamp.
