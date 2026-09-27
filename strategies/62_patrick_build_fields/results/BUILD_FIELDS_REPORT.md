# Patrick Build-Fields Report

Fields only. No trade. No continuation/fade. Prior-session P7 (causal).

## Freeze

- `(q, N) = (0.99, 5000)`, `N_min=500`, reset at Globex roll
- P7 = prior-session POC/VAH/VAL, tol=1 tick
- Open-hour range field: `globex_open_60m_*` (not IB)

## Audit summary

```json
{
  "LOOKAHEAD_CHECK": "PASS",
  "P7_CAUSAL": "prior_session_levels",
  "NO_IB_FIELD_NAME": true,
  "q": 0.99,
  "N": 5000,
  "N_min": 500,
  "tick": 0.25,
  "tol_ticks": 1,
  "n_p1_sessions": 127,
  "n_p1_complete": 96,
  "n_sessions_streamed": 127,
  "p6a_flag_rate_mean": 0.015349863954413498,
  "p6a_flag_rate_p10": 0.01449135090932411,
  "p6a_flag_rate_p50": 0.015202328364383117,
  "p6a_flag_rate_p90": 0.0162830860269576,
  "p6a_flag_rate_max": 0.026,
  "tie_mass_mean": 0.48615347407983717,
  "threshold_on_round_lot_frac_mean": 0.4171514152069202,
  "n_p6a_flagged_prints": 706052,
  "n_p7_joins": 2135,
  "n_p7_sessions_with_hit": 79,
  "p2_sessions": 127,
  "globex_open_60m_fields": [
    "globex_open_60m_high",
    "globex_open_60m_low"
  ],
  "note_p6a_store": "p6a_print_flags.parquet stores flagged prints only; rates from p6a_session_stats.csv"
}
```

## P6a per-session flag rate (head)

session_date  n_trades  n_p6a_valid  n_p6a  flag_rate  tie_mass_at_threshold  threshold_on_round_lot_frac  median_threshold
  2026-03-24    354356       353856   5247   0.014828               0.470745                     0.509916               5.0
  2026-03-25    378275       377775   5852   0.015491               0.501538                     0.408487               5.0
  2026-03-26    386074       385574   6024   0.015623               0.520750                     0.377704               5.0
  2026-03-29    366410       365910   5489   0.015001               0.508107                     0.288508               5.0
  2026-03-30    521859       521359   8127   0.015588               0.506214                     0.483114               5.0
  2026-03-31    393449       392949   5830   0.014837               0.474099                     0.398085               5.0
  2026-04-01    408726       408226   6140   0.015041               0.489414                     0.607222               5.0
  2026-04-02     30949        30449    505   0.016585               0.506931                     0.407238               4.0
  2026-04-05    289900       289400   4893   0.016907               0.550378                     0.562426               5.0
  2026-04-06    395135       394635   5967   0.015120               0.491872                     0.493940               5.0
  2026-04-07    433532       433032   6390   0.014756               0.459155                     0.433640               5.0
  2026-04-08    341457       340957   4954   0.014530               0.461042                     0.254868               6.0
  2026-04-09    284381       283881   4199   0.014791               0.438676                     0.297797               6.0
  2026-04-12    315789       315289   4762   0.015104               0.461991                     0.334312               6.0
  2026-04-13    299713       299213   4334   0.014485               0.437471                     0.233693               7.0

## P2 session meta (head)

session_date  n_periods  n_tpo_cells  globex_open_60m_high  globex_open_60m_low
  2026-03-24         46        12352                   NaN                  NaN
  2026-03-25         46        13194              24373.50             24308.00
  2026-03-26         46        11968              23890.75             23824.00
  2026-03-29         46        12328                   NaN                  NaN
  2026-03-30         46        16579              23147.75             23097.75
  2026-03-31         46        11967              23974.00             23880.00
  2026-04-01         46        13974              24206.00             24158.00
  2026-04-02         31         3530              24219.50             24177.50
  2026-04-05         46        10771                   NaN                  NaN
  2026-04-06         46        14389              24384.00             24299.75

## P7 level mix

level_name
prev_poc    1048
prev_vah     563
prev_val     524
