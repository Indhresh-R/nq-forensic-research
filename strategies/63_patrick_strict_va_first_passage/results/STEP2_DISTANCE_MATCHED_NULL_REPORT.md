# Patrick VA Step 2 — Distance-Matched First-Passage Null

**Mechanism diagnostic only. NO TRADE. NO P&L. No promote.**

**Verdict: `KILL` (code A)**

Observed Δ statistically consistent with the distance-matched null (barrier geometry explains pooled first-passage asymmetry).

## Frozen contract

- Parent prereg: `PATRICK_VA_STEP2_DISTANCE_NULL_PREREGISTRATION.md`
- Events: Step-1 `events_strict_va.parquet`, `subgroup == strict`
- n_strict = **338**
- Levels: prev_VAH / prev_VAL; TPO = false; H_CAP = 60m
- Barriers / timestamps: unchanged from Step 1
- Terciles: frozen Step-1 `qcut(dist_ratio, 3)`

## Null construction

Zero-drift arithmetic Brownian motion per event:
- into barrier at `-dist_into`, away at `+dist_away`
- `dX = σ_i dW`, absorb on first hit; else unresolved at T=3600s
- `σ_i`: causal pre-event 1s last-trade return std in [30m before t0); floor=0.25; thin-window fill = sample median of finite σ̂
- Monte Carlo: N_SIM=10000, SEED=20260923, DT_SEC=15.0
- Same-step both barriers → `away_first`
- Null does not alter observed labels or sample selection

- σ finite events: 338 / fill: 0 / median_fill: 1.565027

## Barrier-distance audit (observed)

- med dist_into: **87.000**
- med dist_away: **45.375**
- med dist_ratio: **2.090**

## Pooled strict primary (n=338)

| Statistic | Value |
| --- | ---: |
| observed p_into | 0.201183 |
| observed p_away | 0.437870 |
| observed p_unresolved | 0.360947 |
| observed Delta | -0.236686 |
| null mean Delta | -0.213374 |
| null 95% interval | [-0.298817, -0.127219] |
| empirical two-sided p | 0.600000 |
| null mean p_into / p_away / p_unres | 0.2680 / 0.4814 / 0.2505 |
| N_SIM / SEED | 10000 / 20260923 |

## Dist_ratio terciles (frozen)

| Tercile | n | p_into | p_away | Delta_obs | null mean Δ | null 95% | p |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| T1_low | 114 | 0.3333 | 0.3947 | -0.0614 | 0.0513 | [-0.1140, 0.2193] | 0.1746 |
| T2_mid | 111 | 0.2072 | 0.4955 | -0.2883 | -0.2949 | [-0.4505, -0.1351] | 0.9442 |
| T3_high | 113 | 0.0619 | 0.4248 | -0.3628 | -0.4003 | [-0.5221, -0.2743] | 0.5900 |

## Audit

```json
{
  "LOOKAHEAD_CHECK": "PASS",
  "n_strict": 338,
  "timestamps_unchanged": true,
  "dist_into_away_unchanged": true,
  "same_print_both_count": 0,
  "sigma_uses_pre_event_only": true,
  "null_does_not_alter_observed_labels": true,
  "SEED": 20260923,
  "N_SIM": 10000,
  "DT_SEC": 15.0,
  "H_CAP_SEC": 3600.0,
  "W_PRE_MIN": 30
}
```

## Final verdict

**`KILL`** — Observed Δ statistically consistent with the distance-matched null (barrier geometry explains pooled first-passage asymmetry).

**Explicit: no trade was tested. No P&L. No IS/OOS promotion.**
