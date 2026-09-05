# Data Specification

## Primary series

| Item | Spec |
|------|------|
| Instrument | NQ futures continuous 1-minute |
| Typical path | `nq_1m_continuous.parquet` (repo root) |
| Timezone | America/New_York for session logic |
| RTH focus | 09:30–16:00 (research windows vary by dossier) |
| Overnight | Used for ONH/ONL/ONR where defined |

## Derived

| Feature | Definition (see `run_ny_open_path_asymmetry.py`) |
|---------|--------------------------------------------------|
| ONR | Overnight range used as scale |
| rng_onr | Session range from 09:30→T divided by ONR |
| Structural opportunity | max excursion from next open >= `0.25 * ONR` within H |

## External

| Source | Use |
|--------|-----|
| QQQ EOD options (`d:\NQ\...`) | E1 options direction (lagged) |
| FRED/Investing macro events JSON | E2 scheduled events |

Secrets: never commit API keys or live credentials.
