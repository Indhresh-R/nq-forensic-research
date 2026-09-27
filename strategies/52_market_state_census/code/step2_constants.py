"""Step 2 constants — transition-event mechanics."""
from __future__ import annotations

from constants import RESULTS, RNG_COMP, RNG_EXP, RNG_MID
from step1_constants import (
    CELL_A,
    CELL_B,
    CELL_C,
    CELL_D,
    CELLS,
    HORIZONS,
)

FAMILY_COMP_EXIT = "CompExit"
FAMILY_EXP_EXIT = "ExpExit"

ORIGIN_COMP = (CELL_A, CELL_B)
ORIGIN_EXP = (CELL_C, CELL_D)

CENSOR_EVENT = "event"
CENSOR_SESSION_END = "session_end_or_gap"
CENSOR_OPPOSITE_RANGE = "hit_opposite_range_before_normal"
CENSOR_CELL_SWITCH = "switched_abcd_cell_before_normal"
CENSOR_NO_NORMAL = "no_normal_before_end"
