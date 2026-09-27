"""One-day timing and size report. Does not process multi-year history."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from research.mbo.replay_day import STORE, replay_day
from research.mbo.sessions import IS_SESSIONS, rth_grid
from research.mbo.version import REPLAY_ENGINE_VERSION

ROOT = Path(__file__).resolve().parents[2]
H02_DIR = ROOT / "strategies" / "44_mbo_orderflow" / "results" / "sampled_features"
TRADING_DAYS = {"3m": 63, "6m": 126, "1y": 252, "5y": 1260, "9y": 2268}


def compare_flow(date_str: str) -> dict:
    new = pd.read_parquet(STORE / "snapshots" / f"date={date_str}" / "snapshots.parquet")
    old_path = H02_DIR / f"h02_samples_{date_str}.parquet"
    if not old_path.exists():
        return {"date": date_str, "compared": False}
    old = pd.read_parquet(old_path, columns=["ts_ns", "trade_b_1s", "trade_a_1s", "mid_px"])
    merged = new.merge(old, on="ts_ns", suffixes=("_new", "_old"))
    if merged.empty:
        return {"date": date_str, "compared": False, "reason": "no shared timestamps"}
    return {
        "date": date_str,
        "compared": True,
        "rows": int(len(merged)),
        "trade_b_match": float((merged["trade_b_1s_new"] == merged["trade_b_1s_old"]).mean()),
        "trade_a_match": float((merged["trade_a_1s_new"] == merged["trade_a_1s_old"]).mean()),
        "mid_max_abs": float((merged["mid_px_new"] - merged["mid_px_old"]).abs().max()),
        "grid_open_ns": int(rth_grid(date_str)[0]),
        "old_open_ns": int(old["ts_ns"].iloc[0]),
    }


def extrapolate(stats: dict) -> dict:
    seconds = float(stats["seconds"])
    out_bytes = int(stats["output_bytes"])
    raw_bytes = int(stats["raw_bytes"])
    rows = {
        "measured_day": {
            "events": stats["events"],
            "seconds": seconds,
            "events_per_sec": stats["events_per_sec"],
            "rss_peak_mb": stats["rss_peak_mb"],
            "snapshot_rows": stats["snapshot_rows"],
            "trade_rows": stats["trade_rows"],
            "output_mb": round(out_bytes / (1024 * 1024), 2),
            "raw_mb": round(raw_bytes / (1024 * 1024), 2),
            "compression_vs_raw": round(raw_bytes / out_bytes, 2) if out_bytes else None,
        }
    }
    for label, days in TRADING_DAYS.items():
        rows[label] = {
            "days": days,
            "hours": round(seconds * days / 3600, 1),
            "output_gb": round(out_bytes * days / (1024 ** 3), 2),
            "raw_gb": round(raw_bytes * days / (1024 ** 3), 2),
            "peak_ram_mb": stats["rss_peak_mb"],
        }
    rows["26_sessions_estimate"] = {
        "hours": round(seconds * len(IS_SESSIONS) / 3600, 2),
        "output_gb": round(out_bytes * len(IS_SESSIONS) / (1024 ** 3), 2),
    }
    return rows


def main() -> None:
    import sys

    date_str = sys.argv[1] if len(sys.argv) > 1 else "2026-07-08"
    stats = replay_day(date_str, force=False)
    if stats.get("skipped"):
        # Re-read the log line for this date if we skipped a completed file.
        log = STORE / "logs" / "replay.jsonl"
        found = None
        if log.exists():
            for line in log.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if row.get("date") == date_str and not row.get("error"):
                    found = row
        if found is None:
            stats = replay_day(date_str, force=True)
        else:
            stats = found
    report = {
        "version": REPLAY_ENGINE_VERSION,
        "timing": extrapolate(stats),
        "flow_check": compare_flow(date_str),
    }
    out = STORE / "logs" / f"benchmark_{date_str}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
