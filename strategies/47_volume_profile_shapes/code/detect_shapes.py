"""Detect local volume nodes and assign preregistered shape flags.

Thresholds live in frozen.py. This file does not search them.
"""

from __future__ import annotations

import json
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_prominences

from frozen import (
    BIMODAL_SEPARATION_MIN,
    BIMODAL_VALLEY_DEPTH_MIN,
    BODY_RANGE_FRAC,
    CLASS_B_DOUBLE,
    CLASS_B_LOWER,
    CLASS_D,
    CLASS_P,
    CLASS_UNCLASSIFIED,
    CLEAR_AGREE,
    CLEAR_MIN_EACH,
    CLEAR_UNCLASS_MAX,
    D_CONCENTRATION_MIN,
    D_POC_HI,
    D_POC_LO,
    D_SIDE_BALANCE_MAX,
    D_TAIL_DIFF_MAX,
    MAJOR_PEAK_VOLUME_FRAC,
    MAX_RANGE_TICKS,
    NAMED_CLASSES,
    P_ABOVE_SHARE_MIN,
    P_POC_MIN,
    P_TAIL_ASYM_MIN,
    P_UPPER_BODY_MIN,
    POC_BAND_FRAC,
    B_BELOW_SHARE_MIN,
    B_LOWER_BODY_MIN,
    B_POC_MAX,
    B_TAIL_ASYM_MIN,
    PROMINENCE_FRAC,
    RESULTS,
    SEPARATION_FRAC,
    TAIL_VOLUME_FRAC,
    TICK_SIZE,
    WEAK_AGREE,
    WEAK_CLASS_COUNT,
    WEAK_MIN_CLASSES,
)

VERDICT_TEXT = {
    "CLEAR STRUCTURE": "The profile shapes are objectively distinguishable and reasonably stable.",
    "WEAK STRUCTURE": "Some geometric differences exist, but classification is sensitive or ambiguous.",
    "NO CLEAR STRUCTURE": "The textbook categories cannot be reliably separated using objective profile geometry.",
}


def collapse_flat_peaks(volume: np.ndarray) -> np.ndarray:
    """Keep the lower-price edge of a flat local-maximum plateau."""
    original = np.asarray(volume, dtype=np.float64)
    collapsed = original.copy()
    n = len(original)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and original[j + 1] == original[i]:
            j += 1
        if j > i and original[i] > 0:
            left_ok = i == 0 or original[i - 1] < original[i]
            right_ok = j == n - 1 or original[j + 1] < original[i]
            if left_ok and right_ok:
                collapsed[i + 1 : j + 1] = original[i] - 1.0
        i = j + 1
    return collapsed


def enforce_poc(peak_idx: np.ndarray, poc_index: int, distance: int, volume: np.ndarray) -> list[int]:
    peaks = [int(i) for i in peak_idx]
    if poc_index not in peaks:
        peaks.append(int(poc_index))
    kept: list[int] = []
    for peak in sorted(peaks, key=lambda i: (-float(volume[i]), i)):
        if all(abs(peak - prior) >= distance for prior in kept):
            kept.append(peak)
    return sorted(kept)


def tail_offset(volume: np.ndarray, total: float, from_high: bool) -> int:
    seq = volume[::-1] if from_high else volume
    running = 0.0
    target = TAIL_VOLUME_FRAC * total
    for i, value in enumerate(seq):
        running += float(value)
        if running + 1e-9 >= target:
            return int(i)
    return int(len(volume) - 1)


def ge_deficit(value: float, minimum: float) -> float:
    if value != value:
        return 1.0
    scale = abs(minimum) if minimum != 0 else 1.0
    return float(max(0.0, (minimum - value) / scale))


def le_deficit(value: float, maximum: float) -> float:
    if value != value:
        return 1.0
    scale = abs(maximum) if maximum != 0 else 1.0
    return float(max(0.0, (value - maximum) / scale))


def band_deficit(value: float, lo: float, hi: float) -> float:
    if value != value:
        return 1.0
    if value < lo:
        return float((lo - value) / lo) if lo else 1.0
    if value > hi:
        return float((value - hi) / hi) if hi else 1.0
    return 0.0


def _valley_between(volume: np.ndarray, left: int, right: int) -> int | None:
    if right <= left + 1:
        return None
    segment = volume[left + 1 : right]
    lowest = float(segment.min())
    candidates = np.flatnonzero(segment == lowest) + (left + 1)
    mid = (left + right) / 2.0
    return int(min(candidates, key=lambda tick: (abs(tick - mid), tick)))


def detect_extrema(
    volume: np.ndarray,
    poc_index: int,
    prominence_frac: float,
    separation_frac: float,
) -> dict:
    range_ticks = len(volume) - 1
    distance = max(1, int(round(separation_frac * range_ticks)))
    prominence = prominence_frac * float(volume[poc_index])
    collapsed = collapse_flat_peaks(volume)
    if prominence <= 0:
        peaks = [int(poc_index)]
    else:
        found, _props = find_peaks(collapsed, prominence=prominence, distance=distance)
        peaks = enforce_poc(found, poc_index, distance, volume)
    if prominence <= 0:
        minima: list[int] = []
    else:
        found_min, _props = find_peaks(-collapsed, prominence=prominence, distance=distance)
        minima = [int(i) for i in found_min]
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="some peaks have a prominence of 0")
        peak_prom = (
            peak_prominences(collapsed, np.asarray(peaks, dtype=int))[0] if peaks else np.array([])
        )
        min_prom = (
            peak_prominences(-collapsed, np.asarray(minima, dtype=int))[0] if minima else np.array([])
        )
    return {
        "peaks": peaks,
        "minima": minima,
        "peak_prominence": [float(v) for v in peak_prom],
        "min_prominence": [float(v) for v in min_prom],
        "distance_ticks": distance,
        "prominence_floor": float(prominence),
    }


def empty_peak_fields() -> dict:
    return {
        "peak1_price": np.nan,
        "peak2_price": np.nan,
        "peak1_volume": np.nan,
        "peak2_volume": np.nan,
        "peak_separation": np.nan,
        "normalized_separation": np.nan,
        "valley_price": np.nan,
        "valley_volume": np.nan,
        "valley_ratio": np.nan,
        "valley_depth": np.nan,
        "peak_balance": np.nan,
        "peak_relative_volume": np.nan,
    }


def classify_volume(
    low_tick: int,
    volume: np.ndarray,
    prominence_frac: float = PROMINENCE_FRAC,
    separation_frac: float = SEPARATION_FRAC,
) -> dict:
    volume = np.asarray(volume, dtype=np.float64)
    total = float(volume.sum())
    n = int(len(volume))
    range_ticks = n - 1
    degenerate = total <= 0 or range_ticks <= 0 or range_ticks > MAX_RANGE_TICKS
    row = {
        "degenerate": bool(degenerate),
        "profile_low_ticks": int(low_tick),
        "profile_high_ticks": int(low_tick + range_ticks) if n else np.nan,
        "profile_low": low_tick * TICK_SIZE,
        "profile_high": (low_tick + range_ticks) * TICK_SIZE if n else np.nan,
        "profile_range_ticks": int(range_ticks),
        "profile_range": range_ticks * TICK_SIZE,
        "n_local_maxima": 0,
        "n_local_minima": 0,
        "n_major_peaks": 0,
        "major_max_prices": "[]",
        "major_max_volumes": "[]",
        "major_min_prices": "[]",
        "major_min_volumes": "[]",
        "flag_p": False,
        "flag_b": False,
        "flag_d": False,
        "flag_bimodal": False,
        "flag_multimodal": False,
        "conflict": False,
        "primary_class": CLASS_UNCLASSIFIED,
        "p_strength": np.nan,
        "b_strength": np.nan,
        "d_strength": np.nan,
        "bimodal_strength": np.nan,
        "rule_shortfall": np.nan,
    }
    row.update(empty_peak_fields())
    if degenerate:
        row.update(_blank_geometry())
        return row, []

    prices = (low_tick + np.arange(n)) * TICK_SIZE
    poc_index = int(np.argmax(volume))
    poc_volume = float(volume[poc_index])
    low = float(prices[0])
    high = float(prices[-1])
    span = high - low
    mean = float(np.average(prices, weights=volume))
    variance = float(np.average((prices - mean) ** 2, weights=volume))
    std = float(np.sqrt(variance))
    center = range_ticks / 2.0
    idx = np.arange(n)
    above = float(volume[idx > center].sum())
    below = float(volume[idx < center].sum())
    at_mid = float(volume[idx == center].sum()) if float(center).is_integer() else 0.0
    sides = above + below
    above_share = above / sides if sides else np.nan
    lower_tail = tail_offset(volume, total, from_high=False) / range_ticks
    upper_tail = tail_offset(volume, total, from_high=True) / range_ticks
    upper_cut = high - BODY_RANGE_FRAC * span
    lower_cut = low + BODY_RANGE_FRAC * span
    upper_body = float(volume[prices >= upper_cut - 1e-9].sum()) / total
    lower_body = float(volume[prices <= lower_cut + 1e-9].sum()) / total
    half_band = max(POC_BAND_FRAC * span, TICK_SIZE)
    concentration = float(volume[np.abs(prices - prices[poc_index]) <= half_band + 1e-9].sum()) / total
    geom = {
        "poc": float(prices[poc_index]),
        "poc_ticks": int(low_tick + poc_index),
        "poc_volume": poc_volume,
        "poc_volume_pct": poc_volume / total,
        "poc_location": poc_index / range_ticks,
        "vw_mean": mean,
        "vw_std": std,
        "vw_mean_location": (mean - low) / span,
        "vw_std_norm": std / span,
        "volume_above_mid": above,
        "volume_below_mid": below,
        "volume_at_mid": at_mid,
        "volume_above_share": above_share,
        "volume_below_share": (1.0 - above_share) if above_share == above_share else np.nan,
        "lower_tail_width_10": lower_tail,
        "upper_tail_width_10": upper_tail,
        "tail_asymmetry_lower_minus_upper": lower_tail - upper_tail,
        "upper_body_share": upper_body,
        "lower_body_share": lower_body,
        "poc_concentration_10": concentration,
    }
    row.update(geom)

    extrema = detect_extrema(volume, poc_index, prominence_frac, separation_frac)
    peaks = extrema["peaks"]
    minima = extrema["minima"]
    major = [i for i in peaks if volume[i] + 1e-9 >= MAJOR_PEAK_VOLUME_FRAC * poc_volume]
    row["n_local_maxima"] = len(peaks)
    row["n_local_minima"] = len(minima)
    row["n_major_peaks"] = len(major)
    row["major_max_prices"] = json.dumps([float(prices[i]) for i in major])
    row["major_max_volumes"] = json.dumps([float(volume[i]) for i in major])
    row["major_min_prices"] = json.dumps([float(prices[i]) for i in minima])
    row["major_min_volumes"] = json.dumps([float(volume[i]) for i in minima])

    if len(peaks) >= 2:
        ordered = sorted(peaks, key=lambda i: (-float(volume[i]), i))
        left, right = sorted((ordered[0], ordered[1]))
        v_left = float(volume[left])
        v_right = float(volume[right])
        smaller = min(v_left, v_right)
        larger = max(v_left, v_right)
        valley_i = _valley_between(volume, left, right)
        sep_ticks = right - left
        row["peak1_price"] = float(prices[left])
        row["peak2_price"] = float(prices[right])
        row["peak1_volume"] = v_left
        row["peak2_volume"] = v_right
        row["peak_separation"] = sep_ticks * TICK_SIZE
        row["normalized_separation"] = sep_ticks / range_ticks
        row["peak_balance"] = smaller / larger if larger else np.nan
        row["peak_relative_volume"] = v_right / v_left if v_left else np.nan
        if valley_i is not None and smaller > 0:
            v_valley = float(volume[valley_i])
            row["valley_price"] = float(prices[valley_i])
            row["valley_volume"] = v_valley
            row["valley_ratio"] = v_valley / smaller
            row["valley_depth"] = 1.0 - (v_valley / smaller)

    p_ok = bool(
        geom["poc_location"] >= P_POC_MIN
        and geom["volume_above_share"] >= P_ABOVE_SHARE_MIN
        and geom["tail_asymmetry_lower_minus_upper"] >= P_TAIL_ASYM_MIN
        and geom["upper_body_share"] >= P_UPPER_BODY_MIN
    )
    b_ok = bool(
        geom["poc_location"] <= B_POC_MAX
        and (1.0 - geom["volume_above_share"]) >= B_BELOW_SHARE_MIN
        and (-geom["tail_asymmetry_lower_minus_upper"]) >= B_TAIL_ASYM_MIN
        and geom["lower_body_share"] >= B_LOWER_BODY_MIN
    )
    d_ok = bool(
        D_POC_LO <= geom["poc_location"] <= D_POC_HI
        and abs(geom["volume_above_share"] - 0.5) <= D_SIDE_BALANCE_MAX
        and abs(geom["upper_tail_width_10"] - geom["lower_tail_width_10"]) <= D_TAIL_DIFF_MAX
        and len(major) == 1
        and geom["poc_concentration_10"] >= D_CONCENTRATION_MIN
    )
    bimodal = bool(
        len(major) == 2
        and row["normalized_separation"] == row["normalized_separation"]
        and row["normalized_separation"] >= BIMODAL_SEPARATION_MIN
        and row["valley_depth"] == row["valley_depth"]
        and row["valley_depth"] >= BIMODAL_VALLEY_DEPTH_MIN
    )
    named = []
    if p_ok:
        named.append(CLASS_P)
    if b_ok:
        named.append(CLASS_B_LOWER)
    if d_ok:
        named.append(CLASS_D)
    if bimodal:
        named.append(CLASS_B_DOUBLE)
    below_share = geom["volume_below_share"]
    p_short = (
        ge_deficit(geom["poc_location"], P_POC_MIN)
        + ge_deficit(geom["volume_above_share"], P_ABOVE_SHARE_MIN)
        + ge_deficit(geom["tail_asymmetry_lower_minus_upper"], P_TAIL_ASYM_MIN)
        + ge_deficit(geom["upper_body_share"], P_UPPER_BODY_MIN)
    )
    b_short = (
        le_deficit(geom["poc_location"], B_POC_MAX)
        + ge_deficit(below_share, B_BELOW_SHARE_MIN)
        + ge_deficit(-geom["tail_asymmetry_lower_minus_upper"], B_TAIL_ASYM_MIN)
        + ge_deficit(geom["lower_body_share"], B_LOWER_BODY_MIN)
    )
    d_short = (
        band_deficit(geom["poc_location"], D_POC_LO, D_POC_HI)
        + le_deficit(abs(geom["volume_above_share"] - 0.5), D_SIDE_BALANCE_MAX)
        + le_deficit(abs(geom["upper_tail_width_10"] - geom["lower_tail_width_10"]), D_TAIL_DIFF_MAX)
        + (0.0 if len(major) == 1 else 1.0)
        + ge_deficit(geom["poc_concentration_10"], D_CONCENTRATION_MIN)
    )
    bimodal_short = (
        (0.0 if len(major) == 2 else 1.0)
        + ge_deficit(row["normalized_separation"], BIMODAL_SEPARATION_MIN)
        + ge_deficit(row["valley_depth"], BIMODAL_VALLEY_DEPTH_MIN)
    )
    row.update(
        {
            "flag_p": p_ok,
            "flag_b": b_ok,
            "flag_d": d_ok,
            "flag_bimodal": bimodal,
            "flag_multimodal": len(major) >= 3,
            "conflict": len(named) >= 2,
            "primary_class": named[0] if len(named) == 1 else CLASS_UNCLASSIFIED,
            "p_strength": geom["poc_location"] + geom["upper_body_share"] + geom["tail_asymmetry_lower_minus_upper"],
            "b_strength": (1.0 - geom["poc_location"]) + geom["lower_body_share"] + (-geom["tail_asymmetry_lower_minus_upper"]),
            "d_strength": (
                (1.0 - 2.0 * abs(geom["poc_location"] - 0.5))
                + (1.0 - 2.0 * abs(geom["volume_above_share"] - 0.5))
                + geom["poc_concentration_10"]
                + (1.0 - abs(geom["upper_tail_width_10"] - geom["lower_tail_width_10"]))
            ),
            "bimodal_strength": float(row["valley_depth"] + row["peak_balance"] + row["normalized_separation"]),
            "rule_shortfall": float(min(p_short, b_short, d_short, bimodal_short)),
        }
    )
    nodes = []
    for pos, peak in enumerate(peaks):
        nodes.append(
            {
                "kind": "maximum",
                "price": float(prices[peak]),
                "volume": float(volume[peak]),
                "is_major": peak in major,
                "prominence": extrema["peak_prominence"][pos],
            }
        )
    for pos, valley in enumerate(minima):
        nodes.append(
            {
                "kind": "minimum",
                "price": float(prices[valley]),
                "volume": float(volume[valley]),
                "is_major": True,
                "prominence": extrema["min_prominence"][pos],
            }
        )
    return row, nodes


def _blank_geometry() -> dict:
    keys = (
        "poc",
        "poc_ticks",
        "poc_volume",
        "poc_volume_pct",
        "poc_location",
        "vw_mean",
        "vw_std",
        "vw_mean_location",
        "vw_std_norm",
        "volume_above_mid",
        "volume_below_mid",
        "volume_at_mid",
        "volume_above_share",
        "volume_below_share",
        "lower_tail_width_10",
        "upper_tail_width_10",
        "tail_asymmetry_lower_minus_upper",
        "upper_body_share",
        "lower_body_share",
        "poc_concentration_10",
    )
    return {key: np.nan for key in keys}


def analysis_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["is_complete"].astype(bool)
        & ~frame["is_roll_transition"].astype(bool)
        & frame["symbol_ok"].astype(bool)
        & ~frame["file_problem"].astype(bool)
        & ~frame["corrupt_range"].astype(bool)
        & ~frame["degenerate"].astype(bool)
        & (frame["total_volume"] > 0)
        & (frame["profile_range_ticks"] > 0)
    )


def decide(counts: dict[str, int], n: int, agree_loose: float, agree_strict: float) -> str:
    named = [int(counts.get(name, 0)) for name in NAMED_CLASSES]
    unclassified = int(counts.get(CLASS_UNCLASSIFIED, 0))
    share = unclassified / n if n else 1.0
    if (
        n > 0
        and all(count >= CLEAR_MIN_EACH for count in named)
        and agree_loose >= CLEAR_AGREE
        and agree_strict >= CLEAR_AGREE
        and share < CLEAR_UNCLASS_MAX
    ):
        return "CLEAR STRUCTURE"
    populated = sum(count >= WEAK_CLASS_COUNT for count in named)
    if n > 0 and populated >= WEAK_MIN_CLASSES and agree_loose >= WEAK_AGREE and agree_strict >= WEAK_AGREE:
        return "WEAK STRUCTURE"
    return "NO CLEAR STRUCTURE"


def _gaussian(n: int, center: float, sigma: float, scale: float) -> np.ndarray:
    x = np.arange(n, dtype=np.float64)
    return np.rint(scale * np.exp(-0.5 * ((x - center) / sigma) ** 2)).astype(np.float64)


def run_self_check() -> None:
    width = 101
    bell = _gaussian(width, 50, 8, 10000)
    fat = np.zeros(width)
    fat[80:] = 8000
    fat[:80] = 50
    stem = fat[::-1].copy()
    double = _gaussian(width, 25, 4, 10000) + _gaussian(width, 75, 4, 10000)
    skew = _gaussian(width, 62, 8, 10000)
    flat = np.ones(width)
    expected = {
        "D": (bell, CLASS_D),
        "P": (fat, CLASS_P),
        "b": (stem, CLASS_B_LOWER),
        "B": (double, CLASS_B_DOUBLE),
        "skew": (skew, CLASS_UNCLASSIFIED),
        "flat": (flat, CLASS_UNCLASSIFIED),
    }
    for name, (volume, label) in expected.items():
        row, _nodes = classify_volume(0, volume)
        if row["primary_class"] != label or row["conflict"]:
            raise AssertionError(f"synthetic {name} -> {row['primary_class']} conflict={row['conflict']} flags="
                                 f"P{row['flag_p']} b{row['flag_b']} D{row['flag_d']} B{row['flag_bimodal']} "
                                 f"poc={row['poc_location']:.3f} above={row['volume_above_share']:.3f} "
                                 f"tails={row['lower_tail_width_10']:.3f}/{row['upper_tail_width_10']:.3f} "
                                 f"body={row['upper_body_share']:.3f}/{row['lower_body_share']:.3f} "
                                 f"major={row['n_major_peaks']} sep={row['normalized_separation']} depth={row['valley_depth']}")
        again, _nodes = classify_volume(0, volume)
        if again["primary_class"] != row["primary_class"]:
            raise AssertionError(f"synthetic {name} is not deterministic")
    overlap = _gaussian(width, 38, 3.5, 8000) + _gaussian(width, 88, 3.5, 14000)
    overlap_row, _nodes = classify_volume(0, overlap)
    if not (overlap_row["flag_p"] and overlap_row["flag_bimodal"] and overlap_row["conflict"]):
        raise AssertionError(
            "synthetic top-heavy double distribution should keep both flags and stay unclassified: "
            f"class={overlap_row['primary_class']} P={overlap_row['flag_p']} B={overlap_row['flag_bimodal']} "
            f"major={overlap_row['n_major_peaks']} poc={overlap_row['poc_location']:.3f} "
            f"sep={overlap_row['normalized_separation']} depth={overlap_row['valley_depth']} "
            f"upper={overlap_row['upper_body_share']:.3f} above={overlap_row['volume_above_share']:.3f} "
            f"tails={overlap_row['lower_tail_width_10']:.3f}/{overlap_row['upper_tail_width_10']:.3f}"
        )
    if overlap_row["primary_class"] != CLASS_UNCLASSIFIED:
        raise AssertionError("overlapping flags were forced into one class")
    print("[self-check] synthetic P, b, D, B, unclassified, and overlap-conflict passed", flush=True)


def _grid(part: pd.DataFrame, corrupt: bool) -> tuple[int, np.ndarray] | None:
    if corrupt or part.empty:
        return None
    ordered = part.sort_values("price_ticks")
    ticks = ordered["price_ticks"].to_numpy(dtype=np.int64)
    if len(ticks) >= 2 and np.any(np.diff(ticks) != 1):
        return None
    if len(ticks) == 0:
        return None
    return int(ticks[0]), ordered["volume"].to_numpy(dtype=np.float64)


def build_dataset(
    prominence_frac: float = PROMINENCE_FRAC,
    separation_frac: float = SEPARATION_FRAC,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    meta = pd.read_parquet(RESULTS / "session_meta.parquet")
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    grouped = {key: part for key, part in raw.groupby("session_date", sort=False)}
    rows = []
    nodes = []
    for rec in meta.sort_values("session_date").to_dict(orient="records"):
        session = rec["session_date"]
        part = grouped.get(session, raw.iloc[0:0])
        grid = _grid(part, bool(rec["corrupt_range"]))
        noncontiguous = (not bool(rec["corrupt_range"])) and session in grouped and grid is None and len(grouped[session]) > 0
        if grid is None:
            blank, _node_rows = classify_volume(0, np.zeros(1), prominence_frac, separation_frac)
            for key in ("profile_low_ticks", "profile_high_ticks", "profile_low", "profile_high"):
                blank.pop(key, None)
            blank["degenerate"] = True
            blank["noncontiguous_grid"] = bool(noncontiguous)
            blank["volume_matches_meta"] = int(rec["total_volume"]) == 0
        else:
            blank, node_rows = classify_volume(grid[0], grid[1], prominence_frac, separation_frac)
            blank["noncontiguous_grid"] = False
            for node in node_rows:
                node["session_date"] = session
                nodes.append(node)
            blank["volume_matches_meta"] = int(round(float(grid[1].sum()))) == int(rec["total_volume"])
        merged = {**rec, **blank}
        merged["in_analysis_sample"] = bool(analysis_mask(pd.DataFrame([merged])).iloc[0])
        rows.append(merged)
    dataset = pd.DataFrame(rows)
    node_frame = pd.DataFrame(nodes)
    return dataset, node_frame


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    dataset, nodes = build_dataset()
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "profile_shape_dataset.parquet"
    dataset.to_parquet(out, index=False)
    nodes.to_parquet(RESULTS / "nodes.parquet", index=False)
    sample = dataset[dataset["in_analysis_sample"]]
    counts = sample["primary_class"].value_counts().to_dict()
    print(f"[shapes] sessions={len(dataset)} analysis={len(sample)} counts={counts}", flush=True)
    print(f"[shapes] wrote {out}", flush=True)


if __name__ == "__main__":
    main()
