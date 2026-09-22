# Preregistration — 52 Market State Census (Step 0)

**Status:** FROZEN BEFORE CALCULATION.  
**Label:** Descriptive market map only. Not a strategy.  
**Namespace:** `strategies/52_market_state_census/`

No entries, exits, stops, targets, forward returns, win rates, or P&L may be computed under this file. Definitions below must not be edited after census tables exist in order to chase a narrative.

---

## Question

How often is NQ in different **observable** market conditions (directionality, volatility, volume, range compression/expansion), how do those conditions vary by time-of-day / day-of-week / year, and how persistent are they?

This is **not**:

- a regime-trading system
- an edge search
- authorization to trade “trend” or “chop”
- a profitability study

---

## Data

| Item | Freeze |
| --- | --- |
| Instrument | Continuous NQ futures |
| Source | `data/nq_1m_continuous.parquet` via `common.nq_session.load_nq` (read-only) |
| Clock | `America/New_York` |
| Session | Globex `session_date` roll at 18:00 ET (`common.nq_session`) |
| Working bar | **1-minute** |
| Primary analysis window | **09:30–16:00 ET** (`ny_min ∈ [570, 960)`) |
| NY RTH open | 09:30 ET |

Rolling features may look backward into pre-09:30 bars when the contiguous 1m segment allows it. Gaps > 1.5 minutes break rolling continuity.

---

## Chronological threshold freeze

Tercile thresholds (33% / 67%) for labeling are computed **only** on census-eligible bars whose `session_date` year is in Discovery / IS:

| Sample | Years |
| --- | --- |
| Threshold freeze (IS) | 2010–2021 |
| Validation years (labeled with frozen cuts; not used to set cuts) | 2022–2024 |
| OOS years (same) | 2025–2026 |

2026 is a partial-year sample whenever the dataset ends mid-year.

---

## Frozen feature definitions (causal)

All features at timestamp `t` use information at or before `t` only.

### Directionality — Efficiency Ratio

\[
ER_N = \frac{|Close_t - Close_{t-N}|}{\sum_{i=t-N+1}^{t} |Close_i - Close_{i-1}|}
\]

Windows: **30, 60, 120** minutes.  
**Primary label window:** `ER_60`.

### Volatility

- `RV_N` = sqrt(sum of squared 1-minute simple returns) over N minutes; N ∈ {30, 60}
- `ATR_30` = mean true range over 30 minutes  
**Primary label:** `RV_60`.

### Volume — time-of-day relative volume

- `vol_roll_30` = sum of volume over last 30 contiguous minutes
- Expected = trailing mean of `vol_roll_30` at the **same `ny_min`** over the prior **60 sessions** (sessions with no history → NaN)
- `RVOL = vol_roll_30 / expected`  
**Primary label:** `RVOL`.

### Range / compression

- `range_N = rolling_high_N - rolling_low_N`, N ∈ {30, 60}
- `range_norm_N = range_N / ATR_30`  
**Primary label:** `range_norm_60`.

### Eligibility

A bar is census-eligible iff it is inside the analysis window and all primary features (`ER_60`, `RV_60`, `RVOL`, `range_norm_60`, `ATR_30`) are finite.

---

## Frozen label rules

Predetermined terciles on the IS freeze sample:

| Bucket | Rule |
| --- | --- |
| Low | ≤ IS 33rd percentile |
| Mid / Normal | (IS 33rd, IS 67th] |
| High | > IS 67th percentile |

Independent labels: `directionality_state`, `volatility_state`, `volume_state`, `range_state`.

### Composite descriptive flags (non-exclusive)

| Flag | Definition |
| --- | --- |
| TRENDING | High directionality |
| CHOP_RANGE | Low directionality |
| HIGH_ACTIVITY | High volatility **OR** high volume |
| LOW_ACTIVITY | Low volatility **AND** low volume |
| COMPRESSION | Low range state |
| EXPANSION | High range state |

### Mutually exclusive `composite_primary` priority

`TRENDING` > `CHOP_RANGE` > `COMPRESSION` > `EXPANSION` > `HIGH_ACTIVITY` > `LOW_ACTIVITY` > `TRANSITION_MIXED`

---

## Forbidden

- Strategy construction; entry/exit/stop/target rules
- Forward-return / P&L / optimization
- Selecting thresholds because they look “tradable”
- Using future bars to classify state at `t`
- Volume profile / POC in this step
- Calling any state “profitable” or “optimal”

---

## Outputs

| Path | Role |
| --- | --- |
| `results/market_state_features.parquet` | Continuous features (analysis window) |
| `results/thresholds_frozen.json` | IS tercile cuts |
| `results/market_states.parquet` | Labeled panel |
| `results/table*.csv` | Distribution / persistence / transitions |
| `results/audit_report.json` | Leakage audit |
| `MARKET_STATE_CENSUS.md` | Final descriptive report |

---

## Verdict format

The report ends with **MARKET CENSUS VERDICT** and one **NEXT RESEARCH QUESTION** (mechanism only). That next question is **not** answered in Step 0.
