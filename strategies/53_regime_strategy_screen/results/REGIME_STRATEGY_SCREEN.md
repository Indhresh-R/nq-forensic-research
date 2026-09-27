# Regime-Conditioned Strategy Family Screen

**Strategy 53.** Screening study only. Market state is a routing variable.

## 1. Objective

Determine whether simple strategy families show positive path/expectancy **when applied only inside** the frozen Strategy 52 market condition where their mechanism should plausibly operate.

## 2. Frozen state definitions

Independent Strategy 52 flags (IS-frozen terciles; not re-fit): `flag_trending`, `flag_chop`, `flag_compression`, `flag_expansion` from `strategies/52_market_state_census/`.

## 3. Four regime → strategy mappings

| Cell | State | Family |
| --- | --- | --- |
| A | TRENDING | continuation |
| B | CHOP_RANGE (flag_chop) | mean reversion |
| C | COMPRESSION | breakout |
| D | EXPANSION | exhaustion / reversal |

## 4–6. Signal and execution definitions

As frozen in `PREREGISTRATION.md`. Common: entry `open[t+1]`, exit `close[t+15]`, cost **1.0** pt RT, no SL/TP.

## 7. Cost assumption

**1.0 NQ point** round-trip (mid). Gross and net both reported.

## 8. IS / Validation / OOS results

| cell_id | state_label | family | split | n_trades | signals_per_year | mean_gross | mean_net | median_net | win_rate | profit_factor | median_mfe_15 | median_mae_15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | TRENDING | continuation | IS | 274147 | 22845.58 | -0.0675 | -1.0675 | -1.0000 | 0.4172 | 0.7793 | 4.5000 | 4.5000 |
| A | TRENDING | continuation | Validation | 98494 | 32831.33 | 0.0542 | -0.9458 | -1.0000 | 0.4785 | 0.9197 | 16.5000 | 16.7500 |
| A | TRENDING | continuation | OOS | 49772 | 24886.00 | -0.1388 | -1.1388 | -1.2500 | 0.4800 | 0.9344 | 22.7500 | 22.7500 |
| B | CHOP_RANGE | mean_reversion | IS | 196852 | 16404.33 | -0.0411 | -1.0411 | -1.0000 | 0.3983 | 0.7362 | 3.5000 | 3.5000 |
| B | CHOP_RANGE | mean_reversion | Validation | 60162 | 20054.00 | -0.1240 | -1.1240 | -1.2500 | 0.4726 | 0.8917 | 14.5000 | 14.7500 |
| B | CHOP_RANGE | mean_reversion | OOS | 33442 | 16721.00 | -0.0204 | -1.0204 | -1.1250 | 0.4815 | 0.9272 | 18.7500 | 18.7500 |
| C | COMPRESSION | breakout | IS | 24501 | 2041.75 | -0.0341 | -1.0341 | -1.0000 | 0.4110 | 0.7859 | 4.5000 | 4.2500 |
| C | COMPRESSION | breakout | Validation | 9970 | 3323.33 | -0.6542 | -1.6542 | -0.7500 | 0.4826 | 0.8609 | 15.7500 | 16.0000 |
| C | COMPRESSION | breakout | OOS | 5246 | 2623.00 | -0.8961 | -1.8961 | -1.7500 | 0.4716 | 0.8867 | 20.5000 | 22.5000 |
| D | EXPANSION | exhaustion_reversal | IS | 143168 | 11930.67 | 0.3217 | -0.6783 | -0.7500 | 0.4255 | 0.8376 | 4.0000 | 4.0000 |
| D | EXPANSION | exhaustion_reversal | Validation | 41421 | 13807.00 | -0.3454 | -1.3454 | -1.0000 | 0.4786 | 0.8838 | 16.0000 | 16.2500 |
| D | EXPANSION | exhaustion_reversal | OOS | 21112 | 10556.00 | 0.4267 | -0.5733 | -0.2500 | 0.4963 | 0.9663 | 23.0000 | 22.5000 |


## 9. Year-by-year results

| cell_id | session_year | n_trades | mean_net | sum_net | win_rate |
| --- | --- | --- | --- | --- | --- |
| A | 2010 | 2986 | -1.0022 | -2992.50 | 0.3312 |
| A | 2011 | 7580 | -1.0328 | -7829.00 | 0.3563 |
| A | 2012 | 11639 | -1.0409 | -12115.50 | 0.3589 |
| A | 2013 | 21792 | -1.0537 | -22963.25 | 0.3392 |
| A | 2014 | 21739 | -1.0250 | -22283.50 | 0.3840 |
| A | 2015 | 25175 | -1.0872 | -27371.00 | 0.4071 |
| A | 2016 | 29090 | -0.9894 | -28780.25 | 0.4046 |
| A | 2017 | 27819 | -1.0107 | -28117.75 | 0.3884 |
| A | 2018 | 30303 | -1.2457 | -37747.25 | 0.4476 |
| A | 2019 | 30868 | -0.9542 | -29452.75 | 0.4387 |
| A | 2020 | 32859 | -1.2436 | -40862.50 | 0.4736 |
| A | 2021 | 32297 | -0.9949 | -32131.50 | 0.4732 |
| A | 2022 | 33839 | -1.0077 | -34098.00 | 0.4848 |
| A | 2023 | 31920 | -1.2559 | -40088.00 | 0.4706 |
| A | 2024 | 32735 | -0.5796 | -18974.25 | 0.4798 |
| A | 2025 | 30537 | -1.1619 | -35481.25 | 0.4782 |
| A | 2026 | 19235 | -1.1022 | -21200.50 | 0.4829 |
| B | 2010 | 2685 | -0.9913 | -2661.75 | 0.2883 |
| B | 2011 | 5609 | -1.1006 | -6173.50 | 0.3380 |
| B | 2012 | 8762 | -1.0942 | -9587.50 | 0.3392 |
| B | 2013 | 17883 | -1.0801 | -19316.00 | 0.3169 |
| B | 2014 | 17484 | -1.1335 | -19817.25 | 0.3634 |
| B | 2015 | 18905 | -1.2298 | -23248.50 | 0.3965 |
| B | 2016 | 21610 | -0.9648 | -20850.25 | 0.3974 |
| B | 2017 | 21693 | -0.9965 | -21617.25 | 0.3752 |
| B | 2018 | 20796 | -1.2830 | -26681.00 | 0.4258 |
| B | 2019 | 20716 | -1.0211 | -21153.75 | 0.4208 |
| B | 2020 | 19722 | -1.0321 | -20355.25 | 0.4543 |
| B | 2021 | 20987 | -0.6422 | -13477.00 | 0.4763 |
| B | 2022 | 19571 | -2.0211 | -39555.50 | 0.4702 |
| B | 2023 | 19982 | -0.7252 | -14490.00 | 0.4736 |
| B | 2024 | 20609 | -0.6587 | -13575.75 | 0.4738 |
| B | 2025 | 21332 | -0.6433 | -13722.75 | 0.4885 |
| B | 2026 | 12110 | -1.6846 | -20400.50 | 0.4692 |
| C | 2010 | 260 | -0.6481 | -168.50 | 0.3308 |
| C | 2011 | 654 | -0.7359 | -481.25 | 0.3838 |
| C | 2012 | 904 | -1.1662 | -1054.25 | 0.3363 |
| C | 2013 | 1766 | -0.8774 | -1549.50 | 0.3381 |
| C | 2014 | 1943 | -1.1759 | -2284.75 | 0.3464 |
| C | 2015 | 2260 | -0.8028 | -1814.25 | 0.4181 |
| C | 2016 | 2511 | -0.9562 | -2401.00 | 0.3986 |
| C | 2017 | 2238 | -0.9763 | -2185.00 | 0.3619 |
| C | 2018 | 2959 | -1.2848 | -3801.75 | 0.4437 |
| C | 2019 | 2583 | -1.3540 | -3497.50 | 0.4104 |
| C | 2020 | 3248 | -0.2973 | -965.75 | 0.4954 |
| C | 2021 | 3175 | -1.6164 | -5132.00 | 0.4472 |
| C | 2022 | 3507 | -0.9716 | -3407.25 | 0.5001 |
| C | 2023 | 3346 | -2.0412 | -6830.00 | 0.4791 |
| C | 2024 | 3117 | -2.0067 | -6254.75 | 0.4668 |
| C | 2025 | 3259 | -1.9410 | -6325.75 | 0.4701 |
| C | 2026 | 1987 | -1.8223 | -3621.00 | 0.4741 |
| D | 2010 | 1843 | -1.0948 | -2017.75 | 0.3321 |
| D | 2011 | 4341 | -0.8484 | -3682.75 | 0.3734 |
| D | 2012 | 7148 | -0.8924 | -6378.75 | 0.3802 |
| D | 2013 | 13658 | -0.8486 | -11590.75 | 0.3611 |
| D | 2014 | 12756 | -0.8975 | -11449.00 | 0.3978 |
| D | 2015 | 13999 | -0.9809 | -13732.00 | 0.4189 |
| D | 2016 | 16039 | -0.9551 | -15319.00 | 0.4155 |
| D | 2017 | 15070 | -0.8942 | -13475.50 | 0.4079 |
| D | 2018 | 14891 | -0.7820 | -11645.00 | 0.4614 |
| D | 2019 | 14299 | -0.8978 | -12837.25 | 0.4513 |
| D | 2020 | 14598 | 0.4781 | 6979.75 | 0.4767 |
| D | 2021 | 14526 | -0.1349 | -1959.50 | 0.4818 |
| D | 2022 | 14353 | -0.9032 | -12963.50 | 0.4861 |
| D | 2023 | 13555 | -1.3419 | -18189.00 | 0.4760 |
| D | 2024 | 13513 | -1.8187 | -24575.50 | 0.4734 |
| D | 2025 | 12826 | -0.5149 | -6604.50 | 0.4874 |
| D | 2026 | 8286 | -0.6636 | -5498.50 | 0.5100 |


## 10. Baseline comparison

| baseline | cell_id | split | n_trades | mean_net | mean_gross |
| --- | --- | --- | --- | --- | --- |
| shuffle_side | A | IS | 274147 | -0.9635 | 0.0365 |
| shuffle_side | A | Validation | 98494 | -0.9139 | 0.0861 |
| shuffle_side | A | OOS | 49772 | -0.7720 | 0.2280 |
| shuffle_side | B | IS | 196852 | -0.9917 | 0.0083 |
| shuffle_side | B | Validation | 60162 | -0.8205 | 0.1795 |
| shuffle_side | B | OOS | 33442 | -0.8151 | 0.1849 |
| shuffle_side | C | IS | 24501 | -0.9328 | 0.0672 |
| shuffle_side | C | Validation | 9970 | -0.3235 | 0.6765 |
| shuffle_side | C | OOS | 5246 | -1.8300 | -0.8300 |
| shuffle_side | D | IS | 143168 | -0.9367 | 0.0633 |
| shuffle_side | D | Validation | 41421 | -0.6781 | 0.3219 |
| shuffle_side | D | OOS | 21112 | -0.8111 | 0.1889 |
| all_bars_long | A | IS | 296047 | -0.9292 | 0.0708 |
| all_bars_long | A | Validation | 100201 | -1.2200 | -0.2200 |
| all_bars_long | A | OOS | 50422 | -0.7382 | 0.2618 |
| all_bars_short | A | IS | 296047 | -1.0708 | -0.0708 |
| all_bars_short | A | Validation | 100201 | -0.7800 | 0.2200 |
| all_bars_short | A | OOS | 50422 | -1.2618 | -0.2618 |
| all_bars_long | B | IS | 294869 | -0.9377 | 0.0623 |
| all_bars_long | B | Validation | 91478 | -0.8714 | 0.1286 |
| all_bars_long | B | OOS | 51196 | -0.5651 | 0.4349 |
| all_bars_short | B | IS | 294869 | -1.0623 | -0.0623 |
| all_bars_short | B | Validation | 91478 | -1.1286 | -0.1286 |
| all_bars_short | B | OOS | 51196 | -1.4349 | -0.4349 |
| all_bars_long | C | IS | 292914 | -0.9248 | 0.0752 |
| all_bars_long | C | Validation | 104970 | -0.8522 | 0.1478 |
| all_bars_long | C | OOS | 56541 | -0.9490 | 0.0510 |
| all_bars_short | C | IS | 292914 | -1.0752 | -0.0752 |
| all_bars_short | C | Validation | 104970 | -1.1478 | -0.1478 |
| all_bars_short | C | OOS | 56541 | -1.0510 | -0.0510 |
| all_bars_long | D | IS | 298101 | -1.0000 | -0.0000 |
| all_bars_long | D | Validation | 89411 | -0.9347 | 0.0653 |
| all_bars_long | D | OOS | 45183 | -0.7892 | 0.2108 |
| all_bars_short | D | IS | 298101 | -1.0000 | 0.0000 |
| all_bars_short | D | Validation | 89411 | -1.0653 | -0.0653 |
| all_bars_short | D | OOS | 45183 | -1.2108 | -0.2108 |


## 11. MFE / MAE path analysis

| cell_id | split | n | median_mfe_5 | median_mfe_15 | median_mae_5 | median_mae_15 |
| --- | --- | --- | --- | --- | --- | --- |
| A | IS | 274147 | 2.5000 | 4.5000 | 2.5000 | 4.5000 |
| A | Validation | 98494 | 9.5000 | 16.5000 | 9.7500 | 16.7500 |
| A | OOS | 49772 | 13.2500 | 22.7500 | 13.2500 | 22.7500 |
| A | ALL | 422413 | 4.2500 | 7.2500 | 4.2500 | 7.2500 |
| B | IS | 196852 | 2.0000 | 3.5000 | 2.0000 | 3.5000 |
| B | Validation | 60162 | 8.5000 | 14.5000 | 8.2500 | 14.7500 |
| B | OOS | 33442 | 10.7500 | 18.7500 | 10.7500 | 18.7500 |
| B | ALL | 290456 | 3.0000 | 5.5000 | 3.2500 | 5.7500 |
| C | IS | 24501 | 2.5000 | 4.5000 | 2.5000 | 4.2500 |
| C | Validation | 9970 | 9.0000 | 15.7500 | 9.5000 | 16.0000 |
| C | OOS | 5246 | 12.5000 | 20.5000 | 13.0000 | 22.5000 |
| C | ALL | 39717 | 4.2500 | 7.5000 | 4.2500 | 7.5000 |
| D | IS | 143168 | 2.2500 | 4.0000 | 2.2500 | 4.0000 |
| D | Validation | 41421 | 9.5000 | 16.0000 | 9.2500 | 16.2500 |
| D | OOS | 21112 | 13.5000 | 23.0000 | 13.2500 | 22.5000 |
| D | ALL | 205701 | 3.5000 | 6.0000 | 3.5000 | 6.0000 |


## 12. Leakage audit

```text
LOOKAHEAD_CHECK = PASS
STATE_AT_T_ONLY = True
SIGNAL_AT_T_ONLY = True
ENTRY_OPEN_T_PLUS_1 = True
NO_SAME_BAR_EXECUTION = True
NO_FUTURE_STATE = True
NO_OUTCOME_FILTERING = True
NO_PARAMETER_FIT_ON_VAL_OOS = True
PARAMETER_OPTIMIZATION = False
```

## 13. Multiple-testing statement

Exactly **four** primary hypotheses were preregistered. No additional variants, lookbacks, horizons, thresholds, or filters were added after seeing results.

## 14. Independent classification of each cell

- **A (TRENDING → continuation):** `REJECTED`
  - IS: n=274147, E_net=-1.0674811323851803, pass=False
  - Validation: n=98494, E_net=-0.9458469551444758, pass=False
  - OOS: n=49772, E_net=-1.1388280559350639, pass=False
- **B (CHOP_RANGE → mean_reversion):** `REJECTED`
  - IS: n=196852, E_net=-1.0410816247739418, pass=False
  - Validation: n=60162, E_net=-1.1239860709417906, pass=False
  - OOS: n=33442, E_net=-1.0203710902457988, pass=False
- **C (COMPRESSION → breakout):** `REJECTED`
  - IS: n=24501, E_net=-1.0340598342924778, pass=False
  - Validation: n=9970, E_net=-1.6541624874623873, pass=False
  - OOS: n=5246, E_net=-1.8960636675562332, pass=False
- **D (EXPANSION → exhaustion_reversal):** `REJECTED`
  - IS: n=143168, E_net=-0.6782765701832811, pass=False
  - Validation: n=41421, E_net=-1.3454045049612515, pass=False
  - OOS: n=21112, E_net=-0.5732758620689655, pass=False

A REJECTED or PATH-ONLY cell does **not** invalidate the market condition — only this representative rule inside that condition.

## 15. Recommended next research direction

No cell cleared PROMISING. Do **not** deepen Strategy 52 mechanics to rescue these representatives.

**Strategy 53 is COMPLETE / FROZEN.** See `COMPLETE.md`.

Next: **Strategy 54 — Transition Path Screen** (transition/event → path difference → only interesting transitions → later one simple execution). Do not invent another generic state→family test.

## Final research question

> Does routing simple, mechanically representative strategy families into the market conditions for which they are theoretically appropriate produce enough evidence to justify deeper research?

**Answer:** Not under this frozen four-cell screen — no PROMISING cell. State remains useful as a map; these representative rules do not graduate.
