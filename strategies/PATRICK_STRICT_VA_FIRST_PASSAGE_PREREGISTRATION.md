# Patrick — Strict print at prior VA: first-passage (fade vs acceptance)

**Status:** FROZEN BEFORE ANY PATH / OUTCOME COMPUTATION. **v2 — amends v1 pre-code.**  
**Namespace (when coded):** `strategies/63_patrick_strict_va_first_passage/`  
**Parents:**  
- `PATRICK_BUILD_FIELDS_PREREGISTRATION.md`  
- `62_patrick_build_fields/P6A_SUBGROUP_DECISION.md` (**B confirmed**)  
- `BRANCH_CLOSED_USE_ATLAS.md` (R1–R6)  
- `CHARTER_PATRICK_INFO_DATA.md`

**Amendment note (v1 → v2):** Three fixes folded in before any code was written — no results existed under v1. See "Changelog" at bottom.

---

## Confirmed upstream

| Item | Freeze |
| --- | --- |
| P6a subgroup | **Strict-only primary** (`size > threshold`); tie = robustness only |
| `(q, N)` | Unchanged (0.99, 5000 prints, roll reset) |
| Levels | Prior Globex session completed POC/VAH/VAL |
| Expected N (order of magnitude) | **~1171** strict P7 joins / **~79** sessions on `trades_24h_6m`; VAH+VAL-only subset smaller (~565 strict in build inspection) — **state actual N at run from artifacts** |

---

## Scope (honest half-stack)

```text
THIS PREREG = prior-session VP levels × strict big print (P1 + P6a/P7)
TPO (P2–P5 balance/trend/poor structure) = DEFERRED
```

This tests **VP + size**, not the full Patrick stack (VP × TPO × size).  
Full-stack confirmation is a **later** layer, not smuggled in by renaming this study "Patrick complete."

---

## What this is / is not

| Is | Is not |
| --- | --- |
| Fresh first-passage question on strict prints at prior VA | Import of Strategy 47 fade lean as a prior |
| Target + adverse defined **together** | Destination% then invent barriers |
| Single descriptive fold | IS/Val/OOS promotable verdict |
| Path / which-barrier-first | Fixed 15m hold (R3/R60) |
| Unsigned size participation | Aggressor side / P8 |

---

## Research question (no directional prior)

> After a **strict** P6a print within 1 tick of a **prior-session VAH or VAL**, which barrier is reached first — **into value** or **away from value** — and is that path survivable (adverse excursion vs. own resolution) under a co-defined first-passage design?

**No assumption** that fade wins. No assumption that acceptance wins.  
Strategy 47's geometry-only lean is **explicitly not imported**.

---

## Event definition (primary)

### Inclusion

From `p7_prints_at_prior_levels.parquet` (or equivalent rebuild):

1. `size > threshold` (**strict**)  
2. `level_name ∈ {prev_vah, prev_val}`  
3. Prior session complete; prior levels finite  
4. Print inside current Globex session window  

### Primary vs secondary level

| Level | Role |
| --- | --- |
| **prev_vah / prev_val** | **PRIMARY** — into-value vs away is well-defined without trade side |
| **prev_poc** | **SECONDARY / descriptive only** in this prereg (unsigned; fade/accept at center is ambiguous without aggressor or approach rule) |

### Dedup (frozen)

If multiple strict prints hit the same `(session_date, level_name)` within **5 minutes**, keep the **first** only (onset). Report dropped count in audit.

---

## Barriers — defined together (first-passage)

Let `L` = prior level price (VAH or VAL).  
Let `W = prior value_area_width` (points) from prior profile; if missing, `W = |prev_vah − prev_val|`.  
Require `W > 0`.

### Into value (toward prior POC)

| Event at | Into-value barrier |
| --- | --- |
| `prev_vah` | Touch **prev_poc** — operational: `low ≤ poc` (or `\|price − poc\| ≤ 1 tick`) |
| `prev_val` | Touch **prev_poc** — operational: `high ≥ poc` |

### Away from value (acceptance beyond level)

| Event at | Away barrier |
| --- | --- |
| `prev_vah` | Touch `L + max(0.25 × W, 4 × tick)` i.e. at least **1.0 point** beyond VAH |
| `prev_val` | Touch `L − max(0.25 × W, 4 × tick)` |

`tick = 0.25`.

### Barrier-distance diagnostic (mandatory, non-tunable)

The into-barrier (distance to POC) and the away-barrier (fixed `0.25×W` or `1pt` floor) are **not symmetric distances**. A raw `Δ = p_into − p_away` conflates "fade pressure" with "POC happened to be close this session." This must be surfaced, not just computed on:

| Field | Definition |
| --- | --- |
| `dist_into` | `\|event_price − prev_poc\|` at event time (points) |
| `dist_away` | `max(0.25 × W, 4 × tick)` at event time (points) |
| `dist_ratio` | `dist_into / dist_away` |

**Required reporting (not a promote gate, not a retune):**

- Report `dist_into`, `dist_away`, `dist_ratio` distributions (median, IQR) alongside `p_into`/`p_away`.  
- Report `Δ` **stratified into terciles of `dist_ratio`** (computed on this sample, described as descriptive strata — not an IS-frozen threshold, since there is no promotion to protect).  
- The main-text interpretation of `Δ` must reference `dist_ratio` explicitly. A headline "`p_into` > `p_away`" claim without the distance context is **not permitted** in the report.

This is a required diagnostic column set, same class as the P6a tie-mass check — it does not change the barrier definitions, targets, `H_cap`, or `(q,N)`.

### Horizon / resolution

| Item | Freeze |
| --- | --- |
| `H_cap` | **60 minutes** of contiguous session time after event print, or Globex session end if sooner |
| **Resolution granularity** | **Trade-level prints** (not 1-minute OHLC bars) — same precision standard as the P6a build; a level/barrier is touched at the first qualifying print, not the first bar |
| Same-print/same-timestamp both | **Away wins** (conservative vs "fade worked") — mirror 59's adverse-wins conservatism, flipped to not favor fade |
| Unresolved | Neither barrier by `H_cap` |

**Audit requirement:** report the realized rate of `same_print_both` (or same-timestamp-both) ties in `audit.json`. At trade-level resolution this is expected to be rare; if it is not rare, that itself is reportable, not silently absorbed by the tie-rule.

### Path diagnostics (not optional add-ons)

On each resolved event:

- `outcome ∈ {into_first, away_first, unresolved}`  
- `bars_or_seconds_to_resolve`  
- **`adverse_excursion_vs_own_resolution`** (outcome-conditioned — see below)

Report MFE in the direction of actual resolution as secondary.

**Adverse excursion (outcome-conditioned — not fixed-direction):**

A fixed-direction MAE toward into-value is tautological for `away_first` (bounded below by the away distance by construction). Redefined, conditioned on the event's own actual outcome:

| Outcome | Adverse excursion measured as |
| --- | --- |
| `into_first` | Maximum excursion **toward the away barrier** (against the fade) before resolution into POC — upper-bounded by the away distance since it didn't resolve away |
| `away_first` | Maximum excursion **back toward value / POC** (against the acceptance move) before resolution away — upper-bounded by the into distance |
| `unresolved` | Report both directions' max excursion over `H_cap`, unconditioned (no barrier to bound against) |

These are two separate, non-tautological metrics, each conditioned on its own outcome group — not one metric compared across groups. Report them in `path_mae_by_outcome.csv` under their outcome-conditioned names (`adverse_excursion_into_first`, `adverse_excursion_away_first`), not pooled into a single column.

**R2/R60:** If these outcome-conditioned adverse-excursion medians look large relative to their own bounding barrier (e.g., median adverse excursion on `into_first` is a large fraction of `dist_away`), do **not** narrate a "fade edge" from a destination-style win rate alone — a high `p_into` with routinely-large stop-out risk on the way there is not a survivable path.

---

## Invalidation (operational — not "15m hold")

This study is **not** a timed hold. The trade *concept* ends when the first barrier hits:

| If one were trading fade (into value) | Invalidation = **away** barrier first |
| If one were trading acceptance (away) | Invalidation = **into value** barrier first |

The prereg **measures both**; it does not pick a side to promote.  
Auction phrases ("poor structure repair," "time without continuation") are **not** operational here until TPO layer exists — do not invent ad hoc time stops beyond `H_cap` unresolved.

---

## Aggregates (descriptive fold only)

On primary VAH/VAL strict onset events:

| Metric | Definition |
| --- | --- |
| `n` | Onset events |
| `p_into` | P(into_first) |
| `p_away` | P(away_first) |
| `p_unresolved` | P(unresolved) |
| `Δ = p_into − p_away` | Signed contrast — **no promote gate**; **must be reported alongside `dist_ratio` strata**, not standalone |
| `dist_into`, `dist_away`, `dist_ratio` | Barrier-distance diagnostic (mandatory) |
| Adverse-excursion tables | By outcome, using the **outcome-conditioned** definitions above |
| `same_print_both` rate | From audit — realized tie frequency at trade-level resolution |

**Tie robustness:** repeat table on tie subgroup; do not pool into primary Δ.

**POC secondary:** optional same barrier construction only if a sourced amendment defines POC into/away; otherwise skip.

---

## Sample-size constraint (prereg, not post-hoc caveat)

```text
Corpus: trades_24h_6m Patrick build (~79 sessions with P7 joins).
Primary N: strict VAH/VAL onsets after dedup (expect hundreds, not thousands).
THIS IS A SINGLE DESCRIPTIVE FOLD.
- No IS / Validation / OOS split
- No year split for promotion
- No "ADVANCE to trade" regardless of Δ
- Result language: DESCRIPTIVE_ONLY / INCONCLUSIVE_AT_THIS_N — never SUPPORTED
```

Same honesty class as refusing to finish-claim Strategy 47's small POC cells.

---

## Explicit non-goals

- No trade / P&L / cost gate in this run  
- No TPO balance filter  
- No retune of `(q,N)`, away multiple, or `H_cap` after seeing Δ  
- No merging tie into primary  
- No importing 47 fade narrative as success criterion  
- No paid DOM / Fabio / Imre  
- **No headline `Δ` claim without `dist_ratio` context**  
- **No pooled adverse-excursion metric across outcome groups**  

---

## Outputs (when executed later)

| Path | Role |
| --- | --- |
| `results/events_strict_va.parquet` | Onset events + barriers + `dist_into`/`dist_away`/`dist_ratio` |
| `results/first_passage_summary.csv` | p_into / p_away / Δ, **stratified by `dist_ratio` tercile** (+ tie robustness) |
| `results/path_mae_by_outcome.csv` | Outcome-conditioned adverse-excursion diagnostics |
| `results/verdict.json` | `DESCRIPTIVE_ONLY` + n + Δ (no promote) |
| `results/FIRST_PASSAGE_REPORT.md` | Report — must include `dist_ratio` context and `same_print_both` rate |
| `results/audit.json` | Strict-only, VAH/VAL, no TPO, no IS split, resolution = trade-level, tie rate |

---

## Decision record

| Choice | Value |
| --- | --- |
| Subgroup | **B — strict primary** |
| Stack scope | VP + size; **TPO deferred** |
| Levels | VAH/VAL primary; POC secondary/out |
| Design | First-passage into vs away, barriers co-defined |
| Resolution granularity | **Trade-level prints** (v2) |
| Adverse-excursion definition | **Outcome-conditioned**, not fixed-direction (v2) |
| Barrier-distance diagnostic | **Mandatory**, `Δ` never reported without `dist_ratio` context (v2) |
| 47 prior | **Not imported** |
| Promotion | **Impossible** at this N by prereg text |

---

## Changelog (v1 → v2, pre-code)

| # | Issue | Fix |
| - | --- | --- |
| 1 | `Δ = p_into − p_away` conflated fade pressure with asymmetric barrier distances (POC proximity vs. fixed away offset) | Added mandatory `dist_into`/`dist_away`/`dist_ratio` diagnostic; `Δ` must be reported stratified by `dist_ratio`, never standalone |
| 2 | Fixed-direction `mae_before_resolve` was tautological for `away_first` events (bounded below by the away distance by construction) | Redefined as outcome-conditioned adverse excursion: measured against the barrier the event *didn't* hit, bounded by the barrier it *did* |
| 3 | Resolution granularity unspecified — 1m bars could inflate `same_bar_both` and let the tie-rule silently overrule near events | Froze resolution to **trade-level prints**; added mandatory audit reporting of realized tie rate |

Ready for code only after explicit go-ahead.

---

## Execution record

| Field | Value |
| --- | --- |
| Run | Strategy 63 — complete |
| Classification | `DESCRIPTIVE_ONLY` / `INCONCLUSIVE_AT_THIS_N` |
| Artifacts | `strategies/63_patrick_strict_va_first_passage/results/` |
| Promote | **false** |
