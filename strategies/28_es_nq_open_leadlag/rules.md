# Rules — Strategy 28 (FROZEN before look)

## Source

- `data/es_1m_continuous.parquet`, `data/nq_1m_continuous.parquet`
- Same continuous construction as Strategy 27 (Databento OHLCV-1m)
- Sync key: (`session_date`, `ny_min`) inner join; drop unpaired minutes

## Causality

```text
Signal at end of completed bar t (features use only bar ≤ t)
Entry: next bar open on the FOLLOWER book (bar t+1)
Outcomes: path high/low/close on follower bars t+1 .. t+H
No look-ahead: YES
```

`ret_1m` = NaN when prior gap > 1.01 minutes (no ffill across holes/rolls).

## TOD windows (pre-registered)

| ID | `ny_min` range (bar open) | Role |
|----|---------------------------|------|
| `OPEN5` | [09:30, 09:35) | First 5 minutes |
| `OPEN15` | [09:30, 09:45) | First 15 minutes |
| `OPEN30` | [09:30, 10:00) | First 30 minutes |
| `MID` | [11:00, 14:00) | Mid-day **control** |
| `RTH` | [09:30, 16:00) | Full RTH descriptive only |

Signals for Phase 2 scalps are taken **only** when bar `t` is inside the window.

## Phase 1 — lead/lag features (descriptive)

| Feature | Definition |
|---------|------------|
| `es_ret_1m` | ES close_t / close_{t-1} − 1 |
| `nq_ret_1m` | NQ close_t / close_{t-1} − 1 |
| `es_ret_sum5` | sum of last 5 finite ES 1m rets, same session |
| `nq_ret_sum5` | same for NQ |

Spearman of leader_ret_t vs follower_ret over horizons **1, 5, 15, 30** minutes
(forward % return on follower close). Also report **contemporaneous** (h=0) as
contamination check.

## Phase 2 — scalp signals (frozen; no mining)

| ID | Leader → follower | Side |
|----|-------------------|------|
| `es_lead_nq` | ES → NQ | `sign(es_ret_1m)` |
| `nq_lead_es` | NQ → ES | `sign(nq_ret_1m)` |
| `es5_lead_nq` | ES sum5 → NQ | `sign(es_ret_sum5)` |
| `nq5_lead_es` | NQ sum5 → ES | `sign(nq_ret_sum5)` |

Skip when side = 0 or leader ret NaN.

### Scalp economics (NQ follower)

| Parameter | Frozen values |
|-----------|---------------|
| Target | **+20, +25, +30** NQ points |
| Stop | **−target** (strict 1:1) |
| Time stop H | **15, 30** minutes |
| Cost | **1.0** NQ point round-turn (deducted from PnL) |

### Scalp economics (ES follower)

| Parameter | Frozen values |
|-----------|---------------|
| Target | **+8, +10, +12** ES points (~$ similar to 20/25/30 NQ) |
| Stop | **−target** |
| Time stop H | **15, 30** minutes |
| Cost | **0.50** ES point round-turn |

Path rule: first touch of stop or target on bar high/low wins; if both in same
bar → **stop first** (hostile). Else exit at time-stop close.

## Splits

| Split | Years |
|-------|-------|
| Discovery | 2010–2021 |
| Validation | 2022–2024 |
| OOS | 2025–2026 |

No Discovery threshold fitting — all parameters frozen above.

## Hard bans

- No ORB / EMA / Fib / gamma / overnight RS
- No combining signals; no retuning targets after look
- No Strategy-12 HIGH required (optional descriptive attachment only if cheap)
- Do not promote from Discovery alone
