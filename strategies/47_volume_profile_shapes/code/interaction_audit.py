"""Next-session interaction audit for prior LVN bands.

Definitions are copied from STEP3_PREREGISTRATION.md. No returns are computed.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[3]
CODE_DIR = Path(__file__).resolve().parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from boundaries import SYNC_TOLERANCE, _parse_date
from build_profiles import read_trades, session_bounds
from frozen import RESULTS, TICK_SIZE, TRADES_DIR

APPROACH_LABELS = (
    "lower_region",
    "upper_region",
    "outside_below",
    "outside_above",
    "other_inside",
    "open_in_band",
)
NY = ZoneInfo("America/New_York")


def _zone(price: float, boundary: pd.Series) -> str:
    if boundary["valley_left_price"] - 1e-12 <= price <= boundary["valley_right_price"] + 1e-12:
        return "lvn_band"
    if boundary["lower_left"] - 1e-12 <= price <= boundary["lower_right"] + 1e-12:
        return "lower_region"
    if boundary["upper_left"] - 1e-12 <= price <= boundary["upper_right"] + 1e-12:
        return "upper_region"
    if price < boundary["profile_low"] - 1e-12:
        return "outside_below"
    if price > boundary["profile_high"] + 1e-12:
        return "outside_above"
    return "other_inside"


def _intersects(low: float, high: float, left: float, right: float) -> bool:
    return high >= left - 1e-12 and low <= right + 1e-12


def _trade_files_for_session(session: date) -> list[Path]:
    names = {
        f"trades_24h_{session.isoformat()}.dbn.zst",
        f"trades_24h_{(session + timedelta(days=1)).isoformat()}.dbn.zst",
    }
    paths = []
    for name in sorted(names):
        path = TRADES_DIR / name
        if path.exists():
            paths.append(path)
    return paths


def load_session_minute_bars(session: date) -> pd.DataFrame:
    start, end = session_bounds(session)
    frames = []
    for path in _trade_files_for_session(session):
        frame = read_trades(path)
        part = frame.loc[frame["session_date"] == session].copy()
        if part.empty:
            continue
        part = part.loc[part["size"] > 0]
        if part.empty:
            continue
        frames.append(part)
    if not frames:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume", "ny_min"])
    trades = pd.concat(frames, ignore_index=True)
    trades = trades.sort_values(["ts_event", "sequence"], kind="mergesort").reset_index(drop=True)
    prices = trades["price_ticks"].to_numpy(dtype=np.float64) * TICK_SIZE
    ts = pd.to_datetime(trades["ts_event"], utc=True).dt.tz_convert(NY)
    keep = (ts >= start) & (ts < end)
    trades = trades.loc[keep].copy()
    prices = prices[keep.to_numpy()]
    ts = ts.loc[keep]
    if trades.empty:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume", "ny_min"])
    minute = ts.dt.floor("min")
    bars = pd.DataFrame(
        {
            "ts": minute,
            "price": prices,
            "size": trades["size"].to_numpy(dtype=np.int64),
        }
    )
    grouped = bars.groupby("ts", sort=True)
    out = pd.DataFrame(
        {
            "ts": grouped["ts"].first().to_numpy(),
            "open": grouped["price"].first().to_numpy(dtype=float),
            "high": grouped["price"].max().to_numpy(dtype=float),
            "low": grouped["price"].min().to_numpy(dtype=float),
            "close": grouped["price"].last().to_numpy(dtype=float),
            "volume": grouped["size"].sum().to_numpy(dtype=np.int64),
        }
    ).reset_index(drop=True)
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    return out


def _complete(bars: pd.DataFrame) -> bool:
    if bars.empty:
        return False
    first = int(bars["ny_min"].iloc[0])
    if first < 18 * 60 or first > 18 * 60 + 5:
        return False
    return bool(((bars["ny_min"] >= 16 * 60) & (bars["ny_min"] <= 16 * 60 + 59)).any())


def audit_boundary(boundary: pd.Series, bars: pd.DataFrame) -> dict:
    opens = bars["open"].to_numpy(dtype=float)
    highs = bars["high"].to_numpy(dtype=float)
    lows = bars["low"].to_numpy(dtype=float)
    closes = bars["close"].to_numpy(dtype=float)
    band_left = float(boundary["valley_left_price"])
    band_right = float(boundary["valley_right_price"])
    open_zone = _zone(float(opens[0]), boundary)
    touch_i = None
    for i in range(len(bars)):
        if _intersects(float(lows[i]), float(highs[i]), band_left, band_right):
            touch_i = i
            break
    if touch_i is None:
        return {
            "touched": False,
            "open_zone": open_zone,
            "approach": "",
            "touch_bar": -1,
            "minutes_to_touch": np.nan,
            "touch_open": np.nan,
            "reached_opposite_side": False,
            "returned_to_approach": False,
            "later_touched_lower_hvn": False,
            "later_touched_upper_hvn": False,
        }
    if touch_i == 0:
        approach = "open_in_band" if open_zone == "lvn_band" else open_zone
    else:
        approach = _zone(float(closes[touch_i - 1]), boundary)
        if approach == "lvn_band":
            raise RuntimeError(
                f"previous close in LVN band without earlier intersection: "
                f"{boundary['prior_session']} gap {boundary['gap_index']}"
            )
    minutes = (bars["ts"].iloc[touch_i] - bars["ts"].iloc[0]).total_seconds() / 60.0
    lower_hvn = float(boundary["lower_hvn_price"])
    upper_hvn = float(boundary["upper_hvn_price"])
    later_low = float(lows[touch_i + 1 :].min()) if touch_i + 1 < len(bars) else np.nan
    later_high = float(highs[touch_i + 1 :].max()) if touch_i + 1 < len(bars) else np.nan
    touched_lower = bool(later_low == later_low and later_low <= lower_hvn + 1e-12)
    touched_upper = bool(later_high == later_high and later_high >= upper_hvn - 1e-12)
    if approach == "lower_region":
        reached_opposite = touched_upper
    elif approach == "upper_region":
        reached_opposite = touched_lower
    else:
        reached_opposite = touched_lower and touched_upper
    returned = False
    if approach in ("lower_region", "upper_region") and touch_i + 1 < len(bars):
        left = float(boundary["lower_left" if approach == "lower_region" else "upper_left"])
        right = float(boundary["lower_right" if approach == "lower_region" else "upper_right"])
        for j in range(touch_i + 1, len(bars)):
            if _intersects(float(lows[j]), float(highs[j]), left, right):
                returned = True
                break
    return {
        "touched": True,
        "open_zone": open_zone,
        "approach": approach,
        "touch_bar": int(touch_i),
        "minutes_to_touch": float(minutes),
        "touch_open": float(opens[touch_i]),
        "reached_opposite_side": bool(reached_opposite),
        "returned_to_approach": bool(returned),
        "later_touched_lower_hvn": touched_lower,
        "later_touched_upper_hvn": touched_upper,
    }


def run_audit() -> pd.DataFrame:
    boundaries = pd.read_csv(RESULTS / "step3_boundaries.csv")
    dataset = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    dataset["session_date"] = dataset["session_date"].astype(str)
    cache: dict[str, pd.DataFrame] = {}
    rows = []
    excluded = {
        "no_next_session": 0,
        "incomplete_next_trades": 0,
        "sync_mismatch": 0,
    }
    for boundary in boundaries.itertuples(index=False):
        record = boundary._asdict()
        if not bool(boundary.has_next_session):
            excluded["no_next_session"] += 1
            record.update(
                {
                    "in_interaction_sample": False,
                    "exclude_reason": "no_next_session",
                    "touched": False,
                    "open_zone": "",
                    "approach": "",
                }
            )
            rows.append(record)
            continue
        next_key = str(boundary.next_session)
        if next_key not in cache:
            cache[next_key] = load_session_minute_bars(_parse_date(next_key))
        bars = cache[next_key]
        if not _complete(bars):
            excluded["incomplete_next_trades"] += 1
            record.update(
                {
                    "in_interaction_sample": False,
                    "exclude_reason": "incomplete_next_trades",
                    "touched": False,
                    "open_zone": "",
                    "approach": "",
                    "next_1m_bars": int(len(bars)),
                }
            )
            rows.append(record)
            continue
        next_profile = dataset.loc[dataset["session_date"] == next_key]
        if len(next_profile) != 1:
            raise SystemExit(f"Next session {next_key} missing from profile dataset.")
        next_row = next_profile.iloc[0]
        high_gap = abs(float(bars["high"].max()) - float(next_row["profile_high"]))
        low_gap = abs(float(bars["low"].min()) - float(next_row["profile_low"]))
        if high_gap > SYNC_TOLERANCE or low_gap > SYNC_TOLERANCE:
            excluded["sync_mismatch"] += 1
            raise SystemExit(
                f"Trade-bar sync failed for next session {next_key}: "
                f"high_gap={high_gap} low_gap={low_gap}. Stopping."
            )
        audit = audit_boundary(pd.Series(record), bars)
        record.update(audit)
        record["in_interaction_sample"] = True
        record["exclude_reason"] = ""
        record["next_1m_bars"] = int(len(bars))
        rows.append(record)

    out = pd.DataFrame(rows)
    sample = out.loc[out["in_interaction_sample"]].copy()
    RESULTS.mkdir(parents=True, exist_ok=True)
    out.to_csv(RESULTS / "step3_interactions.csv", index=False)
    sample.to_csv(RESULTS / "step3_interactions_sample.csv", index=False)
    touch = sample.loc[sample["touched"]]
    approach_counts = touch["approach"].value_counts().to_dict()
    open_counts = sample["open_zone"].value_counts().to_dict()
    verification = {
        "boundary_rows": int(len(out)),
        "interaction_sample": int(len(sample)),
        "excluded": excluded,
        "touched": int(sample["touched"].sum()),
        "no_touch": int((~sample["touched"]).sum()),
        "approach_counts": {key: int(approach_counts.get(key, 0)) for key in APPROACH_LABELS},
        "open_zone_counts": {str(key): int(value) for key, value in open_counts.items()},
        "price_source": "trades_24h_1m_ohlc",
    }
    (RESULTS / "step3_interaction_verification.json").write_text(
        json.dumps(verification, indent=2),
        encoding="utf-8",
    )
    print(
        f"[step3] interaction_sample={len(sample)} touched={verification['touched']} "
        f"excluded={excluded}",
        flush=True,
    )
    return out


def run_self_check() -> None:
    boundary = pd.Series(
        {
            "prior_session": "synthetic",
            "gap_index": 0,
            "lower_left": 100.0,
            "lower_right": 110.0,
            "upper_left": 120.0,
            "upper_right": 130.0,
            "valley_left_price": 111.0,
            "valley_right_price": 119.0,
            "profile_low": 100.0,
            "profile_high": 130.0,
            "lower_hvn_price": 105.0,
            "upper_hvn_price": 125.0,
        }
    )
    ts0 = pd.Timestamp("2026-01-01 18:00", tz="America/New_York")
    bars = pd.DataFrame(
        {
            "ts": [ts0, ts0 + timedelta(minutes=1), ts0 + timedelta(minutes=2)],
            "open": [105.0, 108.0, 115.0],
            "high": [106.0, 112.0, 126.0],
            "low": [104.0, 107.0, 114.0],
            "close": [105.5, 111.5, 125.0],
            "ny_min": [18 * 60, 18 * 60 + 1, 18 * 60 + 2],
        }
    )
    result = audit_boundary(boundary, bars)
    if not result["touched"] or result["approach"] != "lower_region":
        raise AssertionError(f"expected lower_region approach, got {result}")
    if not result["reached_opposite_side"]:
        raise AssertionError("expected later upper HVN touch")
    if result["returned_to_approach"]:
        raise AssertionError("synthetic path should not return to the lower region")
    bars2 = bars.copy()
    bars2.loc[0, ["open", "high", "low", "close"]] = [115.0, 116.0, 114.0, 115.0]
    result2 = audit_boundary(boundary, bars2)
    if result2["approach"] != "open_in_band":
        raise AssertionError(f"expected open_in_band, got {result2}")
    if TRADES_DIR.name != "trades_24h_6m":
        raise AssertionError("unexpected trade directory")
    print("[step3] interaction self-check passed", flush=True)


def main() -> None:
    run_self_check()
    if "--self-check" in sys.argv:
        return
    run_audit()


if __name__ == "__main__":
    main()
