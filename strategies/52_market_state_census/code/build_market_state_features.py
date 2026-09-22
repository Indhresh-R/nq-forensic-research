"""
Build causal 1-minute market-state features for Strategy 52.

No outcomes. No forward returns. Rolling windows are backward-looking only.
Uses contiguous-segment numpy rolling (fast on ~5M bars).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from common.nq_session import load_nq
from common.paths import DATA

from constants import (
    ANALYSIS_END_NY,
    ANALYSIS_START_NY,
    ATR_WINDOW,
    ER_WINDOWS,
    GAP_TOLERANCE_MINUTES,
    PRIMARY_ER_WINDOW,
    PRIMARY_RANGE_WINDOW,
    PRIMARY_RV_WINDOW,
    RANGE_WINDOWS,
    RESULTS,
    RVOL_HIST_SESSIONS,
    RVOL_WINDOW,
    RV_WINDOWS,
    TZ,
)


def _segment_ids(ts: pd.Series) -> np.ndarray:
    t = pd.to_datetime(ts)
    n = len(t)
    if n == 0:
        return np.array([], dtype=np.int64)
    delta_min = np.empty(n, dtype=np.float64)
    delta_min[0] = 0.0
    if n > 1:
        d = t.iloc[1:].to_numpy(dtype="datetime64[ns]") - t.iloc[:-1].to_numpy(
            dtype="datetime64[ns]"
        )
        delta_min[1:] = d.astype("timedelta64[ns]").astype(np.float64) / 60e9
    breaks = delta_min > GAP_TOLERANCE_MINUTES
    breaks[0] = True
    return np.cumsum(breaks.astype(np.int64)) - 1


def _segment_slices(seg: np.ndarray) -> list[tuple[int, int]]:
    """Return [start, end) slices for each contiguous segment (seg must be sorted runs)."""
    n = len(seg)
    if n == 0:
        return []
    change = np.empty(n, dtype=bool)
    change[0] = True
    change[1:] = seg[1:] != seg[:-1]
    starts = np.flatnonzero(change)
    ends = np.concatenate([starts[1:], [n]])
    return list(zip(starts.tolist(), ends.tolist()))


def _roll_sum(x: np.ndarray, window: int) -> np.ndarray:
    """Causal rolling sum; NaN until `window` finite values in window."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < window:
        return out
    finite = np.isfinite(x)
    x0 = np.where(finite, x, 0.0)
    c = np.cumsum(x0)
    cf = np.cumsum(finite.astype(np.int64))
    s = c.copy()
    s[window:] = c[window:] - c[:-window]
    f = cf.copy()
    f[window:] = cf[window:] - cf[:-window]
    # first window-1 remain nan
    valid = np.arange(n) >= (window - 1)
    ok = valid & (f >= window)
    out[ok] = s[ok]
    return out


def _roll_mean(x: np.ndarray, window: int) -> np.ndarray:
    s = _roll_sum(x, window)
    return s / float(window)


def _roll_max(x: np.ndarray, window: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < window:
        return out
    # stride tricks when possible; fallback deque
    from collections import deque as dq

    q: dq[int] = dq()
    for i in range(n):
        while q and x[q[-1]] <= x[i]:
            q.pop()
        q.append(i)
        start = i - window + 1
        if start < 0:
            continue
        while q[0] < start:
            q.popleft()
        out[i] = x[q[0]]
    return out


def _roll_min(x: np.ndarray, window: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < window:
        return out
    from collections import deque as dq

    q: dq[int] = dq()
    for i in range(n):
        while q and x[q[-1]] >= x[i]:
            q.pop()
        q.append(i)
        start = i - window + 1
        if start < 0:
            continue
        while q[0] < start:
            q.popleft()
        out[i] = x[q[0]]
    return out


def _apply_per_segment(
    values: np.ndarray, slices: list[tuple[int, int]], fn, *args
) -> np.ndarray:
    out = np.full(len(values), np.nan, dtype=np.float64)
    for a, b in slices:
        if b <= a:
            continue
        out[a:b] = fn(values[a:b], *args)
    return out


def _efficiency_ratio(close: np.ndarray, slices: list[tuple[int, int]], window: int) -> np.ndarray:
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    for a, b in slices:
        c = close[a:b]
        m = len(c)
        if m <= window:
            continue
        abs_d = np.empty(m, dtype=np.float64)
        abs_d[0] = np.nan
        abs_d[1:] = np.abs(c[1:] - c[:-1])
        path = _roll_sum(abs_d, window)
        net = np.full(m, np.nan)
        net[window:] = np.abs(c[window:] - c[:-window])
        with np.errstate(invalid="ignore", divide="ignore"):
            er = net / path
        er[~np.isfinite(er)] = np.nan
        er[path <= 0] = np.nan
        out[a:b] = er
    return out


def _realized_vol(close: np.ndarray, slices: list[tuple[int, int]], window: int) -> np.ndarray:
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    for a, b in slices:
        c = close[a:b]
        m = len(c)
        if m <= window:
            continue
        rets = np.full(m, np.nan, dtype=np.float64)
        with np.errstate(invalid="ignore", divide="ignore"):
            rets[1:] = (c[1:] - c[:-1]) / c[:-1]
        ssq = _roll_sum(rets * rets, window)
        out[a:b] = np.sqrt(ssq)
    return out


def _true_range(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, slices: list[tuple[int, int]]
) -> np.ndarray:
    n = len(close)
    tr = np.empty(n, dtype=np.float64)
    for a, b in slices:
        h = high[a:b]
        l = low[a:b]
        c = close[a:b]
        prev = np.empty_like(c)
        prev[0] = c[0]
        prev[1:] = c[:-1]
        tr[a:b] = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    return tr


def _relative_volume(
    volume: np.ndarray,
    ny_min: np.ndarray,
    session_ids: np.ndarray,
    slices: list[tuple[int, int]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    RVOL = rolling volume / trailing TOD expected rolling volume.

    session_ids: dense 0..S-1 in chronological order (same order as appearance).
    Expected uses only prior sessions at the same ny_min.
    """
    vol_roll = _apply_per_segment(volume.astype(np.float64), slices, _roll_sum, RVOL_WINDOW)
    n = len(volume)
    expected = np.full(n, np.nan, dtype=np.float64)
    rvol = np.full(n, np.nan, dtype=np.float64)

    # Process sessions in order 0..S-1
    n_sess = int(session_ids.max()) + 1 if len(session_ids) else 0
    # For each session, gather indices via change points on session_ids
    change = np.empty(n, dtype=bool)
    if n:
        change[0] = True
        change[1:] = session_ids[1:] != session_ids[:-1]
    starts = np.flatnonzero(change)
    ends = np.concatenate([starts[1:], [n]]) if n else np.array([], dtype=np.int64)

    history: dict[int, deque] = defaultdict(lambda: deque(maxlen=RVOL_HIST_SESSIONS))
    hist_sum: dict[int, float] = defaultdict(float)

    for s0, s1 in zip(starts.tolist(), ends.tolist()):
        mins = ny_min[s0:s1]
        rolls = vol_roll[s0:s1]
        # classify using history BEFORE updating
        for j in range(s1 - s0):
            m = int(mins[j])
            hist = history[m]
            if len(hist) > 0:
                mu = hist_sum[m] / len(hist)
                expected[s0 + j] = mu
                r = rolls[j]
                if np.isfinite(r) and mu > 0:
                    rvol[s0 + j] = r / mu
        # update history after session
        for j in range(s1 - s0):
            r = rolls[j]
            if not np.isfinite(r):
                continue
            m = int(mins[j])
            hist = history[m]
            if len(hist) == hist.maxlen:
                hist_sum[m] -= hist[0]
            hist.append(float(r))
            hist_sum[m] += float(r)

    return vol_roll, expected, rvol


def build_features(df_1m: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    if df_1m is None:
        df_1m = load_nq()
    print("  sort…", flush=True)
    x = df_1m.sort_values("ts").reset_index(drop=True).copy()
    print("  segments…", flush=True)
    seg = _segment_ids(x["ts"])
    slices = _segment_slices(seg)
    print(f"  n_segments={len(slices)}", flush=True)

    close = x["close"].to_numpy(np.float64)
    high = x["high"].to_numpy(np.float64)
    low = x["low"].to_numpy(np.float64)
    volume = x["volume"].to_numpy(np.float64)
    ny_min = x["ny_min"].to_numpy(np.int16)
    session_date = x["session_date"].to_numpy()

    # dense chronological session ids
    _, session_ids = np.unique(session_date, return_inverse=True)

    feats: dict[str, np.ndarray] = {"segment_id": seg.astype(np.int64)}

    for w in ER_WINDOWS:
        print(f"  ER_{w}…", flush=True)
        feats[f"er_{w}"] = _efficiency_ratio(close, slices, w)

    for w in RV_WINDOWS:
        print(f"  RV_{w}…", flush=True)
        feats[f"rv_{w}"] = _realized_vol(close, slices, w)

    print(f"  ATR_{ATR_WINDOW}…", flush=True)
    tr = _true_range(high, low, close, slices)
    atr = _apply_per_segment(tr, slices, _roll_mean, ATR_WINDOW)
    feats[f"atr_{ATR_WINDOW}"] = atr
    feats["tr"] = tr

    for w in RANGE_WINDOWS:
        print(f"  range_{w}…", flush=True)
        rh = _apply_per_segment(high, slices, _roll_max, w)
        rl = _apply_per_segment(low, slices, _roll_min, w)
        rng = rh - rl
        feats[f"range_{w}"] = rng
        with np.errstate(invalid="ignore", divide="ignore"):
            feats[f"range_norm_{w}"] = rng / np.where(atr > 0, atr, np.nan)

    print("  RVOL…", flush=True)
    vol_roll, vol_exp, rvol = _relative_volume(volume, ny_min, session_ids, slices)
    feats[f"vol_roll_{RVOL_WINDOW}"] = vol_roll
    feats["vol_expected_tod"] = vol_exp
    feats["rvol"] = rvol

    out = x
    for k, v in feats.items():
        out[k] = v

    out["session_year"] = pd.to_datetime(pd.Series(out["session_date"])).dt.year.astype(
        np.int16
    )

    in_window = (out["ny_min"] >= ANALYSIS_START_NY) & (out["ny_min"] < ANALYSIS_END_NY)
    out["in_analysis_window"] = in_window

    primary_ok = (
        in_window
        & np.isfinite(out[f"er_{PRIMARY_ER_WINDOW}"])
        & np.isfinite(out[f"rv_{PRIMARY_RV_WINDOW}"])
        & np.isfinite(out["rvol"])
        & np.isfinite(out[f"range_norm_{PRIMARY_RANGE_WINDOW}"])
        & np.isfinite(out[f"atr_{ATR_WINDOW}"])
    )
    out["census_eligible"] = primary_ok

    data_path = DATA / "nq_1m_continuous.parquet"
    meta = {
        "dataset_path": str(data_path.resolve()) if data_path.exists() else "via load_nq",
        "timezone": TZ,
        "session_roll": "18:00 ET",
        "analysis_window": "09:30–16:00 ET (end exclusive)",
        "n_1m_bars": int(len(out)),
        "n_sessions": int(pd.Series(session_date).nunique()),
        "n_segments": int(len(slices)),
        "ts_min": str(out["ts"].iloc[0]),
        "ts_max": str(out["ts"].iloc[-1]),
        "n_analysis_window": int(in_window.sum()),
        "n_census_eligible": int(primary_ok.sum()),
        "windows": {
            "er": list(ER_WINDOWS),
            "rv": list(RV_WINDOWS),
            "atr": ATR_WINDOW,
            "range": list(RANGE_WINDOWS),
            "rvol": RVOL_WINDOW,
            "rvol_hist_sessions": RVOL_HIST_SESSIONS,
            "primary_er": PRIMARY_ER_WINDOW,
            "primary_rv": PRIMARY_RV_WINDOW,
            "primary_range": PRIMARY_RANGE_WINDOW,
        },
        "gap_tolerance_minutes": GAP_TOLERANCE_MINUTES,
        "lookahead": False,
        "outcomes": False,
    }
    return out, meta


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading NQ 1m…", flush=True)
    df = load_nq()
    print(f"rows={len(df):,}", flush=True)
    print("Building features…", flush=True)
    feats, meta = build_features(df)

    keep_cols = [
        "ts",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "year",
        "dow",
        "ny_min",
        "session_date",
        "session_year",
        "segment_id",
        "in_analysis_window",
        "census_eligible",
        "er_30",
        "er_60",
        "er_120",
        "rv_30",
        "rv_60",
        f"atr_{ATR_WINDOW}",
        "tr",
        "range_30",
        "range_60",
        "range_norm_30",
        "range_norm_60",
        f"vol_roll_{RVOL_WINDOW}",
        "vol_expected_tod",
        "rvol",
    ]
    aw = feats.loc[feats["in_analysis_window"], keep_cols].reset_index(drop=True)
    path = RESULTS / "market_state_features.parquet"
    print(f"Writing {path}…", flush=True)
    aw.to_parquet(path, index=False)
    (RESULTS / "feature_meta.json").write_text(
        json.dumps(meta, indent=2, default=str), encoding="utf-8"
    )
    print(f"Wrote {path} rows={len(aw):,} eligible={int(aw['census_eligible'].sum()):,}", flush=True)


if __name__ == "__main__":
    main()
