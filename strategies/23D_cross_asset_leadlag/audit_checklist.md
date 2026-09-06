# Hostile Audit Checklist — 23D-ES

Copied from `research_framework/audit_checklist.md`. Applies to the **ES leg only**.

- [x] Signal uses only `t <= T`
- [x] Outcomes start at next open
- [x] Thresholds frozen on IS only
- [x] No grid search for the promoted rule
- [x] Val and OOS scored once after freeze — **N/A: skipped**; IS already fails incremental bar everywhere (cheapest kill; documented)
- [x] 2025 / 2026 separated — **N/A** (no Val/OOS by design)
- [x] Multi-clock or multi-horizon check
- [x] Same-TOD or unconditional baseline where relevant
- [x] Ambiguity policy documented
- [x] Overlap / clustering documented if multiple signals/day
- [x] External data lag documented (overnight closes before 09:30)
- [x] Failure mode written in `conclusion.md` (not just "failed")

## Evidence

| Item | Result |
|------|--------|
| Grid | **24** pre-registered |
| Strong / soft | **0** / **2** |
| Incremental vs HIGH-long | **negative all H30 clocks** |
| Verdict | **C** (23D-ES only) |
| Bonds | **UNTESTED** — separate open item |
