# Conclusion

**Phase 2 class: C — Research signal, not trading edge.**

Vilkov’s 30-minute surface contains some information about subsequent ES volatility, but most of that is already in IV ATM + ordinary market state. Residual OI-gamma information is small, horizon-dependent, and does not transfer cleanly to NQ.

**Phase 3: `MIXED_MECHANISM`**

What survived:

- ES RV30/60 identity ΔR² (~+0.012 / +0.014) **beats IV/TOD-matched and residual placebos** (nulls ≈ 0).
- Among frozen surface-part probes, **ATM share** is the strongest ES30/60 residual (not peak distance / slope / PC asym).
- Chrono blocks mostly positive for ES30 except **2019–2021**.

What did not:

- Effect is **not a general TOD property** — per-stamp OOS ΔR² is noisy and usually near zero / negative.
- **Regime dependence is unstable** (stronger in low IV / low prior-RV for some horizons; mid/high often worse).
- **NQ residual after ES-RV control stays tiny**; no clean ES-lead → NQ-follow trading story.
- Continuous atm×IV interaction adds nothing (slightly negative).

**Decision:** Do **not** open a trading-rule phase. Archive **Strategy 26 — Vilkov 0DTE Surface** as a well-tested research hypothesis (valuable negative / mixed library entry), unless new post-2024 surface data appears for a fresh OOS check.

Panel years: 2016-2024 (no 2025-26 in Vilkov `data_opt`)

See `artifacts/26_vilkov_0dte_surface/phase3_report.md`.
