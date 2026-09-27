"""Frozen H02 CVD comparison. The rule is not changed here.

Full-sample 10th/90th percentile of cvd_1s, 15-second cooldown,
5-second taker: buy at ask, sell at bid, minus 0.25 points.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_DIR.parents[2]
sys.path.append(str(CODE_DIR))

from test_snapshot_clock import assert_samples_respect_snapshot_clock

FEATURES_DIR = PROJECT_ROOT / "strategies" / "44_mbo_orderflow" / "results" / "engineered_features"
SAMPLES_DIR = PROJECT_ROOT / "strategies" / "44_mbo_orderflow" / "results" / "sampled_features"
IS_SESSIONS = [
    "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15",
    "2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23",
    "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31",
    "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10",
    "2026-08-11", "2026-08-12",
]


def load_features() -> pd.DataFrame:
    frames = []
    for date_str in IS_SESSIONS:
        path = FEATURES_DIR / f"h02_features_{date_str}.parquet"
        if not path.exists():
            raise FileNotFoundError(path)
        frames.append(pd.read_parquet(path))
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["date", "ts_ns"]).reset_index(drop=True)


def frozen_taker_comparison(df: pd.DataFrame) -> None:
    p90 = df["cvd_1s"].quantile(0.90)
    p10 = df["cvd_1s"].quantile(0.10)
    sign = np.where(df["cvd_1s"] >= p90, 1, np.where(df["cvd_1s"] <= p10, -1, 0))
    sign = np.where(df["cvd_1s"].isna(), 0, sign)

    take = []
    dates = df["date"].to_numpy()
    last = -10**9
    last_date = None
    for i, side in enumerate(sign):
        if dates[i] != last_date:
            last = -10**9
            last_date = dates[i]
        if side != 0 and (i - last) >= 15:
            take.append(i)
            last = i

    sub = df.iloc[take].dropna(subset=["fwd_bid_5s", "fwd_ask_5s", "ask_px", "bid_px", "fwd_ret_5s", "cvd_1s"])
    side = np.where(sub["cvd_1s"] >= p90, 1.0, -1.0)
    net = np.where(
        side > 0,
        sub["fwd_bid_5s"] - sub["ask_px"] - 0.25,
        sub["bid_px"] - sub["fwd_ask_5s"] - 0.25,
    )
    gross = side * sub["fwd_ret_5s"].to_numpy()
    day = pd.Series(net).groupby(sub["date"].to_numpy()).sum()
    daily_ic = []
    for _, group in df.dropna(subset=["cvd_1s", "fwd_ret_1s"]).groupby("date"):
        daily_ic.append(stats.spearmanr(group["cvd_1s"], group["fwd_ret_1s"]).correlation)

    print(f"n {len(sub)}")
    print(f"gross {float(np.mean(gross)):.3f}")
    print(f"net {float(np.mean(net)):.3f}")
    print(f"days+ {int((day > 0).sum())} / {len(day)}")
    print(f"total {float(np.sum(net)):.1f}")
    print(f"daily_ic_1s {float(np.mean(daily_ic)):.4f}")


if __name__ == "__main__":
    assert_samples_respect_snapshot_clock(SAMPLES_DIR)
    print("snapshot clock passed")
    frozen_taker_comparison(load_features())
