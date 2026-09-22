"""Frozen constants for Strategy 50 Step 2 extraction."""
from __future__ import annotations

TICK = 0.25
TICK_INV = 4.0  # 1 / TICK

PIVOT_L = 2
ATR_N = 20
GAP_TOLERANCE_MINUTES = 20.0

# TR construction
SWING_TOL_ATR = 0.25
TR_HEIGHT_MIN_ATR = 0.75
TR_MIN_DEV_BARS = 12
TR_REVISIT_FRAC = 0.15
LATE_MIN_BARS = 8

# Terminal event
R_MAX = 6  # recovery window bars (0..5 inclusive of start => 6 bars)
MIN_VIOL_TICKS = 1  # max(0.25 pt, 0.05*height) handled in code
MIN_VIOL_HEIGHT_FRAC = 0.05
MAX_EXCURSION_HEIGHT_FRAC = 1.00
ACCEPT_CONSEC_CLOSES = 4

# Confirmation
W_CONFIRM = 12

# Control A
CONTROL_A_LOOKBACK = 20
