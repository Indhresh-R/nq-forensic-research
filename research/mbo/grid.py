"""Predefined mechanism grid. This is not a search space.

Buckets are half-open so a size is in one bucket only.
90 is in [90, 130), not in [50, 90).
"""

from __future__ import annotations

# (label, lo_inclusive, hi_exclusive). None hi means unbounded.
SIZE_BUCKETS: tuple[tuple[str, int, int | None], ...] = (
    ("50-89", 50, 90),
    ("90-129", 90, 130),
    ("130-169", 130, 170),
    ("170-199", 170, 200),
    ("200+", 200, None),
)

# Seconds. Matches the research-horizon list, not a tuned holding period.
HORIZON_SECONDS: tuple[int, ...] = (1, 5, 15, 30, 60, 120, 300, 600, 900)

SIDES: tuple[str, ...] = ("B", "A", "ALL")
