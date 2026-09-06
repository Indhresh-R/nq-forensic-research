# Hostile Audit Checklist — 23A COT Positioning

Copied from `research_framework/audit_checklist.md`.

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
- [x] External data lag documented
- [x] Failure mode written in `conclusion.md` (not just "failed")

## Evidence

| Item | Note |
|------|------|
| Freeze | Zero adjustment IS→Val→OOS |
| Multiplicity | 120 cells; 5 IS strong ≈ noise |
| Kill metric | HIGH+COT vs HIGH-long: IS +2.5pp → Val −7.4pp → OOS −11.3pp |
| Verdict | **C** — see `conclusion.md` |
