"""Step 7 deterministic geometric null for prior-POC band contact.

Definitions are copied from STEP7_PREREGISTRATION.md.
The null is the reflection of the prior POC through the next open.
No randomization, no uniform center, no clipping, and no P&L.
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
from frozen import POC_BAND_FRAC, RESULTS
from interaction_audit import load_session_minute_bars

EXPECTED_PAIRS = 95
EXPECTED_POC_TOUCHES = 70
EXPECTED_EXACT_CROSSES = 67
DISTANCE_ATOL = 1e-6
VWAP_ATOL = 1e-6
PRICE_ATOL = 1e-8
INTERSECT_ATOL = 1e-12
CALENDAR_CUT = "2026-06-20"
UNSTABLE_N = 15


def _intersect(lows: np.ndarray, highs: np.ndarray, left: float, right: float) -> np.ndarray:
    return (highs >= left - INTERSECT_ATOL) & (lows <= right + INTERSECT_ATOL)


def _first_minutes(bars: pd.DataFrame, hits: np.ndarray) -> float:
    if not bool(hits.any()):
        return float("nan")
    index = int(np.flatnonzero(hits)[0])
    return float((bars["ts"].iloc[index] - bars["ts"].iloc[0]).total_seconds() / 60.0)


def _imbalance(closes: np.ndarray, hits: np.ndarray, level: float) -> float:
    if not bool(hits.any()):
        return float("nan")
    index = int(np.flatnonzero(hits)[0])
    later = closes[index + 1 :]
    n_above = int((later > level + INTERSECT_ATOL).sum())
    n_below = int((later < level - INTERSECT_ATOL).sum())
    return float(n_above - n_below)


def _score_center(bars: pd.DataFrame, center: float, half_width: float) -> dict:
    lows = bars["low"].to_numpy(dtype=float)
    highs = bars["high"].to_numpy(dtype=float)
    closes = bars["close"].to_numpy(dtype=float)
    band_hits = _intersect(lows, highs, center - half_width, center + half_width)
    point_hits = _intersect(lows, highs, center, center)
    return {
        "band_touch": bool(band_hits.any()),
        "point_touch": bool(point_hits.any()),
        "minutes_to_band": _first_minutes(bars, band_hits),
        "imbalance": _imbalance(closes, point_hits, center),
    }


def _touch_order(poc_touch: bool, poc_minutes: float, null_touch: bool, null_minutes: float) -> str:
    poc_key = (0, poc_minutes) if poc_touch else (1, 0.0)
    null_key = (0, null_minutes) if null_touch else (1, 0.0)
    if poc_key < null_key:
        return "poc_sooner"
    if null_key < poc_key:
        return "null_sooner"
    return "tie"


def _rate_row(frame: pd.DataFrame, obs_col: str, null_col: str) -> dict:
    n = int(len(frame))
    obs_n = int(frame[obs_col].sum()) if n else 0
    null_n = int(frame[null_col].sum()) if n else 0
    obs = float(obs_n / n) if n else float("nan")
    null = float(null_n / n) if n else float("nan")
    both = int((frame[obs_col] & frame[null_col]).sum()) if n else 0
    poc_only = int((frame[obs_col] & ~frame[null_col]).sum()) if n else 0
    null_only = int((~frame[obs_col] & frame[null_col]).sum()) if n else 0
    neither = int((~frame[obs_col] & ~frame[null_col]).sum()) if n else 0
    return {
        "n": n,
        "observed_n": obs_n,
        "null_n": null_n,
        "observed_rate": obs,
        "null_rate": null,
        "observed_minus_null": obs - null if n else float("nan"),
        "both": both,
        "poc_only": poc_only,
        "null_only": null_only,
        "neither": neither,
        "unstable": bool(n < UNSTABLE_N),
    }


def _median_minutes(series: pd.Series) -> float:
    values = series.dropna().astype(float)
    if values.empty:
        return float("nan")
    return float(values.median())


def _location_bin(location: float) -> str:
    if location < (1.0 / 3.0):
        return "lower"
    if location < (2.0 / 3.0):
        return "middle"
    return "upper"


def _distribution(series: pd.Series) -> dict:
    values = series.dropna().astype(float)
    if values.empty:
        return {"n": 0}
    quantiles = values.quantile([0.25, 0.5, 0.75])
    return {
        "n": int(len(values)),
        "mean": float(values.mean()),
        "median": float(quantiles.loc[0.5]),
        "p25": float(quantiles.loc[0.25]),
        "p75": float(quantiles.loc[0.75]),
    }


def _verdict(audit_ok: bool, delta: float) -> str:
    if not audit_ok:
        return "INCONCLUSIVE"
    if delta > 0:
        return "MECHANISM SUPPORTED"
    return "MECHANISM NOT SUPPORTED"


def _measure_rows(frame: pd.DataFrame) -> pd.DataFrame:
    cache: dict[str, pd.DataFrame] = {}
    rows = []
    for record in frame.itertuples(index=False):
        key = str(record.next_session)
        if key not in cache:
            bars = load_session_minute_bars(_parse_date(key))
            if bars.empty:
                raise SystemExit(f"No trade bars for {key}. Stopping.")
            cache[key] = bars
        bars = cache[key]
        opening = float(bars["open"].iloc[0])
        first_low = float(bars["low"].iloc[0])
        first_high = float(bars["high"].iloc[0])
        if opening < first_low - INTERSECT_ATOL or opening > first_high + INTERSECT_ATOL:
            raise SystemExit(f"First bar does not contain its open on {key}. Stopping.")
        poc = float(record.prior_poc)
        prior_range = float(record.prior_range)
        if prior_range <= 0:
            raise SystemExit(f"Non-positive prior range for {record.prior_session}. Stopping.")
        half_width = POC_BAND_FRAC * prior_range
        displacement = poc - opening
        null_center = opening - displacement
        if abs(abs(null_center - opening) - abs(poc - opening)) > DISTANCE_ATOL:
            raise SystemExit(f"Reflection does not preserve distance for {key}. Stopping.")
        # Raw reflection. Do not clip to the prior profile.
        poc_score = _score_center(bars, poc, half_width)
        null_score = _score_center(bars, null_center, half_width)
        volumes = bars["volume"].to_numpy(dtype=float)
        if np.any(volumes <= 0):
            raise SystemExit(f"Non-positive bar volume on {key}. Stopping.")
        typical = (
            bars["high"].to_numpy(dtype=float)
            + bars["low"].to_numpy(dtype=float)
            + bars["close"].to_numpy(dtype=float)
        ) / 3.0
        vwap = float(np.average(typical, weights=volumes))
        dist_poc = abs(vwap - poc)
        dist_null = abs(vwap - null_center)
        if abs(dist_poc - dist_null) <= PRICE_ATOL:
            closer = "tie"
        elif dist_poc < dist_null:
            closer = "poc"
        else:
            closer = "null"
        inside = abs(poc - opening) <= half_width + PRICE_ATOL
        rows.append(
            {
                "prior_session": str(record.prior_session),
                "next_session": key,
                "open": opening,
                "prior_poc": poc,
                "prior_range": prior_range,
                "prior_poc_location": float(record.prior_poc_location),
                "poc_location_third": _location_bin(float(record.prior_poc_location)),
                "half_width": half_width,
                "displacement": displacement,
                "null_center": null_center,
                "null_outside_prior_range": bool(
                    null_center < float(record.prior_profile_low) - PRICE_ATOL
                    or null_center > float(record.prior_profile_high) + PRICE_ATOL
                ),
                "open_inside_both_bands": bool(inside),
                "n_bars": int(len(bars)),
                "vwap_proxy": vwap,
                "poc_band_touch": poc_score["band_touch"],
                "null_band_touch": null_score["band_touch"],
                "poc_point_touch": poc_score["point_touch"],
                "null_point_touch": null_score["point_touch"],
                "minutes_to_poc_band": poc_score["minutes_to_band"],
                "minutes_to_null_band": null_score["minutes_to_band"],
                "touch_order": _touch_order(
                    poc_score["band_touch"],
                    poc_score["minutes_to_band"],
                    null_score["band_touch"],
                    null_score["minutes_to_band"],
                ),
                "abs_migration_poc": dist_poc / prior_range,
                "abs_migration_null": dist_null / prior_range,
                "closer_center": closer,
                "imbalance_poc": poc_score["imbalance"],
                "imbalance_null": null_score["imbalance"],
            }
        )
    return pd.DataFrame(rows)


def _audit(step6: pd.DataFrame, scored: pd.DataFrame) -> list[str]:
    failures = []
    if len(scored) != EXPECTED_PAIRS:
        failures.append(f"scored {len(scored)} pairs, expected {EXPECTED_PAIRS}")
    merged = step6.merge(scored, on=["prior_session", "next_session"], how="outer", indicator=True)
    if not bool((merged["_merge"] == "both").all()):
        failures.append("pair keys do not match Step 6")
        return failures
    if not np.allclose(merged["prior_poc_x"], merged["prior_poc_y"], rtol=0, atol=DISTANCE_ATOL):
        failures.append("prior POC does not match Step 6")
    if not np.allclose(merged["prior_range_x"], merged["prior_range_y"], rtol=0, atol=DISTANCE_ATOL):
        failures.append("prior range does not match Step 6")
    open_from_step6 = merged["prior_poc_x"] + merged["open_to_poc"]
    if not np.allclose(open_from_step6, merged["open"], rtol=0, atol=DISTANCE_ATOL):
        failures.append("open does not match Step 6 open_to_poc")
    if not np.allclose(merged["next_vwap_proxy"], merged["vwap_proxy"], rtol=0, atol=VWAP_ATOL):
        failures.append("VWAP proxy does not match Step 6")
    if not np.allclose(merged["n_bars_x"], merged["n_bars_y"], rtol=0, atol=0):
        failures.append("bar count does not match Step 6")
    step6_touch = merged["touched_poc_band"].astype(bool)
    if not bool((step6_touch == merged["poc_band_touch"]).all()):
        failures.append("POC-band touch flags disagree with Step 6")
    if int(merged["poc_band_touch"].sum()) != EXPECTED_POC_TOUCHES:
        failures.append(
            f"POC-band touch count is {int(merged['poc_band_touch'].sum())}, expected {EXPECTED_POC_TOUCHES}"
        )
    step6_cross = merged["crossed_poc"].astype(bool)
    if not bool((step6_cross == merged["poc_point_touch"]).all()):
        failures.append("exact POC cross flags disagree with Step 6")
    if int(merged["poc_point_touch"].sum()) != EXPECTED_EXACT_CROSSES:
        failures.append(
            f"exact cross count is {int(merged['poc_point_touch'].sum())}, expected {EXPECTED_EXACT_CROSSES}"
        )
    if not np.allclose(merged["half_width"], POC_BAND_FRAC * merged["prior_range_y"], rtol=0, atol=PRICE_ATOL):
        failures.append("half-width is not 0.10 * prior range")
    reflected = 2.0 * merged["open"] - merged["prior_poc_y"]
    if not np.allclose(merged["null_center"], reflected, rtol=0, atol=PRICE_ATOL):
        failures.append("null center is not 2*O - P")
    if bool(merged["open_inside_both_bands"].any()):
        inside = merged.loc[merged["open_inside_both_bands"]]
        if not bool(inside["poc_band_touch"].all() and inside["null_band_touch"].all()):
            failures.append("open inside the band did not touch both bands")
    return failures


def _summarize(scored: pd.DataFrame, audit_ok: bool, failures: list[str]) -> dict:
    primary = _rate_row(scored, "poc_band_touch", "null_band_touch")
    exact = _rate_row(scored, "poc_point_touch", "null_point_touch")
    outside = scored.loc[~scored["open_inside_both_bands"]]
    inside = scored.loc[scored["open_inside_both_bands"]]
    order_counts = scored["touch_order"].value_counts().to_dict()
    closer_counts = scored["closer_center"].value_counts().to_dict()
    both_cross = scored.loc[scored["poc_point_touch"] & scored["null_point_touch"]]
    paired_imbalance = both_cross["imbalance_poc"] - both_cross["imbalance_null"]
    calendar = {}
    for label, part in (
        ("before_2026-06-20", scored.loc[scored["next_session"] < CALENDAR_CUT]),
        ("from_2026-06-20", scored.loc[scored["next_session"] >= CALENDAR_CUT]),
    ):
        calendar[label] = _rate_row(part, "poc_band_touch", "null_band_touch")
    location = {}
    for name, part in scored.groupby("poc_location_third", sort=False):
        location[str(name)] = _rate_row(part, "poc_band_touch", "null_band_touch")
    delta = float(primary["observed_minus_null"])
    return {
        "audit_ok": audit_ok,
        "audit_failures": failures,
        "verdict": _verdict(audit_ok, delta),
        "primary": primary,
        "exact_level": exact,
        "open_inside_band": _rate_row(inside, "poc_band_touch", "null_band_touch"),
        "open_outside_band": _rate_row(outside, "poc_band_touch", "null_band_touch"),
        "poc_location_third": location,
        "calendar_descriptive": calendar,
        "touch_order_counts": {str(key): int(value) for key, value in order_counts.items()},
        "minutes_to_poc_band_among_touches": _median_minutes(
            scored.loc[scored["poc_band_touch"], "minutes_to_poc_band"]
        ),
        "minutes_to_null_band_among_touches": _median_minutes(
            scored.loc[scored["null_band_touch"], "minutes_to_null_band"]
        ),
        "poc_band_zero_minute_touches": int(
            ((scored["poc_band_touch"]) & (scored["minutes_to_poc_band"] == 0)).sum()
        ),
        "null_band_zero_minute_touches": int(
            ((scored["null_band_touch"]) & (scored["minutes_to_null_band"] == 0)).sum()
        ),
        "mean_abs_migration_poc": float(scored["abs_migration_poc"].mean()),
        "mean_abs_migration_null": float(scored["abs_migration_null"].mean()),
        "abs_migration_poc_minus_null": float(
            scored["abs_migration_poc"].mean() - scored["abs_migration_null"].mean()
        ),
        "closer_counts": {str(key): int(value) for key, value in closer_counts.items()},
        "imbalance_poc_among_crosses": _distribution(scored.loc[scored["poc_point_touch"], "imbalance_poc"]),
        "imbalance_null_among_crosses": _distribution(
            scored.loc[scored["null_point_touch"], "imbalance_null"]
        ),
        "both_levels_crossed_n": int(len(both_cross)),
        "both_levels_crossed_unstable": bool(len(both_cross) < UNSTABLE_N),
        "paired_imbalance_both_crossed": _distribution(paired_imbalance),
        "null_center_outside_prior_range_n": int(scored["null_outside_prior_range"].sum()),
        "sample_altered": False,
        "clipped": False,
        "randomized": False,
    }


def run_self_check() -> None:
    bars = pd.DataFrame(
        {
            "ts": pd.to_datetime(
                ["2026-01-01 09:30", "2026-01-01 09:31", "2026-01-01 09:32"]
            ),
            "open": [100.0, 101.0, 90.0],
            "high": [101.0, 112.0, 91.0],
            "low": [99.0, 101.0, 88.0],
            "close": [100.5, 111.0, 89.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )
    # O = 100, P = 110, R = 100, half-width = 10, P_null = 90.
    # POC band [100, 120] is touched. Null band [80, 100] is touched by the open bar.
    opening = 100.0
    poc = 110.0
    null_center = opening - (poc - opening)
    if null_center != 90.0:
        raise AssertionError("reflection")
    poc_score = _score_center(bars, poc, 10.0)
    null_score = _score_center(bars, null_center, 10.0)
    if not poc_score["band_touch"] or not null_score["band_touch"]:
        raise AssertionError("both bands should touch in the fixture")
    # O = 100, P = 130, half-width = 10. POC band [120, 140]. Mirror center 70, band [60, 80].
    # The bar reaches 125 and only down to 95, so it misses the mirror band.
    one_sided = pd.DataFrame(
        {
            "ts": pd.to_datetime(["2026-01-01 09:30", "2026-01-01 09:31"]),
            "open": [100.0, 110.0],
            "high": [110.0, 125.0],
            "low": [95.0, 108.0],
            "close": [108.0, 124.0],
            "volume": [1.0, 1.0],
        }
    )
    if _score_center(one_sided, 130.0, 10.0)["band_touch"] is not True:
        raise AssertionError("POC band touch")
    if _score_center(one_sided, 70.0, 10.0)["band_touch"] is not False:
        raise AssertionError("mirror band should miss")
    if _touch_order(True, 0.0, False, float("nan")) != "poc_sooner":
        raise AssertionError("non-touch is later")
    if _touch_order(False, float("nan"), False, float("nan")) != "tie":
        raise AssertionError("two non-touches tie")
    if _verdict(False, 0.2) != "INCONCLUSIVE":
        raise AssertionError("audit failure")
    if _verdict(True, 0.01) != "MECHANISM SUPPORTED":
        raise AssertionError("positive delta")
    if _verdict(True, 0.0) != "MECHANISM NOT SUPPORTED":
        raise AssertionError("zero delta")
    if _verdict(True, -0.2) != "MECHANISM NOT SUPPORTED":
        raise AssertionError("negative delta")
    print("[step7] self-check passed", flush=True)


def run() -> None:
    step6 = pd.read_csv(RESULTS / "step6_volume_location.csv")
    step6["prior_session"] = step6["prior_session"].astype(str)
    step6["next_session"] = step6["next_session"].astype(str)
    sample = step6.loc[step6["in_location_sample"].astype(bool)].copy()
    if len(sample) != EXPECTED_PAIRS or len(step6) != EXPECTED_PAIRS:
        raise SystemExit(
            f"Step 6 sample is {len(sample)} in-sample rows of {len(step6)}. Stopping."
        )
    scored = _measure_rows(sample)
    failures = _audit(sample, scored)
    audit_ok = not failures
    summary = _summarize(scored, audit_ok, failures)
    RESULTS.mkdir(parents=True, exist_ok=True)
    scored.to_csv(RESULTS / "step7_pairs.csv", index=False)
    (RESULTS / "step7_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    primary = summary["primary"]
    print(
        f"[step7] audit_ok={audit_ok} verdict={summary['verdict']} "
        f"observed={primary['observed_n']}/{primary['n']} "
        f"null={primary['null_n']}/{primary['n']} "
        f"delta={primary['observed_minus_null']}",
        flush=True,
    )
    if failures:
        print(json.dumps(failures, indent=2), flush=True)
    print(json.dumps(summary, indent=2), flush=True)


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    run()


if __name__ == "__main__":
    main()
