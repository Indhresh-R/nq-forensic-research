"""Same events must produce the same rows."""

from __future__ import annotations

import unittest

import pandas as pd

from research.mbo.tests.test_partition import _events, _run


class DeterminismTests(unittest.TestCase):
    def test_two_passes_match(self) -> None:
        first = _run(_events())
        second = _run(list(_events()))
        pd.testing.assert_frame_equal(pd.DataFrame(first.snapshots), pd.DataFrame(second.snapshots))
        pd.testing.assert_frame_equal(pd.DataFrame(first.trades), pd.DataFrame(second.trades))


if __name__ == "__main__":
    unittest.main()
