"""Apply the frozen verdict rule. This module does not choose buckets."""
from __future__ import annotations

import numpy as np
import pandas as pd

from definitions import DEPTH_POOLS, MIN_MEDIAN_SPREAD, MIN_POOL_N, PRIMARY_HORIZONS, SPEARMAN_FLAT


def _finite(series: pd.Series) -> np.ndarray:
    values = series.to_numpy(np.float64)
    return values[np.isfinite(values)]


def spearman(left: np.ndarray, right: np.ndarray) -> float:
    mask = np.isfinite(left) & np.isfinite(right)
    left = left[mask]
    right = right[mask]
    if len(left) < MIN_POOL_N:
        return float("nan")
    rank_left = pd.Series(left).rank().to_numpy(np.float64)
    rank_right = pd.Series(right).rank().to_numpy(np.float64)
    if float(rank_left.std()) == 0.0 or float(rank_right.std()) == 0.0:
        return float("nan")
    return float(np.corrcoef(rank_left, rank_right)[0, 1])


def relations(medians: dict[str, float]) -> tuple[int, ...] | None:
    """Pairwise order of shallow, mid, deep. None if any median is missing."""
    if any(not np.isfinite(medians[name]) for name in DEPTH_POOLS):
        return None
    signs: list[int] = []
    for index, left in enumerate(DEPTH_POOLS):
        for right in DEPTH_POOLS[index + 1 :]:
            gap = medians[right] - medians[left]
            if abs(gap) < 1e-12:
                signs.append(0)
            elif gap > 0.0:
                signs.append(1)
            else:
                signs.append(-1)
    return tuple(signs)


def pool_snapshot(frame: pd.DataFrame, horizon: str) -> dict:
    medians: dict[str, float] = {}
    counts: dict[str, int] = {}
    column = f"fwd_ret_rng_{horizon}"
    for name in DEPTH_POOLS:
        values = _finite(frame.loc[frame["retracement_pool"] == name, column])
        counts[name] = int(len(values))
        medians[name] = float(np.median(values)) if len(values) else float("nan")
    evaluable = all(counts[name] >= MIN_POOL_N for name in DEPTH_POOLS)
    order = relations(medians) if evaluable else None
    finite_medians = [medians[name] for name in DEPTH_POOLS if np.isfinite(medians[name])]
    spread = float(max(finite_medians) - min(finite_medians)) if len(finite_medians) == 3 else float("nan")
    return {
        "medians": medians,
        "counts": counts,
        "ordering": order,
        "spread": spread,
        "evaluable": evaluable and order is not None,
    }


def decide(panel: pd.DataFrame) -> dict:
    """Return the frozen verdict and the snapshots that produced it."""
    slices: dict[str, dict] = {}
    for label, frame in (
        ("combined", panel),
        ("bullish", panel[panel["direction"] == "bullish"]),
        ("bearish", panel[panel["direction"] == "bearish"]),
        ("IS", panel[panel["split"] == "IS"]),
        ("Validation", panel[panel["split"] == "Validation"]),
        ("OOS", panel[panel["split"] == "OOS"]),
    ):
        slices[label] = {horizon: pool_snapshot(frame, horizon) for horizon in PRIMARY_HORIZONS}

    rhos = {}
    for horizon in PRIMARY_HORIZONS:
        rhos[horizon] = spearman(
            panel["retracement_penetration_pct"].to_numpy(np.float64),
            panel[f"fwd_ret_rng_{horizon}"].to_numpy(np.float64),
        )

    def matched(horizon: str) -> bool:
        in_sample = slices["IS"][horizon]
        validation = slices["Validation"][horizon]
        if not in_sample["evaluable"] or not validation["evaluable"]:
            return False
        if in_sample["ordering"] != validation["ordering"]:
            return False
        if in_sample["spread"] < MIN_MEDIAN_SPREAD or validation["spread"] < MIN_MEDIAN_SPREAD:
            return False
        for side in ("bullish", "bearish"):
            side_slice = slices[side][horizon]
            if not side_slice["evaluable"] or side_slice["ordering"] != in_sample["ordering"]:
                return False
        out_of_sample = slices["OOS"][horizon]
        if not out_of_sample["evaluable"]:
            return False
        if out_of_sample["ordering"] != in_sample["ordering"]:
            return False
        if out_of_sample["spread"] < MIN_MEDIAN_SPREAD:
            return False
        return True

    supported = all(matched(horizon) for horizon in PRIMARY_HORIZONS)

    def disagreed(horizon: str) -> bool:
        in_sample = slices["IS"][horizon]
        validation = slices["Validation"][horizon]
        if not in_sample["evaluable"] or not validation["evaluable"]:
            return False
        return in_sample["ordering"] != validation["ordering"]

    correlations_flat = all(
        (not np.isfinite(rhos[horizon])) or abs(rhos[horizon]) < SPEARMAN_FLAT for horizon in PRIMARY_HORIZONS
    )
    not_supported = all(disagreed(horizon) for horizon in PRIMARY_HORIZONS) and correlations_flat

    if supported:
        verdict = "MECHANISM SUPPORTED"
    elif not_supported:
        verdict = "MECHANISM NOT SUPPORTED"
    else:
        verdict = "MECHANISM UNCLEAR"

    return {"verdict": verdict, "slices": slices, "spearman_30m": rhos["30m"], "spearman_60m": rhos["60m"]}
