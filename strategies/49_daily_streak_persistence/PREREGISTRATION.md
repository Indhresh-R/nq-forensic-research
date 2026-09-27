# Preregistration — 49 Daily directional streak persistence

Information test only. Strategy 48 is not modified and is not re-interpreted.

The question is whether same-direction NQ Globex streaks are longer, or continue more often, than the unconditional bull/bear base rate already implies. It is not whether one green or red day predicts the next day.

## Session

Use `strategies/48_daily_candle_continuation/code/candles.py` `load_candles()` unchanged.

- NQ continuous 1-minute, Globex `session_date`, roll at 18:00 America/New_York.
- Complete sessions only. Same completeness rules as Strategy 48.
- Open = first bar, high = max, low = min, close = last bar.
- Not NAS100 CFD. Not RTH-only.

## Direction

```text
Bull: Close > Open
Bear: Close < Open
Flat: Close == Open
```

No filter. Yesterday's close is not part of the direction label.

A flat day breaks a directional streak and is not itself a bull or bear streak.

## Samples

Streaks are built inside each sample separately. A streak does not cross a sample boundary.

| Sample | Sessions |
| --- | --- |
| All | every kept session, in order |
| IS | signal-session years 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |
| Year | that calendar year only |

The next day in a continuation rate is the next kept session inside that same sample.

## Continuation

After a bull or bear session that has a next session in the sample, the current streak length is the consecutive count ending on that session.

Continuation means the next session has the same label. A flat next session is not continuation.

Buckets: 1, 2, 3, 4, 5, 6, >=7.

Matched base:

- Bull bucket: unconditional bull rate in that sample (bull sessions / all sessions in the sample, flats included).
- Bear bucket: unconditional bear rate in that sample.
- Pooled bucket: (n_bull observations × bull rate + n_bear observations × bear rate) / n.

Lift in percentage points = (observed continuation − matched base) × 100.

L = 1 is reported. It is not a verdict input. The hypothesis is not the one-day transition.

## Null

Permute the sample's bull/bear/flat labels, preserving the three counts. 10,000 permutations. Generator seed 49, started fresh for each sample.

One-sided `p_ge` = (number of permutations with statistic >= observed) / 10000.

A statistic is above the null only if observed > null mean and `p_ge` <= 0.05.

Every requested count is reported. The verdict uses only:

- Full sample: pooled streaks with length >= 3, and pooled streaks with length >= 4.
- OOS: pooled streaks with length >= 3.

Maxima and the >= 5 counts are reported and are not a second way to pass.

## Verdict

Frozen before the run. Not revised after results.

A bucket with n < 30 is descriptive only.

Let L2 and L3 be the pooled continuation rows for lengths 2 and 3.

- Clause A, full null: both pre-registered full-sample statistics are above the null.
- Clause A, OOS null: the OOS pooled >= 3 count is above the null.
- Clause B: on All, L2 and L3 each have n >= 100 and lift > 0.
- Clause C: on OOS, L2 and L3 each have n >= 30 and lift > 0.
- Clause D: for L2 and for L3, at least three calendar years each have n >= 20 and lift > 0. Year rates are computed inside that year only.

Display rule, separate from the verdict: a year-table continuation cell is `NA` when its n < 5.

```text
REAL MECHANISM
    A full, A OOS, B, C, and D all hold.

NOT REAL
    A full fails, or B fails, or OOS n is at least 30 and C's lift test fails.

INCONCLUSIVE
    otherwise.
```

No entries, stops, P&L, threshold search, or extra filters. No streak length is chosen because its continuation rate is the highest.
