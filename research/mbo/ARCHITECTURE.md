# MBO research architecture

Engine version: `REPLAY_ENGINE_V2_TIMESTAMP_CORRECT`

This is research infrastructure. It is not a trading strategy.

## Data flow

```text
RAW MBO  data/mbo_full_state_50/mbo_YYYY-MM-DD.dbn.zst
   |
   |  one trading day at a time, then the file is released
   v
L3 REPLAY  research/mbo/engine.py
   |  LimitOrderBook from common/order_book.py
   |  clock from research/mbo/clock.py
   v
NORMALIZED PARQUET
   data/mbo_research/v2/snapshots/date=YYYY-MM-DD/snapshots.parquet
   data/mbo_research/v2/trades/date=YYYY-MM-DD/trades.parquet
   |
   |  no raw MBO
   v
FEATURES  research/mbo/features.py
   data/mbo_research/v2/features/date=YYYY-MM-DD/features.parquet
   |
   v
MECHANISM TABLE  research/mbo/mechanism.py
   predefined size buckets and horizons
   |
   v
HYPOTHESIS RESEARCH
   read Parquet or DuckDB views: snapshots, trades, features
   |
   v
STRATEGY RESEARCH
   not implemented here
   starts only after a mechanism result survives the protocol
```

Ordinary hypothesis tests must not open `data/mbo_full_state_50`.

## Timestamp audit

The rejected assignment, which was in `strategies/44_mbo_orderflow/code/replay_mbo.py` before the clock fix, was:

```text
idx = (ts_event - open_ns) // 1_000_000_000
```

1. Event timestamps are `ts_event` on each Databento MBO record.
2. Trade bins are the one-second rows written by the replay. `trade_b_1s` and `trade_a_1s` count aggressive trades (`action == T`) whose `ts_event` falls in that row.
3. A book snapshot at grid time `t` is the book after every record with `ts_event <= t` has been applied. `action T` and `action F` do not change resting size. Adds, cancels, modifies, and clears do.
4. Floor division maps `[t, t+1s)` onto the row stamped `t`. The forward return `mid[t+1s] - mid[t]` is then the move caused by trades that are already inside the feature.
5. The correct convention is the other edge. Row `t` contains `(t-1s, t]`. An event at `t + 999ms` belongs to row `t+1s`.
6. The fix is `snapshot_bin_index` in `research/mbo/clock.py`. The replay flushes a grid row before applying any later event, so the book on that row cannot contain a future trade. `flow_max_ts_ns <= ts_ns` is checked on write. Forward returns are `mid` shifted by a positive number of grid steps, and the feature builder rejects a future timestamp that is not strictly later.

The leaked comparison (about +1.59 net points, 26/26 days) and the column-shift comparison (about -1.22 net points, 0/26 days) are not evidence. The column shift was applied on top of the old bins. It is not this engine.

Strategy 44's sampler now calls the same `snapshot_bin_index`. Its signal rules were not changed.

## Replay semantics

- Version string: `REPLAY_ENGINE_V2_TIMESTAMP_CORRECT`.
- Session grid: `[09:30, 12:00)` America/New_York. The 12:00 bar is not included. In July and August 2026 this is 13:30-16:00 UTC and matches the existing H01 sample clock.
- Step: 1 second. 9,000 rows per session.
- Warmup: the file is read from the start, including the Databento snapshot (`F_SNAPSHOT` / `F_LAST`), so the 09:30 book is not empty. Snapshot records are not flow.
- Processing stops at the first event after the last grid time. Later events are not needed for this window.
- One day is replayed, written, and dropped. Days are not concatenated in memory.
- Running the same records twice is deterministic. Replaying a day in two sequential chunks matches one pass.

## Normalized schema

Prices are index points (`raw / 1e9`). Sizes are contracts. Timestamps are nanoseconds.

Snapshot row `t` is known at `t`. It does not contain a forward return. Field list: `research/mbo/schema.py` `SNAPSHOT_FIELDS`.

Trade row observation time is `ts_event`. `mid_px`, `bid_px`, and `ask_px` are the book after events with `ts_event` less than or equal to that trade. `distance_from_mid = price - mid_px`. Field list: `TRADE_FIELDS`.

Not stored, on purpose:

- Every add, cancel, and modify as its own row. Those actions are summed on the snapshot. Storing them again would copy raw MBO.
- Order lifetime. The book does not keep a birth timestamp. Lifetime is a later feature, not part of this replay.
- Forward returns on the trade file. Those are joined from a later snapshot.

## Feature schema

`build_features` reads one snapshot partition.

- `cvd_1s`, `cvd_5s`, `cvd_15s`, `cvd_60s`: sums of completed bins ending at `ts_ns`. The first incomplete windows are null. Nothing is backfilled.
- `add_net_1s`, `cancel_net_1s`.
- `fwd_ret_{k}s` for `k` in 1, 5, 15, 30, 60, 120, 300, 600, 900. Definition: `mid[t+k] - mid[t]`. The builder checks that the future grid timestamp is at least `k` seconds after `t`.

## Partition layout

```text
data/mbo_research/v2/snapshots/date=YYYY-MM-DD/snapshots.parquet
data/mbo_research/v2/trades/date=YYYY-MM-DD/trades.parquet
data/mbo_research/v2/features/date=YYYY-MM-DD/features.parquet
data/mbo_research/v2/logs/replay.jsonl
```

Parquet, zstd, one day per directory. DuckDB views `snapshots`, `trades`, and `features` read those globs with hive partitioning. Select columns in SQL instead of loading every field.

## Memory

The resident set is one book plus one day's rows. The book is the large object: every resting order from the session warmup. The next day constructs a new `ReplaySession`. Do not parallelize this replay until a measured run shows the memory headroom. The default runner is one day after another.

## Reproducibility

From the repository root:

```text
python -m unittest research.mbo.tests.test_clock research.mbo.tests.test_forward research.mbo.tests.test_partition research.mbo.tests.test_determinism
python -m research.mbo.replay_day --date 2026-07-08
python -m research.mbo.replay_day --all-is
python -m research.mbo.features
python -m research.mbo.benchmark 2026-07-08
```

`--force` on the replay rebuilds a day that is already written. Features skip existing files unless `--force` is passed.

## Mechanism grid

Documented before any run, in `research/mbo/grid.py`:

- Size, half-open: `[50, 90)`, `[90, 130)`, `[130, 170)`, `[170, 200)`, `[200, inf)`.
- Horizons, seconds: 1, 5, 15, 30, 60, 120, 300, 600, 900.
- Sides: B, A, and ALL. ALL is the pool, not a chosen side.
- Hit: buy aggressor and forward return `> 0`, or sell aggressor and forward return `< 0`.
- The table keeps every cell, including `n = 0`. It is not sorted by return.

`run_predefined_grid` reads the normalized partitions. It does not open raw MBO.

## Benchmark

Measured by `python -m research.mbo.benchmark 2026-07-08` on the corrected engine. One session, then the process exits.

| | 2026-07-08 |
|---|---:|
| Events applied | 20,503,806 |
| Trades written | 148,329 |
| Snapshot rows | 9,000 |
| Time | 249 s |
| Events/sec | 82,199 |
| Peak RSS | 236 MB |
| Normalized output | 3.0 MB |
| Raw MBO file | 403 MB |

The output is smaller than the raw file because the store keeps one-second book rows and trade rows, not every add and cancel. Peak RSS is one book, not the raw file.

Against the already corrected strategy-44 files for this date: aggressor buy size and sell size match on all 9,000 rows, and the reconstructed mid matches the H01 mid with maximum absolute error 0.

Linear estimate from this day, sequential, one day in memory at a time. Not a 9-year run.

| Span | Sessions | Hours | Normalized disk | Raw MBO | Peak RAM |
|---|---:|---:|---:|---:|---:|
| 26 sessions | 26 | 1.8 | 0.08 GB | ~10 GB | 236 MB |
| 3 months | 63 | 4.4 | 0.19 GB | 25 GB | 236 MB |
| 6 months | 126 | 8.7 | 0.37 GB | 50 GB | 236 MB |
| 1 year | 252 | 17.5 | 0.75 GB | 99 GB | 236 MB |
| 5 years | 1,260 | 87 | 3.7 GB | 495 GB | 236 MB |
| 9 years | 2,268 | 157 | 6.7 GB | 892 GB | 236 MB |

One year is practical. Nine years is a few machine-weeks of replay and under 10 GB of normalized output, if the raw files exist. Do not start that replay until a hypothesis needs those dates. The 26-session raw files are the current disk set.

## Known limitations

- The research window is 09:30-12:00 New York, not the full Globex session.
- Order lifetime and queue position are not in the normalized store.
- `action F` is counted as flow and does not change the book. The cancel does.
- The old strategy-44 feature file still backfills `vol_15m` and the absorption percentile. That file is not this store. This store does not backfill.
- A full 26-session information rerun of H02-A through H02-D has not been done on this engine. The frozen taker rule was rerun only on the corrected bins inside strategy 44.
- Trade `size` is the MBO print size. On 2026-07-08 the median print is 1 contract and only 3 prints are 50 or larger, so the predefined 50+ buckets are almost empty. A sweep total (prints sharing one `ts_event`) can be built later from the trade partition. It does not require another raw replay.
