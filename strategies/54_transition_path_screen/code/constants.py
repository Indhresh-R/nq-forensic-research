"""Constants for Strategy 54 transition path screen."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
RESULTS = STRAT / "results"
S52_RESULTS = ROOT / "strategies" / "52_market_state_census" / "results"

HORIZONS = (5, 15, 30)
PRIMARY_H = 15
MIN_IS = 500
MIN_VAL = 200
MIN_OOS = 100
G_IS = 0.25
G_VAL = 0.15

CATALOGS = (
    {"catalog": "R", "state_col": "range_state", "label": "range_state"},
    {"catalog": "C", "state_col": "composite_primary", "label": "composite_primary"},
)
