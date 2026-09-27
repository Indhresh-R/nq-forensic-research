# 49 Daily directional streak persistence

**Verdict: NOT REAL**

NOT REAL. The preregistered null or matched-base continuation test does not show persistence.

- Clause A full null: fail. pooled_ge_3 observed 411, null mean 422.39, p_ge 0.8233; pooled_ge_4 observed 204, null mean 215.81, p_ge 0.8771
- Clause A OOS null (pooled_ge_3): fail. observed 40, null mean 49.53, p_ge 0.9891
- Clause B All L=2 and L=3: fail. lift -0.39 pp is not positive (n=821); lift -1.44 pp is not positive (n=411)
- Clause C OOS L=2 and L=3: fail. lift -8.56 pp is not positive (n=96); lift -5.37 pp is not positive (n=40)
- Clause D years: pass. L=2 positive years 6; L=3 positive years 6

No streak length was selected after seeing the tables. The continuation clause uses only pooled lengths 2 and 3. Length 1 is the one-day transition and is not a verdict input. Buckets with n < 30 are descriptive. A result that looks large against 50% is not evidence.

## 1. Hypothesis

Same-direction Globex sessions may form streaks that are longer, or that continue more often, than the unconditional bull and bear rates already imply. The test is not whether one bull or bear day predicts the next day.

## 2. Session definition

NQ continuous futures. One candle per complete Globex session from Strategy 48 `load_candles()`, unmodified. The session rolls at 18:00 America/New_York. Open is the first price, high the session high, low the session low, close the last price. This is not a NAS100 cash CFD candle and not an RTH-only candle.

Bull means close above open. Bear means close below open. Flat means close equal to open. A flat day ends a streak and is not a bull or bear streak. Inside each sample, the next day is the next kept session in that sample.

## 3. Sample

- Bars: 4788194
- Sessions before the completeness filter: 4175
- Complete sessions: 3400
- Incomplete sessions dropped: 775 (n_bars<1100,no_1600_hour=603, n_bars<1100,open_not_in_1800_1805,no_1600_hour=11, n_bars<1100=63, n_bars<1100,open_not_in_1800_1805=8, open_not_in_1800_1805=9, no_1600_hour=81)
- Bars with high < low: 0
- First kept session: 2010-06-07
- Last kept session: 2026-08-07

IS is 2010–2021, Validation is 2022–2024, OOS is 2025–2026, by the session year. Each sample is sequenced on its own. A streak does not continue across a sample boundary.

## 4. Bull and bear base rates

Rates use every session in the sample, including flats, as the denominator.

Sessions 3400. Bull 1887 (55.50%). Bear 1503 (44.21%). Flat 10 (0.29%).

IS: Sessions 2256. Bull 1282 (56.83%). Bear 965 (42.77%). Flat 9 (0.40%).

Validation: Sessions 747. Bull 392 (52.48%). Bear 354 (47.39%). Flat 1 (0.13%).

OOS: Sessions 397. Bull 213 (53.65%). Bear 184 (46.35%). Flat 0 (0.00%).

## 5–10. Distribution, continuation, null, and asymmetry

Lift is observed continuation minus the matched base, in percentage points. The bull matched base is the sample bull rate. The bear matched base is the sample bear rate. The pooled matched base weights those two rates by the bull and bear observations inside the bucket. The permutation shuffles labels and keeps the bull, bear, and flat counts. 10,000 draws, seed 49, one-sided p_ge = share of draws at least as large as the observed count.

### All

Sessions 3400. Bull 1887 (55.50%). Bear 1503 (44.21%). Flat 10 (0.29%).

Streak distribution

| side | length | streaks | pct of all streaks | pct of this side | sessions inside |
| --- | --- | --- | --- | --- | --- |
| pooled | 1 | 905 | 52.43% | 52.43% | 905 |
| pooled | 2 | 410 | 23.75% | 23.75% | 820 |
| pooled | 3 | 207 | 11.99% | 11.99% | 621 |
| pooled | 4 | 87 | 5.04% | 5.04% | 348 |
| pooled | 5 | 66 | 3.82% | 3.82% | 330 |
| pooled | 6 | 21 | 1.22% | 1.22% | 126 |
| pooled | >=7 | 30 | 1.74% | 1.74% | 240 |
| bull | 1 | 410 | 23.75% | 47.45% | 410 |
| bull | 2 | 204 | 11.82% | 23.61% | 408 |
| bull | 3 | 113 | 6.55% | 13.08% | 339 |
| bull | 4 | 51 | 2.95% | 5.90% | 204 |
| bull | 5 | 47 | 2.72% | 5.44% | 235 |
| bull | 6 | 12 | 0.70% | 1.39% | 72 |
| bull | >=7 | 27 | 1.56% | 3.12% | 219 |
| bear | 1 | 495 | 28.68% | 57.42% | 495 |
| bear | 2 | 206 | 11.94% | 23.90% | 412 |
| bear | 3 | 94 | 5.45% | 10.90% | 282 |
| bear | 4 | 36 | 2.09% | 4.18% | 144 |
| bear | 5 | 19 | 1.10% | 2.20% | 95 |
| bear | 6 | 9 | 0.52% | 1.04% | 54 |
| bear | >=7 | 3 | 0.17% | 0.35% | 21 |

Continuation and matched-base lift. Survival given current length is this same rate.

| side | length | n | observed | matched base | lift pp | n<30 |
| --- | --- | --- | --- | --- | --- | --- |
| bull | 1 | 863 | 52.61% | 55.50% | -2.89 |  |
| bull | 2 | 454 | 55.07% | 55.50% | -0.43 |  |
| bull | 3 | 250 | 54.80% | 55.50% | -0.70 |  |
| bull | 4 | 137 | 62.77% | 55.50% | +7.27 |  |
| bull | 5 | 86 | 45.35% | 55.50% | -10.15 |  |
| bull | 6 | 39 | 69.23% | 55.50% | +13.73 |  |
| bull | >=7 | 57 | 52.63% | 55.50% | -2.87 |  |
| bear | 1 | 862 | 42.58% | 44.21% | -1.63 |  |
| bear | 2 | 367 | 43.87% | 44.21% | -0.34 |  |
| bear | 3 | 161 | 41.61% | 44.21% | -2.59 |  |
| bear | 4 | 67 | 46.27% | 44.21% | +2.06 |  |
| bear | 5 | 31 | 38.71% | 44.21% | -5.50 |  |
| bear | 6 | 12 | 25.00% | 44.21% | -19.21 | yes |
| bear | >=7 | 3 | 0.00% | 44.21% | -44.21 | yes |
| pooled | 1 | 1725 | 47.59% | 49.86% | -2.26 |  |
| pooled | 2 | 821 | 50.06% | 50.45% | -0.39 |  |
| pooled | 3 | 411 | 49.64% | 51.08% | -1.44 |  |
| pooled | 4 | 204 | 57.35% | 51.79% | +5.56 |  |
| pooled | 5 | 117 | 43.59% | 52.51% | -8.92 |  |
| pooled | 6 | 51 | 58.82% | 52.84% | +5.98 |  |
| pooled | >=7 | 60 | 50.00% | 54.94% | -4.94 |  |

Randomized null

| statistic | observed | null mean | null p50 | null p95 | percentile | null >= observed | p_ge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max_bull | 14 | 12.91 | 13.0 | 17.0 | 80.3 | 3244/10000 | 0.3244 |
| max_bear | 7 | 9.43 | 9.0 | 12.0 | 6.1 | 9984/10000 | 0.9984 |
| bull_ge_3 | 250 | 258.62 | 259.0 | 273.0 | 17.0 | 8614/10000 | 0.8614 |
| bear_ge_3 | 161 | 163.76 | 164.0 | 176.0 | 38.3 | 6649/10000 | 0.6649 |
| bull_ge_4 | 137 | 143.46 | 143.0 | 155.0 | 20.1 | 8328/10000 | 0.8328 |
| bear_ge_4 | 67 | 72.35 | 72.0 | 83.0 | 22.1 | 8203/10000 | 0.8203 |
| bull_ge_5 | 86 | 79.56 | 80.0 | 90.0 | 87.4 | 1647/10000 | 0.1647 |
| bear_ge_5 | 31 | 31.89 | 32.0 | 40.0 | 47.5 | 6106/10000 | 0.6106 |
| pooled_ge_3 | 411 | 422.39 | 422.0 | 443.0 | 19.6 | 8233/10000 | 0.8233 |
| pooled_ge_4 | 204 | 215.81 | 216.0 | 234.0 | 14.4 | 8771/10000 | 0.8771 |
| pooled_ge_5 | 117 | 111.45 | 111.0 | 126.0 | 76.3 | 2762/10000 | 0.2762 |

Bull versus bear streak lengths

| side | streaks | mean | median | max |
| --- | --- | --- | --- | --- |
| bull | 864 | 2.18 | 2.00 | 14 |
| bear | 862 | 1.74 | 1.00 | 7 |

### IS

Sessions 2256. Bull 1282 (56.83%). Bear 965 (42.77%). Flat 9 (0.40%).

Streak distribution

| side | length | streaks | pct of all streaks | pct of this side | sessions inside |
| --- | --- | --- | --- | --- | --- |
| pooled | 1 | 615 | 53.62% | 53.62% | 615 |
| pooled | 2 | 259 | 22.58% | 22.58% | 518 |
| pooled | 3 | 134 | 11.68% | 11.68% | 402 |
| pooled | 4 | 57 | 4.97% | 4.97% | 228 |
| pooled | 5 | 47 | 4.10% | 4.10% | 235 |
| pooled | 6 | 14 | 1.22% | 1.22% | 84 |
| pooled | >=7 | 21 | 1.83% | 1.83% | 165 |
| bull | 1 | 274 | 23.89% | 47.74% | 274 |
| bull | 2 | 123 | 10.72% | 21.43% | 246 |
| bull | 3 | 76 | 6.63% | 13.24% | 228 |
| bull | 4 | 35 | 3.05% | 6.10% | 140 |
| bull | 5 | 39 | 3.40% | 6.79% | 195 |
| bull | 6 | 8 | 0.70% | 1.39% | 48 |
| bull | >=7 | 19 | 1.66% | 3.31% | 151 |
| bear | 1 | 341 | 29.73% | 59.51% | 341 |
| bear | 2 | 136 | 11.86% | 23.73% | 272 |
| bear | 3 | 58 | 5.06% | 10.12% | 174 |
| bear | 4 | 22 | 1.92% | 3.84% | 88 |
| bear | 5 | 8 | 0.70% | 1.40% | 40 |
| bear | 6 | 6 | 0.52% | 1.05% | 36 |
| bear | >=7 | 2 | 0.17% | 0.35% | 14 |

Continuation and matched-base lift. Survival given current length is this same rate.

| side | length | n | observed | matched base | lift pp | n<30 |
| --- | --- | --- | --- | --- | --- | --- |
| bull | 1 | 574 | 52.26% | 56.83% | -4.56 |  |
| bull | 2 | 300 | 59.00% | 56.83% | +2.17 |  |
| bull | 3 | 177 | 57.06% | 56.83% | +0.24 |  |
| bull | 4 | 101 | 65.35% | 56.83% | +8.52 |  |
| bull | 5 | 66 | 40.91% | 56.83% | -15.92 |  |
| bull | 6 | 27 | 70.37% | 56.83% | +13.54 | yes |
| bull | >=7 | 37 | 48.65% | 56.83% | -8.18 |  |
| bear | 1 | 573 | 40.49% | 42.77% | -2.29 |  |
| bear | 2 | 232 | 41.38% | 42.77% | -1.40 |  |
| bear | 3 | 96 | 39.58% | 42.77% | -3.19 |  |
| bear | 4 | 37 | 43.24% | 42.77% | +0.47 |  |
| bear | 5 | 16 | 50.00% | 42.77% | +7.23 | yes |
| bear | 6 | 8 | 25.00% | 42.77% | -17.77 | yes |
| bear | >=7 | 2 | 0.00% | 42.77% | -42.77 | yes |
| pooled | 1 | 1147 | 46.38% | 49.81% | -3.42 |  |
| pooled | 2 | 532 | 51.32% | 50.70% | +0.62 |  |
| pooled | 3 | 273 | 50.92% | 51.89% | -0.97 |  |
| pooled | 4 | 138 | 59.42% | 53.06% | +6.36 |  |
| pooled | 5 | 82 | 42.68% | 54.08% | -11.40 |  |
| pooled | 6 | 35 | 60.00% | 53.61% | +6.39 |  |
| pooled | >=7 | 39 | 46.15% | 56.11% | -9.95 |  |

Randomized null

| statistic | observed | null mean | null p50 | null p95 | percentile | null >= observed | p_ge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max_bull | 10 | 12.66 | 12.0 | 17.0 | 14.4 | 9708/10000 | 0.9708 |
| max_bear | 7 | 8.61 | 8.0 | 11.0 | 23.7 | 9657/10000 | 0.9657 |
| bull_ge_3 | 177 | 178.83 | 179.0 | 191.0 | 42.6 | 6286/10000 | 0.6286 |
| bear_ge_3 | 96 | 100.96 | 101.0 | 111.0 | 23.5 | 8147/10000 | 0.8147 |
| bull_ge_4 | 101 | 101.49 | 101.0 | 111.0 | 50.5 | 5636/10000 | 0.5636 |
| bear_ge_4 | 38 | 43.09 | 43.0 | 51.0 | 17.6 | 8726/10000 | 0.8726 |
| bull_ge_5 | 66 | 57.55 | 58.0 | 66.0 | 96.4 | 554/10000 | 0.0554 |
| bear_ge_5 | 16 | 18.45 | 18.0 | 25.0 | 30.2 | 7885/10000 | 0.7885 |
| pooled_ge_3 | 273 | 279.79 | 280.0 | 296.0 | 26.6 | 7665/10000 | 0.7665 |
| pooled_ge_4 | 139 | 144.58 | 144.0 | 159.0 | 27.6 | 7606/10000 | 0.7606 |
| pooled_ge_5 | 82 | 76.00 | 76.0 | 87.0 | 82.6 | 2113/10000 | 0.2113 |

Bull versus bear streak lengths

| side | streaks | mean | median | max |
| --- | --- | --- | --- | --- |
| bull | 574 | 2.23 | 2.00 | 10 |
| bear | 573 | 1.68 | 1.00 | 7 |

### Validation

Sessions 747. Bull 392 (52.48%). Bear 354 (47.39%). Flat 1 (0.13%).

Streak distribution

| side | length | streaks | pct of all streaks | pct of this side | sessions inside |
| --- | --- | --- | --- | --- | --- |
| pooled | 1 | 179 | 48.12% | 48.12% | 179 |
| pooled | 2 | 95 | 25.54% | 25.54% | 190 |
| pooled | 3 | 51 | 13.71% | 13.71% | 153 |
| pooled | 4 | 26 | 6.99% | 6.99% | 104 |
| pooled | 5 | 13 | 3.49% | 3.49% | 65 |
| pooled | 6 | 3 | 0.81% | 0.81% | 18 |
| pooled | >=7 | 5 | 1.34% | 1.34% | 37 |
| bull | 1 | 83 | 22.31% | 44.62% | 83 |
| bull | 2 | 52 | 13.98% | 27.96% | 104 |
| bull | 3 | 26 | 6.99% | 13.98% | 78 |
| bull | 4 | 12 | 3.23% | 6.45% | 48 |
| bull | 5 | 6 | 1.61% | 3.23% | 30 |
| bull | 6 | 2 | 0.54% | 1.08% | 12 |
| bull | >=7 | 5 | 1.34% | 2.69% | 37 |
| bear | 1 | 96 | 25.81% | 51.61% | 96 |
| bear | 2 | 43 | 11.56% | 23.12% | 86 |
| bear | 3 | 25 | 6.72% | 13.44% | 75 |
| bear | 4 | 14 | 3.76% | 7.53% | 56 |
| bear | 5 | 7 | 1.88% | 3.76% | 35 |
| bear | 6 | 1 | 0.27% | 0.54% | 6 |
| bear | >=7 | 0 | 0.00% | 0.00% | 0 |

Continuation and matched-base lift. Survival given current length is this same rate.

| side | length | n | observed | matched base | lift pp | n<30 |
| --- | --- | --- | --- | --- | --- | --- |
| bull | 1 | 186 | 55.38% | 52.48% | +2.90 |  |
| bull | 2 | 103 | 49.51% | 52.48% | -2.96 |  |
| bull | 3 | 51 | 49.02% | 52.48% | -3.46 |  |
| bull | 4 | 25 | 52.00% | 52.48% | -0.48 | yes |
| bull | 5 | 13 | 53.85% | 52.48% | +1.37 | yes |
| bull | 6 | 7 | 71.43% | 52.48% | +18.95 | yes |
| bull | >=7 | 7 | 28.57% | 52.48% | -23.91 | yes |
| bear | 1 | 186 | 48.39% | 47.39% | +1.00 |  |
| bear | 2 | 90 | 52.22% | 47.39% | +4.83 |  |
| bear | 3 | 47 | 46.81% | 47.39% | -0.58 |  |
| bear | 4 | 21 | 38.10% | 47.39% | -9.29 | yes |
| bear | 5 | 8 | 12.50% | 47.39% | -34.89 | yes |
| bear | 6 | 1 | 0.00% | 47.39% | -47.39 | yes |
| bear | >=7 | 0 | NA | NA | NA | yes |
| pooled | 1 | 372 | 51.88% | 49.93% | +1.95 |  |
| pooled | 2 | 193 | 50.78% | 50.10% | +0.67 |  |
| pooled | 3 | 98 | 47.96% | 50.04% | -2.08 |  |
| pooled | 4 | 46 | 45.65% | 50.15% | -4.50 |  |
| pooled | 5 | 21 | 38.10% | 50.54% | -12.44 | yes |
| pooled | 6 | 8 | 62.50% | 51.84% | +10.66 | yes |
| pooled | >=7 | 7 | 28.57% | 52.48% | -23.91 | yes |

Randomized null

| statistic | observed | null mean | null p50 | null p95 | percentile | null >= observed | p_ge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max_bull | 8 | 9.49 | 9.0 | 13.0 | 33.9 | 8833/10000 | 0.8833 |
| max_bear | 6 | 8.27 | 8.0 | 11.0 | 10.8 | 9933/10000 | 0.9933 |
| bull_ge_3 | 51 | 51.27 | 51.0 | 58.0 | 52.8 | 5751/10000 | 0.5751 |
| bear_ge_3 | 47 | 41.73 | 42.0 | 48.0 | 94.1 | 994/10000 | 0.0994 |
| bull_ge_4 | 25 | 26.86 | 27.0 | 32.0 | 33.7 | 7660/10000 | 0.7660 |
| bear_ge_4 | 22 | 19.73 | 20.0 | 25.0 | 81.9 | 2792/10000 | 0.2792 |
| bull_ge_5 | 13 | 14.02 | 14.0 | 19.0 | 43.3 | 7016/10000 | 0.7016 |
| bear_ge_5 | 8 | 9.31 | 9.0 | 13.0 | 37.3 | 7725/10000 | 0.7725 |
| pooled_ge_3 | 98 | 93.00 | 93.0 | 103.0 | 82.5 | 2220/10000 | 0.2220 |
| pooled_ge_4 | 47 | 46.59 | 47.0 | 55.0 | 57.6 | 5001/10000 | 0.5001 |
| pooled_ge_5 | 21 | 23.33 | 23.0 | 30.0 | 33.7 | 7506/10000 | 0.7506 |

Bull versus bear streak lengths

| side | streaks | mean | median | max |
| --- | --- | --- | --- | --- |
| bull | 186 | 2.11 | 2.00 | 8 |
| bear | 186 | 1.90 | 1.00 | 6 |

### OOS

Sessions 397. Bull 213 (53.65%). Bear 184 (46.35%). Flat 0 (0.00%).

Streak distribution

| side | length | streaks | pct of all streaks | pct of this side | sessions inside |
| --- | --- | --- | --- | --- | --- |
| pooled | 1 | 112 | 53.85% | 53.85% | 112 |
| pooled | 2 | 56 | 26.92% | 26.92% | 112 |
| pooled | 3 | 22 | 10.58% | 10.58% | 66 |
| pooled | 4 | 5 | 2.40% | 2.40% | 20 |
| pooled | 5 | 5 | 2.40% | 2.40% | 25 |
| pooled | 6 | 4 | 1.92% | 1.92% | 24 |
| pooled | >=7 | 4 | 1.92% | 1.92% | 38 |
| bull | 1 | 53 | 25.48% | 50.96% | 53 |
| bull | 2 | 29 | 13.94% | 27.88% | 58 |
| bull | 3 | 11 | 5.29% | 10.58% | 33 |
| bull | 4 | 4 | 1.92% | 3.85% | 16 |
| bull | 5 | 2 | 0.96% | 1.92% | 10 |
| bull | 6 | 2 | 0.96% | 1.92% | 12 |
| bull | >=7 | 3 | 1.44% | 2.88% | 31 |
| bear | 1 | 59 | 28.37% | 56.73% | 59 |
| bear | 2 | 27 | 12.98% | 25.96% | 54 |
| bear | 3 | 11 | 5.29% | 10.58% | 33 |
| bear | 4 | 1 | 0.48% | 0.96% | 4 |
| bear | 5 | 3 | 1.44% | 2.88% | 15 |
| bear | 6 | 2 | 0.96% | 1.92% | 12 |
| bear | >=7 | 1 | 0.48% | 0.96% | 7 |

Continuation and matched-base lift. Survival given current length is this same rate.

| side | length | n | observed | matched base | lift pp | n<30 |
| --- | --- | --- | --- | --- | --- | --- |
| bull | 1 | 103 | 49.51% | 53.65% | -4.14 |  |
| bull | 2 | 51 | 43.14% | 53.65% | -10.52 |  |
| bull | 3 | 22 | 50.00% | 53.65% | -3.65 | yes |
| bull | 4 | 11 | 63.64% | 53.65% | +9.98 | yes |
| bull | 5 | 7 | 71.43% | 53.65% | +17.78 | yes |
| bull | 6 | 5 | 60.00% | 53.65% | +6.35 | yes |
| bull | >=7 | 13 | 76.92% | 53.65% | +23.27 | yes |
| bear | 1 | 104 | 43.27% | 46.35% | -3.08 |  |
| bear | 2 | 45 | 40.00% | 46.35% | -6.35 |  |
| bear | 3 | 18 | 38.89% | 46.35% | -7.46 | yes |
| bear | 4 | 7 | 85.71% | 46.35% | +39.37 | yes |
| bear | 5 | 6 | 50.00% | 46.35% | +3.65 | yes |
| bear | 6 | 3 | 33.33% | 46.35% | -13.01 | yes |
| bear | >=7 | 1 | 0.00% | 46.35% | -46.35 | yes |
| pooled | 1 | 207 | 46.38% | 49.98% | -3.61 |  |
| pooled | 2 | 96 | 41.67% | 50.23% | -8.56 |  |
| pooled | 3 | 40 | 45.00% | 50.37% | -5.37 |  |
| pooled | 4 | 18 | 72.22% | 50.81% | +21.41 | yes |
| pooled | 5 | 13 | 61.54% | 50.28% | +11.26 | yes |
| pooled | 6 | 8 | 50.00% | 50.91% | -0.91 | yes |
| pooled | >=7 | 14 | 71.43% | 53.13% | +18.30 | yes |

Randomized null

| statistic | observed | null mean | null p50 | null p95 | percentile | null >= observed | p_ge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max_bull | 14 | 8.80 | 8.0 | 12.0 | 98.9 | 228/10000 | 0.0228 |
| max_bear | 7 | 7.21 | 7.0 | 10.0 | 64.7 | 6247/10000 | 0.6247 |
| bull_ge_3 | 22 | 28.39 | 28.0 | 33.0 | 2.0 | 9928/10000 | 0.9928 |
| bear_ge_3 | 18 | 21.14 | 21.0 | 26.0 | 16.4 | 9098/10000 | 0.9098 |
| bull_ge_4 | 11 | 15.13 | 15.0 | 19.0 | 6.0 | 9762/10000 | 0.9762 |
| bear_ge_4 | 7 | 9.71 | 10.0 | 13.0 | 16.0 | 9311/10000 | 0.9311 |
| bull_ge_5 | 7 | 8.06 | 8.0 | 11.0 | 39.5 | 7772/10000 | 0.7772 |
| bear_ge_5 | 6 | 4.44 | 4.0 | 7.0 | 88.2 | 2611/10000 | 0.2611 |
| pooled_ge_3 | 40 | 49.53 | 50.0 | 56.0 | 1.9 | 9891/10000 | 0.9891 |
| pooled_ge_4 | 18 | 24.84 | 25.0 | 31.0 | 4.0 | 9774/10000 | 0.9774 |
| pooled_ge_5 | 13 | 12.50 | 12.0 | 17.0 | 63.9 | 4987/10000 | 0.4987 |

Bull versus bear streak lengths

| side | streaks | mean | median | max |
| --- | --- | --- | --- | --- |
| bull | 104 | 2.05 | 1.00 | 14 |
| bear | 104 | 1.77 | 1.00 | 7 |

## 11. Year by year

Each year is its own sequence. A continuation cell is NA when that cell has fewer than 5 observations. The year clause in the verdict uses pooled lengths 2 and 3 and ignores a year cell with n < 20.

| year | n | bull rate | bear rate | avg bull | med bull | max bull | avg bear | med bear | max bear | bull after 1 | bull after 2 | bull after 3 | bear after 1 | bear after 2 | bear after 3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2010 | 29 | 55.17% | 44.83% | 2.29 | 1.0 | 7 | 1.86 | 1.0 | 4 | 50.00% | NA | NA | 42.86% | NA | NA |
| 2011 | 63 | 57.14% | 41.27% | 2.25 | 1.0 | 7 | 1.73 | 2.0 | 3 | 43.75% | 57.14% | NA | 60.00% | 25.00% | NA |
| 2012 | 100 | 55.00% | 44.00% | 2.12 | 1.0 | 7 | 1.69 | 1.0 | 4 | 48.00% | 66.67% | 50.00% | 46.15% | 41.67% | 20.00% |
| 2013 | 177 | 58.19% | 41.24% | 2.24 | 2.0 | 5 | 1.66 | 1.5 | 4 | 63.04% | 57.14% | 50.00% | 50.00% | 27.27% | 16.67% |
| 2014 | 181 | 56.91% | 43.09% | 2.34 | 2.0 | 9 | 1.73 | 1.0 | 4 | 54.55% | 54.17% | 61.54% | 47.73% | 47.62% | 20.00% |
| 2015 | 212 | 51.42% | 48.11% | 2.22 | 2.0 | 6 | 2.00 | 2.0 | 5 | 57.14% | 64.29% | 44.44% | 56.86% | 46.43% | 53.85% |
| 2016 | 251 | 51.79% | 47.81% | 1.86 | 1.0 | 8 | 1.71 | 1.0 | 6 | 40.00% | 64.29% | 33.33% | 37.14% | 53.85% | 46.15% |
| 2017 | 249 | 63.45% | 36.55% | 2.47 | 1.0 | 10 | 1.42 | 1.0 | 5 | 48.44% | 64.52% | 75.00% | 26.56% | 29.41% | 60.00% |
| 2018 | 247 | 53.85% | 45.75% | 2.08 | 1.0 | 8 | 1.82 | 1.0 | 7 | 49.21% | 51.61% | 56.25% | 41.94% | 50.00% | 46.15% |
| 2019 | 249 | 60.24% | 39.36% | 2.34 | 2.0 | 6 | 1.53 | 1.0 | 6 | 55.56% | 68.57% | 58.33% | 37.50% | 16.67% | NA |
| 2020 | 247 | 60.32% | 38.87% | 2.37 | 2.0 | 10 | 1.52 | 1.0 | 6 | 53.23% | 54.55% | 83.33% | 28.57% | 44.44% | 37.50% |
| 2021 | 251 | 55.78% | 44.22% | 2.19 | 2.0 | 9 | 1.71 | 1.0 | 6 | 57.81% | 54.05% | 50.00% | 40.00% | 46.15% | 41.67% |
| 2022 | 250 | 46.00% | 54.00% | 1.77 | 2.0 | 5 | 2.11 | 2.0 | 6 | 50.77% | 40.62% | 23.08% | 56.25% | 55.56% | 50.00% |
| 2023 | 248 | 56.05% | 43.95% | 2.32 | 2.0 | 8 | 1.79 | 1.0 | 5 | 60.00% | 55.56% | 60.00% | 44.26% | 53.85% | 42.86% |
| 2024 | 249 | 55.42% | 44.18% | 2.26 | 2.0 | 8 | 1.77 | 1.0 | 5 | 55.74% | 52.94% | 55.56% | 45.16% | 46.43% | 38.46% |
| 2025 | 247 | 53.44% | 46.56% | 1.91 | 1.0 | 8 | 1.64 | 1.0 | 7 | 44.93% | 51.61% | 50.00% | 35.71% | 36.00% | 55.56% |
| 2026 | 150 | 54.00% | 46.00% | 2.31 | 2.0 | 14 | 1.97 | 2.0 | 6 | 58.82% | 30.00% | 50.00% | 57.14% | 45.00% | 22.22% |

## 12. Interpretation

Long runs of green or red days are expected once the base rate is above one half. The permutation asks whether the observed run counts still stand out after that base rate is locked in. The continuation table asks whether a streak that has already reached length 2 or 3 is more likely to extend than the base rate. Length 1 answers a different question and is not used to pass the test.

## 13. Verdict

NOT REAL

NOT REAL. The preregistered null or matched-base continuation test does not show persistence.

This file does not contain an entry, a stop, or a P&L.
