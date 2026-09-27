# Step 2 Preregistration — Transition-event mechanics

**Status:** FROZEN BEFORE PATH ANALYSIS.  
**Parent:** Strategy 52 Steps 0–1 (labels, cells, episode onsets frozen).  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Mechanism description only. **Not** a trading strategy.

No entries, exits, stops, targets, signed trade P&L, win rates, or parameter optimization.

---

## Question

Does the **transition event** contain path-geometry information that the **persistent state label** (Step 1) does not?

Primary contrasts:

1. **A → NORMAL** vs **B → NORMAL** (compression exits)
2. **C → NORMAL** vs **D → NORMAL** (expansion exits)

Hypothesis form (unsigned):

> Does the transition from A→NORMAL have a measurably different subsequent path geometry from B→NORMAL?

Not: “A→NORMAL is bullish/bearish.”

---

## Event families

| Family | Origin cells | Transition |
| --- | --- | --- |
| CompExit | A, B | first `COMPRESSION → NORMAL_RANGE` |
| ExpExit | C, D | first `EXPANSION → NORMAL_RANGE` |

Origin cells are Step 1 four-cell labels (IS-frozen terciles). No re-thresholding.

---

## Event definition (causal)

Start from each Step 1 **episode onset** at panel index `i0` with cell ∈ {A,B,C,D}.

Scan forward bars `i = i0+1, i0+2, …` while:

1. Same `session_date`
2. Contiguous `ny_min` (+1 each bar)
3. Same `segment_id`

**Abort without an event** if, before hitting NORMAL:

- Origin range family is left for the **opposite** extreme  
  (A/B: hit `EXPANSION`; C/D: hit `COMPRESSION`), or
- Four-cell label switches to a **different** A/B/C/D cell  
  (e.g. A→B while still compressed)

**Event** occurs at the first bar `te` with `range_state == NORMAL_RANGE` under the scan above.

Important freezes:

- At most **one** event per episode onset (first qualifying transition only).
- The event timestamp is the **first NORMAL bar**, not the original onset.
- Event membership (A vs B, or C vs D) is the **origin cell at `i0`**, not labels after `te`.
- Do **not** condition event inclusion on anything that happens after `te`.

Episodes that never print a qualifying NORMAL under the abort rules are counted as **censored** (no event) and reported in funnel tables only.

---

## Forward path (after the transition)

Horizons **H ∈ {5, 15, 30, 60}** minutes.

Reference bar is `te` (event). Close `C_e = Close[te]`. ATR scale = `ATR_30[te]`.

Path bars: **`te+1 … te+H`** (strictly subsequent).

Horizon validity matches Step 1 (same session, contiguous minutes, same segment). Invalid horizons excluded.

---

## Frozen metrics (unsigned / two-sided)

| Metric | Definition |
| --- | --- |
| `wait_to_event` | `te − i0` in minutes (onset → first NORMAL) |
| `abs_net_atr` | `|Close[te+H]−C_e| / ATR_30[te]` |
| `max_up_atr` | `(max High[path] − C_e) / ATR_30[te]` |
| `max_down_atr` | `(C_e − min Low[path]) / ATR_30[te]` |
| `max_range_atr` | `(max High − min Low) / ATR_30[te]` |
| `er_forward` | net path efficiency over `te…te+H` (same construction as Step 1) |
| `still_normal` | terminal range == NORMAL |
| `returned_to_origin_range` | any path bar returns to origin range (COMP for CompExit; EXP for ExpExit) |
| `reached_opposite_range` | any path bar reaches opposite extreme (EXP for CompExit; COMP for ExpExit) |
| `time_to_leave_normal` | minutes to first non-NORMAL in path; NaN if never |
| `time_to_origin_range` | minutes to first return to origin range; NaN if never |
| `time_to_opposite_range` | minutes to first opposite extreme; NaN if never |
| `terminal_dir_high` | terminal directionality == HIGH |
| `terminal_dir_low` | terminal directionality == LOW |
| `path_dir_high_share` | fraction of path bars with HIGH directionality |
| `path_dir_low_share` | fraction of path bars with LOW directionality |

No long/short side. No P&L.

---

## Contrasts

| Contrast | Events |
| --- | --- |
| CompExit A vs B | origin A vs origin B, both with Comp→Normal event |
| ExpExit C vs D | origin C vs origin D, both with Exp→Normal event |

Report by horizon; optionally by IS / Validation / OOS without retuning.

---

## Forbidden

- Entries, exits, stops, targets, friction
- Selecting events using post-`te` information
- Multiple transitions from one episode
- Calling either transition bullish/bearish or an edge

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step2_events.parquet` | Qualifying transition events |
| `results/step2_funnel.json` | Onsets → events / censored reasons |
| `results/step2_path_metrics.parquet` | Event × horizon metrics |
| `results/step2_contrasts.json` | A vs B, C vs D summaries |
| `results/step2_audit.json` | Scope audit |
| `STEP2_TRANSITION_EVENTS.md` | Report |

---

## Verdict format

**STEP 2 VERDICT** — whether transition events separate path geometry where persistent labels did not — then **NEXT RESEARCH QUESTION** (still not a trading rule).
