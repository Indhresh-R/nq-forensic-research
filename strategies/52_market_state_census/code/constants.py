"""Frozen descriptive constants for Strategy 52 market-state census (Step 0)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
RESULTS = STRAT / "results"

# Clock (must match common.nq_session / common.sessions)
TZ = "America/New_York"
NY_OPEN = 9 * 60 + 30
SESSION_START = 18 * 60
RTH_END = 16 * 60
ANALYSIS_START_NY = NY_OPEN  # 09:30 inclusive
ANALYSIS_END_NY = RTH_END  # 16:00 exclusive

# Rolling windows (minutes = bars on contiguous 1m series)
ER_WINDOWS = (30, 60, 120)
RV_WINDOWS = (30, 60)
ATR_WINDOW = 30
RANGE_WINDOWS = (30, 60)
RVOL_WINDOW = 30
RVOL_HIST_SESSIONS = 60  # trailing sessions for TOD expected volume

# Primary labels use these windows (others reported as continuous diagnostics)
PRIMARY_ER_WINDOW = 60
PRIMARY_RV_WINDOW = 60
PRIMARY_RANGE_WINDOW = 60

# Predetermined tercile cuts (not optimized)
Q_LOW = 1.0 / 3.0
Q_HIGH = 2.0 / 3.0

# Threshold freeze sample: Discovery / IS years only (common.splits)
THRESHOLD_YEARS = frozenset(range(2010, 2022))
IS_YEARS = THRESHOLD_YEARS
VAL_YEARS = frozenset({2022, 2023, 2024})
OOS_YEARS = frozenset({2025, 2026})

# Gap break for contiguous rolling (minutes)
GAP_TOLERANCE_MINUTES = 1.5

# Time-of-day blocks (ny_min inclusive start, exclusive end)
TOD_BLOCKS: dict[str, tuple[int, int]] = {
    "NY_AM": (NY_OPEN, 12 * 60),
    "NY_MIDDAY": (12 * 60, 14 * 60),
    "NY_PM": (14 * 60, RTH_END),
    "FIRST_30": (NY_OPEN, NY_OPEN + 30),
    "FIRST_60": (NY_OPEN, NY_OPEN + 60),
    "1030_1200": (10 * 60 + 30, 12 * 60),
    "1200_1400": (12 * 60, 14 * 60),
    "1400_1600": (14 * 60, RTH_END),
}

DOW_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

# Label strings
DIR_LOW = "LOW_DIRECTIONALITY"
DIR_MID = "MID_DIRECTIONALITY"
DIR_HIGH = "HIGH_DIRECTIONALITY"
VOL_LOW = "LOW_VOLATILITY"
VOL_MID = "NORMAL_VOLATILITY"
VOL_HIGH = "HIGH_VOLATILITY"
VLM_LOW = "LOW_VOLUME"
VLM_MID = "NORMAL_VOLUME"
VLM_HIGH = "HIGH_VOLUME"
RNG_COMP = "COMPRESSION"
RNG_MID = "NORMAL_RANGE"
RNG_EXP = "EXPANSION"

COMPOSITE_TRENDING = "TRENDING"
COMPOSITE_CHOP = "CHOP_RANGE"
COMPOSITE_HIGH_ACT = "HIGH_ACTIVITY"
COMPOSITE_LOW_ACT = "LOW_ACTIVITY"
COMPOSITE_COMPRESSION = "COMPRESSION"
COMPOSITE_EXPANSION = "EXPANSION"
COMPOSITE_MIXED = "TRANSITION_MIXED"
