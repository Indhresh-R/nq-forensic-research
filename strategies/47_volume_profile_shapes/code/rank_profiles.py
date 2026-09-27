"""Rank the frozen continuous scores. Does not change formulas or labels."""

from __future__ import annotations

import pandas as pd

from continuous_scores import SCORE_COLUMNS, SHAPE_ORDER
from frozen import RESULTS

COMPONENT_COLUMNS = {
    "P": ("P1", "P2", "P3", "P4"),
    "b": ("b1", "b2", "b3", "b4"),
    "D": ("D1", "D2", "D3", "D4"),
    "B": ("B1", "B2", "B3", "B4"),
}
GEOMETRY = (
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
)


def rank_scores(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for shape in SHAPE_ORDER:
        score_column = SCORE_COLUMNS[shape]
        ordered = scored.sort_values(
            [score_column, "session_date"],
            ascending=[False, True],
            kind="mergesort",
        ).reset_index(drop=True)
        components = COMPONENT_COLUMNS[shape]
        for rank, source in enumerate(ordered.itertuples(index=False), start=1):
            record = {
                "shape": shape,
                "rank": rank,
                "session_date": source.session_date,
                "score": getattr(source, score_column),
                "step1_label": source.primary_class,
                "component_1": getattr(source, components[0]),
                "component_2": getattr(source, components[1]),
                "component_3": getattr(source, components[2]),
                "component_4": getattr(source, components[3]),
                "component_1_name": components[0],
                "component_2_name": components[1],
                "component_3_name": components[2],
                "component_4_name": components[3],
            }
            for name in GEOMETRY:
                record[name] = getattr(source, name)
            if shape == "B":
                record["B_score_reason"] = source.B_score_reason
            rows.append(record)
    return pd.DataFrame(rows)


def main() -> None:
    scored = pd.read_parquet(RESULTS / "continuous_shape_scores.parquet")
    ranked = rank_scores(scored)
    out = RESULTS / "shape_rankings.csv"
    ranked.to_csv(out, index=False)
    print(f"[step1b] wrote {out} rows={len(ranked)}", flush=True)


if __name__ == "__main__":
    main()
