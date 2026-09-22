# Research ledger — Strategies 52 → 58 (frozen)

**Purpose:** Close market-state routing and the Strategy 55–58 price-event family search; constrain what may open next.

**Date context:** 2026-09-22 / 2026-09-23.

---

## Verdict on the original thesis

> **Market state as a routing variable for generic strategy families has not demonstrated an edge.**

State remains useful as a **descriptive map / context**, not as the source of a trade by itself.

---

## Evidence stack (do not reopen)

| Layer | Strategy | Result |
| --- | --- | --- |
| State census | 52 Step 0 | Persistent, measurable states exist |
| Transition / destination mechanism | 52 Steps 1–8 | Exp→Normal destination asymmetry under controls; Step 9 trade **KILL** |
| Broad state → generic family | 53 | All 4 cells **REJECTED** |
| Transition → path vs stay | 54 | No clean candidate; activity hits **definitional** |
| Event A | 55 | Destination yes → trade **KILL_AFTER_TRADE** |
| Event B | 56 | Destination yes → trade **KILL_AFTER_TRADE** |
| Event B path | 57 | **PATH_KILL** (touches ≠ directional close path; MFE ≈ MAE) |
| Event C | 58 | **KILL** at destination Step 1 (Δ wrong sign) |

---

## Closed: Event family search (55–58)

**Status: STOP.** Do not invent Event D from the Strategy 55 menu. Do not retune A/B/C. Do not horizon-shop.

| Project | What happened |
| --- | --- |
| 55 — Displacement → retracement | Destination asymmetry → path/trade failed |
| 56 — Range break → failed return | Destination asymmetry → trade failed |
| 57 — Event B timing | Destination probability ≠ tradable drift |
| 58 — Extreme excursion → rejection | **Destination hypothesis failed immediately** (anchor 59.2% vs extreme 62.0%, Δ = −2.8 pp) |

Event C: no path analysis, no trade, no retuning — correct kill.

### Hard conclusion from 55–58

> **Finding statistically stable destination relationships is relatively easy; finding a destination relationship with a favorable first-passage path and acceptable adverse excursion is the real bottleneck.**

Also (from 57): high eventual destination probability ≠ favorable holding path.

---

## What died

```text
STATE → GENERIC STRATEGY
TRANSITION → MORE/LESS MOVEMENT THAN STAYING
ACTIVITY TRANSITIONS AS PATH “EDGE”
RESCUING 52–54 WITH MORE FILTERS
DESTINATION-FIRST EVENT MENU (Families 1–4) AS THE SEARCH FORM
EVENT WITH DESTINATION ASYMMETRY → ASSUME HOLDABLE PATH
HORIZON SHOPPING AFTER A FAILED FIXED HOLD
DRILLING FURTHER INTO EVENT A / B / C
AUTOMATIC EVENT D
```

---

## Next research frame (after 52–58)

Do **not** start from another arbitrary price event and hope destination + path appear later.

Start from a **specific executable mechanism/path**, with **target and adverse barrier defined together** from the beginning:

```text
EVENT
  ↓
TARGET + ADVERSE BARRIER
  ↓
Which is reached first?
  ↓
How much MAE before target?
  ↓
How long?
  ↓
ONE trade
```

**Project size (hard):** one mechanism → first-passage (target vs adverse) → MAE/time diagnostics → **one** execution if it survives.

Forbidden until a new prereg names a concrete mechanism:

- Reopening 52–58 closed branches
- Menu-style Event D/E/F without a first-passage design
- CVD/VWAP/ATR/TOD as post-hoc filters
- Horizon P&L shopping
- Combining killed events

Market state may appear only as **context**, not as the signal.

---

## Next project status

Strategy 59 (ORB first-passage): **KILL** at Step 1 (adverse before target; Δ_fp ≈ −21 pp IS).  
See `59_orb_first_passage/COMPLETE.md`.

---

## Frozen artifact index

| Strategy | Status | Key report |
| --- | --- | --- |
| 52 | Mechanism complete; Step 9 **KILL** | `52_market_state_census/` |
| 53 | **COMPLETE / FROZEN** all REJECTED | `53_regime_strategy_screen/COMPLETE.md` |
| 54 | **COMPLETE / FROZEN** no clean path candidate | `54_transition_path_screen/COMPLETE.md` |
| 55 | Event A **KILL_AFTER_TRADE** | `55_price_path_events/EVENT_A_COMPLETE.md` |
| 56 | Event B **KILL_AFTER_TRADE** | `56_range_break_failed_return/EVENT_B_COMPLETE.md` |
| 57 | Event B path **PATH_KILL** | `57_event_b_path_timing/COMPLETE.md` |
| 58 | Event C **KILL** (destination; path not run) | `58_extreme_rejection_path/EVENT_C_COMPLETE.md` |
| 59 | ORB first-passage **KILL** (adverse before target) | `59_orb_first_passage/COMPLETE.md` |
