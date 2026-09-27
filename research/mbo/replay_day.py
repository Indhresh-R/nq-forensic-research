"""Write one trading day of normalized Parquet, then release it."""

from __future__ import annotations

import argparse
import json
import time
import traceback
from pathlib import Path

import databento as db
import pandas as pd
import psutil
import pyarrow as pa
import pyarrow.parquet as pq

from research.mbo.engine import ReplaySession
from research.mbo.sessions import IS_SESSIONS, rth_grid
from research.mbo.version import REPLAY_ENGINE_VERSION

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "mbo_full_state_50"
STORE = ROOT / "data" / "mbo_research" / "v2"


def snapshot_path(date_str: str, store: Path = STORE) -> Path:
    return store / "snapshots" / f"date={date_str}" / "snapshots.parquet"


def trade_path(date_str: str, store: Path = STORE) -> Path:
    return store / "trades" / f"date={date_str}" / "trades.parquet"


def _write(frame: pd.DataFrame, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    meta = dict(table.schema.metadata or {})
    meta[b"replay_version"] = REPLAY_ENGINE_VERSION.encode()
    pq.write_table(table.replace_schema_metadata(meta), path, compression="zstd")
    return path.stat().st_size


def replay_day(date_str: str, store: Path = STORE, force: bool = False) -> dict:
    """Replay one raw file. Does not retain the previous day."""
    out_snap = snapshot_path(date_str, store)
    out_trd = trade_path(date_str, store)
    if out_snap.exists() and out_trd.exists() and not force:
        return {"date": date_str, "skipped": True, "snapshot_bytes": out_snap.stat().st_size, "trade_bytes": out_trd.stat().st_size}

    src = DATA_DIR / f"mbo_{date_str}.dbn.zst"
    if not src.exists():
        raise FileNotFoundError(src)

    open_ns, close_ns, _n = rth_grid(date_str)
    session = ReplaySession(date_str, open_ns, close_ns)
    proc = psutil.Process()
    rss_peak = proc.memory_info().rss
    t0 = time.perf_counter()
    store_db = db.DBNStore.from_file(src)
    seen = 0
    for record in store_db:
        if not isinstance(record, db.MBOMsg):
            continue
        session.consume((record,))
        seen += 1
        if seen % 1_000_000 == 0:
            rss_peak = max(rss_peak, proc.memory_info().rss)
        if session.stopped:
            break
    session.finish()
    rss_peak = max(rss_peak, proc.memory_info().rss)
    elapsed = time.perf_counter() - t0

    snaps = pd.DataFrame(session.snapshots)
    trades = pd.DataFrame(session.trades)
    if not snaps.empty and (snaps["flow_max_ts_ns"] > snaps["ts_ns"]).any():
        raise AssertionError(f"{date_str} wrote a snapshot with future flow")
    snap_bytes = _write(snaps, out_snap)
    trade_bytes = _write(trades, out_trd) if not trades.empty else _write(pd.DataFrame(columns=["date", "ts_event"]), out_trd)
    raw_bytes = src.stat().st_size
    stats = {
        "date": date_str,
        "skipped": False,
        "replay_version": REPLAY_ENGINE_VERSION,
        "events": int(session.events_seen),
        "seconds": round(elapsed, 3),
        "events_per_sec": round(session.events_seen / elapsed, 1) if elapsed else 0,
        "rss_peak_mb": round(rss_peak / (1024 * 1024), 1),
        "snapshot_rows": int(len(snaps)),
        "trade_rows": int(len(trades)),
        "snapshot_bytes": snap_bytes,
        "trade_bytes": trade_bytes,
        "raw_bytes": raw_bytes,
        "output_bytes": snap_bytes + trade_bytes,
        "error": None,
    }
    log_path = store / "logs" / "replay.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(stats) + "\n")
    print(
        f"[{date_str}] events={stats['events']:,} trades={stats['trade_rows']:,} "
        f"time={stats['seconds']}s rss={stats['rss_peak_mb']}MB",
        flush=True,
    )
    del snaps, trades, session
    return stats


def replay_dates(dates: tuple[str, ...] | list[str], store: Path = STORE, force: bool = False) -> list[dict]:
    results = []
    for date_str in dates:
        try:
            results.append(replay_day(date_str, store, force=force))
        except Exception as exc:
            err = {"date": date_str, "error": f"{exc.__class__.__name__}: {exc}", "trace": traceback.format_exc()}
            results.append(err)
            print(f"[{date_str}] ERROR {exc}", flush=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay one NQ MBO day into normalized Parquet")
    parser.add_argument("--date", default="")
    parser.add_argument("--all-is", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.all_is:
        replay_dates(IS_SESSIONS, force=args.force)
    elif args.date:
        replay_day(args.date, force=args.force)
    else:
        parser.error("pass --date YYYY-MM-DD or --all-is")


if __name__ == "__main__":
    main()
