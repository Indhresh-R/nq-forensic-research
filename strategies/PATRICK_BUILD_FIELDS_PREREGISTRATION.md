# Patrick build-fields — Preregistration (P1 / P2 / P6a / P7)

**Status:** FROZEN BEFORE ANY FIELD BUILD OR OUTCOME.  
**Namespace (when coded later):** `strategies/62_patrick_build_fields/` *(folder not required until build go-ahead)*  
**Parent charter:** `strategies/CHARTER_PATRICK_INFO_DATA.md`  
**Order:** **Build fields first.** Continuation vs fade is **out of scope** until P1–P7 exist and can be inspected.

---

## What this prereg is

Materialize **information fields only**:

| ID | Field |
| --- | --- |
| P1 | Full-Globex volume profile (session) |
| P2 | Full-Globex 30m TPO letters (same window) |
| P6a | Big **single** print flag (causal trailing quantile) |
| P7 | P6a prints joined to **prior-session** P1 levels (**causal**) |

No trade, no first-passage, no continuation/fade hypothesis, no P&L, no paid DOM.

---

## What this prereg is not

- Not a Patrick “strategy”  
- Not Strategy 47 POC-contact reopen  
- Not Fabio / Imre  
- Not P6b burst/sweep  
- Not P8 aggressor (unless a later, separate validation prereg)  
- Not a place to choose continue vs fade from priors  

---

## Session clock (inherited, immutable)

| Item | Value |
| --- | --- |
| Timezone | America/New_York |
| Session | **18:00 → 17:00** next calendar day (Globex), matching `volume_profile/CONFIG.yaml` / `common/nq_session.py` |
| Roll | Existing instrument_id / gap rules from VP stack |

**Hard rule:** P1, P2, and P6a lookbacks all respect this session. No RTH-only TPO on a Globex VP.

---

## P1 — Volume profile (build spec)

Per completed Globex session (and optionally causal intra-session cumulative profile if build code supports it — **session-complete profile is the required minimum artifact**):

| Output | Rule |
| --- | --- |
| Tick size | 0.25 |
| Value area | 70% (`value_area_pct: 0.70` from VP CONFIG) |
| POC tie-break | lower price (CONFIG) |
| VA tie-break | expand lower on equal volume (CONFIG) |
| Levels exported | POC, VAH, VAL, plus HVN/LVN if already defined in VP codebase — **reuse, do not reinvent** |

Do not change 47’s closed *mechanism* claims; only reuse session/profile **construction**.

---

## P2 — TPO (build spec)

| Item | Freeze |
| --- | --- |
| Window | Same Globex session as P1 |
| Period length | **30 minutes** |
| Lettering | Sequential periods from session open (18:00); overnight included |
| Price | Tick grid 0.25; a period “prints” a letter at each price traded (or 1m bar H–L coverage — **pick one in code go-ahead and document**; default preference: **trades** if available, else 1m OHLC range fill) |

Export per session: period table, TPO count per price, and:

| Field name | Definition |
| --- | --- |
| `globex_open_60m_high` / `globex_open_60m_low` | High/low of the **first two** 30m periods after Globex open (18:00–19:00 ET) |

**Do not name this `IB`.** Classical AMT / Patrick “IB” means RTH first hour (09:30–10:30). That object is **`rth_ib_*` — not built in this prereg.** Using “IB” here would silently mean the wrong hour in later P4/P5 predicates.

Poor high/low / single-print AMT predicates: **not required in this build**; may be added in a later sourced amendment.


---

## P6a — Big single print `(q, N)` (fully specified)

### Frozen primary

| Symbol | Value | Meaning |
| --- | --- | --- |
| `q` | **0.99** | Top **1%** of trailing print sizes (“block-like,” rarer than top 2%) |
| `N` | **5000** | Trailing window = **last 5000 prints** |
| Window unit | **Prints**, not sessions | Adapts to slow volume growth **and** intraday participation shifts |
| Session boundary | **Reset at Globex session roll** | No bleed-through from prior session |
| Bleed-through | **Forbidden** | At/after 18:00 roll, trailing buffer starts empty |

### Causal quantile (no IS freeze step)

At each print `i` within a session, let `S` = sizes of the up-to-`N` **prior** prints in the **same** session (excluding `i`).

- If `|S| < N_min`, **P6a = False** (undefined / not big) — see warmup  
- Else threshold `t = quantile(S, q)` with `q=0.99`  
- `P6a_i = 1` iff `size_i ≥ t`

**Round-lot clustering (known failure mode):** Futures sizes bunch at 1, 2, 5, 10, 20, 50, 100, …. If `t` lands on a round lot, `size ≥ t` can flag **far more than ~1%** of prints (everything tied at `t`). That would turn P6a from “rare block” into “common institutional round lot” — a different concept.

**Do not retune `(q, N)` to “fix” ties.** Instead, `build_audit.json` **must** report (report-only diagnostics):

| Diagnostic | Definition |
| --- | --- |
| `tie_mass_at_threshold` | Among P6a flags with valid warmup: fraction with `size == t` vs `size > t` (overall + per session) |
| `flag_rate_by_session` | Distribution across sessions of `(n_p6a / n_valid_prints)` — mean, p10, p50, p90, max — **not** only a global average |
| `threshold_value_histogram` | How often `t` equals common round lots |

These do not change the frozen rule. They make the ~1% “plausible rate” check actually diagnostic.

**Why no IS/Val/OOS threshold freeze:** the rule is **causal at every timestamp** (trailing past only). It is not a global IS-frozen tercile (contrast Strategy 52-style freezes). State this explicitly in any report.

### Warmup

| Symbol | Value |
| --- | --- |
| `N_min` | **500** |

Until 500 prior prints exist in-session, P6a is false/undefined (export a `p6a_valid` flag).

### Robustness only (not primary; not for choosing)

After primary fields exist, **report-only** sensitivity (no promotion, no redefinition of primary):

| Param | Robustness values |
| --- | --- |
| `q` | 0.98 |
| `N` | 2000, 10000 |

Do **not** pick the “best” robustness cell. Primary remains `(q=0.99, N=5000)`.

### Rejected alternatives

| Alternative | Why rejected |
| --- | --- |
| Fixed lots | Non-stationary; era retune risk |
| Trailing N **sessions** | Blind to intraday regime; disagrees with print-time participation |
| Trailing N prints **with bleed** across 18:00 | Breaks same-auction discipline as P1/P2 |
| `q=0.98` as primary | Garden-variety large vs Patrick “big”; keep as robustness |

---

## P7 — Big prints at VP levels (build spec)

### Level timing — FROZEN (option b)

**Primary P7 uses the prior Globex session’s completed profile levels — causal.**

| Print time (session `S`) | Levels used |
| --- | --- |
| Any print in session `S` | POC / VAH / VAL (and HVN/LVN if exported) from **completed** profile of session **`S_prev`** (prior Globex session under the same roll rules) |

| Rejected default | Why |
| --- | --- |
| Same-session **completed** P1 levels | Retrospective: a 10:00 print scored vs a POC finalized at session end includes **future volume** → look-ahead; cannot feed later first-passage/trade without rebuild |

Same-session completed join may exist only as an optional **descriptive** artifact named e.g. `p7_descriptive_same_session_*` and must be labeled **non-causal / not for hypothesis preregs**. It is **not** the primary P7 output.

Intra-session cumulative “profile so far” is **not** required in this build (deferred). Prior-session levels match the causal pattern already used in Strategy 47’s prior-day POC methodology — reuse that discipline; do **not** reopen 47’s closed mechanism verdict.

### Join rules

| Item | Freeze |
| --- | --- |
| Level set | Prior session POC, VAH, VAL (minimum); HVN/LVN if exported |
| Missing prior | If `S_prev` profile missing/incomplete → P7 rows null / excluded; count in audit |
| Proximity | Within **1 tick** (0.25), matching VP CONFIG `interaction_tolerance_ticks: 1` (or document reused helper) |
| Output | Per P6a print in `S`: nearest prior level id + distance ticks; per-session aggregates of counts near each prior level |

**Unsigned only** (size participation). No aggressor side → no P8 → G1 MBO check **not** required for this prereg’s success.


---

## Build success criteria (information only)

| Check | Pass |
| --- | --- |
| P1 | Profiles build for eligible sessions; POC/VA finite |
| P2 | Letter periods cover full Globex; `globex_open_60m_*` present; **no field named IB** |
| P6a | Global flag rate order-of-magnitude ~1% **and** audit includes tie-mass + per-session rate distribution |
| P7 | Primary join uses **prior-session** levels only; non-empty on a non-trivial fraction of sessions with valid `S_prev` |
| Audit | Shared Globex clock; no P6a bleed; `(q,N)=(0.99,5000)`; P7 causality flag = prior-session |

Fail = engineering/data issue. **Not** an edge kill. Round-lot tie-mass does not auto-fail the build; it must be **visible** in the report for human judgment before any hypothesis prereg.


---

## Explicitly deferred

| Item | When |
| --- | --- |
| Continuation vs fade hypothesis | **After** fields exist and can be looked at |
| P6b burst/sweep | Separate prereg |
| P8/P9 + MBO proxy agreement | Only if a later claim needs side |
| First-passage / trade / cost | Obey R1–R6; separate prereg |
| Paid DOM | Not for Patrick |

---

## Outputs (when executed later)

| Path | Role |
| --- | --- |
| `results/p1_session_profiles.parquet` | Session VP levels |
| `results/p2_tpo_periods.parquet` | TPO letters / counts |
| `results/p6a_print_flags.parquet` | Print-level P6a + threshold |
| `results/p7_prints_at_prior_levels.parquet` | **Primary causal** P7 |
| `results/p7_descriptive_same_session.parquet` | Optional non-causal only (if built) |
| `results/build_audit.json` | Clock / (q,N) / flag rates / **tie mass** / per-session rate dist / P7 prior coverage |
| `results/BUILD_FIELDS_REPORT.md` | Human report |

---

## Decision record

| Choice | Value |
| --- | --- |
| Order | Build-fields **before** continuation-vs-fade |
| `q` | **0.99** (primary); 0.98 robustness-only |
| `N` | **5000 prints** (primary); 2000/10000 robustness-only |
| Boundary | **Reset at Globex roll**; no bleed-through |
| Causal P6a | Trailing quantile → **no IS threshold freeze step** |
| **P7 levels** | **Prior session completed profile only** (primary); same-session completed = descriptive-only if present |
| Open-hour range | Field name **`globex_open_60m_*`**, not `IB` |
| Round lots | Audit tie-mass + per-session flag-rate dist; do not retune `(q,N)` |

`(q, N)` and P7 causality are fully specified. Buildable without a throwaway P7.

