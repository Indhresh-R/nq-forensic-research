# Step 2 Addendum — Implementation freezes (before coding)

**Status:** Settled ex ante. Does not change the research question or outcome definitions.  
**Date:** 2026-09-21  
**Scope:** Resolve the three open implementation ambiguities in `PREREGISTRATION.md`. No alternatives will be compared after this file.

---

## 1. ATR convention

**Choice:** Causal **simple mean of true range**, length 20, lagged one bar — the same construction used by this repository’s existing 15-minute causal studies (`research/15m_downside_break_failure`, Strategy 42 sibling ATR usage pattern).

```text
TR[t]  = max(high[t]-low[t], |high[t]-close[t-1]|, |low[t]-close[t-1]|)
ATR20[t] = mean(TR[t-19] … TR[t])     # requires 20 finite TR values in-segment
ATR20_prior[t] = ATR20[t-1]           # used at bar t (causal)
```

At a segment start, ATR is undefined until 20 in-segment bars exist. No Wilder smoothing. No parameter search.

**Class:** `RESEARCHER-DEFINED` implementation reuse — **not** a Wyckoff source definition.

---

## 2. Maintenance gaps / missing 15m bars

**Choice:**

1. Aggregate 1m → 15m only for buckets with **exactly 15** one-minute prints (`n == 15`). Incomplete buckets are **dropped**.
2. **Never** forward-fill OHLC or volume across missing buckets.
3. A **segment break** occurs when the time from the previous kept bar’s `end` to the current bar’s `start` exceeds **20 minutes** (15m bar + 5m tolerance), or at the first bar.
4. Effects of a segment break:
   - Pivot confirmation windows may not cross the break.
   - ATR warm-up resets inside the new segment.
   - Any open eligible TR is **invalidated** at the break (does not continue across the gap).
   - Open spring/upthrust recovery or confirmation windows **abort** (no event completion across the gap).

This freezes gap handling more strictly than the informal “ranges may span session boundaries” note: spans are allowed only across contiguous kept 15m bars (e.g. overnight Globex continuity). The daily 17:00–18:00 maintenance hole and weekends interrupt structure.

**Class:** `RESEARCHER-DEFINED`.

---

## 3. Tick-grid equality

**Choice:**

```text
TICK = 0.25
ticks(price) = round(price / TICK)     # nearest-tick integer
```

All boundary comparisons, equality tests (including Control A exclusion when `support20` matches `TR_low`), minimum-violation distances, and tolerance checks that compare two prices use **integer tick units**. Floating-point raw floats are not used for equality.

Distances in the preregistration stated in points are converted as `points / TICK` ticks (e.g. `0.25` point = 1 tick).

**Class:** `RESEARCHER-DEFINED`.

---

## Step 2 deliverable scope

```text
raw NQ 1m → 15m bars → pivots → candidate TRs
  → terminal event → return → confirmation
  → frozen event dataset (A / B / C labels)
  → independent lookahead / timestamp audit
```

**Forbidden in Step 2:** forward returns, leave-range outcomes, win rates, P&L, threshold search, interpretation of whether Wyckoff “works.”
