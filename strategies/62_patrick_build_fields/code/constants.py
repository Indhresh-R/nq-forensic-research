"""Patrick build-fields frozen constants."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
RESULTS = STRAT / "results"

VP_ROOT = ROOT / "volume_profile"
VP_PROFILES = VP_ROOT / "data" / "session_profiles.parquet"
VP_CODE = VP_ROOT / "code"

Q = 0.99
N_PRINTS = 5000
N_MIN = 500
TICK = 0.25
TOL_TICKS = 1
TPO_MINUTES = 30
VALUE_AREA_PCT = 0.70
