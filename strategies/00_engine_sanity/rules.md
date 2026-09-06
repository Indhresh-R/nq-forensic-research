# Rules — Engine sanity benchmarks

## Data

- Instrument: NQ continuous 1-minute (`data/nq_1m_continuous.parquet`)
- Daily bar: Globex `session_date` day (rolls **18:00 America/New_York**)
- Require ≥ 60 one-minute bars per day

## 1. Buy-and-hold

- Enter long at **first** Globex daily close in sample
- Exit at **last** Globex daily close
- Gross points = `exit_close − entry_close`
- Optional round-trip costs: 0 / 0.5 / 1.0 / 2.0 pts (report mid = 1.0)
- **Pass:** engine gross == hand calc within 1e-9

## 2. SMA 50 / 200 (long-only)

- `SMA_fast` = mean of last 50 daily closes (inclusive)
- `SMA_slow` = mean of last 200 daily closes (inclusive)
- **Golden cross:** prior regime fast≤slow, current fast>slow
- **Death cross:** prior regime fast>slow, current fast≤slow
- Fill: **next Globex day open** after signal close (causal next-bar)
- Flat when not in long regime; force-flat at sample end if still long
- Round-trip cost on each completed round trip: mid **1.0** pt default

## External reference

- Yahoo `^NDX` daily auto-adjusted close, same SMA rules
- Match each NQ Globex cross to nearest same-type ^NDX cross within **10** calendar days
- Expect approximate agreement only (futures roll ≠ cash index)
