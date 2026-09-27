"""Candle classification, FVG, swings, SMT — all confirmation-gated (no lookahead)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import BacktestConfig


def classify_c2_vs_c1(c1: pd.Series, c2: pd.Series) -> dict:
    """Continuation / reversal of C2 relative to C1 after C2 has closed.

    C2 sweeps C1 high if c2.high > c1.high; sweeps low if c2.low < c1.low.
    Continuation: sweeps and closes beyond that extreme.
    Reversal: sweeps but closes back inside C1 range.
    """
    swept_high = float(c2["high"]) > float(c1["high"])
    swept_low = float(c2["low"]) < float(c1["low"])
    inside = (float(c1["low"]) <= float(c2["close"]) <= float(c1["high"]))
    cont_up = swept_high and float(c2["close"]) > float(c1["high"])
    cont_dn = swept_low and float(c2["close"]) < float(c1["low"])
    rev_up = swept_low and float(c2["close"]) > float(c1["low"]) and not cont_dn
    # Reversal after sweep of low that closes back inside (bullish reversal)
    # Reversal after sweep of high that closes back inside (bearish reversal)
    rev_from_high = swept_high and inside
    rev_from_low = swept_low and inside

    if cont_up:
        kind, direction = "continuation", 1
    elif cont_dn:
        kind, direction = "continuation", -1
    elif rev_from_low or (swept_low and float(c2["close"]) >= float(c1["low"])):
        kind, direction = "reversal", 1
    elif rev_from_high or (swept_high and float(c2["close"]) <= float(c1["high"])):
        kind, direction = "reversal", -1
    else:
        kind, direction = "none", 0

    return {
        "kind": kind,
        "direction": direction,
        "swept_high": swept_high,
        "swept_low": swept_low,
        "cont_up": cont_up,
        "cont_dn": cont_dn,
        "rev_up": bool(rev_from_low),
        "rev_dn": bool(rev_from_high),
    }


def detect_fvgs(ohlc: pd.DataFrame) -> pd.DataFrame:
    """Standard 3-candle FVG. Indexed by the 3rd candle (formation candle).

    Bullish FVG: candle1.high < candle3.low  (gap between 1 and 3)
    Bearish FVG: candle1.low > candle3.high
    Zone = [c1.high, c3.low] bullish / [c3.high, c1.low] bearish.
    Known only after candle3 close_ts.
    """
    if len(ohlc) < 3:
        return pd.DataFrame()
    o = ohlc.reset_index(drop=True)
    rows = []
    for i in range(2, len(o)):
        c1, c3 = o.iloc[i - 2], o.iloc[i]
        if float(c1["high"]) < float(c3["low"]):
            rows.append(
                {
                    "idx": i,
                    "direction": 1,
                    "bottom": float(c1["high"]),
                    "top": float(c3["low"]),
                    "formed_at": c3["close_ts"],
                    "session_date": c3.get("session_date"),
                }
            )
        if float(c1["low"]) > float(c3["high"]):
            rows.append(
                {
                    "idx": i,
                    "direction": -1,
                    "bottom": float(c3["high"]),
                    "top": float(c1["low"]),
                    "formed_at": c3["close_ts"],
                    "session_date": c3.get("session_date"),
                }
            )
    return pd.DataFrame(rows)


def mitigation_mask(
    fvg: pd.Series,
    closes: np.ndarray,
    close_times: np.ndarray,
) -> np.ndarray | None:
    """Return first time index where close mitigates FVG (closes through it)."""
    # Bullish mitigated when close < bottom; bearish when close > top
    after = close_times > np.datetime64(pd.Timestamp(fvg["formed_at"]))
    if fvg["direction"] == 1:
        hit = after & (closes < float(fvg["bottom"]))
    else:
        hit = after & (closes > float(fvg["top"]))
    if not hit.any():
        return None
    return int(np.argmax(hit))


def confirmed_swings(
    highs: np.ndarray,
    lows: np.ndarray,
    close_ts: np.ndarray,
    lookback: int,
) -> tuple[list[dict], list[dict]]:
    """Fractal swings confirmed only after ``lookback`` bars to the right close.

    Swing high at i if highs[i] == max(highs[i-L:i+L+1]) strictly greater than
    neighbors on at least one side; confirmed at bar i+L close.
    """
    n = len(highs)
    L = lookback
    sh, sl = [], []
    for i in range(L, n - L):
        window_h = highs[i - L : i + L + 1]
        window_l = lows[i - L : i + L + 1]
        if highs[i] >= window_h.max() and highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            sh.append(
                {
                    "idx": i,
                    "price": float(highs[i]),
                    "confirmed_at": close_ts[i + L],
                    "kind": "high",
                }
            )
        if lows[i] <= window_l.min() and lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            sl.append(
                {
                    "idx": i,
                    "price": float(lows[i]),
                    "confirmed_at": close_ts[i + L],
                    "kind": "low",
                }
            )
    return sh, sl


def smt_at_bar(
    nq_swings_h: list[dict],
    nq_swings_l: list[dict],
    es_swings_h: list[dict],
    es_swings_l: list[dict],
    now_ts,
    direction: int,
) -> dict | None:
    """Detect SMT using only swings confirmed at or before now_ts.

    Bearish SMT (direction=-1): one market makes HH vs its prior swing high,
    the other fails (lower or equal high).
    Bullish SMT (direction=1): one makes LL, the other fails (higher or equal low).
    """
    now = pd.Timestamp(now_ts)

    def last_two(swings: list[dict]) -> tuple[dict, dict] | None:
        avail = [s for s in swings if pd.Timestamp(s["confirmed_at"]) <= now]
        if len(avail) < 2:
            return None
        return avail[-2], avail[-1]

    if direction < 0:
        nq = last_two(nq_swings_h)
        es = last_two(es_swings_h)
        if nq is None or es is None:
            return None
        nq_hh = nq[1]["price"] > nq[0]["price"]
        es_hh = es[1]["price"] > es[0]["price"]
        nq_fail = nq[1]["price"] <= nq[0]["price"]
        es_fail = es[1]["price"] <= es[0]["price"]
        if (nq_hh and es_fail) or (es_hh and nq_fail):
            extreme = max(nq[1]["price"], es[1]["price"])  # for NQ stop use NQ swing
            return {
                "smt_dir": -1,
                "nq_swing": nq[1]["price"],
                "es_swing": es[1]["price"],
                "leader": "NQ" if nq_hh else "ES",
            }
    else:
        nq = last_two(nq_swings_l)
        es = last_two(es_swings_l)
        if nq is None or es is None:
            return None
        nq_ll = nq[1]["price"] < nq[0]["price"]
        es_ll = es[1]["price"] < es[0]["price"]
        nq_fail = nq[1]["price"] >= nq[0]["price"]
        es_fail = es[1]["price"] >= es[0]["price"]
        if (nq_ll and es_fail) or (es_ll and nq_fail):
            return {
                "smt_dir": 1,
                "nq_swing": nq[1]["price"],
                "es_swing": es[1]["price"],
                "leader": "NQ" if nq_ll else "ES",
            }
    return None


def find_engulfing_protected(
    ohlc: pd.DataFrame,
    bias: int,
    asof_ts,
) -> dict | None:
    """Protected low/high from engulfing structure known by asof_ts.

    Bullish: prior down-close, then candle closes above prior high
    -> protected low = min(engulfed.low, engulfer.low). Mirror for bearish.
    Only scans the last 120 closed candles (recent structure).
    """
    avail = ohlc[ohlc["close_ts"] <= asof_ts].tail(120).reset_index(drop=True)
    if len(avail) < 2:
        return None
    best = None
    for i in range(1, len(avail)):
        prev, cur = avail.iloc[i - 1], avail.iloc[i]
        if bias > 0:
            prior_down = float(prev["close"]) < float(prev["open"])
            if prior_down and float(cur["close"]) > float(prev["high"]):
                prot = min(float(prev["low"]), float(cur["low"]))
                best = {
                    "level": prot,
                    "formed_at": cur["close_ts"],
                    "idx": i,
                    "side": "low",
                }
        else:
            prior_up = float(prev["close"]) > float(prev["open"])
            if prior_up and float(cur["close"]) < float(prev["low"]):
                prot = max(float(prev["high"]), float(cur["high"]))
                best = {
                    "level": prot,
                    "formed_at": cur["close_ts"],
                    "idx": i,
                    "side": "high",
                }
    return best


def price_in_fvg(price: float, fvg: dict | pd.Series) -> bool:
    return float(fvg["bottom"]) <= price <= float(fvg["top"])


def nearest_unmitigated_fvg(
    fvgs: pd.DataFrame,
    direction: int,
    asof_ts,
    ref_price: float,
    close_series: pd.DataFrame | None = None,
) -> dict | None:
    """Nearest unmitigated FVG in ``direction`` relative to ref_price by asof_ts."""
    if fvgs is None or fvgs.empty:
        return None
    cand = fvgs[(fvgs["direction"] == direction) & (fvgs["formed_at"] <= asof_ts)]
    if cand.empty:
        return None
    # Mitigate using closes through asof
    kept = []
    for _, f in cand.iterrows():
        mitigated = False
        if close_series is not None:
            later = close_series[
                (close_series["close_ts"] > f["formed_at"])
                & (close_series["close_ts"] <= asof_ts)
            ]
            if direction > 0 and (later["close"] < f["bottom"]).any():
                mitigated = True
            if direction < 0 and (later["close"] > f["top"]).any():
                mitigated = True
        if not mitigated:
            mid = 0.5 * (f["bottom"] + f["top"])
            kept.append((abs(mid - ref_price), f))
    if not kept:
        return None
    kept.sort(key=lambda x: x[0])
    return kept[0][1].to_dict()


def equal_liquidity_levels(
    swings: list[dict],
    tol: float,
    asof_ts,
    direction: int,
    entry: float,
) -> float | None:
    """Nearest equal highs (short TP) or equal lows (long TP) beyond entry."""
    now = pd.Timestamp(asof_ts)
    avail = [s for s in swings if pd.Timestamp(s["confirmed_at"]) <= now]
    if len(avail) < 2:
        return None
    # Find equal pairs within tol
    levels = []
    for i in range(len(avail)):
        for j in range(i + 1, len(avail)):
            if abs(avail[i]["price"] - avail[j]["price"]) <= tol:
                levels.append(0.5 * (avail[i]["price"] + avail[j]["price"]))
    if not levels:
        return None
    if direction > 0:
        above = [lv for lv in levels if lv > entry]
        return min(above) if above else None
    below = [lv for lv in levels if lv < entry]
    return max(below) if below else None


def nearest_swing_target(
    swings: list[dict],
    asof_ts,
    direction: int,
    entry: float,
) -> float | None:
    now = pd.Timestamp(asof_ts)
    avail = [s for s in swings if pd.Timestamp(s["confirmed_at"]) <= now]
    if direction > 0:
        above = [s["price"] for s in avail if s["kind"] == "high" and s["price"] > entry]
        return min(above) if above else None
    below = [s["price"] for s in avail if s["kind"] == "low" and s["price"] < entry]
    return max(below) if below else None


@dataclass
class CandleStore:
    """Precomputed multi-TF OHLC with close_ts gating."""

    daily: pd.DataFrame
    h7: pd.DataFrame
    h4: pd.DataFrame
    h1: pd.DataFrame
    m15: pd.DataFrame
    m5: pd.DataFrame
    m1: pd.DataFrame
