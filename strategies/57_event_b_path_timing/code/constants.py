"""Strategy 57 frozen constants — Event B path/timing diagnostic."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
RESULTS = STRAT / "results"
S52_RESULTS = ROOT / "strategies" / "52_market_state_census" / "results"
S56_EVENTS = (
    ROOT / "strategies" / "56_range_break_failed_return" / "results" / "event_b_events.parquet"
)
S56_VERDICT = (
    ROOT / "strategies" / "56_range_break_failed_return" / "results" / "event_b_verdict.json"
)

HORIZONS = (5, 15, 30, 60)
MAX_FIRST_REBREAK = 60
PREDICTED_SIDE_RULE = "toward_rebreak"

MIN_IS = 500
MIN_VAL = 200
MIN_OOS = 100
