# Conclusion — Family 23 (external causal sources)

**Status: CLOSED** (hard stop fired on 23D-ZN IS)

## Tested legs

| Leg | Verdict | Specific failure mode |
|-----|---------|------------------------|
| **23A** COT TFF | **C** | Incremental vs HIGH-long **monotonic** IS +2.5 → Val −7.4 → OOS −11.3pp (worse-than-baseline trend) |
| **23D-ES** overnight ES−NQ | **C** | IS-only; 0 strong / 24; all H30 clocks neg vs HIGH-long |
| **23D-ZN** overnight ZN−NQ | **C** | IS-only; 0 strong / 24; all H30 clocks neg vs HIGH-long; **hard stop** |

## Not tested (do not misread)

| Leg | Status |
|-----|--------|
| **23D-ZB** | **UNTESTED** — `ZB.FUT` never downloaded (duplicate ZN jobs only). Not a null. **Not** a family-23 rescue. |

## Family reading

Three external sources under Strategy-12 HIGH (COT positioning, ES overnight RS,
ZN overnight RS) all failed to add **stable incremental sign** over the already-validated
activity gate. Pattern: either IS-null incremental (ES, ZN) or IS soft lift that
**degrades monotonically** into worse-than-baseline (COT). Consistent with these
“externals” proxying the same activity/flow regime Strategy 12 already captures,
rather than supplying independent direction.

Per pre-registered hard stop: **no 5th external candidate** without a new argument.
**HOW** (sizing/execution conditional on Strategy 12 WHEN only) is the remaining
honest branch — or stop.
