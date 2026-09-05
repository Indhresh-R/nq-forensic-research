# NQ Path-Asymmetry Discovery

**Verdict: `B_weak_path_asymmetry`**

Soft path-asymmetry leftovers exist at ~53–56% but fail year-stability and/or are micro-R artifacts (local ATR almost always resolves). Not strategy-ready. Local-ATR +1R resolves ~98% within 15–30m — these are micro path flips, not rare opportunity moments. Structural ONR-R (0.25·ONR) +1R resolves ~78% — the economically larger hurdle. Several aggregate-OOS 'survivors' flip between 2025 and 2026 — demoted from strong.

Prior kills (do not reopen): named strategy · level confirmation · simple state→direction / raw-point magnitude.

---

## Question

> Are there observable states (09:30–11:00) where the future price path is meaningfully asymmetric in R-space — e.g. P(+1R before −1R) ≫ 50% — even when directional accuracy stays near 50%?

## Protocol

| Rule | Implementation |
|------|----------------|
| Clocks T | every 5m from 09:35–11:00 |
| State | bars with `ny_min <= T` only |
| Path start | **next bar open** after T |
| Local R | `max(mean TR 09:30→T, 0.05·ONR, 1pt)` |
| Structural R | `0.25·ONR` (rarer / economically larger) |
| Metrics | MFE≺MAE; P(+0.5R≺−0.5R); P(+1R≺−1R); excursions; time-to-MFE/MAE |
| Ambiguous bar | both sides same 1m → excluded from hit rates |
| Strong bar | also requires 2025 **and** 2026 ≥52% (n≥20) |
| Thresholds | IS terciles frozen |
| Splits | IS 2010–21 / Val 2022–24 / OOS 2025–26 |

Panel: **64,778** rows · **3,600** days.

## Unconditional IS baselines

| T+ | H | n | dir win | local P(+1R≺) | local resolved | onr P(+1R≺) | onr resolved | med local R |
|----|---|---|---------|---------------|----------------|-------------|--------------|-------------|
| +5m | 15 | 2414 | 51.8% | 51.4% | 97.7% | 50.6% | 82.4% | 5.4 |
| +5m | 30 | 2414 | 51.9% | 51.2% | 99.4% | 50.0% | 92.1% | 5.4 |
| +15m | 15 | 2411 | 49.3% | 47.8% | 97.5% | 49.0% | 76.4% | 4.9 |
| +15m | 30 | 2411 | 49.9% | 47.9% | 99.3% | 49.1% | 90.2% | 4.9 |
| +30m | 15 | 2413 | 49.5% | 50.2% | 98.0% | 50.1% | 73.4% | 4.4 |
| +30m | 30 | 2413 | 49.1% | 50.2% | 99.0% | 50.5% | 87.0% | 4.4 |
| +60m | 15 | 2414 | 47.8% | 49.9% | 97.3% | 48.1% | 61.5% | 4.0 |
| +60m | 30 | 2414 | 48.6% | 50.0% | 99.3% | 48.8% | 79.8% | 4.0 |
| +90m | 15 | 2404 | 47.5% | 49.4% | 95.9% | 50.0% | 53.8% | 3.7 |
| +90m | 30 | 2404 | 49.1% | 49.5% | 99.3% | 50.3% | 74.8% | 3.7 |

## Hostile finding on local R

Local-ATR R almost always resolves inside 15–30 minutes. A ~55% P(+0.5R before −0.5R) on that scale is a **microstructure** result, not evidence of rare 1–2/day opportunity structure.

Structural `0.25·ONR` is the harder / more tradable hurdle.

## Candidates

Strong (year-stable): **0** · Soft: **63** · Abs-edge: **0** · Near-coin-dir: **56** · Structural-ONR-R survivors: **34**

| Tier | State | T+ | H | Metric | IS n | IS p | Δunc | dir | Val | OOS | 2025 | 2026 |
|------|-------|----|---|--------|------|------|------|-----|-----|-----|------|------|
| soft | `open_near_ONH` | +80m | 15 | p1onrR_dir | 586 | 56.3% | 3.6pp | 55.1% | 56.6% | 64.3% | 75.0% | 50.0% |
| soft | `open_near_ONH` | +80m | 10 | p1onrR_dir | 586 | 59.0% | 5.6pp | 51.5% | 57.1% | 56.2% | 64.7% | 46.7% |
| soft | `price_near_ONL` | +90m | 30 | mfe_first_dir | 654 | 55.9% | 4.1pp | 44.0% | 57.0% | 57.3% | 62.3% | 47.5% |
| soft | `strong_and_persistent` | +5m | 30 | p0p5onrR_dir | 468 | 55.8% | 3.5pp | 53.8% | 61.6% | 58.8% | 61.5% | 55.2% |
| soft | `strong_and_persistent` | +5m | 10 | p0p5onrR_dir | 468 | 55.7% | 3.3pp | 50.6% | 60.3% | 56.5% | 57.5% | 55.2% |
| soft | `strong_and_persistent` | +5m | 15 | p0p5onrR_dir | 468 | 55.6% | 3.2pp | 52.8% | 60.6% | 58.0% | 60.0% | 55.2% |
| soft | `open_near_ONH` | +90m | 5 | p1onrR_dir | 582 | 56.2% | 5.0pp | 49.8% | 55.6% | 64.7% | 72.7% | 50.0% |
| soft | `wide_ON_quiet_open` | +55m | 10 | p0p5R_dir | 452 | 55.5% | 6.3pp | 51.1% | 55.7% | 57.0% | 67.4% | 42.4% |
| soft | `wide_ON_quiet_open` | +55m | 15 | p0p5R_dir | 452 | 55.2% | 5.8pp | 47.3% | 55.5% | 58.4% | 67.4% | 45.2% |
| soft | `wide_ON_quiet_open` | +55m | 30 | p0p5R_dir | 452 | 55.3% | 6.0pp | 51.1% | 54.9% | 57.9% | 66.7% | 45.2% |
| soft | `strong_and_persistent` | +90m | 5 | p1onrR_dir | 475 | 54.5% | 3.3pp | 47.4% | 54.7% | 67.7% | 64.7% | 71.4% |
| soft | `wide_ON_quiet_open` | +55m | 5 | p0p5onrR_dir | 452 | 54.7% | 4.7pp | 50.9% | 54.4% | 58.5% | 64.0% | 50.0% |
| soft | `open_near_ONH` | +85m | 5 | p1onrR_dir | 586 | 55.3% | 3.3pp | 52.0% | 53.8% | 60.0% | 71.4% | 50.0% |
| soft | `vol_expansion_low` | +25m | 5 | p1onrR_dir | 797 | 60.6% | 6.8pp | 52.4% | 53.8% | 73.9% | 80.0% | 62.5% |
| soft | `strong_and_persistent` | +5m | 5 | p0p5R_dir | 468 | 54.9% | 4.0pp | 55.3% | 59.2% | 53.7% | 55.3% | 51.7% |
| soft | `wide_ON_quiet_open` | +5m | 5 | p1R_dir | 451 | 57.1% | 4.8pp | 54.3% | 53.7% | 62.0% | 66.0% | 52.4% |
| soft | `low_local_vol` | +90m | 30 | p1onrR_dir | 793 | 53.7% | 3.4pp | 50.6% | 53.7% | 54.7% | 51.2% | 60.9% |
| soft | `wide_ON_quiet_open` | +55m | 5 | p0p5R_dir | 452 | 55.5% | 6.3pp | 50.9% | 54.5% | 53.7% | 63.3% | 39.4% |
| soft | `strong_and_persistent` | +5m | 10 | p0p5R_dir | 468 | 55.1% | 4.2pp | 50.6% | 59.5% | 53.6% | 55.0% | 51.7% |
| soft | `low_local_vol` | +25m | 5 | p1onrR_dir | 797 | 62.1% | 8.4pp | 52.7% | 53.6% | 62.5% | 62.5% | 62.5% |

## Quiet / wait structure (IS)

Does `quiet_wait` (low range expansion ∩ weak move) reduce resolution (market says wait)?

| T+ | H | n | Δ local +1R resolved | Δ structural +1R resolved |
|----|---|---|----------------------|---------------------------|
| +5m | 15 | 489 | +0.8pp | -17.0pp |
| +5m | 30 | 489 | +0.4pp | -10.9pp |
| +10m | 15 | 486 | +0.3pp | -18.6pp |
| +10m | 30 | 486 | -0.4pp | -11.4pp |
| +15m | 15 | 486 | -0.1pp | -19.2pp |
| +15m | 30 | 486 | -0.3pp | -12.0pp |
| +20m | 15 | 485 | -0.4pp | -22.2pp |
| +20m | 30 | 485 | -0.1pp | -15.3pp |
| +25m | 15 | 477 | -0.6pp | -22.2pp |
| +25m | 30 | 477 | -0.3pp | -14.9pp |
| +30m | 15 | 480 | -0.1pp | -23.0pp |
| +30m | 30 | 480 | +0.4pp | -15.3pp |

## Stage verdict

**`B_weak_path_asymmetry`**

Soft path-asymmetry leftovers exist at ~53–56% but fail year-stability and/or are micro-R artifacts (local ATR almost always resolves). Not strategy-ready. Local-ATR +1R resolves ~98% within 15–30m — these are micro path flips, not rare opportunity moments. Structural ONR-R (0.25·ONR) +1R resolves ~78% — the economically larger hurdle. Several aggregate-OOS 'survivors' flip between 2025 and 2026 — demoted from strong.

### Hostile notes

- Local-ATR +1R resolves ~98% within 15–30m — these are micro path flips, not rare opportunity moments.
- Structural ONR-R (0.25·ONR) +1R resolves ~78% — the economically larger hurdle.
- Several aggregate-OOS 'survivors' flip between 2025 and 2026 — demoted from strong.

### Explicit non-actions

- Do not optimize R multiples, clocks, or terciles
- Do not convert soft leftovers into a strategy
- Do not reopen direction-prediction with more filters on these states
- Do not treat local-ATR ~55% path flips as 1–2/day edge

## Artifacts

- `artifacts/ny_open_path_asym_panel.parquet`
- `artifacts/ny_open_path_asym_results.csv`
- `artifacts/ny_open_path_asym_report.json`
- `artifacts/ny_open_path_asym_thresholds_IS.json`
- `run_ny_open_path_asymmetry.py`
