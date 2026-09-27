# Research postmortem — Strategies 52 → 59

**Status:** FROZEN. No new mechanism hunt until Frame A (below) is completed.  
**Date:** 2026-09-23.

---

## One-sentence diagnosis

We got good at finding **destination statistics**. We did not find a **path the book can be paid for** after **1.0 pt RT**.

That is not “50 near-misses.” It is one repeated scientific result wearing different costumes.

---

## Kill taxonomy

| Bucket | Strategies | Meaning |
| --- | --- | --- |
| **A — Wrong directional hypothesis** | 58 (Event C), 59 (ORB) | Predicted side/target loses to the opposite barrier or extreme |
| **B — Destination without holdable path** | 55, 56, 57 | Asymmetry or touch rates real; close-path / MFE–MAE / fixed hold fails |
| **C — Structural / definitional non-edge** | 53, 54 (activity), parts of 52 Step 9 | Routing or magnitude claims that are baselines, definitional, or dead at execution |
| **D — Meta** | — | Horizon shopping / Event D would only recycle A–C |

### Headline numbers (do not reopen)

| ID | Result |
| --- | --- |
| 55 | Trade mean_gross ≈ 0 → mean_net ≈ −1 |
| 56 | Same pattern |
| 57 | Rebreak touch 22%→66%; med prog_close negative; **MFE ≈ MAE** |
| 58 | Δ(anchor−extreme) = **−2.8 pp** (wrong sign) |
| 59 | p_target_first 16% vs p_adverse_first 37%; Δ_fp ≈ **−21 pp** |

---

## Forbidden repeats (hard)

```text
Another destination-menu event (Event D / Family 3 leftover)
ORB / barrier retune (0.5R, different mid, H_cap shop)
Horizon P&L shopping after a killed hold
Reopening 52–59 definitions to “fix” them
Screens that rank many ideas and pick a winner
```

---

## Chosen next frame: **A — Cost / feasibility reality check**

**Not B** (risk-unit redesign) and **not C** (refusal map) yet.

**Why A first:**  
Before inventing Strategy 60-as-mechanism, answer whether the **class** we keep testing is even capable of clearing cost given the path shapes we already measured.

```text
Under cost = 1.0 pt RT and simple NQ 1m execution,
what (win rate, win size, loss size, path symmetry)
is required for mean_net > 0?

Do Strategies 55–59’s empirical gross / MFE–MAE / first-passage
sit inside that region — or structurally outside it?
```

**Interesting because:** if the feasible region is empty (or only reachable with first-passage rates we have never seen), continuing mechanism hunting is irrational. If a narrow region exists, Frame B/C can target it deliberately.

**Project:** Strategy 60 — see `60_cost_feasibility/` (**COMPLETE:** `CLASS_STRUCTURALLY_UNDERWATER`).

**Then chose Frame C** — Strategy 61 refusal map (`MAP_LOCKED`). See `61_refusal_map/COMPLETE.md`.

Frame **B** not started.

---

## After Frame A (decision tree)

| Frame A verdict | Then |
| --- | --- |
| Class infeasible under 1pt + observed path symmetry | Stop simple event→hold hunt; consider Frame **C** (when-not-to-trade) or change cost/execution assumptions explicitly |
| Narrow feasible region exists | Only prereg mechanisms that hit that region (likely Frame **B**: target/adverse payoff math first) |
| Feasible but 55–59 never approached it | Confirms search was mis-aimed; new hunt must be constrained by the envelope |

---

## Emotional truth (still a research fact)

Failing 50+ ideas in this geometry is consistent with:

> **NQ 1m + 1pt RT + symmetric adverse/favorable path ≈ expected net ≈ −cost.**

The fix is not “try harder at Event D.” It is **change the claim class** or **prove a feasibility envelope first.**
