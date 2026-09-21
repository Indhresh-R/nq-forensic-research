"""Timestamp assignment tests. No raw MBO."""

from __future__ import annotations

import unittest

from research.mbo.clock import STEP_NS, snapshot_bin_index
from research.mbo.version import REPLAY_ENGINE_VERSION

OPEN = 10_000_000_000_000
STEP = STEP_NS
N = 10
CLOSE = OPEN + (N - 1) * STEP


class ClockTests(unittest.TestCase):
    def test_version_is_frozen(self) -> None:
        self.assertEqual(REPLAY_ENGINE_VERSION, "REPLAY_ENGINE_V2_TIMESTAMP_CORRECT")

    def test_event_at_999ms_does_not_enter_the_row_at_t(self) -> None:
        event = OPEN + 999_000_000
        self.assertEqual(snapshot_bin_index(event, OPEN, CLOSE, STEP, N), 1)
        leaked = (event - OPEN) // STEP
        self.assertEqual(leaked, 0)
        self.assertNotEqual(snapshot_bin_index(event, OPEN, CLOSE, STEP, N), leaked)

    def test_exact_grid_time_stays_on_that_row(self) -> None:
        self.assertEqual(snapshot_bin_index(OPEN, OPEN, CLOSE, STEP, N), 0)
        self.assertEqual(snapshot_bin_index(OPEN + STEP, OPEN, CLOSE, STEP, N), 1)

    def test_prior_second_lands_on_open_row(self) -> None:
        self.assertEqual(snapshot_bin_index(OPEN - 1, OPEN, CLOSE, STEP, N), 0)
        self.assertIsNone(snapshot_bin_index(OPEN - STEP, OPEN, CLOSE, STEP, N))

    def test_after_last_snapshot_is_dropped(self) -> None:
        self.assertEqual(snapshot_bin_index(CLOSE, OPEN, CLOSE, STEP, N), N - 1)
        self.assertIsNone(snapshot_bin_index(CLOSE + 1, OPEN, CLOSE, STEP, N))


if __name__ == "__main__":
    unittest.main()
