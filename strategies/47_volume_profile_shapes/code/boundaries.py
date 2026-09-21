"""Prior-session structural boundaries from frozen Step 2 gaps.

Definitions are copied from STEP3_PREREGISTRATION.md. This module does not
scan the next session and does not compute returns.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

from continuous_scores import verify_sample
from detect_shapes import _grid
from frozen import RESULTS, TICK_SIZE

SIZE_SHARE_MIN = 0.25
LOW_VOLUME_FRAC = 0.70
SYNC_TOLERANCE = 1.0


def _parse_date(value: object) -> date:
    return date.fromisoformat(str(value)[:10])


def profile_to_nq_session(session: date) -> date:
    """Map a Step 1 profile session_date to the load_nq session_date."""
    return session + timedelta(days=1)


def valley_band(
    volume: np.ndarray,
    low_tick: int,
    left_price: float,
    right_price: float,
    valley_price: float,
    left_volume: float,
    right_volume: float,
) -> dict:
    prices = (low_tick + np.arange(len(volume))) * TICK_SIZE
    left_candidates = np.flatnonzero(np.isclose(prices, left_price, rtol=0, atol=1e-9))
    right_candidates = np.flatnonzero(np.isclose(prices, right_price, rtol=0, atol=1e-9))
    valley_candidates = np.flatnonzero(np.isclose(prices, valley_price, rtol=0, atol=1e-9))
    if len(left_candidates) != 1 or len(right_candidates) != 1 or len(valley_candidates) != 1:
        raise ValueError("peak or valley price is not unique on the grid")
    left_i = int(left_candidates[0])
    right_i = int(right_candidates[0])
    valley_i = int(valley_candidates[0])
    if not (left_i < valley_i < right_i):
        raise ValueError("valley is not strictly between the HVN peaks")
    range_ticks = len(volume) - 1
    threshold = LOW_VOLUME_FRAC * min(float(left_volume), float(right_volume))
    if float(volume[valley_i]) > threshold + 1e-9:
        raise ValueError("valley tick is not low-volume under the frozen width rule")
    low_mask = np.zeros(len(volume), dtype=bool)
    low_mask[left_i + 1 : right_i] = volume[left_i + 1 : right_i] <= threshold + 1e-9
    start = valley_i
    while start - 1 > left_i and low_mask[start - 1]:
        start -= 1
    end = valley_i
    while end + 1 < right_i and low_mask[end + 1]:
        end += 1
    width_ticks = end - start + 1
    return {
        "valley_index": valley_i,
        "valley_left_index": start,
        "valley_right_index": end,
        "valley_left_price": float(prices[start]),
        "valley_right_price": float(prices[end]),
        "valley_width_ticks": int(width_ticks),
        "valley_width": width_ticks / range_ticks,
        "low_volume_threshold": float(threshold),
    }


def _regions_for_gap(regions: pd.DataFrame, valley_price: float) -> tuple[pd.Series, pd.Series]:
    lower = regions.loc[np.isclose(regions["right_price"].to_numpy(dtype=float), valley_price, rtol=0, atol=1e-9)]
    if len(lower) != 1:
        raise ValueError(f"expected one lower region ending at valley {valley_price}, found {len(lower)}")
    lower_row = lower.iloc[0]
    upper = regions.loc[regions["region_index"] == int(lower_row["region_index"]) + 1]
    if len(upper) != 1:
        raise ValueError("upper region does not follow the valley-owning region")
    upper_row = upper.iloc[0]
    expected_left = float(valley_price) + TICK_SIZE
    if not np.isclose(float(upper_row["left_price"]), expected_left, rtol=0, atol=1e-9):
        raise ValueError("upper region does not start on the tick after the valley")
    return lower_row, upper_row


def build_boundaries() -> pd.DataFrame:
    dataset = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    sample = verify_sample(dataset, raw)
    sessions = pd.read_csv(RESULTS / "step2_sessions.csv")
    gaps = pd.read_csv(RESULTS / "step2_gaps.csv")
    regions = pd.read_csv(RESULTS / "step2_regions.csv")
    sessions["session_date"] = sessions["session_date"].astype(str)
    gaps["session_date"] = gaps["session_date"].astype(str)
    regions["session_date"] = regions["session_date"].astype(str)
    sample_dates = sorted(sample["session_date"].astype(str).tolist())
    if set(sessions["session_date"]) != set(sample_dates):
        raise SystemExit("Step 2 session dates do not match the verified analysis sample. Stopping.")

    grids = {}
    for session, part in raw.groupby(raw["session_date"].astype(str), sort=False):
        grid = _grid(part, False)
        if grid is not None:
            grids[str(session)] = grid

    material = gaps.loc[gaps["material"]].copy()
    rows = []
    for gap in material.itertuples(index=False):
        prior = str(gap.session_date)
        later = [day for day in sample_dates if day > prior]
        next_session = later[0] if later else ""
        grid = grids.get(prior)
        if grid is None:
            raise SystemExit(f"Missing raw profile for prior session {prior}. Stopping.")
        low_tick, volume = grid
        band = valley_band(
            volume,
            low_tick,
            float(gap.left_price),
            float(gap.right_price),
            float(gap.valley_price),
            float(gap.left_volume),
            float(gap.right_volume),
        )
        session_regions = regions.loc[regions["session_date"] == prior]
        lower_row, upper_row = _regions_for_gap(session_regions, float(gap.valley_price))
        stored = sample.loc[sample["session_date"].astype(str) == prior].iloc[0]
        lower_share = float(lower_row["volume_share"])
        upper_share = float(upper_row["volume_share"])
        rows.append(
            {
                "prior_session": prior,
                "gap_index": int(gap.gap_index),
                "next_session": next_session,
                "has_next_session": bool(next_session),
                "lower_hvn_price": float(gap.left_price),
                "upper_hvn_price": float(gap.right_price),
                "lower_hvn_volume": float(gap.left_volume),
                "upper_hvn_volume": float(gap.right_volume),
                "lower_mode_price": float(lower_row["mode_price"]),
                "upper_mode_price": float(upper_row["mode_price"]),
                "lower_left": float(lower_row["left_price"]),
                "lower_right": float(lower_row["right_price"]),
                "upper_left": float(upper_row["left_price"]),
                "upper_right": float(upper_row["right_price"]),
                "lower_share": lower_share,
                "upper_share": upper_share,
                "both_regions_sized": min(lower_share, upper_share) >= SIZE_SHARE_MIN,
                "separation": float(gap.separation),
                "valley_price": float(gap.valley_price),
                "valley_depth": float(gap.valley_depth),
                "clean": bool(gap.clean),
                "minor_peaks_between": int(gap.minor_peaks_between),
                "poc_price": float(stored["poc"]),
                "profile_low": float(stored["profile_low"]),
                "profile_high": float(stored["profile_high"]),
                "lower_mode_to_poc": float(lower_row["mode_price"]) - float(stored["poc"]),
                "upper_mode_to_poc": float(upper_row["mode_price"]) - float(stored["poc"]),
                **band,
            }
        )
    out = pd.DataFrame(rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    out.to_csv(RESULTS / "step3_boundaries.csv", index=False)
    verification = {
        "material_gaps": int(len(out)),
        "with_next_session": int(out["has_next_session"].sum()),
        "without_next_session": int((~out["has_next_session"]).sum()),
        "both_regions_sized": int(out["both_regions_sized"].sum()),
        "clean": int(out["clean"].sum()),
        "size_share_min": SIZE_SHARE_MIN,
        "low_volume_frac": LOW_VOLUME_FRAC,
        "sync_tolerance": SYNC_TOLERANCE,
    }
    (RESULTS / "step3_boundary_verification.json").write_text(
        json.dumps(verification, indent=2),
        encoding="utf-8",
    )
    print(
        f"[step3] boundaries={len(out)} with_next={verification['with_next_session']} "
        f"sized={verification['both_regions_sized']} clean={verification['clean']}",
        flush=True,
    )
    return out


def run_self_check() -> None:
    volume = np.zeros(201)
    volume[40] = 1000
    volume[160] = 1000
    volume[41:160] = 50
    volume[100] = 10
    band = valley_band(volume, 0, 10.0, 40.0, 25.0, 1000.0, 1000.0)
    if band["valley_width_ticks"] != 119:
        raise AssertionError(f"expected full interior low-volume width, got {band}")
    volume2 = volume.copy()
    volume2[70:90] = 800
    band2 = valley_band(volume2, 0, 10.0, 40.0, 25.0, 1000.0, 1000.0)
    if band2["valley_left_index"] != 90 or band2["valley_right_index"] != 159:
        raise AssertionError(f"width should stop at the elevated block: {band2}")
    if profile_to_nq_session(date(2026, 3, 26)) != date(2026, 3, 27):
        raise AssertionError("profile to nq map failed")
    print("[step3] boundary self-check passed", flush=True)


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    build_boundaries()


if __name__ == "__main__":
    main()
