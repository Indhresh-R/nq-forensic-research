"""
23A — Pull CFTC TFF (Futures Only) Nasdaq-100 Consolidated, cache parquet,
build lagged extreme-positioning features.

Causal lag (frozen):
  report_date = Tuesday snapshot
  release     = following Friday 15:30 America/New_York
  usable from = next trading session after that release
                (typically Sunday 18:00 ET → session_date = Monday)

Credentials (optional; public endpoint works without, token raises rate limits):
  CFTC_APP_TOKEN / CFTC_APP_SECRET from environment or repo-root .env
  Never hardcode secrets in this file.
"""
from __future__ import annotations

import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import art

warnings.filterwarnings("ignore", category=FutureWarning)

SODA_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
# Pre-registered market: covers ~2010–2026 (matches NQ continuous sample)
MARKET_EXACT = "NASDAQ-100 Consolidated - CHICAGO MERCANTILE EXCHANGE"
FUTONLY = "FutOnly"
ROLL_WEEKS = 104  # trailing 2y
DECILE_LO = 10.0
DECILE_HI = 90.0
RELEASE_TOD_MIN = 15 * 60 + 30  # Friday 15:30 ET
PAGE = 2000


def _load_dotenv() -> None:
    env_path = _ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _headers() -> dict[str, str]:
    return {"Accept": "application/json"}


def _auth() -> tuple[str, str] | None:
    """Socrata HTTP Basic (app token as username). X-App-Token header 403s on this portal."""
    _load_dotenv()
    tok = os.environ.get("CFTC_APP_TOKEN", "").strip()
    sec = os.environ.get("CFTC_APP_SECRET", "").strip()
    if tok:
        return (tok, sec)
    return None


def fetch_tff_raw() -> pd.DataFrame:
    """Paginated SODA pull; writes raw cache parquet."""
    cache = art("nq_cot_tff_raw.parquet")
    where = (
        f"market_and_exchange_names='{MARKET_EXACT}' "
        f"AND futonly_or_combined='{FUTONLY}'"
    )
    rows: list[dict[str, Any]] = []
    offset = 0
    headers = _headers()
    auth = _auth()
    print(f"Fetching TFF: {MARKET_EXACT} FutOnly …", flush=True)
    while True:
        params = {
            "$where": where,
            "$order": "report_date_as_yyyy_mm_dd ASC",
            "$limit": str(PAGE),
            "$offset": str(offset),
        }
        r = requests.get(
            SODA_URL, params=params, headers=headers, auth=auth, timeout=120
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        print(f"  offset={offset} +{len(batch)} total={len(rows)}", flush=True)
        if len(batch) < PAGE:
            break
        offset += PAGE
        time.sleep(0.25)
    if not rows:
        raise RuntimeError("CFTC TFF pull returned 0 rows")
    raw = pd.DataFrame(rows)
    raw.to_parquet(cache, index=False)
    print(f"Raw rows={len(raw)} -> {cache}", flush=True)
    return raw


def _f(x: Any) -> float:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return np.nan
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def normalize_raw(raw: pd.DataFrame) -> pd.DataFrame:
    """Map SODA columns → typed weekly frame (field names verified 2026-09)."""
    d = pd.DataFrame(
        {
            "report_date": pd.to_datetime(raw["report_date_as_yyyy_mm_dd"]).dt.normalize(),
            "market": raw["market_and_exchange_names"].astype(str),
            "open_interest": raw["open_interest_all"].map(_f),
            "dealer_long": raw["dealer_positions_long_all"].map(_f),
            "dealer_short": raw["dealer_positions_short_all"].map(_f),
            # TFF uses non-_all names for AM / Lev on this dataset
            "am_long": raw["asset_mgr_positions_long"].map(_f),
            "am_short": raw["asset_mgr_positions_short"].map(_f),
            "lev_long": raw["lev_money_positions_long"].map(_f),
            "lev_short": raw["lev_money_positions_short"].map(_f),
        }
    )
    d = d.drop_duplicates("report_date").sort_values("report_date").reset_index(drop=True)
    d["net_dealer"] = d["dealer_long"] - d["dealer_short"]
    d["net_am"] = d["am_long"] - d["am_short"]
    d["net_lev"] = d["lev_long"] - d["lev_short"]
    return d


def friday_after_tuesday(tue: pd.Timestamp) -> pd.Timestamp:
    """Following Friday calendar date after Tuesday snapshot."""
    tue = pd.Timestamp(tue).normalize()
    # Tuesday=1 in pandas (Mon=0)
    if tue.dayofweek != 1:
        # COT report_date is almost always Tuesday; snap forward to next Tue then +3
        days_to_tue = (1 - tue.dayofweek) % 7
        tue = tue + pd.Timedelta(days=days_to_tue)
    return tue + pd.Timedelta(days=3)


def first_usable_session_date(report_date: pd.Timestamp):
    """
    Next session_date after Friday 15:30 ET release.

    Globex weekend: Friday RTH ends ~17:00; next open Sunday 18:00 ET
    with session_date = Monday. We freeze Monday = release_friday + 3 days.
    """
    fri = friday_after_tuesday(report_date)
    monday = fri + pd.Timedelta(days=3)
    return monday.date()


def rolling_z_and_extreme(net: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Causal trailing-W z and decile extremes (exclusive window)."""
    n = len(net)
    z = np.full(n, np.nan)
    z_lo = np.full(n, np.nan)
    z_hi = np.full(n, np.nan)
    ext = np.zeros(n, dtype=np.int8)  # -1 lo, +1 hi, 0 none
    for i in range(n):
        if i < ROLL_WEEKS:
            continue
        window = net[i - ROLL_WEEKS : i]
        if not np.all(np.isfinite(window)):
            continue
        mu = float(np.mean(window))
        sd = float(np.std(window, ddof=1))
        if sd <= 0 or not np.isfinite(net[i]):
            continue
        z[i] = (float(net[i]) - mu) / sd
    for i in range(n):
        if i < ROLL_WEEKS or not np.isfinite(z[i]):
            continue
        z_hist = z[i - ROLL_WEEKS : i]
        z_hist = z_hist[np.isfinite(z_hist)]
        if len(z_hist) < max(40, ROLL_WEEKS // 2):
            continue
        lo = float(np.percentile(z_hist, DECILE_LO))
        hi = float(np.percentile(z_hist, DECILE_HI))
        z_lo[i] = lo
        z_hi[i] = hi
        if z[i] >= hi:
            ext[i] = 1
        elif z[i] <= lo:
            ext[i] = -1
    return z, z_lo, z_hi, ext


def build_features(weekly: pd.DataFrame) -> pd.DataFrame:
    out = weekly.copy()
    for cat, col in (("lev", "net_lev"), ("am", "net_am"), ("dealer", "net_dealer")):
        z, zlo, zhi, ext = rolling_z_and_extreme(out[col].to_numpy(float))
        out[f"z_{cat}"] = z
        out[f"z_{cat}_p10"] = zlo
        out[f"z_{cat}_p90"] = zhi
        out[f"ext_{cat}"] = ext  # +1 hi / -1 lo / 0 none

    # Pre-registered trade sides (0 = no signal)
    # lev_fade: extreme long lev → short NQ (−1); extreme short lev → long (+1)
    out["side_lev_fade"] = np.where(
        out["ext_lev"] == 1, -1, np.where(out["ext_lev"] == -1, 1, 0)
    ).astype(np.int8)
    # am_follow: extreme long AM → long (+1); extreme short AM → short (−1)
    out["side_am_follow"] = np.where(
        out["ext_am"] == 1, 1, np.where(out["ext_am"] == -1, -1, 0)
    ).astype(np.int8)

    out["release_friday"] = out["report_date"].map(friday_after_tuesday)
    out["first_usable_session_date"] = out["report_date"].map(first_usable_session_date)
    # Exclusive end = next report's first usable
    out["next_first_usable_session_date"] = out["first_usable_session_date"].shift(-1)
    out["release_tod_et"] = "15:30"
    out["lag_rule"] = "tue_snapshot__fri_1530_release__next_session_only"
    return out


def build_session_map(feat: pd.DataFrame) -> pd.DataFrame:
    """Expand weekly features to one row per usable calendar session_date."""
    rows: list[dict[str, Any]] = []
    for _, r in feat.iterrows():
        start = r["first_usable_session_date"]
        end = r["next_first_usable_session_date"]
        if pd.isna(start):
            continue
        start_ts = pd.Timestamp(start)
        if pd.isna(end):
            end_ts = start_ts + pd.Timedelta(days=7)
        else:
            end_ts = pd.Timestamp(end)
        # session_dates in [start, end)
        days = pd.date_range(start_ts, end_ts - pd.Timedelta(days=1), freq="D")
        for d in days:
            rows.append(
                {
                    "session_date": d.date(),
                    "report_date": r["report_date"].date()
                    if hasattr(r["report_date"], "date")
                    else r["report_date"],
                    "release_friday": pd.Timestamp(r["release_friday"]).date(),
                    "first_usable_session_date": start,
                    "z_lev": r["z_lev"],
                    "z_am": r["z_am"],
                    "ext_lev": int(r["ext_lev"]),
                    "ext_am": int(r["ext_am"]),
                    "side_lev_fade": int(r["side_lev_fade"]),
                    "side_am_follow": int(r["side_am_follow"]),
                    "net_lev": r["net_lev"],
                    "net_am": r["net_am"],
                    "open_interest": r["open_interest"],
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    print("=== 23A build_cot_features ===", flush=True)
    raw = fetch_tff_raw()
    weekly = normalize_raw(raw)
    weekly_path = art("nq_cot_tff_weekly.parquet")
    weekly.to_parquet(weekly_path, index=False)
    print(
        f"Weekly rows={len(weekly)} "
        f"{weekly['report_date'].min().date()} -> {weekly['report_date'].max().date()}",
        flush=True,
    )

    feat = build_features(weekly)
    feat_path = art("nq_cot_features.parquet")
    # parquet-friendly dates
    feat_out = feat.copy()
    feat_out["report_date"] = pd.to_datetime(feat_out["report_date"])
    feat_out["release_friday"] = pd.to_datetime(feat_out["release_friday"])
    feat_out["first_usable_session_date"] = feat_out["first_usable_session_date"].astype(str)
    feat_out["next_first_usable_session_date"] = feat_out["next_first_usable_session_date"].astype(str)
    feat_out.to_parquet(feat_path, index=False)
    print(f"Features -> {feat_path}", flush=True)

    smap = build_session_map(feat)
    smap_path = art("nq_cot_session_map.parquet")
    smap.to_parquet(smap_path, index=False)
    n_sig = int(((smap["side_lev_fade"] != 0) | (smap["side_am_follow"] != 0)).sum())
    print(f"Session map rows={len(smap)} signal-days~{n_sig} -> {smap_path}", flush=True)

    meta = {
        "market": MARKET_EXACT,
        "futonly_or_combined": FUTONLY,
        "roll_weeks": ROLL_WEEKS,
        "decile_lo": DECILE_LO,
        "decile_hi": DECILE_HI,
        "release_tod_et": "15:30",
        "lag_rule": "tue_snapshot__fri_1530_release__next_session_only",
        "n_raw": int(len(raw)),
        "n_weekly": int(len(weekly)),
        "n_session_map": int(len(smap)),
        "date_start": str(weekly["report_date"].min().date()),
        "date_end": str(weekly["report_date"].max().date()),
        "sides_frozen": ["lev_fade", "am_follow"],
        "formula": "z=trailing_104_exclusive; extreme=p10/p90 of trailing z; no IS Sharpe pick",
    }
    meta_path = art("nq_cot_features_meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Meta -> {meta_path}", flush=True)
    print("DONE build_cot_features", flush=True)


if __name__ == "__main__":
    main()
