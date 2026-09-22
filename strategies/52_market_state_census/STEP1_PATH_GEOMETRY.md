# Step 1 — State-transition / path-geometry mechanics

**Status:** Complete (mechanism description only).
**Parent:** Strategy 52 Step 0 census labels (frozen).
**Forbidden here:** entries, exits, stops, targets, signed trade P&L, optimization.

---

## Question

What path geometry tends to follow each of four observable state combinations?

| Cell | Definition |
| --- | --- |
| **A** | Compression + Low directionality |
| **B** | Compression + Mid/High directionality |
| **C** | Expansion + High directionality |
| **D** | Expansion + Low directionality |

Event unit: **episode onset** within a session (not every minute).
Horizons: 5 / 15 / 30 / 60 minutes of **subsequent** bars only.

---

## Sample

| Item | Value |
| --- | --- |
| Eligible RTH bars | 1377851 |
| Bars in four cells | 826137 |
| Residual bars (e.g. expansion+mid) | 551714 |
| Episodes total | 140102 |
| Episodes A_COMP_LOW_DIR | 46606 |
| Episodes B_COMP_MIDHIGH_DIR | 52656 |
| Episodes C_EXP_HIGH_DIR | 29704 |
| Episodes D_EXP_LOW_DIR | 11136 |

---

## Key path table (valid horizons)

Rates are proportions of valid episodes. Magnitudes are ATR-normalized medians at onset.

| cell | horizon | n_valid | rate_still_compressed | rate_reached_normal | rate_reached_expansion | rate_still_expanded | rate_left_expansion | abs_net_atr_median | max_range_atr_median | er_forward_median | max_up_atr_median | max_down_atr_median | time_to_leave_compression_median | time_to_expansion_median | time_to_leave_expansion_median | expansion_is_directional_mean | expansion_is_two_sided_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_COMP_LOW_DIR | 5 | 45807 | 0.8329 | 0.2010 | 0.0108 | 0.0092 | 0.9997 | 0.9541 | 2.146 | 0.4217 | 0.9735 | 0.9420 | 3.000 | 4.000 | 1.000 | 0.6519 | 0.0201 |
| A_COMP_LOW_DIR | 15 | 44296 | 0.6466 | 0.4461 | 0.0832 | 0.0680 | 0.9998 | 1.656 | 3.721 | 0.2285 | 1.683 | 1.651 | 6.000 | 11.000 | 1.000 | 0.5996 | 0.0629 |
| A_COMP_LOW_DIR | 30 | 42107 | 0.4514 | 0.6857 | 0.2544 | 0.1991 | 0.9999 | 2.299 | 5.192 | 0.1591 | 2.349 | 2.288 | 11.000 | 20.000 | 1.000 | 0.5703 | 0.1003 |
| A_COMP_LOW_DIR | 60 | 38150 | 0.3106 | 0.9129 | 0.5730 | 0.3507 | 1.000 | 3.161 | 7.196 | 0.1119 | 3.267 | 3.147 | 16.000 | 33.000 | 1.000 | 0.5416 | 0.1194 |
| B_COMP_MIDHIGH_DIR | 5 | 51719 | 0.7876 | 0.2573 | 0.0176 | 0.0149 | 0.9996 | 0.9677 | 2.176 | 0.4182 | 0.9836 | 0.9623 | 2.000 | 4.000 | 1.000 | 0.8570 | 0.0022 |
| B_COMP_MIDHIGH_DIR | 15 | 49937 | 0.6173 | 0.4893 | 0.1070 | 0.0864 | 0.9998 | 1.668 | 3.741 | 0.2287 | 1.695 | 1.648 | 5.000 | 10.000 | 1.000 | 0.7291 | 0.0311 |
| B_COMP_MIDHIGH_DIR | 30 | 47559 | 0.4367 | 0.7095 | 0.2798 | 0.2192 | 0.9999 | 2.300 | 5.210 | 0.1586 | 2.354 | 2.296 | 9.000 | 18.000 | 1.000 | 0.6454 | 0.0702 |
| B_COMP_MIDHIGH_DIR | 60 | 43016 | 0.3164 | 0.9187 | 0.5880 | 0.3472 | 0.9999 | 3.144 | 7.184 | 0.1114 | 3.252 | 3.166 | 14.000 | 31.000 | 1.000 | 0.5760 | 0.1063 |
| C_EXP_HIGH_DIR | 5 | 29383 | 0.0301 | 0.2925 | 0.9347 | 0.7532 | 0.2936 | 0.9745 | 2.209 | 0.4118 | 1.000 | 0.9740 | 1.000 | 1.000 | 2.000 | 0.8124 | 0.0017 |
| C_EXP_HIGH_DIR | 15 | 28683 | 0.1542 | 0.5396 | 0.9487 | 0.5580 | 0.5417 | 1.667 | 3.802 | 0.2222 | 1.718 | 1.688 | 1.000 | 1.000 | 5.000 | 0.8093 | 0.0025 |
| C_EXP_HIGH_DIR | 30 | 27716 | 0.2688 | 0.7439 | 0.9589 | 0.4198 | 0.7470 | 2.357 | 5.345 | 0.1560 | 2.362 | 2.400 | 1.000 | 1.000 | 8.000 | 0.8063 | 0.0036 |
| C_EXP_HIGH_DIR | 60 | 25736 | 0.3167 | 0.9335 | 0.9766 | 0.3448 | 0.9362 | 3.252 | 7.423 | 0.1102 | 3.281 | 3.333 | 1.000 | 1.000 | 12.000 | 0.8004 | 0.0066 |
| D_EXP_LOW_DIR | 5 | 11054 | 0.0140 | 0.3024 | 0.9386 | 0.7636 | 0.3038 | 0.9106 | 2.126 | 0.4000 | 0.9739 | 0.9302 | 1.000 | 1.000 | 2.000 | 0.0090 | 0.6622 |
| D_EXP_LOW_DIR | 15 | 10842 | 0.1045 | 0.5517 | 0.9586 | 0.5871 | 0.5533 | 1.579 | 3.713 | 0.2143 | 1.703 | 1.627 | 1.000 | 1.000 | 5.000 | 0.0136 | 0.6556 |
| D_EXP_LOW_DIR | 30 | 10524 | 0.2621 | 0.7739 | 0.9679 | 0.4175 | 0.7761 | 2.246 | 5.192 | 0.1524 | 2.408 | 2.240 | 1.000 | 1.000 | 8.000 | 0.0180 | 0.6520 |
| D_EXP_LOW_DIR | 60 | 9837 | 0.3290 | 0.9543 | 0.9841 | 0.3347 | 0.9557 | 3.091 | 7.148 | 0.1084 | 3.394 | 3.020 | 1.000 | 1.000 | 12.000 | 0.0253 | 0.6443 |


Full detail: `results/step1_cell_summary.csv`, `results/step1_cell_summary_by_split.csv`.

---

## Primary contrasts

### Horizon = 15 minutes

**A vs B (compression)** — n_A=44296.0, n_B=49937.0. Deltas are B − A.

| Metric | A | B | B−A |
| --- | ---: | ---: | ---: |
| P(reached expansion) | 8.3% | 10.7% | +2.4 pp |
| P(reached normal) | 44.6% | 48.9% | +4.3 pp |
| P(still compressed) | 64.7% | 61.7% | -2.9 pp |
| median abs_net / ATR | 1.656 | 1.668 | +0.012 |
| median max_range / ATR | 3.721 | 3.741 | +0.021 |
| median forward ER | 0.229 | 0.229 | +0.000 |
| median max_up / ATR | 1.683 | 1.695 | +0.012 |
| median max_down / ATR | 1.651 | 1.648 | -0.002 |

**C vs D (expansion)** — n_C=28683.0, n_D=10842.0. Deltas are D − C.

| Metric | C | D | D−C |
| --- | ---: | ---: | ---: |
| P(still expanded) | 55.8% | 58.7% | +2.9 pp |
| P(left expansion) | 54.2% | 55.3% | +1.2 pp |
| median abs_net / ATR | 1.667 | 1.579 | -0.088 |
| median max_range / ATR | 3.802 | 3.713 | -0.089 |
| median forward ER | 0.222 | 0.214 | -0.008 |
| median max_up / ATR | 1.718 | 1.703 | -0.015 |
| median max_down / ATR | 1.688 | 1.627 | -0.060 |

### Horizon = 30 minutes

**A vs B (compression)** — n_A=42107.0, n_B=47559.0. Deltas are B − A.

| Metric | A | B | B−A |
| --- | ---: | ---: | ---: |
| P(reached expansion) | 25.4% | 28.0% | +2.5 pp |
| P(reached normal) | 68.6% | 71.0% | +2.4 pp |
| P(still compressed) | 45.1% | 43.7% | -1.5 pp |
| median abs_net / ATR | 2.299 | 2.300 | +0.000 |
| median max_range / ATR | 5.192 | 5.210 | +0.018 |
| median forward ER | 0.159 | 0.159 | -0.000 |
| median max_up / ATR | 2.349 | 2.354 | +0.005 |
| median max_down / ATR | 2.288 | 2.296 | +0.008 |

**C vs D (expansion)** — n_C=27716.0, n_D=10524.0. Deltas are D − C.

| Metric | C | D | D−C |
| --- | ---: | ---: | ---: |
| P(still expanded) | 42.0% | 41.8% | -0.2 pp |
| P(left expansion) | 74.7% | 77.6% | +2.9 pp |
| median abs_net / ATR | 2.357 | 2.246 | -0.111 |
| median max_range / ATR | 5.345 | 5.192 | -0.153 |
| median forward ER | 0.156 | 0.152 | -0.004 |
| median max_up / ATR | 2.362 | 2.408 | +0.047 |
| median max_down / ATR | 2.400 | 2.240 | -0.160 |

### Horizon = 60 minutes

**A vs B (compression)** — n_A=38150.0, n_B=43016.0. Deltas are B − A.

| Metric | A | B | B−A |
| --- | ---: | ---: | ---: |
| P(reached expansion) | 57.3% | 58.8% | +1.5 pp |
| P(reached normal) | 91.3% | 91.9% | +0.6 pp |
| P(still compressed) | 31.1% | 31.6% | +0.6 pp |
| median abs_net / ATR | 3.161 | 3.144 | -0.017 |
| median max_range / ATR | 7.196 | 7.184 | -0.012 |
| median forward ER | 0.112 | 0.111 | -0.000 |
| median max_up / ATR | 3.267 | 3.252 | -0.016 |
| median max_down / ATR | 3.147 | 3.166 | +0.019 |

**C vs D (expansion)** — n_C=25736.0, n_D=9837.0. Deltas are D − C.

| Metric | C | D | D−C |
| --- | ---: | ---: | ---: |
| P(still expanded) | 34.5% | 33.5% | -1.0 pp |
| P(left expansion) | 93.6% | 95.6% | +1.9 pp |
| median abs_net / ATR | 3.252 | 3.091 | -0.162 |
| median max_range / ATR | 7.423 | 7.148 | -0.275 |
| median forward ER | 0.110 | 0.108 | -0.002 |
| median max_up / ATR | 3.281 | 3.394 | +0.113 |
| median max_down / ATR | 3.333 | 3.020 | -0.313 |

---

## Leakage / scope audit

```text
LOOKAHEAD_CHECK = PASS
FUTURE_DATA_USED_IN_STATE_LABEL = False
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
FORWARD_PATH_USED = True
```

Subsequent bars used only for descriptive path geometry after labeled onset; labels themselves are causal.

---

## STEP 1 VERDICT

- **Architecture:** four-cell state → subsequent path geometry is measurable at episode scale without constructing trades.
- **A vs B (compression):** over 15–60m, ATR-scaled move/range realization and forward ER are **largely similar**. B leaves compression slightly faster and is somewhat more likely to reach expansion by H=30 (~28% vs ~25%). Differences are modest — not a license to trade “directional compression.”
- **C vs D (expansion):** persistence of expansion and ATR-scaled path envelopes are also **similar**. The clear descriptive split is directional *character* at/after onset (high-dir vs low-dir expansion), which is partly built into the cell definition and should not be mistaken for an edge.
- **Compression path structure:** among compression onsets, reaching NORMAL is far more common than reaching EXPANSION at short horizons (e.g. H=15: ~45–49% reach normal vs ~8–11% reach expansion), consistent with Step 0’s finding that compression→expansion is usually indirect.
- **Sample sizes are adequate** for these descriptive contrasts (tens of thousands of episodes per cell).
- **Not done here:** no long/short rule; no claim that any cell is tradeable.

## NEXT RESEARCH QUESTION

Given that **magnitude path geometry is similar within compression (A vs B) and within expansion (C vs D)**, does a more specific **event** — e.g. the first COMPRESSION→NORMAL transition, or the first return to NORMAL from EXPANSION — produce distinguishable subsequent path geometry conditional on whether the pre-transition cell was A vs B (or C vs D)? Still mechanism-only; still no trade.

_Do not answer that question by building a strategy in this step._
