# Phase 3 — Stability / mechanism audit

No threshold search. No trading rules. No Sharpe hunting.

Question: why does residual ATM OI-gamma concentration relate to subsequent ES RV,
and is that relationship coherent / stable enough to justify a trading-rule phase?

## Classification context (Phase 2)

**C — Research signal, not trading edge.** Small positive ES residual ΔR²; NQ transfer weak.

## 1. Gamma × IV regime (DiscVal→OOS, atm_share)

```
regime                    high       low       mid
instrument horizon_m                              
es         15        -0.005031  0.019997 -0.007563
           30         0.013876  0.007466 -0.007799
           60         0.002440  0.033452  0.018813
nq         15        -0.002834 -0.000673 -0.004091
           30        -0.010693 -0.013373 -0.014426
           60         0.002143 -0.002622 -0.001098
```

Interaction extra ΔR² (atm × z(IV) after A+atm):
```
                      delta_r2_interaction_extra
instrument horizon_m                            
es         15                          -0.001194
           30                          -0.003022
           60                          -0.000618
nq         15                          -0.003129
           30                          -0.007981
           60                          -0.003059
```

## 2. Gamma × prior-RV regime

```
regime                    high       low       mid
instrument horizon_m                              
es         15        -0.010027 -0.000237 -0.001360
           30        -0.013802  0.017298  0.004920
           60        -0.003866  0.011962  0.017399
nq         15        -0.003264 -0.001803 -0.001757
           30        -0.026072  0.016010 -0.022384
           60        -0.019332  0.012971  0.004770
```

## 3. Surface-part probes (which slice of 0.98–1.02)

```
part                  atm_share  m_centroid   m_slope  near_share   pc_asym  peak_dist
instrument horizon_m                                                                  
es         15          0.000391    0.000782  0.000058    0.003458  0.000045  -0.000003
           30          0.011682    0.000164  0.000047    0.008164  0.000527   0.000791
           60          0.014403   -0.000292  0.000111    0.012886  0.000252   0.001206
nq         15         -0.000542    0.000723 -0.000002   -0.001315 -0.000074   0.000139
           30         -0.004239    0.000022  0.000002   -0.007797 -0.000264   0.000683
           60          0.006311   -0.000553  0.000010    0.004519 -0.000930   0.001295
```

## 4. ES lead → NQ response

Discovery Spearman(es_rv, nq_rv):
```
nq_horizon_m        15        30        60
es_horizon_m                              
5             0.766805  0.720023  0.682956
15            0.908453  0.868328  0.831078
30            0.866628  0.925674  0.892117
```

NQ RV: ΔR² of atm_share **after** A_nq + es_rv control:
```
es_horizon_m        5         15        30
nq_horizon_m                              
15           -0.000002  0.001022  0.009775
30            0.002251  0.000735  0.001757
60            0.009408  0.004879 -0.004685
```

ES RV: ΔR² of atm_share after A_es + nq_rv (symmetry check):
```
nq_horizon_m        5         15        30
es_horizon_m                              
15            0.004188 -0.000122 -0.000734
30            0.019324  0.012075  0.002366
60            0.020985  0.015898  0.006116
```

## 5. Time-of-day decomposition (ES RV 30m)

```
  tod  delta_r2  n_train  n_test
10:00 -0.061517      956      68
10:30 -0.001570      956      68
11:00 -0.002661      957      68
11:30  0.003360      957      68
12:00  0.001865      957      68
12:30 -0.000350      957      68
13:00 -0.021728      912      66
13:30  0.009286      909      66
14:00 -0.014078      909      66
14:30 -0.004365      909      66
15:00  0.001816      909      66
15:30 -0.007348      909      66
16:00 -0.004341     1164      66
```

## 6. Chronological blocks (atm_share ΔR²)

```
block                 2016_2018  2019_2021  2022_2023      2024
instrument horizon_m                                           
es         15          0.003700  -0.002619   0.001305  0.000391
           30          0.011786  -0.012636   0.013785  0.011682
           60          0.007637  -0.013037   0.008687  0.014403
nq         15          0.000036  -0.001339  -0.000179 -0.000542
           30          0.002703  -0.014235   0.003752 -0.004239
           60          0.000976  -0.015654   0.002560  0.006311
```

## 7. Mechanism falsification (matched scramble)

ES RV 30m:
```
                      how  delta_r2     r2_A   r2_ext  n_test
                 identity  0.011682 0.389278 0.400960     870
           permute_global -0.001388 0.389512 0.388124     870
permute_within_iv_tercile -0.001635 0.389331 0.387696     870
       permute_within_tod -0.005720 0.389459 0.383739     870
   gaussian_match_moments -0.000295 0.389278 0.388984     870
         residual_permute  0.000031 0.389278 0.389310     870
```

ES RV 60m:
```
                      how  delta_r2     r2_A   r2_ext  n_test
                 identity  0.014403 0.370323 0.384725     870
           permute_global  0.000007 0.370695 0.370702     870
permute_within_iv_tercile -0.000008 0.370382 0.370375     870
       permute_within_tod  0.003130 0.370525 0.373656     870
   gaussian_match_moments -0.000142 0.370323 0.370181     870
         residual_permute -0.000320 0.370323 0.370003     870
```

## Verdict

**MIXED_MECHANISM** — Some conditional structure exists, but stability / falsification / transfer checks are mixed. Do not open trading-rule search; archive or narrow only with new data.

### Headline diagnostics

- ES RV30 identity ΔR²: `0.011682`
- Mean matched-null ΔR²: `-0.001905`
- Beats matched nulls: `True`
- IV-regime ΔR² spread (ES30): `0.021676`
- Prior-RV regime ΔR² spread (ES30): `0.031100`
- Chrono blocks frac(ΔR²>0.002) ES30: `0.75`
- TOD stamps frac(ΔR²>0.002) ES30: `0.15384615384615385`
- ATM share is strongest surface-part probe (ES30): `True`
- Mean NQ30 ΔR² after ES-RV control: `0.001581`

## Artifacts

- `phase3_iv_regime.csv`
- `phase3_vol_regime.csv`
- `phase3_surface_part.csv`
- `phase3_es_lead_nq.csv`
- `phase3_tod.csv`
- `phase3_chrono_blocks.csv`
- `phase3_falsification.csv`
- `phase3_verdict.json`
