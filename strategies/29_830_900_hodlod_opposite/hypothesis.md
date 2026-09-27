# Hypothesis — 08:30–09:00 HOD/LOD → 09:30 opposite dip/recovery

## Market behavior under test

The **08:30–09:00 ET** window often prints the **high or low of the day**.
At the **09:30** cash open, price offers an **opposite-side** trade: enter after a
**dip and recovery**, targeting the **opposite extreme** of that window (scalp
scale ~20–30 NQ points when the range allows).

```text
08:30–09:00 prints HOD  →  at 09:30 look SHORT (opposite) via dip→recovery
08:30–09:00 prints LOD  →  at 09:30 look LONG  (opposite) via dip→recovery
```

## Causality split (mandatory)

| Study | Allowed at decision? | Role |
|-------|----------------------|------|
| **A frequency** | End-of-day extremes | How often is the claim true? |
| **B oracle** | Uses end-of-day HOD/LOD label | **Upper bound only** — not tradable |
| **C causal** | Info ≤ 09:00 / trigger bars only | Real strategy candidate |

If B fails → idea is dead even with perfect labels.  
If B works but C fails → need a better causal classifier, not target mining.

## Economic rationale

Pre-cash push into a session extreme can be a liquidity/stop run; NY open
reprices the opposite way. Dip-and-recovery is the confirmation trigger.

## Success / failure

### Success

- Phase A: material HOD-or-LOD rate (not ~coin-flip noise vs other 30m windows)
- Phase B: oracle opposite scalp E_net > 0 Val+OOS (fixed rules)
- Phase C: causal proxy same-sign Val+OOS; frequency compatible with 1–2/day cap

### Failure

- Window is not special vs control TOD for HOD/LOD
- Oracle E_net ≤ 0 after costs / hostile path
- Only oracle works; causal proxies fail → do not live-trade labels
