# Hypothesis — ES↔NQ minute lead/lag at the open (scalp capacity)

## Market behavior under test

At the **NY cash open**, short-horizon **cross-book lead/lag** may exist:
completed ES (NQ) 1-minute returns carry incremental signed information about
the **other** book's next 1–30 minutes — enough, in rare cases, to support a
**fixed 1:1 scalp** of about **20–30 NQ points** (or ES-point equivalent).

```text
ES ret (completed bar t)  →  NQ path t+1..t+H   (es_lead_nq)
NQ ret (completed bar t)  →  ES path t+1..t+H   (nq_lead_es)
```

## Why this is not Strategies 15 / 23D

| Prior | What it tested | Result |
|-------|----------------|--------|
| **15** | Cumulative session open→T ES/NQ **resolvers under HIGH** | B→kill |
| **23D-ES** | **Overnight** ES−NQ relative strength → post-open under HIGH | C |
| **28** | **Minute-level** lead/lag, **open TOD windows**, **fixed scalp path** (MFE/stop) | *this dossier* |

Different information clock (1m lag), different outcome (hit ±20/25/30 before time-stop), not another overnight or HIGH-resolver family.

## Economic / mechanical rationale

At 09:30 ET both books reprice together; microstructure / index-arb lag can
leave one book a bar behind the other. If that lag is stable after costs, a
rules-capped 1–2 tickets/day scalp is possible. If the lead is only same-bar
correlation or collapses after costs → no trade.

## Explicit non-goals

- No multi-TF confluence, ORB, Fib, dealer-gamma, or overnight RS revival
- No Strategy-12 HIGH as a required gate (optional descriptive slice only)
- No stop/target mining — targets frozen at 20 / 25 / 30 NQ pts, 1:1 stop
- No claiming “prop-ready strategy” from Discovery-only prints

## Success / failure

### Success (promote to narrow Phase 3 / rules discussion)

- Descriptive lead (Phase 1) same-sign Discovery → Val → OOS in ≥1 open window
- Scalp probe (Phase 2) **E_net > 0** same-sign Val+OOS for a **pre-registered** cell
- Frequency plausible for 3–4 tickets/week under a 1–2/day cap (not daily spray)

### Failure (close)

- Lead ≈ contemporaneous correlation only; lag-1 Spearman ≈ 0
- Open windows no better than mid-day control
- Scalp E_net ≤ 0 or year-unstable after costs
- Only soft single-window IS hits
