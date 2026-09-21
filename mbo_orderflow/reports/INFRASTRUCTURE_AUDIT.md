# MBO infrastructure audit

Status: PASS

`REPLAY_ENGINE_V2_TIMESTAMP_CORRECT` is frozen. The crossed-book check did not change the replay engine, did not drop rows, and did not read the volume-profile dataset.

```text
MBO INFRASTRUCTURE V2

[PASS] session coverage
[PASS] file completeness
[PASS] timestamp monotonicity
[PASS] snapshot clock integrity
[PASS] trade → prior-book causality
[PASS] trade aggregation reconciliation
[PASS] deterministic rebuild
[PASS] trade classification
[PASS] spot checks
[PASS] crossed-book investigation
[PASS/NA] 09:30–12:00 window specification
```

The 09:30–12:00 New York window is the declared execution window: 9,000 one-second states per session. It is not incomplete CME data. The replay is not being expanded to 18:00–17:00. Previous-session volume profile, if used later, is built separately. It is not joined here.

Information tests were not run. Next step is information-only MBO tests. Previous-session POC stays out until after that.

## Coverage

- Expected sessions: 26
- Sessions in the coverage table: 26
- Snapshot files present: 26
- Trade files present: 26
- Problems: none

## Timestamp and book

- Snapshot rows whose step is not 1 second: 0
- Snapshots whose flow timestamp is after the row clock: 0
- Trades credited to a snapshot clocked before the trade: 0
- Trade-size bins that do not match `trade_b_1s` / `trade_a_1s`: 0
- Backward trade timestamps: 0
- Backward sequence numbers: 0
- Crossed books (bid > ask): 25. Explained from the raw feed. Rows kept.
  - 2026-07-10 10:32:42–10:32:56 New York, 15 seconds, cross 40 to 147 points.
  - 2026-07-13 10:16:46–10:16:50 New York, 5 seconds, cross 86 to 117 points.
  - 2026-08-11 09:46:02–09:46:06 New York, 5 seconds, cross 60.25 points.
  - Cause: the feed publishes Add records, and on 2026-07-13 a Modify, that rest ask orders below the best bid and bid orders above the best ask. Same instrument (42004177). No bad-book flag, no clear, no timestamp reversal, no same-timestamp sequence reversal, no orphan cancel or modify. The second before each burst is a normal spread. The second after is uncrossed again.
  - The replayed book matches stored bid, ask, and size on every one of those seconds and on the neighboring seconds. Detail is in `CROSSED_BOOKS.md`.
  - These 25 mids are averages of a crossed book. Later tests have to declare how they treat that state. They are not dropped here.
- Locked books (bid = ask): 0
- Negative sizes: 0
- Prices outside 1000 to 100000: 0

Sequence numbers are checked for order, not for a gapless counter. A missing sequence between trades is expected because adds and cancels are not in the trade file.

## Trade classification

- Aggressive buy (side B, lifts the ask): 2149409 (0.4996)
- Aggressive sell (side A, hits the bid): 2152505 (0.5004)
- Unclassified side: 4 (0.0000)
- Side B printing at or through the ask: 2149396
- Side B printing at or through the bid: 13
- Side A printing at or through the bid: 2152494
- Side A printing at or through the ask: 11
- Trade inside the spread: 0
- Trade with a missing book: 0

Side is the feed aggressor flag. Price versus bid/ask uses the book stored on that trade row.

## Rebuild of 2026-07-08

The raw file was replayed in memory and compared with the stored parquet. The stored files were not overwritten.
- Snapshot checksum stored: 3d62c55635047c1543a7679a3329c37e8b0ad4368efcee87a306587cfd119eaa
- Snapshot checksum rebuild: 3d62c55635047c1543a7679a3329c37e8b0ad4368efcee87a306587cfd119eaa
- Trade checksum stored: 01f78f5b61a0d30b3b864797af46fe66f56a67067c335e340addcd37d8d86e5e
- Trade checksum rebuild: 01f78f5b61a0d30b3b864797af46fe66f56a67067c335e340addcd37d8d86e5e
- Largest gap between stored bid and the book before the trade was applied: 0.0
- Largest gap between stored ask and the book before the trade was applied: 0.0
- Largest bid change caused by applying the trade itself: 0.0
- Book clears after 09:30: 0

Actions T and F do not change resting size. The book on a trade row is the book after every earlier record, including earlier records with the same timestamp, and before this trade. A later record with the same timestamp is not in that book.

## Spot checks

- first_at_or_after_open at 2026-07-08 09:30:00.000081169-04:00: side B price 29202.75 size 1. Book before 29200.75 / 29202.75. Stored 29200.75 / 29202.75. Book after the trade record 29200.75 / 29202.75.
- nearest_1000 at 2026-07-08 10:00:00.000970131-04:00: side B price 29366.25 size 1. Book before 29365.0 / 29366.25. Stored 29365.0 / 29366.25. Book after the trade record 29365.0 / 29366.25.
- nearest_1100 at 2026-07-08 11:00:00.001153651-04:00: side B price 29212.25 size 1. Book before 29210.5 / 29212.25. Stored 29210.5 / 29212.25. Book after the trade record 29210.5 / 29212.25.
- last at 2026-07-08 11:59:58.931517903-04:00: side A price 29098.0 size 1. Book before 29098.0 / 29099.25. Stored 29098.0 / 29099.25. Book after the trade record 29098.0 / 29099.25.

## Information test

Not run. Infrastructure is sufficient to start that test, and this step stopped before it. Previous-session POC is not an input.
