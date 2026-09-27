"""Build Globex session VA proxy from 1m bars (research scaffold).

Frozen: CHARTER_ENVIRONMENT_ATLAS_1M_VA_PROXY.md
NOT trade-tape VA. NO TRADE.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(ROOT / "volume_profile" / "code"))

from build_session_profiles import choose_poc, expand_value_area  # noqa: E402
from constants import BARS_PATH, RESULTS, TICK  # noqa: E402

NY = "America/New_York"
SESSION_START_MIN = 18 * 60
VA_PCT = 0.70
MIN_BARS = 500
TRADE_P1 = ROOT / "strategies" / "62_patrick_build_fields" / "results" / "p1_session_profiles.parquet"


def _as_date(v) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    return date.fromisoformat(str(v)[:10])


def load_session_bars() -> pd.DataFrame:
    df = pd.read_parquet(BARS_PATH, columns=["ts_event", "open", "high", "low", "close", "volume"])
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    out = pd.DataFrame(
        {
            "ts": ts,
            "high": df["high"].to_numpy(np.float64),
            "low": df["low"].to_numpy(np.float64),
            "close": df["close"].to_numpy(np.float64),
            "volume": df["volume"].to_numpy(np.float64),
        }
    )
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    cal = out["ts"].dt.date
    out["session_date"] = np.where(
        out["ny_min"].to_numpy() >= SESSION_START_MIN,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    out["session_date"] = out["session_date"].map(_as_date)
    return out


def accumulate_bar_volume(high: np.ndarray, low: np.ndarray, volume: np.ndarray) -> dict[int, int]:
    """Uniform volume across ticks in [low, high] per bar."""
    ok = np.isfinite(high) & np.isfinite(low) & np.isfinite(volume) & (volume > 0)
    if not ok.any():
        return {}
    high = high[ok]
    low = low[ok]
    volume = volume[ok]
    a = np.rint(low / TICK).astype(np.int64)
    b = np.rint(high / TICK).astype(np.int64)
    swap = b < a
    a2 = np.where(swap, b, a)
    b2 = np.where(swap, a, b)
    t0 = int(a2.min())
    t1 = int(b2.max())
    width = t1 - t0 + 1
    if width <= 0 or width > 500_000:
        return {}
    acc = np.zeros(width, dtype=np.float64)
    for i in range(len(volume)):
        lo = int(a2[i]) - t0
        hi = int(b2[i]) - t0
        n = hi - lo + 1
        acc[lo : hi + 1] += float(volume[i]) / n
    out: dict[int, int] = {}
    nz = np.flatnonzero(acc > 0)
    for j in nz:
        out[t0 + int(j)] = max(1, int(round(acc[j])))
    return out


def profile_one(session: date, g: pd.DataFrame) -> dict | None:
    n_bars = len(g)
    total_vol = float(g["volume"].sum())
    if n_bars < MIN_BARS or total_vol <= 0:
        return {
            "session_date": session,
            "n_bars": n_bars,
            "total_volume": total_vol,
            "poc": np.nan,
            "vah": np.nan,
            "val": np.nan,
            "value_area_width": np.nan,
            "is_complete": False,
            "source": "1m_bar_proxy_v1",
        }
    vols = accumulate_bar_volume(
        g["high"].to_numpy(),
        g["low"].to_numpy(),
        g["volume"].to_numpy(),
    )
    if not vols:
        return {
            "session_date": session,
            "n_bars": n_bars,
            "total_volume": total_vol,
            "poc": np.nan,
            "vah": np.nan,
            "val": np.nan,
            "value_area_width": np.nan,
            "is_complete": False,
            "source": "1m_bar_proxy_v1",
        }
    poc_t = choose_poc(vols)
    val_t, vah_t, _inc = expand_value_area(vols, poc_t, VA_PCT)
    return {
        "session_date": session,
        "n_bars": n_bars,
        "total_volume": total_vol,
        "poc": poc_t * TICK,
        "vah": vah_t * TICK,
        "val": val_t * TICK,
        "value_area_width": (vah_t - val_t) * TICK,
        "is_complete": True,
        "source": "1m_bar_proxy_v1",
    }


def overlap_audit(proxy: pd.DataFrame) -> dict:
    if not TRADE_P1.exists():
        return {"available": False}
    trade = pd.read_parquet(TRADE_P1)
    trade["session_date"] = trade["session_date"].map(_as_date)
    trade = trade.loc[trade["is_complete"], ["session_date", "poc", "vah", "val"]].copy()
    p = proxy.loc[proxy["is_complete"], ["session_date", "poc", "vah", "val"]].copy()
    m = trade.merge(p, on="session_date", suffixes=("_trade", "_proxy"))
    if m.empty:
        return {"available": True, "n_overlap": 0}
    # location agreement at session close proxy vs trade VA using proxy close ≈ trade mid:
    # compare whether a common reference (trade poc) sits in same L bucket vs each VA
    def loc(px, vah, val):
        if px > vah:
            return "ABOVE"
        if px < val:
            return "BELOW"
        return "INSIDE"

    # use trade POC as a shared test price
    same_bucket = []
    for _, r in m.iterrows():
        px = float(r["poc_trade"])
        lt = loc(px, float(r["vah_trade"]), float(r["val_trade"]))
        # trade POC is always INSIDE trade VA by construction — use session mid instead
        mid = 0.5 * (float(r["vah_trade"]) + float(r["val_trade"]))
        lt = loc(mid, float(r["vah_trade"]), float(r["val_trade"]))
        lp = loc(mid, float(r["vah_proxy"]), float(r["val_proxy"]))
        same_bucket.append(lt == lp)
    return {
        "available": True,
        "n_overlap": int(len(m)),
        "med_abs_poc_diff": float((m["poc_proxy"] - m["poc_trade"]).abs().median()),
        "med_abs_vah_diff": float((m["vah_proxy"] - m["vah_trade"]).abs().median()),
        "med_abs_val_diff": float((m["val_proxy"] - m["val_trade"]).abs().median()),
        "midprice_L_agree_rate": float(np.mean(same_bucket)),
        "note": (
            "Absolute level diffs vs trade P1 are expected: 1m series is continuous/"
            "back-adjusted while trade P1 uses contract prints. Atlas uses proxy+bars "
            "consistently; do not treat abs POC gap as proxy failure."
        ),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("loading 1m bars...", flush=True)
    bars = load_session_bars()
    print(f"  bars={len(bars)} sessions={bars.session_date.nunique()}", flush=True)

    rows = []
    for i, (sess, g) in enumerate(bars.groupby("session_date", sort=True)):
        rows.append(profile_one(_as_date(sess), g))
        if (i + 1) % 250 == 0:
            print(f"  profiled {i+1} sessions", flush=True)

    out = pd.DataFrame(rows)
    path = RESULTS / "p1_1m_va_proxy.parquet"
    out.to_parquet(path, index=False)

    complete = out.loc[out["is_complete"]]
    summary = {
        "source": "1m_bar_proxy_v1",
        "n_sessions": int(len(out)),
        "n_complete": int(len(complete)),
        "session_min": str(out["session_date"].min()),
        "session_max": str(out["session_date"].max()),
        "med_va_width": float(complete["value_area_width"].median()) if len(complete) else None,
        "overlap_vs_trade_p1": overlap_audit(out),
    }
    (RESULTS / "p1_1m_va_proxy_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str), flush=True)
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
