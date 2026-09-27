"""Frozen constants for the daily-candle continuation information test.

Nothing here is a trading rule, a filter, or a tuned threshold.
"""
from __future__ import annotations

from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
STUDY_DIR = CODE_DIR.parent
RESULTS_DIR = STUDY_DIR / "results"

# Globex completeness. Same structural checks as strategy 46. Not outcome-based.
MIN_BARS = 1100
OPEN_NY_MIN = 18 * 60
OPEN_TOLERANCE_MIN = 5
LATE_START_NY = 16 * 60
LATE_END_NY = 17 * 60

NONE = "NONE"
UP = "UP"
DOWN = "DOWN"

PRIMARY = "primary"
SECONDARY = "secondary"

MODELS = (
    "test1_bull",
    "test1_bear",
    "test1_pooled",
    "test2_up",
    "test2_down",
    "test2_pooled",
    "always_long",
)

SPLIT_ORDER = ("All", "IS", "Validation", "OOS")

REQUIRED_SPLITS = ("IS", "Validation", "OOS")
