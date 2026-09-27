# Strategy 40: Volatility Persistence → Directional Distribution

## Status: **VERDICT C (Scientific Boundary Established: Volatility Is Predictable, Direction Is NOT)**

Strategy 40 investigated whether the volatility clustering confirmed in Strategy 39 provides any conditional directional information (momentum, mean reversion, tail asymmetry, or excursion bias) across continuous NQ futures.

### Core Findings
- **Directional Continuation is a Coin Flip (45%–50%)**: High-volatility states do not persist directionally (continuation rate 45.3% for high vol, 44.8% for extreme vol).
- **Tail Variance Expands Symmetrically**: Large up moves (9.9%) and large down moves (9.4%) occur with nearly equal frequency under extreme volatility (+0.5% spread).
- **Excursions Expand Symmetrically**: Mean upside excursion (0.653 ATR) matches downside excursion (0.651 ATR) to within +0.002 ATR.
- **Directional Instability**: Directional follow-through after high volatility flips signs across out-of-sample periods (-151 pts in 2025 vs +132 pts in 2026).

### Directory Structure
- [PREREGISTRATION.md](PREREGISTRATION.md): Frozen research hypothesis and kill criteria.
- [hypothesis.md](hypothesis.md): Theoretical framing and decoupling of "WHEN" from "WHICH WAY".
- [rules.md](rules.md): Mathematical definitions and feature engineering specifications.
- [testing_methodology.md](testing_methodology.md): Chronological splits and statistical tests.
- [conclusion.md](conclusion.md): Final programmatic post-mortem and scientific boundary.
- [code/run_volatility_direction_scan.py](code/run_volatility_direction_scan.py): Scan execution script.
- [results/full_report.md](results/full_report.md): Detailed tabular report across IS, Validation, and OOS.
- [results/summary_metrics.json](results/summary_metrics.json): JSON metrics and baseline splits.
