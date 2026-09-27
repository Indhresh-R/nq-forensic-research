"""Build CME-session volume profiles from the 24-hour NQ trade files.

Prints the input audit before any shape classification. Does not label P/b/D/B.
"""

from __future__ import annotations

import json
import traceback
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

from frozen import (
    COMPLETENESS_SLACK_MINUTES,
    EXPECTED_FILE_COUNT,
    EXPECTED_FIRST_FILE,
    EXPECTED_LAST_FILE,
    EXPECTED_SYMBOL,
    MAX_RANGE_TICKS,
    PRICE_SCALE,
    RESULTS,
    ROLL_GAP_POINTS,
    TICK_SIZE,
    TRADES_DIR,
)

NY = ZoneInfo("America/New_York")


def assign_cme_sessions(ts_event_utc: pd.Series) -> pd.Series:
    """New York time at or after 18:00 belongs to that calendar date."""
    ny = pd.to_datetime(ts_event_utc, utc=True).dt.tz_convert(NY)
    day = ny.dt.floor("D")
    session = day.where(ny.dt.hour >= 18, day - pd.Timedelta(days=1))
    return session.dt.date


def assign_cme_session(ts_event_utc) -> date:
    return assign_cme_sessions(pd.Series([ts_event_utc])).iloc[0]


def session_bounds(session_date: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(
        datetime(session_date.year, session_date.month, session_date.day, 18, 0),
        tz=NY,
    )
    nxt = session_date + timedelta(days=1)
    end = pd.Timestamp(datetime(nxt.year, nxt.month, nxt.day, 18, 0), tz=NY)
    return start, end


def session_close(session_date: date) -> pd.Timestamp:
    nxt = session_date + timedelta(days=1)
    return pd.Timestamp(datetime(nxt.year, nxt.month, nxt.day, 17, 0), tz=NY)


def file_date(path: Path) -> str:
    return path.stem.replace("trades_24h_", "").replace(".dbn", "")


def list_trade_files() -> list[Path]:
    return sorted(TRADES_DIR.glob("trades_24h_*.dbn.zst"))


def points_from_price(price: np.ndarray) -> np.ndarray:
    values = np.asarray(price, dtype=np.float64)
    if values.size == 0:
        return values
    if np.nanmax(np.abs(values)) > 1_000_000:
        return values / PRICE_SCALE
    return values


def to_ticks(points: np.ndarray) -> np.ndarray:
    return np.rint(points / TICK_SIZE).astype(np.int64)


def read_trades(path: Path) -> pd.DataFrame:
    store = db.DBNStore.from_file(path)
    symbols = list(getattr(store.metadata, "symbols", []) or [])
    frame = store.to_df()
    if "ts_event" not in frame.columns:
        frame = frame.reset_index()
    if "ts_event" not in frame.columns:
        raise ValueError("ts_event missing")
    for col in ("price", "size"):
        if col not in frame.columns:
            raise ValueError(f"{col} missing")
    points = points_from_price(frame["price"].to_numpy())
    ticks = to_ticks(points)
    out = pd.DataFrame(
        {
            "ts_event": pd.to_datetime(frame["ts_event"], utc=True),
            "price_ticks": ticks,
            "size": frame["size"].to_numpy(dtype=np.int64),
            "sequence": (
                frame["sequence"].to_numpy(dtype=np.int64)
                if "sequence" in frame.columns
                else np.zeros(len(frame), dtype=np.int64)
            ),
            "instrument_id": (
                frame["instrument_id"].to_numpy(dtype=np.int64)
                if "instrument_id" in frame.columns
                else np.zeros(len(frame), dtype=np.int64)
            ),
        }
    )
    out["session_date"] = assign_cme_sessions(out["ts_event"])
    out.attrs["symbols"] = symbols
    out.attrs["max_tick_error"] = (
        float(np.max(np.abs(points - ticks * TICK_SIZE))) if len(points) else 0.0
    )
    return out


def _trade_keys(path: Path) -> set[tuple[int, int, int]]:
    frame = read_trades(path)
    return set(
        zip(
            frame["ts_event"].astype("int64").to_numpy().tolist(),
            frame["sequence"].to_numpy().tolist(),
            frame["instrument_id"].to_numpy().tolist(),
        )
    )


def _count_key_hits(path: Path, keys: set[tuple[int, int, int]]) -> int:
    frame = read_trades(path)
    triples = zip(
        frame["ts_event"].astype("int64").to_numpy().tolist(),
        frame["sequence"].to_numpy().tolist(),
        frame["instrument_id"].to_numpy().tolist(),
    )
    return sum(1 for key in triples if key in keys)


def check_session_assignment() -> None:
    cases = {
        "2026-03-25 22:30:00": date(2026, 3, 25),
        "2026-03-26 04:00:00": date(2026, 3, 25),
        "2026-03-26 14:00:00": date(2026, 3, 25),
        "2026-03-26 20:59:59": date(2026, 3, 25),
        "2026-03-26 21:00:00": date(2026, 3, 25),
        "2026-03-26 21:59:59": date(2026, 3, 25),
        "2026-03-26 22:00:00": date(2026, 3, 26),
        "2026-01-15 23:00:00": date(2026, 1, 15),
        "2026-01-16 21:59:00": date(2026, 1, 15),
        "2026-01-16 22:00:00": date(2026, 1, 15),
        "2026-01-16 23:00:00": date(2026, 1, 16),
        "2026-03-07 23:00:00": date(2026, 3, 7),
        "2026-03-08 06:30:00": date(2026, 3, 7),
        "2026-03-08 07:30:00": date(2026, 3, 7),
        "2026-03-08 22:00:00": date(2026, 3, 8),
        "2026-11-01 05:30:00": date(2026, 10, 31),
        "2026-11-01 06:30:00": date(2026, 10, 31),
        "2026-11-01 23:00:00": date(2026, 11, 1),
    }
    for raw, expected in cases.items():
        got = assign_cme_session(pd.Timestamp(raw, tz="UTC"))
        if got != expected:
            raise AssertionError(f"{raw} -> {got}, expected {expected}")


def _empty_audit(path: Path, status: str, error: str) -> dict:
    return {
        "filename": path.name,
        "file_date": file_date(path),
        "row_count": 0,
        "min_ts_event": "",
        "max_ts_event": "",
        "total_volume": 0,
        "duplicate_extra_rows": 0,
        "negative_size_rows": 0,
        "symbol_ok": False,
        "status": status,
        "error": error,
    }


def mark_rolls(meta: pd.DataFrame) -> pd.DataFrame:
    out = meta.sort_values("session_date").reset_index(drop=True)
    changed = out["instrument_id"].ne(out["instrument_id"].shift(1)) & out["instrument_id"].shift(1).notna()
    multi = out["n_instrument_ids"] > 1
    gap = (out["first_ticks"] - out["last_ticks"].shift(1)).abs() * TICK_SIZE
    gap_flag = gap.fillna(0) >= ROLL_GAP_POINTS
    flag = (changed | multi | gap_flag).copy()
    if len(out):
        flag.iloc[0] = bool(out.iloc[0]["n_instrument_ids"] > 1)
    out["roll_id_change"] = (changed | multi).to_numpy()
    if len(out):
        out.loc[0, "roll_id_change"] = bool(out.iloc[0]["n_instrument_ids"] > 1)
    out["roll_gap"] = gap_flag.to_numpy()
    if len(out):
        out.loc[0, "roll_gap"] = False
    out["is_roll_transition"] = flag.to_numpy()
    return out


def accumulate(files: list[Path]) -> tuple[pd.DataFrame, dict[date, dict[int, int]], dict, dict]:
    volumes: dict[date, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    meta: dict[date, dict] = {}
    audit_rows: list[dict] = []
    parsed = 0
    failed: list[str] = []
    total_trades = 0
    total_volume = 0
    duplicate_extra = 0
    negative_rows = 0
    global_min = None
    global_max = None
    prev_max = None
    overlap_pairs: list[tuple[Path, Path]] = []
    cross_file_duplicate_rows = 0
    prev_path: Path | None = None

    for path in files:
        try:
            frame = read_trades(path)
        except Exception as exc:
            audit_rows.append(_empty_audit(path, "fail", f"{exc.__class__.__name__}: {exc}"))
            failed.append(f"{path.name}: {exc}")
            print(f"[audit] {path.name} FAIL {exc}", flush=True)
            continue

        symbols = frame.attrs.get("symbols", [])
        symbol_ok = EXPECTED_SYMBOL in symbols
        tick_error = float(frame.attrs.get("max_tick_error", 0.0))
        dup_extra = int(frame.duplicated(["ts_event", "sequence", "instrument_id"], keep="first").sum())
        neg = int((frame["size"] < 0).sum())
        row_min = frame["ts_event"].min() if len(frame) else pd.NaT
        row_max = frame["ts_event"].max() if len(frame) else pd.NaT
        vol = int(frame.loc[frame["size"] > 0, "size"].sum()) if len(frame) else 0
        status = "ok"
        error = ""
        if not symbol_ok:
            status = "problem"
            error = f"symbol {symbols} does not contain {EXPECTED_SYMBOL}"
        elif tick_error > 1e-4:
            status = "problem"
            error = f"tick error {tick_error}"
        elif neg:
            status = "problem"
            error = f"negative size rows {neg}"

        if prev_max is not None and prev_path is not None and pd.notna(row_min) and row_min <= prev_max:
            overlap_pairs.append((prev_path, path))
        prev_max = row_max if pd.notna(row_max) else prev_max
        prev_path = path

        audit_rows.append(
            {
                "filename": path.name,
                "file_date": file_date(path),
                "row_count": int(len(frame)),
                "min_ts_event": "" if row_min is pd.NaT else str(row_min),
                "max_ts_event": "" if row_max is pd.NaT else str(row_max),
                "total_volume": vol,
                "duplicate_extra_rows": dup_extra,
                "negative_size_rows": neg,
                "symbol_ok": bool(symbol_ok),
                "status": status,
                "error": error,
            }
        )
        parsed += 1
        total_trades += int(len(frame))
        total_volume += vol
        duplicate_extra += dup_extra
        negative_rows += neg
        if len(frame):
            global_min = row_min if global_min is None or row_min < global_min else global_min
            global_max = row_max if global_max is None or row_max > global_max else global_max

        positive = frame[frame["size"] > 0]
        if not positive.empty:
            grouped = positive.groupby(["session_date", "price_ticks"], sort=False)["size"].sum()
            for (session, ticks), size in grouped.items():
                volumes[session][int(ticks)] += int(size)
        for session, part in frame.groupby("session_date", sort=False):
            order = part.sort_values(["ts_event", "sequence"], kind="mergesort")
            first = order.iloc[0]
            last = order.iloc[-1]
            first_key = (int(first["ts_event"].value), int(first["sequence"]))
            last_key = (int(last["ts_event"].value), int(last["sequence"]))
            ids = {int(v) for v in order["instrument_id"].unique()}
            slot = meta.get(session)
            if slot is None:
                meta[session] = {
                    "n_trades": int(len(order)),
                    "first_key": first_key,
                    "last_key": last_key,
                    "first_ts": first["ts_event"],
                    "last_ts": last["ts_event"],
                    "first_ticks": int(first["price_ticks"]),
                    "last_ticks": int(last["price_ticks"]),
                    "instrument_ids": ids,
                    "symbol_ok": bool(symbol_ok),
                    "file_problem": status != "ok",
                }
            else:
                slot["n_trades"] += int(len(order))
                slot["instrument_ids"].update(ids)
                slot["symbol_ok"] = bool(slot["symbol_ok"] and symbol_ok)
                slot["file_problem"] = bool(slot["file_problem"] or status != "ok")
                if first_key < slot["first_key"]:
                    slot["first_key"] = first_key
                    slot["first_ts"] = first["ts_event"]
                    slot["first_ticks"] = int(first["price_ticks"])
                if last_key > slot["last_key"]:
                    slot["last_key"] = last_key
                    slot["last_ts"] = last["ts_event"]
                    slot["last_ticks"] = int(last["price_ticks"])
        print(f"[audit] {path.name} {status} rows={len(frame)} volume={vol}", flush=True)
        del frame

    for left, right in overlap_pairs:
        left_keys = _trade_keys(left)
        cross_file_duplicate_rows += _count_key_hits(right, left_keys)
        print(f"[audit] overlap {left.name}|{right.name}", flush=True)

    summary = {
        "files_found": len(files),
        "files_expected": EXPECTED_FILE_COUNT,
        "files_parsed": parsed,
        "files_failed": failed,
        "first_timestamp": "" if global_min is None else str(global_min),
        "last_timestamp": "" if global_max is None else str(global_max),
        "total_trades": total_trades,
        "total_volume": total_volume,
        "duplicate_extra_rows_within_files": duplicate_extra,
        "cross_file_timestamp_overlaps": [f"{left.name}|{right.name}" for left, right in overlap_pairs],
        "cross_file_duplicate_rows": cross_file_duplicate_rows,
        "negative_size_rows": negative_rows,
        "session_count": len(meta),
    }
    return pd.DataFrame(audit_rows), volumes, meta, summary


def calendar_gaps(files: list[Path]) -> list[str]:
    dates = sorted(date.fromisoformat(file_date(path)) for path in files)
    if not dates:
        return []
    missing = []
    cursor = dates[0]
    present = set(dates)
    while cursor <= dates[-1]:
        if cursor not in present:
            missing.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return missing


def session_table(volumes: dict[date, dict[int, int]], meta: dict[date, dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    vap_rows = []
    if not meta:
        return pd.DataFrame(), pd.DataFrame()
    for session in sorted(meta):
        info = meta[session]
        volmap = dict(volumes.get(session, {}))
        total = int(sum(volmap.values()))
        start, _end = session_bounds(session)
        close = session_close(session)
        slack = pd.Timedelta(minutes=COMPLETENESS_SLACK_MINUTES)
        complete = bool(info["first_ts"] <= start + slack and info["last_ts"] >= close - slack)
        ids = sorted(info["instrument_ids"])
        low_tick = min(volmap) if volmap else int(info["first_ticks"])
        high_tick = max(volmap) if volmap else int(info["first_ticks"])
        corrupt_range = bool(volmap) and (high_tick - low_tick) > MAX_RANGE_TICKS
        interior = 0
        if volmap and high_tick > low_tick and not corrupt_range:
            interior = int(high_tick - low_tick + 1 - len(volmap))
        rows.append(
            {
                "session_date": session.isoformat(),
                "total_volume": total,
                "n_trades": int(info["n_trades"]),
                "n_price_levels": int(len(volmap)),
                "n_zero_interior_ticks": interior,
                "profile_low_ticks": int(low_tick) if volmap else np.nan,
                "profile_high_ticks": int(high_tick) if volmap else np.nan,
                "first_trade_ts": info["first_ts"],
                "last_trade_ts": info["last_ts"],
                "first_ticks": int(info["first_ticks"]),
                "last_ticks": int(info["last_ticks"]),
                "instrument_id": ids[0] if len(ids) == 1 else -1,
                "n_instrument_ids": len(ids),
                "is_complete": complete,
                "symbol_ok": bool(info["symbol_ok"]),
                "file_problem": bool(info["file_problem"]),
                "corrupt_range": corrupt_range,
            }
        )
        running = 0
        prices = sorted(volmap) if corrupt_range else range(low_tick, high_tick + 1)
        for px in prices if volmap else []:
            vol = int(volmap.get(px, 0))
            running += vol
            vap_rows.append(
                {
                    "session_date": session.isoformat(),
                    "price": px * TICK_SIZE,
                    "price_ticks": px,
                    "volume": vol,
                    "volume_pct": (vol / total) if total else 0.0,
                    "cumulative_volume": running,
                    "cumulative_volume_pct": (running / total) if total else 0.0,
                }
            )
    sessions = mark_rolls(pd.DataFrame(rows))
    raw = pd.DataFrame(vap_rows)
    return sessions, raw


def print_audit(files: list[Path], audit: pd.DataFrame, summary: dict, sessions: pd.DataFrame) -> None:
    names = [path.name for path in files]
    print("", flush=True)
    print("=== DATASET AUDIT (before shape classification) ===", flush=True)
    print(f"files found: {summary['files_found']}", flush=True)
    print(f"files expected: {summary['files_expected']}", flush=True)
    print(f"files parsed: {summary['files_parsed']}", flush=True)
    print(f"first file: {names[0] if names else ''}", flush=True)
    print(f"last file: {names[-1] if names else ''}", flush=True)
    print(f"expected first: {EXPECTED_FIRST_FILE}", flush=True)
    print(f"expected last: {EXPECTED_LAST_FILE}", flush=True)
    print(f"first timestamp: {summary['first_timestamp']}", flush=True)
    print(f"last timestamp: {summary['last_timestamp']}", flush=True)
    print(f"total trades: {summary['total_trades']}", flush=True)
    print(f"total volume: {summary['total_volume']}", flush=True)
    print(f"failed files: {len(summary['files_failed'])}", flush=True)
    for item in summary["files_failed"]:
        print(f"  corrupt/failed: {item}", flush=True)
    problems = audit[audit["status"] != "ok"] if len(audit) else audit
    print(f"parsed files with problems: {len(problems)}", flush=True)
    print(f"duplicate extra rows within files: {summary['duplicate_extra_rows_within_files']}", flush=True)
    print(f"cross-file timestamp overlaps: {len(summary['cross_file_timestamp_overlaps'])}", flush=True)
    print(f"cross-file duplicate rows on overlap: {summary['cross_file_duplicate_rows']}", flush=True)
    print(f"negative size rows: {summary['negative_size_rows']}", flush=True)
    print(f"session count: {summary['session_count']}", flush=True)
    print(f"complete sessions: {int(sessions['is_complete'].sum()) if len(sessions) else 0}", flush=True)
    print(f"roll-transition sessions: {int(sessions['is_roll_transition'].sum()) if len(sessions) else 0}", flush=True)
    gaps = calendar_gaps(files)
    print(f"calendar days with no file between first and last filename date: {len(gaps)}", flush=True)
    print("=== END AUDIT ===", flush=True)
    print("", flush=True)


def main() -> None:
    check_session_assignment()
    RESULTS.mkdir(parents=True, exist_ok=True)
    files = list_trade_files()
    try:
        audit, volumes, meta, summary = accumulate(files)
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
    sessions, raw = session_table(volumes, meta)
    summary["calendar_gaps"] = calendar_gaps(files)
    summary["complete_sessions"] = int(sessions["is_complete"].sum()) if len(sessions) else 0
    summary["roll_transition_sessions"] = int(sessions["is_roll_transition"].sum()) if len(sessions) else 0
    summary["first_file"] = files[0].name if files else ""
    summary["last_file"] = files[-1].name if files else ""
    if names_mismatch(files):
        summary["filename_span_mismatch"] = True
    else:
        summary["filename_span_mismatch"] = False
    print_audit(files, audit, summary, sessions)
    audit.to_csv(RESULTS / "input_audit.csv", index=False)
    sessions.to_parquet(RESULTS / "session_meta.parquet", index=False)
    raw.to_parquet(RESULTS / "raw_price_volume.parquet", index=False)
    (RESULTS / "audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        f"[profile] sessions={len(sessions)} raw_rows={len(raw)} wrote {RESULTS}",
        flush=True,
    )


def names_mismatch(files: list[Path]) -> bool:
    if len(files) != EXPECTED_FILE_COUNT:
        return True
    if not files:
        return True
    return files[0].name != EXPECTED_FIRST_FILE or files[-1].name != EXPECTED_LAST_FILE


if __name__ == "__main__":
    main()
