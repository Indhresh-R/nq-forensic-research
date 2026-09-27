# Strategy 61 — Refusal Map (Frame C)

**Status:** FROZEN PREREG BEFORE VERIFICATION.  
**Namespace:** `strategies/61_refusal_map/`  
**Parents:** `RESEARCH_POSTMORTEM_52_59.md`, Strategy 60 `CLASS_STRUCTURALLY_UNDERWATER`  
**Choice:** Frame **C** (not B). No new entry signal.

---

## Why C (not B)

Frame B would design another payoff geometry and hunt again.  
Strategy 60 showed the **simple event→hold / 1R-extension class is underwater** under 1pt RT + measured path symmetry.  

Frame C treats 52–60 as a **negative knowledge product**: rules for when **not** to trade / not to promote a research candidate.

---

## Research question

> Can we lock a small, preregistered set of **refusal rules** whose supporting evidence remains true on the frozen 55–60 artifacts (IS/Val/OOS where applicable), with no retuning?

Success = **`MAP_LOCKED`**.  
This does **not** claim a profitable strategy.

---

## Refusal rules (frozen — do not optimize)

| ID | Rule | Evidence source |
| --- | --- | --- |
| **R1** | Do **not** trade **ORB break continuation** with target ≤ `1×R` and adverse = `OR_mid` (Strategy 59 geometry). | 59: p_target_first ≪ p*; adverse-first dominates |
| **R2** | Do **not** promote a candidate whose path diagnostic has **MFE ≈ MAE** (within 10% on IS primary horizon) to a trade test. | 57 + 60 |
| **R3** | Do **not** promote a fixed-horizon hold if IS **\|mean_gross\| ≤ 0.25** pts (cost 1.0 will dominate). | 55, 56, 60 |
| **R4** | Do **not** treat **destination asymmetry alone** as an edge (require path / first-passage / MAE before any trade). | 55–58 lesson |
| **R5** | Do **not** route generic strategy families from **census market state** alone. | 53 |
| **R6** | Do **not** reopen / retune Events A/B/C or ORB constants to rescue a kill. | Ledger moratorium |

---

## Verification (read-only)

For each rule, load frozen artifacts and assert the supporting inequality still holds.

| Rule | Pass condition |
| --- | --- |
| R1 | 59 IS `p_target_first` < orb `p_star` from 60 envelope (or Δ_fp < 0) |
| R2 | 57 IS h=15: `|med_mfe − med_mae| / max(med_mfe, med_mae) ≤ 0.10` |
| R3 | 55 and 56 IS `|mean_gross| ≤ 0.25` |
| R4 | Documentary + 58 wrong-sign Δ **or** 55/56 kill-after-trade present |
| R5 | 53 verdict all cells REJECTED (from frozen COMPLETE/verdict) |
| R6 | Meta: 60 action is moratorium (always pass if 60 verdict file says STRUCTURALLY_UNDERWATER) |

All six pass → **`MAP_LOCKED`**.  
Any fail → **`MAP_INCONSISTENT`** (artifact drift — investigate, do not invent new rules).

---

## Explicit non-goals

- No new entries, exits, or P&L optimization  
- No “skip days using future first-passage outcome” (lookahead)  
- No Frame B payoff hunt in this folder  
- No Strategy 62 event costume  

---

## Outputs

| Path | Role |
| --- | --- |
| `results/rule_checks.json` | Per-rule pass/fail + numbers |
| `results/verdict.json` | MAP_LOCKED / MAP_INCONSISTENT |
| `results/REFUSAL_MAP.md` | Human-readable atlas |
| `results/audit.json` | Freeze checks |

---

## Decision record

**Frame C chosen** after Strategy 60. The interesting next product is a **locked refusal atlas**, not another mechanism.
