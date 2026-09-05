"""
NQ NY Open — State Transition Discovery (09:30–10:30 ET)

Objective: find variables that materially change the odds of subsequent returns.
NO entries, stops, targets, or parameter optimization.
NO named strategies. Contaminated level-reject work is out of scope.

At each decision minute T in {09:35, 09:40, 09:45, 09:50, 10:00, 10:15, 10:30}:
  - build state from bars with ny_min <= T only
  - measure forward returns from NEXT bar open after T (executable clock)
  - compare conditional vs same-TOD unconditional

Splits: IS 2010-2021 / Val 2022-2024 / OOS 2025-2026.
Tercile / binary thresholds frozen from IS only.
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
from datetime import date as date_cls
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

from common.paths import art, ART, DATA, ROOT

NY_OPEN = 9 * 60 + 30
SESSION_START = 18 * 60
# Decision clocks (inclusive end of information window)
DECISION_OFFSETS = (5, 10, 15, 20, 30, 45, 60)  # minutes after 09:30
HORIZONS = (5, 10, 15, 20, 30)
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
            "volume": df["volume"].to_numpy(np.int64),
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
        "mean": float(np.mean(x)),
        "median": float(np.median(x)),
        "std": float(np.std(x, ddof=1)) if n > 1 else 0.0,
        "win_p": float(np.mean(x > 0)),
        "p_gt_0": float(np.mean(x > 0)),
        "p_abs_gt_5": float(np.mean(np.abs(x) >= 5)),
        "p_abs_gt_10": float(np.mean(np.abs(x) >= 10)),
        "p_abs_gt_0p05_onr": None,  # filled when onr-normalized series passed
    }


def dist_onr(x: np.ndarray) -> dict[str, Any]:
    st = dist(x)
    if st.get("n", 0):
        st["p_abs_gt_0p05"] = float(np.mean(np.abs(x) >= 0.05))
        st["p_abs_gt_0p10"] = float(np.mean(np.abs(x) >= 0.10))
    return st


def build_day_context(df: pd.DataFrame) -> pd.DataFrame:
    """Per session: overnight stats from cached day facts + overnight path length."""
    facts_path = art("ny_open_day_facts.parquet")
    if not facts_path.exists():
        raise FileNotFoundError("ny_open_day_facts.parquet required")
    facts = pd.read_parquet(facts_path)
    rows = []
    onr_hist: list[float] = []
    frames = {sd: g for sd, g in df.groupby("session_date", sort=True)}
    for _, fr in facts.iterrows():
        sd = fr["session_date"]
        sd_key = date_cls.fromisoformat(sd) if isinstance(sd, str) else sd
        g = frames.get(sd_key)
        if g is None:
            continue
        on = g[g["ny_min"] < NY_OPEN]
        on_c = on["close"].to_numpy(float)
        on_rv = float(np.sum(np.abs(np.diff(on_c)))) if len(on_c) > 1 else float(fr["onr"])
        onr = float(fr["onr"])
        onr_med20 = (
            float(np.median(onr_hist[-20:]))
            if len(onr_hist) >= 5
            else (float(fr["onr_med20"]) if np.isfinite(fr.get("onr_med20", np.nan)) else np.nan)
        )
        rows.append(
            {
                "session_date": sd_key,
                "year": int(fr["year"]),
                "dow": int(fr["dow"]),
                "split": str(fr["split"]),
                "onh": float(fr["onh"]),
                "onl": float(fr["onl"]),
                "onr": onr,
                "on_rv": on_rv,
                "open_930": float(fr["open_930"]),
                "open_loc": float(fr["open_loc_onr"]),
                "gap_onr": float(fr["gap_onr"]),
                "pdh": float(fr["pdh"]),
                "pdl": float(fr["pdl"]),
                "pdc": float(fr["pdc"]),
                "pdr": float(fr["pdr"]),
                "onr_med20": onr_med20,
                "onr_vs_med": (onr / onr_med20) if onr_med20 and onr_med20 > 0 else np.nan,
            }
        )
        onr_hist.append(onr)
    return pd.DataFrame(rows)


def slice_rth(df: pd.DataFrame, sd, end_min: int | None = None) -> pd.DataFrame:
    g = df[df["session_date"] == sd]
    g = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)]
    if end_min is not None:
        g = g[g["ny_min"] <= end_min]
    return g.reset_index(drop=True)


def state_at_T(rth_to_T: pd.DataFrame, ctx: dict, T_ny: int) -> dict[str, float] | None:
    """Causal state using only bars with ny_min <= T."""
    if len(rth_to_T) < 3:
        return None
    o930 = float(ctx["open_930"])
    onr = float(ctx["onr"])
    c = rth_to_T["close"].to_numpy(float)
    h = rth_to_T["high"].to_numpy(float)
    l = rth_to_T["low"].to_numpy(float)
    o = rth_to_T["open"].to_numpy(float)
    ny = rth_to_T["ny_min"].to_numpy(int)
    if ny[-1] != T_ny:
        # require exact T bar present
        if T_ny not in set(ny.tolist()):
            return None
        rth_to_T = rth_to_T[rth_to_T["ny_min"] <= T_ny].reset_index(drop=True)
        c = rth_to_T["close"].to_numpy(float)
        h = rth_to_T["high"].to_numpy(float)
        l = rth_to_T["low"].to_numpy(float)
        o = rth_to_T["open"].to_numpy(float)
        ny = rth_to_T["ny_min"].to_numpy(int)

    last_c = float(c[-1])
    elapsed = max(int(T_ny - NY_OPEN), 1)
    # opening range so far
    rng = float(h.max() - l.min())
    rng_onr = rng / onr
    # signed move from open
    move = last_c - o930
    move_onr = move / onr
    # realized path length
    path = float(np.sum(np.abs(np.diff(c)))) if len(c) > 1 else abs(move)
    path_onr = path / onr
    # speed: |move| per minute / ONR
    speed = abs(move_onr) / elapsed
    # vol expansion vs overnight: first-elapsed-min range vs expected share of ONR
    # expected linear: elapsed/390 * onr is wrong; use ratio rng/onr
    vol_exp = rng_onr  # high = expansion into day
    # vs overnight compression: onr_vs_med known pre-open
    onr_vs_med = float(ctx["onr_vs_med"]) if np.isfinite(ctx["onr_vs_med"]) else np.nan
    # directional: sign established?
    # first 5m move if T>=5
    move5 = np.nan
    if elapsed >= 5:
        sub5 = rth_to_T[rth_to_T["ny_min"] < NY_OPEN + 5]
        if len(sub5):
            move5 = float(sub5.iloc[-1]["close"] - o930)
    # persistence so far: fraction of 1m closes in direction of current move
    if abs(move) < 0.25:
        persist_frac = np.nan
        dir_sign = 0.0
    else:
        dir_sign = 1.0 if move > 0 else -1.0
        deltas = np.diff(c)
        persist_frac = float(np.mean(np.sign(deltas) == dir_sign)) if len(deltas) else np.nan
    # location of last price in overnight
    loc_now = (last_c - float(ctx["onl"])) / onr
    open_loc = float(ctx["open_loc"])
    # expansion vs overnight RV share
    on_rv = float(ctx["on_rv"])
    path_vs_onrv = path / on_rv if on_rv > 0 else np.nan

    return {
        "elapsed": float(elapsed),
        "rng_onr": rng_onr,
        "move_onr": move_onr,
        "abs_move_onr": abs(move_onr),
        "path_onr": path_onr,
        "speed": speed,
        "vol_exp": vol_exp,
        "onr_vs_med": onr_vs_med,
        "move5_onr": (move5 / onr) if np.isfinite(move5) else np.nan,
        "persist_frac": persist_frac,
        "dir_sign": dir_sign,
        "loc_now": loc_now,
        "open_loc": open_loc,
        "path_vs_onrv": path_vs_onrv,
        "gap_onr": float(ctx["gap_onr"]),
        "onr": onr,
    }


def forward_from_next(rth_full: pd.DataFrame, T_ny: int) -> dict[int, float] | None:
    """Forward returns from open of first bar AFTER T, unsigned (signed later by state)."""
    after = rth_full[rth_full["ny_min"] > T_ny].reset_index(drop=True)
    if len(after) < max(HORIZONS):
        return None
    entry = float(after.iloc[0]["open"])
    out = {}
    for h in HORIZONS:
        # bar index h-1 after entry bar (entry is index 0)
        j = h - 1
        if j >= len(after):
            out[h] = np.nan
        else:
            out[h] = float(after.iloc[j]["close"] - entry)
    return out


def main() -> None:
    print("=== State Transition Discovery ===", flush=True)
    df = load_nq()
    print("Building day context...", flush=True)
    ctx_df = build_day_context(df)
    print(f"Days: {len(ctx_df)}", flush=True)
    ctx_map = {r["session_date"]: r for _, r in ctx_df.iterrows()}

    # Pre-group RTH
    print("Indexing RTH...", flush=True)
    rth_map: dict = {}
    for sd, g in df.groupby("session_date", sort=False):
        if sd not in ctx_map:
            continue
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
        if len(rth) >= 90:
            rth_map[sd] = rth
    print(f"RTH days: {len(rth_map)}", flush=True)

    # Panel rows
    panel_rows = []
    for sd, ctx in ctx_map.items():
        rth = rth_map.get(sd)
        if rth is None:
            continue
        for off in DECISION_OFFSETS:
            T = NY_OPEN + off
            to_T = rth[rth["ny_min"] <= T]
            st = state_at_T(to_T, ctx, T)
            if st is None:
                continue
            fwd = forward_from_next(rth, T)
            if fwd is None:
                continue
            panel_rows.append(
                {
                    "session_date": str(sd),
                    "year": int(ctx["year"]),
                    "dow": int(ctx["dow"]),
                    "split": ctx["split"],
                    "T_offset": off,
                    "T_ny": T,
                    **st,
                    **{f"fwd_{h}": fwd[h] for h in HORIZONS},
                    # signed in established direction (0 if flat)
                    **{
                        f"fwd_dir_{h}": (fwd[h] * st["dir_sign"] if st["dir_sign"] != 0 else np.nan)
                        for h in HORIZONS
                    },
                    **{f"fwd_abs_{h}": abs(fwd[h]) for h in HORIZONS},
                    **{f"fwd_onr_{h}": fwd[h] / st["onr"] for h in HORIZONS},
                    **{
                        f"fwd_dir_onr_{h}": (
                            (fwd[h] * st["dir_sign"] / st["onr"]) if st["dir_sign"] != 0 else np.nan
                        )
                        for h in HORIZONS
                    },
                }
            )

    panel = pd.DataFrame(panel_rows)
    panel.to_parquet(art("ny_open_state_panel.parquet"), index=False)
    print(f"Panel rows: {len(panel)}", flush=True)

    # --- Freeze IS tercile thresholds per (T_offset, feature) ---
    features = [
        "rng_onr",
        "abs_move_onr",
        "path_onr",
        "speed",
        "onr_vs_med",
        "persist_frac",
        "open_loc",
        "loc_now",
        "path_vs_onrv",
        "gap_onr",
    ]

    thresholds: dict[str, dict[int, dict[str, float]]] = {}
    is_p = panel[panel["split"] == "IS"]
    for feat in features:
        thresholds[feat] = {}
        for off in DECISION_OFFSETS:
            s = is_p.loc[is_p["T_offset"] == off, feat].dropna()
            if len(s) < 100:
                continue
            thresholds[feat][off] = {
                "p33": float(s.quantile(0.33)),
                "p66": float(s.quantile(0.66)),
                "p20": float(s.quantile(0.20)),
                "p80": float(s.quantile(0.80)),
            }

    with open(art("ny_open_state_thresholds_IS.json"), "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2)

    # --- Condition definitions (behavioral, not optimized) ---
    # Each returns boolean mask on a T_offset slice
    def conditions_for(sub: pd.DataFrame, off: int) -> dict[str, pd.Series]:
        th = {feat: thresholds.get(feat, {}).get(off, {}) for feat in features}
        c: dict[str, pd.Series] = {}
        # Vol expansion: high opening range vs ONR
        if th["rng_onr"]:
            c["vol_expansion_high"] = sub["rng_onr"] >= th["rng_onr"]["p66"]
            c["vol_expansion_low"] = sub["rng_onr"] <= th["rng_onr"]["p33"]
        # Overnight compression then day expansion
        if th["onr_vs_med"] and th["rng_onr"]:
            c["compress_then_expand"] = (sub["onr_vs_med"] <= th["onr_vs_med"]["p33"]) & (
                sub["rng_onr"] >= th["rng_onr"]["p66"]
            )
            c["wide_ON_quiet_open"] = (sub["onr_vs_med"] >= th["onr_vs_med"]["p66"]) & (
                sub["rng_onr"] <= th["rng_onr"]["p33"]
            )
        # Strong directional move so far
        if th["abs_move_onr"]:
            c["strong_dir_move"] = (sub["abs_move_onr"] >= th["abs_move_onr"]["p66"]) & (
                sub["dir_sign"] != 0
            )
            c["weak_dir_move"] = sub["abs_move_onr"] <= th["abs_move_onr"]["p33"]
        # Persistence given direction
        if th["persist_frac"]:
            c["high_persistence"] = (sub["persist_frac"] >= th["persist_frac"]["p66"]) & (
                sub["dir_sign"] != 0
            )
            c["low_persistence"] = (sub["persist_frac"] <= th["persist_frac"]["p33"]) & (
                sub["dir_sign"] != 0
            )
        # Speed
        if th["speed"]:
            c["fast_move"] = (sub["speed"] >= th["speed"]["p66"]) & (sub["dir_sign"] != 0)
            c["slow_move"] = sub["speed"] <= th["speed"]["p33"]
        # Open location extremes
        if th["open_loc"]:
            c["open_near_ONH"] = sub["open_loc"] >= 0.80
            c["open_near_ONL"] = sub["open_loc"] <= 0.20
            c["open_mid"] = (sub["open_loc"] > 0.40) & (sub["open_loc"] < 0.60)
        # Current location extremes (at T)
        c["price_near_ONH"] = sub["loc_now"] >= 0.90
        c["price_near_ONL"] = sub["loc_now"] <= 0.10
        # Path vs overnight activity
        if th["path_vs_onrv"]:
            c["path_vs_ON_high"] = sub["path_vs_onrv"] >= th["path_vs_onrv"]["p66"]
        # Combined: strong move + high persistence (still not optimized — fixed intersection)
        if "strong_dir_move" in c and "high_persistence" in c:
            c["strong_and_persistent"] = c["strong_dir_move"] & c["high_persistence"]
        if "strong_dir_move" in c and "low_persistence" in c:
            c["strong_but_choppy"] = c["strong_dir_move"] & c["low_persistence"]
        if "fast_move" in c and "vol_expansion_high" in c:
            c["fast_and_expanded"] = c["fast_move"] & c["vol_expansion_high"]
        return c

    # Metrics: for each condition × T × horizon, compare to unconditional at that T
    # Primary: shift in |fwd| distribution (vol regime) AND shift in signed dir fwd (persistence)
    results = []
    for off in DECISION_OFFSETS:
        sub = panel[panel["T_offset"] == off].copy()
        if len(sub) < 200:
            continue
        conds = conditions_for(sub, off)
        # unconditional baselines per split
        for cname, mask in conds.items():
            for split in ("IS", "Validation", "OOS", "ALL"):
                base = sub if split == "ALL" else sub[sub["split"] == split]
                m = mask if split == "ALL" else mask.loc[base.index]
                # align
                if split != "ALL":
                    m = mask.reindex(base.index).fillna(False)
                else:
                    m = mask.reindex(base.index).fillna(False)
                cond = base.loc[m.to_numpy()]
                unc = base
                if len(cond) < 20:
                    continue
                for h in (5, 15, 30):
                    # absolute move (does state change magnitude odds?)
                    ca = cond[f"fwd_abs_{h}"].to_numpy(float)
                    ua = unc[f"fwd_abs_{h}"].to_numpy(float)
                    # signed in direction of state (persistence)
                    cd = cond[f"fwd_dir_{h}"].to_numpy(float)
                    # also raw signed long
                    cr = cond[f"fwd_{h}"].to_numpy(float)
                    ur = unc[f"fwd_{h}"].to_numpy(float)
                    # ONR-norm abs
                    cn = cond[f"fwd_onr_{h}"].to_numpy(float)
                    un = unc[f"fwd_onr_{h}"].to_numpy(float)

                    d_abs = dist(ca)
                    d_unc_abs = dist(ua)
                    d_dir = dist(cd)
                    d_raw = dist(cr)
                    d_unc_raw = dist(ur)
                    d_onr = dist_onr(cn)
                    d_unc_onr = dist_onr(un)

                    # odds shifts
                    delta_abs_mean = (
                        d_abs["mean"] - d_unc_abs["mean"]
                        if d_abs.get("n") and d_unc_abs.get("n")
                        else np.nan
                    )
                    delta_p_abs10 = (
                        d_abs.get("p_abs_gt_10", np.nan) - d_unc_abs.get("p_abs_gt_10", np.nan)
                        if d_abs.get("n") and d_unc_abs.get("n")
                        else np.nan
                    )
                    delta_dir_win = (
                        d_dir.get("win_p", np.nan) - 0.5 if d_dir.get("n") else np.nan
                    )
                    delta_raw_win = (
                        d_raw.get("win_p", np.nan) - d_unc_raw.get("win_p", np.nan)
                        if d_raw.get("n") and d_unc_raw.get("n")
                        else np.nan
                    )

                    results.append(
                        {
                            "condition": cname,
                            "T_offset": off,
                            "horizon": h,
                            "split": split,
                            "n": int(len(cond)),
                            "n_unc": int(len(unc)),
                            "rate": float(len(cond) / len(unc)),
                            "abs_mean": d_abs.get("mean"),
                            "unc_abs_mean": d_unc_abs.get("mean"),
                            "delta_abs_mean": delta_abs_mean,
                            "p_abs_gt_10": d_abs.get("p_abs_gt_10"),
                            "unc_p_abs_gt_10": d_unc_abs.get("p_abs_gt_10"),
                            "delta_p_abs10": delta_p_abs10,
                            "dir_win": d_dir.get("win_p"),
                            "dir_mean": d_dir.get("mean"),
                            "delta_dir_win_vs_50": delta_dir_win,
                            "raw_win": d_raw.get("win_p"),
                            "unc_raw_win": d_unc_raw.get("win_p"),
                            "delta_raw_win": delta_raw_win,
                            "onr_abs_mean": float(np.nanmean(np.abs(cn))),
                            "unc_onr_abs_mean": float(np.nanmean(np.abs(un))),
                            "dir_onr_mean": float(np.nanmean(cond[f"fwd_dir_onr_{h}"].to_numpy(float))),
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("ny_open_state_transitions.csv"), index=False)

    # --- Score: require IS material shift + same sign Val + OOS ---
    # Two tracks: (1) magnitude/odds of large move (2) directional persistence
    def score_track(metric_key: str, unc_compare: str, min_is_n: int = 80) -> list[dict]:
        ranked = []
        keys = res_df[["condition", "T_offset", "horizon"]].drop_duplicates()
        for _, k in keys.iterrows():
            block = res_df[
                (res_df["condition"] == k["condition"])
                & (res_df["T_offset"] == k["T_offset"])
                & (res_df["horizon"] == k["horizon"])
            ]
            is_r = block[block["split"] == "IS"]
            va_r = block[block["split"] == "Validation"]
            oo_r = block[block["split"] == "OOS"]
            if len(is_r) == 0 or len(va_r) == 0 or len(oo_r) == 0:
                continue
            is_r, va_r, oo_r = is_r.iloc[0], va_r.iloc[0], oo_r.iloc[0]
            if is_r["n"] < min_is_n or va_r["n"] < 30 or oo_r["n"] < 20:
                continue
            is_v, va_v, oo_v = is_r[metric_key], va_r[metric_key], oo_r[metric_key]
            if not (np.isfinite(is_v) and np.isfinite(va_v) and np.isfinite(oo_v)):
                continue
            # material on IS
            if metric_key == "delta_dir_win_vs_50":
                material = abs(is_v) >= 0.03  # 3pp vs coin
                same = (np.sign(is_v) == np.sign(va_v) == np.sign(oo_v)) and abs(is_v) > 0
            elif metric_key == "delta_p_abs10":
                material = abs(is_v) >= 0.05  # 5pp shift in P(|r|>=10)
                same = np.sign(is_v) == np.sign(va_v) == np.sign(oo_v)
            elif metric_key == "delta_abs_mean":
                # relative
                rel = is_v / is_r["unc_abs_mean"] if is_r["unc_abs_mean"] else 0
                material = abs(rel) >= 0.15
                same = np.sign(is_v) == np.sign(va_v) == np.sign(oo_v)
                is_v = rel  # store relative for ranking
            else:
                material = abs(is_v) >= 0.03
                same = np.sign(is_v) == np.sign(va_v) == np.sign(oo_v)

            survives = bool(material and same)
            ranked.append(
                {
                    "track": unc_compare,
                    "condition": k["condition"],
                    "T_offset": int(k["T_offset"]),
                    "horizon": int(k["horizon"]),
                    "survives": survives,
                    "material_IS": bool(material),
                    "same_sign": bool(same),
                    "IS_n": int(is_r["n"]),
                    "Val_n": int(va_r["n"]),
                    "OOS_n": int(oo_r["n"]),
                    "rate_IS": float(is_r["rate"]),
                    "IS_metric": float(is_r[metric_key]) if np.isfinite(is_r[metric_key]) else None,
                    "Val_metric": float(va_r[metric_key]) if np.isfinite(va_r[metric_key]) else None,
                    "OOS_metric": float(oo_r[metric_key]) if np.isfinite(oo_r[metric_key]) else None,
                    "IS_dir_win": float(is_r["dir_win"]) if np.isfinite(is_r["dir_win"]) else None,
                    "Val_dir_win": float(va_r["dir_win"]) if np.isfinite(va_r["dir_win"]) else None,
                    "OOS_dir_win": float(oo_r["dir_win"]) if np.isfinite(oo_r["dir_win"]) else None,
                    "IS_dir_mean": float(is_r["dir_mean"]) if np.isfinite(is_r["dir_mean"]) else None,
                    "IS_abs_mean": float(is_r["abs_mean"]) if np.isfinite(is_r["abs_mean"]) else None,
                    "unc_abs_mean_IS": float(is_r["unc_abs_mean"]) if np.isfinite(is_r["unc_abs_mean"]) else None,
                    "score": float(abs(is_r[metric_key]) + 0.5 * abs(va_r[metric_key]) + 0.5 * abs(oo_r[metric_key]))
                    if all(np.isfinite([is_r[metric_key], va_r[metric_key], oo_r[metric_key]]))
                    else -1,
                }
            )
        return sorted(ranked, key=lambda x: (x["survives"], x["score"]), reverse=True)

    track_dir = score_track("delta_dir_win_vs_50", "directional_persistence")
    track_mag = score_track("delta_p_abs10", "magnitude_P_abs_ge_10")
    track_abs = score_track("delta_abs_mean", "abs_mean_shift")

    survivors = {
        "directional": [x for x in track_dir if x["survives"]][:20],
        "magnitude_p10": [x for x in track_mag if x["survives"]][:20],
        "abs_mean": [x for x in track_abs if x["survives"]][:20],
    }

    # 2025 vs 2026 for top survivors
    def year_break(condition: str, off: int, horizon: int) -> dict:
        sub = panel[(panel["T_offset"] == off)].copy()
        conds = conditions_for(sub, off)
        if condition not in conds:
            return {}
        m = conds[condition]
        out = {}
        for y in (2025, 2026):
            s = sub[(sub["year"] == y) & m.reindex(sub.index).fillna(False)]
            arr = s[f"fwd_dir_{horizon}"].to_numpy(float)
            abs_arr = s[f"fwd_abs_{horizon}"].to_numpy(float)
            out[str(y)] = {"dir": dist(arr), "abs": dist(abs_arr), "n": int(len(s))}
        return out

    top_detail = []
    seen = set()
    for track_name, lst in survivors.items():
        for x in lst[:5]:
            key = (x["condition"], x["T_offset"], x["horizon"], track_name)
            if key in seen:
                continue
            seen.add(key)
            top_detail.append(
                {
                    **x,
                    "y2025_2026": year_break(x["condition"], x["T_offset"], x["horizon"]),
                }
            )

    # Baseline table at each T
    baselines = []
    for off in DECISION_OFFSETS:
        sub = panel[panel["T_offset"] == off]
        for split in ("IS", "Validation", "OOS", "ALL"):
            s = sub if split == "ALL" else sub[sub["split"] == split]
            for h in (5, 15, 30):
                baselines.append(
                    {
                        "T_offset": off,
                        "split": split,
                        "horizon": h,
                        "abs": dist(s[f"fwd_abs_{h}"].to_numpy(float)),
                        "raw": dist(s[f"fwd_{h}"].to_numpy(float)),
                    }
                )

    report = {
        "meta": {
            "objective": "Find state transitions 09:30-10:30 that change forward odds",
            "no_strategy": True,
            "decision_offsets_min_after_930": list(DECISION_OFFSETS),
            "horizons": list(HORIZONS),
            "splits": {"IS": "2010-2021", "Validation": "2022-2024", "OOS": "2025-2026"},
            "threshold_rule": "IS terciles only; open_loc extremes fixed at 20/80 and 10/90",
            "entry_clock": "forward from next bar open after T (no overlap with state window)",
        },
        "n_panel_rows": int(len(panel)),
        "n_days": int(panel["session_date"].nunique()),
        "survivors": survivors,
        "top_detail": top_detail,
        "rankings": {
            "directional_top15": track_dir[:15],
            "magnitude_p10_top15": track_mag[:15],
            "abs_mean_top15": track_abs[:15],
        },
        "baselines_sample": [b for b in baselines if b["split"] == "ALL" and b["horizon"] == 15],
        "verdict_note": None,
    }

    # Verdict for this stage
    n_surv = sum(len(v) for v in survivors.values())
    if n_surv == 0:
        report["verdict_note"] = (
            "No state transition survived IS materiality + Val/OOS same-sign under frozen terciles. "
            "NY open changes the level of volatility over years, but within-morning conditional states "
            "tested here do not stably reprice forward odds beyond baseline."
        )
        stage_verdict = "C_no_state_transition"
    else:
        # Check if any directional survivor has |delta|>=5pp and OOS dir_win>=0.55
        strong = [
            x
            for x in survivors["directional"]
            if abs(x.get("IS_metric") or 0) >= 0.05
            and (x.get("OOS_dir_win") or 0) >= 0.55
            and (x.get("IS_dir_win") or 0) >= 0.55
        ]
        mag_strong = [
            x
            for x in survivors["magnitude_p10"]
            if abs(x.get("IS_metric") or 0) >= 0.08
        ]
        if strong or mag_strong:
            report["verdict_note"] = (
                "At least one state transition materially shifts odds across IS→Val→OOS. "
                "Not yet a strategy — candidate for a later mechanical conversion stage."
            )
            stage_verdict = "B_state_transition_found"
            report["strong_directional"] = strong[:5]
            report["strong_magnitude"] = mag_strong[:5]
        else:
            report["verdict_note"] = (
                "Weak-but-stable state transitions found (survive sign tests) but effect sizes "
                "are borderline. Not yet enough to justify strategy construction."
            )
            stage_verdict = "B_weak_state_transition"
    report["stage_verdict"] = stage_verdict

    with open(art("ny_open_state_transition_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    md = render_md(report, survivors, track_dir, track_mag, track_abs, panel)
    (art("ny_open_state_transition_report.md")).write_text(md, encoding="utf-8")
    print("Stage verdict:", stage_verdict, flush=True)
    print("Directional survivors:", len(survivors["directional"]), flush=True)
    print("Magnitude survivors:", len(survivors["magnitude_p10"]), flush=True)
    for x in survivors["directional"][:5]:
        print(
            f"  DIR {x['condition']} T+{x['T_offset']} h{x['horizon']}: "
            f"IS dWin={x['IS_metric']:.3f} win={x['IS_dir_win']:.3f} "
            f"Val={x['Val_dir_win']:.3f} OOS={x['OOS_dir_win']:.3f} n={x['IS_n']}",
            flush=True,
        )
    for x in survivors["magnitude_p10"][:5]:
        print(
            f"  MAG {x['condition']} T+{x['T_offset']} h{x['horizon']}: "
            f"IS dP10={x['IS_metric']:.3f} rate={x['rate_IS']:.2f} n={x['IS_n']}",
            flush=True,
        )


def render_md(report, survivors, track_dir, track_mag, track_abs, panel) -> str:
    L = []
    L += [
        "# NQ NY Open — State Transition Discovery",
        "",
        f"**Stage verdict: `{report['stage_verdict']}`**",
        "",
        report["verdict_note"],
        "",
        "## Scope",
        "",
        "- Window: **09:30–10:30 ET** decision clocks at +5/+10/+15/+20/+30/+45/+60m.",
        "- State uses only bars `ny_min <= T`.",
        "- Forwards from **next bar open after T** (no overlap).",
        "- No entries, stops, targets, or named strategies.",
        "- Terciles frozen on **IS only**.",
        "- Prior level-confirmation hypothesis: **stopped** (clean failure).",
        "",
        f"Panel: **{report['n_panel_rows']}** rows, **{report['n_days']}** days.",
        "",
        "## What we are measuring",
        "",
        "Two kinds of odds-shift:",
        "",
        "1. **Directional persistence** — given an established direction at T, P(forward move continues) vs 50%.",
        "2. **Magnitude / expansion** — P(|forward| ≥ 10 pts) vs same-TOD unconditional.",
        "",
        "## Survivors (IS material + Val/OOS same sign)",
        "",
    ]

    def tbl(title, rows, cols):
        L.append(f"### {title}")
        L.append("")
        if not rows:
            L.append("_None._")
            L.append("")
            return
        L.append("| " + " | ".join(cols) + " |")
        L.append("|" + "|".join(["---"] * len(cols)) + "|")
        for r in rows[:12]:
            L.append(
                "| "
                + " | ".join(
                    [
                        str(r["condition"]),
                        f"+{r['T_offset']}m",
                        f"h{r['horizon']}",
                        str(r["IS_n"]),
                        f"{r['rate_IS']:.2f}",
                        f"{r['IS_metric']:.3f}" if r["IS_metric"] is not None else "",
                        f"{r.get('IS_dir_win') or float('nan'):.3f}"
                        if r.get("IS_dir_win") is not None
                        else "—",
                        f"{r.get('Val_dir_win') or float('nan'):.3f}"
                        if r.get("Val_dir_win") is not None
                        else "—",
                        f"{r.get('OOS_dir_win') or float('nan'):.3f}"
                        if r.get("OOS_dir_win") is not None
                        else "—",
                        "Y" if r["survives"] else "N",
                    ]
                )
                + " |"
            )
        L.append("")

    # directional table
    L.append("### Directional persistence survivors")
    L.append("")
    rows = survivors["directional"]
    if not rows:
        L.append("_None._")
        L.append("")
    else:
        L.append(
            "| Condition | T | H | IS n | Rate | IS Δwin vs 50 | IS win | Val win | OOS win |"
        )
        L.append("|-----------|---|---|------|------|---------------|--------|---------|---------|")
        for r in rows[:15]:
            L.append(
                f"| `{r['condition']}` | +{r['T_offset']}m | {r['horizon']} | {r['IS_n']} | "
                f"{r['rate_IS']:.2f} | {r['IS_metric']:.3f} | {r['IS_dir_win']:.3f} | "
                f"{r['Val_dir_win']:.3f} | {r['OOS_dir_win']:.3f} |"
            )
        L.append("")

    L.append("### Magnitude survivors (Δ P(|fwd|≥10 pts))")
    L.append("")
    rows = survivors["magnitude_p10"]
    if not rows:
        L.append("_None._")
        L.append("")
    else:
        L.append(
            "| Condition | T | H | IS n | Rate | IS ΔP10 | Val ΔP10 | OOS ΔP10 |"
        )
        L.append("|-----------|---|---|------|------|---------|----------|----------|")
        for r in rows[:15]:
            L.append(
                f"| `{r['condition']}` | +{r['T_offset']}m | {r['horizon']} | {r['IS_n']} | "
                f"{r['rate_IS']:.2f} | {r['IS_metric']:.3f} | {r['Val_metric']:.3f} | {r['OOS_metric']:.3f} |"
            )
        L.append("")

    L.append("## Top detail (with 2025/2026)")
    L.append("")
    for d in report.get("top_detail", [])[:8]:
        L.append(
            f"- **`{d['condition']}`** at T+{d['T_offset']}m → h{d['horizon']} "
            f"[{d['track']}]: IS metric={d['IS_metric']:.3f}, "
            f"dir wins IS/Val/OOS="
            f"{d.get('IS_dir_win')}/{d.get('Val_dir_win')}/{d.get('OOS_dir_win')}; "
            f"2025/26=`{d.get('y2025_2026')}`"
        )
    L.append("")

    L.append("## Near-misses / killed (top by score, not surviving)")
    L.append("")
    L.append("Directional:")
    for r in track_dir[:8]:
        if r["survives"]:
            continue
        L.append(
            f"- `{r['condition']}` T+{r['T_offset']} h{r['horizon']}: "
            f"material={r['material_IS']} same_sign={r['same_sign']} "
            f"IS Δ={r['IS_metric']} wins={r['IS_dir_win']}/{r['Val_dir_win']}/{r['OOS_dir_win']}"
        )
    L.append("")
    L.append("## Interpretation rule")
    L.append("")
    L.append(
        "A useful state transition must change the **conditional distribution** vs same-time-of-day "
        "unconditional — not merely describe that the open is volatile. "
        "If nothing survives, that is success: we know these states are not the information source."
    )
    L.append("")
    L.append("## Next step gate")
    L.append("")
    if report["stage_verdict"].startswith("B"):
        L.append(
            "Only if a survivor is economically meaningful (directional ≥~55% stable, or large "
            "magnitude shift) do we convert **one** state into a mechanical wait/go rule."
        )
    else:
        L.append(
            "No conversion to strategy. Optionally test *other* fundamental state families "
            "(order-flow proxies, cross-asset, time-of-week interaction) — still without optimizing."
        )
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
