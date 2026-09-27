# Step 2 Report — Implementation + audit only

**Status:** Complete.  
**Date:** 2026-09-21  
**Scope:** Frozen event extraction and lookahead/timestamp audit. **No forward returns. No leave-range outcomes. No mechanism verdict.**

Governing docs: `PREREGISTRATION.md`, `STEP2_ADDENDUM.md`, `WYCKOFF_SOURCE_MAP.md`.

---

## Settled before coding

| Item | Freeze |
| --- | --- |
| ATR | Causal simple mean of true range, length 20 (project 15m convention). Not Wilder. Not a Wyckoff source rule. |
| Gaps | Incomplete 15m buckets dropped; no OHLC forward-fill; gap > 20 minutes breaks segments, pivots, open TRs, open recovery/confirm windows. |
| Tick grid | All boundary/equality comparisons use integer ticks at 0.25 point. |

---

## Pipeline delivered

```text
NQ 1m → 15m (n==15) → segments → ATR → pivots
  → candidate TRs → terminal violation → return
  → confirmation → event classes A / B / C
  → independent audit
```

### Code

| Path | Role |
| --- | --- |
| `code/constants.py` | Frozen numeric constants |
| `code/bars.py` | 15m aggregate, gaps, ATR, tick helpers |
| `code/extract.py` | TR / terminal / confirm / Control A extractor |
| `code/audit.py` | Timestamp / lookahead / class invariants |
| `code/run_extract.py` | Runner |
| `code/test_synthetic.py` | Tick / pivot / gap unit checks |

### Artifacts (no outcome columns)

| Path | Contents |
| --- | --- |
| `results/bars_15m.parquet` | Working 15m series |
| `results/trading_ranges.parquet` | Eligible TR instances |
| `results/events.parquet` | A/B/C event rows |
| `results/event_counts.csv` | Counts by split × class × kind |
| `results/extract_meta.json` | Extraction meta |
| `results/audit_report.json` | Audit pass/fail detail |

---

## Extraction counts (not a verdict)

| Meta | Value |
| --- | --- |
| 1m rows | 4,788,194 |
| 15m bars | 288,266 |
| Segments | 8,069 |
| Swing lows / highs | 33,523 / 33,159 |
| Trading ranges | 2,402 |
| Events total | 13,510 |

| Split | A | B | C |
| --- | ---: | ---: | ---: |
| IS | 7,386 | 204 | 10 |
| Validation | 3,768 | 121 | 6 |
| OOS | 1,918 | 93 | 4 |
| **Total** | **13,072** | **418** | **20** |

Class C is rare relative to A and B under the frozen grammar. That is an **implementation frequency fact**, not a license to retune TR/confirmation rules, and not a mechanism conclusion.

---

## Audit result

**`all_pass = true`**

Checked (among others):

- `t_viol <= t_return`
- Class C: `t_return < t_confirm` (separate timestamps)
- Confirm within `W=12`
- Return within `R_max=6`
- Same segment for viol/return
- Spring extreme below `TR_low`; upthrust extreme above `TR_high`
- No outcome / leave / PnL columns present
- `test_pivot + L == t_confirm` for C

---

## Explicit non-actions

Step 2 did **not**:

- compute leave-range rates
- compare C vs A or C vs B on outcomes
- calculate win rate, Sharpe, or P&L
- optimize any threshold
- interpret whether Wyckoff “works”

---

## Notes for a future Step 3 (not started)

- Primary C sample sizes (IS n=10, OOS n=4) sit below the preregistration `SUPPORTED` floors (`n≥30` IS / `n≥20` OOS for C and A). Under the frozen pass/fail rule, that path would be **power / `INCONCLUSIVE`**, not a retune mandate.
- B vs C remains the sharper mechanism contrast once outcomes are allowed; A remains the generic false-break null.
- Do not change event grammar after joining outcomes.

**Next allowed step:** Step 3 outcome join under the frozen preregistration, or an explicit power-failure closeout without parameter search.
