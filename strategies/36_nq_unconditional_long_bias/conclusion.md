# Conclusion: Strategy 36 Unconditional NQ Long Bias

**Verdict:** **C (KILL as an active trading edge / Alpha)**  
**Status:** FAMILY CLOSED. NO ACTIVE EDGE.

---

## 1. Official Forensic Verdict
The 2010–2026 sample provides strong evidence of positive passive RTH drift, but **no evidence that unconditional intraday long exposure produces exploitable alpha after realistic costs**.

Across 16 years of continuous 1-minute NQ data (2010--2026):
1. **Intraday Horizons are Net Negative**: All short/intermediate horizons (5m, 15m, 30m, 60m) are strictly loss-making after 1.0 point round-trip friction across In-Sample and full-period metrics. Cumulative 60-minute holding from 09:35 lost **-2,753.75 net points** with a Sharpe of **-0.179**.
2. **Session Drift is Pure Passive Beta, Not Alpha**: While holding from 09:35 to 15:55 produced positive net points (+2,429.75 pts), it is strictly dominated by the passive RTH Buy-and-Hold benchmark (+3,657.00 pts, Sharpe 0.123 vs 0.085, Calmar 0.056 vs 0.046). Active entry timing sacrificed over 1,200 points of market drift while paying 58.9% of gross profits in broker/exchange friction.
3. **Active Risk Structures Guarantee Losses**: Symmetric stop/target active systems (1.0R and 1.5R ATR pairs) produced **0 out of 8** positive cells In-Sample and **0 out of 8** positive cells in Validation.

The finding settles the question definitively: NQ went up over sufficiently long passive exposure (+3,657 pts), but "buy NQ at some intraday time and make money after costs" is completely disproven. This also explains Strategy 35: bull flags looked profitable only because they selected situations inside NQ's upward drift, whereas a simple impulse outperformed the flag. The conjecture that "the secret is simply to be long NQ" is permanently closed.

---

## 2. Hostile Audit Checklist Confirmation
- [x] Signal uses only $t \le T$ (pure clock timestamps)
- [x] Outcomes start at next open ($T+1$ open)
- [x] Thresholds frozen on IS only (PREREGISTRATION.md locked)
- [x] No grid search or post-hoc filter optimization
- [x] Val and OOS scored once after freeze
- [x] 2025 / 2026 separated in reporting
- [x] Multi-horizon check (5m, 15m, 30m, 60m, session close)
- [x] Symmetric Long vs Short identical pair comparison
- [x] Passive Buy-and-Hold benchmark comparison
- [x] Ambiguity policy enforced (stop-first adverse assumption)
- [x] Specific failure mode documented in `conclusion.md`
