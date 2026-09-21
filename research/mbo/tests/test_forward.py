"""Forward-return tests. The future mid must be strictly later."""

from __future__ import annotations

import unittest

import pandas as pd

from research.mbo.clock import STEP_NS, future_snapshot_index
from research.mbo.features import build_features

OPEN = 10_000_000_000_000


class ForwardTests(unittest.TestCase):
    def test_future_index_is_after_the_event(self) -> None:
        event = OPEN + 400_000_000
        idx = future_snapshot_index(event, STEP_NS, OPEN, STEP_NS, 10)
        self.assertIsNotNone(idx)
        snap_ts = OPEN + idx * STEP_NS
        self.assertGreater(snap_ts, event)
        self.assertGreaterEqual(snap_ts, event + STEP_NS)

    def test_same_bin_index_is_rejected(self) -> None:
        idx = future_snapshot_index(OPEN, 0, OPEN, STEP_NS, 5)
        self.assertIsNone(idx)

    def test_feature_forward_return_matches_later_mid(self) -> None:
        rows = []
        for i in range(8):
            rows.append(
                {
                    "replay_version": "REPLAY_ENGINE_V2_TIMESTAMP_CORRECT",
                    "ts_ns": OPEN + i * STEP_NS,
                    "mid_px": 100.0 + i,
                    "trade_b_1s": 1,
                    "trade_a_1s": 0,
                    "add_b_1s": 0,
                    "add_a_1s": 0,
                    "cancel_b_1s": 0,
                    "cancel_a_1s": 0,
                }
            )
        out = build_features(pd.DataFrame(rows))
        self.assertEqual(out.loc[0, "fwd_ret_1s"], 1.0)
        self.assertEqual(out.loc[0, "fwd_ret_5s"], 5.0)
        self.assertTrue(pd.isna(out.loc[7, "fwd_ret_1s"]))
        self.assertTrue(pd.isna(out.loc[0, "cvd_5s"]))
        self.assertEqual(out.loc[4, "cvd_5s"], 5)


if __name__ == "__main__":
    unittest.main()
