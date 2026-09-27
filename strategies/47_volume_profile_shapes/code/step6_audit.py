"""Read-only chronological audit of frozen Step 5 rejection rows.

Does not change LVN, rejection, horizon, or null definitions.
Does not search thresholds. Writes a summary CSV only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parents[1] / "results"
# Calendar midpoint of the frozen trade window 2026-03-25 through 2026-09-16.
# Chosen from the input file span, not from rejection outcomes.
CALENDAR_CUT = "2026-06-20"
HORIZONS = ("H30", "H60", "H120", "session_end")


def _stats(frame: pd.DataFrame) -> dict:
    obs = frame["is_reject"].astype(float)
    null = frame["null_reject_prob"].astype(float)
    diff = obs - null
    return {
        "n": int(len(frame)),
        "reject_n": int(obs.sum()),
        "observed_reject": float(obs.mean()) if len(frame) else float("nan"),
        "mean_null_reject": float(null.mean()) if len(frame) else float("nan"),
        "mean_reject_minus_null": float(diff.mean()) if len(frame) else float("nan"),
        "diff_p25": float(diff.quantile(0.25)) if len(frame) else float("nan"),
        "diff_median": float(diff.median()) if len(frame) else float("nan"),
        "diff_p75": float(diff.quantile(0.75)) if len(frame) else float("nan"),
        "lower_n": int((frame["approach"] == "lower_region").sum()),
        "upper_n": int((frame["approach"] == "upper_region").sum()),
        "date_min": str(frame["next_session"].min()) if len(frame) else "",
        "date_max": str(frame["next_session"].max()) if len(frame) else "",
    }


def main() -> None:
    frame = pd.read_csv(RESULTS / "step5_rejections.csv")
    rows: list[dict] = []
    for horizon in HORIZONS:
        part = frame.loc[frame["horizon"] == horizon].copy()
        part["block"] = (part["next_session"].astype(str) >= CALENDAR_CUT).map(
            {False: "early_before_2026-06-20", True: "late_from_2026-06-20"}
        )
        ordered = part.sort_values(["next_session", "prior_session", "gap_index"]).reset_index(drop=True)
        mid = len(ordered) // 2
        ordered["half"] = "late_equal_count"
        ordered.loc[: mid - 1, "half"] = "early_equal_count"
        for label, subset in (
            ("all", part),
            ("early_before_2026-06-20", part.loc[part["block"] == "early_before_2026-06-20"]),
            ("late_from_2026-06-20", part.loc[part["block"] == "late_from_2026-06-20"]),
            ("early_equal_count", ordered.loc[ordered["half"] == "early_equal_count"]),
            ("late_equal_count", ordered.loc[ordered["half"] == "late_equal_count"]),
        ):
            rows.append({"horizon": horizon, "block": label, "split": "calendar_or_count", **_stats(subset)})
        part["ym"] = part["next_session"].astype(str).str.slice(0, 7)
        for ym, subset in part.groupby("ym"):
            rows.append({"horizon": horizon, "block": str(ym), "split": "month", **_stats(subset)})

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "step6_temporal_audit.csv", index=False)
    show = out.loc[
        (out["horizon"].isin(["H60", "H120"])) & (out["split"] == "calendar_or_count")
    ]
    print(show.to_string(index=False))


if __name__ == "__main__":
    main()
