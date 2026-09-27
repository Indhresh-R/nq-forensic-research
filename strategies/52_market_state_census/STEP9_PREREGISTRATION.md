# Step 9 Preregistration — One simple executable hypothesis

**Status:** FROZEN BEFORE ANY P&L COMPUTATION.  
**Parent:** Strategy 52 Steps 0–8 (`PATH_FEASIBLE` / `GO_TO_STEP9`).  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Single executable hypothesis test. Not a research tree. Not parameter search.

---

## Research question

> Can the observed low-transition-ER ExpExit destination asymmetry be converted into **positive net expectancy** under one simple, fixed entry/exit rule and realistic NQ costs?

If **no** on any of IS / Validation / OOS → **KILL**, regardless of mechanism interest.

---

## Why this hypothesis (frozen motivation)

Steps 2–8 established an associative destination asymmetry for low-`ER_60[te]` ExpExit C vs D, with early path scale (median first destination ~6m; median 15m `hl_range` ~13 pts vs 1.0 pt RT cost).

Signed net displacement at short horizons is near zero for both cells — the asymmetry is **not** an unconditional long/short drift. The simplest price-mapped rule that uses only pre-`te` geometry already measured in Steps 4–5 is:

> **Fade toward the pre-event origin midpoint** after a low-ER ExpExit from cell **D** (the cell whose competing path more often returns to origin range first).

Cell **C** is evaluated with the **identical** rule as a **control arm only** (not a second hypothesis, not used for promotion).

---

## Frozen population

Identical to Step 7 / Step 8:

- ExpExit; first EXPANSION → NORMAL at `te`
- `te_er_60 ≤` Step 6 IS q33 (not re-fit)
- Event ids from `results/step7_population.parquet`

**Primary arm (promotion):** `origin_cell == D_EXP_LOW_DIR`  
**Control arm (diagnostic only):** `origin_cell == C_EXP_HIGH_DIR` with the same side/exit rule

No additional filters (no TOD, ATR, duration, S-bin, volume, EMA, VWAP, CVD, SMT).

---

## Single hypothesis H1 (primary arm = D)

| Element | Frozen rule |
| --- | --- |
| Signal bar | `te` (event bar close completes the Exp→NORMAL label) |
| Entry | Open of bar `te+1` (next 1-minute bar). Skip if `te+1` not contiguous same session/segment. |
| Side | `side = +1` if `close[te] < P_mid`; `side = −1` if `close[te] > P_mid`; **skip** if `close[te] == P_mid` or envelope invalid (`R ≤ 0`) |
| Envelope | `P_high`, `P_low`, `P_mid` from bars `[i0, te)` exactly as Step 5 |
| Exit | Close of bar `te+15` (fixed **15-minute** horizon — Step 8 peak destination separation). If path breaks earlier, flatten at last contiguous bar close. |
| Stops / targets | **None** (pure horizon drift). No stop/target grid. |
| Cost | **1.0 NQ point** round-trip (mid scenario). Subtracted once per trade. |
| Overlap | Each event is one trade; overlapping events allowed as separate ledger rows (no portfolio netting). |

Gross P&L (points) = `side × (exit_price − entry_price)`  
Net P&L = gross − 1.0

---

## Forbidden

- Any second hypothesis competing for promotion
- Stop/target/horizon/side optimization or grid search
- Adding filters after seeing P&L
- Different exit rules for C vs D
- EMA / VWAP / CVD / SMT / multi-target / time-of-day search
- Re-cutting low-ER threshold
- Calling mechanism findings a profitable strategy without this gate

---

## Promotion / kill gate

Let `E_net(split)` = mean net P&L (points) on the **primary D arm** for that chronological split.

| Verdict | Rule |
| --- | --- |
| **PROMOTE_CANDIDATE** | `E_net(IS) > 0` **and** `E_net(Validation) > 0` **and** `E_net(OOS) > 0`, each split with `n_trades ≥ 200` |
| **KILL** | Any of the above fails |

Control-arm C results are reported but **do not** change the verdict.

No Sharpe/PF promotion requirement in this step (simple expectancy gate only). Prop-risk evaluation is out of scope unless PROMOTE_CANDIDATE.

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step9_trades.parquet` | Trade ledger |
| `results/step9_summary.csv` | Split × arm expectancy table |
| `results/step9_verdict.json` | PROMOTE_CANDIDATE / KILL |
| `results/step9_audit.json` | Leakage / freeze audit |
| `STEP9_EXECUTABLE_HYPOTHESIS.md` | Report |

---

## Verdict format

**STEP 9 VERDICT** = `PROMOTE_CANDIDATE` or `KILL`, then explicit next action (prop-risk eval vs stop).
