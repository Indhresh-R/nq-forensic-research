"""Causal snapshot clock for REPLAY_ENGINE_V2_TIMESTAMP_CORRECT.

The rejected assignment was floor division:

    idx = (ts_event - open_ns) // step_ns

That puts every event in [t, t + step) onto the row timestamped t, so the row
contains trades that have not happened yet. Forward returns that start at t
then include those same trades.
"""

from __future__ import annotations

import numpy as np

STEP_NS = 1_000_000_000
F_SNAPSHOT = 32
F_LAST = 128


def snapshot_bin_index(
    ts: int,
    open_ns: int,
    close_ns: int,
    step_ns: int,
    n_bins: int,
) -> int | None:
    """Return the row whose clock is the first grid time t >= ts_event.

    Row t holds (t - step, t]. Returns None outside that session grid.
    """
    if ts <= open_ns - step_ns or ts > close_ns:
        return None
    idx = (ts - open_ns + step_ns - 1) // step_ns
    if idx < 0 or idx >= n_bins:
        return None
    return int(idx)


def future_snapshot_index(
    ts_event: int,
    horizon_ns: int,
    open_ns: int,
    step_ns: int,
    n_bins: int,
) -> int | None:
    """First grid index whose timestamp is >= ts_event + horizon and > ts_event."""
    target = ts_event + horizon_ns
    if target <= open_ns:
        return None
    idx = (target - open_ns + step_ns - 1) // step_ns
    if idx < 0 or idx >= n_bins:
        return None
    snap_ts = open_ns + idx * step_ns
    if snap_ts <= ts_event:
        return None
    return int(idx)


def future_snapshot_indices(ts_event, horizon_ns: int, open_ns: int, step_ns: int, n_bins: int):
    """Vector form of future_snapshot_index. Missing rows are -1."""
    ts = np.asarray(ts_event, dtype=np.int64)
    target = ts + horizon_ns
    idx = (target - open_ns + step_ns - 1) // step_ns
    snap_ts = open_ns + idx * step_ns
    bad = (target <= open_ns) | (idx < 0) | (idx >= n_bins) | (snap_ts <= ts)
    out = idx.astype(np.int64, copy=True)
    out[bad] = -1
    return out


def grid_bounds(open_ns: int, n_bins: int, step_ns: int = STEP_NS) -> tuple[int, int]:
    close_ns = open_ns + (n_bins - 1) * step_ns
    return open_ns, close_ns
