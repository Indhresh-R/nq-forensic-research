# Patrick stack — Information ↔ Data matrix

**Status:** CHARTER — definitions for P1/P2/P6 **FROZEN** below. No strategy code. No P&L. No paid-data purchase.  
**Date:** 2026-09-23 (rev: definition freeze)  
**Parent constraints:** `strategies/BRANCH_CLOSED_USE_ATLAS.md` (R1–R6); do not reopen 47’s closed POC-contact claim as this charter.

---

## Attribution (frozen for this doc)

| Trader | Stack |
| --- | --- |
| **Patrick** | Volume profile + big trades + TPO |
| Fabio | 40-range + NQ effort + ultra delta *(out of scope here)* |
| Imre | VP + big trades + deep DOM *(out of scope here)* |

**Principle:** Tools matter less than **information required to execute**.  
Spend money on feeds only after proving we can / cannot reproduce that information with data we already have.

**Not success** = matching Bookmap colors.  
**Success for this phase** = observable fields for location × auction structure × participation.

---

## Why Patrick uses these tools (information intent)

| Tool on the screen | Information he is trying to see |
| --- | --- |
| **Volume profile** | Where the market has **accepted value** (HVN/POC/VA) vs **rejected / thin** areas (LVN) |
| **TPO** | **How** the auction built over time (balance vs trend day, poor highs/lows, single prints, IB vs later excess) |
| **Big trades** | Whether **size** agrees with the move at that location (participation / conviction), not just price wick |

```text
LOCATION (VP)  ×  AUCTION STRUCTURE (TPO)  ×  PARTICIPATION (big prints)
        →
decision context for continue vs fade vs stand aside
```

Continuation vs fade is **not** chosen in this charter.

---

## Gaps named before definition freeze

### G1 — Aggressor proxy quality (P8/P9) is necessary if direction matters

Tick-rule / Lee-Ready-style side inference on futures tape commonly misclassifies on the order of **~10–20%** of prints, and error rates rise in fast markets — exactly when “big trades” cluster.

If P7 later needs **directional** agreement (buyers vs sellers at a VP level), a noisy trades-only side can manufacture or erase effects **before** any first-passage test.

**Rule:** If any later Patrick prereg uses aggressor direction of big prints, a prior **proxy-vs-MBO agreement check** on `data/mbo_full_state_50/` is **mandatory**, falsifiable, and **not optional**.  
That check only answers: “Is the trades-side proxy trustworthy enough to use?” — it does **not** test Patrick’s edge.

Unsigned / size-only P6–P7 (participation without side) can proceed without P8.

### G2 — ~50 MBO sessions = validation-only, never discovery

| Allowed use of `mbo_full_state_50` | Forbidden use |
| --- | --- |
| Proxy vs ground-truth agreement (G1) | Any **promotable** mechanism / edge verdict |
| “Is this field buildable?” smoke tests | Ranking thresholds, shopping filters, OOS claims |

Stating this explicitly so a future run does not treat a 50-session MBO cross-check as promotable evidence (lesson adjacent to Strategy 44 H02 risk).

---

## Local data (relevant)

| Asset | Where | Role |
| --- | --- | --- |
| Trades → VP | `volume_profile/` + trades store | P1 primary |
| Session convention | `volume_profile/CONFIG.yaml` + `common/nq_session.py` | **18:00 → 17:00** ET Globex roll |
| Bars / time grid | Strategy 52 panel / continuous NQ | TPO scaffolding |
| MBO (~50 sessions) | `data/mbo_full_state_50/` | **Validation-only** (G1/G2) |
| Paid deep DOM | Not purchased for Patrick | Imre track only |

---

## Frozen definitions (P1 / P2 / P6)

### P1 — VP window

**FROZEN: full Globex session, 18:00 open → 17:00 close ET (instrument roll per existing VP / `nq_session` convention).**

| Rejected alternative | Why |
| --- | --- |
| RTH-only 09:30–16:00 | Classical AMT classroom default, but **second** session law vs 47 / `nq_session` → silent join drift |
| Multi-day composite as *base* window | Useful later for “prior session value”; **second** question, not base P1 |

Rationale: reuse what is already frozen in-repo; R1–R6 exist partly to stop convention drift across studies.

### P2 — TPO period length

**FROZEN: 30-minute letters spanning the same full Globex window as P1** (overnight + RTH; ~40+ letters possible per session — accepted).

| Rejected alternative | Why |
| --- | --- |
| Classic RTH-only ~13–14 letters | Would describe a **different auction** than a full-Globex VP |
| Session-anchored 30m from RTH open only | Same mismatch if P1 = full Globex |

**Hard consistency rule:** `P2.window == P1.window`.  
“How the auction built to this value” is invalid if VP and TPO cover different clocks.

Departure from retail “classic TPO” is intentional and documented.

### P6 — Big trade threshold

**FROZEN in build-fields prereg:** `strategies/PATRICK_BUILD_FIELDS_PREREGISTRATION.md`

| Symbol | Primary |
| --- | --- |
| `q` | **0.99** |
| `N` | **5000 prints** (trailing), **reset at Globex roll**, no bleed |
| Form | Single print (P6a); causal trailing quantile → **no IS freeze step** |

Supersedes earlier “N sessions” placeholder in this charter.


### P6 fork — single print vs burst (named and decided)

These are different phenomena:

| ID | Meaning | Patrick screen default |
| --- | --- | --- |
| **P6a** | One print ≥ quantile threshold | **PRIMARY — FROZEN for first build** |
| **P6b** | Burst / sweep: cluster of same-side (or unsigned) size in a short window that no single print flags | **DEFERRED** — separate information channel; not in first Patrick build |

**Decision:** First information build uses **P6a only**.  
P6b requires its own frozen burst definition later; mixing it into P6a would change build logic and invite dual hypotheses under one label.

---

## Information ↔ data matrix (updated)

| # | Information | Observable now? | Build from | MBO role | Paid DOM? |
| --- | ---: | --- | --- | --- | ---: |
| P1 | Full-Globex VP (POC/VA/HVN/LVN) | **YES** | Trades @ frozen session | No | No |
| P2 | Full-Globex 30m TPO letters | **YES** | Time × price on same window | No | No |
| P3–P5 | Balance/trend, poor H/L, IB vs later | **YES** | From P2 (+ rules sourced later) | No | No |
| P6a | Big **single** print (rolling quantile) | **YES** | Trades sizes | No | No |
| P6b | Burst / sweep | Deferred | — | — | — |
| P7 | P6a prints at **prior-session** VP levels (causal) | **YES** | Join P6a × prior P1 | No | No |
| P8 | Aggressor side of P6a | **PARTIAL** | Trades proxy; MBO truth | **Mandatory validation if used** (G1/G2) | No |
| P9 | CVD (optional) | **PARTIAL** | Trades / MBO | Validation-only sample | No |
| P10 | Deep DOM | **NO** (Patrick) | — | — | Imre only |

### Spend rule (unchanged intent)

```text
Prove P1–P7 (P6a) on existing trades
  → if direction needed, run G1 proxy check on 50 MBO (validation-only)
  → if information dead: do not buy DOM/UI to revive it
  → if live: scale history/latency later — not vendor cosmetics
```

---

## Explicit non-goals

- No Fabio / Imre pipelines in this charter  
- No purchase recommendation  
- No Strategy number / backtest / P&L  
- No reopen of Strategy 47 POC-contact mechanism  
- No treating 50-session MBO results as promotable discovery  
- No P6b burst logic in the first build  
- No RTH-TPO + Globex-VP mismatch  

---

## Next talk / build steps

1. **Done:** `(q, N)` specified  
2. **Done:** fields built — `62_patrick_build_fields/`  
3. **Next:** first-passage prereg frozen — `PATRICK_STRICT_VA_FIRST_PASSAGE_PREREGISTRATION.md` (run only on go-ahead)


---

## Decision record

- Patrick first: information mostly on trades.  
- VP/TPO window aligned to existing Globex 18:00 roll.  
- Big trades = rolling quantile single prints (P6a).  
- G1/G2 named so proxy noise and tiny MBO samples cannot silently become “evidence.”
