"""Strategy 63 frozen constants — Patrick strict VA first-passage v2."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
RESULTS = STRAT / "results"
P62 = ROOT / "strategies" / "62_patrick_build_fields" / "results"

TICK = 0.25
H_CAP_MIN = 60
DEDUP_MIN = 5
AWAY_W_FRAC = 0.25
AWAY_MIN_TICKS = 4
TOL_TICKS = 1
