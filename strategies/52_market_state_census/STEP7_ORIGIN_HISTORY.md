# Step 7 — Low-transition-ER origin-history decomposition

**Status:** Complete (mechanism decomposition audit).
**Scope:** ExpExit C vs D with low `ER_60[te]` only. No trade. No new CEM.

## Population

Low-ER cut (frozen from Step 6 IS `te_er_60` q33): **0.12101910828025478**.
Population n=9442 (C=4529, D=4913).

Low-ER pooled D−C @ 30m: return +19.9 pp, opposite -20.2 pp (n_c=4235, n_d=4590).

---

## Primary feature: expansion duration (`duration_bars`)

IS-frozen terciles (low-ER ExpExit only): q33=4.0, q67=12.0 (n_IS=6949).

---

## Composition (C vs D across duration bins)

| origin_cell | bin | n | pct_of_cell | mean_duration | mean_te_er_60 |
| --- | --- | --- | --- | --- | --- |
| C_EXP_HIGH_DIR | DUR_T1 | 1047 | 23.1177 | 2.4842 | 0.0898 |
| C_EXP_HIGH_DIR | DUR_T2 | 1197 | 26.4297 | 8.0485 | 0.0859 |
| C_EXP_HIGH_DIR | DUR_T3 | 2285 | 50.4526 | 35.2551 | 0.0849 |
| D_EXP_LOW_DIR | DUR_T1 | 2656 | 54.0607 | 2.0474 | 0.0502 |
| D_EXP_LOW_DIR | DUR_T2 | 1439 | 29.2896 | 7.6970 | 0.0559 |
| D_EXP_LOW_DIR | DUR_T3 | 818 | 16.6497 | 19.9438 | 0.0580 |


---

## History balance at/before transition (D − C SMD)

| feature | mean_c | mean_d | smd_d_minus_c | n_c_finite | n_d_finite |
| --- | --- | --- | --- | --- | --- |
| duration_bars | 20.4886 | 6.6819 | -0.9012 | 4529 | 4913 |
| te_er_60 | 0.0863 | 0.0532 | -1.0920 | 4529 | 4913 |
| excursion_atr | 4.4445 | 2.4798 | -0.8355 | 4529 | 4913 |
| pre_er | 0.3592 | 0.5028 | 0.4137 | 4266 | 3731 |
| max_ext_atr | 2.8773 | 1.1937 | -0.8159 | 4529 | 4913 |
| late_share | 0.4937 | 0.4877 | -0.0223 | 3727 | 2638 |


---

## Within-duration-bin D−C destination contrasts (horizon 30m)

| bin | n_c | n_d | eligible | mean_duration_c | mean_duration_d | return | opposite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DUR_T1 | 987 | 2473 | True | 2.4894 | 2.0514 | +22.6 pp | -25.1 pp |
| DUR_T2 | 1106 | 1355 | True | 8.0741 | 7.6974 | +18.3 pp | -18.8 pp |
| DUR_T3 | 2142 | 762 | True | 35.4972 | 19.9738 | +14.1 pp | -14.9 pp |


### Secondary horizon 60m

| bin | n_c | n_d | eligible | return | opposite |
| --- | --- | --- | --- | --- | --- |
| DUR_T1 | 903 | 2270 | True | +13.2 pp | -12.0 pp |
| DUR_T2 | 1001 | 1234 | True | +8.5 pp | -7.8 pp |
| DUR_T3 | 1938 | 683 | True | +7.2 pp | -5.5 pp |


---

## Predeclared classification

- **Classification:** `PROGRESSIVE`
- Base class: `HISTORY_RESIDUAL`
- Progressive upgrade: `True`

- `DUR_T1`: return=+22.6 pp, opposite=-25.1 pp, keeps=(True,True)
- `DUR_T2`: return=+18.3 pp, opposite=-18.8 pp, keeps=(True,True)
- `DUR_T3`: return=+14.1 pp, opposite=-14.9 pp, keeps=(True,True)

---

## Leakage / scope audit

```text
LOOKAHEAD_CHECK = PASS
POST_EVENT_INFO_IN_HISTORY = False
SCOPE_LOW_ER_EXPEXIT_ONLY = True
LOW_ER_CUT_FROZEN_FROM_STEP6 = True
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
```

---

## STEP 7 VERDICT

- Within low-transition-ER ExpExit, the C/D destination asymmetry **survives every eligible duration bin** (history residual) but **shrinks monotonically** as expansion duration lengthens (short: ~+23/−25 pp → long: ~+14/−15 pp). Trajectory age conditions the magnitude; it does not remove the association.
- Wording remains associative: low-ER ExpExit origin cells remain associated with destination behavior under the stated history conditioning — not “exhaustion,” not a trade.

## NEXT RESEARCH QUESTION

Given that the low-ER C/D association **survives all duration bins** but **shrinks monotonically** with longer expansions, does a single frozen shape descriptor (`pre_er` or `max_ext_atr` on `[i0, te)`) account for the residual — still without a trade or CEM expansion?

_Do not answer by building a strategy in this step._
