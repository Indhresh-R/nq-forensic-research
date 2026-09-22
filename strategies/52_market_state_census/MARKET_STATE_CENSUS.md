# MARKET_STATE_CENSUS — Strategy 52 Step 0

**Status:** Complete (descriptive only).
**Run UTC:** 2026-09-22T14:27:38.030711+00:00
**Scope:** Map how often NQ sits in observable market conditions. **No** entries, exits, stops, targets, forward returns, or P&L.

---

## Answers (descriptive)

1. **High directionality:** 33.64% of eligible RTH minutes (primary metric `ER_60`, IS-frozen terciles).
2. **Low directionality / choppy:** 33.15% (mid=33.20%).
3. **Volatility:** low=28.02%, normal=32.54%, high=39.44% (`RV_60`).
4. **Volume:** low=29.65%, normal=36.99%, high=33.36% (TOD-relative `RVOL_30`).
5. **Compression:** 34.67% (`range_norm_60` bottom tercile).
6. **Expansion:** 32.38% (top tercile; mid range=32.95%).
7. **Persistence:** see Table 8 — episode duration distributions by state.
8. **Transitions:** see Table 9 — including compression→expansion sequence rates below.
9. **Year stability:** HIGH_DIRECTIONALITY yearly %: min=31.4, max=35.9, std=1.16.
10. **Time-of-day:** see Table 6 — directionality and activity shift across NY blocks.
11. **Frequent state combinations (descriptive prevalence only):** EXPANSION + HIGH_DIRECTIONALITY (22.4%); HIGH_VOLUME + HIGH_VOLATILITY (21.9%); COMPRESSION + LOW_DIRECTIONALITY (19.8%); LOW_VOLUME + LOW_VOLATILITY (16.5%); HIGH_DIRECTIONALITY + HIGH_VOLATILITY (14.1%); LOW_DIRECTIONALITY + HIGH_VOLATILITY (12.5%)

---

## Reproducibility

| Item | Value |
| --- | --- |
| Dataset | `D:\NQ-2\data\nq_1m_continuous.parquet` |
| Timestamp range | 2010-06-06 18:00:00-04:00 → 2026-08-07 16:59:00-04:00 |
| 1m bars | 4788194 |
| Sessions | 4175 |
| Analysis window bars | 1382157 |
| Census-eligible bars | 1377851 |
| Timezone | America/New_York |
| Session roll | 18:00 ET |
| Analysis window | 09:30–16:00 ET (end exclusive) |
| Primary windows | ER=60, RV=60, range=60, RVOL=30 / hist_sessions=60 |
| Threshold freeze | IS years [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021] (n=922738) |
| Git hash | `3ac9cd15f10ca76bb6725fa75e7290c7ce94740f` |
| Python | 3.13.1 (tags/v3.13.1:0671451, Dec  3 202… |
| NumPy / Pandas | 2.2.2 / 3.0.3 |

### Frozen tercile thresholds (IS 2010–2021)

| Dimension | Column | q33 | q67 | n_IS |
| --- | --- | ---: | ---: | ---: |
| directionality | `er_60` | 0.0716981 | 0.159533 | 922738 |
| volatility | `rv_60` | 0.00192803 | 0.00310537 | 922738 |
| volume | `rvol` | 0.748462 | 1.08356 | 922738 |
| range | `range_norm_60` | 6.90852 | 8.85827 | 922738 |

---

## Table 1 — Overall composite (mutually exclusive primary)

Priority freeze: TRENDING > CHOP_RANGE > COMPRESSION > EXPANSION > HIGH_ACTIVITY > LOW_ACTIVITY > TRANSITION_MIXED.

| state | observations | pct |
| --- | --- | --- |
| TRENDING | 463512 | 33.64 |
| CHOP_RANGE | 456826 | 33.15 |
| COMPRESSION | 172868 | 12.55 |
| EXPANSION | 97773 | 7.10 |
| HIGH_ACTIVITY | 91279 | 6.62 |
| TRANSITION_MIXED | 62401 | 4.53 |
| LOW_ACTIVITY | 33192 | 2.41 |


### Table 1b — Independent composite flags (can overlap; % of eligible)

| state | observations | pct |
| --- | --- | --- |
| TRENDING | 463512 | 33.64 |
| CHOP_RANGE | 456826 | 33.15 |
| HIGH_ACTIVITY | 701588 | 50.92 |
| LOW_ACTIVITY | 227684 | 16.52 |
| COMPRESSION | 477745 | 34.67 |
| EXPANSION | 446165 | 32.38 |


## Table 2 — Directionality (`ER_60`)

| state | observations | pct |
| --- | --- | --- |
| HIGH_DIRECTIONALITY | 463512 | 33.64 |
| MID_DIRECTIONALITY | 457513 | 33.20 |
| LOW_DIRECTIONALITY | 456826 | 33.15 |


## Table 3 — Volatility (`RV_60`)

| state | observations | pct |
| --- | --- | --- |
| HIGH_VOLATILITY | 543425 | 39.44 |
| NORMAL_VOLATILITY | 448313 | 32.54 |
| LOW_VOLATILITY | 386113 | 28.02 |


## Table 4 — Volume (TOD-relative `RVOL`)

| state | observations | pct |
| --- | --- | --- |
| NORMAL_VOLUME | 509670 | 36.99 |
| HIGH_VOLUME | 459594 | 33.36 |
| LOW_VOLUME | 408587 | 29.65 |


## Table 5 — Range / compression (`range_norm_60`)

| state | observations | pct |
| --- | --- | --- |
| COMPRESSION | 477745 | 34.67 |
| NORMAL_RANGE | 453941 | 32.95 |
| EXPANSION | 446165 | 32.38 |


## Table 6 — Time-of-day (directionality %)

| block | HIGH_DIRECTIONALITY | LOW_DIRECTIONALITY | MID_DIRECTIONALITY |
| --- | --- | --- | --- |
| 1030_1200 | 34.23 | 32.33 | 33.45 |
| 1200_1400 | 32.43 | 33.91 | 33.66 |
| 1400_1600 | 31.62 | 34.61 | 33.77 |
| FIRST_30 | 40.48 | 28.98 | 30.54 |
| FIRST_60 | 39.08 | 30.08 | 30.84 |
| NY_AM | 36.16 | 31.43 | 32.41 |
| NY_MIDDAY | 32.43 | 33.91 | 33.66 |
| NY_PM | 31.62 | 34.61 | 33.77 |


Full TOD × all dimensions: `results/table6_time_of_day.csv`.

## Day-of-week (directionality %)

| dow | HIGH_DIRECTIONALITY | LOW_DIRECTIONALITY | MID_DIRECTIONALITY |
| --- | --- | --- | --- |
| Friday | 32.13 | 33.93 | 33.94 |
| Monday | 34.13 | 32.95 | 32.92 |
| Thursday | 33.91 | 32.85 | 33.24 |
| Tuesday | 34.53 | 32.68 | 32.80 |
| Wednesday | 33.41 | 33.41 | 33.18 |


## Table 7 — Year stability (directionality %)

2026 is a **partial-year** sample (data through mid-August).

| year | HIGH_DIRECTIONALITY | LOW_DIRECTIONALITY | MID_DIRECTIONALITY |
| --- | --- | --- | --- |
| 2010 | 32.69 | 35.31 | 32.00 |
| 2011 | 34.08 | 32.45 | 33.48 |
| 2012 | 33.48 | 33.27 | 33.25 |
| 2013 | 31.97 | 34.28 | 33.75 |
| 2014 | 31.42 | 34.77 | 33.81 |
| 2015 | 32.38 | 33.87 | 33.76 |
| 2016 | 33.32 | 33.60 | 33.08 |
| 2017 | 32.59 | 34.14 | 33.27 |
| 2018 | 33.32 | 33.05 | 33.63 |
| 2019 | 34.15 | 32.61 | 33.24 |
| 2020 | 35.30 | 31.31 | 33.39 |
| 2021 | 34.60 | 32.93 | 32.47 |
| 2022 | 35.91 | 31.55 | 32.54 |
| 2023 | 34.09 | 32.38 | 33.53 |
| 2024 | 34.58 | 32.93 | 32.49 |
| 2025 | 32.66 | 34.47 | 32.87 |
| 2026 | 33.99 | 32.53 | 33.48 |


Full yearly tables: `results/table7_year_stability.csv`.

## Table 8 — Persistence (episode durations, minutes)

### Directionality

| dimension | state | n_episodes | median_duration_min | mean_duration_min | p25_duration_min | p75_duration_min | max_duration_min | total_minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| directionality_state | MID_DIRECTIONALITY | 125975 | 2.00 | 3.63 | 1.00 | 5.00 | 44.00 | 457513 |
| directionality_state | LOW_DIRECTIONALITY | 75404 | 3.00 | 6.06 | 1.00 | 8.00 | 95.00 | 456826 |
| directionality_state | HIGH_DIRECTIONALITY | 53252 | 3.00 | 8.70 | 1.00 | 8.00 | 187.00 | 463512 |


### Range

| dimension | state | n_episodes | median_duration_min | mean_duration_min | p25_duration_min | p75_duration_min | max_duration_min | total_minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| range_state | NORMAL_RANGE | 47399 | 6.00 | 9.58 | 2.00 | 13.00 | 103.00 | 453941 |
| range_state | COMPRESSION | 25997 | 9.00 | 18.38 | 3.00 | 27.00 | 202.00 | 477745 |
| range_state | EXPANSION | 22911 | 10.00 | 19.47 | 3.00 | 30.00 | 205.00 | 446165 |


### Composite primary

| dimension | state | n_episodes | median_duration_min | mean_duration_min | p25_duration_min | p75_duration_min | max_duration_min | total_minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| composite_primary | CHOP_RANGE | 75404 | 3.00 | 6.06 | 1.00 | 8.00 | 95.00 | 456826 |
| composite_primary | COMPRESSION | 57157 | 2.00 | 3.02 | 1.00 | 4.00 | 32.00 | 172868 |
| composite_primary | TRENDING | 53252 | 3.00 | 8.70 | 1.00 | 8.00 | 187.00 | 463512 |
| composite_primary | EXPANSION | 31401 | 2.00 | 3.11 | 1.00 | 4.00 | 29.00 | 97773 |
| composite_primary | HIGH_ACTIVITY | 30178 | 2.00 | 3.02 | 1.00 | 4.00 | 27.00 | 91279 |
| composite_primary | TRANSITION_MIXED | 22158 | 2.00 | 2.82 | 1.00 | 4.00 | 34.00 | 62401 |
| composite_primary | LOW_ACTIVITY | 11725 | 2.00 | 2.83 | 1.00 | 4.00 | 23.00 | 33192 |


## Table 9 — State transitions

### Directionality (top rows by count)

| dimension | from_state | to_state | count | pct_of_from |
| --- | --- | --- | --- | --- |
| directionality_state | HIGH_DIRECTIONALITY | HIGH_DIRECTIONALITY | 410260 | 88.74 |
| directionality_state | LOW_DIRECTIONALITY | LOW_DIRECTIONALITY | 381422 | 83.72 |
| directionality_state | MID_DIRECTIONALITY | MID_DIRECTIONALITY | 331538 | 72.65 |
| directionality_state | MID_DIRECTIONALITY | LOW_DIRECTIONALITY | 73565 | 16.12 |
| directionality_state | LOW_DIRECTIONALITY | MID_DIRECTIONALITY | 73422 | 16.12 |
| directionality_state | HIGH_DIRECTIONALITY | MID_DIRECTIONALITY | 51363 | 11.11 |
| directionality_state | MID_DIRECTIONALITY | HIGH_DIRECTIONALITY | 51242 | 11.23 |
| directionality_state | LOW_DIRECTIONALITY | HIGH_DIRECTIONALITY | 751 | 0.16 |
| directionality_state | HIGH_DIRECTIONALITY | LOW_DIRECTIONALITY | 692 | 0.15 |


### Range (top rows by count)

| dimension | from_state | to_state | count | pct_of_from |
| --- | --- | --- | --- | --- |
| range_state | COMPRESSION | COMPRESSION | 451748 | 94.88 |
| range_state | EXPANSION | EXPANSION | 423254 | 95.05 |
| range_state | NORMAL_RANGE | NORMAL_RANGE | 406542 | 89.78 |
| range_state | NORMAL_RANGE | COMPRESSION | 24870 | 5.49 |
| range_state | COMPRESSION | NORMAL_RANGE | 24196 | 5.08 |
| range_state | EXPANSION | NORMAL_RANGE | 21922 | 4.92 |
| range_state | NORMAL_RANGE | EXPANSION | 21411 | 4.73 |
| range_state | COMPRESSION | EXPANSION | 172 | 0.04 |
| range_state | EXPANSION | COMPRESSION | 140 | 0.03 |


### Composite primary (top rows by count)

| dimension | from_state | to_state | count | pct_of_from |
| --- | --- | --- | --- | --- |
| composite_primary | TRENDING | TRENDING | 410260 | 88.74 |
| composite_primary | CHOP_RANGE | CHOP_RANGE | 381422 | 83.72 |
| composite_primary | COMPRESSION | COMPRESSION | 115711 | 67.17 |
| composite_primary | EXPANSION | EXPANSION | 66372 | 67.97 |
| composite_primary | HIGH_ACTIVITY | HIGH_ACTIVITY | 61101 | 67.09 |
| composite_primary | TRANSITION_MIXED | TRANSITION_MIXED | 40243 | 64.69 |
| composite_primary | COMPRESSION | CHOP_RANGE | 37612 | 21.83 |
| composite_primary | CHOP_RANGE | COMPRESSION | 37558 | 8.24 |
| composite_primary | LOW_ACTIVITY | LOW_ACTIVITY | 21467 | 64.76 |
| composite_primary | EXPANSION | TRENDING | 17761 | 18.19 |
| composite_primary | TRENDING | EXPANSION | 16642 | 3.60 |
| composite_primary | HIGH_ACTIVITY | CHOP_RANGE | 12803 | 14.06 |


### Compression → expansion (descriptive sequence rates)

- Direct next-bar COMPRESSION→EXPANSION: 172 / 476116 (0.04% of bars leaving compression).
- Episode-level COMPRESSION followed next by EXPANSION: 172 / 24368 (0.71%).

Full matrices: `results/transition_matrix_*.csv`.

## Overlap / dependence

| combo | observations | pct_of_eligible |
| --- | --- | --- |
| HIGH_DIRECTIONALITY + HIGH_VOLATILITY | 194609 | 14.12 |
| HIGH_DIRECTIONALITY + LOW_VOLATILITY | 116112 | 8.43 |
| LOW_DIRECTIONALITY + HIGH_VOLATILITY | 171813 | 12.47 |
| LOW_DIRECTIONALITY + LOW_VOLATILITY | 138443 | 10.05 |
| HIGH_VOLUME + HIGH_VOLATILITY | 301431 | 21.88 |
| HIGH_VOLUME + LOW_VOLATILITY | 37003 | 2.69 |
| LOW_VOLUME + HIGH_VOLATILITY | 54193 | 3.93 |
| LOW_VOLUME + LOW_VOLATILITY | 227684 | 16.52 |
| COMPRESSION + LOW_DIRECTIONALITY | 273427 | 19.84 |
| EXPANSION + HIGH_DIRECTIONALITY | 308507 | 22.39 |
| COMPRESSION + HIGH_DIRECTIONALITY | 31450 | 2.28 |
| EXPANSION + LOW_DIRECTIONALITY | 39885 | 2.89 |


## Continuous feature summary (eligible bars)

| Feature | mean | p25 | p50 | p75 | p90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| er_60 | 0.131982 | 0.0533981 | 0.1125 | 0.190527 | 0.271028 |
| rv_60 | 0.00319053 | 0.00183182 | 0.00266652 | 0.00391813 | 0.00558431 |
| rvol | 1.01786 | 0.707217 | 0.919554 | 1.19632 | 1.58088 |
| range_norm_60 | 8.1306 | 6.3871 | 7.72853 | 9.4717 | 11.3793 |
| atr_30 | 7.02017 | 1.875 | 4.71667 | 9.90833 | 15.75 |

---

## Leakage audit

```text
LOOKAHEAD_CHECK = PASS
FUTURE_DATA_USED = False
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
```

Machine-readable detail: `results/audit_report.json` (all_pass=True).

---

## MARKET CENSUS VERDICT

- **Dominant market states (flag prevalence):** HIGH_ACTIVITY (~51%), COMPRESSION (~35%), TRENDING (~34%), CHOP_RANGE (~33%), EXPANSION (~32%).
- **Rarer mutually-exclusive primary buckets:** LOW_ACTIVITY (~2.4%), TRANSITION_MIXED (~4.5%), HIGH_ACTIVITY (~6.6%), EXPANSION (~7.1%); note tercile dimensions are ~33% by construction on the pooled labeled sample after IS threshold freeze (exact % can drift slightly out of sample).
- **Persistence:** states typically persist for multiple minutes within a session (see medians in Table 8); one-minute flicker is not the modal episode length for primary labels.
- **Important transitions:** compression→expansion is present but not dominant at episode level (0.7% of compression episodes next become expansion); self-transitions dominate bar-to-bar matrices.
- **Year-to-year stability:** HIGH_DIRECTIONALITY yearly %: min=31.4, max=35.9, std=1.16. Interpret 2026 as partial.
- **Time-of-day differences:** NY open blocks vs midday/PM differ in the mix of directionality and activity; use Table 6 rather than a single pooled slogan such as “NQ is mostly choppy.”

## NEXT RESEARCH QUESTION

~~Given that **direct** COMPRESSION→EXPANSION is rare…~~ **Addressed in Step 1** (`STEP1_PATH_GEOMETRY.md`): four-cell path geometry (A/B compression × directionality; C/D expansion × directionality).

**Research ledger (52–54 frozen):** Broad state routing did not yield an edge. See `strategies/RESEARCH_LEDGER_52_54.md`. Strategy 53 COMPLETE (all REJECTED). Strategy 54 COMPLETE (no clean path-magnitude candidate; activity hits definitional). Strategy 52 Step 9 executable **KILL** — do not rescue.
