# Patrick field inspection — tie vs strict (descriptive)

**No hypothesis. No continuation/fade. No verdict. `(q,N)` unchanged.**

## Namespace problem

P6a mixes **tie** (`size==t`, ~49%) and **strict** (`size>t`, ~51%).

- P7 joins: **2135** = tie **964** + strict **1171** (79 sessions)

## Level mix

```
level_name  prev_poc  prev_vah  prev_val
subgroup                                
strict           611       280       280
tie              437       283       244
```

## RTH open (09–10 ET) share of P7 joins

- Tie: **36.4%**
- Strict: **38.8%**

Both concentrate at RTH open; hour table in `inspect_p7_hour_by_subgroup.csv`.

## Distance / concentration

```
           count      mean       std  min  25%  50%  75%  max
subgroup                                                     
strict    1171.0  0.427839  0.494977  0.0  0.0  0.0  1.0  1.0
tie        964.0  0.513485  0.500078  0.0  0.0  1.0  1.0  1.0
```

Top-5 sessions share of joins: **17.6%**.

## Valid coverage

Mean valid frac **99.32%** — warmup not the main bias.

## Tie-mass stability

Mean **0.486** ± 0.040; only 7 sessions >0.55. **Structural, not outlier-driven.**

## Sample framing

79 sessions / ~2.1k joins (~1.2k strict). Descriptive fold only — not promotable multi-split.

## Next

Read `P6A_SUBGROUP_DECISION.md` before any continuation/fade prereg.
