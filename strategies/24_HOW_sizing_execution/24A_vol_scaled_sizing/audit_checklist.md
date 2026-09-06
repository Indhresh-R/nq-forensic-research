# Hostile Audit Checklist — 24A Vol-Scaled Sizing

Copied from `research_framework/audit_checklist.md`, plus family-24 item.

- [x] Signal uses only `t <= T`
- [x] Outcomes start at next open
- [x] Thresholds frozen on IS only
- [x] No grid search for the promoted rule
- [x] Val and OOS scored once after freeze
- [x] 2025 / 2026 separated
- [x] Multi-clock or multi-horizon check
- [x] Same-TOD or unconditional baseline where relevant
- [x] Ambiguity policy documented
- [x] Overlap / clustering documented if multiple signals/day
- [x] External data lag documented *(N/A — no external series)*
- [x] Failure mode written in `conclusion.md` (not just "failed")
- [x] No directional claim smuggled in (verify PnL is measured on a symmetric/agnostic structure, or separately for both directions with no net directional bet implied)

## Evidence

| Item | Note |
|------|------|
| Freeze | W=30; clips 0.25/4.0; s_HIGH=0.70; rv_ref=IS median |
| Direction audit | coin-flip + long/short; same-sign deterioration |
| Triple | IS_NULL → VAL_CONFIRMS_NULL → OOS_NULL |
| Verdict | **C CLOSED** (sizing only) |
