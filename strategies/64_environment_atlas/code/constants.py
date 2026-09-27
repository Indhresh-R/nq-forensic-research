"""Strategy 64 frozen constants — Morning Environment Atlas."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
RESULTS = STRAT / "results"

BARS_PATH = ROOT / "data" / "nq_1m_continuous.parquet"
P1_PATH = RESULTS / "p1_1m_va_proxy.parquet"
P1_TRADE_PATH = ROOT / "strategies" / "62_patrick_build_fields" / "results" / "p1_session_profiles.parquet"
VA_SOURCE = "1m_bar_proxy_v1"

WINDOW_START = "08:00"
WINDOW_END = "12:00"
CLOCKS = ("08:30", "09:30", "10:30", "11:30")

TRAIL_SESSIONS = 60
MIN_RV_RETURNS = 20
FLAT_RANGE_MIN = 1.0  # 4 ticks
MIN_CELL_N = 50
TICK = 0.25
