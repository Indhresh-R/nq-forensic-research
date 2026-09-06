# Methodology — 23D Cross-asset overnight lead-lag

## Lessons applied from 23A (before any scan)

1. **Pre-register grid size** and noise base rate before looking at results.
2. **Three-way contrast from the start:** ALL+signal / HIGH-long / HIGH+signal.
   The research question is incremental lift over Strategy 12, not absolute win rate.
3. Stage-gate: publish **IS first**; Val/OOS only after IS review.

## Causality card

```text
Information at T (NY_AM decision clock):
  - Overnight window fully closed before 09:30 (prior RTH close → NY open)
  - NQ bars <= T
  - Strategy-12 HIGH from rng_psr at T using frozen IS terciles

Entry / outcome:
  next bar OPEN after T

Forbidden:
  - Using same-morning post-09:30 ES/NQ path in the RS feature
  - Refitting sides / windows on Val/OOS
  - Expanding to ZN/ZB after seeing ES results (data absent; would be rescue)
```

## Overnight / pre-open window (frozen)

For each NQ `session_date` S with a 09:30 bar:

```text
prior_close_px = last available close with ny_min <= 16:00 on the previous
                 trading session_date (Globex calendar) for that instrument
open_930_px    = open of the first bar at ny_min == 09:30 on S
                 (or first bar with ny_min >= 09:30 if exact missing)

overnight_ret  = open_930_px / prior_close_px - 1
rs_es          = overnight_ret_ES - overnight_ret_NQ
```

Feature known before any NY_AM decision offset ≥ 15.

## Pre-registered grid (BEFORE scan)

| Axis | Values | Count |
|------|--------|------:|
| Session | NY_AM only (open-to-H1 hypothesis) | 1 |
| Clocks | T ∈ {15, 30, 60, 90} min from NY open | 4 |
| Horizons | H ∈ {15, 30, 60} | 3 |
| Signals | `es_follow`, `es_fade` | 2 |
| **Total cells** | | **24** |

Expected false strong at ~5% single-test rate: **~1.2** cells.
Promotion bar (IS): ≥2 distinct clocks strong on **incremental** lift vs HIGH-long,
not merely vs ALL+signal.

ZN/ZB would have added 4 more signals (follow/fade × 2) → 48 cells — **not opened**
without data.

## Three-way universes (every cell)

1. **ALL+signal** — signal side, any regime  
2. **HIGH-long** — always long inside HIGH (Strategy 12 alone)  
3. **HIGH+signal** — signal side inside HIGH  

Primary kill/promote metric: `lift_vs_HIGH_long = HIGH+signal − HIGH-long`.

## Splits

Identical to `train_validation_oos.md`: IS 2010–2021 / Val 2022–2024 / OOS 2025–2026.

## Ambiguity / clustering

- Forward close at H; no stop/target dual-touch
- Multiple NY_AM clocks/day clustered — require multi-clock for promotion

## Family-23 multi-comparison

23A already consumed one external hypothesis (**C**). 23D is a second draw;
do not promote on a single soft IS hit.
