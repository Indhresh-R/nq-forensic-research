"""Feature rows from normalized snapshots. Does not open raw MBO."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from research.mbo.clock import STEP_NS
from research.mbo.grid import HORIZON_SECONDS
from research.mbo.sessions import IS_SESSIONS
from research.mbo.version import REPLAY_ENGINE_VERSION

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data" / "mbo_research" / "v2"


def snapshot_path(date_str: str, store: Path = STORE) -> Path:
    return store / "snapshots" / f"date={date_str}" / "snapshots.parquet"


def feature_path(date_str: str, store: Path = STORE) -> Path:
    return store / "features" / f"date={date_str}" / "features.parquet"


def build_features(snapshots: pd.DataFrame) -> pd.DataFrame:
    """Add causal rolling flow and forward mids. One session, already time-ordered."""
    out = snapshots.copy()
    if "replay_version" in out.columns and not (out["replay_version"] == REPLAY_ENGINE_VERSION).all():
        raise ValueError("snapshot replay_version does not match this engine")
    out["cvd_1s"] = out["trade_b_1s"].astype("int64") - out["trade_a_1s"].astype("int64")
    out["cvd_5s"] = out["cvd_1s"].rolling(5, min_periods=5).sum()
    out["cvd_15s"] = out["cvd_1s"].rolling(15, min_periods=15).sum()
    out["cvd_60s"] = out["cvd_1s"].rolling(60, min_periods=60).sum()
    out["add_net_1s"] = out["add_b_1s"].astype("int64") - out["add_a_1s"].astype("int64")
    out["cancel_net_1s"] = out["cancel_b_1s"].astype("int64") - out["cancel_a_1s"].astype("int64")
    for seconds in HORIZON_SECONDS:
        future_ts = out["ts_ns"].shift(-seconds)
        out[f"fwd_ret_{seconds}s"] = out["mid_px"].shift(-seconds) - out["mid_px"]
        known = out[f"fwd_ret_{seconds}s"].notna()
        if known.any() and not bool((future_ts[known] > out.loc[known, "ts_ns"]).all()):
            raise AssertionError(f"fwd_ret_{seconds}s used a timestamp at or before the observation")
        if known.any():
            step = int((future_ts[known] - out.loc[known, "ts_ns"]).min())
            if step < seconds * STEP_NS:
                raise AssertionError(f"fwd_ret_{seconds}s horizon is shorter than {seconds}s")
    return out


def write_features(date_str: str, store: Path = STORE, force: bool = False) -> Path:
    out = feature_path(date_str, store)
    if out.exists() and not force:
        return out
    src = snapshot_path(date_str, store)
    if not src.exists():
        raise FileNotFoundError(src)
    frame = build_features(pd.read_parquet(src))
    out.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    meta = dict(table.schema.metadata or {})
    meta[b"replay_version"] = REPLAY_ENGINE_VERSION.encode()
    pq.write_table(table.replace_schema_metadata(meta), out, compression="zstd")
    return out


def write_all(store: Path = STORE, force: bool = False) -> None:
    for date_str in IS_SESSIONS:
        if snapshot_path(date_str, store).exists():
            path = write_features(date_str, store, force=force)
            print(f"[{date_str}] features -> {path}", flush=True)


if __name__ == "__main__":
    import sys

    write_all(force="--force" in sys.argv)
