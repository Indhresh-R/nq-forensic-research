# Phase 2 — Incremental R² + hostile placebos

No optimization. Coefficients fit on earlier splits only; R² scored on later splits.

## Primary question

Does OI-gamma concentration (ATM share) add OOS explanatory power for forward RV after TOD + prior return/RV/range + IV ATM?

## OOS ΔR² (fit Discovery+Validation → score OOS, target=RV)

```
model                 B_oi_gamma  C_volg_skew  atm_share_only  family_iv_vs_no_iv
instrument horizon_m                                                             
es         5           -0.001025     0.005459       -0.001423            0.021503
           15           0.011734     0.017367        0.000391            0.040771
           30           0.014269     0.023829        0.011682            0.067762
           60           0.029361     0.032651        0.014403            0.102687
           120          0.029603     0.032654        0.003360            0.121158
nq         5            0.006835     0.005835        0.005410            0.007533
           15          -0.001941     0.003971       -0.000542            0.013774
           30          -0.018286    -0.003833       -0.004239            0.032925
           60           0.001670     0.014727        0.006311            0.072522
           120          0.014235     0.028715        0.000711            0.099067
```

## Placebos (ΔR² for atm_share_only, NQ RV 30m)

```
     placebo  delta_r2     r2_A   r2_ext  n_test
    identity -0.004239 0.332500 0.328261     870
permute_rows -0.000045 0.332641 0.332597     870
 shift_fwd_1 -0.001661 0.457872 0.456211     804
 shift_fwd_2 -0.001573 0.472967 0.471394     738
shift_back_1 -0.000793 0.297939 0.297146     802
shift_back_2 -0.000548 0.275990 0.275442     734
   wrong_day -0.005198 0.332347 0.327149     870
```

## Year stability note

Vilkov `data_opt` ends **2024-05-01** — **2025–2026 years are not in this panel.** Year table covers 2016–2024 only.

```
 year                 protocol  delta_r2  n_test
 2016       loo_Discovery_year  0.012706     418
 2017       loo_Discovery_year  0.002483    1418
 2018       loo_Discovery_year  0.000812    1344
 2019       loo_Discovery_year  0.001614    1447
 2020       loo_Discovery_year -0.014140    1460
 2021       loo_Discovery_year  0.016128    1457
 2022 fit_Discovery_score_year  0.004033    2227
 2023 fit_Discovery_score_year  0.005621    2590
 2024 fit_Discovery_score_year -0.001060     870
```

## Direction (signed ret) OOS ΔR² — expect near zero

```
model                 B_oi_gamma  atm_share_only
instrument horizon_m                            
es         5           -0.007207       -0.001079
           15          -0.009749        0.001148
           30          -0.001097        0.004319
           60           0.005423        0.005091
           120          0.013047        0.009142
nq         5           -0.004994       -0.000976
           15          -0.006950        0.000243
           30          -0.003023        0.002272
           60           0.003730        0.002593
           120          0.010530        0.006155
```

## Verdict

**WEAK_OR_UNSTABLE** — Some positive incremental RV R², but small / not clearly surviving both legs and placebos. Do not promote to strategy search yet.

## Artifacts

- `phase2_incremental_r2.csv`
- `phase2_year_stability.csv`
- `phase2_placebos.csv`
- `phase2_verdict.json`
