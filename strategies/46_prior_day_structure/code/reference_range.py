"""Reference range from a completed previous-day candle. No following-day prices."""
from __future__ import annotations

import numpy as np


def build_reference(previous: dict[str, float | str]) -> dict[str, float | str] | None:
    """Return the close-to-extreme reference, or None if it is undefined.

    Undefined cases: doji, non-positive full range, or a zero close-to-extreme
    distance. Callers must pass only the previous session's candle fields.
    """
    direction = str(previous["direction"])
    if direction == "doji":
        return None
    full_range = float(previous["range"])
    if not np.isfinite(full_range) or full_range <= 0.0:
        return None
    close_px = float(previous["close"])
    if direction == "bullish":
        extreme = float(previous["low"])
        ref_range = close_px - extreme
        if ref_range <= 0.0:
            return None
        return {
            "direction": direction,
            "sign": 1,
            "reference_start": close_px,
            "reference_extreme": extreme,
            "reference_range": ref_range,
        }
    if direction == "bearish":
        extreme = float(previous["high"])
        ref_range = extreme - close_px
        if ref_range <= 0.0:
            return None
        return {
            "direction": direction,
            "sign": -1,
            "reference_start": close_px,
            "reference_extreme": extreme,
            "reference_range": ref_range,
        }
    return None
