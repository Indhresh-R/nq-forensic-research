# NQ HIGH + Cross-Asset (ES) Directional Discovery

**Verdict: `C_no_cross_asset_direction_inside_HIGH`**

Inside frozen HIGH, contemporaneous ES / NQ–ES relative signals do not reliably reprice NQ direction beyond HIGH alone.

Frozen ARM: **`vol_expansion_high`** — untouched. Family: **cross-asset (ES only)**. Volume / multi-scale deferred.

Unavailable this pass: QQQ, SPY, VIX, DXY, yields.

---

## Question

> Inside HIGH, does contemporaneous ES / NQ–ES relative information change NQ's next directional probabilities vs HIGH alone?

Each X independent. No combining. No gate retuning.

## Protocol

| Rule | Implementation |
|------|----------------|
| Universe | HIGH (`vol_expansion_high`) at T with aligned ES bar |
| Cross-asset | ES 1m continuous, same NY session clock |
| Returns | %-returns from 09:30 open → T (NQ and ES) |
| Outcome | NQ next-bar open → H∈{10,15,30}, signed by X |
| Baseline | HIGH alone LONG + FOLLOW |
| Splits | IS / Val / OOS + 2025 / 2026 |

Panel: **19,924** rows · **1,884** days.

## HIGH-alone baselines (sanity)

| Mech | T+ | H | IS win/mean | Val | OOS |
|------|----|---|-------------|-----|-----|
| `HIGH_ALONE_FOLLOW` | +15m | 15 | 51.3%/+0.65 | 53.6%/+1.32 | 55.0%/+8.76 |
| `HIGH_ALONE_LONG` | +15m | 15 | 50.4%/+0.21 | 52.3%/+2.57 | 43.3%/-22.64 |
| `HIGH_ALONE_FOLLOW` | +15m | 30 | 53.0%/+1.26 | 50.0%/+1.41 | 50.8%/+9.46 |
| `HIGH_ALONE_LONG` | +15m | 30 | 50.5%/-0.16 | 55.9%/+1.03 | 42.5%/-22.84 |
| `HIGH_ALONE_FOLLOW` | +30m | 15 | 48.7%/+0.40 | 50.0%/+1.58 | 53.2%/+4.29 |
| `HIGH_ALONE_LONG` | +30m | 15 | 51.3%/-0.53 | 50.5%/-0.59 | 56.3%/+0.41 |
| `HIGH_ALONE_FOLLOW` | +30m | 30 | 47.6%/+0.13 | 48.6%/-3.69 | 50.0%/+3.56 |
| `HIGH_ALONE_LONG` | +30m | 30 | 52.4%/+0.56 | 55.5%/+1.18 | 57.9%/+1.67 |
| `HIGH_ALONE_FOLLOW` | +45m | 15 | 48.8%/-0.21 | 50.5%/-1.11 | 48.0%/-4.94 |
| `HIGH_ALONE_LONG` | +45m | 15 | 55.8%/+0.96 | 50.5%/+0.26 | 44.0%/-5.84 |
| `HIGH_ALONE_FOLLOW` | +45m | 30 | 47.5%/-0.21 | 47.7%/-1.67 | 52.8%/+3.11 |
| `HIGH_ALONE_LONG` | +45m | 30 | 55.2%/-0.06 | 51.4%/-0.19 | 47.2%/-6.61 |
| `HIGH_ALONE_FOLLOW` | +60m | 15 | 45.9%/+0.08 | 49.6%/+1.35 | 55.0%/+7.33 |
| `HIGH_ALONE_LONG` | +60m | 15 | 48.3%/-0.85 | 50.9%/-1.03 | 40.5%/-5.52 |
| `HIGH_ALONE_FOLLOW` | +60m | 30 | 48.0%/-0.37 | 55.7%/+0.93 | 49.6%/+5.15 |
| `HIGH_ALONE_LONG` | +60m | 30 | 52.5%/-0.14 | 48.7%/-0.85 | 47.3%/-4.63 |

## Mechanisms (independent)

| ID | Rule |
|----|------|
| `follow_es` | Trade NQ in direction of ES open→T % return |
| `rs_continue` | NQ % − ES % > 0 → long (relative-strength continuation) |
| `rs_fade` | Opposite of `rs_continue` |
| `es_last5` | Trade NQ in direction of ES last-5m return |
| `agree_nq_es` | Only when NQ and ES same sign; that direction |
| `disagree_follow_es` | Only when signs disagree; follow ES |
| `disagree_follow_nq` | Only when signs disagree; follow NQ |

## Candidates

Strong cells: **0** · Soft: **0** · Multi-clock strong mechanisms: **0**

**None** cleared soft/strong bars.
## Clock stability

No candidate mechanisms.
## Stage verdict

**`C_no_cross_asset_direction_inside_HIGH`**

Inside frozen HIGH, contemporaneous ES / NQ–ES relative signals do not reliably reprice NQ direction beyond HIGH alone.

### Research tree status

```
FROZEN HIGH GATE
   ├── Cross-asset (ES)  → this stage
   ├── Volume shock      → next (only if needed)
   └── Multi-scale       → next (only if needed)
```

### Explicit non-actions

- Do not unfreeze HIGH
- Do not combine cross-asset X with dead NQ price patterns
- Do not start volume/multi-scale until this family is closed
- Do not promote single-clock leftovers

## Artifacts

- `artifacts/frozen_opportunity_gate.md`
- `artifacts/ny_open_high_xasset_panel.parquet`
- `artifacts/ny_open_high_xasset_results.csv`
- `artifacts/ny_open_high_xasset_report.json`
- `run_ny_open_high_cross_asset.py`
