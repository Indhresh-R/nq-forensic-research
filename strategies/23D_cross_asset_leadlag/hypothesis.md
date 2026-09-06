# Hypothesis — Overnight cross-asset RS → NQ open-to-H1 under HIGH

## Market behavior under test

Overnight / pre-open **relative strength** of related futures vs NQ carries
incremental signed information about NQ's post-open path when Strategy 12
flags an elevated activity regime.

```text
Overnight RS (ES [+ ZN/ZB if present] vs NQ)
    → frozen follow/fade side
    → Strategy-12 HIGH at NY_AM clocks
    → NQ next-open → H minute return
```

## Why allowed

External to pure NQ price/state resolvers (13–22). Uses another liquid futures
book's overnight move — information class adjacent to, but distinct from,
Strategy 15's *intra-session* ES/NQ resolvers (already **B→kill**).

## Data availability (frozen before look)

| Instrument | Status |
|------------|--------|
| ES | **Available** — tested as **23D-ES** → **C CLOSED** |
| ZN (10Y) | **UNAVAILABLE** then — still **UNTESTED**; open if parquet sourced |
| ZB (30Y) | **UNAVAILABLE** then — still **UNTESTED**; open if parquet sourced |

ZN/ZB were **never** part of the ES kill. See `conclusion.md` and
`research_framework/direction_resolution.md`.

## Economic rationale (pre-registered sides)

| Signal | Side |
|--------|------|
| `es_follow` | side = sign(overnight_ret_ES − overnight_ret_NQ) |
| `es_fade` | opposite |

Skip when relative return ≈ 0.

## Success / failure

### Success

- Material **incremental** lift of HIGH+signal over HIGH-long (and over ALL+signal)
- Same-sign IS → Val → OOS; multi-clock (≥2) under the **24-cell** frozen grid
- Survives multiplicity bar calibrated to ~5% noise rate on 24 cells (≈1 expected false strong)

### Failure

- Absolute edge without incremental lift vs HIGH-long (23A failure mode)
- Soft single-clock / Val flip / OOS collapse
- Cherry-picking among the 24 cells after the fact
