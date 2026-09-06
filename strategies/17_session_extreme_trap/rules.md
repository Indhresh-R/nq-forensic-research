# Rules — 17 session extreme trap

## Frozen

| Item | Value |
|------|-------|
| Activity | Strategy 12 `rng_psr` IS terciles (untouched) |
| W | 15 minutes |
| thr | `max(0.50, 0.05 × psr)` |
| Buyers trapped | recent high touches SH and close_T ≤ SH − thr → short |
| Sellers trapped | recent low touches SL and close_T ≥ SL + thr → long |
| H | 15, 30, 60, 90, 120 |
| Primary | H=30, H=60 |
| Universes | ALL+trap, HIGH+trap, LOW+trap, HIGH_long |

## Forbidden

- Stops / targets / RR
- Retuning W, thr, or Strategy 12
- Combining with 16A/16B
- Selecting H/clock after results
