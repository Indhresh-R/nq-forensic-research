# E2 — Scheduled Information Events → NQ Intraday Direction (NO HIGH)

**Classification: `C`** — No persistent directional asymmetry from CPI/NFP/FOMC/PPI/CLAIMS (impulse cont/fade, surprise, and event-long all fail vs 50% and/or same-TOD control).

Kill scheduled-events family: **True**. Events tested **separately**. ISM unavailable in source calendar. No HIGH. Not a vol/opportunity test.

Frozen: impulse=5m after release; mechanisms=cont/fade/surprise/long; surprise maps={'CPI': -1, 'PPI': -1, 'NFP': -1, 'CLAIMS': -1, 'FOMC': -1}.

Strong cells: 0 · Soft: 0 · Multi-horizon strong: 0

## Per-event IS summary (median across horizons)

| Event | Mechanism | med n | win | Δ50 | Δctrl | mean z | MFE>MAE | P(+1R≺) |
|-------|-----------|-------|-----|-----|-------|--------|---------|---------|
| `PPI` | `impulse_fade` | 100 | 45.0% | -5.0pp | -4.4pp | -0.407 | 46.0% | 50.0% |
| `PPI` | `surprise_dir` | 83 | 45.8% | -4.2pp | — | -0.174 | 48.2% | 44.0% |
| `PPI` | `impulse_cont` | 100 | 53.0% | +3.0pp | +5.4pp | +0.407 | 53.0% | 50.0% |
| `NFP` | `evt_long` | 102 | 52.9% | +2.9pp | +4.0pp | -0.186 | 50.0% | 56.6% |
| `CLAIMS` | `impulse_cont` | 447 | 47.3% | -2.7pp | +0.1pp | -0.167 | 48.3% | 47.2% |
| `NFP` | `surprise_dir` | 101 | 47.5% | -2.5pp | — | -0.259 | 45.0% | 48.0% |
| `NFP` | `impulse_cont` | 102 | 47.5% | -2.5pp | +1.2pp | -0.667 | 47.1% | 53.9% |
| `CLAIMS` | `evt_long` | 447 | 47.8% | -2.2pp | -1.2pp | -0.356 | 47.1% | 48.3% |
| `CPI` | `surprise_dir` | 64 | 48.4% | -1.6pp | — | -0.207 | 52.3% | 63.1% |
| `CPI` | `impulse_cont` | 103 | 48.5% | -1.5pp | +2.3pp | +0.174 | 49.5% | 53.6% |
| `NFP` | `impulse_fade` | 102 | 51.0% | +1.0pp | +1.0pp | +0.667 | 51.5% | 46.1% |
| `CLAIMS` | `surprise_dir` | 433 | 49.3% | -0.7pp | — | +0.072 | 49.7% | 51.6% |
| `CPI` | `impulse_fade` | 103 | 50.5% | +0.5pp | -0.6pp | -0.174 | 49.0% | 46.4% |
| `CLAIMS` | `impulse_fade` | 447 | 49.8% | -0.2pp | +0.7pp | +0.167 | 50.4% | 52.8% |
| `CPI` | `evt_long` | 103 | 50.0% | +0.0pp | +1.9pp | +0.262 | 48.5% | 46.9% |
| `PPI` | `evt_long` | 100 | 50.0% | +0.0pp | +1.2pp | -0.316 | 50.0% | 52.3% |

## Surviving cells

None.

## Stability (horizons stand in for clocks)

n/a

## Final: **C**

**Kill scheduled-information-events family.** Do not combine dead events.

This was the last major fundamentally different information family queued. Reconsider whether a short-horizon **directional engine** is realistic given: OHLC ❌, EOD options ❌, scheduled events ❌, while frozen HIGH opportunity timing ✅.
HIGH remains untouched (timing only).
