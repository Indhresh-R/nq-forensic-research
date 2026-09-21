# Previous-day directional structure — mechanism report

**Pre-cost mechanism analysis — no executable strategy.**

No executable strategy is defined or tested in this document.

The event is clean separation beyond the previous close, then the first later bar that retraces into the previous close-to-extreme range. Penetration is measured on that later bar. The discarded opening-bar touch is not in these tables. No ATR cutoff is applied.

## Research verdict: MECHANISM UNCLEAR

The verdict is the frozen rule in `PREREGISTRATION.md`. It is not a profitability claim.

## A. Dataset audit

| Item | Value |
| --- | --- |
| Requested path | `d:\NQ\nq_data` (not present on this machine) |
| Source used | `data/nq_1m_continuous.parquet` via `common.nq_session.load_nq`, read only |
| Timestamp range | 2010-06-06 18:00:00-04:00 → 2026-08-07 16:59:00-04:00 |
| 1-minute bars | 4788194 |
| Bars with high < low | 0 |
| Session convention | Globex `session_date`, rolls at 18:00 America/New_York |
| Session end | Last 1-minute bar of that Globex session |
| Splits | IS 2010–2021 / Validation 2022–2024 / OOS 2025–2026, by the following session's year |
| Observed sessions | 4175 |
| Complete sessions | 3400 |
| Incomplete sessions | 775 |
| Adjacent slots blocked because one side was incomplete | 1097 |
| Eligible directional pairs | 3068 |
| Previous day doji, dropped | 9 |
| Undefined reference range, dropped | 0 |
| First bar entered the range before separation | 2297 |
| Separated, no return into the range | 75 |
| Retracement events | 696 |
| Retracement with a forward bar | 696 |
| Retracement on the last bar, no forward path | 0 |

A complete session has at least 1100 bars, starts in 18:00–18:05 ET, and prints at least one bar in 16:00–16:59 ET. Incomplete sessions are not used as the previous day and are not skipped over.

Incomplete reasons (a session can fail more than one check; the stored reason is the joined list):

| Reason | Sessions |
| --- | --- |
| `n_bars<1100,no_1600_hour` | 603 |
| `no_1600_hour` | 81 |
| `n_bars<1100` | 63 |
| `n_bars<1100,open_not_in_1800_1805,no_1600_hour` | 11 |
| `open_not_in_1800_1805` | 9 |
| `n_bars<1100,open_not_in_1800_1805` | 8 |

## B. Previous-day candle distribution

Counted on complete sessions, before the following-session pair filter.

| Direction | Complete sessions |
| --- | --- |
| bullish | 1887 |
| bearish | 1503 |
| doji | 10 |

Range, body fraction, and wick fractions:

| measure | N | mean | p10 | p25 | p50 | p75 | p90 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| range (points) | 3400 | 200.488 | 34.500 | 57.688 | 138.750 | 285.250 | 443.025 |
| body / range | 3400 | 0.465 | 0.096 | 0.233 | 0.466 | 0.687 | 0.833 |
| upper wick / range | 3400 | 0.239 | 0.031 | 0.080 | 0.189 | 0.356 | 0.533 |
| lower wick / range | 3400 | 0.296 | 0.044 | 0.115 | 0.262 | 0.442 | 0.611 |

Body-fraction buckets on complete sessions:

| Body fraction | Sessions |
| --- | --- |
| <25% | 906 |
| 25-50% | 917 |
| 50-75% | 948 |
| >75% | 629 |

## C. Sequence audit

Bullish previous day: before any bar with `low <= previous close`, require a bar with `low > previous close`. That bar is separation, including one tick. The retracement is the first later bar with `low <= previous close`. Bearish previous day mirrors this with `high < previous close`, then a later bar with `high >= previous close`. A bar that trades both sides of the close does not establish separation. Separation with no return is an audit count, not a penetration bucket. No ATR and no point-distance cutoff.

At 1-minute resolution the first bar either enters the range or lies entirely on the continuation side of the close. Clean separation is that first bar. The return, when it happens, is a later bar. This is the definition, not a delay filter.

Separation is the first bar in 771 of 771 separated sessions (exceptions: 0).

| item | direction | N | share |
| --- | --- | --- | --- |
| entered_before_separation | all | 2297 | 74.9% |
| entered_before_separation | bullish | 1281 | 76.2% |
| entered_before_separation | bearish | 1016 | 73.3% |
| separated_no_return | all | 75 | 2.4% |
| separated_no_return | bullish | 43 | 2.6% |
| separated_no_return | bearish | 32 | 2.3% |
| retracement | all | 696 | 22.7% |
| retracement | bullish | 357 | 21.2% |
| retracement | bearish | 339 | 24.4% |
| retracement_with_forward_bar | all | 696 | 22.7% |

Minutes from the separation bar to the retracement bar, among retracement events:

| direction | N | mean | p10 | p25 | p50 | p75 | p90 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all | 696 | 241.8 | 2.5 | 12.0 | 119.0 | 236.8 | 928.5 |
| bullish | 357 | 239.4 | 2.6 | 14.0 | 119.0 | 205.0 | 933.2 |
| bearish | 339 | 244.2 | 2.8 | 11.0 | 119.0 | 281.5 | 881.2 |

Clock time of the retracement bar, in minutes after 18:00 ET:

| direction | N | p10 | p50 | p90 |
| --- | --- | --- | --- | --- |
| all | 696 | 2.5 | 119.0 | 928.5 |
| bullish | 357 | 2.6 | 119.0 | 933.2 |
| bearish | 339 | 2.8 | 119.0 | 881.2 |

The retracement bar is the 18:00 ET open in 0.0% of retracement events. That share is zero when separation occupies the first bar and the return is a later bar.

## D. Penetration at the retracement

Retracement penetration is the penetration of that later bar, measured at its low (bullish previous day) or high (bearish previous day). This is not a tick-level first print. One minute can travel from the boundary to a deep extreme, so this depth is an upper bound on the instantaneous entry. Maximum penetration uses the whole following session and is an outcome, not an entry-time fact. Buckets are unchanged.

| Bucket | Retracement sessions | Maximum-penetration sessions |
| --- | --- | --- |
| no penetration | — | 75 |
| 0-10% | 655 | 270 |
| 10-20% | 28 | 296 |
| 20-30% | 5 | 272 |
| 30-40% | 7 | 240 |
| 40-50% | 1 | 203 |
| 50-75% | 0 | 476 |
| 75-100% | 0 | 330 |
| >100% | 0 | 906 |

Retracement median (among return events) = 1.06%. Maximum-penetration median (all eligible pairs) = 58.13%.

Median separation duration and clock time of the retracement, by penetration bucket:

| bucket | N | median separation minutes | median minutes after 18:00 |
| --- | --- | --- | --- |
| 0-10% | 655 | 100.0 | 100.0 |
| 10-20% | 28 | 119.0 | 119.0 |
| 20-30% | 5 | 119.0 | 119.0 |
| 30-40% | 7 | 785.0 | 785.0 |
| 40-50% | 1 | 961.0 | 961.0 |
| 50-75% | 0 | — | — |
| 75-100% | 0 | — | — |
| >100% | 0 | — | — |

## E. Forward outcomes by retracement penetration

Positive values continue the previous day's direction. Percentage positive counts strictly positive returns. It is not a win rate. There is no position and no cost.

Measurement price is the open of the bar after the retracement bar. Point units are NQ index points.

### Combined sample, points — medians

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 635 | +0.00 | +0.00 | +0.00 | -0.25 | -0.50 | +1.25 |
| 10-20% | 27 | +0.00 | +0.38 | -0.25 | +0.38 | +1.50 | -0.62 |
| 20-30% | 4 | +0.00 | -0.25 | +0.25 | +1.00 | -1.50 | -17.00 |
| 30-40% | 6 | -2.00 | -1.75 | -0.75 | -0.88 | +5.75 | -2.25 |
| 40-50% | 1 | -3.50 | -9.00 | -14.25 | -11.25 | -0.25 | -3.00 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Combined sample, points — means

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 635 | -0.37 | +0.56 | +2.00 | +0.27 | +0.82 | -6.00 |
| 10-20% | 27 | +5.08 | +7.32 | +2.21 | +6.50 | +15.60 | +25.58 |
| 20-30% | 4 | +0.35 | +0.05 | +0.31 | +1.35 | -0.90 | -7.90 |
| 30-40% | 6 | -53.29 | -39.75 | -36.50 | -5.46 | -26.90 | -2.14 |
| 40-50% | 1 | -3.50 | -9.00 | -14.25 | -11.25 | -0.25 | -3.00 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Combined sample, points — standard deviation

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 635 | 26.72 | 26.67 | 34.07 | 44.47 | 52.87 | 157.63 |
| 10-20% | 27 | 22.20 | 28.07 | 22.70 | 26.23 | 55.88 | 94.23 |
| 20-30% | 4 | 0.63 | 1.27 | 1.46 | 2.17 | 4.60 | 20.60 |
| 30-40% | 6 | 122.04 | 101.68 | 171.25 | 58.56 | 138.74 | 144.53 |
| 40-50% | 1 | — | — | — | — | — | — |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Combined sample — percentage positive (not a win rate)

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 635 | 48.5 | 48.5 | 48.7 | 48.5 | 46.6 | 50.7 |
| 10-20% | 27 | 42.9 | 53.6 | 40.7 | 53.6 | 60.7 | 50.0 |
| 20-30% | 4 | 40.0 | 40.0 | 50.0 | 80.0 | 40.0 | 40.0 |
| 30-40% | 6 | 28.6 | 28.6 | 50.0 | 33.3 | 80.0 | 42.9 |
| 40-50% | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Combined sample, return / previous-day range — medians

This unit is pre-registered so that the rise in the NQ price level across 2010–2026 does not dominate the comparison. It is not a filter.

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 635 | +0.0000 | +0.0000 | +0.0000 | -0.0029 | -0.0067 | +0.0278 |
| 10-20% | 27 | +0.0000 | +0.0081 | -0.0056 | +0.0128 | +0.0400 | -0.0177 |
| 20-30% | 4 | +0.0000 | -0.0106 | +0.0044 | +0.0223 | -0.0335 | -0.4804 |
| 30-40% | 6 | -0.0190 | -0.0085 | -0.0156 | -0.0107 | +0.0489 | -0.0375 |
| 40-50% | 1 | -0.1111 | -0.2857 | -0.4524 | -0.3571 | -0.0079 | -0.0952 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Combined sample, return / previous-day range — means

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 635 | +0.0005 | +0.0006 | +0.0020 | -0.0079 | -0.0125 | -0.0091 |
| 10-20% | 27 | +0.0128 | +0.0189 | +0.0019 | +0.0192 | +0.0534 | +0.0124 |
| 20-30% | 4 | +0.0093 | -0.0014 | +0.0076 | +0.0317 | -0.0601 | -0.3444 |
| 30-40% | 6 | -0.0891 | -0.0648 | -0.0366 | -0.0016 | +0.0218 | -0.0483 |
| 40-50% | 1 | -0.1111 | -0.2857 | -0.4524 | -0.3571 | -0.0079 | -0.0952 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

## F. MFE / MAE

Excursions run from the measurement bar through the horizon bar. The retracement bar is excluded. For a bullish previous day, MFE is the highest high above the measurement price and MAE is the deepest low below it. For a bearish previous day, MFE is the deepest low below the measurement price and MAE is the highest high above it. Both are floored at zero.

| bucket | horizon | N | median MFE pts | median MAE pts | median MFE / range | median MAE / range |
| --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 30m | 635 | 5.00 | 5.00 | 0.0351 | 0.0370 |
| 0-10% | 60m | 625 | 6.75 | 7.25 | 0.0473 | 0.0511 |
| 0-10% | session_end | 655 | 54.00 | 51.00 | 0.3763 | 0.3978 |
| 10-20% | 30m | 27 | 2.50 | 5.75 | 0.0457 | 0.0838 |
| 10-20% | 60m | 28 | 5.12 | 6.38 | 0.0979 | 0.0873 |
| 10-20% | session_end | 28 | 34.75 | 30.25 | 0.5788 | 0.3785 |
| 20-30% | 30m | 4 | 0.88 | 1.00 | 0.0323 | 0.0325 |
| 20-30% | 60m | 5 | 3.25 | 0.75 | 0.0726 | 0.0319 |
| 20-30% | session_end | 5 | 3.25 | 20.00 | 0.1667 | 0.7039 |
| 30-40% | 30m | 6 | 5.38 | 36.25 | 0.0661 | 0.1321 |
| 30-40% | 60m | 6 | 3.12 | 36.25 | 0.0330 | 0.1321 |
| 30-40% | session_end | 7 | 26.50 | 55.50 | 0.4240 | 0.5193 |
| 40-50% | 30m | 1 | 1.25 | 15.25 | 0.0397 | 0.4841 |
| 40-50% | 60m | 1 | 1.25 | 16.75 | 0.0397 | 0.5317 |
| 40-50% | session_end | 1 | 5.50 | 16.75 | 0.1746 | 0.5317 |
| 50-75% | 30m | 0 | — | — | — | — |
| 50-75% | 60m | 0 | — | — | — | — |
| 50-75% | session_end | 0 | — | — | — | — |
| 75-100% | 30m | 0 | — | — | — | — |
| 75-100% | 60m | 0 | — | — | — | — |
| 75-100% | session_end | 0 | — | — | — | — |
| >100% | 30m | 0 | — | — | — | — |
| >100% | 60m | 0 | — | — | — | — |
| >100% | session_end | 0 | — | — | — | — |

The full horizon set, including means, is in `results/mfe_mae_by_retracement.csv`.

## G. Bullish versus bearish previous days

Returns stay direction-normalized. Positive still means continuation of that previous day.

### Bullish previous day — median points

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 330 | -0.25 | -0.25 | +0.00 | -0.25 | -0.25 | +6.75 |
| 10-20% | 12 | +0.00 | +8.50 | +2.62 | +5.00 | +4.75 | -6.25 |
| 20-30% | 1 | +1.25 | +1.25 | +2.00 | +4.50 | +5.00 | +10.50 |
| 30-40% | 1 | -7.50 | -3.50 | +52.75 | +68.25 | +105.25 | +290.75 |
| 40-50% | 0 | — | — | — | — | — | — |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Bearish previous day — median points

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 305 | +0.25 | +0.25 | +0.00 | -0.25 | -1.00 | -4.00 |
| 10-20% | 15 | +0.00 | -1.00 | -1.50 | -0.25 | +0.25 | +1.75 |
| 20-30% | 3 | +0.00 | -0.62 | -0.50 | +0.62 | -2.62 | -19.25 |
| 30-40% | 5 | -1.12 | -1.00 | -2.25 | -1.50 | +4.88 | -19.25 |
| 40-50% | 1 | -3.50 | -9.00 | -14.25 | -11.25 | -0.25 | -3.00 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Bullish previous day — median return / previous-day range

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 330 | -0.0021 | -0.0014 | +0.0000 | -0.0040 | -0.0026 | +0.0729 |
| 10-20% | 12 | +0.0000 | +0.0563 | +0.0376 | +0.0635 | +0.0964 | -0.0645 |
| 20-30% | 1 | +0.0311 | +0.0311 | +0.0497 | +0.1118 | +0.1242 | +0.2609 |
| 30-40% | 1 | -0.0190 | -0.0089 | +0.1339 | +0.1732 | +0.2671 | +0.7379 |
| 40-50% | 0 | — | — | — | — | — | — |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Bearish previous day — median return / previous-day range

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 305 | +0.0036 | +0.0036 | +0.0000 | -0.0019 | -0.0122 | -0.0635 |
| 10-20% | 15 | +0.0000 | -0.0170 | -0.0290 | -0.0035 | +0.0046 | +0.0285 |
| 20-30% | 3 | +0.0000 | -0.0193 | -0.0256 | +0.0165 | -0.1129 | -0.6761 |
| 30-40% | 5 | -0.0191 | -0.0067 | -0.0375 | -0.0128 | +0.0435 | -0.0976 |
| 40-50% | 1 | -0.1111 | -0.2857 | -0.4524 | -0.3571 | -0.0079 | -0.0952 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Baseline from the session open

Same direction-normalized return, measured from the following session's 18:00 open, with no penetration condition. This is the previous-day-direction drift control.

| sample | unit | N 30m | 30m median | 60m median | 30m % > 0 | session-end median |
| --- | --- | --- | --- | --- | --- | --- |
| all_eligible | points | 3012 | +0.00 | +0.00 | 48.4 | -1.38 |
| all_eligible | range | 3012 | +0.0000 | +0.0000 | 48.4 | -0.0165 |
| retracement_only | points | 681 | +0.50 | +0.50 | 52.4 | -4.38 |
| retracement_only | range | 681 | +0.0053 | +0.0072 | 52.4 | -0.0435 |
| bullish | points | 1651 | +0.00 | +0.25 | 48.9 | +6.00 |
| bullish | range | 1651 | +0.0000 | +0.0032 | 48.9 | +0.0621 |
| bearish | points | 1361 | -0.25 | -0.50 | 47.8 | -11.25 |
| bearish | range | 1361 | -0.0013 | -0.0044 | 47.8 | -0.1242 |

## H. Chronological stability

Range-normalized median forward return by retracement bucket. Fixed horizons are the stability evidence. Session-end residual time varies with the retracement clock.

### IS

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 400 | +0.0000 | +0.0000 | +0.0000 | -0.0033 | -0.0112 | -0.0051 |
| 10-20% | 23 | +0.0000 | +0.0026 | -0.0056 | +0.0019 | +0.0160 | -0.0645 |
| 20-30% | 4 | +0.0000 | -0.0106 | +0.0044 | +0.0223 | -0.0335 | -0.4804 |
| 30-40% | 3 | -0.0022 | -0.0000 | -0.0375 | -0.0128 | +0.0928 | +0.0057 |
| 40-50% | 1 | -0.1111 | -0.2857 | -0.4524 | -0.3571 | -0.0079 | -0.0952 |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Validation

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 151 | +0.0013 | +0.0021 | -0.0008 | -0.0032 | -0.0033 | +0.1120 |
| 10-20% | 2 | +0.1031 | +0.1191 | +0.0326 | +0.1557 | +0.6676 | +0.4394 |
| 20-30% | 0 | — | — | — | — | — | — |
| 30-40% | 1 | -0.0190 | -0.0089 | +0.1339 | +0.1732 | +0.2671 | +0.7379 |
| 40-50% | 0 | — | — | — | — | — | — |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### OOS

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-10% | 84 | -0.0004 | +0.0009 | +0.0099 | +0.0017 | +0.0091 | -0.0201 |
| 10-20% | 2 | +0.1011 | +0.0884 | +0.0430 | +0.1193 | +0.1443 | +0.1943 |
| 20-30% | 0 | — | — | — | — | — | — |
| 30-40% | 2 | -0.2873 | -0.1985 | -0.1204 | -0.0602 | -0.1720 | -0.3085 |
| 40-50% | 0 | — | — | — | — | — | — |
| 50-75% | 0 | — | — | — | — | — | — |
| 75-100% | 0 | — | — | — | — | — | — |
| >100% | 0 | — | — | — | — | — | — |

### Year by year, 30-minute return / previous-day range

| year | split | N | Spearman | shallow N | shallow median | mid N | mid median | deep N | deep median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2011 | IS | 3 | — | 3 | +0.0408 | 0 | — | 0 | — |
| 2012 | IS | 16 | — | 16 | -0.0064 | 0 | — | 0 | — |
| 2013 | IS | 45 | — | 45 | -0.0093 | 0 | — | 0 | — |
| 2014 | IS | 45 | — | 44 | +0.0000 | 1 | -0.0818 | 0 | — |
| 2015 | IS | 49 | — | 49 | +0.0000 | 0 | — | 0 | — |
| 2016 | IS | 47 | — | 46 | +0.0191 | 1 | -0.4524 | 0 | — |
| 2017 | IS | 43 | — | 42 | -0.0138 | 1 | -0.0375 | 0 | — |
| 2018 | IS | 50 | +0.203 | 49 | -0.0091 | 1 | +0.0064 | 0 | — |
| 2019 | IS | 42 | — | 42 | +0.0012 | 0 | — | 0 | — |
| 2020 | IS | 56 | -0.028 | 56 | -0.0053 | 0 | — | 0 | — |
| 2021 | IS | 35 | — | 35 | +0.0030 | 0 | — | 0 | — |
| 2022 | Validation | 64 | +0.107 | 64 | -0.0028 | 0 | — | 0 | — |
| 2023 | Validation | 47 | — | 47 | -0.0009 | 0 | — | 0 | — |
| 2024 | Validation | 43 | — | 42 | +0.0023 | 1 | +0.1339 | 0 | — |
| 2025 | OOS | 52 | +0.180 | 51 | +0.0114 | 1 | +0.3018 | 0 | — |
| 2026 | OOS | 36 | — | 35 | +0.0052 | 1 | -0.5426 | 0 | — |

Shallow is retracement penetration in [0, 30). Mid is [30, 75). Deep is above 75, including beyond the previous extreme. These pools only summarize the frozen buckets.

## I. Previous-day candle structure

Fixed body-fraction bins. No bin was added or dropped after seeing returns.

| direction | body | N | median retracement % | median max penetration % | median 30m / range | 30m % > 0 |
| --- | --- | --- | --- | --- | --- | --- |
| bullish | <25% | 83 | 1.7 | 69.9 | +0.0193 | 66.3 |
| bullish | 25-50% | 90 | 1.1 | 51.6 | +0.0016 | 51.1 |
| bullish | 50-75% | 112 | 0.6 | 46.3 | -0.0052 | 41.1 |
| bullish | >75% | 59 | 0.5 | 22.0 | -0.0116 | 39.0 |
| bearish | <25% | 104 | 2.0 | 101.5 | -0.0015 | 45.2 |
| bearish | 25-50% | 90 | 0.8 | 63.5 | -0.0012 | 44.4 |
| bearish | 50-75% | 92 | 1.1 | 42.4 | +0.0031 | 51.1 |
| bearish | >75% | 43 | 0.5 | 47.4 | +0.0000 | 48.8 |
| combined | <25% | 187 | 1.8 | 90.9 | +0.0086 | 54.5 |
| combined | 25-50% | 180 | 0.9 | 57.9 | +0.0000 | 47.8 |
| combined | 50-75% | 204 | 0.9 | 43.5 | -0.0010 | 45.6 |
| combined | >75% | 102 | 0.5 | 35.5 | -0.0077 | 43.1 |

Descriptive rank correlations on qualifying retracements (not a search):

| Association | Spearman |
| --- | --- |
| spearman_body_vs_max_penetration | -0.287 |
| spearman_upper_wick_vs_max_penetration | +0.183 |
| spearman_lower_wick_vs_max_penetration | +0.181 |
| spearman_body_vs_30m | -0.113 |
| spearman_upper_wick_vs_30m | +0.063 |
| spearman_lower_wick_vs_30m | +0.086 |

Body-fraction 30m median span=0.0163 previous-day ranges. Spearman of body fraction vs 30m return: IS=-0.114, Validation=-0.064.

Structure does not meet the pre-registered bar for a later dedicated candle-structure test.

## Non-causal appendix: maximum penetration

These medians group sessions by how far price eventually traveled, which can happen after the forward window. They are not a decision-time relationship. Do not read a cell as something that was known at the retracement.

| bucket | N 30m | 5m | 15m | 30m | 60m | 120m | session end |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no_penetration | 0 | — | — | — | — | — | — |
| 0-10% | 81 | +0.0052 | +0.0103 | +0.0219 | +0.0383 | +0.0767 | +0.5333 |
| 10-20% | 76 | -0.0006 | +0.0004 | -0.0027 | +0.0046 | -0.0065 | +0.2689 |
| 20-30% | 60 | +0.0000 | +0.0000 | -0.0036 | -0.0007 | +0.0132 | +0.3047 |
| 30-40% | 54 | +0.0055 | -0.0007 | -0.0048 | -0.0113 | +0.0035 | +0.0681 |
| 40-50% | 49 | -0.0039 | -0.0029 | +0.0000 | -0.0064 | -0.0297 | -0.0753 |
| 50-75% | 95 | +0.0000 | -0.0010 | +0.0000 | -0.0149 | -0.0026 | -0.0625 |
| 75-100% | 64 | +0.0048 | +0.0086 | +0.0040 | -0.0075 | -0.0186 | -0.3766 |
| >100% | 194 | -0.0023 | -0.0073 | -0.0056 | -0.0196 | -0.0407 | -0.7152 |

## J. Interpretation

Frozen verdict: **MECHANISM UNCLEAR**.

Combined-sample Spearman of continuous retracement penetration versus the range-normalized return: 30m = +0.023, 60m = +0.005.

30-minute pool snapshot:

- combined: not evaluable (shallow_0_30 N=666, mid_30_75 N=7, deep_gt_75 N=0)
- IS: not evaluable (shallow_0_30 N=427, mid_30_75 N=4, deep_gt_75 N=0)
- Validation: not evaluable (shallow_0_30 N=153, mid_30_75 N=1, deep_gt_75 N=0)
- OOS: not evaluable (shallow_0_30 N=86, mid_30_75 N=2, deep_gt_75 N=0)
- bullish: not evaluable (shallow_0_30 N=343, mid_30_75 N=1, deep_gt_75 N=0)
- bearish: not evaluable (shallow_0_30 N=323, mid_30_75 N=6, deep_gt_75 N=0)

60-minute pool snapshot:

- combined: not evaluable (shallow_0_30 N=658, mid_30_75 N=7, deep_gt_75 N=0)
- IS: not evaluable (shallow_0_30 N=419, mid_30_75 N=4, deep_gt_75 N=0)
- Validation: not evaluable (shallow_0_30 N=153, mid_30_75 N=1, deep_gt_75 N=0)
- OOS: not evaluable (shallow_0_30 N=86, mid_30_75 N=2, deep_gt_75 N=0)
- bullish: not evaluable (shallow_0_30 N=340, mid_30_75 N=1, deep_gt_75 N=0)
- bearish: not evaluable (shallow_0_30 N=318, mid_30_75 N=6, deep_gt_75 N=0)

### 1. Does penetration depth matter?

Penetration in these tables is the later retracement, after a prior bar traded entirely on the continuation side of the previous close. Sessions whose first bar already entered the range are excluded. The retracement bar is the 18:00 open in 0.0% of return events. Median time from separation to that bar is 119.0 minutes. Median penetration is 1.06%. 655 of 696 forward paths sit in 0–10%, and the deep pool has N=0 at 30 minutes. In 0–10% the 30-minute median is +0.0000 previous-day ranges and the 60-minute median is -0.0029. The open baseline, with no penetration condition, is +0.0000 at 30 minutes and +0.0000 at 60 minutes. Spearman of retracement penetration versus the range-normalized return is +0.023 at 30 minutes and +0.005 at 60 minutes. The frozen verdict above is the depth conclusion for this event. It does not reuse the discarded opening-bar touch.

### 2. Is the relationship stable across time?

Stability uses the same shallow, mid, and deep pools, now on retracement penetration. IS deep N=0 (not evaluable); Validation deep N=0 (not evaluable); OOS deep N=0 (not evaluable). A pool below N=50 cannot support the frozen stability claim. The years present are 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026. 2010 does not appear when almost none of its sessions passed the completeness rule. No year was kept or dropped after seeing its median.

### 3. Is it present on both bullish and bearish previous days?

Returns stay direction-normalized on the retracement sample. Bullish 0–10% session-end median is +0.0729 of the previous range (30m N=330), against an open baseline of +0.0621. Bearish 0–10% session-end median is -0.0635 (30m N=305), against an open baseline of -0.1242. Deep buckets at 30 minutes, 75–100% plus >100%, have N=0 on bullish previous days and N=0 on bearish previous days. A shared pattern requires both sides to clear the frozen pool rule. The non-causal maximum-penetration appendix is not a substitute: its session-end column can move because the session-end price is part of the path that defined the bin.

### 4. Does previous-day candle structure appear relevant?

Body-fraction 30m median span=0.0163 previous-day ranges. Spearman of body fraction vs 30m return: IS=-0.114, Validation=-0.064. The rank correlation of body fraction with maximum penetration is -0.287, and the wick fractions move the other way. That is mostly geometry: a small body leaves a shorter close-to-extreme distance, so the same point retracement is a larger penetration percent. It is not a forecast of the 30-minute return. This pass does not justify a dedicated structure test.

### 5. What mechanism, if any, deserves the next test?

Do not add ATR, a point-distance separation cutoff, a 50% level, a candle filter, a recovery rule, or an entry. The event in this report is already the later retracement after clean separation. First-bar range entries are excluded, and separation without a return stays an audit count. Candle structure did not clear its pre-registered descriptive bar.

## Safety checks

- PASS: previous session date is strictly earlier
- PASS: doji previous days are excluded
- PASS: direction uses only the completed previous candle
- PASS: reference range is the previous close-to-extreme distance
- PASS: forward returns exist only after a usable retracement
- PASS: separation is the first bar and the retracement is a later bar
- PASS: recomputed retracement, penetration, bucket, and next-open price on a sample
- PASS: no ATR, SMT, Fibonacci, or P&L columns
- PASS: penetration buckets were not refit
- PASS: no trading cost was applied

Confirmed absent: lookahead in the previous-day label, future bars redefining the retracement, forward returns inside the retracement bar, bucket edits after results, parameter optimization, ATR, SMT, order flow, volume profile, Fibonacci, lower-timeframe confirmation, recovery rules, and trading P&L.

## Figures

- `reports/figures/penetration_distributions.png`
- `reports/figures/separation_duration.png`
- `reports/figures/forward_vs_penetration.png`
- `reports/figures/median_forward_by_bucket.png`
- `reports/figures/mfe_mae_by_bucket.png`
- `reports/figures/bull_vs_bear.png`
- `reports/figures/year_stability.png`

Display histograms clip the horizontal axis at 150% penetration. Tables do not.

## How this was run

```
python strategies/46_prior_day_structure/code/run_mechanism.py
```

Working directory: repository root. `strategies/45_ict_ny_smt` already existed, so this study is folder 46 and does not share code with it.
