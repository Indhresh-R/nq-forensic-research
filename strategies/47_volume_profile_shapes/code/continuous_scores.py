"""Continuous P/b/D/B similarity scores from stored Step 1 geometry.

Formulas are frozen in STEP1B_PREREGISTRATION.md. This module does not
classify profiles and does not read prices beyond the saved Step 1 tables.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from detect_shapes import analysis_mask
from frozen import RESULTS

EXPECTED_N = 96
EXPECTED_COUNTS = {
    "P-like": 1,
    "b-like": 2,
    "D-like": 0,
    "B-like": 7,
    "UNCLASSIFIED": 86,
}
P_INPUTS = (
    "poc_location",
    "volume_above_share",
    "lower_tail_width_10",
    "upper_tail_width_10",
    "upper_body_share",
)
B_SHAPE_INPUTS = (
    "poc_location",
    "volume_below_share",
    "lower_tail_width_10",
    "upper_tail_width_10",
    "lower_body_share",
)
D_INPUTS = (
    "poc_location",
    "volume_above_share",
    "lower_tail_width_10",
    "upper_tail_width_10",
    "n_major_peaks",
)
SHAPE_ORDER = ("P", "b", "D", "B")
SCORE_COLUMNS = {
    "P": "P_score",
    "b": "b_score",
    "D": "D_score",
    "B": "B_score",
}


def _clip(values: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(values, dtype=np.float64), 0.0, 1.0)


def _require_finite(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    bad = []
    for column in columns:
        mask = ~np.isfinite(frame[column].to_numpy(dtype=np.float64))
        if mask.any():
            dates = frame.loc[mask, "session_date"].astype(str).tolist()
            bad.append(f"{column}: {dates}")
    if bad:
        raise SystemExit(f"Non-finite {label} inputs. Stopping.\n" + "\n".join(bad))


def d4_from_counts(n_major: np.ndarray) -> np.ndarray:
    counts = np.asarray(n_major, dtype=np.int64)
    scores = np.zeros(len(counts), dtype=np.float64)
    scores[counts == 1] = 1.0
    scores[counts == 2] = 0.5
    scores[counts == 3] = 0.25
    return scores


def score_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return one row per input row. Does not rank or plot."""
    _require_finite(frame, P_INPUTS, "P")
    _require_finite(frame, B_SHAPE_INPUTS, "b")
    _require_finite(frame, D_INPUTS, "D")

    poc = frame["poc_location"].to_numpy(dtype=np.float64)
    above = frame["volume_above_share"].to_numpy(dtype=np.float64)
    below = frame["volume_below_share"].to_numpy(dtype=np.float64)
    lower_tail = frame["lower_tail_width_10"].to_numpy(dtype=np.float64)
    upper_tail = frame["upper_tail_width_10"].to_numpy(dtype=np.float64)
    upper_body = frame["upper_body_share"].to_numpy(dtype=np.float64)
    lower_body = frame["lower_body_share"].to_numpy(dtype=np.float64)
    n_major = frame["n_major_peaks"].to_numpy(dtype=np.int64)
    n_local = frame["n_local_maxima"].to_numpy(dtype=np.int64)

    p1 = _clip((poc - 0.50) / 0.30)
    p2 = _clip((above - 0.50) / 0.20)
    p3 = _clip((lower_tail - upper_tail) / 0.30)
    p4 = _clip((upper_body - 0.33) / 0.27)
    p_score = (p1 + p2 + p3 + p4) / 4.0

    b1 = _clip((0.50 - poc) / 0.30)
    b2 = _clip((below - 0.50) / 0.20)
    b3 = _clip((upper_tail - lower_tail) / 0.30)
    b4 = _clip((lower_body - 0.33) / 0.27)
    b_score = (b1 + b2 + b3 + b4) / 4.0

    d1 = _clip(1.0 - np.abs(poc - 0.50) / 0.30)
    d2 = _clip(1.0 - np.abs(above - 0.50) / 0.25)
    d3 = _clip(1.0 - np.abs(upper_tail - lower_tail) / 0.30)
    d4 = d4_from_counts(n_major)
    d_score = (d1 + d2 + d3 + d4) / 4.0

    two = n_local >= 2
    separation = frame["normalized_separation"].to_numpy(dtype=np.float64)
    valley = frame["valley_depth"].to_numpy(dtype=np.float64)
    balance = frame["peak_balance"].to_numpy(dtype=np.float64)
    peak1 = frame["peak1_volume"].to_numpy(dtype=np.float64)
    peak2 = frame["peak2_volume"].to_numpy(dtype=np.float64)
    poc_volume = frame["poc_volume"].to_numpy(dtype=np.float64)
    weak = np.minimum(peak1, peak2) / poc_volume

    b1s = np.zeros(len(frame), dtype=np.float64)
    b2s = np.zeros(len(frame), dtype=np.float64)
    b3s = np.zeros(len(frame), dtype=np.float64)
    b4s = np.zeros(len(frame), dtype=np.float64)
    reasons: list[str] = []
    finite_sep = np.isfinite(separation)
    finite_valley = np.isfinite(valley)
    finite_balance = np.isfinite(balance)
    finite_weak = np.isfinite(weak)
    b1s[two & finite_sep] = _clip((separation[two & finite_sep] - 0.05) / 0.25)
    b2s[two & finite_valley] = _clip((valley[two & finite_valley] - 0.20) / 0.70)
    b3s[two & finite_balance] = _clip((balance[two & finite_balance] - 0.20) / 0.80)
    b4s[two & finite_weak] = _clip((weak[two & finite_weak] - 0.30) / 0.70)
    b_total = (b1s + b2s + b3s + b4s) / 4.0

    for i in range(len(frame)):
        if not two[i]:
            reasons.append("fewer than two prominence-qualified local maxima")
            continue
        missing = []
        if not finite_sep[i]:
            missing.append("normalized_separation")
        if not finite_valley[i]:
            missing.append("valley_depth")
        if not finite_balance[i]:
            missing.append("peak_balance")
        if not finite_weak[i]:
            missing.append("weak_peak_strength")
        reasons.append("missing " + ",".join(missing) if missing else "")

    matrix = np.column_stack([p_score, b_score, d_score, b_total])
    top_score = matrix.max(axis=1)
    order = np.sort(matrix, axis=1)
    second_score = order[:, -2]
    is_top = matrix == top_score[:, None]
    top_index = np.argmax(is_top, axis=1)
    names = np.asarray(SHAPE_ORDER, dtype=object)
    out = frame[["session_date"]].copy()
    out["primary_class"] = frame["primary_class"].astype(str).to_numpy()
    out["P1"] = p1
    out["P2"] = p2
    out["P3"] = p3
    out["P4"] = p4
    out["P_score"] = p_score
    out["b1"] = b1
    out["b2"] = b2
    out["b3"] = b3
    out["b4"] = b4
    out["b_score"] = b_score
    out["D1"] = d1
    out["D2"] = d2
    out["D3"] = d3
    out["D4"] = d4
    out["D_score"] = d_score
    out["B1"] = b1s
    out["B2"] = b2s
    out["B3"] = b3s
    out["B4"] = b4s
    out["B_score"] = b_total
    out["B_score_reason"] = reasons
    out["zero_major_peaks"] = n_major == 0
    out["top_shape"] = names[top_index]
    out["top_shape_tie"] = is_top.sum(axis=1) > 1
    out["top_score"] = top_score
    out["second_score"] = second_score
    out["shape_margin"] = top_score - second_score
    out["shape_ambiguity"] = 1.0 - (top_score - second_score)
    keep = (
        "poc_location",
        "volume_above_share",
        "volume_below_share",
        "lower_tail_width_10",
        "upper_tail_width_10",
        "upper_body_share",
        "lower_body_share",
        "n_major_peaks",
        "n_local_maxima",
        "normalized_separation",
        "valley_depth",
        "peak_balance",
        "peak1_volume",
        "peak2_volume",
        "poc_volume",
    )
    for column in keep:
        out[column] = frame[column].to_numpy()
    return out.reset_index(drop=True)


def verify_sample(dataset: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    mask = analysis_mask(dataset)
    stored = dataset["in_analysis_sample"].astype(bool)
    if not mask.equals(stored):
        mismatch = dataset.loc[mask != stored, "session_date"].astype(str).tolist()
        raise SystemExit(
            "in_analysis_sample does not match analysis_mask. Stopping. "
            f"Sessions: {mismatch}"
        )
    sample = dataset.loc[stored].copy()
    sample["session_date"] = sample["session_date"].astype(str)
    if sample["session_date"].duplicated().any():
        raise SystemExit("Duplicate analysis session_date values. Stopping.")
    if len(sample) != EXPECTED_N:
        raise SystemExit(f"Analysis sample is {len(sample)}, expected {EXPECTED_N}. Stopping.")
    labels = sample["primary_class"].astype(str)
    unexpected = sorted(set(labels) - set(EXPECTED_COUNTS))
    counts = {label: int((labels == label).sum()) for label in EXPECTED_COUNTS}
    if unexpected or counts != EXPECTED_COUNTS:
        raise SystemExit(
            f"Step 1 label counts differ. Stopping. Found {counts}, unexpected {unexpected}."
        )
    raw_dates = set(raw["session_date"].astype(str))
    missing = sorted(set(sample["session_date"]) - raw_dates)
    if missing:
        raise SystemExit(f"Raw profiles missing for {missing}. Stopping.")
    totals = raw.groupby(raw["session_date"].astype(str))["volume"].sum()
    for row in sample.itertuples(index=False):
        raw_volume = float(totals.loc[row.session_date])
        if int(round(raw_volume)) != int(row.total_volume):
            raise SystemExit(
                f"Raw volume does not match session total for {row.session_date}. Stopping."
            )
    return sample.sort_values("session_date").reset_index(drop=True)


def _assert_formula_anchors() -> None:
    frame = pd.DataFrame(
        {
            "session_date": ["a", "b"],
            "primary_class": ["UNCLASSIFIED", "UNCLASSIFIED"],
            "poc_location": [0.80, 0.20],
            "volume_above_share": [0.70, 0.25],
            "volume_below_share": [0.30, 0.75],
            "lower_tail_width_10": [0.30, 0.00],
            "upper_tail_width_10": [0.00, 0.30],
            "upper_body_share": [0.60, 0.33],
            "lower_body_share": [0.33, 0.60],
            "n_major_peaks": [1, 4],
            "n_local_maxima": [2, 1],
            "normalized_separation": [0.30, np.nan],
            "valley_depth": [0.90, np.nan],
            "peak_balance": [1.0, np.nan],
            "peak1_volume": [100.0, np.nan],
            "peak2_volume": [100.0, np.nan],
            "poc_volume": [100.0, 100.0],
        }
    )
    scored = score_frame(frame)
    first = scored.iloc[0]
    second = scored.iloc[1]
    if not np.isclose(first["P_score"], 1.0):
        raise SystemExit(f"P anchor failed: {first['P_score']}")
    if not np.isclose(first["b_score"], 0.0):
        raise SystemExit(f"b anchor failed: {first['b_score']}")
    if not np.isclose(first["D1"], 0.0) or not np.isclose(first["D4"], 1.0):
        raise SystemExit("D anchor failed")
    if not np.isclose(first["B_score"], 1.0):
        raise SystemExit(f"B anchor failed: {first['B_score']}")
    if not np.isclose(second["b_score"], 1.0):
        raise SystemExit(f"mirror b anchor failed: {second['b_score']}")
    if second["B_score"] != 0.0 or not second["B_score_reason"]:
        raise SystemExit("B zero-peak rule failed")
    if second["D4"] != 0.0:
        raise SystemExit("D4 4+ rule failed")


def main() -> None:
    _assert_formula_anchors()
    dataset = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    sample = verify_sample(dataset, raw)
    scored = score_frame(sample)
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "continuous_shape_scores.parquet"
    scored.to_parquet(out, index=False)
    verification = {
        "analysis_sessions": int(len(scored)),
        "session_dates": scored["session_date"].astype(str).tolist(),
        "step1_counts": EXPECTED_COUNTS,
        "mask_matches_stored_flag": True,
        "raw_volume_matches_session_total": True,
        "zero_major_peak_sessions": int(scored["zero_major_peaks"].sum()),
    }
    (RESULTS / "step1b_verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(f"[step1b] verified {len(scored)} sessions and wrote {out}", flush=True)


if __name__ == "__main__":
    main()
