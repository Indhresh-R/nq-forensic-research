# Hostile Audit Checklist — 24D Vol-Harvest Structure

Copied from `research_framework/audit_checklist.md`, plus family-24 item.

- [x] Signal uses only `t <= T`
- [x] Outcomes start at next open
- [x] Thresholds frozen on IS only
- [x] No grid search for the promoted rule
- [x] Val and OOS scored once after freeze *(Val done; OOS optional)*
- [ ] 2025 / 2026 separated *(OOS not required to close)*
- [x] Multi-clock or multi-horizon check *(multi-session)*
- [x] Same-TOD or unconditional baseline where relevant
- [x] Ambiguity policy documented *(dual breakout skip; stop-first)*
- [x] Overlap / clustering documented if multiple signals/day
- [x] External data lag documented *(N/A)*
- [x] Failure mode written in `conclusion.md` (not just "failed")
- [x] No directional claim smuggled in (verify PnL is measured on a symmetric/agnostic structure, or separately for both directions with no net directional bet implied)

## Evidence

| Item | Note |
|------|------|
| Decisive contrast | `regime_width` − `uncond_wide` (not each-vs-base alone) |
| IS → Val | ΔSharpe −3.10 → −2.79; CI entirely below 0 |
| 24B | Folded — `regime_width` arm is the 24B hypothesis |
| Verdict | **C** on HIGH harvest; see `conclusion.md` |
