# Testing methodology

1. Build Globex daily OHLC from 1m NQ.
2. Run buy-and-hold full-sample + yearly; assert identity vs hand subtract.
3. Compute SMA50/200, log every golden/death cross, simulate long-only next-open fills.
4. Recompute last SMA50/200 with `numpy.mean` — must match pandas rolling.
5. Download `^NDX` via yfinance; compare cross calendars (±10 days).
6. Write artifacts under `artifacts/00_engine_sanity/` and mirror report to `results/full_report.md`.

Pass criterion: `verdict == ENGINE_OK` in `nq_engine_sanity_report.json`.
