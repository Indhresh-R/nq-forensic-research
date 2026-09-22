# Step 8 — Path Feasibility Audit

**Status:** Complete (path-feasibility audit).
**Scope:** Frozen low-transition-ER ExpExit C vs D. No trade. No optimization.

## 1. Objective

Does the already-observed low-transition-ER ExpExit C/D destination asymmetry occur early enough and with sufficient raw price excursion to potentially support a simple executable hypothesis?

This step does **not** construct, optimize, or validate a strategy.

## 2. Frozen population

Step 7 population reused exactly: n=9442 (C=4529, D=4913). Expected ≈ 9442 (C≈4529, D≈4913). Match OK=True.

Low-ER cut remains the frozen Step 6 IS `te_er_60` q33. No redefinition of C/D.

## 3. Leakage audit

```text
LOOKAHEAD_CHECK = PASS
EVENT_POPULATION_FROZEN = PASS
FORWARD_PATH_STRICTLY_AFTER_TE = PASS
OUTCOME_USED_FOR_SELECTION = False
STRATEGY_DATA_USED = False
PARAMETER_OPTIMIZATION = False
```

## 4. Sample counts

Pooled valid paths inherit Step 2 session/segment continuity. Reference 30m destination: D−C return +19.9 pp, opposite -20.2 pp (n_c=4235, n_d=4590).

## 5m path results

Destination (valid n_c=4475, n_d=4853, eligible=True):

- Return to origin: C=15.4%, D=38.6%, D−C=+23.2 pp
- Reach opposite: C=31.9%, D=9.7%, D−C=-22.2 pp

Raw excursion (NQ points; no trade side):

| origin_cell | feature | n | mean | p25 | p50 | p75 | p90 | frac_gt_5 | frac_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POOLED | max_up | 9328.00 | 6.95 | 1.25 | 3.00 | 8.00 | 18.75 | 0.3597 | 0.2048 |
| POOLED | max_down | 9328.00 | 7.52 | 1.00 | 3.00 | 8.75 | 19.50 | 0.3669 | 0.2159 |
| POOLED | abs_max_excursion | 9328.00 | 11.41 | 2.50 | 6.00 | 14.50 | 28.00 | 0.5405 | 0.3507 |
| POOLED | net_displacement | 9328.00 | -0.3139 | -3.00 | 0.0000 | 3.00 | 10.00 | 0.1754 | 0.0987 |
| POOLED | hl_range | 9328.00 | 14.47 | 3.50 | 7.75 | 19.25 | 35.25 | 0.6139 | 0.4277 |
| POOLED | abs_net | 9328.00 | 7.21 | 1.00 | 3.00 | 8.25 | 19.00 | 0.3596 | 0.2055 |
| C_EXP_HIGH_DIR | max_up | 4475.00 | 6.77 | 1.00 | 2.75 | 8.00 | 18.40 | 0.3511 | 0.1993 |
| C_EXP_HIGH_DIR | max_down | 4475.00 | 7.59 | 1.00 | 3.00 | 9.25 | 20.50 | 0.3763 | 0.2208 |
| C_EXP_HIGH_DIR | abs_max_excursion | 4475.00 | 11.36 | 2.50 | 6.00 | 15.00 | 27.50 | 0.5446 | 0.3526 |
| C_EXP_HIGH_DIR | net_displacement | 4475.00 | -0.5286 | -3.25 | 0.0000 | 2.75 | 9.75 | 0.1712 | 0.0972 |
| C_EXP_HIGH_DIR | hl_range | 4475.00 | 14.36 | 3.25 | 7.75 | 19.25 | 34.25 | 0.6103 | 0.4340 |
| C_EXP_HIGH_DIR | abs_net | 4475.00 | 7.30 | 1.00 | 3.00 | 8.50 | 19.25 | 0.3640 | 0.2087 |
| D_EXP_LOW_DIR | max_up | 4853.00 | 7.11 | 1.25 | 3.25 | 8.25 | 19.25 | 0.3676 | 0.2098 |
| D_EXP_LOW_DIR | max_down | 4853.00 | 7.45 | 1.00 | 3.00 | 8.25 | 19.00 | 0.3581 | 0.2114 |
| D_EXP_LOW_DIR | abs_max_excursion | 4853.00 | 11.45 | 2.50 | 5.75 | 14.25 | 28.25 | 0.5368 | 0.3489 |
| D_EXP_LOW_DIR | net_displacement | 4853.00 | -0.1160 | -2.75 | 0.0000 | 3.25 | 10.20 | 0.1793 | 0.1001 |
| D_EXP_LOW_DIR | hl_range | 4853.00 | 14.56 | 3.50 | 7.75 | 19.25 | 35.70 | 0.6171 | 0.4220 |
| D_EXP_LOW_DIR | abs_net | 4853.00 | 7.13 | 1.00 | 3.00 | 8.00 | 18.50 | 0.3555 | 0.2026 |


## 15m path results

Destination (valid n_c=4348, n_d=4706, eligible=True):

- Return to origin: C=31.3%, D=56.1%, D−C=+24.8 pp
- Reach opposite: C=57.5%, D=28.8%, D−C=-28.7 pp

Raw excursion (NQ points; no trade side):

| origin_cell | feature | n | mean | p25 | p50 | p75 | p90 | frac_gt_5 | frac_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POOLED | max_up | 9054.00 | 11.84 | 2.00 | 5.25 | 13.50 | 30.00 | 0.5059 | 0.3178 |
| POOLED | max_down | 9054.00 | 12.63 | 1.75 | 5.00 | 14.25 | 33.25 | 0.4980 | 0.3280 |
| POOLED | abs_max_excursion | 9054.00 | 19.31 | 4.50 | 10.00 | 25.00 | 46.75 | 0.7046 | 0.4966 |
| POOLED | net_displacement | 9054.00 | -0.2805 | -4.75 | 0.2500 | 5.25 | 17.00 | 0.2510 | 0.1582 |
| POOLED | hl_range | 9054.00 | 24.47 | 6.00 | 13.00 | 33.25 | 57.50 | 0.7987 | 0.5739 |
| POOLED | abs_net | 9054.00 | 12.15 | 2.00 | 5.00 | 13.75 | 31.75 | 0.4928 | 0.3185 |
| C_EXP_HIGH_DIR | max_up | 4348.00 | 11.19 | 1.75 | 5.00 | 13.06 | 29.50 | 0.4910 | 0.3119 |
| C_EXP_HIGH_DIR | max_down | 4348.00 | 12.85 | 1.75 | 5.25 | 14.75 | 35.00 | 0.5041 | 0.3323 |
| C_EXP_HIGH_DIR | abs_max_excursion | 4348.00 | 19.09 | 4.50 | 10.00 | 26.00 | 45.75 | 0.7077 | 0.4991 |
| C_EXP_HIGH_DIR | net_displacement | 4348.00 | -1.03 | -5.25 | -0.2500 | 4.75 | 16.83 | 0.2380 | 0.1509 |
| C_EXP_HIGH_DIR | hl_range | 4348.00 | 24.05 | 5.75 | 13.00 | 33.81 | 56.75 | 0.8004 | 0.5752 |
| C_EXP_HIGH_DIR | abs_net | 4348.00 | 12.05 | 2.00 | 5.00 | 14.00 | 31.50 | 0.4920 | 0.3190 |
| D_EXP_LOW_DIR | max_up | 4706.00 | 12.43 | 2.25 | 5.50 | 14.25 | 31.25 | 0.5195 | 0.3232 |
| D_EXP_LOW_DIR | max_down | 4706.00 | 12.43 | 1.75 | 5.00 | 14.25 | 31.50 | 0.4924 | 0.3241 |
| D_EXP_LOW_DIR | abs_max_excursion | 4706.00 | 19.52 | 4.50 | 10.00 | 24.00 | 47.25 | 0.7017 | 0.4943 |
| D_EXP_LOW_DIR | net_displacement | 4706.00 | 0.4125 | -4.25 | 0.5000 | 5.50 | 17.00 | 0.2631 | 0.1649 |
| D_EXP_LOW_DIR | hl_range | 4706.00 | 24.86 | 6.00 | 13.00 | 32.75 | 58.75 | 0.7971 | 0.5727 |
| D_EXP_LOW_DIR | abs_net | 4706.00 | 12.24 | 2.00 | 5.00 | 13.50 | 32.12 | 0.4936 | 0.3181 |


## 30m path results

Destination (valid n_c=4235, n_d=4590, eligible=True):

- Return to origin: C=47.5%, D=67.4%, D−C=+19.9 pp
- Reach opposite: C=70.2%, D=49.9%, D−C=-20.2 pp

Raw excursion (NQ points; no trade side):

| origin_cell | feature | n | mean | p25 | p50 | p75 | p90 | frac_gt_5 | frac_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POOLED | max_up | 8825.00 | 16.57 | 3.00 | 7.25 | 19.25 | 43.25 | 0.6082 | 0.4062 |
| POOLED | max_down | 8825.00 | 17.57 | 2.50 | 7.25 | 20.50 | 46.75 | 0.5882 | 0.4131 |
| POOLED | abs_max_excursion | 8825.00 | 26.91 | 6.50 | 14.25 | 34.75 | 64.25 | 0.8229 | 0.6016 |
| POOLED | net_displacement | 8825.00 | 0.1627 | -6.75 | 0.5000 | 7.75 | 24.50 | 0.3116 | 0.2082 |
| POOLED | hl_range | 8825.00 | 34.15 | 8.50 | 18.25 | 45.00 | 82.00 | 0.9100 | 0.6876 |
| POOLED | abs_net | 8825.00 | 17.00 | 2.75 | 7.25 | 19.50 | 44.00 | 0.5952 | 0.4074 |
| C_EXP_HIGH_DIR | max_up | 4235.00 | 15.98 | 2.75 | 7.00 | 18.75 | 40.50 | 0.5894 | 0.3943 |
| C_EXP_HIGH_DIR | max_down | 4235.00 | 17.87 | 2.50 | 7.25 | 21.25 | 47.15 | 0.5950 | 0.4170 |
| C_EXP_HIGH_DIR | abs_max_excursion | 4235.00 | 26.86 | 6.25 | 14.25 | 35.50 | 64.25 | 0.8215 | 0.6054 |
| C_EXP_HIGH_DIR | net_displacement | 4235.00 | -0.3643 | -7.50 | 0.5000 | 7.75 | 24.15 | 0.3011 | 0.2066 |
| C_EXP_HIGH_DIR | hl_range | 4235.00 | 33.85 | 8.50 | 18.00 | 45.00 | 79.90 | 0.9055 | 0.6893 |
| C_EXP_HIGH_DIR | abs_net | 4235.00 | 17.10 | 2.75 | 7.75 | 20.00 | 42.65 | 0.6012 | 0.4234 |
| D_EXP_LOW_DIR | max_up | 4590.00 | 17.13 | 3.25 | 7.50 | 20.00 | 44.75 | 0.6255 | 0.4172 |
| D_EXP_LOW_DIR | max_down | 4590.00 | 17.30 | 2.75 | 7.25 | 19.75 | 45.53 | 0.5819 | 0.4096 |
| D_EXP_LOW_DIR | abs_max_excursion | 4590.00 | 26.95 | 6.50 | 14.00 | 33.75 | 64.30 | 0.8242 | 0.5980 |
| D_EXP_LOW_DIR | net_displacement | 4590.00 | 0.6490 | -6.00 | 0.7500 | 7.75 | 24.75 | 0.3214 | 0.2096 |
| D_EXP_LOW_DIR | hl_range | 4590.00 | 34.43 | 8.50 | 18.75 | 45.00 | 84.28 | 0.9142 | 0.6861 |
| D_EXP_LOW_DIR | abs_net | 4590.00 | 16.91 | 2.75 | 7.00 | 18.75 | 45.50 | 0.5898 | 0.3926 |


## 60m path results

Destination (valid n_c=3842, n_d=4187, eligible=True):

- Return to origin: C=70.4%, D=82.1%, D−C=+11.7 pp
- Reach opposite: C=83.8%, D=74.4%, D−C=-9.4 pp

Raw excursion (NQ points; no trade side):

| origin_cell | feature | n | mean | p25 | p50 | p75 | p90 | frac_gt_5 | frac_gt_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POOLED | max_up | 8029.00 | 23.30 | 4.25 | 10.25 | 28.25 | 59.25 | 0.7026 | 0.5004 |
| POOLED | max_down | 8029.00 | 24.68 | 3.75 | 10.25 | 29.00 | 65.00 | 0.6685 | 0.5022 |
| POOLED | abs_max_excursion | 8029.00 | 37.54 | 9.25 | 20.25 | 48.00 | 91.50 | 0.9121 | 0.7127 |
| POOLED | net_displacement | 8029.00 | 0.8064 | -8.75 | 1.25 | 11.50 | 35.50 | 0.3690 | 0.2670 |
| POOLED | hl_range | 8029.00 | 47.99 | 12.00 | 25.75 | 65.00 | 115.75 | 0.9797 | 0.8053 |
| POOLED | abs_net | 8029.00 | 23.50 | 4.00 | 10.00 | 27.00 | 64.50 | 0.6874 | 0.4982 |
| C_EXP_HIGH_DIR | max_up | 3842.00 | 22.83 | 4.25 | 9.75 | 28.44 | 56.23 | 0.6874 | 0.4883 |
| C_EXP_HIGH_DIR | max_down | 3842.00 | 25.14 | 3.75 | 10.50 | 31.00 | 69.25 | 0.6812 | 0.5094 |
| C_EXP_HIGH_DIR | abs_max_excursion | 3842.00 | 37.65 | 9.25 | 21.25 | 47.25 | 90.98 | 0.9102 | 0.7173 |
| C_EXP_HIGH_DIR | net_displacement | 3842.00 | 0.1247 | -9.69 | 1.25 | 11.25 | 34.50 | 0.3581 | 0.2624 |
| C_EXP_HIGH_DIR | hl_range | 3842.00 | 47.97 | 12.25 | 27.00 | 65.75 | 115.00 | 0.9836 | 0.8053 |
| C_EXP_HIGH_DIR | abs_net | 3842.00 | 23.65 | 4.00 | 10.50 | 27.75 | 65.00 | 0.6918 | 0.5055 |
| D_EXP_LOW_DIR | max_up | 4187.00 | 23.74 | 4.25 | 10.50 | 28.00 | 61.75 | 0.7165 | 0.5116 |
| D_EXP_LOW_DIR | max_down | 4187.00 | 24.26 | 3.50 | 10.00 | 28.25 | 63.10 | 0.6568 | 0.4956 |
| D_EXP_LOW_DIR | abs_max_excursion | 4187.00 | 37.44 | 9.00 | 19.75 | 48.88 | 92.10 | 0.9138 | 0.7084 |
| D_EXP_LOW_DIR | net_displacement | 4187.00 | 1.43 | -8.00 | 1.50 | 11.50 | 37.25 | 0.3790 | 0.2713 |
| D_EXP_LOW_DIR | hl_range | 4187.00 | 48.00 | 11.88 | 25.00 | 64.50 | 116.50 | 0.9761 | 0.8053 |
| D_EXP_LOW_DIR | abs_net | 4187.00 | 23.37 | 4.00 | 9.75 | 27.00 | 63.00 | 0.6833 | 0.4915 |


## 9. Destination timing

Among events that reach each destination within 60m (censored excluded from timing):

| origin_cell | feature | n_reached | n_events | frac_reached | p25 | p50 | p75 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C_EXP_HIGH_DIR | time_to_origin_range | 2706.00 | 3842.00 | 0.7043 | 7.00 | 19.00 | 36.00 |
| C_EXP_HIGH_DIR | time_to_opposite_range | 3218.00 | 3842.00 | 0.8376 | 3.00 | 8.00 | 20.00 |
| C_EXP_HIGH_DIR | time_to_first_destination | 3836.00 | 3842.00 | 0.9984 | 3.00 | 6.00 | 13.00 |
| D_EXP_LOW_DIR | time_to_origin_range | 3437.00 | 4187.00 | 0.8209 | 2.00 | 6.00 | 22.00 |
| D_EXP_LOW_DIR | time_to_opposite_range | 3115.00 | 4187.00 | 0.7440 | 10.00 | 21.00 | 36.50 |
| D_EXP_LOW_DIR | time_to_first_destination | 4185.00 | 4187.00 | 0.9995 | 2.00 | 6.00 | 13.00 |
| POOLED | time_to_origin_range | 6143.00 | 8029.00 | 0.7651 | 3.00 | 11.00 | 30.00 |
| POOLED | time_to_opposite_range | 6333.00 | 8029.00 | 0.7888 | 5.00 | 13.00 | 30.00 |
| POOLED | time_to_first_destination | 8021.00 | 8029.00 | 0.9990 | 2.00 | 6.00 | 13.00 |


## 10. Competing-path analysis

Which destination occurs first within 60m (path states only — not wins/losses):

| origin_cell | feature | n | rate |
| --- | --- | --- | --- |
| C_EXP_HIGH_DIR | reach_opposite | 2421.00 | 0.6301 |
| C_EXP_HIGH_DIR | return_to_origin | 1415.00 | 0.3683 |
| C_EXP_HIGH_DIR | neither_within_60m | 6.00 | 0.0016 |
| D_EXP_LOW_DIR | return_to_origin | 2722.00 | 0.6501 |
| D_EXP_LOW_DIR | reach_opposite | 1463.00 | 0.3494 |
| D_EXP_LOW_DIR | neither_within_60m | 2.00 | 0.0005 |


## 11. Raw NQ-point scale

Event-time ATR (`atr_e`) distribution for scale context (not an ATR-multiple trading rule):

| origin_cell | n | mean | p25 | p50 | p75 | p90 |
| --- | --- | --- | --- | --- | --- | --- |
| C_EXP_HIGH_DIR | 4529.00 | 5.64 | 1.48 | 3.06 | 8.36 | 13.50 |
| D_EXP_LOW_DIR | 4913.00 | 5.88 | 1.53 | 3.14 | 8.35 | 14.26 |
| POOLED | 9442.00 | 5.77 | 1.51 | 3.11 | 8.36 | 13.73 |


Pooled median `hl_range`: 15m=13.0, 30m=18.25 NQ points.
Pooled median time to first destination (among reached): 6.0 minutes.

## 12. IS / Validation / OOS stability

30m D−C destination contrasts by chronological split (same frozen population):

| split | n_c | n_d | eligible | return | opposite |
| --- | --- | --- | --- | --- | --- |
| ALL | 4235.00 | 4590.00 | True | +19.9 pp | -20.2 pp |
| IS | 3159.00 | 3360.00 | True | +19.2 pp | -20.0 pp |
| Validation | 695.00 | 754.00 | True | +23.3 pp | -22.0 pp |
| OOS | 381.00 | 476.00 | True | +21.1 pp | -20.5 pp |


## 13. Cost-scale context

Project mid round-trip cost assumption: **1.0 NQ point** (`research_framework/execution_assumptions.md`). Observed median post-event ranges at 15m/30m are compared to this scale **without** subtracting costs, computing P&L, or choosing stops/targets.

## 14. Interpretation

Language remains destination / path-excursion / timing / feasibility. No continuation, reversal, long/short, expectancy, or profitability claims.

Clause checklist (preregistered):

- clause1_15 (assoc @15m): `True`
- clause1_30 (assoc @30m): `True`
- clause2 (median hl_range ≥ 5 @15 and @30): `True`
- clause3 (median first destination ≤ 15m): `True`
- clause4 (30m return D−C same sign IS/Val/OOS): `True`

## 15. Predeclared classification

**Classification:** `PATH_FEASIBLE`

## 16. Explicit stop/go decision

**Decision:** `GO_TO_STEP9`

Yes — enough stable path geometry to justify constructing one simple executable hypothesis in a separate Step 9.

A separate Step 9 may construct **one** simple, preregistered executable hypothesis. That hypothesis is **not** constructed in this step.
