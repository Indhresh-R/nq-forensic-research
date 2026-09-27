"""Frozen definitions for the previous-day structure mechanism test.

Nothing in this module is a trading rule. Bucket edges are locked by
PREREGISTRATION.md and must not be edited after results are inspected.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parent
STUDY_DIR = CODE_DIR.parent
RESULTS_DIR = STUDY_DIR / "results"
FIGURES_DIR = STUDY_DIR / "reports" / "figures"
REPORT_PATH = STUDY_DIR / "REPORT.md"

# Globex completeness. Structural, not outcome-based.
MIN_BARS = 1100
OPEN_NY_MIN = 18 * 60
OPEN_TOLERANCE_MIN = 5
LATE_START_NY = 16 * 60
LATE_END_NY = 17 * 60

HORIZONS: tuple[tuple[str, int], ...] = (
    ("5m", 5),
    ("15m", 15),
    ("30m", 30),
    ("60m", 60),
    ("120m", 120),
)
PRIMARY_HORIZONS: tuple[str, ...] = ("30m", "60m")
SESSION_END = "session_end"
ALL_HORIZONS: tuple[str, ...] = tuple(name for name, _ in HORIZONS) + (SESSION_END,)

# Accept the target minute or the immediately previous minute if a print is missing.
HORIZON_TOLERANCE_NS = 60 * 1_000_000_000

PENETRATION_BUCKETS: tuple[str, ...] = (
    "0-10%",
    "10-20%",
    "20-30%",
    "30-40%",
    "40-50%",
    "50-75%",
    "75-100%",
    ">100%",
)
NO_PENETRATION = "no_penetration"

BODY_BUCKETS: tuple[str, ...] = ("<25%", "25-50%", "50-75%", ">75%")
DEPTH_POOLS: tuple[str, ...] = ("shallow_0_30", "mid_30_75", "deep_gt_75")

# Verdict constants. See PREREGISTRATION.md.
MIN_POOL_N = 50
MIN_MEDIAN_SPREAD = 0.02
SPEARMAN_FLAT = 0.03

LABEL = "Pre-cost mechanism analysis — no executable strategy."


def penetration_bucket(pct: float) -> str:
    """Map a penetration percent onto the frozen bins."""
    if pct is None or not np.isfinite(pct) or pct < 0.0:
        return NO_PENETRATION
    if pct < 10.0:
        return "0-10%"
    if pct < 20.0:
        return "10-20%"
    if pct < 30.0:
        return "20-30%"
    if pct < 40.0:
        return "30-40%"
    if pct < 50.0:
        return "40-50%"
    if pct < 75.0:
        return "50-75%"
    if pct <= 100.0:
        return "75-100%"
    return ">100%"


def body_fraction_bucket(fraction: float) -> str:
    if not np.isfinite(fraction):
        return "undefined"
    if fraction < 0.25:
        return "<25%"
    if fraction < 0.50:
        return "25-50%"
    if fraction < 0.75:
        return "50-75%"
    return ">75%"


def depth_pool(pct: float) -> str:
    """Union of frozen buckets used only for the stability summary."""
    if not np.isfinite(pct) or pct < 0.0:
        return NO_PENETRATION
    if pct < 30.0:
        return "shallow_0_30"
    if pct < 75.0:
        return "mid_30_75"
    return "deep_gt_75"


def minutes_from_globex_open(ny_min: int) -> int:
    minute = int(ny_min)
    if minute >= OPEN_NY_MIN:
        return minute - OPEN_NY_MIN
    return (24 * 60 - OPEN_NY_MIN) + minute
