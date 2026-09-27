# SPX 0DTE Dealer Gamma → S&P 500 / NQ Experiment — Final Report

**Verdict: `E`**

Data sourced from FirmTape (https://firmtape.com/).

## 1. Data audit

- **firmtape_sessions**: `33`
- **first_date**: `2024-06-03`
- **last_date**: `2026-09-04`
- **n_observations**: `12859`
- **minutes_per_session_median**: `390.0`
- **minutes_per_session_min**: `379`
- **minutes_per_session_max**: `390`
- **sessions_not_390**: `1`
- **duplicate_timestamps**: `0`
- **timezone**: `America/New_York`
- **calendar_bdays_in_span**: `590`
- **missing_vs_bdays_count**: `557`
- **missing_vs_bdays_sample**: `['2024-06-04', '2024-06-05', '2024-06-06', '2024-06-07', '2024-06-10', '2024-06-11', '2024-06-12', '2024-06-13', '2024-06-14', '2024-06-17', '2024-06-18', '2024-06-19', '2024-06-20', '2024-06-21', '2024-06-24', '2024-06-25', '2024-06-26', '2024-06-27', '2024-06-28', '2024-07-01']`
- **es_range**: `['2024-05-29 09:00:00-04:00', '2026-08-26 16:04:00-04:00']`
- **nq_range**: `['2024-05-29 09:00:00-04:00', '2026-08-07 16:04:00-04:00']`
- **gamma_timing_interpretation**: `Minute label HH:MM treated as end-of-minute snapshot. Signals use gamma lagged by 1 minute (g[t-1] at bar t). Forward returns from close[t] to close[t+h].`
- **ga_backfill_note**: `Archive JSON may include ga_backfill metadata; conventional OI gamma may be reconstructed after the session. Primary tests use ngv_meas (tape-measured).`
- **underlying**: `ES continuous 1m as S&P 500 proxy; NQ for transmission`
- **timestamp_convention_underlying**: `Databento ts_event = bar open; OHLC within minute`

## 2. Causal integrity

Gamma features lagged by 1 minute within session. No same-minute gamma used for decisions. Forward outcomes use close[t]→close[t+h]. Thresholds frozen on Discovery only: {"gamma_q": {"0.2": NaN, "0.4": NaN, "0.6": NaN, "0.8": NaN}, "gamma_norm_q": {"0.2": NaN, "0.4": NaN, "0.6": NaN, "0.8": NaN}, "abs_gamma_q": {"0.5": NaN, "0.8": NaN, "0.9": NaN}, "n_disc": 0}

## 3. Replication of known literature

### Discovery
- `Discovery|rv5|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv5|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv15|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv15|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv30|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv30|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv60|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv60|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv5|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv5|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv15|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv15|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv30|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv30|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv60|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|rv60|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Discovery|mr5|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Discovery|mr5|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Discovery|mr10|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Discovery|mr10|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Discovery|mr15|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Discovery|mr15|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Discovery|mr30|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Discovery|mr30|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
### Validation
- `Validation|rv5|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv5|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv15|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv15|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv30|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv30|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv60|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv60|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv5|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv5|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv15|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv15|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv30|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv30|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv60|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|rv60|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `Validation|mr5|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Validation|mr5|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Validation|mr10|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Validation|mr10|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Validation|mr15|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Validation|mr15|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Validation|mr30|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `Validation|mr30|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
### OOS
- `OOS|rv5|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv5|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv15|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv15|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv30|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv30|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv60|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv60|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv5|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv5|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv15|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv15|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv30|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv30|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv60|neg_vs_pos`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|rv60|E_vs_A`: diff=nan d=nan p=nan p_adj=nan n=0.0/0.0
- `OOS|mr5|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `OOS|mr5|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `OOS|mr10|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `OOS|mr10|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `OOS|mr15|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `OOS|mr15|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `OOS|mr30|pos`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0
- `OOS|mr30|neg`: cont=nan rev=nan theory_ok=None p=nan p_adj=nan n=0.0

## 4. Gamma flip

                                  test  n_a    n_b    mean_a        mean_b      diff  effect_cohen_d    p_raw      stat   n  cont_rate  rev_rate    p_adj
  Discovery|flip_cross_up|ret1_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Discovery|flip_cross_up|ret5_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
   Discovery|flip_cross_up|rv5_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Discovery|flip_cross_up|ret10_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Discovery|flip_cross_up|ret15_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Discovery|flip_cross_up|rv15_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Discovery|flip_cross_up|ret30_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Discovery|flip_cross_up|rv30_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Discovery|flip_cross_dn|ret1_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Discovery|flip_cross_dn|ret5_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
   Discovery|flip_cross_dn|rv5_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Discovery|flip_cross_dn|ret10_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Discovery|flip_cross_dn|ret15_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Discovery|flip_cross_dn|rv15_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Discovery|flip_cross_dn|ret30_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Discovery|flip_cross_dn|rv30_vs_base  0.0    0.0       NaN           NaN       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_up|ret1_vs_base  1.0  389.0  0.000000 -4.913168e-06       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_up|ret5_vs_base  1.0  389.0 -0.000235 -2.531307e-05       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Validation|flip_cross_up|rv5_vs_base  1.0  389.0  0.000211  6.771962e-04       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
Validation|flip_cross_up|ret10_vs_base  1.0  389.0  0.000471 -9.406906e-05       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
Validation|flip_cross_up|ret15_vs_base  1.0  389.0  0.000047 -1.635395e-04       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_up|rv15_vs_base  1.0  389.0  0.000889  1.288797e-03       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
Validation|flip_cross_up|ret30_vs_base  1.0  389.0 -0.001507 -3.072250e-04       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_up|rv30_vs_base  1.0  389.0  0.002263  1.882120e-03       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_dn|ret1_vs_base  0.0  389.0       NaN -4.913168e-06       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_dn|ret5_vs_base  0.0  389.0       NaN -2.531307e-05       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
  Validation|flip_cross_dn|rv5_vs_base  0.0  389.0       NaN  6.771962e-04       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
Validation|flip_cross_dn|ret10_vs_base  0.0  389.0       NaN -9.406906e-05       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
Validation|flip_cross_dn|ret15_vs_base  0.0  389.0       NaN -1.635395e-04       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_dn|rv15_vs_base  0.0  389.0       NaN  1.288797e-03       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
Validation|flip_cross_dn|ret30_vs_base  0.0  389.0       NaN -3.072250e-04       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
 Validation|flip_cross_dn|rv30_vs_base  0.0  389.0       NaN  1.882120e-03       NaN             NaN      NaN       NaN NaN        NaN       NaN      NaN
        OOS|flip_cross_up|ret1_vs_base 35.0 9674.0  0.000015 -6.735065e-07  0.000016        0.061148 0.721805  0.358993 NaN        NaN       NaN 0.771584
        OOS|flip_cross_up|ret5_vs_base 35.0 9674.0 -0.000026 -2.647583e-06 -0.000023       -0.034759 0.855629 -0.183323 NaN        NaN       NaN 0.884150
         OOS|flip_cross_up|rv5_vs_base 35.0 9674.0  0.000750  4.833261e-04  0.000266        0.658888 0.001978  3.351065 NaN        NaN       NaN 0.004088
       OOS|flip_cross_up|ret10_vs_base 35.0 9669.0  0.000437  1.034844e-05  0.000427        0.304440 0.161718  1.430378 NaN        NaN       NaN 0.227875
       OOS|flip_cross_up|ret15_vs_base 35.0 9664.0  0.000496  2.784611e-05  0.000468        0.289034 0.170397  1.400515 NaN        NaN       NaN 0.229666
        OOS|flip_cross_up|rv15_vs_base 35.0 9664.0  0.001643  9.202620e-04  0.000722        0.588318 0.011072  2.686919 NaN        NaN       NaN 0.020191
       OOS|flip_cross_up|ret30_vs_base 35.0 9649.0  0.001021  8.375657e-05  0.000938        0.460966 0.022109  2.397759 NaN        NaN       NaN 0.034269
        OOS|flip_cross_up|rv30_vs_base 35.0 9649.0  0.002285  1.346887e-03  0.000938        0.711739 0.001310  3.502042 NaN        NaN       NaN 0.003125

## 5. Incremental information

[
  {
    "split": "Discovery",
    "error": "insufficient"
  },
  {
    "split": "Validation",
    "error": "insufficient"
  },
  {
    "split": "OOS",
    "n": 9729,
    "r2_base_fwd_ret_5": 0.010042108075026812,
    "r2_gamma_fwd_ret_5": 0.01985523658274524,
    "delta_r2_fwd_ret_5": 0.009813128507718427,
    "r2_base_fwd_rv_15": 0.33034525669040504,
    "r2_gamma_fwd_rv_15": 0.351637218221712,
    "delta_r2_fwd_rv_15": 0.02129196153130697
  },
  {
    "split": "Discovery",
    "error": "insufficient",
    "instrument": "NQ"
  },
  {
    "split": "Validation",
    "error": "insufficient",
    "instrument": "NQ"
  },
  {
    "split": "OOS",
    "n": 4670,
    "r2_base_fwd_ret_5": 0.02371807287803418,
    "r2_gamma_fwd_ret_5": 0.04570845598749729,
    "delta_r2_fwd_ret_5": 0.021990383109463107,
    "r2_base_fwd_rv_15": 0.2726427467671395,
    "r2_gamma_fwd_rv_15": 0.2869329227450079,
    "delta_r2_fwd_rv_15": 0.014290175977868413,
    "instrument": "NQ"
  }
]

## 6. NQ transmission

                         test  n_a  n_b  mean_a  mean_b  diff  effect_cohen_d  p_raw  stat   n  cont_rate  rev_rate  p_adj
  Discovery|NQ|rv5|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
      Discovery|NQ|rv5|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
 Discovery|NQ|rv15|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
     Discovery|NQ|rv15|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
 Discovery|NQ|rv30|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
     Discovery|NQ|rv30|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
 Discovery|NQ|rv60|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
     Discovery|NQ|rv60|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
         Discovery|NQ|mr5|pos  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
         Discovery|NQ|mr5|neg  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
        Discovery|NQ|mr10|pos  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
        Discovery|NQ|mr10|neg  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
        Discovery|NQ|mr15|pos  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
        Discovery|NQ|mr15|neg  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
        Discovery|NQ|mr30|pos  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
        Discovery|NQ|mr30|neg  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
 Validation|NQ|rv5|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
     Validation|NQ|rv5|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
Validation|NQ|rv15|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
    Validation|NQ|rv15|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
Validation|NQ|rv30|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
    Validation|NQ|rv30|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
Validation|NQ|rv60|neg_vs_pos  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
    Validation|NQ|rv60|E_vs_A  0.0  0.0     NaN     NaN   NaN             NaN    NaN   NaN NaN        NaN       NaN    NaN
        Validation|NQ|mr5|pos  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
        Validation|NQ|mr5|neg  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
       Validation|NQ|mr10|pos  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
       Validation|NQ|mr10|neg  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
       Validation|NQ|mr15|pos  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN
       Validation|NQ|mr15|neg  NaN  NaN     NaN     NaN   NaN             NaN    NaN   NaN 0.0        NaN       NaN    NaN

## 7. OOS results

                               test    n_a    n_b        mean_a        mean_b          diff  effect_cohen_d        p_raw      stat   n  cont_rate  rev_rate        p_adj
                 OOS|rv5|neg_vs_pos    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                     OOS|rv5|E_vs_A    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                OOS|rv15|neg_vs_pos    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                    OOS|rv15|E_vs_A    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                OOS|rv30|neg_vs_pos    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                    OOS|rv30|E_vs_A    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                OOS|rv60|neg_vs_pos    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                    OOS|rv60|E_vs_A    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
                        OOS|mr5|pos    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
                        OOS|mr5|neg    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
                       OOS|mr10|pos    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
                       OOS|mr10|neg    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
                       OOS|mr15|pos    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
                       OOS|mr15|neg    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
                       OOS|mr30|pos    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
                       OOS|mr30|neg    NaN    NaN           NaN           NaN           NaN             NaN          NaN       NaN 0.0        NaN       NaN          NaN
     OOS|flip_cross_up|ret1_vs_base   35.0 9674.0  1.537206e-05 -6.735065e-07  1.604557e-05        0.061148 7.218048e-01  0.358993 NaN        NaN       NaN 7.715845e-01
     OOS|flip_cross_up|ret5_vs_base   35.0 9674.0 -2.573946e-05 -2.647583e-06 -2.309188e-05       -0.034759 8.556286e-01 -0.183323 NaN        NaN       NaN 8.841496e-01
      OOS|flip_cross_up|rv5_vs_base   35.0 9674.0  7.497197e-04  4.833261e-04  2.663936e-04        0.658888 1.977966e-03  3.351065 NaN        NaN       NaN 4.087797e-03
    OOS|flip_cross_up|ret10_vs_base   35.0 9669.0  4.372990e-04  1.034844e-05  4.269506e-04        0.304440 1.617178e-01  1.430378 NaN        NaN       NaN 2.278751e-01
    OOS|flip_cross_up|ret15_vs_base   35.0 9664.0  4.958162e-04  2.784611e-05  4.679701e-04        0.289034 1.703973e-01  1.400515 NaN        NaN       NaN 2.296659e-01
     OOS|flip_cross_up|rv15_vs_base   35.0 9664.0  1.642743e-03  9.202620e-04  7.224807e-04        0.588318 1.107224e-02  2.686919 NaN        NaN       NaN 2.019056e-02
    OOS|flip_cross_up|ret30_vs_base   35.0 9649.0  1.021413e-03  8.375657e-05  9.376562e-04        0.460966 2.210933e-02  2.397759 NaN        NaN       NaN 3.426946e-02
     OOS|flip_cross_up|rv30_vs_base   35.0 9649.0  2.284673e-03  1.346887e-03  9.377856e-04        0.711739 1.310377e-03  3.502042 NaN        NaN       NaN 3.124744e-03
     OOS|flip_cross_dn|ret1_vs_base   30.0 9674.0 -7.945067e-07 -6.735065e-07 -1.210002e-07       -0.000404 9.984285e-01 -0.001987 NaN        NaN       NaN 9.984285e-01
     OOS|flip_cross_dn|ret5_vs_base   30.0 9674.0 -1.699510e-04 -2.647583e-06 -1.673035e-04       -0.245209 2.477306e-01 -1.179558 NaN        NaN       NaN 3.071860e-01
      OOS|flip_cross_dn|rv5_vs_base   30.0 9674.0  6.489399e-04  4.833261e-04  1.656138e-04        0.476794 1.986544e-02  2.464267 NaN        NaN       NaN 3.241203e-02
    OOS|flip_cross_dn|ret10_vs_base   30.0 9669.0  2.113791e-04  1.034844e-05  2.010307e-04        0.166264 4.543521e-01  0.758340 NaN        NaN       NaN 5.030327e-01
    OOS|flip_cross_dn|ret15_vs_base   30.0 9664.0  3.282050e-04  2.784611e-05  3.003589e-04        0.205461 3.451057e-01  0.959724 NaN        NaN       NaN 3.962324e-01
     OOS|flip_cross_dn|rv15_vs_base   30.0 9664.0  1.415558e-03  9.202620e-04  4.952957e-04        0.661912 1.935473e-03  3.407223 NaN        NaN       NaN 4.087797e-03
    OOS|flip_cross_dn|ret30_vs_base   30.0 9649.0  1.078994e-03  8.375657e-05  9.952374e-04        0.509295 1.784276e-02  2.510955 NaN        NaN       NaN 3.072920e-02
     OOS|flip_cross_dn|rv30_vs_base   30.0 9649.0  1.987623e-03  1.346887e-03  6.407360e-04        0.689604 3.790501e-04  4.015802 NaN        NaN       NaN 1.068232e-03
           OOS|dist|rv5|near_vs_far  365.0 7886.0  5.787996e-04  4.729302e-04  1.058694e-04        0.345490 1.392657e-10  6.588943 NaN        NaN       NaN 5.396545e-10
       OOS|dist|absret5|near_vs_far  365.0 7886.0  4.845397e-04  3.854644e-04  9.907528e-05        0.255234 3.557286e-06  4.702284 NaN        NaN       NaN 1.225288e-05
          OOS|dist|rv15|near_vs_far  365.0 7883.0  1.370642e-03  8.876447e-04  4.829977e-04        0.526998 4.529641e-15  8.177064 NaN        NaN       NaN 2.808377e-14
      OOS|dist|absret15|near_vs_far  365.0 7883.0  1.259375e-03  7.023555e-04  5.570192e-04        0.494046 2.015599e-13  7.625695 NaN        NaN       NaN 1.041393e-12
          OOS|dist|rv30|near_vs_far  365.0 7868.0  1.809664e-03  1.312347e-03  4.973165e-04        0.473895 1.326157e-15  8.336604 NaN        NaN       NaN 1.027771e-14
      OOS|dist|absret30|near_vs_far  365.0 7868.0  1.600377e-03  1.083406e-03  5.169713e-04        0.390017 5.059918e-11  6.760681 NaN        NaN       NaN 2.240821e-10
        OOS|ix|rv5|ext_near_vs_rest    0.0 9739.0           NaN  4.847936e-04           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
      OOS|ix|rv5|ext_volexp_vs_rest    0.0 9739.0           NaN  4.847936e-04           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
      OOS|ix|corr|g_x_prev5_vs_fwd5 9714.0    0.0 -4.261855e-02  0.000000e+00 -4.261855e-02       -0.042619 2.647584e-05 -0.042619 NaN        NaN       NaN 8.207511e-05
       OOS|ix|rv15|ext_near_vs_rest    0.0 9729.0           NaN  9.243884e-04           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
     OOS|ix|rv15|ext_volexp_vs_rest    0.0 9729.0           NaN  9.243884e-04           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
     OOS|ix|corr|g_x_prev5_vs_fwd15 9704.0    0.0 -3.366845e-02  0.000000e+00 -3.366845e-02       -0.033668 9.093926e-04 -0.033668 NaN        NaN       NaN 2.349264e-03
       OOS|ix|rv30|ext_near_vs_rest    0.0 9714.0           NaN  1.352245e-03           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
     OOS|ix|rv30|ext_volexp_vs_rest    0.0 9714.0           NaN  1.352245e-03           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
     OOS|ix|corr|g_x_prev5_vs_fwd30 9689.0    0.0 -2.619888e-02  0.000000e+00 -2.619888e-02       -0.026199 9.910501e-03 -0.026199 NaN        NaN       NaN 1.920160e-02
OOS|tod|09:30-09:35|rv15_neg_vs_pos    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
OOS|tod|09:35-09:45|rv15_neg_vs_pos    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN
OOS|tod|09:45-10:00|rv15_neg_vs_pos    0.0    0.0           NaN           NaN           NaN             NaN          NaN       NaN NaN        NaN       NaN          NaN

## 8. Economic significance

     split instrument     rule  n
 Discovery         ES   fade_A  0
 Discovery         ES follow_E  0
 Discovery         NQ   fade_A  0
 Discovery         NQ follow_E  0
Validation         ES   fade_A  0
Validation         ES follow_E  0
Validation         NQ   fade_A  0
Validation         NQ follow_E  0
       OOS         ES   fade_A  0
       OOS         ES follow_E  0
       OOS         NQ   fade_A  0
       OOS         NQ follow_E  0

## 9. Failure modes

- FirmTape measured gamma is a reconstruction, not exchange-verified dealer books.
- Conventional OI gamma may include post-session backfill (`ga_backfill`).
- ES futures ≠ SPX cash; basis and roll effects remain.
- Minute timestamp semantics assumed end-of-minute; 1-minute lag is conservative but may blunt true effects.
- Many correlated tests; BH controls FDR but not all dependence.
- Economic rules are illustrative frozen heuristics, not optimized strategies.
- Placebo battery:
                                      test  n_a  n_b mean_a mean_b diff effect_cohen_d p_raw stat
   placebo|future_shift_-1|rv15_neg_vs_pos    0    0   None   None None           None  None None
      placebo|past_shift_1|rv15_neg_vs_pos    0    0   None   None None           None  None None
   placebo|future_shift_-5|rv15_neg_vs_pos    0    0   None   None None           None  None None
      placebo|past_shift_5|rv15_neg_vs_pos    0    0   None   None None           None  None None
  placebo|future_shift_-15|rv15_neg_vs_pos    0    0   None   None None           None  None None
     placebo|past_shift_15|rv15_neg_vs_pos    0    0   None   None None           None  None None
  placebo|future_shift_-30|rv15_neg_vs_pos    0    0   None   None None           None  None None
     placebo|past_shift_30|rv15_neg_vs_pos    0    0   None   None None           None  None None
placebo|shuffle_within_day|rv15_neg_vs_pos    0    0   None   None None           None  None None
         placebo|wrong_day|rv15_neg_vs_pos    0    0   None   None None           None  None None

## 10. Final verdict

`E` — Invalid for confirmatory claim: FirmTape minute archive incomplete (sessions=26, years=[2024, 2026]). Bulk snapshot download blocked by FirmTape visitor limit — see DATA_BLOCKER.md.
