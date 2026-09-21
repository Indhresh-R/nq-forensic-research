"""Assemble eligible previous-day / following-session pairs. No outcome statistics."""
from __future__ import annotations

import numpy as np
import pandas as pd

from daily_candles import SessionBars, candle_fields
from definitions import body_fraction_bucket, depth_pool
from forward_outcomes import outcomes_from_entry
from penetration import measure_sequence
from reference_range import build_reference


def build_panel(sessions: list[SessionBars]) -> tuple[pd.DataFrame, dict[str, int]]:
    """Pair adjacent sessions. Incomplete days are not bridged and not used."""
    counts = {
        "adjacent_slots": 0,
        "blocked_by_incomplete": 0,
        "doji_previous": 0,
        "undefined_reference": 0,
        "eligible_pairs": 0,
        "entered_before_separation": 0,
        "separated_no_return": 0,
        "retracement": 0,
        "retracement_on_last_bar": 0,
    }
    rows: list[dict] = []
    ordered = sorted(sessions, key=lambda item: item.session_date)
    for previous, current in zip(ordered, ordered[1:]):
        counts["adjacent_slots"] += 1
        if not previous.complete or not current.complete:
            counts["blocked_by_incomplete"] += 1
            continue
        candle = candle_fields(previous)
        if candle["direction"] == "doji":
            counts["doji_previous"] += 1
            continue
        reference = build_reference(candle)
        if reference is None:
            counts["undefined_reference"] += 1
            continue
        measured = measure_sequence(current, reference)
        sign = int(reference["sign"])
        previous_range = float(candle["range"])
        baseline = outcomes_from_entry(current, 0, sign, previous_range, "base")
        state = str(measured["sequence_state"])
        retracement_index = int(measured["retracement_index"])
        usable = state == "retracement" and retracement_index + 1 < len(current.open)
        if usable:
            if int(current.ts_ns[retracement_index + 1]) <= int(current.ts_ns[retracement_index]):
                raise RuntimeError("Forward bar is not strictly after the retracement bar")
            forward = outcomes_from_entry(current, retracement_index + 1, sign, previous_range, "fwd")
            counts["retracement"] += 1
        else:
            forward = outcomes_from_entry(current, -1, sign, previous_range, "fwd")
            if state == "retracement":
                counts["retracement_on_last_bar"] += 1
            elif state == "separated_no_return":
                counts["separated_no_return"] += 1
            elif state == "entered_before_separation":
                counts["entered_before_separation"] += 1
            else:
                raise RuntimeError(f"Unknown sequence state {state}")

        pct = measured["retracement_penetration_pct"]
        has_event = state == "retracement"
        row: dict = {
            "session_date": str(current.session_date),
            "previous_session_date": str(previous.session_date),
            "year": current.year,
            "split": current.split,
            "previous_open": candle["open"],
            "previous_high": candle["high"],
            "previous_low": candle["low"],
            "previous_close": candle["close"],
            "previous_range": previous_range,
            "previous_body": candle["body"],
            "previous_body_fraction": candle["body_fraction"],
            "previous_upper_wick": candle["upper_wick"],
            "previous_lower_wick": candle["lower_wick"],
            "previous_upper_wick_fraction": candle["upper_wick_fraction"],
            "previous_lower_wick_fraction": candle["lower_wick_fraction"],
            "body_bucket": body_fraction_bucket(float(candle["body_fraction"])),
            "direction": reference["direction"],
            "reference_start": reference["reference_start"],
            "reference_extreme": reference["reference_extreme"],
            "reference_range": reference["reference_range"],
            "sequence_state": state,
            "qualified": usable,
            "separation_index": int(measured["separation_index"]),
            "separation_ts": measured["separation_ts"],
            "separation_minutes_from_open": measured["separation_minutes_from_open"],
            "blocked_index": int(measured["blocked_index"]),
            "retracement_index": retracement_index,
            "retracement_ts": measured["retracement_ts"],
            "retracement_minutes_from_open": measured["retracement_minutes_from_open"],
            "separation_duration_minutes": measured["separation_duration_minutes"],
            "retracement_penetration_pct": pct if has_event else np.nan,
            "retracement_bucket": measured["retracement_bucket"] if has_event else "no_retracement",
            "retracement_pool": depth_pool(float(pct)) if has_event else "no_retracement",
            "max_penetration_pct": measured["max_penetration_pct"],
            "max_penetration_bucket": measured["max_penetration_bucket"],
            "max_penetration_ts": measured["max_penetration_ts"],
            "max_penetration_index": measured["max_penetration_index"],
        }
        row.update(baseline)
        row.update(forward)
        rows.append(row)
        counts["eligible_pairs"] += 1
    panel = pd.DataFrame(rows)
    if not panel.empty:
        panel["qualified"] = panel["qualified"].astype(bool)
    return panel, counts
