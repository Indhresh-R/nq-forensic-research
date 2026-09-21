"""Frozen gates for the streak-persistence information test.

These values are the preregistration. They are not tuned to results.
"""
from __future__ import annotations

from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
STUDY_DIR = CODE_DIR.parent
RESULTS_DIR = STUDY_DIR / "results"
REPORT_PATH = STUDY_DIR / "REPORT.md"

BULL = 1
BEAR = -1
FLAT = 0

BUCKETS = ("1", "2", "3", "4", "5", "6", ">=7")
VERDICT_BUCKETS = ("2", "3")

N_PERM = 10_000
SEED = 49
P_GE_MAX = 0.05
SMALL_N = 30
FULL_MIN_N = 100
OOS_MIN_N = 30
YEAR_MIN_N = 20
YEAR_MIN_POSITIVE = 3
YEAR_DISPLAY_MIN_N = 5

NULL_FULL = ("pooled_ge_3", "pooled_ge_4")
NULL_OOS = "pooled_ge_3"

SAMPLES = ("All", "IS", "Validation", "OOS")
