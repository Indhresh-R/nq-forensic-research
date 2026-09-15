# Conclusion: Strategy 35 Bull Flags and Bear Flags

**Verdict:** **C (KILL)**  
**Status:** FAMILY CLOSED. NO TRADE.

---

## 1. Official Forensic Summary
Classical Bull Flags and Bear Flags demonstrate **no standalone predictive edge** on continuous equity index futures (NQ and ES) across the 2010--2026 data window. On ES, the pattern fails decisively out-of-sample across all pre-registered exit rules, producing sub-1.0 profit factors (0.53 to 0.72) and negative expectancy even in frictionless tests. On NQ, apparent profitability in Bull Flags is thoroughly exposed as an artifact of secular long market drift (beta) rather than pattern geometry: benchmark attribution proves that entering immediately after an impulse pole without a flag achieves higher win rates (55% vs 41%) and superior expectancy. Bear flags collapse on both assets. In accordance with repository kill rules, the pattern family is killed outright without post-hoc filter stacking.

---

## 2. Specific Failure Modes
1. **Out-of-Sample Decay on ES**: Every pre-registered target variant (Measured Move, 1.0R, 1.5R, 2.0R, EOD Flat) suffers severe OOS degradation on ES (OOS profit factor 0.53--0.72 vs Validation 1.15--1.52).
2. **Directional Asymmetry & Beta Confound**: Long flag setups piggyback on index drift while short flag setups fail catastrophically (e.g. NQ Bear Flag C4 OOS $E = -59.43$ pts; C5 OOS $E = -65.09$ pts).
3. **Absence of Incremental Alpha**: The "flag" consolidation does not enhance continuation probability; it degrades sample efficiency and lowers the baseline hit rate compared to naive momentum continuation.
4. **Failure of Classical Measured Move**: Projecting 1.0x flagpole height produces anemic hit rates (~32--43%) and fails in hostile live market regimes.

---

## 3. Hostile Audit Checklist Confirmation
- [x] Signal uses only $t \le T$ (completed 5m bar)
- [x] Outcomes start at next open ($T+1$ 1m open)
- [x] Thresholds frozen on IS only (PREREGISTRATION.md locked)
- [x] No grid search for the promoted rule
- [x] Val and OOS scored once after freeze
- [x] 2025 / 2026 separated in reporting
- [x] Multi-asset check executed across NQ and ES
- [x] Same-TOD and unconditional pure impulse baseline evaluated
- [x] Ambiguity policy documented and enforced (stop-first adverse assumption)
- [x] Overlap / clustering documented (max 1 trade/session/candidate)
- [x] Failure mode written in `conclusion.md`
