"""Step 3 constants — destination stability + orthogonal conditioning."""
from __future__ import annotations

from constants import NY_OPEN, RTH_END, RESULTS
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D, HORIZONS
from step2_constants import FAMILY_COMP_EXIT, FAMILY_EXP_EXIT

PRIMARY_HORIZON = 30
SECONDARY_HORIZON = 60
MIN_N_VALID = 200

# Event-bar TOD blocks for Step 3 (exclusive end)
STEP3_TOD_BLOCKS: dict[str, tuple[int, int]] = {
    "FIRST_30": (NY_OPEN, NY_OPEN + 30),
    "1000_1200": (10 * 60, 12 * 60),
    "1200_1400": (12 * 60, 14 * 60),
    "1400_1600": (14 * 60, RTH_END),
}

WAIT_SHORT = "SHORT"
WAIT_MED = "MEDIUM"
WAIT_LONG = "LONG"
WAIT_STRATA = (WAIT_SHORT, WAIT_MED, WAIT_LONG)
