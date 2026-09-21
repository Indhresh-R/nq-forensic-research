"""Attach the previous completed session and detect first interactions.

Previous-session fields are shifted from completed profiles only.
Current-session POC, VAH, and VAL are not attached.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from build_session_profiles import (
    epoch_ns,
    list_trade_files,
    load_config,
    read_trades,
    session_bounds,
    VP,
)

LEVELS = ("poc", "vah", "val", "profile_high", "profile_low")


def _date(value) -> date:
    return date.fromisoformat(str(value)[:10])


def build_research(profiles: pd.DataFrame, tick_size: float) -> pd.DataFrame:
    src = profiles.sort_values("session_date").reset_index(drop=True)
    out = pd.DataFrame({"session_date": src["session_date"]})
    out["prev_session_date"] = src["session_date"].shift(1)
    for col in (
        "poc",
        "vah",
        "val",
        "profile_high",
        "profile_low",
        "total_volume",
        "value_area_width",
        "profile_range",
        "poc_volume_pct",
        "is_roll_transition",
        "is_complete",
    ):
        out[f"prev_{col}"] = src[col].shift(1)
    out["is_roll_transition"] = src["is_roll_transition"].to_numpy()
    out["is_complete"] = src["is_complete"].to_numpy()
    out["open_price"] = src["first_ticks"].to_numpy(dtype=np.float64) * tick_size
    out["instrument_id"] = src["instrument_id"].to_numpy()
    out = out.dropna(subset=["prev_session_date"]).reset_index(drop=True)
    if not (out["prev_session_date"] < out["session_date"]).all():
        raise AssertionError("prev_session_date is not strictly before session_date")
    return out


def _approach(prior: np.ndarray, level: int, tol: int) -> str:
    if prior.size == 0:
        return "ambiguous"
    outside = np.abs(prior - level) > tol
    if not outside.any():
        return "ambiguous"
    last = int(prior[np.flatnonzero(outside)[-1]])
    if last < level:
        return "from_below"
    if last > level:
        return "from_above"
    return "ambiguous"


def _horizon_stats(ticks: np.ndarray, ts: np.ndarray, start_i: int, level: int, horizon_ns: int, session_end_ns: int, approach: str, tick: float) -> dict:
    event_ns = int(ts[start_i])
    limit = min(event_ns + horizon_ns, session_end_ns)
    window = np.flatnonzero((ts >= event_ns) & (ts <= limit) & (np.arange(len(ts)) >= start_i))
    path = ticks[window] if window.size else np.array([level], dtype=np.int64)
    delta = path - level
    if approach == "from_below":
        mfe = int(delta.max())
        mae = int((-delta).max())
    elif approach == "from_above":
        mfe = int((-delta).max())
        mae = int(delta.max())
    else:
        mfe = int(np.abs(delta).max())
        mae = mfe
    target = event_ns + horizon_ns
    fut = np.flatnonzero((ts >= target) & (ts < session_end_ns))
    ret = int(ticks[fut[0]] - level) if fut.size else np.nan
    return {"ret": ret, "mfe": mfe * tick, "mae": mae * tick}


def detect_events(trades: pd.DataFrame, research_row: pd.Series, cfg: dict) -> list[dict]:
    tick = float(cfg["tick_size"])
    tol = int(cfg["interaction_tolerance_ticks"])
    cross = int(cfg["cross_ticks"])
    observe_ns = int(cfg["cross_observe_minutes"]) * 60 * 1_000_000_000
    horizons = [int(v) for v in cfg["horizons_minutes"]]
    session = _date(research_row["session_date"])
    _start, end = session_bounds(session)
    end_ns = int(end.value)
    ordered = trades.sort_values(["ts_event", "sequence"], kind="mergesort")
    ticks = ordered["price_ticks"].to_numpy(dtype=np.int64)
    ts = epoch_ns(ordered["ts_event"])
    events = []
    for name in LEVELS:
        level_px = float(research_row[f"prev_{name}"])
        level = int(round(level_px / tick))
        inside = np.abs(ticks - level) <= tol
        if not inside.any():
            continue
        idx = int(np.flatnonzero(inside)[0])
        approach = _approach(ticks[:idx], level, tol)
        event_ns = int(ts[idx])
        if event_ns < int(_start.value) or event_ns >= end_ns:
            continue
        row = {
            "session_date": research_row["session_date"],
            "prev_session_date": research_row["prev_session_date"],
            "level_name": name,
            "level_price": level * tick,
            "event_ts": pd.to_datetime(event_ns, utc=True),
            "approach": approach,
            "is_roll_transition": bool(research_row["is_roll_transition"]),
            "prev_is_roll_transition": bool(research_row["prev_is_roll_transition"]),
            "is_complete": bool(research_row["is_complete"]),
            "prev_is_complete": bool(research_row["prev_is_complete"]),
            "open_price": float(research_row["open_price"]),
        }
        for minutes in horizons:
            stats = _horizon_stats(ticks, ts, idx, level, minutes * 60 * 1_000_000_000, end_ns, approach, tick)
            row[f"ret_{minutes}m"] = stats["ret"] * tick if stats["ret"] == stats["ret"] else np.nan
            row[f"mfe_{minutes}m"] = stats["mfe"]
            row[f"mae_{minutes}m"] = stats["mae"]
        if name in ("vah", "val"):
            if name == "vah":
                crossed = np.flatnonzero((np.arange(len(ticks)) >= idx) & (ticks >= level + cross) & (ts < end_ns))
            else:
                crossed = np.flatnonzero((np.arange(len(ticks)) >= idx) & (ticks <= level - cross) & (ts < end_ns))
            if crossed.size:
                c0 = int(crossed[0])
                row["time_to_cross_sec"] = (int(ts[c0]) - event_ns) / 1_000_000_000
                observe_end = min(int(ts[c0]) + observe_ns, end_ns)
                after = ticks[(ts >= int(ts[c0])) & (ts <= observe_end)]
                if name == "vah":
                    row["excursion_after_cross"] = float((after - level).max() * tick) if after.size else np.nan
                else:
                    row["excursion_after_cross"] = float((level - after).max() * tick) if after.size else np.nan
            else:
                row["time_to_cross_sec"] = np.nan
                row["excursion_after_cross"] = np.nan
        events.append(row)
    return events


def iter_session_trades(cfg: dict):
    buffers: dict[date, list[pd.DataFrame]] = {}
    files = list_trade_files(cfg)
    for path in files:
        frame = read_trades(path, cfg)
        frame = frame[frame["size"] > 0]
        file_max = frame["ts_event"].max() if len(frame) else pd.Timestamp("1970-01-01", tz="UTC")
        for session, part in frame.groupby("session_date", sort=False):
            buffers.setdefault(session, []).append(part[["ts_event", "sequence", "price_ticks", "size"]])
        ready = []
        for session in list(buffers):
            _start, end = session_bounds(session)
            if file_max >= end:
                ready.append(session)
        for session in ready:
            yield session, pd.concat(buffers.pop(session), ignore_index=True)
        print(f"[events] {path.name} open_sessions={len(buffers)}", flush=True)
        del frame
    for session, parts in buffers.items():
        yield session, pd.concat(parts, ignore_index=True)


def main() -> None:
    cfg = load_config()
    profiles = pd.read_parquet(VP / "data" / "session_profiles.parquet")
    research = build_research(profiles, float(cfg["tick_size"]))
    research.to_parquet(VP / "data" / "session_research.parquet", index=False)
    wanted = {}
    for _, row in research.iterrows():
        wanted[_date(row["session_date"])] = row
    events = []
    for session, trades in iter_session_trades(cfg):
        row = wanted.get(session)
        if row is None:
            continue
        events.extend(detect_events(trades, row, cfg))
    event_frame = pd.DataFrame(events)
    event_frame.to_parquet(VP / "data" / "interaction_events.parquet", index=False)
    print(f"[events] rows={len(event_frame)}", flush=True)


if __name__ == "__main__":
    sys.path.append(str(Path(__file__).resolve().parent))
    main()
