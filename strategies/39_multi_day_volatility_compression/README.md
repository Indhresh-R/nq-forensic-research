# Strategy 39: Multi-Day Volatility Compression → RTH Expansion & Persistence

## Status: **VERDICT C (KILL at Information Gate)**

Strategy 39 investigated whether slow-moving multi-day volatility compression states known prior to the RTH open condition subsequent RTH session range expansion, excursion magnitude, directional efficiency, or clean trend-day probability.

### Core Findings
- **Volatility Clusters (Inertia)**: Rather than exploding into trend days, compression regimes systematically precede continued low-volatility sessions (4+ days compression yields 10.5% expansion probability vs 33.0% for uncompressed).
- **NR7 Patterns Precede Smaller Ranges**: After an NR7 day, subsequent range is 16% smaller than normal (0.881 vs 1.053 normalized) and trend day probability drops from 20.9% to 14.6%.
- **Directional Efficiency Is Invariant**: Directional path efficiency remains flat at 0.46–0.49 across all compression regimes.

### Directory Structure
- [PREREGISTRATION.md](PREREGISTRATION.md): Frozen research hypothesis and kill criteria.
- [hypothesis.md](hypothesis.md): Theoretical framing and decoupling of "WHEN" from "WHICH WAY".
- [rules.md](rules.md): Mathematical definitions and feature engineering specifications.
- [testing_methodology.md](testing_methodology.md): Chronological splits and validation protocol.
- [conclusion.md](conclusion.md): Final post-mortem and scientific summary.
- [code/run_volatility_compression_scan.py](code/run_volatility_compression_scan.py): Scan execution script.
- [results/full_report.md](results/full_report.md): Detailed tabular report across IS, Validation, and OOS.
- [results/summary_metrics.json](results/summary_metrics.json): JSON metrics and baseline splits.
