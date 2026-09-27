# Patrick Strict VA First-Passage Report (v2)

**DESCRIPTIVE_ONLY. No promote. VP+size half-stack. TPO deferred.**

## Freeze / audit

```json
{
  "LOOKAHEAD_CHECK": "PASS",
  "P6A_SUBGROUP": "strict_primary",
  "LEVELS": "prev_vah_prev_val",
  "TPO": false,
  "RESOLUTION": "trade_level",
  "NO_IS_SPLIT": true,
  "NO_PROMOTE": true,
  "H_CAP_MIN": 60,
  "same_print_both_count": 0,
  "same_print_both_rate": 0.0,
  "n_strict": 338,
  "n_tie": 362
}
```

Strict onsets after dedup: **338** (pre-dedup meta {'n_pre_dedup': 560, 'n_onset': 338, 'n_dedup_dropped': 222}). Sessions: **70**.

## Barrier distances (mandatory context for Δ)

- med dist_into (to POC): **87.000**
- med dist_away: **45.375**
- med dist_ratio (into/away): **2.090** (IQR 1.573)

## First-passage (strict primary)

- p_into: **0.2012**
- p_away: **0.4379**
- p_unresolved: **0.3609**
- Δ (into−away): **-0.2367** — *not interpretable without dist_ratio strata below*
- same_print_both rate: **0.0000**

## Δ by dist_ratio tercile (descriptive strata)

                 label   n   p_into   p_away  p_unresolved     delta  med_dist_into  med_dist_away  med_dist_ratio  iqr_dist_ratio  same_print_both_rate  med_ae_into_first  med_ae_away_first  med_ae_into_first_frac_dist_away  med_ae_away_first_frac_dist_into
 strict_primary|T1_low 114 0.333333 0.394737      0.271930 -0.061404           53.5        68.0625        0.985138        0.410818                   0.0             13.375             15.000                          0.196511                          0.280374
 strict_primary|T2_mid 111 0.207207 0.495495      0.297297 -0.288288           81.5        41.0625        2.090452        0.722113                   0.0             14.000             19.000                          0.340944                          0.233129
strict_primary|T3_high 113 0.061947 0.424779      0.513274 -0.362832          127.0        45.3750        3.053892        0.627423                   0.0             14.750             20.625                          0.325069                          0.162402

## Outcome-conditioned adverse excursion

   outcome   n  med_adverse  med_adverse_frac_own_bound     bound
into_first  68        14.25                    0.314050 dist_away
away_first 148        18.00                    0.206897 dist_into

## Tie robustness (not primary)

n=362 Δ=-0.21546961325966849 p_into=0.2292817679558011 p_away=0.4447513812154696

## Verdict

**DESCRIPTIVE_ONLY / INCONCLUSIVE_AT_THIS_N.** No SUPPORTED. No trade.
