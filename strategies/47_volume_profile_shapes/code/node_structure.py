"""Accepted volume regions from the frozen Step 2 rules.

Definitions are copied from STEP2_PREREGISTRATION.md. This module does not
score P, b, D, or B, and it does not read the next session.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from continuous_scores import verify_sample
from detect_shapes import _grid, _valley_between, detect_extrema
from frozen import (
    BIMODAL_SEPARATION_MIN,
    BIMODAL_VALLEY_DEPTH_MIN,
    LOOSER_PROMINENCE_FRAC,
    LOOSER_SEPARATION_FRAC,
    MAJOR_PEAK_VOLUME_FRAC,
    POC_BAND_FRAC,
    PROMINENCE_FRAC,
    RESULTS,
    SEPARATION_FRAC,
    STRICTER_PROMINENCE_FRAC,
    STRICTER_SEPARATION_FRAC,
    TICK_SIZE,
)

GAP_SEPARATION_MIN = BIMODAL_SEPARATION_MIN
GAP_DEPTH_MIN = BIMODAL_VALLEY_DEPTH_MIN
MATCH_ATOL = 1e-8
SETTINGS = (
    ("baseline", PROMINENCE_FRAC, SEPARATION_FRAC),
    ("looser", LOOSER_PROMINENCE_FRAC, LOOSER_SEPARATION_FRAC),
    ("stricter", STRICTER_PROMINENCE_FRAC, STRICTER_SEPARATION_FRAC),
)


def _location_shares(volume: np.ndarray, range_ticks: int) -> dict[str, float]:
    total = float(volume.sum())
    idx = np.arange(len(volume))
    lower = idx * 3 < range_ticks
    middle = (idx * 3 < range_ticks * 2) & ~lower
    upper = ~lower & ~middle
    raw = {
        "lower": float(volume[lower].sum()),
        "middle": float(volume[middle].sum()),
        "upper": float(volume[upper].sum()),
    }
    best = max(raw.values())
    dominant = "lower"
    for name in ("lower", "middle", "upper"):
        if raw[name] == best:
            dominant = name
            break
    return {
        "lower_share": raw["lower"] / total,
        "middle_share": raw["middle"] / total,
        "upper_share": raw["upper"] / total,
        "dominant_third": dominant,
    }


def _basin_shares(volume: np.ndarray, peaks: list[int]) -> dict[int, float]:
    total = float(volume.sum())
    peak_arr = np.asarray(peaks, dtype=int)
    distances = np.abs(np.arange(len(volume))[:, None] - peak_arr[None, :])
    owner = np.argmin(distances, axis=1)
    shares: dict[int, float] = {}
    for pos, peak in enumerate(peak_arr):
        shares[int(peak)] = float(volume[owner == pos].sum()) / total
    return shares


def _concentration(low_tick: int, volume: np.ndarray, range_ticks: int) -> dict[str, float]:
    prices = (low_tick + np.arange(len(volume))) * TICK_SIZE
    total = float(volume.sum())
    poc_index = int(np.argmax(volume))
    mean = float(np.average(prices, weights=volume))
    variance = float(np.average((prices - mean) ** 2, weights=volume))
    span = float(prices[-1] - prices[0])
    half_band = max(POC_BAND_FRAC * span, TICK_SIZE)
    near = np.abs(prices - prices[poc_index]) <= half_band + 1e-9
    return {
        "poc_location": poc_index / range_ticks,
        "vw_std_norm": float(np.sqrt(variance) / span),
        "poc_concentration_10": float(volume[near].sum()) / total,
        "poc_index": poc_index,
        "poc_volume": float(volume[poc_index]),
        "poc_price": float(prices[poc_index]),
    }


def _adjacent_gaps(
    volume: np.ndarray,
    peaks: list[int],
    majors: list[int],
    range_ticks: int,
    low_tick: int,
) -> list[dict]:
    gaps = []
    for left, right in zip(majors, majors[1:]):
        between = [peak for peak in peaks if left < peak < right]
        valley_i = _valley_between(volume, left, right)
        separation = (right - left) / range_ticks
        left_volume = float(volume[left])
        right_volume = float(volume[right])
        if valley_i is None:
            valley_volume = np.nan
            valley_depth = np.nan
            valley_price = np.nan
            material = False
        else:
            valley_volume = float(volume[valley_i])
            smaller = min(left_volume, right_volume)
            valley_depth = 1.0 - valley_volume / smaller if smaller > 0 else np.nan
            valley_price = (low_tick + int(valley_i)) * TICK_SIZE
            material = bool(
                valley_depth == valley_depth
                and separation >= GAP_SEPARATION_MIN
                and valley_depth >= GAP_DEPTH_MIN
            )
        gaps.append(
            {
                "left_index": int(left),
                "right_index": int(right),
                "left_price": (low_tick + int(left)) * TICK_SIZE,
                "right_price": (low_tick + int(right)) * TICK_SIZE,
                "left_volume": left_volume,
                "right_volume": right_volume,
                "separation": float(separation),
                "valley_index": int(valley_i) if valley_i is not None else -1,
                "valley_price": valley_price,
                "valley_volume": valley_volume,
                "valley_depth": valley_depth,
                "minor_peaks_between": int(len(between)),
                "material": material,
                "clean": bool(material and len(between) == 0),
            }
        )
    return gaps


def _regions_from_gaps(
    low_tick: int,
    volume: np.ndarray,
    majors: list[int],
    gaps: list[dict],
    range_ticks: int,
) -> list[dict]:
    n = len(volume)
    total = float(volume.sum())
    cuts = [gap["valley_index"] for gap in gaps if gap["material"]]
    spans: list[tuple[int, int]] = []
    start = 0
    for cut in cuts:
        spans.append((start, int(cut)))
        start = int(cut) + 1
    spans.append((start, n - 1))
    regions = []
    for index, (left, right) in enumerate(spans):
        segment = volume[left : right + 1]
        mode_offset = int(np.argmax(segment))
        mode_index = left + mode_offset
        inside = [peak for peak in majors if left <= peak <= right]
        share = float(segment.sum()) / total
        regions.append(
            {
                "region_index": index,
                "left_index": left,
                "right_index": right,
                "left_price": (low_tick + left) * TICK_SIZE,
                "right_price": (low_tick + right) * TICK_SIZE,
                "volume": float(segment.sum()),
                "volume_share": share,
                "mode_index": mode_index,
                "mode_price": (low_tick + mode_index) * TICK_SIZE,
                "mode_location": mode_index / range_ticks,
                "n_major_peaks_inside": len(inside),
                "span_fraction": (right - left) / range_ticks,
            }
        )
    return regions


def _gap_pick(gaps: list[dict], strongest: bool) -> dict | None:
    material = [gap for gap in gaps if gap["material"]]
    if not material:
        return None
    if strongest:
        return sorted(material, key=lambda gap: (-gap["valley_depth"], -gap["separation"], gap["valley_price"]))[0]
    return sorted(material, key=lambda gap: (gap["valley_depth"], gap["separation"], gap["valley_price"]))[0]


def _empty_gap_fields(prefix: str) -> dict:
    return {
        f"{prefix}_separation": np.nan,
        f"{prefix}_depth": np.nan,
        f"{prefix}_valley_price": np.nan,
        f"{prefix}_minor_peaks_between": 0,
        f"{prefix}_clean": False,
    }


def measure_profile(
    low_tick: int,
    volume: np.ndarray,
    prominence_frac: float = PROMINENCE_FRAC,
    separation_frac: float = SEPARATION_FRAC,
) -> dict:
    volume = np.asarray(volume, dtype=np.float64)
    n = int(len(volume))
    range_ticks = n - 1
    if range_ticks <= 0 or float(volume.sum()) <= 0:
        raise ValueError("profile is degenerate")
    conc = _concentration(low_tick, volume, range_ticks)
    extrema = detect_extrema(volume, int(conc["poc_index"]), prominence_frac, separation_frac)
    peaks = [int(peak) for peak in extrema["peaks"]]
    majors = [peak for peak in peaks if volume[peak] + 1e-9 >= MAJOR_PEAK_VOLUME_FRAC * conc["poc_volume"]]
    if not majors:
        raise ValueError("no major peak")
    gaps = _adjacent_gaps(volume, peaks, majors, range_ticks, low_tick)
    regions = _regions_from_gaps(low_tick, volume, majors, gaps, range_ticks)
    share_sum = float(sum(region["volume"] for region in regions))
    if abs(share_sum - float(volume.sum())) > 1e-6:
        raise ValueError("region volumes do not partition the profile")
    shares = _basin_shares(volume, peaks)
    by_height = sorted(peaks, key=lambda peak: (-float(volume[peak]), peak))
    if len(by_height) >= 2:
        second = by_height[1]
        second_height = float(volume[second]) / conc["poc_volume"]
        second_basin = shares[second]
    else:
        second_height = np.nan
        second_basin = np.nan
    minor_basins = [shares[peak] for peak in peaks if peak not in set(majors)]
    largest_minor = max(minor_basins) if minor_basins else 0.0
    ordered_shares = sorted((region["volume_share"] for region in regions), reverse=True)
    material = [gap for gap in gaps if gap["material"]]
    depths = [gap["valley_depth"] for gap in material]
    structure = {1: "one_region", 2: "two_regions"}.get(len(regions), "many_regions")
    weak = _gap_pick(gaps, strongest=False)
    strong = _gap_pick(gaps, strongest=True)
    clean_gaps = [gap for gap in material if gap["clean"]]
    row = {
        "n_local_maxima": len(peaks),
        "n_major_peaks": len(majors),
        "n_regions": len(regions),
        "n_material_gaps": len(material),
        "n_clean_gaps": len(clean_gaps),
        "n_weak_gaps": len(gaps) - len(material),
        "structure": structure,
        "clean_two": bool(len(regions) == 2 and len(clean_gaps) == 1),
        "largest_region_share": ordered_shares[0],
        "second_region_share": ordered_shares[1] if len(ordered_shares) > 1 else 0.0,
        "second_peak_height_ratio": second_height,
        "second_peak_basin_share": second_basin,
        "largest_minor_basin_share": float(largest_minor),
        "median_gap_depth": float(np.median(depths)) if depths else np.nan,
    }
    row.update(_location_shares(volume, range_ticks))
    row.update(
        {
            "poc_location": conc["poc_location"],
            "vw_std_norm": conc["vw_std_norm"],
            "poc_concentration_10": conc["poc_concentration_10"],
            "poc_price": conc["poc_price"],
        }
    )
    for prefix, picked in (("weak", weak), ("strong", strong)):
        if picked is None:
            row.update(_empty_gap_fields(prefix))
            continue
        row.update(
            {
                f"{prefix}_separation": picked["separation"],
                f"{prefix}_depth": picked["valley_depth"],
                f"{prefix}_valley_price": picked["valley_price"],
                f"{prefix}_minor_peaks_between": picked["minor_peaks_between"],
                f"{prefix}_clean": picked["clean"],
            }
        )
    peak_rows = []
    for peak in peaks:
        peak_rows.append(
            {
                "price": (low_tick + peak) * TICK_SIZE,
                "index": peak,
                "volume": float(volume[peak]),
                "is_major": peak in set(majors),
                "basin_share": shares[peak],
                "location": peak / range_ticks,
            }
        )
    return {"session": row, "regions": regions, "gaps": gaps, "peaks": peak_rows}


def _assert_close(name: str, got: float, expected: float, tol: float = 1e-9) -> None:
    if not np.isclose(got, expected, rtol=0, atol=tol):
        raise AssertionError(f"{name}: got {got}, expected {expected}")


def run_self_check() -> None:
    width = 201
    x = np.arange(width, dtype=np.float64)
    deep = 10000 * np.exp(-0.5 * ((x - 40) / 6) ** 2) + 10000 * np.exp(-0.5 * ((x - 160) / 6) ** 2)
    deep_row = measure_profile(0, deep)
    if deep_row["session"]["n_regions"] != 2 or not deep_row["session"]["clean_two"]:
        raise AssertionError(f"separated pair should be two clean regions: {deep_row['session']}")
    if deep_row["session"]["weak_depth"] < GAP_DEPTH_MIN:
        raise AssertionError("separated pair valley is not deep")

    shallow = np.zeros(101)
    shallow[20] = 1000
    shallow[80] = 1000
    shallow[21:80] = 800
    shallow_row = measure_profile(0, shallow)
    if shallow_row["session"]["n_major_peaks"] != 2 or shallow_row["session"]["n_regions"] != 1:
        raise AssertionError(f"shallow pair should stay one region: {shallow_row['session']}")
    if shallow_row["session"]["n_weak_gaps"] != 1:
        raise AssertionError("shallow pair should record one non-material gap")

    y = np.arange(301, dtype=np.float64)
    triple = (
        8000 * np.exp(-0.5 * ((y - 40) / 5) ** 2)
        + 8000 * np.exp(-0.5 * ((y - 150) / 5) ** 2)
        + 8000 * np.exp(-0.5 * ((y - 260) / 5) ** 2)
    )
    triple_row = measure_profile(0, triple)
    if triple_row["session"]["n_regions"] != 3 or triple_row["session"]["structure"] != "many_regions":
        raise AssertionError(f"three separated peaks should be three regions: {triple_row['session']}")

    upper = np.zeros(100)
    upper[80:] = 100
    upper[90] = 500
    upper_row = measure_profile(0, upper)
    if upper_row["session"]["n_regions"] != 1 or upper_row["session"]["dominant_third"] != "upper":
        raise AssertionError(f"upper mass should be one upper region: {upper_row['session']}")

    interrupted = np.zeros(201)
    interrupted[30] = 1000
    interrupted[170] = 1000
    interrupted[31:170] = 200
    interrupted[100] = 400
    interrupted_row = measure_profile(0, interrupted)
    session = interrupted_row["session"]
    if session["n_regions"] != 2 or session["clean_two"] or session["weak_minor_peaks_between"] != 1:
        raise AssertionError(f"minor peak inside the gap should block clean_two: {session}")
    if session["largest_minor_basin_share"] <= 0:
        raise AssertionError("interrupted profile should keep a minor basin")

    again = measure_profile(0, deep)
    _assert_close("rerun regions", again["session"]["n_regions"], deep_row["session"]["n_regions"], tol=0)
    _assert_close("rerun depth", again["session"]["weak_depth"], deep_row["session"]["weak_depth"])
    print("[step2] synthetic one-region, two-region, three-region, and interrupted-gap checks passed", flush=True)


def _check_stored(measured: dict, stored: pd.Series) -> None:
    session = measured["session"]
    pairs = (
        ("poc_location", session["poc_location"], float(stored["poc_location"])),
        ("vw_std_norm", session["vw_std_norm"], float(stored["vw_std_norm"])),
        ("poc_concentration_10", session["poc_concentration_10"], float(stored["poc_concentration_10"])),
    )
    for name, got, expected in pairs:
        if not np.isclose(got, expected, rtol=0, atol=MATCH_ATOL):
            raise SystemExit(f"{stored['session_date']} {name} recomputed {got} stored {expected}. Stopping.")
    if int(session["n_major_peaks"]) != int(stored["n_major_peaks"]):
        raise SystemExit(
            f"{stored['session_date']} major peaks {session['n_major_peaks']} "
            f"stored {stored['n_major_peaks']}. Stopping."
        )
    if int(session["n_local_maxima"]) != int(stored["n_local_maxima"]):
        raise SystemExit(
            f"{stored['session_date']} local maxima {session['n_local_maxima']} "
            f"stored {stored['n_local_maxima']}. Stopping."
        )


def run_measurement() -> None:
    dataset = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    sample = verify_sample(dataset, raw)
    grids = {}
    for session, part in raw.groupby(raw["session_date"].astype(str), sort=False):
        grid = _grid(part, False)
        if grid is not None:
            grids[str(session)] = grid

    sessions = []
    regions = []
    gaps = []
    peaks = []
    sensitivity = []
    for stored in sample.itertuples(index=False):
        date = str(stored.session_date)
        grid = grids.get(date)
        if grid is None:
            raise SystemExit(f"No contiguous raw profile for {date}. Stopping.")
        low_tick, volume = grid
        measured = measure_profile(low_tick, volume)
        _check_stored(measured, pd.Series(stored._asdict()))
        session_row = {"session_date": date, "primary_class": str(stored.primary_class), **measured["session"]}
        sessions.append(session_row)
        for region in measured["regions"]:
            regions.append({"session_date": date, **region})
        for gap_index, gap in enumerate(measured["gaps"]):
            kept = {key: value for key, value in gap.items() if not key.endswith("_index")}
            gaps.append({"session_date": date, "gap_index": gap_index, **kept})
        for peak in measured["peaks"]:
            peaks.append({"session_date": date, **peak})
        for name, prominence, separation in SETTINGS:
            alt = measure_profile(low_tick, volume, prominence, separation)
            sensitivity.append(
                {
                    "session_date": date,
                    "setting": name,
                    "prominence_frac": prominence,
                    "separation_frac": separation,
                    "n_major_peaks": alt["session"]["n_major_peaks"],
                    "n_regions": alt["session"]["n_regions"],
                    "n_material_gaps": alt["session"]["n_material_gaps"],
                    "n_clean_gaps": alt["session"]["n_clean_gaps"],
                    "structure": alt["session"]["structure"],
                    "clean_two": alt["session"]["clean_two"],
                }
            )

    session_frame = pd.DataFrame(sessions)
    RESULTS.mkdir(parents=True, exist_ok=True)
    session_frame.to_csv(RESULTS / "step2_sessions.csv", index=False)
    pd.DataFrame(regions).to_csv(RESULTS / "step2_regions.csv", index=False)
    pd.DataFrame(gaps).to_csv(RESULTS / "step2_gaps.csv", index=False)
    pd.DataFrame(peaks).to_csv(RESULTS / "step2_peaks.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(RESULTS / "step2_sensitivity.csv", index=False)
    counts = session_frame["structure"].value_counts().to_dict()
    verification = {
        "analysis_sessions": int(len(session_frame)),
        "stored_geometry_matches": True,
        "region_volumes_partition_each_profile": True,
        "structure_counts": {key: int(counts.get(key, 0)) for key in ("one_region", "two_regions", "many_regions")},
        "clean_two_regions": int(session_frame["clean_two"].sum()),
        "gap_cuts": {"separation_min": GAP_SEPARATION_MIN, "valley_depth_min": GAP_DEPTH_MIN},
        "major_peak_volume_frac": MAJOR_PEAK_VOLUME_FRAC,
    }
    (RESULTS / "step2_verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(
        f"[step2] sessions={len(session_frame)} structures={verification['structure_counts']} "
        f"clean_two={verification['clean_two_regions']}",
        flush=True,
    )


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    run_measurement()


if __name__ == "__main__":
    main()
