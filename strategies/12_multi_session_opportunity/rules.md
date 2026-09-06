# Rules — Multi-session opportunity

Mechanical definitions only.

## Instrument / clock (America/New_York)

| Session | Window (`ny_min`) |
|---------|-------------------|
| ASIA | 18:00 → 03:00 (wraps) |
| LONDON | 03:00 → 09:30 |
| NY_AM | 09:30 → 12:00 |
| NY_PM | 12:00 → 16:00 |

`session_date` still rolls at 18:00 (`SESSION_START`).

## Scale unit

`psr` = prior session high−low:

- LONDON ← ASIA (same session_date)
- NY_AM ← LONDON
- NY_PM ← NY_AM
- ASIA ← prior session_date NY_PM

## Structural opportunity (unsigned)

From next-bar open after decision T, within horizon H (remaining bars in the
**same** session):

```text
max(high_max - entry, entry - low_min) >= STRUCT_FRAC * psr
STRUCT_FRAC primary = 0.25  (sensitivity 0.15 / 0.35, not optimized)
```

## Decision offsets (from session open)

```text
ASIA:   +15, +30, +60, +90, +120, +180
LONDON: +15, +30, +60, +90, +120
NY_AM:  +15, +30, +60, +90
NY_PM:  +15, +30, +60, +90, +120
```

State uses only bars in that session with timestamp <= T.
Primary HIGH arm: `vol_expansion_high` (`rng_psr >= IS_p66` at that session×offset).

## Forbidden

- Reusing NY-open HIGH terciles / ONR thresholds
- Fitting STRUCT_FRAC on forward outcomes
- Directional PnL mining inside this dossier
- Treating a single-clock ~55% gap as promotion
