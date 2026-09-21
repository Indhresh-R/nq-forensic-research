"""Fast confirmed-swing and FVG index structures (no lookahead)."""
from __future__ import annotations

import numpy as np
import pandas as pd


class SwingIndex:
    """Sorted swing highs/lows with binary search by confirmed_at."""

    def __init__(self, swings: list[dict]):
        if not swings:
            self.times = np.array([], dtype="datetime64[ns]")
            self.prices = np.array([], dtype=float)
            return
        times = np.array([np.datetime64(pd.Timestamp(s["confirmed_at"]).to_datetime64()) for s in swings])
        prices = np.array([s["price"] for s in swings], dtype=float)
        order = np.argsort(times)
        self.times = times[order]
        self.prices = prices[order]

    def last_two(self, asof) -> tuple[float, float] | None:
        if len(self.times) < 2:
            return None
        t = np.datetime64(pd.Timestamp(asof).to_datetime64())
        i = int(np.searchsorted(self.times, t, side="right")) - 1
        if i < 1:
            return None
        return float(self.prices[i - 1]), float(self.prices[i])

    def last_one(self, asof) -> float | None:
        if len(self.times) < 1:
            return None
        t = np.datetime64(pd.Timestamp(asof).to_datetime64())
        i = int(np.searchsorted(self.times, t, side="right")) - 1
        if i < 0:
            return None
        return float(self.prices[i])


def smt_from_index(
    nq_h: SwingIndex,
    nq_l: SwingIndex,
    es_h: SwingIndex,
    es_l: SwingIndex,
    asof,
    direction: int,
) -> dict | None:
    if direction < 0:
        nq = nq_h.last_two(asof)
        es = es_h.last_two(asof)
        if nq is None or es is None:
            return None
        nq_hh = nq[1] > nq[0]
        es_hh = es[1] > es[0]
        nq_fail = nq[1] <= nq[0]
        es_fail = es[1] <= es[0]
        if (nq_hh and es_fail) or (es_hh and nq_fail):
            return {"smt_dir": -1, "nq_swing": nq[1], "es_swing": es[1]}
    else:
        nq = nq_l.last_two(asof)
        es = es_l.last_two(asof)
        if nq is None or es is None:
            return None
        nq_ll = nq[1] < nq[0]
        es_ll = es[1] < es[0]
        nq_fail = nq[1] >= nq[0]
        es_fail = es[1] >= es[0]
        if (nq_ll and es_fail) or (es_ll and nq_fail):
            return {"smt_dir": 1, "nq_swing": nq[1], "es_swing": es[1]}
    return None


class FVGIndex:
    """FVGs sorted by formed_at for overlap queries."""

    def __init__(self, fvgs: pd.DataFrame):
        if fvgs is None or fvgs.empty:
            self.times = np.array([], dtype="datetime64[ns]")
            self.dirs = np.array([], dtype=int)
            self.bottoms = np.array([], dtype=float)
            self.tops = np.array([], dtype=float)
            return
        f = fvgs.sort_values("formed_at")
        self.times = np.array(
            [np.datetime64(pd.Timestamp(t).to_datetime64()) for t in f["formed_at"]],
            dtype="datetime64[ns]",
        )
        self.dirs = f["direction"].to_numpy(int)
        self.bottoms = f["bottom"].to_numpy(float)
        self.tops = f["top"].to_numpy(float)

    def overlaps(self, asof, bias: int, low: float, high: float) -> bool:
        if len(self.times) == 0:
            return False
        t = np.datetime64(pd.Timestamp(asof).to_datetime64())
        n = int(np.searchsorted(self.times, t, side="right"))
        if n <= 0:
            return False
        # Check recent FVGs first (last 50 formed)
        start = max(0, n - 80)
        for i in range(n - 1, start - 1, -1):
            if self.dirs[i] != bias:
                continue
            if low <= self.tops[i] and high >= self.bottoms[i]:
                return True
        return False
