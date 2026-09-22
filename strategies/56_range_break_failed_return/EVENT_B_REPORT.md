# Event B Report — Range Break → Failed Return

**Family 2 only.** Frozen definitions. No retuning. Not Event A.

## Funnel

- Break onsets: 70203 (up=37664, down=32539)
- Events (failed return): 63725
- Censored: 6478

## Leakage / freeze audit

```text
LOOKAHEAD_CHECK = PASS
EVENT_DEFINITION_FROZEN = True
NO_PARAMETER_RETUNE = True
NO_EVENT_A_COMBINE = True
COST_RT = 1.0
```

## Destination asymmetry

| horizon | split | n_valid | p_opposite | p_mid | p_rebreak | delta_opp_minus_rebreak |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | IS | 40094 | 0.0034 | 0.0287 | 0.2161 | -0.2128 |
| 5 | Validation | 14578 | 0.0032 | 0.0351 | 0.1961 | -0.1929 |
| 5 | OOS | 7570 | 0.0033 | 0.0412 | 0.2024 | -0.1991 |
| 5 | ALL | 62242 | 0.0033 | 0.0317 | 0.2098 | -0.2064 |
| 15 | IS | 38444 | 0.0152 | 0.1179 | 0.4223 | -0.4070 |
| 15 | Validation | 14012 | 0.0153 | 0.1248 | 0.3902 | -0.3748 |
| 15 | OOS | 7230 | 0.0172 | 0.1461 | 0.3929 | -0.3758 |
| 15 | ALL | 59686 | 0.0155 | 0.1229 | 0.4112 | -0.3957 |
| 30 | IS | 36201 | 0.0438 | 0.2420 | 0.5513 | -0.5076 |
| 30 | Validation | 13316 | 0.0481 | 0.2402 | 0.5272 | -0.4790 |
| 30 | OOS | 6867 | 0.0517 | 0.2637 | 0.5261 | -0.4744 |
| 30 | ALL | 56384 | 0.0458 | 0.2442 | 0.5426 | -0.4968 |
| 60 | IS | 31883 | 0.1108 | 0.3857 | 0.6574 | -0.5466 |
| 60 | Validation | 11851 | 0.1098 | 0.3714 | 0.6525 | -0.5427 |
| 60 | OOS | 6129 | 0.1127 | 0.3851 | 0.6355 | -0.5228 |
| 60 | ALL | 49863 | 0.1108 | 0.3822 | 0.6536 | -0.5427 |


Primary Δ = P(opposite) − P(rebreak) at 15m.

## Step 1 / 2 verdict

- **Classification:** `KILL`
- **Stage:** `STEP2`
- **Reason:** `IS_VAL_OOS_stable`
- **Final:** `KILL_AFTER_TRADE`

- IS: n=38444, P(opp)=0.015216938924149413, P(rebreak)=0.4222505462490896, Δ=-40.7 pp
- Validation: n=14012, P(opp)=0.01534399086497288, P(rebreak)=0.390165572366543, Δ=-37.5 pp
- OOS: n=7230, P(opp)=0.01715076071922545, P(rebreak)=0.3929460580912863, Δ=-37.6 pp

## Path feasibility (descriptive)

| horizon | n | median_hl_range | p25 | p75 | cost_rt |
| --- | --- | --- | --- | --- | --- |
| 5.0000 | 62242.00 | 11.25 | 4.5000 | 22.25 | 1.0000 |
| 15.00 | 59686.00 | 19.50 | 7.7500 | 38.25 | 1.0000 |


## Trade test

Side rule: `toward_rebreak` (from IS sign of Δ).
Entry open[t+1], exit close[t+15], cost 1.0 pt RT.

| split | n_trades | mean_gross | mean_net | median_net | hit_rate | eligible |
| --- | --- | --- | --- | --- | --- | --- |
| IS | 38444 | -0.1772 | -1.1772 | -1.2500 | 0.3960 | True |
| Validation | 14012 | 0.0108 | -0.9892 | -0.7500 | 0.4814 | True |
| OOS | 7230 | 0.0715 | -0.9285 | -1.5000 | 0.4783 | True |
| ALL | 59686 | -0.1029 | -1.1029 | -1.2500 | 0.4260 | True |


**Trade classification:** `KILL`

## EVENT B FINAL

**KILL** (`KILL_AFTER_TRADE`). Do not retune W / H_wait / 0.25R. Do not fix Event A. Do not start Family 3/4 in this run.
