"""Constants for Strategy 53 regime strategy screen."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
RESULTS = STRAT / "results"
S52_RESULTS = ROOT / "strategies" / "52_market_state_census" / "results"

COST_RT = 1.0
HOLD_MINUTES = 15
MIN_N_SPLIT = 200
SHUFFLE_SEED = 53

# Path-only descriptive bar (not a stop/target)
PATH_MFE15_MIN = 5.0

CELLS = (
    {
        "cell_id": "A",
        "name": "TRENDING_CONTINUATION",
        "state_flag": "flag_trending",
        "state_label": "TRENDING",
        "family": "continuation",
    },
    {
        "cell_id": "B",
        "name": "CHOP_MEAN_REVERSION",
        "state_flag": "flag_chop",
        "state_label": "CHOP_RANGE",
        "family": "mean_reversion",
    },
    {
        "cell_id": "C",
        "name": "COMPRESSION_BREAKOUT",
        "state_flag": "flag_compression",
        "state_label": "COMPRESSION",
        "family": "breakout",
    },
    {
        "cell_id": "D",
        "name": "EXPANSION_EXHAUSTION",
        "state_flag": "flag_expansion",
        "state_label": "EXPANSION",
        "family": "exhaustion_reversal",
    },
)
