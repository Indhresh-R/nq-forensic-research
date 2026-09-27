"""Strategy 59 frozen constants — ORB first-passage."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
RESULTS = STRAT / "results"
S52_RESULTS = ROOT / "strategies" / "52_market_state_census" / "results"

NY_OPEN = 570
W_OR = 30
H_WAIT = 90
H_CAP = 60
TARGET_R_MULT = 1.0
COST_RT = 1.0

MIN_IS = 500
MIN_VAL = 200
MIN_OOS = 100

P_TARGET_IS = 0.55
P_TARGET_VAL = 0.52
P_TARGET_OOS = 0.50
DELTA_FP_IS = 0.10
DELTA_FP_VAL = 0.05

MAE_R_FRAC = 0.50
MAE_PTS_MAX = 8.0
MIN_TRADES_SPLIT = 200
