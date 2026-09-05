# NQ Structural Opportunity Timing

**Verdict: `A_opportunity_timing_found`**

Causal states reliably reprice P(structural move within H) across IS→Val→OOS and 2025/2026, with multi-clock stability. ONR-matched control preserves the effect. This is a wait/arm gate candidate driven largely by near-term activity persistence — not a directional edge.

**Critical question:** Can we reliably distinguish low- vs high-opportunity periods?

**Answer: YES — with caveats: treat as a gate, not a trade.**

This is a **wait/arm gate** research stage — not a directional edge and not a strategy.

---

## Protocol

| Rule | Implementation |
|------|----------------|
| Clocks T | every 5m from 09:35–11:00 |
| State | bars with `ny_min <= T` only |
| Outcome start | **next bar open** after T |
| Structural resolve | `max(MFE, MAE) ≥ 0.25·ONR` within H (frac pre-specified; sensitivity 0.15/0.35) |
| Horizons | 10 / 15 / 20 / 30 / 45 min |
| Baseline | same-TOD unconditional |
| Strong gate | IS + Val + OOS + 2025 + 2026 same-sign; multi-clock preferred |
| Forbidden | entries, targets, direction, optimization, strategy conversion |

Panel: **64,748** rows · **3,600** days.

## Unconditional IS P(structural resolve) @ 0.25·ONR

| T+ | H10 | H15 | H20 | H30 | H45 |
|----|-----|-----|-----|-----|-----|
| +5m | 72.1% | 82.6% | 87.4% | 92.5% | 95.8% |
| +15m | 65.6% | 76.8% | 84.4% | 90.5% | 94.0% |
| +30m | 61.5% | 73.8% | 80.1% | 87.4% | 92.2% |
| +60m | 48.5% | 61.6% | 70.0% | 79.9% | 88.2% |
| +90m | 40.0% | 53.9% | 63.1% | 75.0% | 83.5% |

## Candidates (primary 0.25·ONR)

Strong: **878** (LOW 363 / HIGH 515) · Soft: **353** · Strong discrimination pairs: **533** · Soft disc: **5**

| Tier | Regime | State | T+ | H | IS n | IS P | Δ | Val Δ | OOS Δ | 2025 Δ | 2026 Δ |
|------|--------|-------|----|---|------|------|---|-------|-------|--------|--------|
| strong | LOW | `wide_ON_quiet_open` | +30m | 10 | 451 | 26.8% | -34.6pp | -25.8pp | -26.0pp | -25.8pp | -24.7pp |
| strong | LOW | `wide_ON_quiet_open` | +80m | 15 | 463 | 22.5% | -34.4pp | -33.9pp | -28.7pp | -28.1pp | -29.8pp |
| strong | LOW | `wide_ON_quiet_open` | +90m | 20 | 464 | 28.7% | -34.4pp | -29.5pp | -27.6pp | -20.7pp | -36.5pp |
| strong | LOW | `wide_ON_quiet_open` | +75m | 15 | 455 | 22.2% | -34.0pp | -30.6pp | -24.4pp | -19.9pp | -29.8pp |
| strong | LOW | `wide_ON_quiet_open` | +85m | 15 | 467 | 20.8% | -33.6pp | -30.2pp | -24.8pp | -19.9pp | -31.1pp |
| strong | LOW | `wide_ON_quiet_open` | +25m | 10 | 442 | 30.3% | -33.3pp | -28.4pp | -27.0pp | -26.5pp | -27.2pp |
| strong | LOW | `wide_ON_quiet_open` | +80m | 20 | 463 | 32.8% | -33.3pp | -32.5pp | -26.1pp | -24.7pp | -28.2pp |
| strong | LOW | `wide_ON_quiet_open` | +40m | 15 | 444 | 33.3% | -33.1pp | -26.4pp | -26.4pp | -22.8pp | -31.1pp |
| strong | LOW | `wide_ON_quiet_open` | +70m | 20 | 455 | 34.3% | -33.0pp | -24.0pp | -27.9pp | -21.1pp | -36.9pp |
| strong | LOW | `low_local_vol` | +75m | 15 | 793 | 23.3% | -32.9pp | -30.3pp | -31.2pp | -34.8pp | -25.7pp |
| strong | LOW | `low_local_vol` | +40m | 15 | 797 | 33.6% | -32.8pp | -29.0pp | -27.5pp | -27.8pp | -27.2pp |
| strong | LOW | `wide_ON_quiet_open` | +45m | 10 | 443 | 19.0% | -32.7pp | -29.1pp | -22.6pp | -21.2pp | -24.0pp |
| strong | LOW | `wide_ON_quiet_open` | +20m | 10 | 438 | 29.5% | -32.2pp | -32.6pp | -23.5pp | -21.7pp | -25.6pp |
| strong | LOW | `low_local_vol` | +30m | 10 | 796 | 29.3% | -32.2pp | -23.2pp | -29.9pp | -25.8pp | -34.7pp |
| strong | LOW | `wide_ON_quiet_open` | +45m | 15 | 443 | 32.7% | -32.0pp | -26.5pp | -20.9pp | -23.0pp | -17.0pp |
| strong | LOW | `low_local_vol` | +35m | 10 | 797 | 25.6% | -32.0pp | -27.7pp | -30.2pp | -29.5pp | -30.9pp |
| strong | LOW | `wide_ON_quiet_open` | +85m | 20 | 467 | 31.3% | -31.9pp | -29.7pp | -26.0pp | -16.8pp | -37.5pp |
| strong | LOW | `wide_ON_quiet_open` | +40m | 10 | 444 | 23.2% | -31.8pp | -28.3pp | -31.4pp | -29.2pp | -34.0pp |
| strong | LOW | `low_local_vol` | +80m | 15 | 793 | 25.1% | -31.8pp | -30.2pp | -30.7pp | -31.5pp | -29.8pp |
| strong | LOW | `low_local_vol` | +55m | 15 | 796 | 31.5% | -31.7pp | -28.0pp | -37.3pp | -40.4pp | -31.9pp |
| strong | LOW | `low_local_vol` | +75m | 20 | 793 | 35.3% | -31.5pp | -31.3pp | -31.0pp | -33.2pp | -27.6pp |
| strong | LOW | `wide_ON_quiet_open` | +55m | 10 | 452 | 19.5% | -31.5pp | -28.9pp | -24.0pp | -25.5pp | -21.4pp |
| strong | LOW | `low_local_vol` | +55m | 10 | 796 | 19.5% | -31.5pp | -25.7pp | -31.6pp | -32.9pp | -29.2pp |
| strong | LOW | `wide_ON_quiet_open` | +70m | 15 | 455 | 26.4% | -31.5pp | -25.7pp | -26.0pp | -23.5pp | -29.2pp |
| strong | LOW | `wide_ON_quiet_open` | +75m | 20 | 455 | 35.4% | -31.4pp | -33.3pp | -25.6pp | -20.5pp | -31.9pp |

## Discrimination: HIGH − LOW opportunity gap

Can the same clock separate a low-opportunity state from a high-opportunity state?

| Tier | Pair | T+ | H | IS gap | Val gap | OOS gap | 2025 | 2026 | IS P(low→high) |
|------|------|----|---|--------|---------|---------|------|------|----------------|
| strong | `low_local_vol` vs `high_local_vol` | +50m | 10 | +62.0pp | +62.4pp | +56.5pp | +55.2pp | +59.0pp | 18.1%→80.0% |
| strong | `low_local_vol` vs `high_local_vol` | +55m | 10 | +61.6pp | +56.1pp | +63.3pp | +60.6pp | +67.7pp | 19.5%→81.1% |
| strong | `low_local_vol` vs `high_local_vol` | +75m | 15 | +61.0pp | +60.8pp | +62.2pp | +64.2pp | +59.2pp | 23.3%→84.4% |
| strong | `low_local_vol` vs `high_local_vol` | +45m | 10 | +61.0pp | +64.5pp | +57.3pp | +58.9pp | +54.9pp | 22.0%→82.9% |
| strong | `low_local_vol` vs `high_local_vol` | +30m | 10 | +60.3pp | +51.9pp | +62.9pp | +56.1pp | +72.0pp | 29.3%→89.5% |
| strong | `low_local_vol` vs `high_local_vol` | +65m | 10 | +60.1pp | +61.6pp | +66.4pp | +64.6pp | +70.1pp | 16.1%→76.2% |
| strong | `low_local_vol` vs `high_local_vol` | +80m | 15 | +60.1pp | +65.1pp | +61.6pp | +60.2pp | +64.8pp | 25.1%→85.2% |
| strong | `low_local_vol` vs `high_local_vol` | +40m | 10 | +60.1pp | +59.5pp | +63.6pp | +63.8pp | +63.9pp | 23.8%→83.9% |
| strong | `low_local_vol` vs `high_local_vol` | +70m | 15 | +60.0pp | +67.3pp | +60.4pp | +58.4pp | +63.9pp | 26.6%→86.6% |
| strong | `low_local_vol` vs `high_local_vol` | +40m | 15 | +59.9pp | +57.3pp | +57.2pp | +56.6pp | +58.5pp | 33.6%→93.5% |
| strong | `low_local_vol` vs `high_local_vol` | +35m | 10 | +59.8pp | +58.0pp | +62.0pp | +56.4pp | +71.9pp | 25.6%→85.4% |
| strong | `low_local_vol` vs `high_local_vol` | +65m | 15 | +59.4pp | +64.6pp | +61.3pp | +58.4pp | +65.8pp | 28.8%→88.2% |
| strong | `low_local_vol` vs `high_local_vol` | +75m | 10 | +59.0pp | +58.3pp | +61.2pp | +59.8pp | +64.0pp | 12.7%→71.8% |
| strong | `low_local_vol` vs `high_local_vol` | +55m | 15 | +58.7pp | +55.4pp | +69.1pp | +70.0pp | +67.2pp | 31.5%→90.2% |
| strong | `low_local_vol` vs `high_local_vol` | +50m | 15 | +58.1pp | +55.2pp | +56.6pp | +56.0pp | +57.1pp | 32.1%→90.3% |
| strong | `low_local_vol` vs `high_local_vol` | +70m | 10 | +58.1pp | +66.8pp | +59.7pp | +53.8pp | +69.6pp | 16.4%→74.5% |
| strong | `low_local_vol` vs `high_local_vol` | +85m | 15 | +57.8pp | +64.3pp | +60.8pp | +65.6pp | +53.3pp | 24.2%→82.0% |
| strong | `low_local_vol` vs `high_local_vol` | +45m | 15 | +57.8pp | +57.9pp | +56.5pp | +56.8pp | +55.5pp | 34.0%→91.8% |
| strong | `low_local_vol` vs `high_local_vol` | +60m | 10 | +57.8pp | +62.3pp | +60.8pp | +64.3pp | +55.3pp | 20.1%→77.8% |
| strong | `low_local_vol` vs `high_local_vol` | +80m | 10 | +57.7pp | +60.6pp | +56.2pp | +56.6pp | +56.3pp | 13.1%→70.8% |

## Clock stability

| State | Regime | H | soft+strong clocks | strong clocks | med IS Δ | med OOS Δ |
|-------|--------|---|--------------------|--------------|---------|-----------|
| `wide_ON_quiet_open` | LOW | 15 | 18 | 18 | -30.5pp | -26.1pp |
| `low_local_vol` | LOW | 15 | 18 | 18 | -30.1pp | -29.6pp |
| `wide_ON_quiet_open` | LOW | 10 | 18 | 18 | -30.1pp | -24.7pp |
| `low_local_vol` | LOW | 10 | 18 | 18 | -29.8pp | -28.9pp |
| `low_local_vol` | LOW | 20 | 18 | 18 | -29.1pp | -29.6pp |
| `wide_ON_quiet_open` | LOW | 20 | 18 | 18 | -28.9pp | -25.8pp |
| `high_local_vol` | HIGH | 10 | 18 | 18 | +28.4pp | +30.0pp |
| `high_local_vol` | HIGH | 15 | 18 | 18 | +26.9pp | +29.2pp |
| `wide_ON_quiet_open` | LOW | 30 | 18 | 18 | -25.1pp | -22.5pp |
| `low_local_vol` | LOW | 30 | 18 | 18 | -24.1pp | -24.4pp |
| `vol_expansion_low` | LOW | 15 | 18 | 18 | -23.9pp | -22.1pp |
| `vol_expansion_low` | LOW | 10 | 18 | 18 | -23.4pp | -21.1pp |
| `high_local_vol` | HIGH | 20 | 18 | 18 | +23.2pp | +23.1pp |
| `quiet_wait` | LOW | 15 | 18 | 18 | -22.9pp | -20.8pp |
| `vol_expansion_low` | LOW | 20 | 18 | 18 | -22.6pp | -19.7pp |

### Discrimination pair stability

| Pair | H | clocks | strong clocks | med IS gap | med OOS gap |
|------|---|--------|---------------|------------|-------------|
| `low_local_vol vs high_local_vol` | 10 | 18 | 18 | +57.9pp | +59.2pp |
| `low_local_vol vs high_local_vol` | 15 | 18 | 18 | +57.3pp | +58.0pp |
| `low_local_vol vs high_local_vol` | 20 | 18 | 18 | +52.8pp | +52.2pp |
| `vol_expansion_low vs vol_expansion_high` | 10 | 18 | 18 | +46.0pp | +47.5pp |
| `quiet_wait vs vol_expansion_high` | 10 | 18 | 18 | +45.0pp | +48.9pp |
| `vol_expansion_low vs vol_expansion_high` | 15 | 18 | 18 | +45.0pp | +48.2pp |
| `quiet_wait vs vol_expansion_high` | 15 | 18 | 18 | +43.7pp | +46.8pp |
| `quiet_wait vs fast_and_expanded` | 10 | 18 | 18 | +43.2pp | +47.2pp |
| `quiet_wait vs fast_and_expanded` | 15 | 18 | 18 | +41.9pp | +45.2pp |
| `low_local_vol vs high_local_vol` | 30 | 18 | 18 | +41.3pp | +42.1pp |

## Sensitivity: `quiet_wait` across structural fracs

| Frac | T+ | H | IS Δ | Val Δ | OOS Δ | 2025 Δ | 2026 Δ |
|------|----|---|------|-------|-------|--------|--------|
| 0.15 | +15m | 15 | -6.9pp | -7.0pp | -4.1pp | -1.1pp | -9.3pp |
| 0.15 | +15m | 30 | -3.9pp | -2.3pp | -2.8pp | -0.2pp | -7.4pp |
| 0.15 | +30m | 15 | -11.1pp | -7.5pp | -15.2pp | -10.2pp | -21.5pp |
| 0.15 | +30m | 30 | -3.4pp | -5.2pp | -7.9pp | -2.1pp | -15.2pp |
| 0.15 | +45m | 15 | -12.0pp | -10.1pp | -16.9pp | -16.9pp | -16.6pp |
| 0.15 | +45m | 30 | -7.0pp | -4.9pp | -5.8pp | -5.9pp | -5.9pp |
| 0.15 | +60m | 15 | -16.2pp | -14.2pp | -15.1pp | -11.3pp | -20.4pp |
| 0.15 | +60m | 30 | -6.9pp | -5.8pp | -14.5pp | -15.2pp | -13.4pp |
| 0.25 | +15m | 15 | -19.4pp | -20.1pp | -8.3pp | -3.1pp | -17.4pp |
| 0.25 | +15m | 30 | -12.1pp | -11.6pp | -9.9pp | -2.8pp | -22.2pp |
| 0.25 | +30m | 15 | -23.4pp | -18.4pp | -23.5pp | -19.7pp | -28.1pp |
| 0.25 | +30m | 30 | -15.7pp | -15.9pp | -18.3pp | -14.8pp | -23.0pp |
| 0.25 | +45m | 15 | -23.6pp | -15.5pp | -24.4pp | -29.4pp | -17.2pp |
| 0.25 | +45m | 30 | -18.7pp | -8.9pp | -20.1pp | -18.0pp | -20.9pp |
| 0.25 | +60m | 15 | -22.1pp | -23.1pp | -16.4pp | -14.2pp | -19.6pp |
| 0.25 | +60m | 30 | -15.5pp | -17.8pp | -17.2pp | -16.7pp | -17.8pp |
| 0.35 | +15m | 15 | -21.6pp | -22.1pp | -22.4pp | -17.1pp | -31.8pp |
| 0.35 | +15m | 30 | -18.7pp | -20.8pp | -15.0pp | -8.0pp | -27.3pp |
| 0.35 | +30m | 15 | -25.8pp | -16.6pp | -25.8pp | -24.7pp | -26.5pp |
| 0.35 | +30m | 30 | -23.7pp | -20.0pp | -28.6pp | -24.9pp | -33.4pp |
| 0.35 | +45m | 15 | -22.4pp | -16.0pp | -19.0pp | -19.6pp | -17.6pp |
| 0.35 | +45m | 30 | -23.1pp | -16.7pp | -24.0pp | -26.6pp | -19.1pp |
| 0.35 | +60m | 15 | -19.7pp | -21.2pp | -18.1pp | -15.7pp | -21.4pp |
| 0.35 | +60m | 30 | -20.1pp | -23.9pp | -24.1pp | -22.7pp | -26.0pp |

## Hostile control: is this just the ONR hurdle?

Concern: `0.25·ONR` is easier on small-ONR days. States like `high_local_vol` (`ATR/ONR` high) partially select small overnight ranges — could inflate discrimination.

**Control:** within IS ONR terciles (matched hurdle size), recompute Δ vs within-bin unconditional.

| State | T+30 H15 raw Δ | ONR-matched median Δ |
|-------|----------------|----------------------|
| `quiet_wait` | −23.4pp | **−20.4pp** |
| `vol_expansion_low` | −22.5pp | **−17.4pp** |
| `low_local_vol` | −27.8pp | **−24.9pp** |
| `high_local_vol` | +21.6pp | **+22.9pp** |
| `wide_ON_quiet_open` | −29.0pp | **−23.6pp** |

Matched deltas shrink modestly but **remain large and same-signed**. Same pattern at T+15/60/90 and H30 (`artifacts/ny_open_opp_timing_onr_matched.csv`).

Interpretation: the gate is largely **near-term activity / vol persistence** under an ONR-scaled hurdle — not a pure overnight-size artifact. That is still valid for WAIT vs ARM. It is **not** evidence of a new directional mechanism.

Preferred gate family (cleaner than pure `vol_unit` labels): **`quiet_wait` / `vol_expansion_low`** (LOW) vs **`vol_expansion_high` / `fast_and_expanded`** (HIGH).

---

## Stage verdict

**`A_opportunity_timing_found`**

Causal states reliably reprice P(structural move within H) across IS→Val→OOS and 2025/2026, with multi-clock stability. ONR-matched control preserves the effect. This is a wait/arm gate candidate driven largely by near-term activity persistence — not a directional edge.

Critical answer: **YES — with caveats: treat as a gate, not a trade.**

### What this is / is not

- **Is:** candidate information for a WAIT vs ARM gate on opportunity size
- **Is not:** a profitable strategy, a direction signal, or proof of edge
- Next (only if A or strong B): keep the gate frozen; search separately for entries

### Explicit non-actions

- Do not optimize STRUCT_FRAC, clocks, or terciles
- Do not convert timing into trades without a separate entry mechanism
- Do not reopen direction-prediction on these states

## Artifacts

- `artifacts/ny_open_opp_timing_panel.parquet`
- `artifacts/ny_open_opp_timing_results.csv`
- `artifacts/ny_open_opp_timing_report.json`
- `artifacts/ny_open_opp_timing_thresholds_IS.json`
- `run_ny_open_opportunity_timing.py`
