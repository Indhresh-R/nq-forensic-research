# Step 2 Report — Implementation + audit only

**Status:** Complete.  
**Date:** 2026-09-22  
**Scope:** Frozen event extraction and lookahead/timestamp audit. **No forward returns. No DOWN_CLOSE / FAIL_CLEAR_ND. No mechanism verdict.**

Governing docs: `PREREGISTRATION.md`, `VSA_SOURCE_MAP.md`.  
Companion funnel: `FUNNEL_DIAGNOSTIC.md`.

---

## Settled before coding (unchanged from preregistration)

| Item | Freeze |
| --- | --- |
| Thresholds | `K=32`, `0.15×ATR`, `L=24`, `close_frac` 0.50/0.25, `wide=1.25×median` — **not retuned** |
| ATR | Causal simple mean of true range, length 20, per segment |
| Medians | Prior-20 within segment (exclude current bar) |
| Gaps | Incomplete 15m buckets dropped; gap > 20 minutes breaks segments and aborts confirmation |
| Tick grid | Available on bars; primary VSA predicates use float OHLC/volume as preregistered |

Researcher-defined thresholds remain explicitly **our operationalization**, not Williams’ exact rules. They were not touched after seeing counts.

---

## Pipeline delivered

```text
NQ 1m
 ↓
15m bars (n==15)
 ↓
causal medians / ATR / SOW seeds
 ↓
background (location + SOW)
 ↓
No Demand morphology
 ↓
next-bar confirmation
 ↓
A / B / C classification
 ↓
independent audit
```

### Code

| Path | Role |
| --- | --- |
| `code/constants.py` | Frozen numeric constants |
| `code/bars.py` | 15m aggregate, gaps, ATR |
| `code/extract.py` | Background / ND / confirm / A·B·C extractor + funnel |
| `code/audit.py` | Timestamp / lookahead / class invariants |
| `code/run_extract.py` | Runner |
| `code/test_synthetic.py` | Tick / gap unit checks |

### Artifacts (no outcome columns)

| Path | Contents |
| --- | --- |
| `results/bars_15m.parquet` | Working 15m series |
| `results/events.parquet` | A/B/C event rows |
| `results/failed_confirmations.parquet` | Gap / not-down confirmation attempts |
| `results/event_counts.csv` | Counts by split × class |
| `results/extract_meta.json` | Extraction meta |
| `results/funnel.json` | Stage counts |
| `results/audit_report.json` | Audit pass/fail detail |

---

## Extraction counts (not a verdict)

| Meta | Value |
| --- | --- |
| 1m rows | 4,788,194 |
| 15m bars | 288,266 |
| Segments | 8,069 |
| Events total | 6,287 |

| Split | A | B | C |
| --- | ---: | ---: | ---: |
| IS | 886 | 2,537 | 41 |
| Validation | 398 | 1,378 | 20 |
| OOS | 251 | 759 | 17 |
| **Total** | **1,535** | **4,674** | **78** |

Class C is uncommon relative to A and B, but **materially more frequent than Strategy 50’s Class C (n=20)**. This is an implementation frequency fact, not a license to retune thresholds, and not a mechanism conclusion.

Versus the frozen Step 3 power floors (`n≥30` IS / `n≥20` OOS for C and A): IS C=41 clears 30; OOS C=17 is **below** 20. A is abundant on all splits.

---

## Audit result

**`all_pass = true`**

Checked (among others):

- `t_event < t_confirmation` and `t_confirmation == t_event + 1`
- Class flags: C = BG∧ND, A = ¬BG∧ND, B = BG∧¬ND
- Event up-bar; confirm down-bar; same segment
- ND close_frac ≤ 0.50 for A/C
- Min separation ≥ 3; unique `t_event`
- No outcome / PnL / CVD / signed-volume columns

---

## Funnel snapshot (detail in `FUNNEL_DIAGNOSTIC.md`)

```text
warmup up-bars                      97,716
  near-high location                18,870
  SOW seed (any up-bar lookback)    85,204
  BG_WEAK                           18,420
  ND morphology                      4,120
  ND ∧ BG (C path candidates)          456
  ND ∧ ¬BG (A path)                  3,664
  BG ∧ ¬ND (B path)                 17,964
        ↓ separation / gap / not-down
  C confirmed                           78
  A confirmed                        1,535
  B confirmed                        4,674
```

Dominant C choke: **intersection of ND morphology with BG_WEAK** (4,120 ND → 456 with background), then next-bar-down confirmation.

---

## Explicit non-actions

Step 2 did **not**:

- compute `DOWN_CLOSE` or `FAIL_CLEAR_ND`
- compare C vs A or C vs B on outcomes
- calculate win rate, Sharpe, or P&L
- optimize any threshold (`K`, ATR frac, `L`, close cuts, wide mult)
- add a daily VSA scan
- interpret whether VSA “works”

---

## Notes for a future Step 3 (not started)

- C is observable enough for a descriptive mechanism table; OOS C n=17 sits under the preregistered OOS floor of 20, so a strict reading of the pass/fail gate may land **`INCONCLUSIVE` on power** even before Δ is examined — that is a frozen-rule consequence, not a retune mandate.
- Do not change event grammar after joining outcomes.
- Do not open a daily experiment because 15m C is “only” 78.

**Next allowed step:** Step 3 outcome join under the frozen preregistration, or an explicit power note without parameter search.
