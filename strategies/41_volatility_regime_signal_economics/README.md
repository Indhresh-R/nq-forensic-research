# Strategy 41: Volatility Regime × Signal Economics

## Status: **VERDICT C (KILL as Economic Trade Filter)**

Strategy 41 tested whether predictable volatility clustering (Strategy 39) functions as an economic filter that rescues trading signals from transaction friction by expanding available price excursions.

### Core Findings
- **Friction Percentage Drops Modestly**: Fixed 1.0 pt friction consumes 3.13% of 60m excursion in Extreme Vol vs 4.24% in Low Vol.
- **Adverse Excursion Explodes**: While MFE expands, MAE expands faster. In Initial Balance Breakouts, MAE grows from 55.8 pts to 90.1 pts (MFE/MAE ratio degrades from 1.00 to 0.82).
- **Extreme Volatility Worsens Net Dollar Losses**: Extreme Vol produced negative net expectancy across all benchmark signal families (IB Breakout: $-9.47$ pts net, PF 0.775; 15m Drive: $-6.46$ pts net, PF 0.755; Fixed-Clock: $-7.44$ pts net, PF 0.741).
- **Core Lesson**: Higher volatility scales loss variance rather than creating edge; saving 1.0 point on friction is dwarfed by a +30 point expansion in whipsaw loss size.

### Directory Structure
- [PREREGISTRATION.md](PREREGISTRATION.md): Frozen research hypothesis and kill criteria.
- [hypothesis.md](hypothesis.md): Theoretical framing of friction decomposition.
- [rules.md](rules.md): Mathematical definitions and benchmark execution specifications.
- [testing_methodology.md](testing_methodology.md): Chronological splits and validation protocol.
- [conclusion.md](conclusion.md): Final post-mortem and scientific conclusion.
- [code/run_cost_capacity_scan.py](code/run_cost_capacity_scan.py): Layer 1 signal-agnostic cost-capacity scan.
- [code/run_benchmark_stratification.py](code/run_benchmark_stratification.py): Layer 2 benchmark signals stratification.
- [results/full_report.md](results/full_report.md): Tabular reports across IS, Validation, and OOS.
- [results/summary_metrics.json](results/summary_metrics.json): JSON metrics summary.
