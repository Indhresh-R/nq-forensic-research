"""Draw Step 2 region galleries from the stored tables.

The session table decides which days appear. This module does not re-segment them.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from frozen import FIGURES, RESULTS, TICK_SIZE
from plot_galleries import load_grids

FILL = "#4C78A8"
SINGLE_SIZE = (7.2, 8.0)
GALLERY_SIZE = (11.5, 24.0)
DPI = 130
STEP2 = FIGURES / "step2"


def _fmt(value: object) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)) or pd.isna(value):
        return "n/a"
    return f"{float(value):.2f}"


def _draw(
    ax,
    grid: tuple[int, np.ndarray],
    session: pd.Series,
    peak_rows: pd.DataFrame,
    gap_rows: pd.DataFrame,
    heading: str,
) -> None:
    low_tick, volume = grid
    prices = (low_tick + np.arange(len(volume))) * TICK_SIZE
    ax.fill_betweenx(prices, 0, volume, step="mid", color=FILL)
    ax.set_xlim(0, float(volume.max()) * 1.08)
    pad = 0.25 if len(prices) < 3 else 0.0
    ax.set_ylim(float(prices[0]) - pad, float(prices[-1]) + pad)
    ax.axhline(float(session["poc_price"]), color="black", lw=1.0, label="POC")
    midpoint = (float(prices[0]) + float(prices[-1])) / 2.0
    ax.axhline(midpoint, color="0.45", lw=0.6, ls="--", label="range midpoint")
    first_major = True
    first_minor = True
    for peak in peak_rows.itertuples(index=False):
        if bool(peak.is_major):
            ax.plot(
                float(peak.volume),
                float(peak.price),
                marker="o",
                color="black",
                ms=4.5,
                label="major peak" if first_major else None,
            )
            first_major = False
        else:
            ax.plot(
                float(peak.volume),
                float(peak.price),
                marker="o",
                color="black",
                ms=4.5,
                fillstyle="none",
                label="other local max" if first_minor else None,
            )
            first_minor = False
    first_material = True
    first_weak = True
    for gap in gap_rows.itertuples(index=False):
        if pd.isna(gap.valley_price):
            continue
        material = bool(gap.material)
        ax.plot(
            float(gap.valley_volume),
            float(gap.valley_price),
            marker="x",
            color="black" if material else "0.55",
            ms=7,
            label=("material valley" if first_material else None)
            if material
            else ("non-material valley" if first_weak else None),
        )
        if material:
            first_material = False
        else:
            first_weak = False
    clean = "yes" if bool(session["clean_two"]) else "no"
    note = (
        f"regions {int(session['n_regions'])}  clean_two {clean}\n"
        f"loc {session['dominant_third']}"
        f"  L {_fmt(session['lower_share'])}"
        f"  M {_fmt(session['middle_share'])}"
        f"  U {_fmt(session['upper_share'])}\n"
        f"weak sep {_fmt(session['weak_separation'])}"
        f"  depth {_fmt(session['weak_depth'])}"
        f"  minors {int(session['weak_minor_peaks_between'])}\n"
        f"strong sep {_fmt(session['strong_separation'])}"
        f"  depth {_fmt(session['strong_depth'])}\n"
        f"std {_fmt(session['vw_std_norm'])}"
        f"  POC conc {_fmt(session['poc_concentration_10'])}"
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


def _save_gallery(path, panels: list[tuple], title: str) -> None:
    fig, axes = plt.subplots(5, 2, figsize=GALLERY_SIZE, dpi=DPI)
    for ax, panel in zip(axes.ravel(), panels):
        grid, session, peaks, gaps, heading = panel
        _draw(ax, grid, session, peaks, gaps, heading)
    for ax in axes.ravel()[len(panels) :]:
        ax.axis("off")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(path)
    plt.close(fig)


def _panel_list(dates: list[str], sessions: pd.DataFrame, peaks: pd.DataFrame, gaps: pd.DataFrame, grids: dict) -> list:
    panels = []
    for date in dates:
        session = sessions.loc[date]
        grid = grids.get(date)
        if grid is None:
            raise SystemExit(f"No raw profile for gallery session {date}. Stopping.")
        heading = f"{date}   {session['structure'].replace('_', ' ')}\nStep 1: {session['primary_class']}"
        panels.append((grid, session, peaks.loc[peaks["session_date"] == date], gaps.loc[gaps["session_date"] == date], heading))
    return panels


def _random_dates(dates: list[str]) -> list[str]:
    rng = np.random.default_rng(42)
    picked = rng.choice(len(dates), size=10, replace=False)
    return [dates[int(i)] for i in picked]


def _bars(path, labels: list[str], values: list[int], title: str, xlabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.2), dpi=DPI)
    ax.bar(labels, values, color=FILL)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Sessions")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    sessions = pd.read_csv(RESULTS / "step2_sessions.csv")
    sessions["session_date"] = sessions["session_date"].astype(str)
    peaks = pd.read_csv(RESULTS / "step2_peaks.csv")
    gaps = pd.read_csv(RESULTS / "step2_gaps.csv")
    peaks["session_date"] = peaks["session_date"].astype(str)
    gaps["session_date"] = gaps["session_date"].astype(str)
    by_date = sessions.set_index("session_date")
    grids = load_grids()
    STEP2.mkdir(parents=True, exist_ok=True)

    two = sessions.loc[sessions["structure"] == "two_regions"].sort_values(
        ["weak_depth", "weak_separation", "session_date"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    two_dates = two["session_date"].head(10).tolist()
    if two_dates:
        title = "Two accepted regions, highest gap depth first. Not a trade label."
        if len(two) > 10:
            title = f"First 10 of {len(two)} two-region sessions, by gap depth. Not a trade label."
        _save_gallery(STEP2 / "gallery_two_regions.png", _panel_list(two_dates, by_date, peaks, gaps, grids), title)
        print(f"[step2] wrote two-region gallery n={len(two_dates)} of {len(two)}", flush=True)
    else:
        print("[step2] no two-region sessions; gallery skipped", flush=True)

    many = sessions.loc[sessions["structure"] == "many_regions"].sort_values(
        ["n_regions", "session_date"],
        ascending=[False, True],
        kind="mergesort",
    )
    many_dates = many["session_date"].head(10).tolist()
    if many_dates:
        _save_gallery(
            STEP2 / "gallery_many_regions.png",
            _panel_list(many_dates, by_date, peaks, gaps, grids),
            "Most accepted regions. Count only, not a trade label.",
        )
        print(f"[step2] wrote many-region gallery n={len(many_dates)}", flush=True)

    dates = sorted(sessions["session_date"].tolist())
    random_dates = _random_dates(dates)
    _save_gallery(
        STEP2 / "gallery_random.png",
        _panel_list(random_dates, by_date, peaks, gaps, grids),
        "Random 10 sessions, seed 42. Draw order, not a ranking.",
    )
    (STEP2 / "random_dates.txt").write_text("\n".join(random_dates) + "\n", encoding="utf-8")
    print("[step2] wrote random gallery", flush=True)

    counts = sessions["n_regions"].value_counts().sort_index()
    _bars(
        STEP2 / "n_regions.png",
        [str(int(index)) for index in counts.index],
        [int(value) for value in counts.to_numpy()],
        "Accepted regions per session",
        "Regions",
    )
    location = sessions["dominant_third"].value_counts().reindex(["lower", "middle", "upper"]).fillna(0)
    _bars(
        STEP2 / "dominant_third.png",
        [str(index) for index in location.index],
        [int(value) for value in location.to_numpy()],
        "Dominant price third by volume",
        "Third",
    )
    print("[step2] wrote histograms", flush=True)


if __name__ == "__main__":
    main()
