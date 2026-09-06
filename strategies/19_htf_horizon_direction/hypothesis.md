# Hypothesis — Longer-horizon direction

Short-horizon scans (H≤120) found ~coin-flip direction inside HIGH.
Hypothesis: the activity regime may resolve directionally on a **longer**
clock (rest of session / multi-hour), and a small frozen HTF/context sign
menu may show conditional lift only at those horizons.

## Frozen outcomes (pre-specified)

| ID | Definition |
|----|------------|
| `H240` | close at entry+240m − entry (skip if <240 bars left in session) |
| `SESS_END` | last session bar close − entry |

## Frozen sign menu (causal ≤ T)

| ID | Side |
|----|------|
| `gap_follow` | sign(session_open − prior Globex day close) |
| `prior_day_color` | sign(prior day close − open) |
| `prior_sess_mid` | sign(close_T − prior session mid) |
| `sess_open_follow` | sign(close_T − session_open) |
| `vwap_follow` | sign(close_T − session VWAP to T) |
| `mom15_follow` | sign(close_T − close_{T−15}) |

No stops/targets. Strategy 12 untouched. No adding features after OOS.
