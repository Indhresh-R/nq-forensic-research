# Event A Report — Displacement → Retracement

**Family 1 only.** Frozen definitions. No retuning.

## Funnel

- Onset displacements: 99658
- Events (retracement confirmed): 80482
- Censored (no retrace / event not eligible): 19176

## Leakage / freeze audit

```text
LOOKAHEAD_CHECK = PASS
EVENT_DEFINITION_FROZEN = True
NO_PARAMETER_RETUNE = True
COST_RT = 1.0
```

## Destination asymmetry

| horizon | split | n_valid | p_origin | p_impulse_end | p_extension | delta_ext_minus_origin |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | IS | 53427 | 0.4727 | 0.5120 | 0.1956 | -0.2772 |
| 5 | Validation | 16460 | 0.4738 | 0.4760 | 0.1834 | -0.2905 |
| 5 | OOS | 9155 | 0.4648 | 0.4888 | 0.1768 | -0.2879 |
| 5 | ALL | 79042 | 0.4720 | 0.5018 | 0.1908 | -0.2812 |
| 15 | IS | 51584 | 0.6651 | 0.6899 | 0.4146 | -0.2505 |
| 15 | Validation | 15728 | 0.6666 | 0.6631 | 0.4006 | -0.2660 |
| 15 | OOS | 8778 | 0.6576 | 0.6737 | 0.3937 | -0.2638 |
| 15 | ALL | 76090 | 0.6645 | 0.6825 | 0.4093 | -0.2552 |
| 30 | IS | 49024 | 0.7564 | 0.7691 | 0.5447 | -0.2117 |
| 30 | Validation | 14887 | 0.7597 | 0.7477 | 0.5356 | -0.2240 |
| 30 | OOS | 8325 | 0.7429 | 0.7577 | 0.5318 | -0.2112 |
| 30 | ALL | 72236 | 0.7555 | 0.7634 | 0.5414 | -0.2142 |
| 60 | IS | 44034 | 0.8183 | 0.8262 | 0.6492 | -0.1691 |
| 60 | Validation | 13495 | 0.8247 | 0.8064 | 0.6399 | -0.1849 |
| 60 | OOS | 7493 | 0.8068 | 0.8176 | 0.6427 | -0.1640 |
| 60 | ALL | 65022 | 0.8183 | 0.8211 | 0.6466 | -0.1718 |


Primary contrast Δ = P(extension) − P(origin) at 15m.

## Step 1 / 2 verdict

- **Classification:** `KILL`
- **Stage:** `STEP2`
- **Reason:** `IS_VAL_OOS_stable`
- **Final:** `KILL_AFTER_TRADE`

- IS: n=51584, P(origin)=0.6650511786600496, P(extension)=0.4145665322580645, Δ=-25.0 pp
- Validation: n=15728, P(origin)=0.6665818921668362, P(extension)=0.40062309257375384, Δ=-26.6 pp
- OOS: n=8778, P(origin)=0.657552973342447, P(extension)=0.39371155160628846, Δ=-26.4 pp

## Path feasibility (descriptive)

| horizon | n | median_hl_range | p25 | p75 | cost_rt |
| --- | --- | --- | --- | --- | --- |
| 5.0000 | 79042.00 | 9.0000 | 3.7500 | 20.00 | 1.0000 |
| 15.00 | 76090.00 | 15.50 | 6.5000 | 34.25 | 1.0000 |


## Trade test

Side rule: `against_impulse` (from IS sign of Δ).
Entry open[t+1], exit close[t+15], cost 1.0 pt RT.

| split | n_trades | mean_gross | mean_net | median_net | hit_rate | eligible |
| --- | --- | --- | --- | --- | --- | --- |
| IS | 51584 | -0.0358 | -1.0358 | -1.0000 | 0.4033 | True |
| Validation | 15728 | 0.0389 | -0.9611 | -1.0000 | 0.4769 | True |
| OOS | 8778 | -0.3190 | -1.3190 | -1.2500 | 0.4761 | True |
| ALL | 76090 | -0.0530 | -1.0530 | -1.0000 | 0.4269 | True |


**Trade classification:** `KILL`

## EVENT A FINAL

**KILL** (`KILL_AFTER_TRADE`). Do not retune W / 1.5 / 0.5 / H_wait. Do not switch to Family 2–4 in this run. Do not add filters.
