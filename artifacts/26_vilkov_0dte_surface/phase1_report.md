# Phase 1 — Frozen surface features + raw conditionals

No optimization. Terciles frozen on Discovery only.

- Feature stamps: `18071`
- Panel rows: `18071`
- Date range: `2016-08-31 16:00:00-04:00` → `2024-04-30 16:00:00-04:00`
- Splits: Discovery years 2016-2021, Validation [2022, 2023], OOS [2024]

## Top |Spearman| (Discovery, NQ, absret/rv)
    split instrument  horizon_m                      feature target    n  spearman  abs_rho
Discovery         nq        120                  surf_iv_atm     rv 7607  0.667242 0.667242
Discovery         nq         60                  surf_iv_atm     rv 7607  0.655815 0.655815
Discovery         nq         30                  surf_iv_atm     rv 7607  0.625901 0.625901
Discovery         nq         15                  surf_iv_atm     rv 7607  0.555441 0.555441
Discovery         nq        120            surf_iv_skew_wing     rv 7607  0.522839 0.522839
Discovery         nq         60            surf_iv_skew_wing     rv 7607  0.508434 0.508434
Discovery         nq         15  surf_atm_oi_gamma_abs_share     rv 7544 -0.496425 0.496425
Discovery         nq         30            surf_iv_skew_wing     rv 7607  0.490320 0.490320
Discovery         nq         15            surf_iv_skew_wing     rv 7607  0.487873 0.487873
Discovery         nq         15 surf_near_oi_gamma_abs_share     rv 7544 -0.487550 0.487550
Discovery         nq          5                  surf_iv_atm     rv 7607  0.479524 0.479524
Discovery         nq          5  surf_atm_oi_gamma_abs_share     rv 7544 -0.466026 0.466026
Discovery         nq          5 surf_near_oi_gamma_abs_share     rv 7544 -0.458461 0.458461
Discovery         nq         30  surf_atm_oi_gamma_abs_share     rv 7544 -0.440465 0.440465
Discovery         nq         60  surf_atm_oi_gamma_abs_share     rv 7544 -0.439247 0.439247
Discovery         nq          5            surf_iv_skew_wing     rv 7607  0.437979 0.437979
Discovery         nq         30 surf_near_oi_gamma_abs_share     rv 7544 -0.435002 0.435002
Discovery         nq         60 surf_near_oi_gamma_abs_share     rv 7544 -0.431514 0.431514
Discovery         nq        120  surf_atm_oi_gamma_abs_share     rv 7544 -0.419801 0.419801
Discovery         nq        120 surf_near_oi_gamma_abs_share     rv 7544 -0.406698 0.406698
Discovery         nq        120                  surf_iv_atm absret 7607  0.381034 0.381034
Discovery         nq         60                  surf_iv_atm absret 7607  0.377141 0.377141
Discovery         nq         30                  surf_iv_atm absret 7607  0.372060 0.372060
Discovery         nq          5                  surf_iv_atm absret 7607  0.346404 0.346404
Discovery         nq         15                  surf_iv_atm absret 7607  0.342854 0.342854

## Artifacts
- `surface_features_30m.parquet`
- `phase1_panel_es_nq.parquet`
- `phase1_conditional_terciles.csv`
- `phase1_spearman_corr.csv`
- `phase1_tercile_cuts_discovery.json`