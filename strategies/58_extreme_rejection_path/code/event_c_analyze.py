"""
Event C — Extreme excursion → rejection (destination → path → optional trade).

Frozen definitions only. No retuning. No Event A/B rescue.
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
    K,
    MIN_IS,
    MIN_OOS,
    MIN_TRADES_SPLIT,
    MIN_VAL,
    PRIMARY_H,
    RESULTS,
    RETRACE_FRAC,
    S52_RESULTS,
    THROUGH_FRAC,
    TRADE_H,
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

    close_lag = np.full(n, np.nan)
    win_ok = np.zeros(n, dtype=bool)
    for _, idx in panel.groupby("segment_id", sort=False).indices.items():
        ix = np.asarray(idx, dtype=np.int64)
        ix.sort()
        c = close[ix]
        ny_s = ny[ix]
        lag = np.full(len(ix), np.nan)
        ok = np.zeros(len(ix), dtype=bool)
        if len(ix) > W:
            lag[W:] = c[:-W]
            ok[W:] = ny_s[W:] == ny_s[:-W] + W
        close_lag[ix] = lag
        win_ok[ix] = ok

    disp = close - close_lag
    atr_ok = np.isfinite(atr) & (atr > 0) & np.isfinite(disp) & win_ok
    thr_met = np.zeros(n, dtype=bool)
    thr_met[atr_ok] = np.abs(disp[atr_ok]) >= K * atr[atr_ok]

    # prior clear per prereg: |disp[t-1]| < K*atr[t-1] (or atr invalid → eligible)
    cont = np.zeros(n, dtype=bool)
    cont[1:] = (
        (session[1:] == session[:-1])
        & (seg[1:] == seg[:-1])
        & (ny[1:] == ny[:-1] + 1)
    )
    atr_p = np.roll(atr, 1)
    disp_p = np.roll(disp, 1)
    win_p = np.roll(win_ok, 1)
    atr_p_ok = np.isfinite(atr_p) & (atr_p > 0) & win_p & np.isfinite(disp_p)
    prior_under = np.zeros(n, dtype=bool)
    prior_under[atr_p_ok] = np.abs(disp_p[atr_p_ok]) < K * atr_p[atr_p_ok]
    prior_clear = cont & (prior_under | (~atr_p_ok))
    prior_clear[0] = False

    onset = thr_met & prior_clear & eligible

    funnel = {
        "n_onset_excursions": int(onset.sum()),
        "n_events": 0,
        "n_censored_no_rejection": 0,
    }

    rows = []
    for te in np.flatnonzero(onset):
        excursion = float(disp[te])
        if excursion == 0.0:
            continue
        ext_dir = 1 if excursion > 0 else -1
        anchor = float(close_lag[te])
        extreme = float(close[te])
        span = abs(extreme - anchor)
        if not (np.isfinite(span) and span > 0):
            continue
        L = extreme - RETRACE_FRAC * (extreme - anchor)
        found = False
        t_event = -1
        for j in range(1, H_WAIT + 1):
            tj = te + j
            if tj >= n or not _fwd_ok(session, seg, ny, te, j):
                break
            if ext_dir > 0:
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
            funnel["n_censored_no_rejection"] += 1
            continue
        funnel["n_events"] += 1
        through_lvl = anchor - ext_dir * THROUGH_FRAC * span
        side = -ext_dir
        rows.append(
            {
                "event_id": f"{session[t_event]}_{int(ny[t_event])}_{te}",
                "te": int(te),
                "event_idx": int(t_event),
                "wait_reject": int(t_event - te),
                "ext_dir": int(ext_dir),
                "side": int(side),
                "anchor": anchor,
                "extreme": extreme,
                "span": span,
                "L": float(L),
                "through_level": float(through_lvl),
                "atr_te": float(atr[te]),
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
        d = int(ev.ext_dir)
        anchor = float(ev.anchor)
        extreme = float(ev.extreme)
        through = float(ev.through_level)
        for h in HORIZONS:
            valid = _fwd_ok(session, seg, ny, t, h) and (t + h < n)
            rec = {
                "event_id": ev.event_id,
                "horizon": h,
                "valid": bool(valid),
                "split": ev.split,
                "ext_dir": d,
                "session_year": int(ev.session_year),
            }
            if not valid:
                rows.append(rec)
                continue
            sl = slice(t + 1, t + h + 1)
            hi = high[sl]
            lo = low[sl]
            if d > 0:
                reach_anchor = bool(np.any(lo <= anchor))
                reach_extreme = bool(np.any(hi >= extreme))
                reach_through = bool(np.any(lo <= through))
            else:
                reach_anchor = bool(np.any(hi >= anchor))
                reach_extreme = bool(np.any(lo <= extreme))
                reach_through = bool(np.any(hi >= through))
            rec.update(
                {
                    "reach_anchor": reach_anchor,
                    "reach_extreme": reach_extreme,
                    "reach_through": reach_through,
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
                        "p_anchor": np.nan,
                        "p_extreme": np.nan,
                        "p_through": np.nan,
                        "delta_anchor_minus_extreme": np.nan,
                    }
                )
                continue
            p_a = float(g["reach_anchor"].mean())
            p_e = float(g["reach_extreme"].mean())
            p_t = float(g["reach_through"].mean())
            rows.append(
                {
                    "horizon": h,
                    "split": split,
                    "n_valid": n,
                    "p_anchor": p_a,
                    "p_extreme": p_e,
                    "p_through": p_t,
                    "delta_anchor_minus_extreme": p_a - p_e,
                }
            )
    return pd.DataFrame(rows)


def classify_destination(summary: pd.DataFrame) -> dict:
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
            "p_anchor": float(r["p_anchor"]),
            "p_extreme": float(r["p_extreme"]),
            "p_through": float(r["p_through"]),
            "delta": float(r["delta_anchor_minus_extreme"]),
        }

    if is_r is None or int(is_r["n_valid"]) < MIN_IS:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "IS_sample_or_missing",
            "detail": detail,
            "advance_to_path": False,
        }
    d_is = float(is_r["delta_anchor_minus_extreme"])
    if not np.isfinite(d_is) or d_is < DELTA_IS_MIN:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "IS_delta_not_material_or_wrong_sign",
            "detail": detail,
            "advance_to_path": False,
            "delta_is": d_is,
        }

    if val_r is None or int(val_r["n_valid"]) < MIN_VAL:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "VAL_sample",
            "detail": detail,
            "advance_to_path": False,
            "delta_is": d_is,
        }
    d_val = float(val_r["delta_anchor_minus_extreme"])
    if not np.isfinite(d_val) or d_val <= 0 or abs(d_val) < DELTA_VAL_MIN:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "VAL_sign_or_magnitude",
            "detail": detail,
            "advance_to_path": False,
            "delta_is": d_is,
            "delta_val": d_val,
        }

    if oos_r is None or int(oos_r["n_valid"]) < MIN_OOS:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "OOS_sample",
            "detail": detail,
            "advance_to_path": False,
            "delta_is": d_is,
            "delta_val": d_val,
        }
    d_oos = float(oos_r["delta_anchor_minus_extreme"])
    if not np.isfinite(d_oos) or d_oos <= 0:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "OOS_sign",
            "detail": detail,
            "advance_to_path": False,
            "delta_is": d_is,
            "delta_val": d_val,
            "delta_oos": d_oos,
        }

    return {
        "classification": "ADVANCE_TO_PATH",
        "stage": "STEP2",
        "reason": "IS_VAL_OOS_destination_ok",
        "detail": detail,
        "advance_to_path": True,
        "delta_is": d_is,
        "delta_val": d_val,
        "delta_oos": d_oos,
    }


def measure_paths(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)

    rows: list[dict] = []
    for ev in events.itertuples(index=False):
        t = int(ev.event_idx)
        side = int(ev.side)
        span = float(ev.span)
        anchor = float(ev.anchor)
        d = int(ev.ext_dir)
        c0 = float(close[t])
        first_anchor = None
        for j in range(1, 61):
            if not _fwd_ok(session, seg, ny, t, j):
                break
            tj = t + j
            if d > 0:
                hit = low[tj] <= anchor
            else:
                hit = high[tj] >= anchor
            if hit:
                first_anchor = j
                break

        for h in HORIZONS:
            valid = _fwd_ok(session, seg, ny, t, h) and (t + h < n) and span > 0
            rec: dict = {
                "event_id": ev.event_id,
                "horizon": h,
                "valid": bool(valid),
                "split": ev.split,
                "side": side,
                "session_year": int(ev.session_year),
                "first_anchor_bars": first_anchor if first_anchor is not None else pd.NA,
            }
            if not valid:
                rec.update(
                    {
                        "prog_close": np.nan,
                        "mfe_dir": np.nan,
                        "mae_dir": np.nan,
                        "hit_anchor": False,
                    }
                )
                rows.append(rec)
                continue
            sl = slice(t + 1, t + h + 1)
            hi = high[sl]
            lo = low[sl]
            c_h = float(close[t + h])
            prog = side * (c_h - c0) / span
            if side > 0:
                mfe = (float(np.max(hi)) - c0) / span
                mae = (c0 - float(np.min(lo))) / span
            else:
                mfe = (c0 - float(np.min(lo))) / span
                mae = (float(np.max(hi)) - c0) / span
            if d > 0:
                hit_a = bool(np.any(lo <= anchor))
            else:
                hit_a = bool(np.any(hi >= anchor))
            rec.update(
                {
                    "prog_close": float(prog),
                    "mfe_dir": float(mfe),
                    "mae_dir": float(mae),
                    "hit_anchor": hit_a,
                }
            )
            rows.append(rec)
    return pd.DataFrame(rows)


def summarize_paths(paths: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        for h in HORIZONS:
            g = paths.loc[(paths["horizon"] == h) & (paths["valid"])]
            if split != "ALL":
                g = g.loc[g["split"] == split]
            n = len(g)
            if n == 0:
                rows.append(
                    {
                        "split": split,
                        "horizon": h,
                        "n": 0,
                        "med": np.nan,
                        "mean": np.nan,
                        "p_pos": np.nan,
                        "med_mfe": np.nan,
                        "med_mae": np.nan,
                        "p_hit_anchor": np.nan,
                    }
                )
                continue
            pc = g["prog_close"].to_numpy(np.float64)
            rows.append(
                {
                    "split": split,
                    "horizon": h,
                    "n": n,
                    "med": float(np.nanmedian(pc)),
                    "mean": float(np.nanmean(pc)),
                    "p_pos": float(np.mean(pc > 0)),
                    "med_mfe": float(np.nanmedian(g["mfe_dir"].to_numpy(np.float64))),
                    "med_mae": float(np.nanmedian(g["mae_dir"].to_numpy(np.float64))),
                    "p_hit_anchor": float(g["hit_anchor"].mean()),
                }
            )
    return pd.DataFrame(rows)


def _meds(ladder: pd.DataFrame, split: str) -> dict[int, float]:
    out = {}
    for h in HORIZONS:
        m = ladder.loc[(ladder["split"] == split) & (ladder["horizon"] == h)]
        out[h] = float("nan") if m.empty else float(m.iloc[0]["med"])
    return out


def _ns(ladder: pd.DataFrame, split: str) -> dict[int, int]:
    out = {}
    for h in HORIZONS:
        m = ladder.loc[(ladder["split"] == split) & (ladder["horizon"] == h)]
        out[h] = 0 if m.empty else int(m.iloc[0]["n"])
    return out


def _mfe_mae_15(ladder: pd.DataFrame, split: str) -> tuple[float, float]:
    m = ladder.loc[(ladder["split"] == split) & (ladder["horizon"] == 15)]
    if m.empty:
        return float("nan"), float("nan")
    return float(m.iloc[0]["med_mfe"]), float(m.iloc[0]["med_mae"])


def mono_ok(meds: dict[int, float]) -> bool:
    vals = [meds[h] for h in HORIZONS]
    if any(not np.isfinite(v) for v in vals):
        return False
    return bool(vals[0] <= vals[1] <= vals[2] <= vals[3])


def classify_path(ladder: pd.DataFrame) -> dict:
    detail = {}
    for split, min_n in (("IS", MIN_IS), ("Validation", MIN_VAL), ("OOS", MIN_OOS)):
        ns = _ns(ladder, split)
        meds = _meds(ladder, split)
        mfe, mae = _mfe_mae_15(ladder, split)
        n_ok = all(ns[h] >= min_n for h in HORIZONS)
        mono = mono_ok(meds)
        end_ok = np.isfinite(meds[60]) and meds[60] > 0
        mid_ok = (np.isfinite(meds[15]) and meds[15] > 0) or (
            np.isfinite(meds[30]) and meds[30] > 0
        )
        mfe_ok = np.isfinite(mfe) and np.isfinite(mae) and mfe > mae
        detail[split] = {
            "n": ns,
            "med": {str(h): meds[h] for h in HORIZONS},
            "n_ok": n_ok,
            "mono": mono,
            "med60_pos": bool(end_ok),
            "mid_ladder_pos": bool(mid_ok),
            "med_mfe_15": mfe,
            "med_mae_15": mae,
            "mfe_gt_mae_15": bool(mfe_ok),
        }

    is_d = detail["IS"]
    if not (
        is_d["n_ok"]
        and is_d["med60_pos"]
        and is_d["mono"]
        and is_d["mid_ladder_pos"]
        and is_d["mfe_gt_mae_15"]
    ):
        reasons = []
        if not is_d["n_ok"]:
            reasons.append("IS_sample")
        if not is_d["med60_pos"]:
            reasons.append("IS_med60_not_pos")
        if not is_d["mono"]:
            reasons.append("IS_not_monotonic")
        if not is_d["mid_ladder_pos"]:
            reasons.append("IS_mid_ladder_not_pos")
        if not is_d["mfe_gt_mae_15"]:
            reasons.append("IS_mfe_not_gt_mae")
        return {
            "classification": "PATH_KILL",
            "stage": "STEP3",
            "reason": "+".join(reasons),
            "detail": detail,
            "path_advance": False,
        }

    for split in ("Validation", "OOS"):
        d = detail[split]
        # Val/OOS: n, med60, mono, mfe>mae (mid-ladder required on IS only per prereg)
        if not (d["n_ok"] and d["med60_pos"] and d["mono"] and d["mfe_gt_mae_15"]):
            reasons = []
            if not d["n_ok"]:
                reasons.append(f"{split}_sample")
            if not d["med60_pos"]:
                reasons.append(f"{split}_med60_not_pos")
            if not d["mono"]:
                reasons.append(f"{split}_not_monotonic")
            if not d["mfe_gt_mae_15"]:
                reasons.append(f"{split}_mfe_not_gt_mae")
            return {
                "classification": "PATH_KILL",
                "stage": "STEP3",
                "reason": "+".join(reasons),
                "detail": detail,
                "path_advance": False,
            }

    return {
        "classification": "PATH_ADVANCE",
        "stage": "STEP3",
        "reason": "IS_VAL_OOS_path_ok",
        "detail": detail,
        "path_advance": True,
    }


def run_trade(panel: pd.DataFrame, events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    open_ = panel["open"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)

    rows = []
    for ev in events.itertuples(index=False):
        t = int(ev.event_idx)
        side = int(ev.side)
        entry_i = t + 1
        exit_i = t + TRADE_H
        ok = (
            entry_i < n
            and exit_i < n
            and _fwd_ok(session, seg, ny, t, 1)
            and _fwd_ok(session, seg, ny, t, TRADE_H)
        )
        if not ok:
            continue
        entry = float(open_[entry_i])
        exit_px = float(close[exit_i])
        gross = side * (exit_px - entry)
        net = gross - COST_RT
        rows.append(
            {
                "event_id": ev.event_id,
                "split": ev.split,
                "side": side,
                "gross": gross,
                "net": net,
            }
        )
    trades = pd.DataFrame(rows)
    sum_rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        g = trades if split == "ALL" else trades.loc[trades["split"] == split]
        n_t = len(g)
        if n_t == 0:
            sum_rows.append(
                {
                    "split": split,
                    "n_trades": 0,
                    "mean_gross": np.nan,
                    "mean_net": np.nan,
                    "median_net": np.nan,
                    "hit_rate": np.nan,
                    "eligible": False,
                }
            )
            continue
        mean_net = float(g["net"].mean())
        sum_rows.append(
            {
                "split": split,
                "n_trades": n_t,
                "mean_gross": float(g["gross"].mean()),
                "mean_net": mean_net,
                "median_net": float(g["net"].median()),
                "hit_rate": float((g["net"] > 0).mean()),
                "eligible": n_t >= MIN_TRADES_SPLIT,
            }
        )
    return trades, pd.DataFrame(sum_rows)


def classify_trade(trade_summary: pd.DataFrame) -> dict:
    detail = {}
    ok = True
    for split in ("IS", "Validation", "OOS"):
        r = trade_summary.loc[trade_summary["split"] == split]
        if r.empty:
            detail[split] = {"ok": False}
            ok = False
            continue
        row = r.iloc[0]
        passed = bool(row["eligible"]) and float(row["mean_net"]) > 0
        detail[split] = {
            "n_trades": int(row["n_trades"]),
            "mean_net": float(row["mean_net"]),
            "pass": passed,
        }
        ok = ok and passed
    return {
        "classification": "ADVANCE" if ok else "KILL",
        "stage": "TRADE",
        "detail": detail,
    }


def first_anchor_summary(paths: pd.DataFrame) -> pd.DataFrame:
    g = paths.loc[
        paths["horizon"] == 60,
        ["event_id", "split", "valid", "first_anchor_bars", "hit_anchor"],
    ]
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        s = g if split == "ALL" else g.loc[g["split"] == split]
        hit = s.loc[s["hit_anchor"] == True]  # noqa: E712
        fr = pd.to_numeric(hit["first_anchor_bars"], errors="coerce")
        rows.append(
            {
                "split": split,
                "n_h60_valid": int(s["valid"].sum()),
                "n_hit_anchor_by_60": int(hit.shape[0]),
                "med_first_anchor_bars": float(fr.median()) if len(fr) else np.nan,
                "p25": float(fr.quantile(0.25)) if len(fr) else np.nan,
                "p75": float(fr.quantile(0.75)) if len(fr) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading panel...", flush=True)
    panel = load_panel()
    print(f"panel={len(panel)}", flush=True)

    print("Extracting Event C...", flush=True)
    events, funnel = extract_events(panel)
    events.to_parquet(RESULTS / "event_c_events.parquet", index=False)
    (RESULTS / "event_c_funnel.json").write_text(
        json.dumps(funnel, indent=2), encoding="utf-8"
    )
    print(json.dumps(funnel, indent=2), flush=True)

    print("Destinations...", flush=True)
    dest = measure_destinations(panel, events)
    dest.to_parquet(RESULTS / "event_c_dest_paths.parquet", index=False)
    dest_sum = summarize_destinations(dest)
    dest_sum.to_csv(RESULTS / "event_c_destinations.csv", index=False)

    dest_v = classify_destination(dest_sum)
    verdict: dict = {
        "destination": dest_v,
        "path": None,
        "trade": None,
        "final": dest_v["classification"],
    }

    if dest_v.get("advance_to_path"):
        print("Path ladder...", flush=True)
        paths = measure_paths(panel, events)
        paths.to_parquet(RESULTS / "path_progress.parquet", index=False)
        ladder = summarize_paths(paths)
        ladder.to_csv(RESULTS / "path_ladder_by_split.csv", index=False)
        first_anchor_summary(paths).to_csv(
            RESULTS / "first_anchor_timing.csv", index=False
        )
        path_v = classify_path(ladder)
        verdict["path"] = path_v
        verdict["final"] = path_v["classification"]

        if path_v.get("path_advance"):
            print("Trade test...", flush=True)
            trades, trade_sum = run_trade(panel, events)
            trades.to_parquet(RESULTS / "event_c_trades.parquet", index=False)
            trade_sum.to_csv(RESULTS / "event_c_trade_summary.csv", index=False)
            trade_v = classify_trade(trade_sum)
            verdict["trade"] = trade_v
            if trade_v["classification"] == "ADVANCE":
                verdict["final"] = "ADVANCE"
            else:
                verdict["final"] = "KILL_AFTER_TRADE"
    else:
        # still write empty path placeholders? skip — report handles missing
        pass

    (RESULTS / "event_c_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "destination": dest_v.get("classification"),
                "path": (verdict["path"] or {}).get("classification"),
                "trade": (verdict["trade"] or {}).get("classification"),
                "final": verdict["final"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
