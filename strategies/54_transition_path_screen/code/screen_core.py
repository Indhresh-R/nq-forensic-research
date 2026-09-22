"""
Strategy 54 — transition path screen (core).

Path difference only. No trades.
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
    CATALOGS,
    G_IS,
    G_VAL,
    HORIZONS,
    MIN_IS,
    MIN_OOS,
    MIN_VAL,
    PRIMARY_H,
    RESULTS,
    S52_RESULTS,
)


def load_panel() -> pd.DataFrame:
    states = pd.read_parquet(S52_RESULTS / "market_states.parquet")
    feats = pd.read_parquet(
        S52_RESULTS / "market_state_features.parquet",
        columns=["ts", "high", "low", "close"],
    )
    if len(states) != len(feats):
        raise RuntimeError("S52 states/features length mismatch")
    panel = states.copy()
    for c in ("high", "low", "close"):
        panel[c] = feats[c].to_numpy(np.float64)
    panel = (
        panel.loc[panel["census_eligible"]]
        .sort_values(["session_date", "ny_min"])
        .reset_index(drop=True)
    )
    panel["split"] = [split_of(int(y)) for y in panel["session_year"].to_numpy()]
    return panel


def _fwd_max(arr: np.ndarray, w: int) -> np.ndarray:
    return pd.Series(arr[::-1]).rolling(w, min_periods=1).max().to_numpy()[::-1]


def _fwd_min(arr: np.ndarray, w: int) -> np.ndarray:
    return pd.Series(arr[::-1]).rolling(w, min_periods=1).min().to_numpy()[::-1]


def horizon_ok(panel: pd.DataFrame, h: int) -> np.ndarray:
    n = len(panel)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    ok = np.zeros(n, dtype=bool)
    idx = np.arange(0, n - h, dtype=np.int64)
    th = idx + h
    ok[idx] = (
        (session[th] == session[idx])
        & (seg[th] == seg[idx])
        & (ny[th] == ny[idx] + h)
    )
    return ok


def extract_transitions(panel: pd.DataFrame, state_col: str) -> pd.DataFrame:
    state = panel[state_col].to_numpy(dtype=object)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)
    prev_ok = np.zeros(n, dtype=bool)
    prev_ok[1:] = (
        (session[1:] == session[:-1])
        & (seg[1:] == seg[:-1])
        & (ny[1:] == ny[:-1] + 1)
    )
    changed = np.zeros(n, dtype=bool)
    changed[1:] = state[1:] != state[:-1]
    mask = prev_ok & changed
    idx = np.flatnonzero(mask)
    return pd.DataFrame(
        {
            "event_idx": idx,
            "from_state": state[idx - 1],
            "to_state": state[idx],
            "split": panel["split"].to_numpy()[idx],
            "session_date": session[idx],
            "session_year": panel["session_year"].to_numpy(np.int16)[idx],
        }
    )


def extract_stay_baseline(panel: pd.DataFrame, state_col: str) -> pd.DataFrame:
    """Bars where state persists at least to t+1 (stay candidates)."""
    state = panel[state_col].to_numpy(dtype=object)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)
    next_ok = np.zeros(n, dtype=bool)
    next_ok[:-1] = (
        (session[:-1] == session[1:])
        & (seg[:-1] == seg[1:])
        & (ny[:-1] + 1 == ny[1:])
        & (state[:-1] == state[1:])
    )
    idx = np.flatnonzero(next_ok)
    return pd.DataFrame(
        {
            "event_idx": idx,
            "from_state": state[idx],
            "to_state": state[idx],  # stay
            "split": panel["split"].to_numpy()[idx],
            "session_date": session[idx],
            "session_year": panel["session_year"].to_numpy(np.int16)[idx],
        }
    )


def attach_paths(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    n = len(panel)
    hi = {h: _fwd_max(high, h) for h in HORIZONS}
    lo = {h: _fwd_min(low, h) for h in HORIZONS}
    ok = {h: horizon_ok(panel, h) for h in HORIZONS}

    t = events["event_idx"].to_numpy(np.int64)
    # path starts after t: use forward window from t+1
    start = t + 1
    rows = []
    base = events.reset_index(drop=True)
    for h in HORIZONS:
        valid = ok[h][t] & (start < n) & (t + h < n)
        # Also require path from t+1 for h bars: ny continuity t -> t+h already in ok[h]
        st = start
        # forward extremes from entry bar t+1 over h bars => use hi[h][t+1]
        # when t+h is last bar of window from t+1: bars t+1..t+h = h bars
        use = valid & (st + h - 1 < n)
        idx = np.flatnonzero(use)
        if len(idx) == 0:
            continue
        tt = t[idx]
        ss = st[idx]
        c0 = close[tt]
        hh = hi[h][ss]
        ll = lo[h][ss]
        c1 = close[tt + h]
        hl = hh - ll
        net = c1 - c0
        abs_net = np.abs(net)
        abs_max = np.fmax(hh - c0, c0 - ll)
        part = base.iloc[idx].copy()
        part["horizon"] = h
        part["valid"] = True
        part["hl_range"] = hl
        part["net"] = net
        part["abs_net"] = abs_net
        part["abs_max_excursion"] = abs_max
        rows.append(part)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def stay_medians(panel: pd.DataFrame, state_col: str) -> pd.DataFrame:
    """Median path metrics for stay-in-state bars, by from_state × split × horizon."""
    stay = extract_stay_baseline(panel, state_col)
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    n = len(panel)
    hi = {h: _fwd_max(high, h) for h in HORIZONS}
    lo = {h: _fwd_min(low, h) for h in HORIZONS}
    ok = {h: horizon_ok(panel, h) for h in HORIZONS}

    t = stay["event_idx"].to_numpy(np.int64)
    split = stay["split"].to_numpy(dtype=object)
    frm = stay["from_state"].to_numpy(dtype=object)
    rows = []
    for h in HORIZONS:
        valid = ok[h][t] & (t + 1 < n) & (t + h < n)
        idx = np.flatnonzero(valid)
        tt = t[idx]
        ss = tt + 1
        c0 = close[tt]
        hl = hi[h][ss] - lo[h][ss]
        abs_net = np.abs(close[tt + h] - c0)
        df = pd.DataFrame(
            {
                "from_state": frm[idx],
                "split": split[idx],
                "hl_range": hl,
                "abs_net": abs_net,
            }
        )
        for (fs, sp), g in df.groupby(["from_state", "split"], sort=True):
            rows.append(
                {
                    "from_state": fs,
                    "split": sp,
                    "horizon": h,
                    "n_stay": len(g),
                    "median_hl_range_stay": float(g["hl_range"].median()),
                    "median_abs_net_stay": float(g["abs_net"].median()),
                }
            )
        # ALL split
        for fs, g in df.groupby("from_state", sort=True):
            rows.append(
                {
                    "from_state": fs,
                    "split": "ALL",
                    "horizon": h,
                    "n_stay": len(g),
                    "median_hl_range_stay": float(g["hl_range"].median()),
                    "median_abs_net_stay": float(g["abs_net"].median()),
                }
            )
    return pd.DataFrame(rows)


def contrast_table(
    catalog: str,
    trans_paths: pd.DataFrame,
    stay_med: pd.DataFrame,
) -> pd.DataFrame:
    h = PRIMARY_H
    tp = trans_paths.loc[trans_paths["horizon"] == h].copy()
    sm = stay_med.loc[stay_med["horizon"] == h]
    rows = []
    for (frm, to), g in tp.groupby(["from_state", "to_state"], sort=True):
        if frm == to:
            continue
        for split in ("IS", "Validation", "OOS", "ALL"):
            gt = g if split == "ALL" else g.loc[g["split"] == split]
            sb = sm.loc[(sm["from_state"] == frm) & (sm["split"] == split)]
            nt = len(gt)
            nb = int(sb["n_stay"].iloc[0]) if len(sb) else 0
            med_t = float(gt["hl_range"].median()) if nt else np.nan
            med_b = float(sb["median_hl_range_stay"].iloc[0]) if len(sb) else np.nan
            abs_b = float(sb["median_abs_net_stay"].iloc[0]) if len(sb) else np.nan
            delta = med_t - med_b if np.isfinite(med_t) and np.isfinite(med_b) else np.nan
            denom = max(med_b, 1.0) if np.isfinite(med_b) else np.nan
            gap = delta / denom if np.isfinite(delta) and np.isfinite(denom) else np.nan
            rows.append(
                {
                    "catalog": catalog,
                    "from_state": frm,
                    "to_state": to,
                    "transition": f"{frm}->{to}",
                    "split": split,
                    "n_transition": nt,
                    "n_stay_baseline": nb,
                    "median_hl_range_trans": med_t,
                    "median_hl_range_stay": med_b,
                    "delta_hl_range": delta,
                    "rel_gap": gap,
                    "median_abs_net_trans": float(gt["abs_net"].median()) if nt else np.nan,
                    "median_abs_net_stay": abs_b,
                    "median_net_trans": float(gt["net"].median()) if nt else np.nan,
                    "median_abs_max_trans": float(gt["abs_max_excursion"].median())
                    if nt
                    else np.nan,
                }
            )
    return pd.DataFrame(rows)


def classify(contrast: pd.DataFrame) -> dict:
    out = {}
    for (cat, trans), g in contrast.groupby(["catalog", "transition"], sort=True):
        by = {r.split: r for r in g.itertuples(index=False)}
        is_r = by.get("IS")
        val_r = by.get("Validation")
        oos_r = by.get("OOS")

        def _n(r):
            return int(r.n_transition) if r is not None else 0

        thin = is_r is None or _n(is_r) < MIN_IS
        detail = {
            "IS": None
            if is_r is None
            else {
                "n": _n(is_r),
                "rel_gap": float(is_r.rel_gap) if np.isfinite(is_r.rel_gap) else None,
                "delta": float(is_r.delta_hl_range)
                if np.isfinite(is_r.delta_hl_range)
                else None,
                "median_hl_trans": float(is_r.median_hl_range_trans)
                if np.isfinite(is_r.median_hl_range_trans)
                else None,
                "median_hl_stay": float(is_r.median_hl_range_stay)
                if np.isfinite(is_r.median_hl_range_stay)
                else None,
            },
            "Validation": None
            if val_r is None
            else {
                "n": _n(val_r),
                "rel_gap": float(val_r.rel_gap) if np.isfinite(val_r.rel_gap) else None,
                "delta": float(val_r.delta_hl_range)
                if np.isfinite(val_r.delta_hl_range)
                else None,
            },
            "OOS": None
            if oos_r is None
            else {
                "n": _n(oos_r),
                "rel_gap": float(oos_r.rel_gap) if np.isfinite(oos_r.rel_gap) else None,
                "delta": float(oos_r.delta_hl_range)
                if np.isfinite(oos_r.delta_hl_range)
                else None,
            },
        }

        if thin:
            cls = "THIN"
            oos_caution = False
        else:
            g_is = float(is_r.rel_gap) if is_r is not None and np.isfinite(is_r.rel_gap) else np.nan
            d_is = float(is_r.delta_hl_range) if is_r is not None and np.isfinite(is_r.delta_hl_range) else np.nan
            val_ok = val_r is not None and _n(val_r) >= MIN_VAL
            if not np.isfinite(g_is) or abs(g_is) < G_IS:
                cls = "KILL"
                oos_caution = False
            elif not val_ok:
                cls = "UNSTABLE"
                oos_caution = False
            else:
                g_val = float(val_r.rel_gap) if np.isfinite(val_r.rel_gap) else np.nan
                d_val = (
                    float(val_r.delta_hl_range)
                    if np.isfinite(val_r.delta_hl_range)
                    else np.nan
                )
                same_sign = (
                    np.isfinite(d_is)
                    and np.isfinite(d_val)
                    and ((d_is > 0 and d_val > 0) or (d_is < 0 and d_val < 0))
                )
                if same_sign and np.isfinite(g_val) and abs(g_val) >= G_VAL:
                    cls = "INTERESTING"
                else:
                    cls = "UNSTABLE"
                oos_caution = False
                if cls == "INTERESTING" and oos_r is not None and _n(oos_r) >= MIN_OOS:
                    d_oos = (
                        float(oos_r.delta_hl_range)
                        if np.isfinite(oos_r.delta_hl_range)
                        else np.nan
                    )
                    if np.isfinite(d_is) and np.isfinite(d_oos):
                        if (d_is > 0) != (d_oos > 0):
                            oos_caution = True

        frm, to = trans.split("->", 1)
        # Activity labels are vol/volume-based; path-range gaps into them can be compositional.
        definitional_overlap = to in {"HIGH_ACTIVITY", "LOW_ACTIVITY"}
        out[f"{cat}:{trans}"] = {
            "catalog": cat,
            "transition": trans,
            "from_state": frm,
            "to_state": to,
            "classification": cls,
            "oos_caution": oos_caution,
            "definitional_overlap": definitional_overlap,
            "detail": detail,
        }
    return out


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading panel…", flush=True)
    panel = load_panel()
    print(f"bars={len(panel):,}", flush=True)

    all_contrast = []
    verdict_cells = {}

    for meta in CATALOGS:
        cat = meta["catalog"]
        col = meta["state_col"]
        print(f"Catalog {cat} ({col})…", flush=True)
        trans = extract_transitions(panel, col)
        print(f"  transitions={len(trans):,}", flush=True)

        tpaths = attach_paths(panel, trans)
        stay_med = stay_medians(panel, col)
        stay_med.to_csv(RESULTS / f"stay_medians_{cat}.csv", index=False)
        trans.to_parquet(RESULTS / f"transitions_{cat}.parquet", index=False)
        tpaths.to_parquet(RESULTS / f"transition_paths_{cat}.parquet", index=False)

        contrast = contrast_table(cat, tpaths, stay_med)
        contrast.to_csv(RESULTS / f"path_contrast_{cat}.csv", index=False)
        all_contrast.append(contrast)
        verdict_cells.update(classify(contrast))
        counts = {}
        for v in verdict_cells.values():
            if v["catalog"] != cat:
                continue
            counts[v["classification"]] = counts.get(v["classification"], 0) + 1
        print(f"  classes={counts}", flush=True)

    pd.concat(all_contrast, ignore_index=True).to_csv(
        RESULTS / "path_contrast_all.csv", index=False
    )
    interesting = sorted(
        k for k, v in verdict_cells.items() if v["classification"] == "INTERESTING"
    )
    interesting_nondef = sorted(
        k
        for k, v in verdict_cells.items()
        if v["classification"] == "INTERESTING" and not v.get("definitional_overlap")
    )
    verdict = {
        "cells": verdict_cells,
        "interesting": interesting,
        "interesting_non_definitional": interesting_nondef,
        "thresholds": {
            "min_is": MIN_IS,
            "min_val": MIN_VAL,
            "min_oos": MIN_OOS,
            "g_is": G_IS,
            "g_val": G_VAL,
            "primary_horizon": PRIMARY_H,
        },
        "note": (
            "No trades. INTERESTING = path distinct from stay baseline. "
            "Transitions into HIGH_ACTIVITY/LOW_ACTIVITY flagged definitional_overlap "
            "(activity labels entangle with subsequent range)."
        ),
    }
    (RESULTS / "verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(f"INTERESTING: {verdict['interesting']}", flush=True)
    print(f"INTERESTING non-definitional: {verdict['interesting_non_definitional']}", flush=True)


if __name__ == "__main__":
    main()
