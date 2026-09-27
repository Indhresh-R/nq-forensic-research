"""Competing traverse / reject / remain paths after first LVN touch.

Definitions are copied from STEP4_PREREGISTRATION.md. No returns are computed.
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

EXPECTED_LOWER = 12
EXPECTED_UPPER = 22
EXPECTED_OPEN_IN_BAND = 5
PRIMARY_APPROACHES = ("lower_region", "upper_region")
HORIZONS = (("H30", 30), ("H60", 60), ("H120", 120), ("session_end", None))


def _event_flags(approach: str, low: float, high: float, lower_hvn: float, upper_hvn: float) -> tuple[bool, bool]:
    if approach == "lower_region":
        return high >= upper_hvn - 1e-12, low <= lower_hvn + 1e-12
    if approach == "upper_region":
        return low <= lower_hvn + 1e-12, high >= upper_hvn - 1e-12
    raise ValueError(f"unsupported approach {approach}")


def _horizon_end_index(bars: pd.DataFrame, touch_i: int, minutes: int | None) -> int:
    if minutes is None:
        return len(bars) - 1
    touch_ts = bars["ts"].iloc[touch_i]
    limit = touch_ts + pd.Timedelta(minutes=minutes)
    last = touch_i
    for i in range(touch_i, len(bars)):
        if bars["ts"].iloc[i] <= limit:
            last = i
        else:
            break
    return last


def _path_metrics(
    approach: str,
    bars: pd.DataFrame,
    touch_i: int,
    end_i: int,
    measurement: float,
    lower_hvn: float,
    upper_hvn: float,
    valley_left: float,
    valley_right: float,
) -> dict:
    highs = bars["high"].to_numpy(dtype=float)[touch_i : end_i + 1]
    lows = bars["low"].to_numpy(dtype=float)[touch_i : end_i + 1]
    hvn_span = upper_hvn - lower_hvn
    lvn_span = valley_right - valley_left
    if hvn_span <= 0:
        raise ValueError("non-positive HVN span")
    if approach == "lower_region":
        max_opp_points = float(max(0.0, float(highs.max()) - measurement))
        max_adv_points = float(max(0.0, measurement - float(lows.min())))
        if lvn_span > 0:
            clipped = np.minimum(highs, valley_right) - valley_left
            max_lvn = float(max(0.0, float(clipped.max()) / lvn_span))
        else:
            max_lvn = float("nan")
    else:
        max_opp_points = float(max(0.0, measurement - float(lows.min())))
        max_adv_points = float(max(0.0, float(highs.max()) - measurement))
        if lvn_span > 0:
            clipped = valley_right - np.maximum(lows, valley_left)
            max_lvn = float(max(0.0, float(clipped.max()) / lvn_span))
        else:
            max_lvn = float("nan")
    return {
        "max_lvn_penetration": max_lvn,
        "max_opposite_excursion": max_opp_points / hvn_span,
        "max_opposite_points": max_opp_points,
        "max_adverse_points": max_adv_points,
    }


def resolve_path(
    approach: str,
    bars: pd.DataFrame,
    touch_i: int,
    end_i: int,
    lower_hvn: float,
    upper_hvn: float,
) -> dict:
    traverse_i = None
    reject_i = None
    for i in range(touch_i, end_i + 1):
        trav, rej = _event_flags(
            approach,
            float(bars["low"].iloc[i]),
            float(bars["high"].iloc[i]),
            lower_hvn,
            upper_hvn,
        )
        if trav and traverse_i is None:
            traverse_i = i
        if rej and reject_i is None:
            reject_i = i
        if traverse_i is not None and reject_i is not None:
            break
    touch_ts = bars["ts"].iloc[touch_i]
    if traverse_i is None and reject_i is None:
        return {
            "outcome": "remain",
            "event_bar": -1,
            "minutes_to_event": np.nan,
            "traverse_bar": -1,
            "reject_bar": -1,
        }
    if traverse_i is not None and reject_i is not None and traverse_i == reject_i:
        return {
            "outcome": "ambiguous_same_bar",
            "event_bar": int(traverse_i),
            "minutes_to_event": (bars["ts"].iloc[traverse_i] - touch_ts).total_seconds() / 60.0,
            "traverse_bar": int(traverse_i),
            "reject_bar": int(reject_i),
        }
    if reject_i is None or (traverse_i is not None and traverse_i < reject_i):
        return {
            "outcome": "traverse",
            "event_bar": int(traverse_i),
            "minutes_to_event": (bars["ts"].iloc[traverse_i] - touch_ts).total_seconds() / 60.0,
            "traverse_bar": int(traverse_i),
            "reject_bar": int(reject_i) if reject_i is not None else -1,
        }
    return {
        "outcome": "reject",
        "event_bar": int(reject_i),
        "minutes_to_event": (bars["ts"].iloc[reject_i] - touch_ts).total_seconds() / 60.0,
        "traverse_bar": int(traverse_i) if traverse_i is not None else -1,
        "reject_bar": int(reject_i),
    }


def _open_in_band_first_hvn(
    bars: pd.DataFrame,
    touch_i: int,
    end_i: int,
    lower_hvn: float,
    upper_hvn: float,
) -> str:
    for i in range(touch_i, end_i + 1):
        hit_l = float(bars["low"].iloc[i]) <= lower_hvn + 1e-12
        hit_u = float(bars["high"].iloc[i]) >= upper_hvn - 1e-12
        if hit_l and hit_u:
            return "both_same_bar"
        if hit_l:
            return "lower_hvn_first"
        if hit_u:
            return "upper_hvn_first"
    return "neither"


def evaluate_row(row: pd.Series, bars: pd.DataFrame, horizon_name: str, minutes: int | None) -> dict:
    touch_i = int(row["touch_bar"])
    if touch_i < 0 or touch_i >= len(bars):
        raise ValueError(f"touch_bar out of range for {row['prior_session']}")
    end_i = _horizon_end_index(bars, touch_i, minutes)
    measurement = float(bars["open"].iloc[touch_i])
    lower_hvn = float(row["lower_hvn_price"])
    upper_hvn = float(row["upper_hvn_price"])
    approach = str(row["approach"])
    out = {
        "prior_session": str(row["prior_session"]),
        "gap_index": int(row["gap_index"]),
        "next_session": str(row["next_session"]),
        "approach": approach,
        "clean": bool(row["clean"]),
        "both_regions_sized": bool(row["both_regions_sized"]),
        "horizon": horizon_name,
        "measurement_price": measurement,
        "touch_bar": touch_i,
        "horizon_end_bar": end_i,
        "bars_in_horizon": int(end_i - touch_i + 1),
    }
    if approach == "open_in_band":
        out["outcome"] = _open_in_band_first_hvn(bars, touch_i, end_i, lower_hvn, upper_hvn)
        out["null_traverse_prob"] = np.nan
        out["dist_to_approach"] = np.nan
        out["dist_to_opposite"] = np.nan
        out["null_defined"] = False
        return out

    if approach == "lower_region":
        dist_app = abs(measurement - lower_hvn)
        dist_opp = abs(measurement - upper_hvn)
    else:
        dist_app = abs(measurement - upper_hvn)
        dist_opp = abs(measurement - lower_hvn)
    out["dist_to_approach"] = dist_app
    out["dist_to_opposite"] = dist_opp
    if dist_app <= 0 or dist_opp <= 0:
        out["null_traverse_prob"] = np.nan
        out["null_defined"] = False
    else:
        out["null_traverse_prob"] = dist_app / (dist_app + dist_opp)
        out["null_defined"] = True
    resolved = resolve_path(approach, bars, touch_i, end_i, lower_hvn, upper_hvn)
    out.update(resolved)
    metrics = _path_metrics(
        approach,
        bars,
        touch_i,
        end_i,
        measurement,
        lower_hvn,
        upper_hvn,
        float(row["valley_left_price"]),
        float(row["valley_right_price"]),
    )
    out.update(metrics)
    return out


def verify_step3_identity(sample: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    touched = sample.loc[sample["touched"]].copy()
    lower_n = int((touched["approach"] == "lower_region").sum())
    upper_n = int((touched["approach"] == "upper_region").sum())
    open_n = int((touched["approach"] == "open_in_band").sum())
    if lower_n != EXPECTED_LOWER or upper_n != EXPECTED_UPPER or open_n != EXPECTED_OPEN_IN_BAND:
        raise SystemExit(
            f"Step 3 touch identity mismatch. "
            f"lower={lower_n} upper={upper_n} open_in_band={open_n}. Stopping."
        )
    primary = touched.loc[touched["approach"].isin(PRIMARY_APPROACHES)].copy()
    if len(primary) != EXPECTED_LOWER + EXPECTED_UPPER:
        raise SystemExit(f"Primary sample size {len(primary)} unexpected. Stopping.")
    return primary, touched.loc[touched["approach"] == "open_in_band"].copy()


def run() -> None:
    sample = pd.read_csv(RESULTS / "step3_interactions_sample.csv")
    primary, open_rows = verify_step3_identity(sample)
    cache: dict[str, pd.DataFrame] = {}
    path_rows = []
    open_path_rows = []
    for frame, sink in ((primary, path_rows), (open_rows, open_path_rows)):
        for row in frame.itertuples(index=False):
            key = str(row.next_session)
            if key not in cache:
                bars = load_session_minute_bars(_parse_date(key))
                if bars.empty:
                    raise SystemExit(f"No trade bars for next session {key}. Stopping.")
                cache[key] = bars
            bars = cache[key]
            series = pd.Series(row._asdict())
            for horizon_name, minutes in HORIZONS:
                sink.append(evaluate_row(series, bars, horizon_name, minutes))

    paths = pd.DataFrame(path_rows)
    opens = pd.DataFrame(open_path_rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    paths.to_csv(RESULTS / "step4_paths.csv", index=False)
    opens.to_csv(RESULTS / "step4_open_in_band.csv", index=False)

    summary = []
    for horizon_name, _minutes in HORIZONS:
        part = paths.loc[paths["horizon"] == horizon_name]
        decided = part.loc[part["outcome"].isin(["traverse", "reject"])]
        null_ok = decided.loc[decided["null_defined"]]
        obs = float((null_ok["outcome"] == "traverse").mean()) if len(null_ok) else float("nan")
        null_mean = float(null_ok["null_traverse_prob"].mean()) if len(null_ok) else float("nan")
        diff = (
            float(((null_ok["outcome"] == "traverse").astype(float) - null_ok["null_traverse_prob"]).mean())
            if len(null_ok)
            else float("nan")
        )
        counts = part["outcome"].value_counts().to_dict()
        summary.append(
            {
                "horizon": horizon_name,
                "n": int(len(part)),
                "traverse": int(counts.get("traverse", 0)),
                "reject": int(counts.get("reject", 0)),
                "remain": int(counts.get("remain", 0)),
                "ambiguous_same_bar": int(counts.get("ambiguous_same_bar", 0)),
                "decided_n": int(len(decided)),
                "null_compare_n": int(len(null_ok)),
                "observed_traverse_share_decided": obs,
                "mean_null_traverse_prob": null_mean,
                "mean_traverse_minus_null": diff,
            }
        )
    summary_frame = pd.DataFrame(summary)
    summary_frame.to_csv(RESULTS / "step4_summary.csv", index=False)
    verification = {
        "primary_rows": int(len(primary)),
        "lower_region": EXPECTED_LOWER,
        "upper_region": EXPECTED_UPPER,
        "open_in_band": EXPECTED_OPEN_IN_BAND,
        "path_rows": int(len(paths)),
        "horizons": [name for name, _ in HORIZONS],
    }
    (RESULTS / "step4_verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(f"[step4] primary={len(primary)} path_rows={len(paths)}", flush=True)
    print(summary_frame.to_string(index=False), flush=True)


def run_self_check() -> None:
    ts0 = pd.Timestamp("2026-01-01 18:00", tz="America/New_York")
    bars = pd.DataFrame(
        {
            "ts": [ts0 + pd.Timedelta(minutes=i) for i in range(5)],
            "open": [105.0, 110.0, 115.0, 120.0, 118.0],
            "high": [106.0, 112.0, 126.0, 121.0, 119.0],
            "low": [104.0, 109.0, 114.0, 100.0, 117.0],
            "close": [105.0, 111.0, 125.0, 101.0, 118.0],
        }
    )
    # touch at bar 1; lower approach; traverse on bar 2 (high 126 >= 125) before reject on bar 3
    got = resolve_path("lower_region", bars, 1, 4, 100.0, 125.0)
    if got["outcome"] != "traverse" or got["event_bar"] != 2:
        raise AssertionError(f"expected traverse on bar 2, got {got}")
    # reject first
    bars2 = bars.copy()
    bars2.loc[2, ["high", "low"]] = [112.0, 99.0]
    got2 = resolve_path("lower_region", bars2, 1, 4, 100.0, 125.0)
    if got2["outcome"] != "reject":
        raise AssertionError(f"expected reject, got {got2}")
    # same bar both
    bars3 = bars.copy()
    bars3.loc[2, ["high", "low"]] = [126.0, 99.0]
    got3 = resolve_path("lower_region", bars3, 1, 4, 100.0, 125.0)
    if got3["outcome"] != "ambiguous_same_bar":
        raise AssertionError(f"expected ambiguous, got {got3}")
    # null geometry
    p = 110.0
    null = abs(p - 100.0) / (abs(p - 100.0) + abs(p - 125.0))
    if not np.isclose(null, 10 / 25):
        raise AssertionError(null)
    print("[step4] self-check passed", flush=True)


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    run()


if __name__ == "__main__":
    main()
