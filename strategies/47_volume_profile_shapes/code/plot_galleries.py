"""Draw ranked profile galleries from the frozen scores and stored grids.

The ranking decides which sessions appear. This module does not rescore them.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from continuous_scores import SCORE_COLUMNS, SHAPE_ORDER
from detect_shapes import _grid
from frozen import FIGURES, RESULTS, TICK_SIZE

# Windows folds top_b and top_B onto one directory, and gallery_b.png onto
# gallery_B.png. These names keep the two rankings as separate files.
FOLDER = {
    "P": "top_P",
    "b": "top_b_lower",
    "D": "top_D",
    "B": "top_B_double",
}
GALLERY = {
    "P": "gallery_P.png",
    "b": "gallery_b_lower.png",
    "D": "gallery_D.png",
    "B": "gallery_B_double.png",
}
COMPONENT_COLUMNS = {
    "P": ("P1", "P2", "P3", "P4"),
    "b": ("b1", "b2", "b3", "b4"),
    "D": ("D1", "D2", "D3", "D4"),
    "B": ("B1", "B2", "B3", "B4"),
}
FILL = "#4C78A8"
SINGLE_SIZE = (7.2, 8.0)
GALLERY_SIZE = (11.5, 24.0)
DPI = 130


def load_grids() -> dict[str, tuple[int, np.ndarray]]:
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    grids = {}
    for session, part in raw.groupby(raw["session_date"].astype(str), sort=False):
        grid = _grid(part, False)
        if grid is not None:
            grids[str(session)] = grid
    return grids


def _fmt(value: object) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)) or pd.isna(value):
        return "n/a"
    return f"{float(value):.2f}"


def _draw(ax, grid: tuple[int, np.ndarray], dataset_row: pd.Series, heading: str, note: str) -> None:
    low_tick, volume = grid
    prices = (low_tick + np.arange(len(volume))) * TICK_SIZE
    ax.fill_betweenx(prices, 0, volume, step="mid", color=FILL)
    ax.set_xlim(0, float(volume.max()) * 1.08)
    pad = 0.25 if len(prices) < 3 else 0.0
    ax.set_ylim(float(prices[0]) - pad, float(prices[-1]) + pad)
    if pd.notna(dataset_row["poc"]):
        ax.axhline(float(dataset_row["poc"]), color="black", lw=1.0, label="POC")
    midpoint = (float(prices[0]) + float(prices[-1])) / 2.0
    ax.axhline(midpoint, color="0.45", lw=0.6, ls="--", label="range midpoint")
    first_major = True
    prices_major = json.loads(dataset_row["major_max_prices"])
    volumes_major = json.loads(dataset_row["major_max_volumes"])
    for price, vol in zip(prices_major, volumes_major):
        ax.plot(vol, price, marker="o", color="black", ms=4.5, label="major peak" if first_major else None)
        first_major = False
    major_keys = {(round(float(price), 4), round(float(vol), 4)) for price, vol in zip(prices_major, volumes_major)}
    first_pair = True
    for price, vol in (
        (dataset_row["peak1_price"], dataset_row["peak1_volume"]),
        (dataset_row["peak2_price"], dataset_row["peak2_volume"]),
    ):
        if pd.isna(price) or pd.isna(vol):
            continue
        key = (round(float(price), 4), round(float(vol), 4))
        if key in major_keys:
            continue
        ax.plot(
            float(vol),
            float(price),
            marker="s",
            color="black",
            ms=4.5,
            fillstyle="none",
            label="other local max used in B pair" if first_pair else None,
        )
        first_pair = False
    if pd.notna(dataset_row["valley_price"]):
        ax.plot(
            float(dataset_row["valley_volume"]),
            float(dataset_row["valley_price"]),
            marker="x",
            color="black",
            ms=7,
            label="valley",
        )
    ax.set_title(heading, fontsize=9)
    ax.set_xlabel("Executed volume", fontsize=8)
    ax.set_ylabel("Price", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.text(
        0.98,
        0.02,
        note,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        family="monospace",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "0.8", "alpha": 0.9},
    )
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend(loc="upper left", frameon=False, fontsize=6)


def _heading(date: str, label: str, score_text: str) -> str:
    return f"{date}   {score_text}\nStep 1: {label}"


def _component_note(row: pd.Series, shape: str) -> str:
    names = COMPONENT_COLUMNS[shape]
    parts = "  ".join(f"{name}={_fmt(row[name])}" for name in names)
    return (
        f"{parts}\n"
        f"POC loc {_fmt(row['poc_location'])}  above {_fmt(row['volume_above_share'])}\n"
        f"tails L {_fmt(row['lower_tail_width_10'])} U {_fmt(row['upper_tail_width_10'])}\n"
        f"body U {_fmt(row['upper_body_share'])} L {_fmt(row['lower_body_share'])}\n"
        f"major {int(row['n_major_peaks'])}  sep {_fmt(row['normalized_separation'])}\n"
        f"valley {_fmt(row['valley_depth'])}  balance {_fmt(row['peak_balance'])}"
    )


def _ordered(scored: pd.DataFrame, shape: str) -> pd.DataFrame:
    column = SCORE_COLUMNS[shape]
    return scored.sort_values([column, "session_date"], ascending=[False, True], kind="mergesort")


def _save_single(path, grid, dataset_row, scored_row, shape: str) -> None:
    fig, ax = plt.subplots(figsize=SINGLE_SIZE, dpi=DPI)
    score = float(scored_row[SCORE_COLUMNS[shape]])
    heading = _heading(str(scored_row.name), str(scored_row["primary_class"]), f"{shape} {score:.3f}")
    _draw(ax, grid, dataset_row, heading, _component_note(scored_row, shape))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _save_gallery(path, panels: list[tuple], title: str) -> None:
    fig, axes = plt.subplots(5, 2, figsize=GALLERY_SIZE, dpi=DPI)
    for ax, panel in zip(axes.ravel(), panels):
        grid, dataset_row, heading, note = panel
        _draw(ax, grid, dataset_row, heading, note)
    for ax in axes.ravel()[len(panels) :]:
        ax.axis("off")
    fig.suptitle(title, fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(path)
    plt.close(fig)


def _random_dates(dates: list[str]) -> list[str]:
    rng = np.random.default_rng(42)
    picked = rng.choice(len(dates), size=10, replace=False)
    return [dates[int(i)] for i in picked]


def main() -> None:
    scored = pd.read_parquet(RESULTS / "continuous_shape_scores.parquet")
    scored["session_date"] = scored["session_date"].astype(str)
    dataset = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    dataset["session_date"] = dataset["session_date"].astype(str)
    dataset = dataset.set_index("session_date")
    grids = load_grids()
    FIGURES.mkdir(parents=True, exist_ok=True)
    by_date = scored.set_index("session_date")

    for shape in SHAPE_ORDER:
        folder = FIGURES / FOLDER[shape]
        folder.mkdir(parents=True, exist_ok=True)
        ordered = _ordered(scored, shape).head(10)
        panels = []
        for rank, row in enumerate(ordered.itertuples(index=False), start=1):
            date = str(row.session_date)
            grid = grids.get(date)
            if grid is None:
                raise SystemExit(f"No raw profile for gallery session {date}. Stopping.")
            scored_row = by_date.loc[date]
            dataset_row = dataset.loc[date]
            path = folder / f"{rank:02d}_{date}.png"
            _save_single(path, grid, dataset_row, scored_row, shape)
            score = float(getattr(row, SCORE_COLUMNS[shape]))
            panels.append(
                (
                    grid,
                    dataset_row,
                    _heading(date, str(row.primary_class), f"{shape} {score:.3f}"),
                    _component_note(scored_row, shape),
                )
            )
        gallery = FIGURES / GALLERY[shape]
        _save_gallery(gallery, panels, f"Top 10 by {shape} score. Ranking only, not a trade label.")
        print(f"[step1b] wrote {gallery}", flush=True)

    dates = sorted(scored["session_date"].tolist())
    random_dates = _random_dates(dates)
    panels = []
    for date in random_dates:
        row = by_date.loc[date]
        grid = grids[date]
        heading = _heading(
            date,
            str(row["primary_class"]),
            f"P {row['P_score']:.2f}  b {row['b_score']:.2f}  D {row['D_score']:.2f}  B {row['B_score']:.2f}",
        )
        note = (
            f"P {_fmt(row['P_score'])}  b {_fmt(row['b_score'])}  "
            f"D {_fmt(row['D_score'])}  B {_fmt(row['B_score'])}\n"
            f"major {int(row['n_major_peaks'])}  POC loc {_fmt(row['poc_location'])}"
        )
        panels.append((grid, dataset.loc[date], heading, note))
    random_path = FIGURES / "gallery_random.png"
    _save_gallery(random_path, panels, "Random 10 analysis sessions, seed 42. Not selected by shape.")
    (RESULTS / "random_gallery_sessions.json").write_text(
        json.dumps({"seed": 42, "session_dates_in_draw_order": random_dates}, indent=2),
        encoding="utf-8",
    )
    print(f"[step1b] wrote {random_path}", flush=True)

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), dpi=DPI)
    bins = np.linspace(0, 1, 21)
    for ax, shape in zip(axes.ravel(), SHAPE_ORDER):
        values = scored[SCORE_COLUMNS[shape]].to_numpy(dtype=np.float64)
        ax.hist(values, bins=bins, color=FILL, edgecolor="white")
        ax.set_xlim(0, 1)
        ax.set_title(f"{shape} score")
        ax.set_xlabel("Score")
        ax.set_ylabel("Sessions")
    fig.suptitle("Continuous shape scores on the 96 analysis sessions")
    fig.tight_layout()
    hist_path = FIGURES / "score_histograms.png"
    fig.savefig(hist_path)
    plt.close(fig)
    print(f"[step1b] wrote {hist_path}", flush=True)


if __name__ == "__main__":
    main()
