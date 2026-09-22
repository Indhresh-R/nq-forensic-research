# Step 6 — Directionality mechanism decomposition (ExpExit)

**Status:** Complete (mechanism decomposition audit).
**Scope:** ExpExit C vs D only. No trade. No new CEM.

Primary measurements at the **event bar `te`** (first NORMAL), where C/D are not forced into disjoint ER bands by construction.

Sanity: `tm_er60` C_min=0.07172995780590717, D_max=0.15949367088607594 (pre-event bands expected disjoint).

---

## Component balance at transition (D − C SMD)

| component | mean_c | mean_d | smd_d_minus_c | n_c_finite | n_d_finite |
| --- | --- | --- | --- | --- | --- |
| te_er_60 | 0.1766 | 0.0649 | -2.0600 | 24298 | 5605 |
| te_er_30 | 0.1587 | 0.1834 | 0.2131 | 24298 | 5605 |
| te_er_120 | 0.1108 | 0.0713 | -0.6297 | 24182 | 5571 |
| te_path_60 | 195.842 | 187.338 | -0.0423 | 21926 | 5118 |
| te_abs_net_60 | 34.4735 | 12.3211 | -0.7215 | 21926 | 5118 |
| te_signed_net_60 | 1.7967 | 0.7139 | -0.0270 | 21926 | 5118 |
| er_60_change | -0.0247 | -0.0029 | 0.5740 | 24298 | 5605 |
| te_signed_net_5 | -0.2827 | -0.7860 | -0.0362 | 23810 | 5426 |
| tm_er_60 | 0.2013 | 0.0679 | -2.7473 | 24298 | 5605 |
| tm_path_60 | 197.120 | 187.456 | -0.0479 | 21823 | 5091 |
| tm_abs_net_60 | 39.5716 | 13.3280 | -0.7818 | 21823 | 5091 |


---

## Within-bin D−C destination contrasts (horizon 30m)

### te_er_60

IS cuts: q33=0.12101910828025478, q67=0.18788751445338914

| bin | n_c | n_d | eligible | mean_feature_c | mean_feature_d | return | opposite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 4235 | 4590 | True | 0.0858 | 0.0535 | +19.9 pp | -20.2 pp |
| T2 | 8556 | 590 | True | 0.1570 | 0.1434 | +1.6 pp | +4.6 pp |
| T3 | 9769 | 51 | False | 0.2323 | 0.2064 | -5.2 pp | +24.4 pp |


### te_path_60

IS cuts: q33=51.0, q67=106.83333333333303

| bin | n_c | n_d | eligible | mean_feature_c | mean_feature_d | return | opposite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nan | 2372 | 487 | True | nan | nan | +7.0 pp | +1.7 pp |
| T1 | 4569 | 1192 | True | 36.6802 | 37.5852 | +13.3 pp | -11.6 pp |
| T2 | 4623 | 1255 | True | 73.7336 | 72.7462 | +17.4 pp | -17.9 pp |
| T3 | 10996 | 2297 | True | 316.968 | 326.332 | +15.3 pp | -17.8 pp |


### te_abs_net_60

IS cuts: q33=6.75, q67=15.25

| bin | n_c | n_d | eligible | mean_feature_c | mean_feature_d | return | opposite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nan | 2372 | 487 | True | nan | nan | +7.0 pp | +1.7 pp |
| T1 | 3677 | 2672 | True | 4.5271 | 2.8264 | +20.7 pp | -22.0 pp |
| T2 | 4953 | 931 | True | 10.4961 | 10.4452 | +6.9 pp | -6.8 pp |
| T3 | 11558 | 1141 | True | 54.8207 | 36.1832 | +8.0 pp | -10.2 pp |


### er_60_change

IS cuts: q33=-0.03506787330316741, q67=-0.006838342064148509

| bin | n_c | n_d | eligible | mean_feature_c | mean_feature_d | return | opposite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 8294 | 1009 | True | -0.0611 | -0.0549 | +16.1 pp | -21.4 pp |
| T2 | 7674 | 1574 | True | -0.0209 | -0.0203 | +18.7 pp | -20.2 pp |
| T3 | 6592 | 2648 | True | 0.0156 | 0.0269 | +9.7 pp | -7.4 pp |


### te_signed_net_5

IS cuts: q33=-1.5, q67=1.25

| bin | n_c | n_d | eligible | mean_feature_c | mean_feature_d | return | opposite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nan | 488 | 179 | False | nan | nan | +10.0 pp | -11.7 pp |
| T1 | 8380 | 2018 | True | -10.0290 | -10.2063 | +11.5 pp | -11.6 pp |
| T2 | 5834 | 1318 | True | -0.0046 | 0.0474 | +15.2 pp | -12.2 pp |
| T3 | 7858 | 1716 | True | 9.9367 | 9.4948 | +19.7 pp | -21.9 pp |


---

## Within-cell monotonicity (descriptive)

| origin_cell | bin | n | mean_feature | return_rate | opposite_rate |
| --- | --- | --- | --- | --- | --- |
| C_EXP_HIGH_DIR | T1 | 4235 | 0.0858 | 0.4751 | 0.7018 |
| C_EXP_HIGH_DIR | T2 | 8556 | 0.1570 | 0.4398 | 0.7509 |
| C_EXP_HIGH_DIR | T3 | 9769 | 0.2323 | 0.5623 | 0.6188 |
| D_EXP_LOW_DIR | T1 | 4590 | 0.0535 | 0.6743 | 0.4993 |
| D_EXP_LOW_DIR | T2 | 590 | 0.1434 | 0.4559 | 0.7966 |
| D_EXP_LOW_DIR | T3 | 51 | 0.2064 | 0.5098 | 0.8627 |


---

## Predeclared classification

- **Classification:** `CONDITIONAL`
- Primary `te_er_60` class: `CONDITIONAL`
- PATH_OR_NET feature (if any): `None`

- `T1`: return=+19.9 pp, opposite=-20.2 pp, keeps=(True,True)
- `T2`: return=+1.6 pp, opposite=+4.6 pp, keeps=(False,False)

---

## Leakage / scope audit

```text
LOOKAHEAD_CHECK = PASS
POST_EVENT_INFO_IN_COMPONENTS = False
SCOPE_EXPEXIT_ONLY = True
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
```

---

## STEP 6 VERDICT

- The ExpExit C/D destination link is **conditional on transition-ER regime**: it remains in the low-`ER_60[te]` band and collapses in the mid-overlap band (high band typically underpowered for D).
- Wording remains associative, not “we discovered the directional mechanism.”

## NEXT RESEARCH QUESTION

Given that the destination asymmetry is concentrated in the **low `ER_60[te]` regime** and collapses where C and D overlap at mid ER, should the next object be **low-transition-ER ExpExit events**, asking whether origin-episode history still separates destinations *within* that regime — still without constructing a trade?

_Do not answer by building a strategy in this step._
