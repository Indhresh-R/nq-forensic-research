# Conclusion — OR5 Liquidity Sweep Fade

## Verdict

**`D` / FAILED** — prior “edge” is an execution artifact (favorable through-stop fills), not a causal edge.

## Why (numbers)

- Contaminated OOS ORB-gate: n=280, WR=64.3%, PF=**6.17**
- Through-stop trades = **59.6%** of book and **99.6%** of OOS PnL
- Causal reject-through stress: OOS ORB PF **0.80**, exp **−$17.56**; 2026 reject PF **0.18**
- Gap-through PRIMARY OOS PF **0.75** (n=613)

## Split snapshot

| Split | Result |
|-------|--------|
| IS | mixed / early weak (2010–18 PF ~0.97) |
| Validation | rising but still contaminated |
| OOS | headline strong → **fails** under reject-through |

## What not to do next

- Do not resurrect Inverse ORB / OR5 on close-fill or gap-stop-at-entry books
- Do not treat PF≈6 OOS as real without through-stop classification
