# Refusal Map — Strategy 61 (Frame C)

**Not an entry strategy.** Locked negative knowledge from 52–60.

## Verdict: `MAP_LOCKED`

## Rules

### R1 — PASS

Refuse ORB continuation (≤1R target, adverse=OR_mid)

```json
{
  "p_target_first_IS": 0.1575124829777576,
  "p_star": 0.34767025089605735,
  "delta_fp_IS": -0.2101679527916477,
  "p_adverse_first_IS": 0.3676804357694053
}
```

### R2 — PASS

Refuse promote when MFE≈MAE (path symmetry)

```json
{
  "med_mfe_15": 0.1979780601642081,
  "med_mae_15": 0.1941462021701884,
  "rel_diff": 0.01935496282184729
}
```

### R3 — PASS

Refuse promote fixed hold if |IS mean_gross|≤0.25

```json
{
  "mean_gross_55_IS": -0.035771750930521,
  "mean_gross_56_IS": -0.177192799916762
}
```

### R4 — PASS

Destination alone is not an edge

```json
{
  "56_final": "KILL_AFTER_TRADE",
  "55_mean_net_IS": -1.035771750930521,
  "58_delta_IS": -0.02790555713008791
}
```

### R5 — PASS

Refuse state→generic family routing

```json
{
  "artifact": "D:\\NQ-2\\strategies\\53_regime_strategy_screen\\results\\verdict.json"
}
```

### R6 — PASS

Refuse reopen/retune of killed event costumes (moratorium)

```json
{
  "60_classification": "CLASS_STRUCTURALLY_UNDERWATER",
  "60_action": "MORATORIUM_simple_event_hold_and_1R_extension_mechanisms"
}
```

## Operator summary

| Do not | Why |
| --- | --- |
| ORB ≤1R vs OR mid continuation | Adverse-first / below breakeven p* |
| Promote when MFE≈MAE | Path premium absent; net≈−cost |
| Promote hold with |IS mean_gross| ≤ 0.25 | Cost dominates |
| Treat destination Δ as a trade | 55–58 |
| Route families from census state | 53 all rejected |
| Retune A/B/C/ORB after kill | Moratorium (60) |

## Next

No Strategy 62 event. Frame B only if explicitly chosen later.
