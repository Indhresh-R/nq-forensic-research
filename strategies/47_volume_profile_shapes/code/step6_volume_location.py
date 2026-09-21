"""Step 6 prior-volume location measurements.

Definitions are copied from STEP6_PREREGISTRATION.md.
No LVN events, no null, no P&L, and no threshold search.
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

from boundaries import SYNC_TOLERANCE, _parse_date
from continuous_scores import EXPECTED_N, verify_sample
from frozen import POC_BAND_FRAC, RESULTS, TICK_SIZE
from interaction_audit import _complete, load_session_minute_bars

EXPECTED_PAIRS = EXPECTED_N - 1
PRICE_ATOL = 1e-8


def open_third(open_price: float, profile_low: float, profile_high: float) -> str:
    """Map a price onto the prior profile using the Step 2 integer third rule."""
    if open_price < profile_low - PRICE_ATOL:
        return "outside_below"
    if open_price > profile_high + PRICE_ATOL:
        return "outside_above"
    span_ticks = (profile_high - profile_low) / TICK_SIZE
    if abs(span_ticks - round(span_ticks)) > 1e-6:
        raise SystemExit("Prior range is not an integer number of ticks. Stopping.")
    range_ticks = int(round(span_ticks))
    if range_ticks <= 0:
        raise SystemExit("Prior range is not positive. Stopping.")
    offset = (open_price - profile_low) / TICK_SIZE
    if abs(offset - round(offset)) > 1e-6:
        raise SystemExit(
            f"Next open {open_price} is not on the prior tick grid. Stopping."
        )
    index = int(round(offset))
    if index < 0 or index > range_ticks:
        raise SystemExit("Open index fell outside the prior range. Stopping.")
    if 3 * index < range_ticks:
        return "prior_lower"
    if 3 * index < 2 * range_ticks:
        return "prior_middle"
    return "prior_upper"


def _distribution(series: pd.Series) -> dict:
    values = series.dropna().astype(float)
    if values.empty:
        return {"n": 0}
    quantiles = values.quantile([0.0, 0.25, 0.5, 0.75, 1.0])
    return {
        "n": int(len(values)),
        "mean": float(values.mean()),
        "min": float(quantiles.loc[0.0]),
        "p25": float(quantiles.loc[0.25]),
        "median": float(quantiles.loc[0.5]),
        "p75": float(quantiles.loc[0.75]),
        "max": float(quantiles.loc[1.0]),
    }


def _measure_pair(prior: pd.Series, bars: pd.DataFrame) -> dict:
    profile_low = float(prior["prior_profile_low"])
    profile_high = float(prior["prior_profile_high"])
    prior_range = float(prior["prior_range"])
    if prior_range <= 0:
        raise SystemExit(f"Non-positive prior range for {prior['prior_session']}. Stopping.")
    poc = float(prior["prior_poc"])
    first_open = float(bars["open"].iloc[0])
    band = POC_BAND_FRAC * prior_range
    band_low = poc - band
    band_high = poc + band
    lows = bars["low"].to_numpy(dtype=float)
    highs = bars["high"].to_numpy(dtype=float)
    closes = bars["close"].to_numpy(dtype=float)
    volumes = bars["volume"].to_numpy(dtype=float)
    if np.any(volumes <= 0):
        raise SystemExit(f"Non-positive bar volume on {prior['next_session']}. Stopping.")
    near = (highs >= band_low - 1e-12) & (lows <= band_high + 1e-12)
    cross = (lows <= poc + 1e-12) & (highs >= poc - 1e-12)
    typical = (highs + lows + closes) / 3.0
    vwap_proxy = float(np.average(typical, weights=volumes))
    near_index = int(np.flatnonzero(near)[0]) if bool(near.any()) else -1
    cross_index = int(np.flatnonzero(cross)[0]) if bool(cross.any()) else -1
    if near_index >= 0:
        minutes = (bars["ts"].iloc[near_index] - bars["ts"].iloc[0]).total_seconds() / 60.0
        touch_status = "touch"
    else:
        minutes = float("nan")
        touch_status = "no_touch"
    if cross_index >= 0:
        later = closes[cross_index + 1 :]
        n_above = int((later > poc + 1e-12).sum())
        n_below = int((later < poc - 1e-12).sum())
        n_equal = int(len(later) - n_above - n_below)
        imbalance = n_above - n_below
    else:
        n_above = n_below = n_equal = 0
        imbalance = float("nan")
    return {
        "open_to_poc": first_open - poc,
        "open_to_poc_frac": (first_open - poc) / prior_range,
        "open_third": open_third(first_open, profile_low, profile_high),
        "n_bars": int(len(bars)),
        "near_bar_n": int(near.sum()),
        "near_share": float(near.mean()),
        "minutes_to_poc_band": float(minutes),
        "poc_band_status": touch_status,
        "touched_poc_band": bool(near.any()),
        "crossed_poc": bool(cross.any()),
        "closes_after_cross": int(len(closes) - cross_index - 1) if cross_index >= 0 else 0,
        "closes_above": n_above,
        "closes_below": n_below,
        "closes_equal": n_equal,
        "close_imbalance": imbalance,
        "next_vwap_proxy": vwap_proxy,
        "migration_frac": (vwap_proxy - poc) / prior_range,
        "in_location_sample": True,
        "exclude_reason": "",
    }


def _empty_measure(reason: str, n_bars: int) -> dict:
    return {
        "open_to_poc": np.nan,
        "open_to_poc_frac": np.nan,
        "open_third": "",
        "n_bars": n_bars,
        "near_bar_n": 0,
        "near_share": np.nan,
        "minutes_to_poc_band": np.nan,
        "poc_band_status": "",
        "touched_poc_band": False,
        "crossed_poc": False,
        "closes_after_cross": 0,
        "closes_above": 0,
        "closes_below": 0,
        "closes_equal": 0,
        "close_imbalance": np.nan,
        "next_vwap_proxy": np.nan,
        "migration_frac": np.nan,
        "in_location_sample": False,
        "exclude_reason": reason,
    }


def _summarize(frame: pd.DataFrame) -> dict:
    sample = frame.loc[frame["in_location_sample"]].copy()
    open_counts = sample["open_third"].value_counts().to_dict()
    cross = pd.crosstab(sample["prior_dominant_third"], sample["open_third"])
    migration_by_third = {
        str(name): _distribution(part["migration_frac"])
        for name, part in sample.groupby("prior_dominant_third", sort=True)
    }
    touched = sample.loc[sample["touched_poc_band"]]
    crossed_among_touch = touched.loc[touched["crossed_poc"]]
    imbalance = crossed_among_touch["close_imbalance"]
    month_counts = (
        sample["next_session"].astype(str).str.slice(0, 7).value_counts().sort_index().to_dict()
    )
    return {
        "date_list_pairs": int(len(frame)),
        "location_sample": int(len(sample)),
        "excluded": frame.loc[~frame["in_location_sample"], "exclude_reason"].value_counts().to_dict(),
        "calendar_gap_pairs": int((frame["calendar_gap_days"] > 1).sum()),
        "open_to_poc_frac": _distribution(sample["open_to_poc_frac"]),
        "open_third_counts": {str(key): int(value) for key, value in open_counts.items()},
        "dominant_by_open_third": {
            str(idx): {str(col): int(cross.loc[idx, col]) for col in cross.columns}
            for idx in cross.index
        },
        "touched_poc_band_n": int(sample["touched_poc_band"].sum()),
        "touched_poc_band_share": float(sample["touched_poc_band"].mean()) if len(sample) else float("nan"),
        "minutes_to_poc_band_among_touches": _distribution(touched["minutes_to_poc_band"]),
        "near_share": _distribution(sample["near_share"]),
        "migration_frac": _distribution(sample["migration_frac"]),
        "migration_by_dominant_third": migration_by_third,
        "crossed_poc_n": int(sample["crossed_poc"].sum()),
        "band_touch_and_cross_n": int(len(crossed_among_touch)),
        "band_touch_without_cross_n": int((~touched["crossed_poc"]).sum()),
        "close_imbalance_among_crosses": _distribution(imbalance),
        "imbalance_above": int((imbalance > 0).sum()),
        "imbalance_below": int((imbalance < 0).sum()),
        "imbalance_tie": int((imbalance == 0).sum()),
        "cross_with_no_later_close": int((crossed_among_touch["closes_after_cross"] == 0).sum()),
        "next_session_month_counts": {str(key): int(value) for key, value in month_counts.items()},
        "dominant_third_counts": {
            str(key): int(value)
            for key, value in sample["prior_dominant_third"].value_counts().sort_index().items()
        },
        "null": None,
        "note": "STEP6_PREREGISTRATION defers a location null. None is computed.",
    }


def run() -> None:
    dataset = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    raw = pd.read_parquet(RESULTS / "raw_price_volume.parquet")
    sample = verify_sample(dataset, raw)
    sessions = pd.read_csv(RESULTS / "step2_sessions.csv")
    sessions["session_date"] = sessions["session_date"].astype(str)
    sample["session_date"] = sample["session_date"].astype(str)
    dates = sorted(sample["session_date"].tolist())
    if set(sessions["session_date"]) != set(dates):
        raise SystemExit("Step 2 session dates do not match the analysis sample. Stopping.")
    pairs = list(zip(dates, dates[1:]))
    if len(pairs) != EXPECTED_PAIRS:
        raise SystemExit(
            f"Adjacent analysis pairs are {len(pairs)}, expected {EXPECTED_PAIRS}. Stopping."
        )

    stored = sample.set_index("session_date")
    step2 = sessions.set_index("session_date")
    for date_key in dates:
        left = step2.loc[date_key]
        right = stored.loc[date_key]
        for left_name, right_name in (
            ("poc_price", "poc"),
            ("poc_location", "poc_location"),
            ("vw_std_norm", "vw_std_norm"),
            ("poc_concentration_10", "poc_concentration_10"),
        ):
            if not np.isclose(float(left[left_name]), float(right[right_name]), rtol=0, atol=1e-8):
                raise SystemExit(
                    f"Stored {left_name} disagrees with Step 1 for {date_key}. Stopping."
                )
        shares = (
            float(left["lower_share"]),
            float(left["middle_share"]),
            float(left["upper_share"]),
        )
        if abs(sum(shares) - 1.0) > 1e-8:
            raise SystemExit(f"Third shares do not sum to 1 for {date_key}. Stopping.")
        best = max(shares)
        expected = "lower"
        for name, share in zip(("lower", "middle", "upper"), shares):
            if share == best:
                expected = name
                break
        if str(left["dominant_third"]) != expected:
            raise SystemExit(f"Dominant third disagrees with the tie rule for {date_key}. Stopping.")

    cache: dict[str, pd.DataFrame] = {}
    rows = []
    for prior_key, next_key in pairs:
        prior = step2.loc[prior_key]
        profile = stored.loc[prior_key]
        prior_range = float(profile["profile_high"]) - float(profile["profile_low"])
        record = {
            "prior_session": prior_key,
            "next_session": next_key,
            "calendar_gap_days": (_parse_date(next_key) - _parse_date(prior_key)).days,
            "prior_poc": float(prior["poc_price"]),
            "prior_poc_location": float(prior["poc_location"]),
            "prior_lower_share": float(prior["lower_share"]),
            "prior_middle_share": float(prior["middle_share"]),
            "prior_upper_share": float(prior["upper_share"]),
            "prior_dominant_third": str(prior["dominant_third"]),
            "prior_vw_std_norm": float(prior["vw_std_norm"]),
            "prior_poc_concentration_10": float(prior["poc_concentration_10"]),
            "prior_profile_low": float(profile["profile_low"]),
            "prior_profile_high": float(profile["profile_high"]),
            "prior_range": prior_range,
        }
        if next_key not in cache:
            cache[next_key] = load_session_minute_bars(_parse_date(next_key))
        bars = cache[next_key]
        if not _complete(bars):
            record.update(_empty_measure("incomplete_next_trades", int(len(bars))))
            rows.append(record)
            continue
        next_profile = stored.loc[next_key]
        high_gap = abs(float(bars["high"].max()) - float(next_profile["profile_high"]))
        low_gap = abs(float(bars["low"].min()) - float(next_profile["profile_low"]))
        if high_gap > SYNC_TOLERANCE or low_gap > SYNC_TOLERANCE:
            raise SystemExit(
                f"Trade-bar sync failed for next session {next_key}: "
                f"high_gap={high_gap} low_gap={low_gap}. Stopping."
            )
        record.update(_measure_pair(pd.Series({**record, "session_date": prior_key}), bars))
        rows.append(record)

    frame = pd.DataFrame(rows)
    summary = _summarize(frame)
    RESULTS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RESULTS / "step6_volume_location.csv", index=False)
    (RESULTS / "step6_volume_location_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(
        f"[step6] pairs={summary['date_list_pairs']} sample={summary['location_sample']} "
        f"excluded={summary['excluded']}",
        flush=True,
    )
    print(json.dumps(summary, indent=2), flush=True)


def run_self_check() -> None:
    # R = 10. Cuts: lower i with 3i < 10, middle 3i < 20, else upper.
    low = 100.0
    high = 100.0 + 10 * TICK_SIZE
    if open_third(low, low, high) != "prior_lower":
        raise AssertionError("index 0 should be prior_lower")
    if open_third(low + 3 * TICK_SIZE, low, high) != "prior_lower":
        raise AssertionError("index 3 should be prior_lower")
    if open_third(low + 4 * TICK_SIZE, low, high) != "prior_middle":
        raise AssertionError("index 4 should be prior_middle")
    if open_third(low + 6 * TICK_SIZE, low, high) != "prior_middle":
        raise AssertionError("index 6 should be prior_middle")
    if open_third(high, low, high) != "prior_upper":
        raise AssertionError("profile high should be prior_upper")
    if open_third(low - TICK_SIZE, low, high) != "outside_below":
        raise AssertionError("below the prior low")
    if open_third(high + TICK_SIZE, low, high) != "outside_above":
        raise AssertionError("above the prior high")
    print("[step6] self-check passed", flush=True)


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    run()


if __name__ == "__main__":
    main()
