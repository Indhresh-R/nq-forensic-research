"""Distribution, Step 1 comparison, and recompute-stability diagnostics.

Does not change the frozen formulas or replace the primary score table.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from continuous_scores import SCORE_COLUMNS, SHAPE_ORDER, score_frame
from detect_shapes import _grid, classify_volume
from frozen import RESULTS

COMPARE_COLUMNS = (
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
PERCENTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
ABOVE = (0.50, 0.60, 0.70, 0.80)
STEP1_LABELS = ("P-like", "b-like", "D-like", "B-like", "UNCLASSIFIED")


def distribution_table(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for shape in SHAPE_ORDER:
        values = scored[SCORE_COLUMNS[shape]].to_numpy(dtype=np.float64)
        quantiles = np.quantile(values, list(PERCENTILES), method="linear")
        row = {
            "shape": shape,
            "n": int(len(values)),
            "minimum": float(values.min()),
            "p10": float(quantiles[0]),
            "p25": float(quantiles[1]),
            "median": float(quantiles[2]),
            "p75": float(quantiles[3]),
            "p90": float(quantiles[4]),
            "maximum": float(values.max()),
        }
        for level in ABOVE:
            row[f"n_above_{level:.2f}"] = int(np.sum(values > level))
        rows.append(row)
    return pd.DataFrame(rows)


def step1_median_table(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label in STEP1_LABELS:
        part = scored[scored["primary_class"] == label]
        row = {"table": "step1_medians", "step1_label": label, "n": int(len(part))}
        for shape in SHAPE_ORDER:
            column = SCORE_COLUMNS[shape]
            row[f"median_{shape}"] = float(part[column].median()) if len(part) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def top10_table(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for shape in SHAPE_ORDER:
        column = SCORE_COLUMNS[shape]
        ordered = scored.sort_values([column, "session_date"], ascending=[False, True], kind="mergesort")
        top = ordered.head(10)[column]
        rows.append(
            {
                "table": "top10_vs_all",
                "shape": shape,
                "top_score": float(top.iloc[0]),
                "median_top10": float(top.median()),
                "median_all_96": float(ordered[column].median()),
            }
        )
    return pd.DataFrame(rows)


def named_step1_scores(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, shape, column in (
        ("P-like", "P", "P_score"),
        ("b-like", "b", "b_score"),
        ("D-like", "D", "D_score"),
        ("B-like", "B", "B_score"),
    ):
        ordered = scored.sort_values([column, "session_date"], ascending=[False, True], kind="mergesort")
        ranks = {date: rank for rank, date in enumerate(ordered["session_date"].tolist(), start=1)}
        part = scored[scored["primary_class"] == label]
        for source in part.itertuples(index=False):
            rows.append(
                {
                    "table": "step1_named_sessions",
                    "step1_label": label,
                    "session_date": source.session_date,
                    "matching_shape": shape,
                    "matching_score": getattr(source, column),
                    "rank_on_matching_score": ranks[source.session_date],
                    "P_score": source.P_score,
                    "b_score": source.b_score,
                    "D_score": source.D_score,
                    "B_score": source.B_score,
                }
            )
    return pd.DataFrame(rows)


def _top10_dates(frame: pd.DataFrame, column: str) -> list[str]:
    ordered = frame.sort_values([column, "session_date"], ascending=[False, True], kind="mergesort")
    return ordered["session_date"].astype(str).head(10).tolist()


def stability_check(scored: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    grouped = {str(key): part for key, part in raw.groupby(raw["session_date"].astype(str), sort=False)}
    recomputed_rows = []
    max_abs = {column: 0.0 for column in COMPARE_COLUMNS}
    for source in scored.itertuples(index=False):
        part = grouped[str(source.session_date)]
        grid = _grid(part, False)
        if grid is None:
            raise SystemExit(f"Could not rebuild the stored grid for {source.session_date}. Stopping.")
        geometry, _nodes = classify_volume(grid[0], grid[1])
        geometry["session_date"] = str(source.session_date)
        geometry["primary_class"] = source.primary_class
        recomputed_rows.append(geometry)
        for column in COMPARE_COLUMNS:
            left = getattr(source, column)
            right = geometry[column]
            left_missing = pd.isna(left)
            right_missing = pd.isna(right)
            if left_missing and right_missing:
                continue
            if left_missing or right_missing:
                max_abs[column] = max(max_abs[column], 1.0)
                continue
            diff = abs(float(left) - float(right))
            if diff > max_abs[column]:
                max_abs[column] = diff
    recomputed = score_frame(pd.DataFrame(recomputed_rows))
    merged = scored.merge(recomputed, on="session_date", suffixes=("_stored", "_recomputed"))
    rows = [{"check": f"max_abs_{column}", "value": max_abs[column]} for column in COMPARE_COLUMNS]
    for shape in SHAPE_ORDER:
        column = SCORE_COLUMNS[shape]
        diff = (merged[f"{column}_stored"] - merged[f"{column}_recomputed"]).abs()
        stored_top = set(_top10_dates(scored, column))
        recomputed_top = set(_top10_dates(recomputed, column))
        rows.append({"check": f"max_abs_{column}", "value": float(diff.max())})
        rows.append({"check": f"top10_overlap_{shape}", "value": float(len(stored_top & recomputed_top))})
    return pd.DataFrame(rows)


def main() -> None:
    scored = pd.read_parquet(RESULTS / "continuous_shape_scores.parquet")
    scored["session_date"] = scored["session_date"].astype(str)
    distributions = distribution_table(scored)
    distributions.to_csv(RESULTS / "score_distributions.csv", index=False)
    summary = pd.concat(
        [step1_median_table(scored), top10_table(scored), named_step1_scores(scored)],
        ignore_index=True,
    )
    summary.to_csv(RESULTS / "score_summary.csv", index=False)
    stability = stability_check(scored)
    stability.to_csv(RESULTS / "stability_diagnostic.csv", index=False)
    print(distributions.to_string(index=False), flush=True)
    print(stability.to_string(index=False), flush=True)
    print("[step1b] wrote distribution, summary, and stability tables", flush=True)


if __name__ == "__main__":
    main()
