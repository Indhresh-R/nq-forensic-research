"""Score frozen forecasts. No thresholds are chosen from the results."""
from __future__ import annotations

import numpy as np
import pandas as pd

from definitions import MODELS, PRIMARY, SECONDARY, SPLIT_ORDER


def slice_names(frame: pd.DataFrame) -> list[str]:
    years = sorted(int(year) for year in frame["year"].unique())
    names = list(SPLIT_ORDER) + [str(year) for year in years]
    if (frame["split"] == "OTHER").any():
        names.append("OTHER")
    return names


def slice_mask(frame: pd.DataFrame, slice_name: str) -> pd.Series:
    if slice_name == "All":
        return pd.Series(True, index=frame.index)
    if slice_name in {"IS", "Validation", "OOS", "OTHER"}:
        return frame["split"] == slice_name
    return frame["year"] == int(slice_name)


def model_sign(frame: pd.DataFrame, model: str) -> pd.Series:
    test1 = frame["test1_sign"]
    test2 = frame["test2_sign"]
    if model == "test1_bull":
        return test1.where(test1 == 1)
    if model == "test1_bear":
        return test1.where(test1 == -1)
    if model == "test1_pooled":
        return test1
    if model == "test2_up":
        return test2.where(test2 == 1)
    if model == "test2_down":
        return test2.where(test2 == -1)
    if model == "test2_pooled":
        return test2
    if model == "always_long":
        return frame["always_long_sign"]
    raise ValueError(model)


def outcome_columns(outcome: str) -> tuple[str, str]:
    if outcome == PRIMARY:
        return "primary_sign", "body"
    if outcome == SECONDARY:
        return "secondary_sign", "close_to_close"
    raise ValueError(outcome)


def base_rates(outcome_sign: np.ndarray) -> tuple[float, float, float]:
    n = len(outcome_sign)
    if n == 0:
        return (np.nan, np.nan, np.nan)
    return (
        float(np.mean(outcome_sign == 1)),
        float(np.mean(outcome_sign == -1)),
        float(np.mean(outcome_sign == 0)),
    )


def summarize(
    sign: np.ndarray,
    outcome_sign: np.ndarray,
    points: np.ndarray,
    p_up: float,
    p_down: float,
    p_flat: float,
) -> dict[str, float | int]:
    n = int(len(sign))
    empty = {
        "n": 0,
        "n_flat": 0,
        "n_up_forecasts": 0,
        "n_down_forecasts": 0,
        "hit_rate": np.nan,
        "p_up": p_up,
        "p_down": p_down,
        "p_flat": p_flat,
        "matched_base_rate": np.nan,
        "lift": np.nan,
        "mean_signed_body": np.nan,
        "median_signed_body": np.nan,
    }
    if n == 0:
        return empty
    flat = outcome_sign == 0
    n_up = int(np.sum(sign == 1))
    n_down = int(np.sum(sign == -1))
    hits = int(np.sum((sign == outcome_sign) & ~flat))
    hit_rate = hits / n
    matched = (n_up * p_up + n_down * p_down) / n
    signed = sign.astype(np.float64) * points
    return {
        "n": n,
        "n_flat": int(np.sum(flat)),
        "n_up_forecasts": n_up,
        "n_down_forecasts": n_down,
        "hit_rate": float(hit_rate),
        "p_up": float(p_up),
        "p_down": float(p_down),
        "p_flat": float(p_flat),
        "matched_base_rate": float(matched),
        "lift": float(hit_rate - matched),
        "mean_signed_body": float(np.mean(signed)),
        "median_signed_body": float(np.median(signed)),
    }


def metrics_table(frame: pd.DataFrame, outcome: str) -> pd.DataFrame:
    outcome_col, points_col = outcome_columns(outcome)
    rows: list[dict[str, object]] = []
    for slice_name in slice_names(frame):
        slice_frame = frame.loc[slice_mask(frame, slice_name)]
        p_up, p_down, p_flat = base_rates(slice_frame[outcome_col].to_numpy())
        for model in MODELS:
            sign = model_sign(slice_frame, model)
            keep = sign.notna()
            chosen_sign = sign.loc[keep].to_numpy(dtype=np.int8)
            chosen = slice_frame.loc[keep]
            summary = summarize(
                chosen_sign,
                chosen[outcome_col].to_numpy(dtype=np.int8),
                chosen[points_col].to_numpy(dtype=np.float64),
                p_up,
                p_down,
                p_flat,
            )
            rows.append({"outcome": outcome, "model": model, "slice": slice_name, **summary})
    return pd.DataFrame(rows)


def agreement_table(frame: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Test 1 days that also have a Test 2 forecast, split by agreement."""
    outcome_col, points_col = outcome_columns(outcome)
    both = frame.loc[frame["test1_sign"].notna() & frame["test2_sign"].notna()].copy()
    both["agree"] = both["test1_sign"] == both["test2_sign"]
    rows: list[dict[str, object]] = []
    for slice_name in slice_names(frame):
        slice_frame = both.loc[slice_mask(both, slice_name)]
        blocks = {
            "agree": slice_frame.loc[slice_frame["agree"]],
            "disagree": slice_frame.loc[~slice_frame["agree"]],
            "all_test1": slice_frame,
        }
        for block, chosen in blocks.items():
            p_up, p_down, p_flat = base_rates(
                frame.loc[slice_mask(frame, slice_name), outcome_col].to_numpy()
            )
            for model, sign_col in (("test1", "test1_sign"), ("test2", "test2_sign")):
                summary = summarize(
                    chosen[sign_col].to_numpy(dtype=np.int8),
                    chosen[outcome_col].to_numpy(dtype=np.int8),
                    chosen[points_col].to_numpy(dtype=np.float64),
                    p_up,
                    p_down,
                    p_flat,
                )
                rows.append(
                    {
                        "outcome": outcome,
                        "block": block,
                        "model": model,
                        "slice": slice_name,
                        **summary,
                    }
                )
    return pd.DataFrame(rows)
