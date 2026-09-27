"""
Event B — Range break → failed return (Steps 1–2, optional trade).

Frozen definitions only. No retuning.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from common.splits import split_of

from constants import (
    COST_RT,
    DELTA_IS_MIN,
    DELTA_VAL_MIN,
    H_WAIT,
    HORIZONS,
    MIN_IS,
    MIN_OOS,
    MIN_TRADES_SPLIT,
    MIN_VAL,
    PRIMARY_H,
    REBREAK_FRAC,
    RESULTS,
    S52_RESULTS,
    W,
)


def load_panel() -> pd.DataFrame:
    states = pd.read_parquet(S52_RESULTS / "market_states.parquet")
    feats = pd.read_parquet(
        S52_RESULTS / "market_state_features.parquet",
        columns=["ts", "open", "high", "low", "close"],
    )
    if len(states) != len(feats):
        raise RuntimeError("S52 length mismatch")
    panel = states.copy()
    for c in ("open", "high", "low", "close"):
        panel[c] = feats[c].to_numpy(np.float64)
    panel = panel.sort_values(["session_date", "ny_min"]).reset_index(drop=True)
    panel["split"] = [split_of(int(y)) for y in panel["session_year"].to_numpy()]
    return panel


def _fwd_ok(session, seg, ny, t: int, h: int) -> bool:
    n = len(session)
    th = t + h
    if th >= n:
        return False
    if session[th] != session[t] or seg[th] != seg[t]:
        return False
    return bool(ny[th] == ny[t] + h)


def extract_events(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    eligible = panel["census_eligible"].to_numpy(bool)
    split = panel["split"].to_numpy(dtype=object)
    year = panel["session_year"].to_numpy(np.int16)
    n = len(panel)

    # segment-local rolling max/min of prior W bars (shift 1 = window ending at t-1)
    rh = np.full(n, np.nan)
    rl = np.full(n, np.nan)
    win_ok = np.zeros(n, dtype=bool)
    for _, idx in panel.groupby("segment_id", sort=False).indices.items():
        ix = np.asarray(idx, dtype=np.int64)
        ix.sort()
        h = high[ix]
        l = low[ix]
        ny_s = ny[ix]
        # rolling max/min over W bars then shift 1 so value at i uses i-W..i-1
        rmax = pd.Series(h).rolling(W, min_periods=W).max().shift(1).to_numpy()
        rmin = pd.Series(l).rolling(W, min_periods=W).min().shift(1).to_numpy()
        ok = np.zeros(len(ix), dtype=bool)
        if len(ix) > W:
            # continuity: ny[i] == ny[i-W] + W
            ok[W:] = ny_s[W:] == ny_s[:-W] + W
        rh[ix] = rmax
        rl[ix] = rmin
        win_ok[ix] = ok & np.isfinite(rmax) & np.isfinite(rmin) & ((rmax - rmin) > 0)

    up_break = win_ok & eligible & (close > rh)
    dn_break = win_ok & eligible & (close < rl)
    # onset: prior close inside this range
    prev_close = np.roll(close, 1)
    prev_ok = np.zeros(n, dtype=bool)
    prev_ok[1:] = (
        (session[1:] == session[:-1])
        & (seg[1:] == seg[:-1])
        & (ny[1:] == ny[:-1] + 1)
    )
    up_onset = up_break & prev_ok & (prev_close <= rh)
    dn_onset = dn_break & prev_ok & (prev_close >= rl)

    funnel = {
        "n_break_onsets": int(up_onset.sum() + dn_onset.sum()),
        "n_up": int(up_onset.sum()),
        "n_down": int(dn_onset.sum()),
        "n_events": 0,
        "n_censored_no_return": 0,
    }

    rows = []
    for direction, mask in ((1, up_onset), (-1, dn_onset)):
        for tb in np.flatnonzero(mask):
            r_high = float(rh[tb])
            r_low = float(rl[tb])
            R = r_high - r_low
            mid = 0.5 * (r_high + r_low)
            found = False
            t_event = -1
            for j in range(1, H_WAIT + 1):
                tj = tb + j
                if tj >= n or not _fwd_ok(session, seg, ny, tb, j):
                    break
                if direction > 0:
                    if low[tj] <= r_high:
                        found = True
                        t_event = tj
                        break
                else:
                    if high[tj] >= r_low:
                        found = True
                        t_event = tj
                        break
            if not found or not eligible[t_event]:
                funnel["n_censored_no_return"] += 1
                continue
            funnel["n_events"] += 1
            if direction > 0:
                rebreak_lvl = r_high + REBREAK_FRAC * R
            else:
                rebreak_lvl = r_low - REBREAK_FRAC * R
            rows.append(
                {
                    "event_id": f"{session[t_event]}_{int(ny[t_event])}_{tb}",
                    "tb": int(tb),
                    "event_idx": int(t_event),
                    "wait_return": int(t_event - tb),
                    "break_dir": int(direction),
                    "R_high": r_high,
                    "R_low": r_low,
                    "R": R,
                    "mid": mid,
                    "rebreak_level": float(rebreak_lvl),
                    "split": split[t_event],
                    "session_date": session[t_event],
                    "session_year": int(year[t_event]),
                }
            )
    return pd.DataFrame(rows), funnel


def measure_destinations(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)

    rows = []
    for ev in events.itertuples(index=False):
        t = int(ev.event_idx)
        d = int(ev.break_dir)
        r_high = float(ev.R_high)
        r_low = float(ev.R_low)
        mid = float(ev.mid)
        rebreak = float(ev.rebreak_level)
        for h in HORIZONS:
            valid = _fwd_ok(session, seg, ny, t, h) and (t + h < n)
            rec = {
                "event_id": ev.event_id,
                "horizon": h,
                "valid": bool(valid),
                "split": ev.split,
                "break_dir": d,
                "session_year": ev.session_year,
            }
            if not valid:
                rows.append(rec)
                continue
            sl = slice(t + 1, t + h + 1)
            hi = high[sl]
            lo = low[sl]
            if d > 0:
                reach_opposite = bool(np.any(lo <= r_low))
                reach_mid = bool(np.any(lo <= mid))
                rebreak_outside = bool(np.any(hi >= rebreak))
            else:
                reach_opposite = bool(np.any(hi >= r_high))
                reach_mid = bool(np.any(hi >= mid))
                rebreak_outside = bool(np.any(lo <= rebreak))
            rec.update(
                {
                    "reach_opposite": reach_opposite,
                    "reach_mid": reach_mid,
                    "rebreak_outside": rebreak_outside,
                }
            )
            rows.append(rec)
    return pd.DataFrame(rows)


def summarize_destinations(dest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h in HORIZONS:
        for split in ("IS", "Validation", "OOS", "ALL"):
            g = dest.loc[(dest["horizon"] == h) & (dest["valid"])]
            if split != "ALL":
                g = g.loc[g["split"] == split]
            n = len(g)
            if n == 0:
                rows.append(
                    {
                        "horizon": h,
                        "split": split,
                        "n_valid": 0,
                        "p_opposite": np.nan,
                        "p_mid": np.nan,
                        "p_rebreak": np.nan,
                        "delta_opp_minus_rebreak": np.nan,
                    }
                )
                continue
            p_o = float(g["reach_opposite"].mean())
            p_m = float(g["reach_mid"].mean())
            p_r = float(g["rebreak_outside"].mean())
            rows.append(
                {
                    "horizon": h,
                    "split": split,
                    "n_valid": n,
                    "p_opposite": p_o,
                    "p_mid": p_m,
                    "p_rebreak": p_r,
                    "delta_opp_minus_rebreak": p_o - p_r,
                }
            )
    return pd.DataFrame(rows)


def classify_steps(summary: pd.DataFrame) -> dict:
    def row(split: str, h: int = PRIMARY_H):
        m = summary.loc[(summary["split"] == split) & (summary["horizon"] == h)]
        return None if m.empty else m.iloc[0]

    is_r, val_r, oos_r = row("IS"), row("Validation"), row("OOS")
    detail = {}
    for name, r in (("IS", is_r), ("Validation", val_r), ("OOS", oos_r)):
        if r is None:
            detail[name] = {"ok": False, "reason": "missing"}
            continue
        detail[name] = {
            "n_valid": int(r["n_valid"]),
            "p_opposite": float(r["p_opposite"]),
            "p_rebreak": float(r["p_rebreak"]),
            "p_mid": float(r["p_mid"]),
            "delta": float(r["delta_opp_minus_rebreak"]),
        }

    if is_r is None or int(is_r["n_valid"]) < MIN_IS:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "IS_sample_or_missing",
            "detail": detail,
            "advance_to_trade": False,
        }
    d_is = float(is_r["delta_opp_minus_rebreak"])
    if not np.isfinite(d_is) or abs(d_is) < DELTA_IS_MIN:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "IS_asymmetry_not_material",
            "detail": detail,
            "advance_to_trade": False,
            "delta_is": d_is,
        }
    sign_is = 1 if d_is > 0 else -1

    if val_r is None or int(val_r["n_valid"]) < MIN_VAL:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "VAL_sample",
            "detail": detail,
            "advance_to_trade": False,
            "delta_is": d_is,
        }
    d_val = float(val_r["delta_opp_minus_rebreak"])
    sign_val = 0 if not np.isfinite(d_val) or d_val == 0 else (1 if d_val > 0 else -1)
    if sign_val != sign_is or abs(d_val) < DELTA_VAL_MIN:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "VAL_sign_or_magnitude",
            "detail": detail,
            "advance_to_trade": False,
            "delta_is": d_is,
            "delta_val": d_val,
        }

    if oos_r is None or int(oos_r["n_valid"]) < MIN_OOS:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "OOS_sample",
            "detail": detail,
            "advance_to_trade": False,
            "delta_is": d_is,
            "delta_val": d_val,
        }
    d_oos = float(oos_r["delta_opp_minus_rebreak"])
    sign_oos = 0 if not np.isfinite(d_oos) or d_oos == 0 else (1 if d_oos > 0 else -1)
    if sign_oos != sign_is:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "OOS_sign_flip",
            "detail": detail,
            "advance_to_trade": False,
            "delta_is": d_is,
            "delta_val": d_val,
            "delta_oos": d_oos,
        }

    return {
        "classification": "ADVANCE_TO_TRADE",
        "stage": "STEP2",
        "reason": "IS_VAL_OOS_stable",
        "detail": detail,
        "advance_to_trade": True,
        "delta_is": d_is,
        "sign_is": sign_is,
        # Δ>0: opposite more likely → fade break (up break → short)
        "trade_side_rule": "toward_opposite" if sign_is > 0 else "toward_rebreak",
    }


def path_feasibility(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    rows = []
    for h in (5, 15):
        ranges = []
        for ev in events.itertuples(index=False):
            t = int(ev.event_idx)
            if not _fwd_ok(session, seg, ny, t, h):
                continue
            sl = slice(t + 1, t + h + 1)
            ranges.append(float(high[sl].max() - low[sl].min()))
        arr = np.asarray(ranges, float)
        rows.append(
            {
                "horizon": h,
                "n": len(arr),
                "median_hl_range": float(np.median(arr)) if len(arr) else np.nan,
                "p25": float(np.quantile(arr, 0.25)) if len(arr) else np.nan,
                "p75": float(np.quantile(arr, 0.75)) if len(arr) else np.nan,
                "cost_rt": COST_RT,
            }
        )
    return pd.DataFrame(rows)


def run_trades(panel: pd.DataFrame, events: pd.DataFrame, sign_is: int) -> pd.DataFrame:
    open_ = panel["open"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)
    hold = 15
    rows = []
    for ev in events.itertuples(index=False):
        t = int(ev.event_idx)
        d = int(ev.break_dir)
        # sign_is>0 → toward opposite: trade against break_dir
        side = -d if sign_is > 0 else d
        if not _fwd_ok(session, seg, ny, t, hold):
            continue
        entry_i = t + 1
        if entry_i >= n or not _fwd_ok(session, seg, ny, t, 1):
            continue
        entry = float(open_[entry_i])
        exit_px = float(close[t + hold])
        gross = side * (exit_px - entry)
        rows.append(
            {
                "event_id": ev.event_id,
                "split": ev.split,
                "session_year": ev.session_year,
                "side": side,
                "break_dir": d,
                "entry_price": entry,
                "exit_price": exit_px,
                "gross_pts": gross,
                "net_pts": gross - COST_RT,
            }
        )
    return pd.DataFrame(rows)


def summarize_trades(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        g = trades if split == "ALL" else trades.loc[trades["split"] == split]
        n = len(g)
        rows.append(
            {
                "split": split,
                "n_trades": n,
                "mean_gross": float(g["gross_pts"].mean()) if n else np.nan,
                "mean_net": float(g["net_pts"].mean()) if n else np.nan,
                "median_net": float(g["net_pts"].median()) if n else np.nan,
                "hit_rate": float((g["net_pts"] > 0).mean()) if n else np.nan,
                "eligible": n >= MIN_TRADES_SPLIT,
            }
        )
    return pd.DataFrame(rows)


def classify_trade(tsum: pd.DataFrame) -> dict:
    ok = True
    detail = {}
    for sp in ("IS", "Validation", "OOS"):
        r = tsum.loc[tsum["split"] == sp]
        if r.empty:
            ok = False
            detail[sp] = {"pass": False}
            continue
        row = r.iloc[0]
        passed = (
            bool(row["eligible"])
            and np.isfinite(row["mean_net"])
            and float(row["mean_net"]) > 0
        )
        detail[sp] = {
            "n_trades": int(row["n_trades"]),
            "mean_net": float(row["mean_net"]),
            "pass": passed,
        }
        if not passed:
            ok = False
    return {
        "classification": "ADVANCE" if ok else "KILL",
        "stage": "TRADE",
        "detail": detail,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading panel…", flush=True)
    panel = load_panel()

    print("Extracting Event B…", flush=True)
    events, funnel = extract_events(panel)
    events.to_parquet(RESULTS / "event_b_events.parquet", index=False)
    (RESULTS / "event_b_funnel.json").write_text(
        json.dumps(funnel, indent=2), encoding="utf-8"
    )
    print(f"funnel={funnel}", flush=True)

    print("Destinations…", flush=True)
    dest = measure_destinations(panel, events)
    dest.to_parquet(RESULTS / "event_b_dest_paths.parquet", index=False)
    summary = summarize_destinations(dest)
    summary.to_csv(RESULTS / "event_b_destinations.csv", index=False)

    verdict = classify_steps(summary)
    print(
        f"Step1/2: {verdict['classification']} stage={verdict.get('stage')} "
        f"reason={verdict.get('reason')}",
        flush=True,
    )

    feas = path_feasibility(panel, events)
    feas.to_csv(RESULTS / "event_b_path_feasibility.csv", index=False)

    if verdict.get("advance_to_trade"):
        print("Running frozen trade…", flush=True)
        trades = run_trades(panel, events, int(verdict["sign_is"]))
        trades.to_parquet(RESULTS / "event_b_trades.parquet", index=False)
        tsum = summarize_trades(trades)
        tsum.to_csv(RESULTS / "event_b_trade_summary.csv", index=False)
        trade_verdict = classify_trade(tsum)
        print(f"Trade: {trade_verdict['classification']}", flush=True)
        verdict["trade"] = trade_verdict
        if trade_verdict["classification"] == "KILL":
            verdict["classification"] = "KILL"
            verdict["final"] = "KILL_AFTER_TRADE"
        else:
            verdict["final"] = "ADVANCE"
    else:
        verdict["final"] = "KILL"
        verdict["trade"] = None

    (RESULTS / "event_b_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
