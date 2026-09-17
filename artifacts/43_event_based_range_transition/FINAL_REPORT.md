# Strategy 43: Event-Based Compression → Range → Breakout → Pullback

**Final verdict: REJECTED.** The framework does not produce a robust, mechanically testable NQ edge under sequential detection, next-minute fills, adverse stop handling, and 1.0-point round-trip friction.

## Design integrity

Ranges were detected from only completed one-minute bars and frozen immediately. The detector was not tied to the NY open: it could trigger throughout the RTH signal window. A breakout permanently disabled range fading, and continuation required a later pullback plus a new one-minute directional confirmation. No future range boundary, future session outcome, trailing parameter, indicator, or OOS result entered a signal.

The frozen 12-cell detector grid was ranked solely on 2010–2018. The selected cell, `N=15`, `range/ATR20<=2.5`, was the least-negative selection result—not a profitable optimum.

## Parameter robustness: broad rejection, not a fragile peak

All 12 selection-period combined cells lost money after costs:

| N | thresholds tested | combined expectancy range, points/trade |
| --- | --- | ---: |
| 8 | 2.5, 3.5, 4.5 | -1.12 to -0.95 |
| 10 | 2.5, 3.5, 4.5 | -1.04 to -0.91 |
| 12 | 2.5, 3.5, 4.5 | -1.05 to -0.90 |
| 15 | 2.5, 3.5, 4.5 | -1.24 to -0.74 |

This is a broad null rather than an isolated parameter failure. No trailing-stop or management variation is warranted.

## Frozen selected-cell results

`N=15`, threshold `2.5`; fixed fade target at the opposite range edge and 1.5R continuation target.

| Period | Arm | Trades | Avg R | PF | Net expectancy (pts) |
| --- | --- | ---: | ---: | ---: | ---: |
| Selection 2010–18 | Fade | 2,149 | -4.45 | 0.13 | -0.85 |
| Selection 2010–18 | Continuation | 1,408 | -0.28 | 0.64 | -0.57 |
| IS confirmation 2019–21 | Fade | 1,081 | -1.44 | 0.33 | -0.54 |
| IS confirmation 2019–21 | Continuation | 666 | -0.11 | 0.83 | -1.51 |
| Validation 2022–24 | Fade | 1,091 | -1.01 | 0.40 | -0.79 |
| Validation 2022–24 | Continuation | 696 | -0.00 | 1.00 | -1.42 |
| OOS 2025–26 | Fade | 569 | -0.83 | 0.42 | -3.07 |
| OOS 2025–26 | Continuation | 374 | -0.02 | 0.97 | +0.81 |

The OOS continuation point expectancy is superficially positive, but its average R is negative, its PF is below 1, and all pre-OOS confirmation periods fail. It is not evidence of an edge.

Combined strategy expectancy is negative in every period: -0.74 (selection), -0.91 (IS confirmation), -1.03 (Validation), and -1.53 points/trade (OOS).

## State diagnostics

- Detected sequential ranges: **5,631**; mean width **20.22 points**, **2.32 ATR**.
- Confirmed expansion breakouts: **5,562** (2,868 upside / 2,694 downside).
- Pullback-to-continuation conversions: **3,144**, or **56.5%** of breakouts.

The state transition is observable and occurs frequently. It simply does not generate positive economics under the specified mechanics. Range-edge fading is the decisive failure; pullback continuation does not compensate for it.

## Required comparisons and decision

- **A. Range fading alone:** rejected across selection, IS confirmation, Validation, and OOS.
- **B. Breakout → pullback → continuation alone:** negative/flat R in every split; rejected.
- **C. Combined state strategy:** negative in every split; rejected.

No further filters, indicators, trailing stops, direction bias, or re-entry logic will be tested as a rescue. The finding is not that all discretionary range reading is impossible; it is that this price-only, event-based compression→fade→breakout→pullback framework fails the specified mechanical baseline.

## Audit outputs

- `parameter_surface.csv` — all 12 preregistered cells.
- `selected_trades.csv` — causal fills/exits and R for the frozen selected cell.
- `selected_summary.csv` — split × arm metrics.
- `yearly_results.csv` — annual trade count and performance results.
- `ranges.csv`, `breakouts.csv`, `diagnostics.json` — state diagnostics.
