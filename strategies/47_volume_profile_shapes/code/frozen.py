"""Thresholds frozen before any NQ profile was classified.

Copied from PREREGISTRATION.md. Do not edit these to change class counts.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
TRADES_DIR = REPO / "data" / "trades_24h_6m"
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"

TICK_SIZE = 0.25
PRICE_SCALE = 1_000_000_000
EXPECTED_SYMBOL = "NQ.c.0"
EXPECTED_FILE_COUNT = 126
EXPECTED_FIRST_FILE = "trades_24h_2026-03-25.dbn.zst"
EXPECTED_LAST_FILE = "trades_24h_2026-09-16.dbn.zst"

COMPLETENESS_SLACK_MINUTES = 30
ROLL_GAP_POINTS = 150.0

# Local extrema. Prominence is a fraction of POC volume.
# Separation is a fraction of the profile range in ticks.
PROMINENCE_FRAC = 0.20
SEPARATION_FRAC = 0.10
LOOSER_PROMINENCE_FRAC = 0.12
LOOSER_SEPARATION_FRAC = 0.06
STRICTER_PROMINENCE_FRAC = 0.30
STRICTER_SEPARATION_FRAC = 0.15

MAJOR_PEAK_VOLUME_FRAC = 0.50
BIMODAL_SEPARATION_MIN = 0.20
BIMODAL_VALLEY_DEPTH_MIN = 0.30

TAIL_VOLUME_FRAC = 0.10
BODY_RANGE_FRAC = 0.30
POC_BAND_FRAC = 0.10

P_POC_MIN = 0.70
P_ABOVE_SHARE_MIN = 0.62
P_TAIL_ASYM_MIN = 0.20
P_UPPER_BODY_MIN = 0.55

B_POC_MAX = 0.30
B_BELOW_SHARE_MIN = 0.62
B_TAIL_ASYM_MIN = 0.20
B_LOWER_BODY_MIN = 0.55

D_POC_LO = 0.40
D_POC_HI = 0.60
D_SIDE_BALANCE_MAX = 0.10
D_TAIL_DIFF_MAX = 0.12
D_CONCENTRATION_MIN = 0.45

# Verdict on the analysis sample. Agreement is the share of sessions
# whose primary label matches the baseline under each sensitivity setting.
CLEAR_MIN_EACH = 8
CLEAR_AGREE = 0.85
CLEAR_UNCLASS_MAX = 0.60
WEAK_MIN_CLASSES = 2
WEAK_CLASS_COUNT = 5
WEAK_AGREE = 0.70

RNG_SEED = 42
RANDOM_EXAMPLES = 3

CLASS_P = "P-like"
CLASS_B_LOWER = "b-like"
CLASS_D = "D-like"
CLASS_B_DOUBLE = "B-like"
CLASS_UNCLASSIFIED = "UNCLASSIFIED"
PRIMARY_CLASSES = (CLASS_P, CLASS_B_LOWER, CLASS_D, CLASS_B_DOUBLE, CLASS_UNCLASSIFIED)
NAMED_CLASSES = (CLASS_P, CLASS_B_LOWER, CLASS_D, CLASS_B_DOUBLE)

# A dense grid wider than this is treated as a corrupt price, not a shape.
MAX_RANGE_TICKS = 500_000
