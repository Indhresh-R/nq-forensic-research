# Strategy 65 — C1 Drive-Exterior Continuation Sleeve

**Gate:** C1_DRIVE_EXT @ 10:30 → with-trend → stop / 12:00 time exit. Cost 1.0 pt RT.

**Verdict: `KILL`**

IS mean_net=-0.1070 ≤ 0

## Freeze

```json
{
  "GATE_CLOCK": "10:30",
  "GATE_CHARACTER": "C1_DRIVE_EXT",
  "ENTRY_MIN": 631,
  "EXIT_MIN": 720,
  "STOP_RANGE_FRAC": 0.35,
  "STOP_FLOOR": 2.0,
  "COST_RT": 1.0,
  "NO_TARGET": true,
  "NO_TRAIL": true,
  "NOT_ORB": true,
  "NOT_VA_FADE": true,
  "n_gates": 930,
  "n_trades": 928
}
```

## Summary by split

split   n  mean_gross  mean_net  med_net  stop_rate  time_exit_rate  med_mfe  med_mae  mfe_mae_rel_diff  win_rate_net
  All 928    2.965127  1.965127    -1.00   0.337284        0.661638   15.750   13.250          0.188679      0.474138
   IS 421    0.892993 -0.107007    -1.25   0.372922        0.624703    7.250    6.750          0.074074      0.448931
  Val 263    3.537928  2.537928    -0.75   0.277567        0.722433   31.000   22.750          0.362637      0.482890
  OOS 244    5.923002  4.923002     2.25   0.340164        0.659836   43.875   44.125         -0.005666      0.508197

## Interpretation

- KILL → do not trail / do not shop characters.
- INCONCLUSIVE → no risk-design follow-on.
- ADVANCE_RISK_DESIGN → new charter only (trails), not live.

**No live trading from this run.**
