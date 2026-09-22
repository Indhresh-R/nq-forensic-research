"""Event A frozen constants — Displacement → Retracement."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
RESULTS = STRAT / "results"
S52_RESULTS = ROOT / "strategies" / "52_market_state_census" / "results"

W = 30
DISP_ATR_MULT = 1.5
RETRACE_FRAC = 0.50
H_WAIT = 60
EXT_FRAC = 0.50
HORIZONS = (5, 15, 30, 60)
PRIMARY_H = 15
COST_RT = 1.0

MIN_IS = 500
MIN_VAL = 200
MIN_OOS = 100
DELTA_IS_MIN = 0.05
DELTA_VAL_MIN = 0.025
MIN_TRADES_SPLIT = 200
