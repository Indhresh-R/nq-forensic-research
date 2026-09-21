"""In-sample dates already on disk. Not a train/validation split decision."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from research.mbo.clock import STEP_NS

NY = ZoneInfo("America/New_York")

# 09:30-12:00 America/New_York, the window the existing H01/H02 samples use.
RTH_OPEN = (9, 30)
RTH_END = (12, 0)

IS_SESSIONS = (
    "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15",
    "2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23",
    "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31",
    "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10",
    "2026-08-11", "2026-08-12",
)


def rth_grid(date_str: str, step_ns: int = STEP_NS) -> tuple[int, int, int]:
    """Return open_ns, close_ns, n_bins for [09:30, 12:00) New York.

    close_ns is the last included snapshot. 12:00:00 itself is not a row.
    """
    day = datetime.strptime(date_str, "%Y-%m-%d")
    start = datetime(day.year, day.month, day.day, RTH_OPEN[0], RTH_OPEN[1], tzinfo=NY)
    end = datetime(day.year, day.month, day.day, RTH_END[0], RTH_END[1], tzinfo=NY)
    open_ns = int(start.timestamp() * 1_000_000_000)
    end_ns = int(end.timestamp() * 1_000_000_000)
    n_bins = (end_ns - open_ns) // step_ns
    close_ns = open_ns + (n_bins - 1) * step_ns
    return open_ns, close_ns, n_bins
