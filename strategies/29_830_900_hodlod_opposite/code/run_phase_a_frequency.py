"""Strategy 29 Phase A — how often 08:30–09:00 is HOD/LOD vs controls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import load_nq
from common.paths import ROOT
from common.splits import IS_YEARS, OOS_YEARS, VAL_YEARS

ART = ROOT / "artifacts" / "29_830_900_hodlod_opposite"

# (name, start_ny_min, end_ny_min exclusive)
WINDOWS = (
    ("W_0830_0900", 8 * 60 + 30, 9 * 60),
    ("CTRL_0730_0800", 7 * 60 + 30, 8 * 60),
    ("CTRL_0900_0930", 9 * 60, 9 * 60 + 30),
    ("CTRL_1000_1030", 10 * 60, 10 * 60 + 30),
)
DAY_START = 8 * 60 + 30
DAY_END = 16 * 60


def split_of(year: int) -> str:
    if year in IS_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    nq = load_nq()
    # restrict to relevant minutes for speed
    m = (nq["ny_min"] >= DAY_START) & (nq["ny_min"] < DAY_END)
    df = nq.loc[m].copy()
    df["split"] = [split_of(int(y)) for y in df["year"].to_numpy()]

    rows = []
    day_rows = []
    for sess, g in df.groupby("session_date", sort=False):
        g = g.sort_values("ny_min")
        if g["ny_min"].min() > DAY_START or g["ny_min"].max() < DAY_END - 1:
            # require coverage of window start and near RTH end loosely
            pass
        day_hi = float(g["high"].max())
        day_lo = float(g["low"].min())
        year = int(g["year"].iloc[0])
        split = split_of(year)
        rec = {"session_date": str(sess), "year": year, "split": split, "day_hi": day_hi, "day_lo": day_lo}
        for name, lo, hi in WINDOWS:
            w = g[(g["ny_min"] >= lo) & (g["ny_min"] < hi)]
            if len(w) < 20:
                rec[f"{name}_ok"] = False
                continue
            wh = float(w["high"].max())
            wl = float(w["low"].min())
            is_hod = abs(wh - day_hi) < 1e-8
            is_lod = abs(wl - day_lo) < 1e-8
            if is_hod and is_lod:
                lab = "BOTH"
            elif is_hod:
                lab = "HOD_ONLY"
            elif is_lod:
                lab = "LOD_ONLY"
            else:
                lab = "NEITHER"
            rec[f"{name}_ok"] = True
            rec[f"{name}_label"] = lab
            rec[f"{name}_hi"] = wh
            rec[f"{name}_lo"] = wl
            rows.append(
                {
                    "window": name,
                    "split": split,
                    "year": year,
                    "label": lab,
                    "is_hod": is_hod,
                    "is_lod": is_lod,
                    "hod_or_lod": is_hod or is_lod,
                    "xor": (is_hod != is_lod),
                }
            )
        day_rows.append(rec)

    freq = pd.DataFrame(rows)
    days = pd.DataFrame(day_rows)
    freq.to_csv(ART / "phase_a_window_labels.csv", index=False)
    days.to_parquet(ART / "phase_a_day_panel.parquet", index=False)

    summary = (
        freq.groupby(["window", "split"], as_index=False)
        .agg(
            n=("label", "size"),
            pct_hod=("is_hod", "mean"),
            pct_lod=("is_lod", "mean"),
            pct_hod_or_lod=("hod_or_lod", "mean"),
            pct_xor=("xor", "mean"),
            pct_both=("label", lambda s: float(np.mean(s == "BOTH"))),
            pct_neither=("label", lambda s: float(np.mean(s == "NEITHER"))),
        )
        .sort_values(["window", "split"])
    )
    summary.to_csv(ART / "phase_a_frequency.csv", index=False)

    # Discovery highlight
    disc = summary[summary["split"] == "Discovery"]
    primary = disc[disc["window"] == "W_0830_0900"].iloc[0].to_dict()
    freeze = {
        "day_range_definition": "[08:30, 16:00) ET extremes",
        "primary_discovery": {
            "pct_hod": primary["pct_hod"],
            "pct_lod": primary["pct_lod"],
            "pct_hod_or_lod": primary["pct_hod_or_lod"],
            "pct_xor": primary["pct_xor"],
            "n": int(primary["n"]),
        },
        "note": "xor = exactly one of HOD/LOD (tradable oracle universe)",
    }
    (ART / "phase_a_summary.json").write_text(json.dumps(freeze, indent=2, default=float), encoding="utf-8")

    md = [
        "# Strategy 29 — Phase A frequency",
        "",
        "Day extremes from **[08:30, 16:00)** ET (includes the 08:30–09:00 window).",
        "",
        f"Primary W Discovery HOD-or-LOD: **{100*primary['pct_hod_or_lod']:.1f}%** "
        f"(xor exactly one: **{100*primary['pct_xor']:.1f}%**, n={int(primary['n'])})",
        "",
        summary.to_markdown(index=False),
        "",
    ]
    (ART / "phase_a_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(freeze, indent=2, default=float))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
