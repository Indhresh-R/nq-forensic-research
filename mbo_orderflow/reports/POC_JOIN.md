# POC event join

The unconditional MBO test stays as recorded in `INFORMATION.md`. This note is the join of that frozen feature list to the frozen previous-session POC event. No new order-flow feature was defined. No entry or exit was tested. The replay engine was not modified.

## Rules used

Event, already stored in `volume_profile/data/interaction_events.parquet`:

- Level: previous session POC.
- Touch: first trade within 1 tick, in `(ts_event, sequence)` order.
- Approach: `from_above`.
- Session eligible only when this session and the previous session are both complete and neither is a roll.

MBO side, unchanged:

- Engine `REPLAY_ENGINE_V2_TIMESTAMP_CORRECT`.
- Window `[09:30, 12:00)` America/New_York.
- Features that would have been read, and were not, because there is no event: `obi_1`, `depth_net_change` at 1 second, `trade_imbalance` at 1 second, `replenish_net` at 1 second.
- Horizons that would have been used: 1, 5, 15, 30, 60 seconds.
- Crossed rows stay in the store and are not return anchors.

A CME session date is the New York date of the 18:00 open. The MBO file date is the New York date of the 09:30–12:00 window. Those are not the same label for the same clock time.

## Intersection

On the 26 MBO dates there are 17 previous-POC first touches. Twelve pass the roll and completeness filter. Six of those twelve are from above.

None of the six is inside 09:30–12:00. Each one prints at the evening reopen:

| CME session | New York time | Approach |
| --- | --- | --- |
| 2026-07-08 | 19:20:02 | from_above |
| 2026-07-09 | 20:02:04 | from_above |
| 2026-07-14 | 18:01:11 | from_above |
| 2026-07-15 | 18:00:01 | from_above |
| 2026-07-28 | 18:18:11 | from_above |
| 2026-08-11 | 18:04:18 | from_above |

The first touch is consumed near 18:00. By the time the stored MBO window opens, that event is already in the past. Two eligible from-below touches do fall in the morning window (11:27 and 09:35). They were not substituted for the from-above event.

No snapshot was joined. No forward return was computed. No comparison sample was built.

## What this does not say

It does not say the book-imbalance result is gone. It does not say the from-above POC description is gone. It says this event and this MBO window do not meet, so the location test cannot be run on the frozen store.

Testing it would require MBO around the 18:00 reopen. That is a new replay window, not a change to the feature definitions. It was not started here.
