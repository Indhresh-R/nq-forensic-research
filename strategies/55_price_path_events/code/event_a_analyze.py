"""
Event A — Displacement → Retracement (Steps 1–2, optional trade).

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
    DISP_ATR_MULT,
    EXT_FRAC,
    H_WAIT,
    HORIZONS,
    MIN_IS,
    MIN_OOS,
    MIN_TRADES_SPLIT,
    MIN_VAL,
    PRIMARY_H,
    RESULTS,
    RETRACE_FRAC,
    S52_RESULTS,
    W,
)


def load_panel() -> pd.DataFrame:
    states = pd.read_parquet(S52_RESULTS / "market_states.parquet")
    feats = pd.read_parquet(
        S52_RESULTS / "market_state_features.parquet",
        columns=["ts", "open", "high", "low", "close", "atr_30"],
    )
    if len(states) != len(feats):
        raise RuntimeError("S52 length mismatch")
    panel = states.copy()
    for c in ("open", "high", "low", "close", "atr_30"):
        panel[c] = feats[c].to_numpy(np.float64)
    panel = panel.sort_values(["session_date", "ny_min"]).reset_index(drop=True)
    panel["split"] = [split_of(int(y)) for y in panel["session_year"].to_numpy()]
    return panel


def _window_ok(session, seg, ny, t0: int, back: int) -> bool:
    t_start = t0 - back
    if t_start < 0:
        return False
    if session[t0] != session[t_start] or seg[t0] != seg[t_start]:
        return False
    return bool(np.all(np.diff(ny[t_start : t0 + 1]) == 1))


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
    atr = panel["atr_30"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    eligible = panel["census_eligible"].to_numpy(bool)
    split = panel["split"].to_numpy(dtype=object)
    year = panel["session_year"].to_numpy(np.int16)
    n = len(panel)

    # segment-local lag-W close and continuity (ny advances by W)
    close_lag = np.full(n, np.nan)
    win_ok = np.zeros(n, dtype=bool)
    # process per segment for correct shift
    for _, idx in panel.groupby("segment_id", sort=False).indices.items():
        ix = np.asarray(idx, dtype=np.int64)
        ix.sort()
        c = close[ix]
        ny_s = ny[ix]
        lag = np.full(len(ix), np.nan)
        ok = np.zeros(len(ix), dtype=bool)
        if len(ix) > W:
            lag[W:] = c[:-W]
            # contiguous W steps inside segment
            ok[W:] = ny_s[W:] == ny_s[:-W] + W
        close_lag[ix] = lag
        win_ok[ix] = ok

    disp = close - close_lag
    atr_ok = np.isfinite(atr) & (atr > 0) & np.isfinite(disp) & win_ok
    thr_met = np.zeros(n, dtype=bool)
    thr_met[atr_ok] = np.abs(disp[atr_ok]) >= DISP_ATR_MULT * atr[atr_ok]

    thr_prev = np.zeros(n, dtype=bool)
    thr_prev[1:] = thr_met[:-1]
    # onset: thr now, not thr prev; RTH eligible at t0
    onset = thr_met & (~thr_prev) & eligible

    funnel = {
        "n_onset_displacements": int(onset.sum()),
        "n_events": 0,
        "n_censored_no_retrace": 0,
    }

    rows = []
    onset_idx = np.flatnonzero(onset)
    for t0 in onset_idx:
        impulse_net = float(disp[t0])
        if impulse_net == 0.0:
            continue
        direction = 1 if impulse_net > 0 else -1
        p0 = float(close_lag[t0])
        p1 = float(close[t0])
        span = abs(p1 - p0)
        L = p1 - RETRACE_FRAC * (p1 - p0)
        found = False
        t_event = -1
        for j in range(1, H_WAIT + 1):
            tj = t0 + j
            if tj >= n or not _fwd_ok(session, seg, ny, t0, j):
                break
            if direction > 0:
                if low[tj] <= L:
                    found = True
                    t_event = tj
                    break
            else:
                if high[tj] >= L:
                    found = True
                    t_event = tj
                    break
        if not found or not eligible[t_event]:
            funnel["n_censored_no_retrace"] += 1
            continue
        funnel["n_events"] += 1
        ext_level = p1 + direction * EXT_FRAC * span
        rows.append(
            {
                "event_id": f"{session[t_event]}_{int(ny[t_event])}_{t0}",
                "t0": int(t0),
                "event_idx": int(t_event),
                "wait_retrace": int(t_event - t0),
                "direction": int(direction),
                "origin": p0,
                "impulse_end": p1,
                "impulse_span": span,
                "L": float(L),
                "ext_level": float(ext_level),
                "atr_t0": float(atr[t0]),
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
        d = int(ev.direction)
        origin = float(ev.origin)
        imp_end = float(ev.impulse_end)
        ext = float(ev.ext_level)
        for h in HORIZONS:
            valid = _fwd_ok(session, seg, ny, t, h)
            rec = {
                "event_id": ev.event_id,
                "horizon": h,
                "valid": bool(valid),
                "split": ev.split,
                "direction": d,
                "session_year": ev.session_year,
            }
            if not valid:
                rows.append(rec)
                continue
            sl = slice(t + 1, t + h + 1)
            hi = high[sl]
            lo = low[sl]
            if d > 0:
                reach_origin = bool(np.any(lo <= origin))
                reach_end = bool(np.any(hi >= imp_end))
                reach_ext = bool(np.any(hi >= ext))
            else:
                reach_origin = bool(np.any(hi >= origin))
                reach_end = bool(np.any(lo <= imp_end))
                reach_ext = bool(np.any(lo <= ext))
            rec.update(
                {
                    "reach_origin": reach_origin,
                    "reach_impulse_end": reach_end,
                    "reach_extension": reach_ext,
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
                        "p_origin": np.nan,
                        "p_impulse_end": np.nan,
                        "p_extension": np.nan,
                        "delta_ext_minus_origin": np.nan,
                    }
                )
                continue
            p_o = float(g["reach_origin"].mean())
            p_e = float(g["reach_impulse_end"].mean())
            p_x = float(g["reach_extension"].mean())
            rows.append(
                {
                    "horizon": h,
                    "split": split,
                    "n_valid": n,
                    "p_origin": p_o,
                    "p_impulse_end": p_e,
                    "p_extension": p_x,
                    "delta_ext_minus_origin": p_x - p_o,
                }
            )
    return pd.DataFrame(rows)


def classify_steps(summary: pd.DataFrame) -> dict:
    def row(split: str, h: int = PRIMARY_H):
        m = summary.loc[(summary["split"] == split) & (summary["horizon"] == h)]
        return None if m.empty else m.iloc[0]

    is_r = row("IS")
    val_r = row("Validation")
    oos_r = row("OOS")

    detail = {}
    for name, r in (("IS", is_r), ("Validation", val_r), ("OOS", oos_r)):
        if r is None:
            detail[name] = {"ok": False, "reason": "missing"}
            continue
        detail[name] = {
            "n_valid": int(r["n_valid"]),
            "p_origin": float(r["p_origin"]),
            "p_extension": float(r["p_extension"]),
            "delta": float(r["delta_ext_minus_origin"]),
        }

    # Step 1
    if is_r is None or int(is_r["n_valid"]) < MIN_IS:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "IS_sample_or_missing",
            "detail": detail,
            "advance_to_trade": False,
        }
    d_is = float(is_r["delta_ext_minus_origin"])
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

    # Step 2 Val
    if val_r is None or int(val_r["n_valid"]) < MIN_VAL:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "VAL_sample",
            "detail": detail,
            "advance_to_trade": False,
            "delta_is": d_is,
        }
    d_val = float(val_r["delta_ext_minus_origin"])
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

    # OOS for advance to trade
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
    d_oos = float(oos_r["delta_ext_minus_origin"])
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
        "trade_side_rule": "with_impulse" if sign_is > 0 else "against_impulse",
        "sign_is": sign_is,
    }


def path_feasibility(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Optional Step 3 — descriptive only."""
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
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
        d_imp = int(ev.direction)
        # with impulse if sign_is>0 else against
        side = d_imp if sign_is > 0 else -d_imp
        if not _fwd_ok(session, seg, ny, t, hold):
            continue
        entry_i = t + 1
        if entry_i >= n or not _fwd_ok(session, seg, ny, t, 1):
            continue
        entry = float(open_[entry_i])
        exit_px = float(close[t + hold])
        gross = side * (exit_px - entry)
        net = gross - COST_RT
        rows.append(
            {
                "event_id": ev.event_id,
                "split": ev.split,
                "session_year": ev.session_year,
                "side": side,
                "impulse_direction": d_imp,
                "entry_price": entry,
                "exit_price": exit_px,
                "gross_pts": gross,
                "net_pts": net,
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
        passed = bool(row["eligible"]) and np.isfinite(row["mean_net"]) and float(row["mean_net"]) > 0
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

    print("Extracting Event A…", flush=True)
    events, funnel = extract_events(panel)
    events.to_parquet(RESULTS / "event_a_events.parquet", index=False)
    (RESULTS / "event_a_funnel.json").write_text(
        json.dumps(funnel, indent=2), encoding="utf-8"
    )
    print(f"funnel={funnel}", flush=True)

    print("Destinations…", flush=True)
    dest = measure_destinations(panel, events)
    dest.to_parquet(RESULTS / "event_a_dest_paths.parquet", index=False)
    summary = summarize_destinations(dest)
    summary.to_csv(RESULTS / "event_a_destinations.csv", index=False)

    verdict = classify_steps(summary)
    print(
        f"Step1/2: {verdict['classification']} stage={verdict.get('stage')} "
        f"reason={verdict.get('reason')}",
        flush=True,
    )

    # Optional step 3 always as descriptive if we have events
    feas = path_feasibility(panel, events)
    feas.to_csv(RESULTS / "event_a_path_feasibility.csv", index=False)

    trade_verdict = None
    if verdict.get("advance_to_trade"):
        print("Running frozen trade…", flush=True)
        trades = run_trades(panel, events, int(verdict["sign_is"]))
        trades.to_parquet(RESULTS / "event_a_trades.parquet", index=False)
        tsum = summarize_trades(trades)
        tsum.to_csv(RESULTS / "event_a_trade_summary.csv", index=False)
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

    (RESULTS / "event_a_step1_2_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
