"""Strategy 65 frozen constants — C1 drive-ext sleeve."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
RESULTS = STRAT / "results"

BARS_PATH = ROOT / "data" / "nq_1m_continuous.parquet"
LABELS_PATH = ROOT / "strategies" / "64_environment_atlas" / "results" / "labels.parquet"

GATE_CLOCK = "10:30"
GATE_CHARACTER = "C1_DRIVE_EXT"
ENTRY_MIN = 10 * 60 + 31  # 10:31
EXIT_MIN = 12 * 60  # 12:00
STOP_RANGE_FRAC = 0.35
STOP_FLOOR = 2.0
COST_RT = 1.0

IS_YEARS = range(2010, 2019)
VAL_YEARS = range(2019, 2023)
OOS_YEARS = range(2023, 2027)
