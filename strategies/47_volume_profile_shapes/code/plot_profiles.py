"""Draw preregistered example profiles. Does not change labels."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from detect_shapes import _grid
from frozen import (
    CLASS_B_DOUBLE,
    CLASS_B_LOWER,
    CLASS_D,
    CLASS_P,
    CLASS_UNCLASSIFIED,
    FIGURES,
    PRIMARY_CLASSES,
    RANDOM_EXAMPLES,
    RESULTS,
    RNG_SEED,
    TICK_SIZE,
)

FILE_TAG = {
    CLASS_P: "P_like",
    CLASS_B_LOWER: "b_lower",
    CLASS_D: "D_like",
    CLASS_B_DOUBLE: "B_double",
    CLASS_UNCLASSIFIED: "UNCLASSIFIED",
}
SCORE = {
    CLASS_P: "p_strength",
    CLASS_B_LOWER: "b_strength",
    CLASS_D: "d_strength",
    CLASS_B_DOUBLE: "bimodal_strength",
}


def _load_grids() -> dict[str, tuple[int, np.ndarray]]:
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    meta = pd.read_parquet(RESULTS / "session_meta.parquet")
    corrupt = dict(zip(meta["session_date"], meta["corrupt_range"]))
    grids = {}
    for session, part in raw.groupby("session_date", sort=False):
        grid = _grid(part, bool(corrupt.get(session, False)))
        if grid is not None:
            grids[str(session)] = grid
    return grids


def _plot(grid: tuple[int, np.ndarray], row: pd.Series, path, heading: str) -> None:
    low_tick, volume = grid
    prices = (low_tick + np.arange(len(volume))) * TICK_SIZE
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.fill_betweenx(prices, 0, volume, step="mid", color="#4C78A8")
    if pd.notna(row["poc"]):
        ax.axhline(float(row["poc"]), color="black", lw=1.0, label="POC")
    first_peak = True
    for price, vol in zip(json.loads(row["major_max_prices"]), json.loads(row["major_max_volumes"])):
        ax.plot(
            vol,
            price,
            marker="o",
            color="black",
            ms=5,
            label="major maximum" if first_peak else None,
        )
        first_peak = False
    if pd.notna(row["valley_price"]):
        ax.plot(float(row["valley_volume"]), float(row["valley_price"]), marker="x", color="0.2", ms=8, label="valley")
    depth = "n/a" if pd.isna(row["valley_depth"]) else f"{float(row['valley_depth']):.2f}"
    sep = "n/a" if pd.isna(row["normalized_separation"]) else f"{float(row['normalized_separation']):.2f}"
    ax.set_title(
        f"{heading}\n{row['session_date']}  {row['primary_class']}"
        f"  POC loc {float(row['poc_location']):.2f}  sep {sep}  valley depth {depth}"
    )
    ax.set_xlabel("Executed volume")
    ax.set_ylabel("Price")
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend(loc="best", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _record(kind: str, row: pd.Series, path) -> dict:
    return {
        "kind": kind,
        "session_date": str(row["session_date"]),
        "primary_class": str(row["primary_class"]),
        "path": str(path.relative_to(RESULTS.parent)).replace("\\", "/"),
        "poc_location": None if pd.isna(row["poc_location"]) else float(row["poc_location"]),
        "rule_shortfall": None if pd.isna(row["rule_shortfall"]) else float(row["rule_shortfall"]),
        "conflict": bool(row["conflict"]),
    }


def main() -> None:
    dataset = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    grids = _load_grids()
    sample = dataset[dataset["in_analysis_sample"]].copy()
    FIGURES.mkdir(parents=True, exist_ok=True)
    manifest = {"strongest": {}, "ambiguous": None, "random": {}, "roll_artifact": None, "missing": []}

    for name in (CLASS_P, CLASS_B_LOWER, CLASS_D, CLASS_B_DOUBLE):
        part = sample[sample["primary_class"] == name].sort_values(
            [SCORE[name], "session_date"], ascending=[False, True]
        )
        tag = FILE_TAG[name]
        if part.empty:
            manifest["missing"].append(f"no analysis-sample session with primary label {name}")
            continue
        row = part.iloc[0]
        path = FIGURES / f"strongest_{tag}.png"
        grid = grids.get(str(row["session_date"]))
        if grid is None:
            manifest["missing"].append(f"no grid for strongest {name} {row['session_date']}")
            continue
        _plot(grid, row, path, f"Strongest {name} by preregistered score")
        manifest["strongest"][name] = _record("strongest", row, path)

    unclass = sample[sample["primary_class"] == CLASS_UNCLASSIFIED].sort_values(
        ["rule_shortfall", "session_date"], ascending=[True, True]
    )
    if unclass.empty:
        manifest["missing"].append("no unclassified session in the analysis sample")
    else:
        row = unclass.iloc[0]
        path = FIGURES / "ambiguous_unclassified.png"
        grid = grids.get(str(row["session_date"]))
        if grid is None:
            manifest["missing"].append(f"no grid for ambiguous {row['session_date']}")
        else:
            if bool(row["conflict"]):
                held = []
                if bool(row["flag_p"]):
                    held.append("P-like")
                if bool(row["flag_b"]):
                    held.append("b-like")
                if bool(row["flag_d"]):
                    held.append("D-like")
                if bool(row["flag_bimodal"]):
                    held.append("B-like")
                heading = "Unclassified conflict: " + " and ".join(held)
            else:
                heading = "Unclassified, smallest rule shortfall"
            _plot(grid, row, path, heading)
            manifest["ambiguous"] = _record("ambiguous", row, path)

    rng = np.random.default_rng(RNG_SEED)
    for name in PRIMARY_CLASSES:
        part = sample[sample["primary_class"] == name].sort_values("session_date")
        manifest["random"][name] = []
        if part.empty:
            continue
        take = min(RANDOM_EXAMPLES, len(part))
        chosen = sorted(int(i) for i in rng.choice(len(part), size=take, replace=False))
        tag = FILE_TAG[name]
        for nth, idx in enumerate(chosen, start=1):
            row = part.iloc[idx]
            path = FIGURES / f"random_{tag}_{nth}.png"
            grid = grids.get(str(row["session_date"]))
            if grid is None:
                manifest["missing"].append(f"no grid for random {name} {row['session_date']}")
                continue
            _plot(grid, row, path, f"Random {name} draw {nth} of {take}, seed {RNG_SEED}")
            manifest["random"][name].append(_record("random", row, path))

    rolls = dataset[(~dataset["in_analysis_sample"]) & dataset["is_roll_transition"] & (dataset["primary_class"] == CLASS_B_DOUBLE)]
    rolls = rolls.sort_values(["bimodal_strength", "session_date"], ascending=[False, True])
    if len(rolls):
        row = rolls.iloc[0]
        path = FIGURES / "roll_artifact_B_like.png"
        grid = grids.get(str(row["session_date"]))
        if grid is not None:
            _plot(grid, row, path, "Roll transition labeled B-like (data artifact, not an example)")
            manifest["roll_artifact"] = _record("roll_artifact", row, path)

    (RESULTS / "plot_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[plots] wrote {FIGURES}", flush=True)


if __name__ == "__main__":
    main()
