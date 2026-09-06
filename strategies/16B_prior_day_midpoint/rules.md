# Rules — 16B prior-day midpoint

## Frozen

| Item | Value |
|------|-------|
| Activity | Strategy 12 `rng_psr` IS terciles (untouched) |
| Resolver | `side = sign(close_T − prior_mid)` |
| `prior_mid` | `(prior_high + prior_low) / 2` of previous Globex `session_date` |
| Flat skip | `abs(close_T − prior_mid) < max(0.25, 0.01 × prior_range)` |
| H | 15, 30, 60, 90, 120 (pre-specified) |
| Primary | H=30, H=60 |
| Outcome | next open → close at H; signed by `side` |
| Universes | ALL+loc, HIGH+loc, LOW+loc, HIGH_long |

## Forbidden

- Stops / targets / RR
- PDH/PDL / inside-range / multi-day variants in this dossier
- Retuning Strategy 12
- Selecting H or clock after seeing results
