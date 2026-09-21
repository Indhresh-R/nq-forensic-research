"""Null-calibrated LVN rejection audit from frozen Step 4 paths.

Definitions are copied from STEP5_PREREGISTRATION.md. No returns are computed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
CODE_DIR = Path(__file__).resolve().parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from boundaries import _parse_date
from frozen import RESULTS
from interaction_audit import load_session_minute_bars
from path_reaction import EXPECTED_LOWER, EXPECTED_UPPER, HORIZONS, _event_flags

PRIMARY_N = EXPECTED_LOWER + EXPECTED_UPPER


def _null_stats(frame: pd.DataFrame, reject_col: str = "is_reject") -> dict:
    ok = frame.loc[frame["null_defined"]].copy()
    if ok.empty:
        return {
            "n": int(len(frame)),
            "null_n": 0,
            "reject_n": int(frame[reject_col].sum()) if len(frame) else 0,
            "observed_reject": float("nan"),
            "mean_null_reject": float("nan"),
            "mean_reject_minus_null": float("nan"),
        }
    obs = ok[reject_col].astype(float)
    null = ok["null_reject_prob"].astype(float)
    return {
        "n": int(len(frame)),
        "null_n": int(len(ok)),
        "reject_n": int(ok[reject_col].sum()),
        "observed_reject": float(obs.mean()),
        "mean_null_reject": float(null.mean()),
        "mean_reject_minus_null": float((obs - null).mean()),
    }


def _reject_location(
    approach: str,
    bars: pd.DataFrame,
    touch_i: int,
    reject_i: int,
    valley_left: float,
    valley_right: float,
) -> str:
    if valley_right - valley_left <= 0:
        return "undefined"
    highs = bars["high"].to_numpy(dtype=float)[touch_i : reject_i + 1]
    lows = bars["low"].to_numpy(dtype=float)[touch_i : reject_i + 1]
    if approach == "lower_region":
        max_toward = float(highs.max())
        far = valley_right
        if max_toward <= far + 1e-12:
            return "band_only"
        return "past_far_edge"
    max_toward = float(lows.min())
    far = valley_left
    if max_toward >= far - 1e-12:
        return "band_only"
    return "past_far_edge"


def _path_extents_to_reject(
    approach: str,
    bars: pd.DataFrame,
    touch_i: int,
    reject_i: int,
    measurement: float,
    lower_hvn: float,
    upper_hvn: float,
    valley_left: float,
    valley_right: float,
) -> dict:
    highs = bars["high"].to_numpy(dtype=float)[touch_i : reject_i + 1]
    lows = bars["low"].to_numpy(dtype=float)[touch_i : reject_i + 1]
    hvn_span = upper_hvn - lower_hvn
    lvn_span = valley_right - valley_left
    if approach == "lower_region":
        opp_points = float(max(0.0, float(highs.max()) - measurement))
        if lvn_span > 0:
            clipped = np.minimum(highs, valley_right) - valley_left
            lvn_pen = float(max(0.0, float(clipped.max()) / lvn_span))
        else:
            lvn_pen = float("nan")
    else:
        opp_points = float(max(0.0, measurement - float(lows.min())))
        if lvn_span > 0:
            clipped = valley_right - np.maximum(lows, valley_left)
            lvn_pen = float(max(0.0, float(clipped.max()) / lvn_span))
        else:
            lvn_pen = float("nan")
    return {
        "reject_path_lvn_penetration": lvn_pen,
        "reject_path_opposite_excursion": opp_points / hvn_span if hvn_span > 0 else float("nan"),
        "reject_path_opposite_points": opp_points,
    }


def run() -> None:
    paths = pd.read_csv(RESULTS / "step4_paths.csv")
    sample = pd.read_csv(RESULTS / "step3_interactions_sample.csv")
    sample["session_key"] = sample["prior_session"].astype(str) + "|" + sample["gap_index"].astype(str)
    meta = sample.set_index("session_key")[
        ["lower_hvn_price", "upper_hvn_price", "valley_left_price", "valley_right_price"]
    ]
    paths["session_key"] = paths["prior_session"].astype(str) + "|" + paths["gap_index"].astype(str)
    paths = paths.merge(meta, left_on="session_key", right_index=True, how="left", validate="many_to_one")
    if paths[["lower_hvn_price", "upper_hvn_price"]].isna().any().any():
        raise SystemExit("Missing HVN metadata for Step 5. Stopping.")

    cache: dict[str, pd.DataFrame] = {}
    enriched = []
    for row in paths.itertuples(index=False):
        record = dict(row._asdict())
        record["null_reject_prob"] = (
            1.0 - float(row.null_traverse_prob) if bool(row.null_defined) else float("nan")
        )
        record["is_reject"] = str(row.outcome) == "reject"
        record["is_traverse"] = str(row.outcome) == "traverse"
        record["is_decided"] = str(row.outcome) in ("reject", "traverse")
        key = str(row.next_session)
        if key not in cache:
            bars = load_session_minute_bars(_parse_date(key))
            if bars.empty:
                raise SystemExit(f"No trade bars for {key}. Stopping.")
            cache[key] = bars
        bars = cache[key]
        touch_i = int(row.touch_bar)
        lower_hvn = float(row.lower_hvn_price)
        upper_hvn = float(row.upper_hvn_price)
        _trav, touch_reject = _event_flags(
            str(row.approach),
            float(bars["low"].iloc[touch_i]),
            float(bars["high"].iloc[touch_i]),
            lower_hvn,
            upper_hvn,
        )
        record["touch_bar_hits_approach_hvn"] = bool(touch_reject)
        if str(row.outcome) == "reject":
            reject_i = int(row.reject_bar)
            record["same_minute_reject"] = reject_i == touch_i
            record["delayed_reject"] = reject_i > touch_i
            record["reject_location"] = _reject_location(
                str(row.approach),
                bars,
                touch_i,
                reject_i,
                float(row.valley_left_price),
                float(row.valley_right_price),
            )
            extents = _path_extents_to_reject(
                str(row.approach),
                bars,
                touch_i,
                reject_i,
                float(row.measurement_price),
                lower_hvn,
                upper_hvn,
                float(row.valley_left_price),
                float(row.valley_right_price),
            )
            record.update(extents)
            record["minutes_to_reject"] = float(row.minutes_to_event)
        else:
            record["same_minute_reject"] = False
            record["delayed_reject"] = False
            record["reject_location"] = ""
            record["reject_path_lvn_penetration"] = np.nan
            record["reject_path_opposite_excursion"] = np.nan
            record["reject_path_opposite_points"] = np.nan
            record["minutes_to_reject"] = np.nan
        enriched.append(record)

    frame = pd.DataFrame(enriched)
    for horizon_name, _ in HORIZONS:
        n = int((frame["horizon"] == horizon_name).sum())
        if n != PRIMARY_N:
            raise SystemExit(f"{horizon_name} has {n} rows, expected {PRIMARY_N}. Stopping.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RESULTS / "step5_rejections.csv", index=False)

    summary_rows = []
    location_rows = []
    for horizon_name, _ in HORIZONS:
        part = frame.loc[frame["horizon"] == horizon_name].copy()
        decided = part.loc[part["is_decided"]]
        delayed_decided = decided.loc[~decided["same_minute_reject"]]
        no_touch_hit = part.loc[~part["touch_bar_hits_approach_hvn"]]

        for label, subset, mode in (
            ("A_decided", decided, "decided"),
            ("B_unconditional", part, "unconditional"),
            ("C_delayed_decided", delayed_decided, "decided"),
            ("D_no_touch_hit_unconditional", no_touch_hit, "unconditional"),
        ):
            stats = _null_stats(subset)
            summary_rows.append({"horizon": horizon_name, "test": label, "mode": mode, **stats})

        rejects = part.loc[part["is_reject"]]
        summary_rows.append(
            {
                "horizon": horizon_name,
                "test": "same_minute_vs_delayed",
                "mode": "count",
                "n": int(len(rejects)),
                "null_n": int(rejects["same_minute_reject"].sum()),
                "reject_n": int(rejects["delayed_reject"].sum()),
                "observed_reject": float("nan"),
                "mean_null_reject": float("nan"),
                "mean_reject_minus_null": float("nan"),
                "same_minute_n": int(rejects["same_minute_reject"].sum()),
                "delayed_n": int(rejects["delayed_reject"].sum()),
            }
        )
        for loc, count in rejects["reject_location"].value_counts().items():
            location_rows.append(
                {
                    "horizon": horizon_name,
                    "reject_location": str(loc),
                    "n": int(count),
                    "share": float(count / len(rejects)) if len(rejects) else float("nan"),
                    "med_minutes": float(rejects.loc[rejects["reject_location"] == loc, "minutes_to_reject"].median()),
                    "med_lvn_pen": float(
                        rejects.loc[rejects["reject_location"] == loc, "reject_path_lvn_penetration"].median()
                    ),
                    "med_opp_exc": float(
                        rejects.loc[rejects["reject_location"] == loc, "reject_path_opposite_excursion"].median()
                    ),
                }
            )
        if len(rejects):
            location_rows.append(
                {
                    "horizon": horizon_name,
                    "reject_location": "ALL_REJECTS",
                    "n": int(len(rejects)),
                    "share": 1.0,
                    "med_minutes": float(rejects["minutes_to_reject"].median()),
                    "med_lvn_pen": float(rejects["reject_path_lvn_penetration"].median()),
                    "med_opp_exc": float(rejects["reject_path_opposite_excursion"].median()),
                }
            )

        for slice_name, mask in (
            ("lower_to_upper", part["approach"] == "lower_region"),
            ("upper_to_lower", part["approach"] == "upper_region"),
            ("clean", part["clean"].astype(bool)),
            ("both_regions_sized", part["both_regions_sized"].astype(bool)),
        ):
            sub = part.loc[mask]
            for label, subset in (
                ("B_unconditional", sub),
                ("A_decided", sub.loc[sub["is_decided"]]),
                ("D_no_touch_hit_unconditional", sub.loc[~sub["touch_bar_hits_approach_hvn"]]),
            ):
                stats = _null_stats(subset)
                summary_rows.append(
                    {
                        "horizon": horizon_name,
                        "test": f"{label}__{slice_name}",
                        "mode": "slice",
                        **stats,
                    }
                )

    summary = pd.DataFrame(summary_rows)
    locations = pd.DataFrame(location_rows)
    summary.to_csv(RESULTS / "step5_null_summary.csv", index=False)
    locations.to_csv(RESULTS / "step5_reject_locations.csv", index=False)
    verification = {
        "primary_n_per_horizon": PRIMARY_N,
        "horizons": [name for name, _ in HORIZONS],
        "note": "Null A is complementary to Step 4 traverse; Null B/C/D are the rejection claims.",
    }
    (RESULTS / "step5_verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(f"[step5] rows={len(frame)}", flush=True)
    show = summary.loc[summary["test"].isin(["A_decided", "B_unconditional", "C_delayed_decided", "D_no_touch_hit_unconditional", "same_minute_vs_delayed"])]
    print(show.to_string(index=False), flush=True)


def run_self_check() -> None:
    # null complement
    assert abs((1 - 0.2) - 0.8) < 1e-12
    ts0 = pd.Timestamp("2026-01-01 18:00", tz="America/New_York")
    bars = pd.DataFrame(
        {
            "ts": [ts0, ts0 + pd.Timedelta(minutes=1), ts0 + pd.Timedelta(minutes=2)],
            "open": [105.0, 112.0, 108.0],
            "high": [113.0, 114.0, 109.0],
            "low": [104.0, 100.0, 99.0],
            "close": [112.0, 101.0, 100.0],
        }
    )
    # lower approach, valley 110-118, reject on bar 1 after clearing far edge 118? high 114 < 118 -> band_only
    loc = _reject_location("lower_region", bars, 0, 1, 110.0, 118.0)
    if loc != "band_only":
        raise AssertionError(loc)
    bars2 = bars.copy()
    bars2.loc[0, "high"] = 120.0
    loc2 = _reject_location("lower_region", bars2, 0, 1, 110.0, 118.0)
    if loc2 != "past_far_edge":
        raise AssertionError(loc2)
    print("[step5] self-check passed", flush=True)


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    run()


if __name__ == "__main__":
    main()
