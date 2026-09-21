"""Mechanism tables from normalized Parquet. Not a strategy search."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from research.mbo.clock import STEP_NS, future_snapshot_indices
from research.mbo.grid import HORIZON_SECONDS, SIDES, SIZE_BUCKETS
from research.mbo.sessions import IS_SESSIONS, rth_grid

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data" / "mbo_research" / "v2"


def store_views(con: duckdb.DuckDBPyConnection, store: Path = STORE) -> None:
    snaps = (store / "snapshots" / "date=*" / "snapshots.parquet").as_posix()
    trades = (store / "trades" / "date=*" / "trades.parquet").as_posix()
    features = (store / "features" / "date=*" / "features.parquet").as_posix()
    con.execute(f"CREATE OR REPLACE VIEW snapshots AS SELECT * FROM read_parquet('{snaps}', hive_partitioning=1)")
    con.execute(f"CREATE OR REPLACE VIEW trades AS SELECT * FROM read_parquet('{trades}', hive_partitioning=1)")
    con.execute(f"CREATE OR REPLACE VIEW features AS SELECT * FROM read_parquet('{features}', hive_partitioning=1)")


def query(sql: str, store: Path = STORE) -> pd.DataFrame:
    """Run SQL over the Parquet store. Views: snapshots, trades, features."""
    con = duckdb.connect()
    store_views(con, store)
    return con.execute(sql).df()


def _bucket_label(size: int) -> str | None:
    for label, lo, hi in SIZE_BUCKETS:
        if size >= lo and (hi is None or size < hi):
            return label
    return None


def _day_frame(date_str: str, store: Path) -> pd.DataFrame | None:
    trade_file = store / "trades" / f"date={date_str}" / "trades.parquet"
    snap_file = store / "snapshots" / f"date={date_str}" / "snapshots.parquet"
    if not trade_file.exists() or not snap_file.exists():
        return None
    trades = pd.read_parquet(trade_file, columns=["ts_event", "side", "size", "mid_px"])
    snaps = pd.read_parquet(snap_file, columns=["ts_ns", "mid_px"])
    if trades.empty or snaps.empty:
        return None
    open_ns, _close, n_bins = rth_grid(date_str)
    mids = snaps["mid_px"].to_numpy()
    rows = []
    ts = trades["ts_event"].to_numpy()
    side = trades["side"].to_numpy()
    size = trades["size"].to_numpy()
    entry = trades["mid_px"].to_numpy()
    labels = np.array([_bucket_label(int(v)) for v in size], dtype=object)
    for seconds in HORIZON_SECONDS:
        horizon_ns = seconds * STEP_NS
        idx = future_snapshot_indices(ts, horizon_ns, open_ns, STEP_NS, n_bins)
        valid = idx >= 0
        if not valid.any():
            continue
        fut_ts = open_ns + idx[valid].astype(np.int64) * STEP_NS
        if np.any(fut_ts <= ts[valid]):
            raise AssertionError("mechanism forward timestamp is not after the trade")
        ret = mids[idx[valid]] - entry[valid]
        part = pd.DataFrame(
            {
                "size_bucket": labels[valid],
                "side": side[valid],
                "horizon_s": seconds,
                "fwd_return": ret,
            }
        )
        part = part[part["size_bucket"].notna()]
        rows.append(part)
    if not rows:
        return None
    return pd.concat(rows, ignore_index=True)


def _summarize(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    grouped = frame.groupby(["size_bucket", "side", "horizon_s"], sort=False)
    stats = {key: group["fwd_return"].to_numpy() for key, group in grouped}
    for label, _lo, _hi in SIZE_BUCKETS:
        for side in SIDES:
            for seconds in HORIZON_SECONDS:
                if side == "ALL":
                    chunks = [stats[key] for key in stats if key[0] == label and key[2] == seconds]
                    values = np.concatenate(chunks) if chunks else np.array([])
                else:
                    values = stats.get((label, side, seconds), np.array([]))
                n = int(values.size)
                if n == 0:
                    records.append(
                        {
                            "size_bucket": label,
                            "side": side,
                            "horizon_s": seconds,
                            "n": 0,
                            "mean_fwd_return": np.nan,
                            "median": np.nan,
                            "hit_rate": np.nan,
                            "q10": np.nan,
                            "q90": np.nan,
                        }
                    )
                    continue
                if side == "B":
                    hits = values > 0
                elif side == "A":
                    hits = values < 0
                else:
                    hits = np.abs(values) >= 0
                    hits = np.concatenate(
                        [
                            stats.get((label, "B", seconds), np.array([])) > 0,
                            stats.get((label, "A", seconds), np.array([])) < 0,
                        ]
                    )
                    values_all = values
                    hit_rate = float(hits.mean()) if hits.size else np.nan
                    records.append(
                        {
                            "size_bucket": label,
                            "side": side,
                            "horizon_s": seconds,
                            "n": n,
                            "mean_fwd_return": float(np.mean(values_all)),
                            "median": float(np.median(values_all)),
                            "hit_rate": hit_rate,
                            "q10": float(np.quantile(values_all, 0.10)),
                            "q90": float(np.quantile(values_all, 0.90)),
                        }
                    )
                    continue
                records.append(
                    {
                        "size_bucket": label,
                        "side": side,
                        "horizon_s": seconds,
                        "n": n,
                        "mean_fwd_return": float(np.mean(values)),
                        "median": float(np.median(values)),
                        "hit_rate": float(np.mean(hits)),
                        "q10": float(np.quantile(values, 0.10)),
                        "q90": float(np.quantile(values, 0.90)),
                    }
                )
    out = pd.DataFrame(records)
    return out.sort_values(["size_bucket", "side", "horizon_s"], kind="mergesort").reset_index(drop=True)


def run_predefined_grid(dates: tuple[str, ...] | list[str] | None = None, store: Path = STORE) -> pd.DataFrame:
    """Full predefined grid. Every bucket is returned, including empty ones. None is selected."""
    chosen = tuple(dates) if dates is not None else IS_SESSIONS
    parts = []
    for date_str in chosen:
        day = _day_frame(date_str, store)
        if day is not None and not day.empty:
            parts.append(day)
    if not parts:
        return _summarize(pd.DataFrame(columns=["size_bucket", "side", "horizon_s", "fwd_return"]))
    return _summarize(pd.concat(parts, ignore_index=True))
