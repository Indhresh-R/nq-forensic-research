"""Frozen constants for Strategy 51 VSA Step 2 extraction."""
from __future__ import annotations

TICK = 0.25
TICK_INV = 4.0

ATR_N = 20
MEDIAN_N = 20
MIN_PRIOR_BARS = 22  # medians(20) + prior-2 volume checks
GAP_TOLERANCE_MINUTES = 20.0

# Background location (A1)
LOC_K = 32
LOC_ATR_FRAC = 0.15

# SOW seed lookback (A2)
SOW_L = 24

# Close location cuts
ND_CLOSE_FRAC_MAX = 0.50
W2_CLOSE_FRAC_MAX = 0.25

# Wide spread multiple
WIDE_MULT = 1.25

# Event dependence
MIN_SEPARATION = 3  # next t_event >= t_event_prev + 3
