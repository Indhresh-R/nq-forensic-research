"""Clock checks for the H02 snapshot bin. No strategy rules."""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(Path(__file__).resolve().parent))

from research.mbo.clock import snapshot_bin_index

STEP = 1_000_000_000
OPEN = 1_783_517_400_000_000_000
CLOSE = OPEN + 8_999 * STEP
N_BINS = 9000


def test_event_after_snapshot_goes_to_next_row():
    assert snapshot_bin_index(OPEN, OPEN, CLOSE, STEP, N_BINS) == 0
    assert snapshot_bin_index(OPEN + 1, OPEN, CLOSE, STEP, N_BINS) == 1
    assert snapshot_bin_index(OPEN + STEP, OPEN, CLOSE, STEP, N_BINS) == 1
    assert snapshot_bin_index(OPEN + STEP + 1, OPEN, CLOSE, STEP, N_BINS) == 2


def test_prior_second_lands_on_open_snapshot():
    assert snapshot_bin_index(OPEN - 1, OPEN, CLOSE, STEP, N_BINS) == 0
    assert snapshot_bin_index(OPEN - STEP + 1, OPEN, CLOSE, STEP, N_BINS) == 0
    assert snapshot_bin_index(OPEN - STEP, OPEN, CLOSE, STEP, N_BINS) is None


def test_events_after_last_snapshot_are_dropped():
    assert snapshot_bin_index(CLOSE, OPEN, CLOSE, STEP, N_BINS) == N_BINS - 1
    assert snapshot_bin_index(CLOSE + 1, OPEN, CLOSE, STEP, N_BINS) is None


def assert_samples_respect_snapshot_clock(sample_dir: Path) -> None:
    files = sorted(sample_dir.glob("h02_samples_*.parquet"))
    if not files:
        raise FileNotFoundError(f"No H02 samples in {sample_dir}")
    for path in files:
        df = pd.read_parquet(path, columns=["ts_ns", "flow_max_ts_ns"])
        late = df["flow_max_ts_ns"] > df["ts_ns"]
        if bool(late.any()):
            raise AssertionError(f"{path.name} has {int(late.sum())} rows with flow after the snapshot")


if __name__ == "__main__":
    test_event_after_snapshot_goes_to_next_row()
    test_prior_second_lands_on_open_snapshot()
    test_events_after_last_snapshot_are_dropped()
    print("snapshot bin tests passed")
