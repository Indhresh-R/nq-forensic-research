"""Shared ES/NQ synced 1m panel for Strategy 28."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common.nq_session import NY_OPEN, load_es, load_nq
from common.paths import ROOT
from common.splits import IS_YEARS, OOS_YEARS, VAL_YEARS

ART = ROOT / "artifacts" / "28_es_nq_open_leadlag"
RTH_END = 16 * 60
GAP_MAX_MIN = 1.01

WINDOWS: dict[str, tuple[int, int]] = {
    "OPEN5": (NY_OPEN, NY_OPEN + 5),
    "OPEN15": (NY_OPEN, NY_OPEN + 15),
    "OPEN30": (NY_OPEN, NY_OPEN + 30),
    "MID": (11 * 60, 14 * 60),
    "RTH": (NY_OPEN, RTH_END),
}

DISC_YEARS = IS_YEARS


def split_of(year: int) -> str:
    if year in DISC_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def _attach_rets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values("ts").reset_index(drop=True).copy()
    close = out["close"].to_numpy(np.float64)
    prev = np.roll(close, 1)
    prev[0] = np.nan
    dt_min = out["ts"].diff().dt.total_seconds().to_numpy() / 60.0
    ret = close / prev - 1.0
    ret[0] = np.nan
    bad_gap = ~np.isfinite(dt_min) | (dt_min > GAP_MAX_MIN) | (dt_min <= 0)
    ret[bad_gap] = np.nan
    out["ret_1m"] = ret

    sess = out["session_date"].to_numpy()
    sum5 = np.full(len(out), np.nan, dtype=np.float64)
    buf: list[float] = []
    prev_s = object()
    for i in range(len(out)):
        s = sess[i]
        if s != prev_s:
            buf = []
            prev_s = s
        r = ret[i]
        if np.isfinite(r):
            buf.append(float(r))
            if len(buf) > 5:
                buf = buf[-5:]
            if len(buf) == 5:
                sum5[i] = float(np.sum(buf))
        else:
            buf = []
    out["ret_sum5"] = sum5
    return out


def _book_frame(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    x = _attach_rets(df)
    return pd.DataFrame(
        {
            "session_date": x["session_date"].to_numpy(),
            "ny_min": x["ny_min"].to_numpy(np.int16),
            "year": x["year"].to_numpy(np.int16),
            f"{prefix}_ts": x["ts"].to_numpy(),
            f"{prefix}_open": x["open"].to_numpy(np.float64),
            f"{prefix}_high": x["high"].to_numpy(np.float64),
            f"{prefix}_low": x["low"].to_numpy(np.float64),
            f"{prefix}_close": x["close"].to_numpy(np.float64),
            f"{prefix}_volume": x["volume"].to_numpy(np.float64),
            f"{prefix}_ret_1m": x["ret_1m"].to_numpy(np.float64),
            f"{prefix}_ret_sum5": x["ret_sum5"].to_numpy(np.float64),
        }
    )


def build_synced_panel() -> pd.DataFrame:
    es = _book_frame(load_es(), "es")
    nq = _book_frame(load_nq(), "nq")
    panel = es.merge(nq, on=["session_date", "ny_min"], how="inner", suffixes=("", "_nqdup"))
    # year: prefer ES
    if "year_nqdup" in panel.columns:
        panel = panel.drop(columns=["year_nqdup"])
    panel["year"] = panel["year"].astype(np.int16)
    panel["split"] = [split_of(int(y)) for y in panel["year"].to_numpy()]
    panel["ts"] = panel["es_ts"]
    panel = panel.sort_values(["session_date", "ny_min"]).reset_index(drop=True)
    return panel


def window_mask(ny_min: np.ndarray, name: str) -> np.ndarray:
    lo, hi = WINDOWS[name]
    return (ny_min >= lo) & (ny_min < hi)


def forward_close_ret(close: np.ndarray, session: np.ndarray, h: int) -> np.ndarray:
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    if h <= 0 or h >= n:
        return out
    fut = close[h:]
    base = close[:-h]
    same = session[h:] == session[:-h]
    r = fut / base - 1.0
    bad = (~same) | (~np.isfinite(base)) | (base <= 0) | (~np.isfinite(fut))
    r[bad] = np.nan
    out[:-h] = r
    return out
