# Feasibility Report — Strategy 60 (Frame A)

**Not a strategy.** Read-only over 55–59. Cost = 1.0 pt RT.

## Verdict

**`CLASS_STRUCTURALLY_UNDERWATER`** — `55_56_gross_near_0+57_mfe_approx_mae+59_p_below_breakeven`

**Action:** `MORATORIUM_simple_event_hold_and_1R_extension_mechanisms`

## Break-even intuition

```text
E[net] = p·W − (1−p)·L − 1.0
p* = (L + 1) / (W + L)
```

If path is symmetric (MFE ≈ MAE, signed progress ≈ 0):

```text
E[gross] ≈ 0  ⇒  E[net] ≈ −1.0
```

### Grid excerpt (need E_net > 0 at p=55%)

Cells with p=55% clearing cost: **23** / 49

| W | L | p* | E_net@55% |
| --- | --- | --- | --- |
| 4 | 2 | 0.500 | 0.30 |
| 6 | 2 | 0.375 | 1.40 |
| 6 | 4 | 0.500 | 0.50 |
| 8 | 2 | 0.300 | 2.50 |
| 8 | 4 | 0.417 | 1.60 |
| 8 | 6 | 0.500 | 0.70 |
| 10 | 2 | 0.250 | 3.60 |
| 10 | 4 | 0.357 | 2.70 |
| 10 | 6 | 0.438 | 1.80 |
| 10 | 8 | 0.500 | 0.90 |
| 15 | 2 | 0.176 | 6.35 |
| 15 | 4 | 0.263 | 5.45 |

### Instructive p*

| W | L | p* (breakeven) |
| --- | --- | --- |
| 4 | 4 | 0.625 |
| 8 | 8 | 0.562 |
| 10 | 5 | 0.400 |
| 20 | 10 | 0.367 |
| 8 | 4 | 0.417 |

## Inventory 55–59

| ID | name | kind | n_IS | mean_gross | mean_net | note |
| --- | --- | --- | --- | --- | --- | --- |
| 55 | Event A hold | fixed_hold_trade | 51584 | -0.036 | -1.036 | gross~0 → net~-cost |
| 56 | Event B hold | fixed_hold_trade | 38444 | -0.177 | -1.177 | gross~0 → net~-cost |
| 57 | Event B path | path_mfe_mae | 38444 | — | — | med_mfe=0.1980 med_mae=0.1941 symmetric=True |
| 58 | Event C destination | destination_delta | 45869 | — | — | delta=-0.0279 wrong_sign |
| 59 | ORB first-passage | first_passage | 2203 | — | — | p_tgt=0.1575 p_adv=0.3677 dfp=-0.2102 |

## ORB-class payoff envelope (59 geometry)

- Median R: **46.50**
- Model W=1R, L=0.5R → W=46.50, L=23.25
- Break-even p*: **0.348**
- Observed p_target_first (IS): **0.158**
- Gap (p* − obs): **0.190**
- Model E[net] at observed rates: **-2.22**

## Implication

The simple **event → fixed hold / 1R extension** class sits **below water** under 1.0 pt RT given measured path symmetry and first-passage rates.

**Moratorium:** do not start another Strategy-61 event costume.
Next allowed moves: Frame **B** (payoff-defined risk unit) or Frame **C** (refusal map) — only after explicit choice.
