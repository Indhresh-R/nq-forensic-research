# Step 2 — Transition-event mechanics

**Status:** Complete (mechanism description only).
**Parent:** Steps 0–1 frozen labels / cells / episode onsets.
**Forbidden:** entries, exits, stops, targets, signed P&L, optimization.

---

## Question

Does the **transition event** separate subsequent path geometry when the persistent state label (Step 1) did not?

| Contrast | Event |
| --- | --- |
| A vs B | first `COMPRESSION → NORMAL` after A/B onset |
| C vs D | first `EXPANSION → NORMAL` after C/D onset |

Event timestamp = **first NORMAL bar**. Path = strictly subsequent 5/15/30/60m.
At most one event per episode onset.

---

## Funnel

| Item | Count |
| --- | ---: |
| Episode onsets | 140102 |
| Qualifying →NORMAL events | 54099 |
| Censored: session_end_or_gap | 2797 |
| Censored: hit_opposite_range_before_normal | 413 |
| Censored: switched_abcd_cell_before_normal | 82793 |
| Censored: no_normal_before_end | 0 |

### Events by origin

| Origin | Events |
| --- | ---: |
| A_COMP_LOW_DIR | 9283 |
| B_COMP_MIDHIGH_DIR | 14913 |
| C_EXP_HIGH_DIR | 24298 |
| D_EXP_LOW_DIR | 5605 |

### Wait onset → first NORMAL

| origin_cell | n_events | wait_median | wait_mean | wait_p25 | wait_p75 |
| --- | --- | --- | --- | --- | --- |
| A_COMP_LOW_DIR | 9283 | 3.000 | 5.763 | 1.000 | 8.000 |
| B_COMP_MIDHIGH_DIR | 14913 | 3.000 | 4.769 | 1.000 | 6.000 |
| C_EXP_HIGH_DIR | 24298 | 10.000 | 17.204 | 3.000 | 25.000 |
| D_EXP_LOW_DIR | 5605 | 4.000 | 6.907 | 2.000 | 9.000 |


---

## Key path table (valid horizons)

| origin_cell | family | horizon | n_valid | rate_still_normal | rate_returned_to_origin_range | rate_reached_opposite_range | abs_net_atr_median | max_range_atr_median | er_forward_median | max_up_atr_median | max_down_atr_median | wait_to_event_median | time_to_leave_normal_median | path_dir_high_share_median | path_dir_low_share_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_COMP_LOW_DIR | CompExit | 5 | 9174 | 0.6966 | 0.3389 | 0.0952 | 0.9251 | 2.131 | 0.4000 | 0.9613 | 0.9586 | 3.000 | 2.000 | 0.0000 | 0.6000 |
| A_COMP_LOW_DIR | CompExit | 15 | 8952 | 0.4987 | 0.4812 | 0.2970 | 1.571 | 3.661 | 0.2215 | 1.639 | 1.634 | 3.000 | 4.000 | 0.0000 | 0.5333 |
| A_COMP_LOW_DIR | CompExit | 30 | 8618 | 0.3611 | 0.5955 | 0.5026 | 2.276 | 5.147 | 0.1591 | 2.328 | 2.273 | 3.000 | 6.000 | 0.1000 | 0.4333 |
| A_COMP_LOW_DIR | CompExit | 60 | 7932 | 0.3330 | 0.7819 | 0.7122 | 3.234 | 7.240 | 0.1141 | 3.214 | 3.131 | 3.000 | 7.000 | 0.2000 | 0.3667 |
| B_COMP_MIDHIGH_DIR | CompExit | 5 | 14667 | 0.6699 | 0.3001 | 0.1326 | 0.9313 | 2.157 | 0.4054 | 0.9788 | 0.9284 | 3.000 | 2.000 | 0.2000 | 0.0000 |
| B_COMP_MIDHIGH_DIR | CompExit | 15 | 14222 | 0.4504 | 0.4305 | 0.3592 | 1.620 | 3.690 | 0.2245 | 1.660 | 1.602 | 3.000 | 5.000 | 0.2667 | 0.0667 |
| B_COMP_MIDHIGH_DIR | CompExit | 30 | 13599 | 0.3496 | 0.5330 | 0.5448 | 2.247 | 5.116 | 0.1556 | 2.295 | 2.250 | 3.000 | 6.000 | 0.3000 | 0.1333 |
| B_COMP_MIDHIGH_DIR | CompExit | 60 | 12445 | 0.3304 | 0.7539 | 0.7443 | 3.091 | 7.077 | 0.1111 | 3.152 | 3.121 | 3.000 | 7.000 | 0.3000 | 0.2500 |
| C_EXP_HIGH_DIR | ExpExit | 5 | 23958 | 0.6144 | 0.2317 | 0.2606 | 0.9502 | 2.184 | 0.4105 | 0.9788 | 0.9528 | 10.000 | 2.000 | 0.4000 | 0.0000 |
| C_EXP_HIGH_DIR | ExpExit | 15 | 23360 | 0.3966 | 0.3650 | 0.5431 | 1.670 | 3.770 | 0.2280 | 1.675 | 1.731 | 10.000 | 4.000 | 0.2000 | 0.1333 |
| C_EXP_HIGH_DIR | ExpExit | 30 | 22560 | 0.3418 | 0.4995 | 0.6845 | 2.375 | 5.316 | 0.1591 | 2.344 | 2.387 | 10.000 | 5.000 | 0.2000 | 0.3000 |
| C_EXP_HIGH_DIR | ExpExit | 60 | 20567 | 0.3344 | 0.7071 | 0.8317 | 3.169 | 7.365 | 0.1086 | 3.219 | 3.261 | 10.000 | 6.000 | 0.2333 | 0.3167 |
| D_EXP_LOW_DIR | ExpExit | 5 | 5531 | 0.6274 | 0.3683 | 0.1240 | 0.9657 | 2.229 | 0.4074 | 1.034 | 0.9633 | 4.000 | 2.000 | 0.0000 | 0.8000 |
| D_EXP_LOW_DIR | ExpExit | 15 | 5367 | 0.4222 | 0.5333 | 0.3330 | 1.630 | 3.848 | 0.2174 | 1.765 | 1.600 | 4.000 | 4.000 | 0.0000 | 0.5333 |
| D_EXP_LOW_DIR | ExpExit | 30 | 5231 | 0.3588 | 0.6481 | 0.5364 | 2.353 | 5.310 | 0.1553 | 2.513 | 2.267 | 4.000 | 5.000 | 0.1000 | 0.4333 |
| D_EXP_LOW_DIR | ExpExit | 60 | 4789 | 0.3393 | 0.8054 | 0.7611 | 3.203 | 7.500 | 0.1057 | 3.478 | 3.070 | 4.000 | 6.000 | 0.2000 | 0.3833 |


Full detail: `results/step2_cell_summary.csv`, `results/step2_cell_summary_by_split.csv`.

---

## Primary contrasts

### Horizon = 15 minutes

**A→NORMAL vs B→NORMAL (CompExit)** — n_A=8952, n_B=14222. Deltas are B − A.

| Metric | A | B | Δ |
| --- | ---: | ---: | ---: |
| P(still NORMAL) | 49.9% | 45.0% | -4.8 pp |
| P(return to origin range) | 48.1% | 43.0% | -5.1 pp |
| P(reach opposite range) | 29.7% | 35.9% | +6.2 pp |
| median abs_net / ATR | 1.571 | 1.620 | +0.049 |
| median max_range / ATR | 3.661 | 3.690 | +0.028 |
| median forward ER | 0.221 | 0.225 | +0.003 |
| median max_up / ATR | 1.639 | 1.660 | +0.021 |
| median max_down / ATR | 1.634 | 1.602 | -0.032 |
| median wait onset→event | 3.000 | 3.000 | +0.000 |
| median time leave NORMAL | 4.000 | 5.000 | +1.000 |
| median path HIGH-dir share | 0.000 | 0.267 | +0.267 |
| median path LOW-dir share | 0.533 | 0.067 | -0.467 |

**C→NORMAL vs D→NORMAL (ExpExit)** — n_C=23360, n_D=5367. Deltas are D − C.

| Metric | C | D | Δ |
| --- | ---: | ---: | ---: |
| P(still NORMAL) | 39.7% | 42.2% | +2.6 pp |
| P(return to origin range) | 36.5% | 53.3% | +16.8 pp |
| P(reach opposite range) | 54.3% | 33.3% | -21.0 pp |
| median abs_net / ATR | 1.670 | 1.630 | -0.040 |
| median max_range / ATR | 3.770 | 3.848 | +0.078 |
| median forward ER | 0.228 | 0.217 | -0.011 |
| median max_up / ATR | 1.675 | 1.765 | +0.089 |
| median max_down / ATR | 1.731 | 1.600 | -0.131 |
| median wait onset→event | 10.000 | 4.000 | -6.000 |
| median time leave NORMAL | 4.000 | 4.000 | +0.000 |
| median path HIGH-dir share | 0.200 | 0.000 | -0.200 |
| median path LOW-dir share | 0.133 | 0.533 | +0.400 |

### Horizon = 30 minutes

**A→NORMAL vs B→NORMAL (CompExit)** — n_A=8618, n_B=13599. Deltas are B − A.

| Metric | A | B | Δ |
| --- | ---: | ---: | ---: |
| P(still NORMAL) | 36.1% | 35.0% | -1.2 pp |
| P(return to origin range) | 59.5% | 53.3% | -6.3 pp |
| P(reach opposite range) | 50.3% | 54.5% | +4.2 pp |
| median abs_net / ATR | 2.276 | 2.247 | -0.029 |
| median max_range / ATR | 5.147 | 5.116 | -0.032 |
| median forward ER | 0.159 | 0.156 | -0.004 |
| median max_up / ATR | 2.328 | 2.295 | -0.034 |
| median max_down / ATR | 2.273 | 2.250 | -0.023 |
| median wait onset→event | 3.000 | 3.000 | +0.000 |
| median time leave NORMAL | 6.000 | 6.000 | +0.000 |
| median path HIGH-dir share | 0.100 | 0.300 | +0.200 |
| median path LOW-dir share | 0.433 | 0.133 | -0.300 |

**C→NORMAL vs D→NORMAL (ExpExit)** — n_C=22560, n_D=5231. Deltas are D − C.

| Metric | C | D | Δ |
| --- | ---: | ---: | ---: |
| P(still NORMAL) | 34.2% | 35.9% | +1.7 pp |
| P(return to origin range) | 49.9% | 64.8% | +14.9 pp |
| P(reach opposite range) | 68.4% | 53.6% | -14.8 pp |
| median abs_net / ATR | 2.375 | 2.353 | -0.022 |
| median max_range / ATR | 5.316 | 5.310 | -0.007 |
| median forward ER | 0.159 | 0.155 | -0.004 |
| median max_up / ATR | 2.344 | 2.513 | +0.169 |
| median max_down / ATR | 2.387 | 2.267 | -0.120 |
| median wait onset→event | 10.000 | 4.000 | -6.000 |
| median time leave NORMAL | 5.000 | 5.000 | +0.000 |
| median path HIGH-dir share | 0.200 | 0.100 | -0.100 |
| median path LOW-dir share | 0.300 | 0.433 | +0.133 |

### Horizon = 60 minutes

**A→NORMAL vs B→NORMAL (CompExit)** — n_A=7932, n_B=12445. Deltas are B − A.

| Metric | A | B | Δ |
| --- | ---: | ---: | ---: |
| P(still NORMAL) | 33.3% | 33.0% | -0.3 pp |
| P(return to origin range) | 78.2% | 75.4% | -2.8 pp |
| P(reach opposite range) | 71.2% | 74.4% | +3.2 pp |
| median abs_net / ATR | 3.234 | 3.091 | -0.144 |
| median max_range / ATR | 7.240 | 7.077 | -0.164 |
| median forward ER | 0.114 | 0.111 | -0.003 |
| median max_up / ATR | 3.214 | 3.152 | -0.062 |
| median max_down / ATR | 3.131 | 3.121 | -0.009 |
| median wait onset→event | 3.000 | 3.000 | +0.000 |
| median time leave NORMAL | 7.000 | 7.000 | +0.000 |
| median path HIGH-dir share | 0.200 | 0.300 | +0.100 |
| median path LOW-dir share | 0.367 | 0.250 | -0.117 |

**C→NORMAL vs D→NORMAL (ExpExit)** — n_C=20567, n_D=4789. Deltas are D − C.

| Metric | C | D | Δ |
| --- | ---: | ---: | ---: |
| P(still NORMAL) | 33.4% | 33.9% | +0.5 pp |
| P(return to origin range) | 70.7% | 80.5% | +9.8 pp |
| P(reach opposite range) | 83.2% | 76.1% | -7.1 pp |
| median abs_net / ATR | 3.169 | 3.203 | +0.033 |
| median max_range / ATR | 7.365 | 7.500 | +0.135 |
| median forward ER | 0.109 | 0.106 | -0.003 |
| median max_up / ATR | 3.219 | 3.478 | +0.259 |
| median max_down / ATR | 3.261 | 3.070 | -0.191 |
| median wait onset→event | 10.000 | 4.000 | -6.000 |
| median time leave NORMAL | 6.000 | 6.000 | +0.000 |
| median path HIGH-dir share | 0.233 | 0.200 | -0.033 |
| median path LOW-dir share | 0.317 | 0.383 | +0.067 |

---

## Leakage / scope audit

```text
LOOKAHEAD_CHECK = PASS
EVENT_USES_POST_EVENT_INFO = False
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
FORWARD_PATH_USED = True
```

Path after te is descriptive only; event at first NORMAL does not use post-te info.

---

## STEP 2 VERDICT

- **Design check:** events are first causal →NORMAL after episode onset; post-event path is descriptive only.
- **Funnel structure:** most non-events are **A/B cell switches while still compressed** (directionality flips before NORMAL), not opposite-range jumps. That is itself a market-structure fact: compression episodes often change directionality label before exiting to NORMAL.
- **Magnitude geometry (abs_net / max_range / ER):** A→NORMAL vs B→NORMAL and C→NORMAL vs D→NORMAL remain **largely similar** at 15–60m — matching Step 1’s conclusion that origin directionality does not strongly separate move *size*.
- **Destination geometry (where the path goes):** more informative than magnitude. At H=30, CompExit A returns to compression more often than B and reaches expansion slightly less often; ExpExit **D returns to expansion more often than C** and reaches compression less often. These are descriptive transition asymmetries, not trade signals.
- **Wait times:** CompExit median wait onset→NORMAL is short (~3m for A/B events); ExpExit waits are longer for C (~10m) than D (~4m) among qualifying events.
- **Interpretation:** origin directionality is a weak magnitude factor even at the transition, but it may still mark **different recycling preferences** after NORMAL. That is a mechanism lead, not an entry rule.
- **Not done:** no long/short rule; no profitability claim.

## NEXT RESEARCH QUESTION

Given similar magnitudes but different **post-NORMAL destination rates**, is the ExpExit (or CompExit) destination asymmetry stable across IS / Validation / OOS, and does an orthogonal frozen covariate at the event bar (volatility, volume, or NY time block) sharpen destination separation *within* one exit family — still mechanism-only, still no trade?

_Do not answer by building a strategy in this step._
