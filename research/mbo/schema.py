"""Column contracts for the normalized research store.

Each entry is name, dtype, definition, unit, source, known_at.
known_at is 'snapshot_t' or 'event_ts'. Nothing here is a future value.
"""

from __future__ import annotations

SNAPSHOT_FIELDS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("replay_version", "string", "Engine version that wrote the row", "text", "replay", "snapshot_t"),
    ("date", "string", "New York session date", "YYYY-MM-DD", "grid", "snapshot_t"),
    ("instrument", "string", "Instrument label", "text", "constant NQ", "snapshot_t"),
    ("ts_ns", "int64", "Snapshot clock. Row contains only events with ts_event <= ts_ns", "ns", "grid", "snapshot_t"),
    ("mid_px", "float64", "Average of best bid and best ask after events with ts_event <= ts_ns", "index points", "book", "snapshot_t"),
    ("bid_px", "float64", "Best bid price after events with ts_event <= ts_ns", "index points", "book", "snapshot_t"),
    ("ask_px", "float64", "Best ask price after events with ts_event <= ts_ns", "index points", "book", "snapshot_t"),
    ("spread", "float64", "ask_px - bid_px", "index points", "book", "snapshot_t"),
    ("q_b1", "int32", "Resting size at the best bid", "contracts", "book", "snapshot_t"),
    ("q_a1", "int32", "Resting size at the best ask", "contracts", "book", "snapshot_t"),
    ("q_b5", "int32", "Sum of resting size on the top 5 bid levels", "contracts", "book", "snapshot_t"),
    ("q_a5", "int32", "Sum of resting size on the top 5 ask levels", "contracts", "book", "snapshot_t"),
    ("obi_1", "float64", "(q_b1 - q_a1) / (q_b1 + q_a1)", "ratio", "book", "snapshot_t"),
    ("obi_5", "float64", "(q_b5 - q_a5) / (q_b5 + q_a5)", "ratio", "book", "snapshot_t"),
    ("trade_b_1s", "int32", "Aggressor-buy size with ts_event in (ts_ns - 1s, ts_ns]", "contracts", "action T side B", "snapshot_t"),
    ("trade_a_1s", "int32", "Aggressor-sell size with ts_event in (ts_ns - 1s, ts_ns]", "contracts", "action T side A", "snapshot_t"),
    ("trade_cnt_b_1s", "int32", "Aggressor-buy trade count in (ts_ns - 1s, ts_ns]", "trades", "action T side B", "snapshot_t"),
    ("trade_cnt_a_1s", "int32", "Aggressor-sell trade count in (ts_ns - 1s, ts_ns]", "trades", "action T side A", "snapshot_t"),
    ("fill_b_1s", "int32", "Fill size on bid orders in (ts_ns - 1s, ts_ns]. Fill does not itself change the book", "contracts", "action F side B", "snapshot_t"),
    ("fill_a_1s", "int32", "Fill size on ask orders in (ts_ns - 1s, ts_ns]", "contracts", "action F side A", "snapshot_t"),
    ("add_b_1s", "int32", "Added bid size in (ts_ns - 1s, ts_ns]", "contracts", "action A side B", "snapshot_t"),
    ("add_a_1s", "int32", "Added ask size in (ts_ns - 1s, ts_ns]", "contracts", "action A side A", "snapshot_t"),
    ("cancel_b_1s", "int32", "Cancelled bid size in (ts_ns - 1s, ts_ns]", "contracts", "action C side B", "snapshot_t"),
    ("cancel_a_1s", "int32", "Cancelled ask size in (ts_ns - 1s, ts_ns]", "contracts", "action C side A", "snapshot_t"),
    ("flow_max_ts_ns", "int64", "Latest ts_event assigned to this row. 0 if the row has no events. Must be <= ts_ns", "ns", "replay", "snapshot_t"),
)

TRADE_FIELDS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("replay_version", "string", "Engine version that wrote the row", "text", "replay", "event_ts"),
    ("date", "string", "New York session date", "YYYY-MM-DD", "grid", "event_ts"),
    ("instrument", "string", "Instrument label", "text", "constant NQ", "event_ts"),
    ("ts_event", "int64", "Trade timestamp. This is the observation time", "ns", "MBO ts_event", "event_ts"),
    ("sequence", "uint64", "Venue sequence number when the record carries one", "count", "MBO sequence", "event_ts"),
    ("order_id", "uint64", "Order id on the trade record, when present", "id", "MBO order_id", "event_ts"),
    ("action", "string", "Always T in this table", "text", "MBO action", "event_ts"),
    ("side", "string", "Aggressor side. B lifts the ask, A hits the bid", "B or A", "MBO side", "event_ts"),
    ("price", "float64", "Trade price", "index points", "MBO price / 1e9", "event_ts"),
    ("size", "int32", "Trade size", "contracts", "MBO size", "event_ts"),
    ("mid_px", "float64", "Book mid after every event with ts_event <= this trade. The trade action does not change the book", "index points", "book", "event_ts"),
    ("bid_px", "float64", "Best bid at ts_event", "index points", "book", "event_ts"),
    ("ask_px", "float64", "Best ask at ts_event", "index points", "book", "event_ts"),
    ("spread", "float64", "ask_px - bid_px at ts_event", "index points", "book", "event_ts"),
    ("distance_from_mid", "float64", "price - mid_px", "index points", "trade and book", "event_ts"),
)

FEATURE_FIELDS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("cvd_1s", "float64", "trade_b_1s - trade_a_1s. Completed bin ending at ts_ns", "contracts", "snapshots", "snapshot_t"),
    ("cvd_5s", "float64", "Sum of cvd_1s over (ts_ns - 5s, ts_ns]. NaN until 5 bins exist. Not backfilled", "contracts", "snapshots", "snapshot_t"),
    ("cvd_15s", "float64", "Sum of cvd_1s over (ts_ns - 15s, ts_ns]. Not backfilled", "contracts", "snapshots", "snapshot_t"),
    ("cvd_60s", "float64", "Sum of cvd_1s over (ts_ns - 60s, ts_ns]. Not backfilled", "contracts", "snapshots", "snapshot_t"),
    ("add_net_1s", "float64", "add_b_1s - add_a_1s", "contracts", "snapshots", "snapshot_t"),
    ("cancel_net_1s", "float64", "cancel_b_1s - cancel_a_1s", "contracts", "snapshots", "snapshot_t"),
)


def field_names(spec: tuple[tuple[str, str, str, str, str, str], ...]) -> tuple[str, ...]:
    return tuple(row[0] for row in spec)
