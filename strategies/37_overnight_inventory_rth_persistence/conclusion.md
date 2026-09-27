# Conclusion: Strategy 37 Overnight Inventory → RTH Persistence

**Verdict:** **C (KILL at Information Gate)**  
**Status:** FAMILY CLOSED. NO PRE-MARKET INVENTORY ALPHA.

---

## 1. Official Forensic Summary
Pre-market Globex overnight inventory features (Gap size, Overnight Range ratio, Inventory Location pinning, Overnight Extension regimes, and Prior-Day Confluence) contain **no statistically robust conditioning information** regarding subsequent RTH directional persistence in continuous NQ futures.

Across 3,470 paired overnight-RTH sessions (2010--2026):
1. **Gap Continuation is Unforecastable**: Across the full sample, RTH moves in the direction of the overnight gap exactly **50.8%** of the time (IS 51.3%, Val 50.7%, OOS 48.0%), indistinguishable from a random coin flip.
2. **Directional Efficiency is Invariant**: RTH directional efficiency ($|Close - Open| / Range$) is virtually identical across all overnight inventory regimes (tightly bound between 0.46 and 0.50). Pinned long inventory (0.493) does not produce higher efficiency than balanced inventory (0.472).
3. **Severe Instability in Extreme Tail Regimes**:
   - `LARGE_GAP_UP` returns flip from +5.79 pts In-Sample to **-7.97 pts** in Validation and **-23.60 pts** in OOS.
   - `TRUE_GAP_DOWN` returns flip violently from **-135.25 pts** in Validation (extreme downward continuation) to **+175.92 pts** in OOS (extreme upward reversal).

Because pre-market overnight inventory fails to demonstrate consistent conditioning over RTH directional persistence, the family is killed at the Information Gate without attempting trade execution or monetization.

---

## 2. Hostile Audit Checklist Confirmation
- [x] Information strictly uses $t \le 09:29:59$ ET (no RTH lookahead)
- [x] Features and bins frozen prior to scan execution
- [x] Chronological splits enforced (IS 2010–2021, Val 2022–2024, OOS 2025–2026)
- [x] No parameter mining or rule fitting
- [x] Tested against unconditional population baselines
- [x] Specific failure mode documented in `conclusion.md`
