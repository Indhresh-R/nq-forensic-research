# Common helpers

Shared primitives for strategy dossiers. Import from repo root on `sys.path`
(strategy scripts under `strategies/*/code/` bootstrap this automatically).

| Module | Role |
|--------|------|
| `paths.py` | `ROOT`, `ART`, `DATA`, `STRATEGIES` |
| `splits.py` | IS / Val / OOS year sets + `split_of` |
| `nq_session.py` | `load_nq`, `load_es`, `build_day_context`, `state_at_T`, `win_rate`, `rate_of` |
| `sessions.py` | Frozen Asia/London/NY_AM/NY_PM clock, `psr`, `state_at_T_session` |

```python
from common.nq_session import ART, load_nq, state_at_T, build_day_context
```

Market data lives under `data/` (`nq_1m_continuous.parquet`, `es_1m_continuous.parquet`).
