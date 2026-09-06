"""
Frozen multi-session Globex clock for NQ (America/New_York).

Session order within a session_date (starts 18:00 ET):
  Asia → London → NY_AM → NY_PM
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from common.splits import split_of

# Mirror nq_session clock constants (avoid circular import).
NY_OPEN = 9 * 60 + 30
SESSION_START = 18 * 60
# End of cash RTH (exclusive upper bound for NY_PM bars)
RTH_END = 16 * 60


@dataclass(frozen=True)
class SessionDef:
    name: str
    start_ny: int  # inclusive
    end_ny: int  # exclusive
    wraps: bool = False  # Asia: 18:00 → 03:00


SESSIONS: tuple[SessionDef, ...] = (
    SessionDef("ASIA", SESSION_START, 3 * 60, wraps=True),
    SessionDef("LONDON", 3 * 60, NY_OPEN, wraps=False),
    SessionDef("NY_AM", NY_OPEN, 12 * 60, wraps=False),
    SessionDef("NY_PM", 12 * 60, RTH_END, wraps=False),
)

SESSION_BY_NAME: dict[str, SessionDef] = {s.name: s for s in SESSIONS}
SESSION_ORDER: tuple[str, ...] = tuple(s.name for s in SESSIONS)

# Decision offsets from each session open (minutes). Horizon room is enforced at runtime.
SESSION_DECISION_OFFSETS: dict[str, tuple[int, ...]] = {
    "ASIA": (15, 30, 60, 90, 120, 180),
    "LONDON": (15, 30, 60, 90, 120),
    "NY_AM": (15, 30, 60, 90),
    "NY_PM": (15, 30, 60, 90, 120),
}

# Prior session used as range scale (psr). Asia uses prior session_date NY_PM.
PRIOR_SESSION: dict[str, str] = {
    "ASIA": "NY_PM",
    "LONDON": "ASIA",
    "NY_AM": "LONDON",
    "NY_PM": "NY_AM",
}


def session_of(ny_min: int) -> str | None:
    """Map a clock minute to a frozen session name, or None if outside all windows."""
    m = int(ny_min)
    if m >= SESSION_START or m < 3 * 60:
        return "ASIA"
    if 3 * 60 <= m < NY_OPEN:
        return "LONDON"
    if NY_OPEN <= m < 12 * 60:
        return "NY_AM"
    if 12 * 60 <= m < RTH_END:
        return "NY_PM"
    return None


def session_mask(ny_min: pd.Series | np.ndarray, name: str) -> np.ndarray:
    """Boolean mask for bars belonging to ``name``."""
    s = SESSION_BY_NAME[name]
    m = np.asarray(ny_min, dtype=np.int64)
    if s.wraps:
        return (m >= s.start_ny) | (m < s.end_ny)
    return (m >= s.start_ny) & (m < s.end_ny)


def bars_in_session(day: pd.DataFrame, name: str) -> pd.DataFrame:
    """Return bars for one session within a session_date group, sorted by ts."""
    mask = session_mask(day["ny_min"].to_numpy(np.int64), name)
    out = day.loc[mask].copy()
    if name == "ASIA" and len(out):
        # Chronological within session_date: 18:00…23:59 then 00:00…02:59
        ord_key = np.where(
            out["ny_min"].to_numpy(np.int64) >= SESSION_START,
            out["ny_min"].to_numpy(np.int64),
            out["ny_min"].to_numpy(np.int64) + 24 * 60,
        )
        out = out.assign(_ord=ord_key).sort_values("_ord").drop(columns=["_ord"])
    else:
        out = out.sort_values("ny_min")
    return out.reset_index(drop=True)


def session_open_ny(name: str) -> int:
    return SESSION_BY_NAME[name].start_ny


def decision_ny_min(name: str, offset: int) -> int:
    """Absolute ny_min for session_open + offset (handles Asia wrap past midnight)."""
    start = session_open_ny(name)
    if name != "ASIA":
        return start + int(offset)
    # Asia starts at 18:00; offsets can cross midnight
    t = start + int(offset)
    if t >= 24 * 60:
        t -= 24 * 60
    return t


def elapsed_from_session_open(name: str, T_ny: int) -> int:
    start = session_open_ny(name)
    if name != "ASIA":
        return max(int(T_ny - start), 1)
    # Asia: T may be before midnight or after
    if T_ny >= start:
        return max(int(T_ny - start), 1)
    return max(int((24 * 60 - start) + T_ny), 1)


def session_range(bars: pd.DataFrame) -> float:
    if len(bars) < 2:
        return float("nan")
    return float(bars["high"].max() - bars["low"].min())


def build_session_facts(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per (session_date, session): open, high, low, close, range, year, split.

    psr is filled in a second pass (prior session range on same session_date;
    Asia uses prior session_date NY_PM).
    """
    rows: list[dict] = []
    for sd, g in df.groupby("session_date", sort=True):
        year = int(g["year"].iloc[0])
        dow = int(g["dow"].iloc[0]) if "dow" in g.columns else int(pd.Timestamp(sd).dayofweek)
        for name in SESSION_ORDER:
            bars = bars_in_session(g, name)
            if len(bars) < 30:
                continue
            o = float(bars.iloc[0]["open"])
            h = float(bars["high"].max())
            l = float(bars["low"].min())
            c = float(bars.iloc[-1]["close"])
            rows.append(
                {
                    "session_date": sd,
                    "session": name,
                    "year": year,
                    "dow": dow,
                    "split": split_of(year),
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "range": h - l,
                    "n_bars": int(len(bars)),
                }
            )
    facts = pd.DataFrame(rows)
    if facts.empty:
        return facts

    facts = facts.sort_values(["session_date", "session"]).reset_index(drop=True)
    # Index prior ranges
    by_key = {
        (r["session_date"], r["session"]): float(r["range"])
        for _, r in facts.iterrows()
    }
    # Chronological session_date list for Asia prior NY_PM
    dates = sorted(facts["session_date"].unique(), key=lambda d: str(d))
    date_i = {d: i for i, d in enumerate(dates)}

    psr_vals: list[float] = []
    for _, r in facts.iterrows():
        name = str(r["session"])
        sd = r["session_date"]
        prior_name = PRIOR_SESSION[name]
        if name == "ASIA":
            i = date_i.get(sd)
            if i is None or i == 0:
                psr_vals.append(float("nan"))
                continue
            prev_sd = dates[i - 1]
            psr_vals.append(by_key.get((prev_sd, "NY_PM"), float("nan")))
        else:
            psr_vals.append(by_key.get((sd, prior_name), float("nan")))
    facts["psr"] = psr_vals
    return facts


def state_at_T_session(
    sess_to_T: pd.DataFrame,
    *,
    session: str,
    T_ny: int,
    session_open: float,
    psr: float,
) -> dict[str, float] | None:
    """
    Causal intra-session state using only bars with timestamp <= T, scaled by psr.
    """
    if len(sess_to_T) < 3 or not np.isfinite(psr) or psr <= 0:
        return None
    if T_ny not in set(sess_to_T["ny_min"].astype(int).tolist()):
        return None

    # Keep causal slice (Asia already chronologically ordered by bars_in_session)
    if session == "ASIA":
        # Include bars up to T in session order
        ord_T = T_ny if T_ny >= SESSION_START else T_ny + 24 * 60
        ord_key = np.where(
            sess_to_T["ny_min"].to_numpy(np.int64) >= SESSION_START,
            sess_to_T["ny_min"].to_numpy(np.int64),
            sess_to_T["ny_min"].to_numpy(np.int64) + 24 * 60,
        )
        sess_to_T = sess_to_T.loc[ord_key <= ord_T].reset_index(drop=True)
    else:
        sess_to_T = sess_to_T[sess_to_T["ny_min"] <= T_ny].reset_index(drop=True)

    if len(sess_to_T) < 3:
        return None

    o = sess_to_T["open"].to_numpy(float)
    h = sess_to_T["high"].to_numpy(float)
    l = sess_to_T["low"].to_numpy(float)
    c = sess_to_T["close"].to_numpy(float)
    last_c = float(c[-1])
    elapsed = elapsed_from_session_open(session, T_ny)

    rng = float(h.max() - l.min())
    rng_psr = rng / psr
    move = last_c - float(session_open)
    move_psr = move / psr
    path = float(np.sum(np.abs(np.diff(c)))) if len(c) > 1 else abs(move)
    path_psr = path / psr
    speed = abs(move_psr) / elapsed

    prev_c = np.concatenate([[o[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    atr = float(np.mean(tr)) if len(tr) else float(rng / max(elapsed, 1))
    vol_unit = max(atr, 0.05 * psr, 1.0)

    if abs(move) < 0.25:
        persist_frac = np.nan
        dir_sign = 0.0
    else:
        dir_sign = 1.0 if move > 0 else -1.0
        deltas = np.diff(c)
        persist_frac = float(np.mean(np.sign(deltas) == dir_sign)) if len(deltas) else np.nan

    return {
        "elapsed": float(elapsed),
        "rng_psr": rng_psr,
        "move_psr": move_psr,
        "abs_move_psr": abs(move_psr),
        "path_psr": path_psr,
        "speed": speed,
        "persist_frac": persist_frac,
        "dir_sign": dir_sign,
        "psr": float(psr),
        "atr": atr,
        "vol_unit": vol_unit,
        "vol_unit_psr": vol_unit / psr,
        "session_open": float(session_open),
    }


def iter_session_names() -> Iterable[str]:
    return SESSION_ORDER


__all__ = [
    "RTH_END",
    "NY_OPEN",
    "SESSION_START",
    "SessionDef",
    "SESSIONS",
    "SESSION_BY_NAME",
    "SESSION_ORDER",
    "SESSION_DECISION_OFFSETS",
    "PRIOR_SESSION",
    "session_of",
    "session_mask",
    "bars_in_session",
    "session_open_ny",
    "decision_ny_min",
    "elapsed_from_session_open",
    "session_range",
    "build_session_facts",
    "state_at_T_session",
    "iter_session_names",
]
