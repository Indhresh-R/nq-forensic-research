"""Chunked replay must match a single pass. No raw MBO."""

from __future__ import annotations

import unittest

from research.mbo.clock import STEP_NS
from research.mbo.engine import ReplaySession

OPEN = 20_000_000_000_000
N = 6
CLOSE = OPEN + (N - 1) * STEP_NS
PX = 1_000_000_000


class Rec:
    def __init__(self, ts: int, action: str, side: str, size: int, price: int, order_id: int) -> None:
        self.ts_event = ts
        self.action = action
        self.side = side
        self.size = size
        self.price = price
        self.order_id = order_id
        self.flags = 0
        self.sequence = order_id


def _events() -> list[Rec]:
    return [
        Rec(OPEN - 2 * STEP_NS, "A", "B", 10, 100 * PX, 1),
        Rec(OPEN - 2 * STEP_NS, "A", "A", 8, 102 * PX, 2),
        Rec(OPEN + 999_000_000, "T", "B", 4, 102 * PX, 9),
        Rec(OPEN + STEP_NS, "T", "A", 1, 100 * PX, 10),
        Rec(OPEN + 2 * STEP_NS + 10, "C", "B", 10, 100 * PX, 1),
    ]


def _run(events: list[Rec]) -> ReplaySession:
    session = ReplaySession("2026-07-08", OPEN, CLOSE, STEP_NS)
    session.consume(events)
    session.finish()
    return session


class PartitionTests(unittest.TestCase):
    def test_chunks_match_full_day(self) -> None:
        events = _events()
        full = _run(events)
        parts = ReplaySession("2026-07-08", OPEN, CLOSE, STEP_NS)
        parts.consume(events[:2])
        parts.consume(events[2:])
        parts.finish()
        full_flow = [(row["ts_ns"], row["trade_b_1s"], row["trade_a_1s"], row["cancel_b_1s"]) for row in full.snapshots]
        part_flow = [(row["ts_ns"], row["trade_b_1s"], row["trade_a_1s"], row["cancel_b_1s"]) for row in parts.snapshots]
        self.assertEqual(full_flow, part_flow)
        self.assertEqual(
            [(row["ts_event"], row["size"]) for row in full.trades],
            [(row["ts_event"], row["size"]) for row in parts.trades],
        )

    def test_late_trade_is_not_on_the_open_row(self) -> None:
        session = _run(_events())
        by_ts = {row["ts_ns"]: row for row in session.snapshots}
        self.assertEqual(by_ts[OPEN]["trade_b_1s"], 0)
        self.assertEqual(by_ts[OPEN + STEP_NS]["trade_b_1s"], 4)
        self.assertLessEqual(by_ts[OPEN + STEP_NS]["flow_max_ts_ns"], OPEN + STEP_NS)


if __name__ == "__main__":
    unittest.main()
