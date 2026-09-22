# Step 5 — Signed exit position (ExpExit diagnostic)

**Status:** Complete (single-feature mechanism diagnostic).
**Scope:** ExpExit C vs D only. Not a trade. Not a new CEM.

## Feature

$S = (P_{\mathrm{event}} - P_{\mathrm{mid}}) / R$

with `P_event = close[te]`, and `P_mid`, `R` from the pre-event envelope `[i0, te)`.

IS-frozen terciles: q33=-0.1894998446722586, q67=0.20588235294117646 (n_IS=20834).

---

## Composition (where C vs D sit in S)

### Terciles

| origin_cell | bin | n | pct_of_cell | mean_S |
| --- | --- | --- | --- | --- |
| C_EXP_HIGH_DIR | S_T1 | 7670 | 31.566 | -0.5324 |
| C_EXP_HIGH_DIR | S_T2 | 8689 | 35.760 | 0.0121 |
| C_EXP_HIGH_DIR | S_T3 | 7939 | 32.673 | 0.5156 |
| D_EXP_LOW_DIR | nan | 1 | 0.0178 | nan |
| D_EXP_LOW_DIR | S_T1 | 2234 | 39.857 | -0.7147 |
| D_EXP_LOW_DIR | S_T2 | 1419 | 25.317 | 0.0033 |
| D_EXP_LOW_DIR | S_T3 | 1951 | 34.808 | 0.6947 |


### Sign

| origin_cell | bin | n | pct_of_cell | mean_S |
| --- | --- | --- | --- | --- |
| C_EXP_HIGH_DIR | ABOVE_OR_AT | 12769 | 52.552 | 0.3585 |
| C_EXP_HIGH_DIR | BELOW | 11529 | 47.448 | -0.3870 |
| D_EXP_LOW_DIR | ABOVE_OR_AT | 2714 | 48.421 | 0.5258 |
| D_EXP_LOW_DIR | BELOW | 2890 | 51.561 | -0.5756 |
| D_EXP_LOW_DIR | nan | 1 | 0.0178 | nan |


---

## Within-bin destination contrasts (D − C), horizon 30m

### S terciles

| bin | n_c | n_d | eligible | mean_S_c | mean_S_d | return | opposite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nan | 0 | 1 | False | nan | nan | n/a | n/a |
| S_T1 | 7085 | 2067 | True | -0.5313 | -0.7027 | +12.5 pp | -13.6 pp |
| S_T2 | 8087 | 1337 | True | 0.0123 | 0.0047 | +13.0 pp | -14.3 pp |
| S_T3 | 7388 | 1826 | True | 0.5102 | 0.6870 | +17.5 pp | -14.9 pp |


### Sign bins

| bin | n_c | n_d | eligible | return | opposite |
| --- | --- | --- | --- | --- | --- |
| ABOVE_OR_AT | 11885 | 2549 | True | +16.9 pp | -15.3 pp |
| BELOW | 10675 | 2681 | True | +13.2 pp | -14.5 pp |
| nan | 0 | 1 | False | n/a | n/a |


60m and CIs: `results/step5_within_bin_contrasts.csv`.

---

## Predeclared classification

- **Classification:** `REMAIN`
- Eligible tercile bins: 3
- Bins keeping both endpoints: 3
- Bins losing both endpoints: 0

### Eligible-bin detail

- `S_T1`: return=+12.5 pp, opposite=-13.6 pp, keep_signs=(True,True), ge_half=(True,True)
- `S_T2`: return=+13.0 pp, opposite=-14.3 pp, keep_signs=(True,True), ge_half=(True,True)
- `S_T3`: return=+17.5 pp, opposite=-14.9 pp, keep_signs=(True,True), ge_half=(True,True)

---

## Leakage / scope audit

```text
LOOKAHEAD_CHECK = PASS
POST_EVENT_INFO_IN_FEATURE = False
SCOPE_EXPEXIT_ONLY = True
OUTCOME_DATA_USED = False
STRATEGY_DATA_USED = False
```

---

## STEP 5 VERDICT

- Within comparable signed-position terciles, the ExpExit C/D destination asymmetry **remains**. This is more consistent with **directionality-at-exit** as an associative description — still not a causal proof, and not a trade.
- CompExit was intentionally not re-tested.

## NEXT RESEARCH QUESTION

Given that signed exit location does not remove the ExpExit destination asymmetry, what is the smallest *non-directional-label* pre-event state descriptor (still frozen before outcomes) that could falsify directionality-at-exit — without constructing a trade?

_Do not answer by building a strategy in this step._
