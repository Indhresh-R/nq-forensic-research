# Conclusion — 23A COT Positioning

**Verdict: `C` CLOSED**

## Methodology (lag — auditors)

COT `report_date` is the **Tuesday** position snapshot. Public release is the
following **Friday ~15:30 ET**. Trades may use that report only on price action
from the **next trading session after Friday's release** — never Tuesday–Friday
of the snapshot week. Same pattern as EOD-options lag in
`research_framework/causal_rules.md`.

Frozen definitions (W=104 z → p10/p90 extremes; sides `lev_fade` / `am_follow`;
Strategy-12 HIGH p66) were **never adjusted** on Val or OOS.

## Triple (headline NY_AM `lev_fade` T+30 H30)

| Split | ALL+COT | HIGH-long | HIGH+COT | vs ALL | vs HIGH-long | n |
|-------|---------|-----------|----------|--------|--------------|---|
| IS | 53.1% | 56.2% | 58.7% | +5.6pp | +2.5pp | 179 |
| Val | 45.8% | 57.4% | 50.0% | +4.2pp | **−7.4pp** | 42 |
| OOS | 47.5% | 54.7% | 43.5% | −4.1pp | **−11.3pp** | 69 |

Multiplicity: **120** grid cells scanned; **5** IS strong (~4.2%) ≈ conventional noise rate.

## Failure mode

COT positioning extremes show a real absolute association with forward direction
(ALL+COT lift persisted weakly into Val), but provide **no stable incremental lift**
over the already-validated Strategy 12 activity gate — the headline IS cell's
incremental edge **reversed sign** at Val (−7.4pp) and stayed negative at OOS (−11.3pp).
Consistent with COT positioning correlating with the same underlying activity/flow
regime Strategy 12 already captures, rather than adding independent directional
information. Do not retune deciles/sides; no 23B/23C rescue.

## Family note

23A is **C**. Sibling **23D** (cross-asset lead-lag) is a separate external-source
test, not a COT retune — still subject to family-23 multi-comparison.
