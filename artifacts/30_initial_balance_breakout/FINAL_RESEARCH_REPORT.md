# Initial Balance research program — final report

## Scope and safeguards

NQ and ES continuous 1-minute data were audited from June 2010 through August 2026. NQ had 3,476 complete 09:30–16:00 ET sessions; shortened/incomplete sessions were excluded. All tests use a completed five-minute signal, next one-minute-open entry, 1-minute stop/target evaluation, adverse stop-first treatment for same-minute ambiguity, and explicit round-trip costs.

The research used chronological gates: Train (2010–2018), Inner Validation (2019–2021), Validation (2022–2024), and OOS (2025–2026). Later periods were not used to select a reported candidate.

## What was tested

- Standard Initial Balance continuation: first 5-minute close outside the 09:30–10:30 IB; opposite-IB stop; 1R target.
- Stop geometry: opposite IB and 0.25/0.50/0.75/1.00 × IB-width stops.
- Targets: 0.75/1.00/1.50/2.00R.
- Causal filters: signal time, relative signal-bar volume, IB-width regime, candle strength, VWAP alignment, and risk caps.
- Causal failed-breakout fade: low relative-volume breakout, completed five-minute re-entry into IB, opposite-side entry, excursion-extreme stop, IB-midpoint/opposite-IB targets.

## Findings

The unfiltered NQ baseline was thin: OOS +6.30 points/trade at a 54.1% win rate and 1.12 profit factor, but its earlier discovery period was effectively flat. ES was weaker (negative in discovery).

High relative-volume, early breakouts were the only broadly encouraging continuation family. A representative 0.50 × IB-width stop / 2R target configuration had mean net points per trade of +0.61 (Train), +10.83 (Inner Validation), +10.10 (Validation), and +17.78 (OOS), using the 1-point NQ cost assumption. The family formed a plateau across neighboring geometries rather than one isolated optimum.

However, the apparent signal is not prop-ready. Its median stop grew from 12.1 NQ points in Train to 91.9 points OOS; an uncapped full-size NQ trade can therefore exceed practical evaluation-account risk. Absolute stop caps reduced recent sample sizes sharply and failed to preserve OOS expectancy. This is an unresolved tradability problem, not a sizing detail.

The low-volume re-entry fade failed both Train and Inner Validation. Its attractive recent result is rejected as non-robust. No tested feature provides a sufficiently stable causal rule for automatically switching between continuation and fade.

## Final conclusion

**No live or prop-firm-ready Initial Balance strategy was validated.**

There is a research lead: high-volume, early IB continuation. It warrants future testing only with a prospectively fixed risk model, likely using smaller contracts and account-specific daily/trailing-drawdown rules. It must not be converted into a full-size NQ prop strategy from these historical results.

The correct operational decision today is **no live deployment**. Preserve the high-volume/early continuation hypothesis as a paper-trading candidate; reject the tested fade strategy and all currently tested risk-cap variants.
