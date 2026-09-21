"""Clock and fate rules. No MBO file is read."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from mbo_orderflow.order_fate.code.definitions import (
    BANNED_P_COLUMNS,
    P_COLUMNS,
    anchor_index,
    assert_study_p_schema,
    classify_removal,
)
from mbo_orderflow.order_fate.code.score import _label, _partial
from research.mbo.clock import STEP_NS


class DefinitionTests(unittest.TestCase):
    def test_anchor_is_strictly_after_the_event(self) -> None:
        open_ns = 1_000_000_000_000
        n_bins = 10
        at_grid = open_ns + 3 * STEP_NS
        idx = anchor_index(at_grid, open_ns, n_bins)
        self.assertEqual(idx, 4)
        self.assertGreater(open_ns + idx * STEP_NS, at_grid)
        inside = open_ns + 3 * STEP_NS + 10
        self.assertEqual(anchor_index(inside, open_ns, n_bins), 4)
        self.assertIsNone(anchor_index(open_ns + 9 * STEP_NS, open_ns, n_bins))

    def test_removal_labels(self) -> None:
        self.assertEqual(classify_removal(0, 5), "cancel")
        self.assertEqual(classify_removal(10, 0), "fill")
        self.assertEqual(classify_removal(4, 6), "partial_then_cancel")

    def test_study_p_schema_rejects_fate(self) -> None:
        assert_study_p_schema(P_COLUMNS)
        self.assertTrue(BANNED_P_COLUMNS.isdisjoint(P_COLUMNS))
        with self.assertRaises(RuntimeError):
            assert_study_p_schema(["age_ms", "fate"])

    def test_partial_association_removes_a_shared_control(self) -> None:
        rng = np.random.default_rng(0)
        n = 4000
        controls = rng.normal(size=(n, 4))
        outcome = controls[:, 0] + rng.normal(size=n)
        shared = controls[:, 0] + 0.05 * rng.normal(size=n)
        redundant, _n = _partial(shared, outcome, controls)
        self.assertLess(abs(redundant), 0.08)
        incremental = outcome + 0.05 * rng.normal(size=n)
        extra, _n = _partial(incremental, outcome, controls)
        self.assertGreater(extra, 0.5)

    def test_label_rule(self) -> None:
        self.assertEqual(_label(0.01, 0.2), "NOT SUPPORTED")
        self.assertEqual(_label(0.03, 0.02), "SUPPORTED")
        self.assertEqual(_label(0.03, -0.02), "INCONCLUSIVE")
        self.assertEqual(_label(float("nan"), 0.2), "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
