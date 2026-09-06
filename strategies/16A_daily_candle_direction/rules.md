# Rules — 16A prior daily candle direction

## Frozen

| Item | Value |
|------|-------|
| Activity | Strategy 12 `rng_psr` IS terciles (untouched) |
| Bias | A only: sign(prior Globex day close − open) |
| Prior day | Previous `session_date` OHLC (18:00 ET day) |
| Horizons | **15, 30, 60, 90, 120** (all pre-specified; skip if insufficient bars) |
| Primary report | H=30 and H=60 |
| Outcome | `side * (close_{entry+H−1} − entry)`; entry = next NQ open after T |
| Universes | ALL, HIGH, LOW (+ HIGH_LONG null: always +1 inside HIGH) |

## Sessions

Independent; report LONDON → NY_PM → NY_AM → ASIA.

## Forbidden

- Stops, targets, RR, cost optimization
- Bias B/C/D or combinations in this dossier
- Retuning Strategy 12 terciles
- Selecting H after seeing results
