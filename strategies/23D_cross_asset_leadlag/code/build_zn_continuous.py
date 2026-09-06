"""
Build volume-front continuous ZN 1m parquet from Databento GLBX CSV.

Same rule as archive/legacy_scripts/build_continuous_data.py:
  per calendar date, pick symbol with max volume; drop spreads ('-' in symbol).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[2]  # strategies/<dossier>/code -> repo root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.paths import DATA, ROOT

# Prefer the dated dump; either folder is byte-identical ZN
CANDIDATES = (
    ROOT / "GLBX-20260906-WL8QFM334H" / "glbx-mdp3-20100606-20260905.ohlcv-1m.csv",
    ROOT / "GLBX-20260906-XMDRMALJEB" / "glbx-mdp3-20100606-20260905.ohlcv-1m.csv",
)
OUT = DATA / "zn_1m_continuous.parquet"
COLS = ["ts_event", "open", "high", "low", "close", "volume", "symbol"]


def main() -> None:
    src = next((p for p in CANDIDATES if p.exists()), None)
    if src is None:
        raise FileNotFoundError("ZN GLBX CSV not found under GLBX-20260906-*")
    print(f"Reading {src} …", flush=True)

    parts: list[pd.DataFrame] = []
    n_raw = 0
    for chunk in pd.read_csv(src, usecols=COLS, chunksize=500_000):
        chunk = chunk[~chunk["symbol"].astype(str).str.contains("-", regex=False)]
        # Keep outright ZN month codes (ZNH/M/U/Z + year digit(s))
        sym = chunk["symbol"].astype(str)
        chunk = chunk[sym.str.match(r"^ZN[HMUZ]\d+$", na=False)]
        n_raw += len(chunk)
        if len(chunk) == 0:
            continue
        chunk["ts_event"] = pd.to_datetime(chunk["ts_event"], utc=True)
        chunk["date"] = chunk["ts_event"].dt.date
        parts.append(chunk)
        if len(parts) % 10 == 0:
            print(f"  chunks={len(parts)} rows~{n_raw:,}", flush=True)

    if not parts:
        raise RuntimeError("No ZN outright rows after filter")
    all_df = pd.concat(parts, ignore_index=True)
    print(f"Total ZN outright rows: {len(all_df):,}", flush=True)

    daily_vol = all_df.groupby(["date", "symbol"], sort=False)["volume"].sum().reset_index()
    front = (
        daily_vol.sort_values(["date", "volume"], ascending=[True, False])
        .groupby("date", sort=False)
        .first()
        .reset_index()
    )
    front_df = all_df.merge(front[["date", "symbol"]], on=["date", "symbol"], how="inner")
    front_df = (
        front_df.drop_duplicates(subset=["ts_event"])
        .sort_values("ts_event")
        .reset_index(drop=True)
    )
    out = front_df[COLS]
    DATA.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(
        f"Continuous ZN rows={len(out):,} "
        f"{out['ts_event'].min()} -> {out['ts_event'].max()} -> {OUT}",
        flush=True,
    )


if __name__ == "__main__":
    main()
