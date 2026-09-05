# NQ HIGH-conditional Directional Discovery

**Verdict: `B_weak_directional_inside_HIGH`**

Soft / single-clock directional leftovers exist inside HIGH, but nothing clears a multi-clock year-stable bar. Gate remains frozen; directional layer still missing.

Frozen ARM: **`vol_expansion_high`** (see `artifacts/frozen_opportunity_gate.md`). Gate was **not** re-tuned.

---

## Question

> Inside HIGH only, does independent X create directional asymmetry beyond HIGH alone?

Each X tested separately. No combinations. Hierarchy: causal → stable → meaningful.

## Protocol

| Rule | Implementation |
|------|----------------|
| Universe | rows where `vol_expansion_high` at T |
| Clocks | every 5m from 09:40–11:00 |
| Baseline | HIGH alone LONG + HIGH alone FOLLOW (`dir_sign`) |
| Outcome | next-bar open → H∈{10,15,30} signed by X direction |
| Compare | HIGH+X win/mean vs HIGH FOLLOW at same T,H |
| Splits | IS / Val / OOS + 2025 / 2026 |

HIGH panel: **19,941** rows · **1,885** days with ≥1 HIGH clock.

## HIGH-alone baselines

| Mech | T+ | H | IS win / mean | Val | OOS |
|------|----|---|---------------|-----|-----|
| `HIGH_ALONE_FOLLOW` | +15m | 15 | 51.3% / +0.65 | 53.6% / +1.32 | 55.0% / +8.76 |
| `HIGH_ALONE_LONG` | +15m | 15 | 50.3% / +0.21 | 52.3% / +2.57 | 43.3% / -22.64 |
| `HIGH_ALONE_FOLLOW` | +15m | 30 | 53.0% / +1.27 | 50.0% / +1.41 | 50.8% / +9.46 |
| `HIGH_ALONE_LONG` | +15m | 30 | 50.4% / -0.17 | 55.9% / +1.03 | 42.5% / -22.84 |
| `HIGH_ALONE_FOLLOW` | +30m | 15 | 48.8% / +0.41 | 50.0% / +1.58 | 53.2% / +4.29 |
| `HIGH_ALONE_LONG` | +30m | 15 | 51.3% / -0.54 | 50.5% / -0.59 | 56.3% / +0.41 |
| `HIGH_ALONE_FOLLOW` | +30m | 30 | 47.7% / +0.14 | 48.6% / -3.69 | 50.0% / +3.56 |
| `HIGH_ALONE_LONG` | +30m | 30 | 52.4% / +0.54 | 55.5% / +1.18 | 57.9% / +1.67 |
| `HIGH_ALONE_FOLLOW` | +45m | 15 | 48.9% / -0.20 | 50.5% / -1.11 | 48.0% / -4.94 |
| `HIGH_ALONE_LONG` | +45m | 15 | 55.7% / +0.95 | 50.5% / +0.26 | 44.0% / -5.84 |
| `HIGH_ALONE_FOLLOW` | +45m | 30 | 47.4% / -0.21 | 47.7% / -1.67 | 52.8% / +3.11 |
| `HIGH_ALONE_LONG` | +45m | 30 | 55.2% / -0.06 | 51.4% / -0.19 | 47.2% / -6.61 |
| `HIGH_ALONE_FOLLOW` | +60m | 15 | 45.9% / +0.07 | 49.6% / +1.35 | 55.0% / +7.33 |
| `HIGH_ALONE_LONG` | +60m | 15 | 48.4% / -0.84 | 50.9% / -1.03 | 40.5% / -5.52 |
| `HIGH_ALONE_FOLLOW` | +60m | 30 | 47.9% / -0.39 | 55.7% / +0.93 | 49.6% / +5.15 |
| `HIGH_ALONE_LONG` | +60m | 30 | 52.6% / -0.13 | 48.7% / -0.85 | 47.3% / -4.63 |

## Mechanisms tested (independent)

- `impulse_follow`
- `vwap_side`
- `or5_accept`
- `or5_reject`
- `structure_hhhl`
- `on_open_continue`
- `on_open_fade`
- `loc_now_continue`
- `loc_now_fade`
- `impulse_pullback`

## Candidates

Strong: **2** · Soft: **1**

> **Hostile note:** both “strong” cells are **single-clock** (`T+80` / `T+85` only). That fails the stability hierarchy even though year splits look fine. Treat as **not promotable**. Soft `loc_now_fade` is also one clock and ~52% IS — kill for strategy use.

| Tier | X | T+ | H | IS n | IS win | Δfollow | Val | OOS | 2025 | 2026 |
|------|---|----|---|------|--------|---------|-----|-----|------|------|
| strong | `on_open_continue` | +85m | 15 | 281 | 56.2% | +10.1pp | 53.5% | 59.6% | 60.0% | 59.1% |
| strong | `on_open_continue` | +80m | 30 | 283 | 53.7% | +8.1pp | 54.8% | 59.6% | 61.5% | 57.1% |
| soft | `loc_now_fade` | +50m | 10 | 640 | 51.6% | +4.4pp | 50.3% | 54.0% | 54.0% | 54.1% |

## Clock stability

| X | H | clocks | strong clocks | med IS win | med Δfollow | med OOS win |
|---|---|--------|---------------|------------|-------------|-------------|
| `on_open_continue` | 15 | 1 | 1 | 56.2% | +10.1pp | 59.6% |
| `on_open_continue` | 30 | 1 | 1 | 53.7% | +8.1pp | 59.6% |
| `loc_now_fade` | 10 | 1 | 0 | 51.6% | +4.4pp | 54.0% |

## Stage verdict

**`B_weak_directional_inside_HIGH`**

Soft / single-clock directional leftovers exist inside HIGH, but nothing clears a multi-clock year-stable bar. Gate remains frozen; directional layer still missing.

### Architecture status

```
09:30–11:00 → HIGH? → NO: WAIT / YES: ARM
             → independent X? → (this stage)
             → mechanical execution → (not yet)
```

### Explicit non-actions

- Do not unfreeze or re-optimize the HIGH gate
- Do not combine X mechanisms until each clears alone
- Do not convert soft leftovers into a strategy
- Do not demand 60%+ win rate; demand stability first

## Artifacts

- `artifacts/frozen_opportunity_gate.md`
- `artifacts/frozen_opportunity_gate.json`
- `artifacts/ny_open_high_dir_panel.parquet`
- `artifacts/ny_open_high_dir_results.csv`
- `artifacts/ny_open_high_dir_report.json`
- `run_ny_open_high_directional.py`
