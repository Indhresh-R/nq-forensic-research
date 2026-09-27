"""Step 1 constants — four-cell path geometry (mechanism only)."""
from __future__ import annotations

from constants import (
    DIR_HIGH,
    DIR_LOW,
    DIR_MID,
    RESULTS,
    RNG_COMP,
    RNG_EXP,
    RNG_MID,
)

HORIZONS = (5, 15, 30, 60)

CELL_A = "A_COMP_LOW_DIR"
CELL_B = "B_COMP_MIDHIGH_DIR"
CELL_C = "C_EXP_HIGH_DIR"
CELL_D = "D_EXP_LOW_DIR"
CELLS = (CELL_A, CELL_B, CELL_C, CELL_D)

STEP1_RESULTS = RESULTS  # same results/ folder
