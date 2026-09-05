# AM Trades NY Continuation — Pre-Committed Mechanical Definitions

**Frozen before any performance evaluation. No parameter search. Ambiguities resolved once.**

Document version: 1.0  
Hypothesis: Core AM Trades daily-bias → session-profile → NY continuation (no SMT, no VWAP, no ORB).

---

## 0. Data & Clock

| Item | Definition |
|------|------------|
| Instrument | Continuous front-month NQ 1-minute OHLCV (`nq_1m_continuous.parquet`) |
| Timezone | `America/New_York` (DST-aware) |
| Session date `S` | If NY clock hour ≥ 18 → `S = calendar_date + 1 day`; else `S = calendar_date` |
| Daily candle `S` | Aggregate all 1m bars with session date `S` from 18:00 (prev calendar) through 16:59 NY |
| Tick size | 0.25 NQ points |
| Splits | IS 2010–2021; Validation 2022–2024; OOS 2025–2026 (untouched until frozen) |

No lookahead: day-`S` bias uses only **completed** daily candles with session date `< S`.

---

## 1. Daily Bias

### 1.1 Ambiguities (AM public material) → one choice each

| Ambiguous term | Pre-committed mechanical choice |
|----------------|----------------------------------|
| “Relevant swing” | Confirmed 3-bar daily pivot (high/low strictly greater/less than both neighbors), plus failure swings (below), inside a 30-completed-day lookback |
| “Required separation” | Minimum **40.0** points between retained same-side swings (absolute price distance). Not optimized. |
| “Failure swing” | Swing high whose price is **strictly below** the prior retained swing high (lower high); swing low **strictly above** prior retained swing low (higher low) |
| “Manipulation” | Session day trades **through** the level and **closes back inside**: for a low `L`: `day.low < L` AND `day.close > L`. For a high `H`: `day.high > H` AND `day.close < H` |
| “Deep close” | Close **beyond** the level: for low `L`: `day.close < L`; for high `H`: `day.close > H`. Deep close **invalidates** that level thereafter |
| When bias is known | At start of session `S`, using manipulations on days `< S` only |

### 1.2 Algorithm (causal)

1. Build completed daily OHLC for all session dates.
2. For each completed day `i` (needs day `i+1` to confirm pivot), mark:
   - `pivot_high[i]` if `H[i] > H[i-1]` and `H[i] > H[i+1]`
   - `pivot_low[i]` if `L[i] < L[i-1]` and `L[i] < L[i+1]`
3. Walk chronologically; retain pivots that are ≥ 40 pts from the last retained same-side swing. Tag failure swings when the new pivot is a lower-high / higher-low vs prior retained.
4. **Active relevant low** at start of `S`: most recent retained swing low with date `< S` that has **not** been deep-closed on any day `d` with `swing_date < d < S`.
5. **Active relevant high**: mirror.
6. **Bullish bias** on `S` iff:
   - There exists an active relevant low `L` that was manipulated on some day `m` with `swing_date < m < S`, and no deep close of `L` on any day after that manipulation through `S-1`, **and**
   - There exists an active relevant high `H` with `H >` prior day close (upside draw).
7. **Bearish bias**: mirror on relevant high manipulation + downside draw to active relevant low.
8. If both bullish and bearish conditions hold, take the bias whose **most recent manipulation day** is later. If tied, **no bias** (invalid).
9. If neither, **no bias** (invalid / no-trade).

---

## 2. Daily Profile (three 7-hour windows)

| Session | NY clock |
|---------|----------|
| Asia | 18:00–01:00 (exclusive end) |
| London | 01:00–08:00 (exclusive end) |
| New York | 08:00–16:00 (entries only until 15:00; flat by 16:00) |

### 2.1 Session extremes

For session window `W` on day `S`:
- `W.high = max(high)`, `W.low = min(low)`, `W.close = close of last 1m bar in window`
- Require ≥ 30 one-minute bars in Asia and London; ≥ 60 in NY before classifying NY-only profiles.

### 2.2 What is a “reversal” (exact)

A **bullish reversal** of level `X` by window `W`:
1. `W.low < X` (takes / runs the level by **any** amount; 1 tick sufficient)
2. `W.close > X` (closes back on the opposite side — strict)

A **bearish reversal** of level `X` by window `W`:
1. `W.high > X`
2. `W.close < X`

### 2.3 Profile classes (must agree with daily bias)

**Bullish bias only — exactly one label, first match wins:**

| Code | Name | Rule |
|------|------|------|
| A | 18:00 reversal | Let `PDL` = prior session day low. Asia reverses `PDL` bullishly. |
| B | 01:00 reversal | London reverses Asia.low bullishly. |
| C | 08:00 NY reversal | Let `ONL = min(Asia.low, London.low)`. During NY, price makes `low < ONL`, then a 1m **close > ONL** occurs at or before 15:00. Profile confirmed at that close bar. |
| D | invalid | None of A/B/C |

**Bearish bias:** mirror (prior day high / Asia.high / overnight high).

Profile direction must equal daily bias direction; otherwise D.

---

## 3. NY Continuation Entry

### 3.1 Sweep extreme

| Bias | Sweep level | Sweep extreme price |
|------|-------------|---------------------|
| Bull A | PDL | minimum low of Asia bars that traded `< PDL` (else Asia.low) |
| Bull B | Asia.low | minimum low of London bars that traded `< Asia.low` |
| Bull C | ONL | minimum NY low from 08:00 until (and including) the confirmation close bar |
| Bear | mirrored highs | |

### 3.2 Reversal confirmation

Already required by profile. Entry logic begins **at/after** the bar that confirms the profile (Asia close for A, London close for B, first NY close back through level for C).

### 3.3 Reference candle (bearish/down-close for longs)

**Pre-committed:**
1. Consider 1-minute bars from the bar that printed the sweep extreme through the profile-confirmation bar (inclusive).
2. **Reference** = last bar in that range with `close < open` (down-close).
3. If none, reference = the sweep-extreme bar itself.
4. **Long trigger:** subsequent 1m bar (after confirmation) with `close > reference.high` (strict).
5. **Short:** last up-close (`close > open`) in range; trigger `close < reference.low`.

### 3.4 Execution

| Item | Rule |
|------|------|
| Signal bar | Trigger close bar |
| Fill | **Next** 1m bar **open** |
| Slippage | +1.0 point adverse (long: `fill = open + 1`; short: `fill = open - 1`) |
| Commission | 0.25 points round-turn (subtracted from PnL) |
| Max entries | 1 per session day |
| Entry cutoff | Signal bar must be ≤ 14:59 NY (fill ≤ 15:00) |
| 09:30 open | Record `open` of 09:30 NY bar as a feature; **not** used as a filter in primary test |

---

## 4. Stop (entry-based invalidation)

| Side | Stop price |
|------|------------|
| Long | `sweep_extreme - 0.25` |
| Short | `sweep_extreme + 0.25` |

- Risk `R_points = |fill - stop|` after slippage.
- If `R_points < 1.0` point → **skip trade** (structure too tight / non-executable risk).
- **Gap through stop after entry:** if a bar’s open is beyond stop, exit at that **open** (not at stop). Never credit fill inside the gap.
- **Gap through stop on entry bar:** if fill is already beyond stop (e.g. long fill ≤ stop), record `gap_through_stop_at_entry`, exit immediately at fill (PnL = −commission only from entry; R loss recorded using intended stop distance before skip rule… actually: if fill beyond stop, skip as non-executable **unless** we already committed — we **do not enter**; count as blocked gap-through).

Revised freeze: if next-bar open after slippage is on/beyond stop → **no entry**, flag `blocked_gap_through_entry`.

---

## 5. Target

| Primary | `2R` from actual fill: long `fill + 2 * R_points` |
| Robustness (only if IS∧Val primary PF>1 and expectancy>0) | Also report 1.5R, 2.5R, 3R — pre-specified, not searched |

Intrabar: if `low ≤ stop` and `high ≥ target` in same bar → **STOP FIRST**, flag `ambiguous_bar = true`.

Time stop: if still open at 16:00 NY, exit at 16:00 bar **open** if present else last close; reason `time_exit`.

---

## 6. Execution forensics (mandatory)

Reported for every trade / aggregate:
- next-bar-open entry, adverse slippage, commission
- ambiguous same-bar stop+target count
- gap-through-stop exits and blocked entries
- entry-to-stop risk distribution (mean/median/p90)
- MAE / MFE in price and R
- minutes to exit
- exit reason histogram

---

## 7. Primary parameter freeze

| Parameter | Value |
|-----------|-------|
| Daily lookback | 30 |
| Swing separation | 40.0 pts |
| Pivot confirmation | 1 bar each side |
| Slippage | 1.0 pt adverse entry |
| Commission | 0.25 pt RT |
| Stop buffer | 1 tick (0.25) |
| Target | 2R |
| Confirmation TF | 1-minute |
| SMT / VWAP / ORB | **OFF** |

### Robustness grid (only if IS and Validation both positive expectancy and PF>1)

1. separation ∈ {30, 40, 50}
2. confirmation ∈ {1m, 5m} (5m = trigger on 5m close through ref high/low; fill still next 1m open after that 5m close)
3. target R ∈ {1.5, 2.0, 2.5, 3.0}
4. reversal close tolerance ∈ {0, 0.25} extra points beyond level (0 = primary)

Do not expand beyond this grid.

---

## 8. SMT secondary (only if OOS primary edge positive)

NQ vs ES divergence at the sweep: for bullish sweep, ES does **not** make a lower low while NQ does (or vice versa) within the sweep window — exact rule documented in code comments if/when run. **Never** used to rescue a failed core.

---

## 9. Failure conditions

Declare **FAILED** and stop optimization if:
- OOS PF < 1.0, or
- OOS expectancy ≤ 0, or
- edge disappears under stated execution assumptions, or
- no reasonable robustness cell survives IS + Validation + OOS

---

## 10. Verdict labels

| Code | Meaning |
|------|---------|
| A | Strong executable edge |
| B | Promising but insufficient evidence |
| C | No demonstrated edge |
| D | Execution/data artifact |
