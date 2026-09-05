"""
NQ NY Open — fast causal retest (numpy). Contaminated v1 discarded.
"""
from __future__ import annotations

import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))


import json
import warnings
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

from common.paths import art, ART, DATA, ROOT

NY_OPEN = 9 * 60 + 30
SESSION_START = 18 * 60
HORIZONS = (5, 10, 15, 20, 30)
ACCEPT_FRAC = 0.15
PB_TRIGGER = 0.382
IMP_WIN = 10
SLIP = 0.50
COMM = 0.50
TICK = 0.25
TARGET_R = 1.5
MAX_HOLD = 60

IS_Y = set(range(2010, 2022))
VAL_Y = {2022, 2023, 2024}
OOS_Y = {2025, 2026}


def split_of(y: int) -> str:
    if y in IS_Y:
        return "IS"
    if y in VAL_Y:
        return "Validation"
    if y in OOS_Y:
        return "OOS"
    return "OTHER"


def load_nq() -> pd.DataFrame:
    df = pd.read_parquet(DATA / "nq_1m_continuous.parquet")
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert("America/New_York")
    out = pd.DataFrame(
        {
            "ts": ts,
            "open": df["open"].to_numpy(np.float64),
            "high": df["high"].to_numpy(np.float64),
            "low": df["low"].to_numpy(np.float64),
            "close": df["close"].to_numpy(np.float64),
        }
    )
    out["year"] = out["ts"].dt.year.astype(np.int16)
    out["dow"] = out["ts"].dt.dayofweek.astype(np.int8)
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    cal = out["ts"].dt.date
    out["session_date"] = np.where(
        out["ny_min"].to_numpy() >= SESSION_START,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    return out


def dist(x: np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return {"n": 0}
    return {
        "n": int(n),
        "mean": float(x.mean()),
        "median": float(np.median(x)),
        "std": float(x.std(ddof=1)) if n > 1 else 0.0,
        "win_p": float((x > 0).mean()),
        "p_gt_5": float((x >= 5).mean()),
        "p_lt_m5": float((x <= -5).mean()),
        "p_gt_10": float((x >= 10).mean()),
        "p_lt_m10": float((x <= -10).mean()),
    }


def fwd_dir(o, h, l, c, entry_i: int, direction: int) -> tuple[dict[int, float], float, float]:
    n = len(c)
    if entry_i >= n:
        return {hh: np.nan for hh in HORIZONS}, np.nan, np.nan
    entry = float(o[entry_i])
    fwd = {}
    for hh in HORIZONS:
        j = entry_i + hh - 1
        fwd[hh] = (float(c[j]) - entry) * direction if j < n else np.nan
    end = min(n, entry_i + 30)
    if end <= entry_i:
        return fwd, np.nan, np.nan
    if direction == 1:
        mfe = float(np.max(h[entry_i:end] - entry))
        mae = float(np.max(entry - l[entry_i:end]))
    else:
        mfe = float(np.max(entry - l[entry_i:end]))
        mae = float(np.max(h[entry_i:end] - entry))
    return fwd, mfe, mae


def aggregate(rows: list[dict]) -> dict[str, Any]:
    out: dict[str, Any] = {"n_total": len(rows)}
    for sp in ("IS", "Validation", "OOS", "ALL"):
        sub = rows if sp == "ALL" else [r for r in rows if r["split"] == sp]
        out[sp] = {"n": len(sub)}
        for hh in HORIZONS:
            out[sp][f"h{hh}"] = dist(np.array([r["fwd"].get(hh, np.nan) for r in sub], float))
        out[sp]["mfe_30"] = dist(np.array([r.get("mfe", np.nan) for r in sub], float))
        out[sp]["mae_30"] = dist(np.array([r.get("mae", np.nan) for r in sub], float))
        out[sp]["h15_onr"] = dist(
            np.array(
                [
                    r["fwd"].get(15, np.nan) / r["onr"]
                    if r.get("onr") and np.isfinite(r["fwd"].get(15, np.nan))
                    else np.nan
                    for r in sub
                ],
                float,
            )
        )
    return out


def score(block: dict) -> dict[str, Any]:
    def e(sp, h=15):
        return block.get(sp, {}).get(f"h{h}", {})

    is_e, va_e, oo_e, oo20 = e("IS"), e("Validation"), e("OOS"), e("OOS", 20)

    def strong(st):
        return st.get("n", 0) >= 50 and st.get("win_p", 0) >= 0.55 and st.get("mean", 0) > 0

    def pos(st):
        return st.get("n", 0) >= 30 and st.get("mean", 0) > 0 and st.get("win_p", 0) > 0.52

    survives = strong(is_e) and pos(va_e) and (pos(oo_e) or pos(oo20))
    same = is_e.get("mean", 0) > 0 and va_e.get("mean", 0) > 0 and (oo_e.get("mean", 0) > 0 or oo20.get("mean", 0) > 0)
    return {
        "survives_strict": bool(survives),
        "same_sign_means": bool(same),
        "IS_h15": is_e,
        "Val_h15": va_e,
        "OOS_h15": oo_e,
        "OOS_h20": oo20,
        "score": float(
            (is_e.get("win_p", 0.5) - 0.5) * 100
            + (va_e.get("win_p", 0.5) - 0.5) * 100
            + (oo_e.get("win_p", 0.5) - 0.5) * 100
        )
        if is_e.get("n", 0)
        else -999,
    }


def build_day_arrays(df: pd.DataFrame, day_df: pd.DataFrame) -> dict[str, dict]:
    """Pre-slice RTH arrays per session_date string."""
    meta = {r["session_date"]: r for _, r in day_df.iterrows()}
    out = {}
    # group once
    for sd, g in df.groupby("session_date", sort=False):
        key = str(sd)
        if key not in meta:
            continue
        g = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)]
        if len(g) < 40:
            continue
        out[key] = {
            "ny": g["ny_min"].to_numpy(np.int16),
            "o": g["open"].to_numpy(np.float64),
            "h": g["high"].to_numpy(np.float64),
            "l": g["low"].to_numpy(np.float64),
            "c": g["close"].to_numpy(np.float64),
            "meta": meta[key],
        }
    return out


def causal_levels(days: dict[str, dict]) -> list[dict]:
    events = []
    for key, d in days.items():
        m = d["meta"]
        ny, o, h, l, c = d["ny"], d["o"], d["h"], d["l"], d["c"]
        onr = float(m["onr"])
        levels = [
            ("ONH", float(m["onh"]), 1),
            ("ONL", float(m["onl"]), -1),
            ("PDH", float(m["pdh"]), 1),
            ("PDL", float(m["pdl"]), -1),
        ]
        n = len(c)
        for lname, lvl, bdir in levels:
            for i in range(n):
                prev = c[i - 1] if i > 0 else o[i]
                if bdir == 1:
                    crossed = c[i] > lvl and prev <= lvl
                else:
                    crossed = c[i] < lvl and prev >= lvl
                if not crossed:
                    continue
                outcome = None
                conf = None
                for j in range(i + 1, min(n, i + 16)):
                    if bdir == 1:
                        if c[j] < lvl:
                            outcome, conf = "reject", j
                            break
                        if c[j] >= lvl + ACCEPT_FRAC * onr:
                            outcome, conf = "accept", j
                            break
                    else:
                        if c[j] > lvl:
                            outcome, conf = "reject", j
                            break
                        if c[j] <= lvl - ACCEPT_FRAC * onr:
                            outcome, conf = "accept", j
                            break
                if outcome is None:
                    break
                entry_i = conf + 1
                if entry_i >= n or ny[entry_i] > 11 * 60:
                    break
                tdir = bdir if outcome == "accept" else -bdir
                fwd, mfe, mae = fwd_dir(o, h, l, c, entry_i, tdir)
                events.append(
                    {
                        "session_date": key,
                        "year": int(m["year"]),
                        "dow": int(m["dow"]),
                        "split": str(m["split"]),
                        "level_name": lname,
                        "outcome": outcome,
                        "trade_dir": tdir,
                        "level": lvl,
                        "entry_i": entry_i,
                        "entry_ny_min": int(ny[entry_i]),
                        "onr": onr,
                        "fwd": fwd,
                        "mfe": mfe,
                        "mae": mae,
                    }
                )
                break
    return events


def causal_impulse(days: dict[str, dict], large_th: float) -> tuple[list[dict], list[dict]]:
    cont, fail = [], []
    for key, d in days.items():
        m = d["meta"]
        ny, o, h, l, c = d["ny"], d["o"], d["h"], d["l"], d["c"]
        onr = float(m["onr"])
        o930 = float(m["open_930"])
        n = len(c)
        # impulse window indices
        wmask = ny < NY_OPEN + IMP_WIN
        if wmask.sum() < 5:
            continue
        w_idx = np.where(wmask)[0]
        net = float(c[w_idx[-1]] - o930)
        if abs(net) < TICK:
            continue
        direction = 1 if net > 0 else -1
        if direction == 1:
            li = int(np.argmax(h[w_idx]))
            extreme = float(h[w_idx[li]])
            imp = extreme - o930
        else:
            li = int(np.argmin(l[w_idx]))
            extreme = float(l[w_idx[li]])
            imp = o930 - extreme
        if imp < TICK:
            continue
        ext_i = int(w_idx[li])
        ext_onr = imp / onr
        large = ext_onr >= large_th
        got_c = got_f = False
        for j in range(ext_i + 1, min(n, ext_i + 41)):
            if direction == 1:
                pb = (extreme - l[j]) / imp
                failed = c[j] < o930
            else:
                pb = (h[j] - extreme) / imp
                failed = c[j] > o930
            if (not got_f) and failed:
                entry_i = j + 1
                if entry_i < n and ny[entry_i] <= 10 * 60 + 45:
                    fwd, mfe, mae = fwd_dir(o, h, l, c, entry_i, -direction)
                    fail.append(
                        {
                            "session_date": key,
                            "year": int(m["year"]),
                            "dow": int(m["dow"]),
                            "split": str(m["split"]),
                            "large": large,
                            "trade_dir": -direction,
                            "entry_i": entry_i,
                            "entry_ny_min": int(ny[entry_i]),
                            "onr": onr,
                            "fwd": fwd,
                            "mfe": mfe,
                            "mae": mae,
                        }
                    )
                got_f = True
            if (not got_c) and pb >= PB_TRIGGER and not failed:
                entry_i = j + 1
                if entry_i < n and ny[entry_i] <= 10 * 60 + 45:
                    fwd, mfe, mae = fwd_dir(o, h, l, c, entry_i, direction)
                    cont.append(
                        {
                            "session_date": key,
                            "year": int(m["year"]),
                            "dow": int(m["dow"]),
                            "split": str(m["split"]),
                            "large": large,
                            "trade_dir": direction,
                            "entry_i": entry_i,
                            "entry_ny_min": int(ny[entry_i]),
                            "onr": onr,
                            "fwd": fwd,
                            "mfe": mfe,
                            "mae": mae,
                        }
                    )
                got_c = True
            if got_c and got_f:
                break
    return cont, fail


def causal_gap(days: dict[str, dict]) -> list[dict]:
    rows = []
    for key, d in days.items():
        m = d["meta"]
        ny, o, h, l, c = d["ny"], d["o"], d["h"], d["l"], d["c"]
        o930, onh, onl, onr = float(m["open_930"]), float(m["onh"]), float(m["onl"]), float(m["onr"])
        n = len(c)
        direction = 0
        conf = None
        if o930 > onh:
            for i in range(1, min(30, n)):
                if c[i] < onh:
                    conf, direction = i, -1
                    break
        elif o930 < onl:
            for i in range(1, min(30, n)):
                if c[i] > onl:
                    conf, direction = i, 1
                    break
        if conf is None:
            continue
        entry_i = conf + 1
        if entry_i >= n:
            continue
        fwd, mfe, mae = fwd_dir(o, h, l, c, entry_i, direction)
        rows.append(
            {
                "session_date": key,
                "year": int(m["year"]),
                "dow": int(m["dow"]),
                "split": str(m["split"]),
                "trade_dir": direction,
                "entry_i": entry_i,
                "onr": onr,
                "fwd": fwd,
                "mfe": mfe,
                "mae": mae,
            }
        )
    return rows


def unconditional(days: dict[str, dict], offset: int) -> list[dict]:
    rows = []
    for key, d in days.items():
        m = d["meta"]
        ny, o, h, l, c = d["ny"], d["o"], d["h"], d["l"], d["c"]
        matches = np.where(ny == NY_OPEN + offset)[0]
        if len(matches) == 0:
            continue
        i = int(matches[0])
        fwd, mfe, mae = fwd_dir(o, h, l, c, i, 1)
        rows.append(
            {
                "split": str(m["split"]),
                "year": int(m["year"]),
                "onr": float(m["onr"]),
                "fwd": fwd,
                "mfe": mfe,
                "mae": mae,
            }
        )
    return rows


@dataclass
class Trade:
    session_date: str
    year: int
    split: str
    dow: int
    direction: int
    entry: float
    stop: float
    target: float
    risk: float
    exit_price: float
    pnl_pts: float
    pnl_R: float
    exit_reason: str
    ambiguous: bool
    minutes_held: int
    mae: float
    mfe: float
    hypothesis: str


def simulate(o, h, l, c, entry_i, direction, stop, target, entry):
    risk = abs(entry - stop)
    if risk < TICK:
        return entry, 0.0, "invalid", False, 0, 0.0, 0.0
    mae = mfe = 0.0
    end = min(len(c), entry_i + MAX_HOLD)
    for j in range(entry_i, end):
        if direction == 1:
            mae = max(mae, entry - l[j])
            mfe = max(mfe, h[j] - entry)
            hs, ht = l[j] <= stop, h[j] >= target
        else:
            mae = max(mae, h[j] - entry)
            mfe = max(mfe, entry - l[j])
            hs, ht = h[j] >= stop, l[j] <= target
        if hs and ht:
            return stop, (stop - entry) * direction, "stop_ambiguous", True, j - entry_i + 1, mae, mfe
        if hs:
            return stop, (stop - entry) * direction, "stop", False, j - entry_i + 1, mae, mfe
        if ht:
            return target, (target - entry) * direction, "target", False, j - entry_i + 1, mae, mfe
    last = float(c[end - 1])
    return last, (last - entry) * direction, "time", False, end - entry_i, mae, mfe


def strat_from_events(days: dict[str, dict], events: list[dict], hyp: str) -> list[Trade]:
    trades = []
    used = set()
    evs = sorted(events, key=lambda e: (e["session_date"], e.get("entry_ny_min", 0)))
    for e in evs:
        if e["session_date"] in used:
            continue
        d = days.get(e["session_date"])
        if d is None:
            continue
        entry_i = e["entry_i"]
        o, h, l, c = d["o"], d["h"], d["l"], d["c"]
        if entry_i >= len(c):
            continue
        entry = float(o[entry_i])
        direction = int(e["trade_dir"])
        risk = max(0.25 * e["onr"], 5.0)
        if direction == 1:
            stop, target = entry - risk, entry + TARGET_R * risk
        else:
            stop, target = entry + risk, entry - TARGET_R * risk
        exit_px, pnl_g, reason, amb, held, mae, mfe = simulate(
            o, h, l, c, entry_i, direction, stop, target, entry
        )
        pnl = pnl_g - 2 * SLIP - COMM
        trades.append(
            Trade(
                session_date=e["session_date"],
                year=e["year"],
                split=e["split"],
                dow=e["dow"],
                direction=direction,
                entry=entry,
                stop=stop,
                target=target,
                risk=risk,
                exit_price=exit_px,
                pnl_pts=pnl,
                pnl_R=pnl / risk,
                exit_reason=reason,
                ambiguous=amb,
                minutes_held=held,
                mae=mae,
                mfe=mfe,
                hypothesis=hyp,
            )
        )
        used.add(e["session_date"])
    return trades


def trade_perf(trades: list[Trade]) -> dict[str, Any]:
    if not trades:
        return {"n": 0}
    df = pd.DataFrame([asdict(t) for t in trades])
    r = df["pnl_R"].to_numpy(float)
    pts = df["pnl_pts"].to_numpy(float)
    wins = pts > 0
    gw = float(pts[wins].sum()) if wins.any() else 0.0
    gl = float(-pts[~wins].sum()) if (~wins).any() else 0.0
    cum = np.cumsum(r)
    dd = float((cum - np.maximum.accumulate(cum)).min())

    def by_sp(name):
        s = df[df["split"] == name]
        if len(s) == 0:
            return {"n": 0}
        rr, pp = s["pnl_R"].to_numpy(float), s["pnl_pts"].to_numpy(float)
        w = pp > 0
        gw2 = float(pp[w].sum()) if w.any() else 0.0
        gl2 = float(-pp[~w].sum()) if (~w).any() else 0.0
        return {
            "n": int(len(s)),
            "win_rate": float(w.mean()),
            "expectancy_R": float(rr.mean()),
            "total_R": float(rr.sum()),
            "avg_pts": float(pp.mean()),
            "pf": float(gw2 / gl2) if gl2 > 0 else None,
            "median_R": float(np.median(rr)),
        }

    yearly = []
    for y, s in df.groupby("year"):
        pp, rr = s["pnl_pts"].to_numpy(float), s["pnl_R"].to_numpy(float)
        yearly.append(
            {
                "year": int(y),
                "n": int(len(s)),
                "total_R": float(rr.sum()),
                "avg_R": float(rr.mean()),
                "win_rate": float((pp > 0).mean()),
                "total_pts": float(pp.sum()),
            }
        )
    yb = {}
    for y in (2025, 2026):
        s = df[df["year"] == y]
        yb[str(y)] = (
            {"n": 0}
            if len(s) == 0
            else {
                "n": int(len(s)),
                "total_R": float(s["pnl_R"].sum()),
                "avg_R": float(s["pnl_R"].mean()),
                "win_rate": float((s["pnl_pts"] > 0).mean()),
            }
        )
    df["ym"] = pd.to_datetime(df["session_date"]).dt.to_period("M").astype(str)
    monthly = [
        {
            "month": ym,
            "n": int(len(s)),
            "total_R": float(s["pnl_R"].sum()),
            "win_rate": float((s["pnl_pts"] > 0).mean()),
        }
        for ym, s in df.groupby("ym")
    ]
    # weekday / vol regime on OOS
    oos = df[df["split"] == "OOS"]
    by_dow = []
    for d, s in oos.groupby("dow"):
        by_dow.append(
            {
                "dow": int(d),
                "n": int(len(s)),
                "avg_R": float(s["pnl_R"].mean()),
                "win_rate": float((s["pnl_pts"] > 0).mean()),
            }
        )
    return {
        "n": int(len(df)),
        "win_rate": float(wins.mean()),
        "profit_factor": float(gw / gl) if gl > 0 else None,
        "expectancy_R": float(r.mean()),
        "total_R": float(r.sum()),
        "max_drawdown_R": dd,
        "median_R": float(np.median(r)),
        "avg_pts": float(pts.mean()),
        "trades_per_day": float(len(df) / max(df["session_date"].nunique(), 1)),
        "unique_days": int(df["session_date"].nunique()),
        "ambiguous_pct": float(df["ambiguous"].mean()),
        "avg_mae": float(df["mae"].mean()),
        "avg_mfe": float(df["mfe"].mean()),
        "costs": {"slippage_per_side": SLIP, "commission_rt_pts": COMM},
        "by_split": {k: by_sp(k) for k in ("IS", "Validation", "OOS")},
        "yearly": yearly,
        "monthly_profitability_pct": float(np.mean([m["total_R"] > 0 for m in monthly])) if monthly else 0.0,
        "monthly": monthly[-24:],
        "y2025_2026": yb,
        "oos_by_dow": by_dow,
        "hypothesis": df["hypothesis"].iloc[0],
    }


def render_md(report, rankings, survivors, soft, falsified, strategy, phase1, large_th, v1_note) -> str:
    v = report["verdict"]
    L = []
    L += [
        "# NQ NY Open — Behavioral Discovery Report",
        "",
        f"**Verdict: {v['code']} — {v['text']}**",
        "",
        f"> **Methodology:** {v1_note['reason']}",
        "",
        f"Dataset: `nq_1m_continuous.parquet` (2010-06 → 2026-08). "
        f"IS/Val/OOS = 2010–2021 / 2022–2024 / 2025–2026. "
        f"Large-impulse threshold (IS P66 impulse/ONR) = **{large_th:.4f}**.",
        "",
        "## 1. NQ Behavioral Facts",
        "",
    ]
    onr = phase1.get("overnight_range", {})
    r1, r5, r10, r30 = (
        phase1.get("first_1m_range", {}),
        phase1.get("first_5m_range", {}),
        phase1.get("first_10m_range", {}),
        phase1.get("first_30m_range", {}),
    )
    touch = phase1.get("level_touch_0930_1100", {})
    pext = phase1.get("p_5m_direction_extends_to_30m", {})
    pb = phase1.get("pullback_frac", {})
    L.append(
        f"- Overnight range median **{onr.get('median', float('nan')):.1f}** pts "
        f"(mean {onr.get('mean', float('nan')):.1f}); non-stationary across 2010–2026."
    )
    L.append(
        f"- Opening range medians: 1m **{r1.get('median', float('nan')):.1f}**, "
        f"5m **{r5.get('median', float('nan')):.1f}**, 10m **{r10.get('median', float('nan')):.1f}**, "
        f"30m **{r30.get('median', float('nan')):.1f}** pts."
    )
    L.append(
        f"- By 11:00 ET: ONH **{100*touch.get('ONH', 0):.0f}%**, ONL **{100*touch.get('ONL', 0):.0f}%**, "
        f"both **{100*touch.get('both_ON', 0):.0f}%**; PDH **{100*touch.get('PDH', 0):.0f}%**, "
        f"PDL **{100*touch.get('PDL', 0):.0f}%**."
    )
    L.append(
        f"- P(5m direction extends to 30m) = **{100*pext.get('p', float('nan')):.1f}%** — weak persistence."
    )
    L.append(
        f"- Ex-post impulse pullback depth (descriptive): median **{pb.get('median', float('nan')):.2f}×** impulse."
    )
    L += ["", "### Year-by-year (median pts)", "", "| Year | n | ONR | 30m | impulse/ONR |", "|------|---|-----|-----|-------------|"]
    for y in phase1.get("yearly_vol", []):
        L.append(
            f"| {y['year']} | {y['n']} | {y['median_onr']:.1f} | {y['median_range_30m']:.1f} | {y['median_impulse_onr']:.3f} |"
        )
    L += [
        "",
        "## 2. Common-Sense Deductions",
        "",
        "- Overnight extremes are tested often enough to study acceptance/rejection.",
        "- First-5m direction is only weakly persistent; blind continuation is unlikely.",
        "- Point thresholds are invalid across eras — normalize by ONR/ATR.",
        "- Any accept/reject edge must be measured **after** confirmation, not during the labeling window.",
        "",
        "## 3. Candidate Phenomena (causal)",
        "",
        "| Rank | ID | n | Score | Strict | IS h15 win/mean | Val | OOS |",
        "|------|----|---|-------|--------|-----------------|-----|-----|",
    ]
    for i, r in enumerate(rankings, 1):
        L.append(
            f"| {i} | `{r['id']}` | {r['n']} | {r['score']:.1f} | {r['survives_strict']} | "
            f"{r['IS_h15'].get('win_p', float('nan')):.3f}/{r['IS_h15'].get('mean', float('nan')):.2f} | "
            f"{r['Val_h15'].get('win_p', float('nan')):.3f} | {r['OOS_h15'].get('win_p', float('nan')):.3f} |"
        )
    L += ["", "### Sanity: IS h5 vs h15 win (causal should not show tautological h5)", "", "| ID | h5 win | h15 win | h15 mean | h15/ONR |", "|----|--------|---------|----------|---------|"]
    for k, c in report.get("contamination_check", {}).items():
        L.append(
            f"| {k} | {c.get('h5_win')} | {c.get('h15_win')} | {c.get('h15_mean')} | {c.get('h15_onr')} |"
        )
    L += ["", "## 4. Falsification", ""]
    for f in falsified:
        L.append(f"- **{f['id']}**: {f['why']}")
    L += ["", "## 5. Surviving Phenomena", ""]
    if survivors:
        for s in survivors:
            L.append(
                f"- **{s['id']}**: win IS/Val/OOS = "
                f"{s['IS_h15'].get('win_p', float('nan')):.3f}/"
                f"{s['Val_h15'].get('win_p', float('nan')):.3f}/"
                f"{s['OOS_h15'].get('win_p', float('nan')):.3f}; mean = "
                f"{s['IS_h15'].get('mean', float('nan')):.2f}/"
                f"{s['Val_h15'].get('mean', float('nan')):.2f}/"
                f"{s['OOS_h15'].get('mean', float('nan')):.2f} pts."
            )
    else:
        L.append("**None** under strict causal criteria.")
        if soft:
            L.append("Soft same-sign: " + ", ".join(f"`{x['id']}`" for x in soft[:8]))
    L += ["", "## 6–7. Strategy & Performance", ""]
    if strategy.get("built"):
        p = strategy["performance"]
        L.append(
            f"From `{strategy['based_on']}` (diagnostic_only={strategy.get('diagnostic_only')}). "
            f"Next-bar entry post-confirm; stop-first; costs {SLIP}pt/side + {COMM}pt RT."
        )
        L.append("")
        L.append(
            f"- N={p['n']}, WR={100*p['win_rate']:.1f}%, PF={p['profit_factor']}, "
            f"E[R]={p['expectancy_R']:.3f}, totalR={p['total_R']:.1f}, maxDD={p['max_drawdown_R']:.1f}R, "
            f"medianR={p['median_R']:.3f}, avgPts={p['avg_pts']:.2f}, trades/day={p['trades_per_day']:.2f}."
        )
        L.append(f"- MAE/MFE: {p['avg_mae']:.1f}/{p['avg_mfe']:.1f}. Ambiguous: {100*p['ambiguous_pct']:.1f}%.")
        L += ["", "| Split | n | WR | E[R] | Total R | Avg pts | PF |", "|-------|---|----|------|---------|---------|----|"]
        for sp in ("IS", "Validation", "OOS"):
            s = p["by_split"].get(sp, {})
            if not s.get("n"):
                continue
            L.append(
                f"| {sp} | {s['n']} | {100*s['win_rate']:.1f}% | {s['expectancy_R']:.3f} | "
                f"{s['total_R']:.1f} | {s['avg_pts']:.2f} | {s.get('pf')} |"
            )
        L += ["", "| Year | n | Total R | Avg R | WR |", "|------|---|---------|-------|----|"]
        for y in p.get("yearly", []):
            L.append(
                f"| {y['year']} | {y['n']} | {y['total_R']:.1f} | {y['avg_R']:.3f} | {100*y['win_rate']:.1f}% |"
            )
        L.append(f"\n2025/2026: `{p.get('y2025_2026')}`")
        L.append(f"OOS by weekday: `{p.get('oos_by_dow')}`")
        L.append(f"Monthly profitability rate: {100*p.get('monthly_profitability_pct', 0):.0f}%.")
    else:
        L.append("No strategy built.")
    L += ["", "## 8. Final Verdict", "", f"**{v['code']} — {v['text']}**", ""]
    return "\n".join(L)


def main() -> None:
    print("=== FAST CAUSAL RETEST ===", flush=True)
    day_df = pd.read_parquet(art("ny_open_day_facts.parquet"))
    large_th = float(day_df.loc[day_df["split"] == "IS", "impulse_ext_onr"].quantile(0.66))
    print(f"days={len(day_df)} large_th={large_th:.4f}", flush=True)

    print("load NQ...", flush=True)
    df = load_nq()
    print("slice day arrays...", flush=True)
    days = build_day_arrays(df, day_df)
    print(f"day arrays: {len(days)}", flush=True)

    print("levels...", flush=True)
    level_ev = causal_levels(days)
    print(f"level events={len(level_ev)}", flush=True)

    print("impulse...", flush=True)
    cont_ev, fail_ev = causal_impulse(days, large_th)
    print(f"cont={len(cont_ev)} fail={len(fail_ev)}", flush=True)

    gap_ev = causal_gap(days)
    base = aggregate(unconditional(days, 15))
    print("baseline h15 long:", base["ALL"]["h15"], flush=True)

    results = {}
    rankings = []

    def add(name, rows):
        results[name] = aggregate(rows)
        rankings.append({"id": name, "n": len(rows), **score(results[name])})

    add("A_large_impulse_continuation", [e for e in cont_ev if e["large"]])
    add("A_any_impulse_continuation", cont_ev)
    add("B_large_failed_impulse_reversal", [e for e in fail_ev if e["large"]])
    add("B_any_failed_impulse_reversal", fail_ev)
    for ln in ("ONH", "ONL", "PDH", "PDL"):
        for oc in ("accept", "reject"):
            add(f"C_{ln}_{oc}", [e for e in level_ev if e["level_name"] == ln and e["outcome"] == oc])
    add("E_gap_through_reclaim", gap_ev)

    rankings = sorted(rankings, key=lambda r: r["score"], reverse=True)
    survivors = [r for r in rankings if r["survives_strict"]]
    soft = [r for r in rankings if r["same_sign_means"] and not r["survives_strict"]]

    print("SURVIVORS:", [r["id"] for r in survivors], flush=True)
    for r in rankings:
        print(
            f"  {r['id']}: strict={r['survives_strict']} score={r['score']:.1f} "
            f"IS {r['IS_h15'].get('win_p', float('nan')):.3f}/{r['IS_h15'].get('mean', float('nan')):.2f} "
            f"Val {r['Val_h15'].get('win_p', float('nan')):.3f} OOS {r['OOS_h15'].get('win_p', float('nan')):.3f} n={r['n']}",
            flush=True,
        )

    contamination_check = {}
    for r in rankings[:8]:
        b = results[r["id"]]
        contamination_check[r["id"]] = {
            "h5_win": b["IS"].get("h5", {}).get("win_p"),
            "h15_win": b["IS"].get("h15", {}).get("win_p"),
            "h15_mean": b["IS"].get("h15", {}).get("mean"),
            "h15_onr": b["IS"].get("h15_onr", {}).get("mean"),
        }

    preferred = [
        "C_ONH_accept",
        "C_ONL_accept",
        "C_ONH_reject",
        "C_ONL_reject",
        "A_large_impulse_continuation",
        "B_large_failed_impulse_reversal",
        "E_gap_through_reclaim",
        "C_PDH_accept",
        "C_PDL_accept",
        "C_PDH_reject",
        "C_PDL_reject",
    ]
    chosen = None
    diagnostic = False
    for pid in preferred:
        hit = next((r for r in survivors if r["id"] == pid), None)
        if hit:
            chosen = hit
            break
    if chosen is None:
        for pid in preferred + [r["id"] for r in rankings]:
            hit = next((r for r in soft if r["id"] == pid), None)
            if hit:
                chosen = hit
                diagnostic = True
                break

    strategy: dict[str, Any] = {"built": False}
    if chosen is not None:
        cid = chosen["id"]
        print(f"strategy from {cid} diagnostic={diagnostic}", flush=True)
        if cid.startswith("C_") and "accept" in cid:
            ln = cid.split("_")[1]
            pool = [e for e in level_ev if e["outcome"] == "accept" and e["level_name"] in ((ln,) if ln in ("ONH", "ONL", "PDH", "PDL") else ())]
            if ln in ("ONH", "ONL"):
                pool = [e for e in level_ev if e["outcome"] == "accept" and e["level_name"] in ("ONH", "ONL")]
            else:
                pool = [e for e in level_ev if e["outcome"] == "accept" and e["level_name"] in ("PDH", "PDL")]
            trades = strat_from_events(days, pool, cid)
        elif cid.startswith("C_") and "reject" in cid:
            ln = cid.split("_")[1]
            if ln in ("ONH", "ONL"):
                pool = [e for e in level_ev if e["outcome"] == "reject" and e["level_name"] in ("ONH", "ONL")]
            else:
                pool = [e for e in level_ev if e["outcome"] == "reject" and e["level_name"] in ("PDH", "PDL")]
            trades = strat_from_events(days, pool, cid)
        elif "continuation" in cid:
            pool = [e for e in cont_ev if e["large"]] if "large" in cid else cont_ev
            trades = strat_from_events(days, pool, cid)
        elif "reversal" in cid or "failed" in cid:
            pool = [e for e in fail_ev if e["large"]] if "large" in cid else fail_ev
            trades = strat_from_events(days, pool, cid)
        elif "gap" in cid:
            trades = strat_from_events(days, gap_ev, cid)
        else:
            trades = []
        if trades:
            strategy = {
                "built": True,
                "diagnostic_only": diagnostic,
                "based_on": cid,
                "performance": trade_perf(trades),
            }
            pd.DataFrame([asdict(t) for t in trades]).to_csv(
                art("ny_open_causal_strategy_trades.csv"), index=False
            )

    if survivors:
        if strategy.get("built") and not strategy.get("diagnostic_only"):
            oos = strategy["performance"]["by_split"].get("OOS", {})
            val = strategy["performance"]["by_split"].get("Validation", {})
            if (
                oos.get("n", 0) >= 40
                and oos.get("expectancy_R", -1) > 0.05
                and oos.get("win_rate", 0) > 0.52
                and val.get("expectancy_R", -1) > 0
            ):
                verdict, vtext = "A", "Demonstrated robust executable edge"
            else:
                verdict, vtext = (
                    "B",
                    "Promising but insufficient evidence — post-confirm conditional drift exists but fails executable R/cost tests",
                )
        else:
            verdict, vtext = "B", "Promising but insufficient evidence"
    elif soft:
        verdict, vtext = "C", "No demonstrated edge (soft same-sign only after causal correction)"
    else:
        verdict, vtext = "C", "No demonstrated edge"

    # If nothing real and strategy loses everywhere, prefer C even if soft
    if strategy.get("built"):
        is_p = strategy["performance"]["by_split"].get("IS", {})
        if is_p.get("expectancy_R", 0) < 0 and not survivors:
            verdict, vtext = "C", "No demonstrated edge"

    v1_note = {
        "status": "D — Invalid / contaminated / non-causal",
        "reason": (
            "First-pass accept/reject and pullback signals selected on future bars that overlapped "
            "the forward-return window (tautological 75–97% short-horizon win rates). "
            "Those results are discarded. This report uses post-confirmation next-bar entries only."
        ),
    }

    prior = json.load(open(art("ny_open_behavioral_report.json"), encoding="utf-8"))
    # phase1 may be nested in prior from v1 or already causal overwrite attempt
    phase1 = prior.get("phase1_behavioral_facts", {})
    if not phase1 and "phase1_behavioral_facts" in prior:
        phase1 = prior["phase1_behavioral_facts"]

    falsified = []
    for r in rankings:
        if r["survives_strict"]:
            continue
        why = []
        if not r["same_sign_means"]:
            why.append("mean sign unstable across splits")
        else:
            why.append("too weak for strict survival")
        if r["IS_h15"].get("n", 0) < 50:
            why.append(f"IS n={r['IS_h15'].get('n', 0)}")
        if r["IS_h15"].get("win_p", 0.5) < 0.55:
            why.append(f"IS win_p={r['IS_h15'].get('win_p', float('nan')):.3f}")
        falsified.append({"id": r["id"], "why": "; ".join(why)})

    report = {
        "meta": {
            "dataset": "nq_1m_continuous.parquet",
            "method": "causal_post_confirmation",
            "v1_discarded": v1_note,
            "splits": {"IS": "2010-2021", "Validation": "2022-2024", "OOS": "2025-2026"},
            "large_impulse_thresh_onr_IS_p66": large_th,
            "costs": {"slippage_per_side_pts": SLIP, "commission_rt_pts": COMM},
        },
        "phase1_behavioral_facts": phase1,
        "baseline_tod_plus15_long": base["ALL"]["h15"],
        "contamination_check": contamination_check,
        "results": results,
        "rankings": rankings,
        "survivors_strict": survivors,
        "soft_same_sign": soft,
        "falsified": falsified,
        "strategy": strategy,
        "verdict": {"code": verdict, "text": vtext},
    }

    with open(art("ny_open_causal_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    with open(art("ny_open_behavioral_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    md = render_md(report, rankings, survivors, soft, falsified, strategy, phase1, large_th, v1_note)
    (art("ny_open_behavioral_report.md")).write_text(md, encoding="utf-8")
    print("VERDICT:", verdict, vtext, flush=True)


if __name__ == "__main__":
    main()
