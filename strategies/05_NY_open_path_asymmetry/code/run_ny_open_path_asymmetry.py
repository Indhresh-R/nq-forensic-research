"""
NQ Path-Asymmetry Discovery (09:30–11:00 ET)

Prior stages killed:
  1) Named strategy / AM Trades core
  2) Level accept-reject confirmation → next return
  3) Simple NY-open state → next return / raw magnitude

This stage asks a different question:
  Are there observable states where the *future path* is asymmetric
  (e.g. +1R before −1R) even when next-bar / horizon direction stays ~50%?

NO entries, stops, targets, or strategy optimization.
NO mining of thresholds — reuse behavioral states + IS-frozen terciles.

Protocol:
  - Decision clocks T every 5m from 09:35 through 11:00
  - State uses only bars with ny_min <= T
  - Path outcomes start at NEXT bar open after T (disjoint windows)
  - Distances in R-units of *current* volatility known at T
  - Splits: IS 2010–21 / Val 2022–24 / OOS 2025–26
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
# 09:35 … 11:00 inclusive
DECISION_OFFSETS = tuple(range(5, 91, 5))
PATH_HORIZONS = (5, 10, 15, 30)
R_LEVELS = (0.5, 1.0)  # multiples of vol_unit
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


def build_day_context(df: pd.DataFrame) -> pd.DataFrame:
    facts = pd.read_parquet(art("ny_open_day_facts.parquet"))
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


def state_at_T(rth_to_T: pd.DataFrame, ctx: dict, T_ny: int) -> dict[str, float] | None:
    """Causal state + current vol unit using only bars with ny_min <= T."""
    if len(rth_to_T) < 3:
        return None
    if T_ny not in set(rth_to_T["ny_min"].tolist()):
        return None
    rth_to_T = rth_to_T[rth_to_T["ny_min"] <= T_ny].reset_index(drop=True)
    o930 = float(ctx["open_930"])
    onr = float(ctx["onr"])
    if onr <= 0:
        return None
    c = rth_to_T["close"].to_numpy(float)
    h = rth_to_T["high"].to_numpy(float)
    l = rth_to_T["low"].to_numpy(float)
    o = rth_to_T["open"].to_numpy(float)
    last_c = float(c[-1])
    elapsed = max(int(T_ny - NY_OPEN), 1)

    rng = float(h.max() - l.min())
    rng_onr = rng / onr
    move = last_c - o930
    move_onr = move / onr
    path = float(np.sum(np.abs(np.diff(c)))) if len(c) > 1 else abs(move)
    path_onr = path / onr
    speed = abs(move_onr) / elapsed

    # Current volatility unit (known at T): mean true range so far, floored by 5% ONR
    prev_c = np.concatenate([[o[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    atr = float(np.mean(tr)) if len(tr) else float(rng / max(elapsed, 1))
    vol_unit = max(atr, 0.05 * onr, 1.0)  # pts; never below 1pt

    onr_vs_med = float(ctx["onr_vs_med"]) if np.isfinite(ctx["onr_vs_med"]) else np.nan
    if abs(move) < 0.25:
        persist_frac = np.nan
        dir_sign = 0.0
    else:
        dir_sign = 1.0 if move > 0 else -1.0
        deltas = np.diff(c)
        persist_frac = float(np.mean(np.sign(deltas) == dir_sign)) if len(deltas) else np.nan

    loc_now = (last_c - float(ctx["onl"])) / onr
    on_rv = float(ctx["on_rv"])
    path_vs_onrv = path / on_rv if on_rv > 0 else np.nan

    return {
        "elapsed": float(elapsed),
        "rng_onr": rng_onr,
        "move_onr": move_onr,
        "abs_move_onr": abs(move_onr),
        "path_onr": path_onr,
        "speed": speed,
        "vol_exp": rng_onr,
        "onr_vs_med": onr_vs_med,
        "persist_frac": persist_frac,
        "dir_sign": dir_sign,
        "loc_now": loc_now,
        "open_loc": float(ctx["open_loc"]),
        "path_vs_onrv": path_vs_onrv,
        "gap_onr": float(ctx["gap_onr"]),
        "onr": onr,
        "atr": atr,
        "vol_unit": vol_unit,
        "vol_unit_onr": vol_unit / onr,
    }


def _first_hit_times(
    highs: np.ndarray,
    lows: np.ndarray,
    entry: float,
    thr: float,
) -> tuple[int | None, int | None, bool]:
    """
    Scan bars after entry. Return (t_up, t_dn, ambiguous_same_bar).
    Times are 1-indexed minutes from entry bar (bar 0 = entry bar).
    Same-bar both-hits → ambiguous (stop-first convention: count as neither for asym).
    """
    t_up = None
    t_dn = None
    for i in range(len(highs)):
        hit_up = highs[i] >= entry + thr
        hit_dn = lows[i] <= entry - thr
        if hit_up and hit_dn:
            return i + 1, i + 1, True
        if hit_up and t_up is None:
            t_up = i + 1
        if hit_dn and t_dn is None:
            t_dn = i + 1
        if t_up is not None and t_dn is not None:
            break
    return t_up, t_dn, False


def path_outcomes(
    rth_full: pd.DataFrame,
    T_ny: int,
    vol_unit: float,
    onr: float,
    dir_sign: float,
) -> dict[str, float] | None:
    """Path metrics from next-bar open after T, over PATH_HORIZONS.

    Two R definitions (both causal at T):
      - local: vol_unit = max(mean TR, 0.05*ONR, 1pt)
      - structural: onr_R = 0.25 * ONR  (economically larger / rarer)
    """
    after = rth_full[rth_full["ny_min"] > T_ny].reset_index(drop=True)
    need = max(PATH_HORIZONS)
    if len(after) < need:
        return None
    entry = float(after.iloc[0]["open"])
    highs = after["high"].to_numpy(float)
    lows = after["low"].to_numpy(float)
    closes = after["close"].to_numpy(float)
    onr_R = max(0.25 * onr, 1.0)
    out: dict[str, float] = {"entry": entry, "onr_R": onr_R}

    def _pack_hits(h_slice, l_slice, thr: float, prefix: str, H: int) -> None:
        t_up, t_dn, amb = _first_hit_times(h_slice, l_slice, entry, thr)
        if amb:
            long_hit = np.nan
            short_hit = np.nan
        elif t_up is not None and (t_dn is None or t_up < t_dn):
            long_hit = 1.0
            short_hit = 0.0
        elif t_dn is not None and (t_up is None or t_dn < t_up):
            long_hit = 0.0
            short_hit = 1.0
        else:
            long_hit = np.nan
            short_hit = np.nan
        out[f"hit_{prefix}_long_{H}"] = long_hit
        out[f"hit_{prefix}_short_{H}"] = short_hit
        out[f"amb_{prefix}_{H}"] = 1.0 if amb else 0.0
        resolved = (not amb) and (t_up is not None or t_dn is not None)
        out[f"resolved_{prefix}_{H}"] = 1.0 if resolved else 0.0
        if dir_sign > 0:
            out[f"hit_{prefix}_dir_{H}"] = long_hit
        elif dir_sign < 0:
            out[f"hit_{prefix}_dir_{H}"] = short_hit
        else:
            out[f"hit_{prefix}_dir_{H}"] = np.nan

    for H in PATH_HORIZONS:
        h_slice = highs[:H]
        l_slice = lows[:H]
        c_end = float(closes[H - 1])
        out[f"fwd_{H}"] = c_end - entry
        out[f"fwd_dir_{H}"] = (c_end - entry) * dir_sign if dir_sign != 0 else np.nan

        mfe_long = float(h_slice.max() - entry)
        mae_long = float(entry - l_slice.min())
        out[f"mfe_long_{H}"] = mfe_long
        out[f"mae_long_{H}"] = mae_long
        out[f"mfe_long_R_{H}"] = mfe_long / vol_unit
        out[f"mae_long_R_{H}"] = mae_long / vol_unit
        out[f"mfe_long_onrR_{H}"] = mfe_long / onr_R
        out[f"mae_long_onrR_{H}"] = mae_long / onr_R

        fav = h_slice - entry
        adv = entry - l_slice
        t_mfe = int(np.argmax(fav)) + 1
        t_mae = int(np.argmax(adv)) + 1
        out[f"t_mfe_long_{H}"] = float(t_mfe)
        out[f"t_mae_long_{H}"] = float(t_mae)
        out[f"mfe_before_mae_long_{H}"] = 1.0 if t_mfe < t_mae else (0.0 if t_mae < t_mfe else np.nan)

        mfe_short = mae_long
        mae_short = mfe_long
        out[f"mfe_short_R_{H}"] = mfe_short / vol_unit
        out[f"mae_short_R_{H}"] = mae_short / vol_unit
        t_mfe_s = t_mae
        t_mae_s = t_mfe
        out[f"t_mfe_short_{H}"] = float(t_mfe_s)
        out[f"t_mae_short_{H}"] = float(t_mae_s)
        out[f"mfe_before_mae_short_{H}"] = (
            1.0 if t_mfe_s < t_mae_s else (0.0 if t_mae_s < t_mfe_s else np.nan)
        )

        if dir_sign > 0:
            out[f"mfe_before_mae_dir_{H}"] = out[f"mfe_before_mae_long_{H}"]
            out[f"t_mfe_dir_{H}"] = float(t_mfe)
            out[f"t_mae_dir_{H}"] = float(t_mae)
            out[f"mfe_dir_R_{H}"] = mfe_long / vol_unit
            out[f"mae_dir_R_{H}"] = mae_long / vol_unit
        elif dir_sign < 0:
            out[f"mfe_before_mae_dir_{H}"] = out[f"mfe_before_mae_short_{H}"]
            out[f"t_mfe_dir_{H}"] = float(t_mfe_s)
            out[f"t_mae_dir_{H}"] = float(t_mae_s)
            out[f"mfe_dir_R_{H}"] = mfe_short / vol_unit
            out[f"mae_dir_R_{H}"] = mae_short / vol_unit
        else:
            out[f"mfe_before_mae_dir_{H}"] = np.nan
            out[f"t_mfe_dir_{H}"] = np.nan
            out[f"t_mae_dir_{H}"] = np.nan
            out[f"mfe_dir_R_{H}"] = np.nan
            out[f"mae_dir_R_{H}"] = np.nan

        for r_mult in R_LEVELS:
            tag = f"{r_mult:g}".replace(".", "p")
            _pack_hits(h_slice, l_slice, r_mult * vol_unit, f"p{tag}R", H)
            _pack_hits(h_slice, l_slice, r_mult * onr_R, f"p{tag}onrR", H)
    return out


def rate_of(series: pd.Series) -> dict[str, float]:
    x = series.to_numpy(float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return {"n": 0, "rate": np.nan}
    return {"n": int(n), "rate": float(np.mean(x))}


def win_rate(series: pd.Series) -> dict[str, float]:
    """P(x > 0) for signed returns."""
    x = series.to_numpy(float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return {"n": 0, "rate": np.nan}
    return {"n": int(n), "rate": float(np.mean(x > 0))}


def main() -> None:
    print("=== NQ Path-Asymmetry Discovery ===", flush=True)
    panel_path = art("ny_open_path_asym_panel.parquet")
    reuse = panel_path.exists()
    if reuse:
        probe = pd.read_parquet(panel_path)
        reuse = "onr_R" in probe.columns
        if reuse:
            panel = probe
            n_days = int(panel["session_date"].nunique())
            print(f"Reusing panel {panel_path}", flush=True)
            print(f"Panel rows: {len(panel)}  days: {n_days}", flush=True)
        else:
            del probe

    if not reuse:
        df = load_nq()
        print("Building day context...", flush=True)
        ctx_df = build_day_context(df)
        print(f"Days: {len(ctx_df)}", flush=True)
        ctx_map = {r["session_date"]: r for _, r in ctx_df.iterrows()}

        print("Indexing RTH...", flush=True)
        rth_map: dict = {}
        for sd, g in df.groupby("session_date", sort=False):
            if sd not in ctx_map:
                continue
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 12 * 60)].reset_index(drop=True)
            if len(rth) >= 100:
                rth_map[sd] = rth
        print(f"RTH days: {len(rth_map)}", flush=True)

        panel_rows: list[dict] = []
        n_days = 0
        for sd, ctx in ctx_map.items():
            rth = rth_map.get(sd)
            if rth is None:
                continue
            n_days += 1
            for off in DECISION_OFFSETS:
                T = NY_OPEN + off
                to_T = rth[rth["ny_min"] <= T]
                st = state_at_T(to_T, ctx, T)
                if st is None:
                    continue
                path = path_outcomes(rth, T, st["vol_unit"], st["onr"], st["dir_sign"])
                if path is None:
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
                        **path,
                    }
                )
            if n_days % 500 == 0:
                print(f"  processed {n_days} days, panel={len(panel_rows)}", flush=True)

        panel = pd.DataFrame(panel_rows)
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows: {len(panel)}  days: {n_days}  -> {panel_path}", flush=True)

    # --- IS tercile thresholds per (T_offset, feature) ---
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
        "vol_unit_onr",
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
    with open(art("ny_open_path_asym_thresholds_IS.json"), "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2)

    def conditions_for(sub: pd.DataFrame, off: int) -> dict[str, pd.Series]:
        th = {feat: thresholds.get(feat, {}).get(off, {}) for feat in features}
        c: dict[str, pd.Series] = {}
        if th["rng_onr"]:
            c["vol_expansion_high"] = sub["rng_onr"] >= th["rng_onr"]["p66"]
            c["vol_expansion_low"] = sub["rng_onr"] <= th["rng_onr"]["p33"]
        if th["onr_vs_med"] and th["rng_onr"]:
            c["compress_then_expand"] = (sub["onr_vs_med"] <= th["onr_vs_med"]["p33"]) & (
                sub["rng_onr"] >= th["rng_onr"]["p66"]
            )
            c["wide_ON_quiet_open"] = (sub["onr_vs_med"] >= th["onr_vs_med"]["p66"]) & (
                sub["rng_onr"] <= th["rng_onr"]["p33"]
            )
        if th["abs_move_onr"]:
            c["strong_dir_move"] = (sub["abs_move_onr"] >= th["abs_move_onr"]["p66"]) & (
                sub["dir_sign"] != 0
            )
            c["weak_dir_move"] = sub["abs_move_onr"] <= th["abs_move_onr"]["p33"]
        if th["persist_frac"]:
            c["high_persistence"] = (sub["persist_frac"] >= th["persist_frac"]["p66"]) & (
                sub["dir_sign"] != 0
            )
            c["low_persistence"] = (sub["persist_frac"] <= th["persist_frac"]["p33"]) & (
                sub["dir_sign"] != 0
            )
        if th["speed"]:
            c["fast_move"] = (sub["speed"] >= th["speed"]["p66"]) & (sub["dir_sign"] != 0)
            c["slow_move"] = sub["speed"] <= th["speed"]["p33"]
        if th["open_loc"]:
            c["open_near_ONH"] = sub["open_loc"] >= 0.80
            c["open_near_ONL"] = sub["open_loc"] <= 0.20
            c["open_mid"] = (sub["open_loc"] > 0.40) & (sub["open_loc"] < 0.60)
        c["price_near_ONH"] = sub["loc_now"] >= 0.90
        c["price_near_ONL"] = sub["loc_now"] <= 0.10
        if th["path_vs_onrv"]:
            c["path_vs_ON_high"] = sub["path_vs_onrv"] >= th["path_vs_onrv"]["p66"]
        if th["vol_unit_onr"]:
            c["high_local_vol"] = sub["vol_unit_onr"] >= th["vol_unit_onr"]["p66"]
            c["low_local_vol"] = sub["vol_unit_onr"] <= th["vol_unit_onr"]["p33"]
        if "strong_dir_move" in c and "high_persistence" in c:
            c["strong_and_persistent"] = c["strong_dir_move"] & c["high_persistence"]
        if "strong_dir_move" in c and "low_persistence" in c:
            c["strong_but_choppy"] = c["strong_dir_move"] & c["low_persistence"]
        if "fast_move" in c and "vol_expansion_high" in c:
            c["fast_and_expanded"] = c["fast_move"] & c["vol_expansion_high"]
        # "wait" style: quiet / compressed / mid — opportunity structure may be poor
        if "vol_expansion_low" in c and "weak_dir_move" in c:
            c["quiet_wait"] = c["vol_expansion_low"] & c["weak_dir_move"]
        return c

    results: list[dict[str, Any]] = []
    for off in DECISION_OFFSETS:
        sub = panel[panel["T_offset"] == off].copy()
        if len(sub) < 200:
            continue
        conds = conditions_for(sub, off)
        # always include unconditional pseudo-condition
        conds = {"UNCONDITIONAL": pd.Series(True, index=sub.index), **conds}

        for cname, mask in conds.items():
            for split in ("IS", "Validation", "OOS", "ALL"):
                base = sub if split == "ALL" else sub[sub["split"] == split]
                m = mask.reindex(base.index).fillna(False)
                cond = base.loc[m.to_numpy()]
                unc = base
                if len(cond) < 30 and cname != "UNCONDITIONAL":
                    continue
                if len(cond) < 20:
                    continue

                for H in PATH_HORIZONS:
                    # directional accuracy (should remain near 50% for the thesis)
                    dir_col = f"fwd_dir_{H}"
                    fwd_col = f"fwd_{H}"
                    d_dir = win_rate(cond[dir_col])
                    d_raw = win_rate(cond[fwd_col])

                    row: dict[str, Any] = {
                        "condition": cname,
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(len(cond)),
                        "n_unc": int(len(unc)),
                        "rate": float(len(cond) / len(unc)),
                        "dir_win": d_dir["rate"],
                        "dir_n": d_dir["n"],
                        "raw_long_win": d_raw["rate"],
                        "vol_unit_med": float(cond["vol_unit"].median()),
                        "onr_R_med": float(cond["onr_R"].median()) if "onr_R" in cond.columns else np.nan,
                    }

                    # MFE before MAE
                    for side in ("long", "short", "dir"):
                        col = f"mfe_before_mae_{side}_{H}"
                        r = rate_of(cond[col])
                        u = rate_of(unc[col])
                        row[f"mfe_first_{side}"] = r["rate"]
                        row[f"mfe_first_{side}_n"] = r["n"]
                        row[f"unc_mfe_first_{side}"] = u["rate"]
                        row[f"delta_mfe_first_{side}"] = (
                            r["rate"] - u["rate"] if r["n"] and u["n"] else np.nan
                        )
                        if side == "dir":
                            t_mfe = cond[f"t_mfe_dir_{H}"].to_numpy(float)
                            t_mae = cond[f"t_mae_dir_{H}"].to_numpy(float)
                        else:
                            t_mfe = cond[f"t_mfe_{side}_{H}"].to_numpy(float)
                            t_mae = cond[f"t_mae_{side}_{H}"].to_numpy(float)
                        ok = np.isfinite(t_mfe) & np.isfinite(t_mae)
                        row[f"mean_t_mfe_{side}"] = float(np.mean(t_mfe[ok])) if ok.any() else np.nan
                        row[f"mean_t_mae_{side}"] = float(np.mean(t_mae[ok])) if ok.any() else np.nan

                    # max excursion in R
                    row["mean_mfe_dir_R"] = float(np.nanmean(cond[f"mfe_dir_R_{H}"].to_numpy(float)))
                    row["mean_mae_dir_R"] = float(np.nanmean(cond[f"mae_dir_R_{H}"].to_numpy(float)))
                    row["mean_mfe_long_R"] = float(np.nanmean(cond[f"mfe_long_R_{H}"].to_numpy(float)))
                    row["mean_mae_long_R"] = float(np.nanmean(cond[f"mae_long_R_{H}"].to_numpy(float)))

                    for r_mult in R_LEVELS:
                        tag = f"{r_mult:g}".replace(".", "p")
                        for scale in ("R", "onrR"):
                            prefix = f"p{tag}{scale}"
                            for side in ("long", "short", "dir"):
                                col = f"hit_{prefix}_{side}_{H}"
                                r = rate_of(cond[col])
                                u = rate_of(unc[col])
                                row[f"{prefix}_{side}"] = r["rate"]
                                row[f"{prefix}_{side}_n"] = r["n"]
                                row[f"unc_{prefix}_{side}"] = u["rate"]
                                row[f"delta_{prefix}_{side}"] = (
                                    r["rate"] - u["rate"] if r["n"] and u["n"] else np.nan
                                )
                            res = rate_of(cond[f"resolved_{prefix}_{H}"])
                            row[f"{prefix}_resolved"] = res["rate"]
                            amb = rate_of(cond[f"amb_{prefix}_{H}"])
                            row[f"{prefix}_amb"] = amb["rate"]

                    results.append(row)

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("ny_open_path_asym_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

    # --- Score candidates: path asym with near-coin direction ---
    # Strong: IS p1R_dir >= 0.55, delta vs unc >= 0.05, Val&OOS >= 0.52, same sign delta
    # Soft: IS >= 0.53, Val&OOS both > unc, dir_win in [0.45, 0.55]
    is_rows = res_df[(res_df["split"] == "IS") & (res_df["condition"] != "UNCONDITIONAL")]
    candidates = []
    for _, r in is_rows.iterrows():
        cname, off, H = r["condition"], int(r["T_offset"]), int(r["horizon"])
        val = res_df[
            (res_df["condition"] == cname)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "Validation")
        ]
        oos = res_df[
            (res_df["condition"] == cname)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "OOS")
        ]
        if len(val) == 0 or len(oos) == 0:
            continue
        v, o = val.iloc[0], oos.iloc[0]

        for metric, key in (
            ("p1R_dir", "p1R_dir"),
            ("p0p5R_dir", "p0p5R_dir"),
            ("p1onrR_dir", "p1onrR_dir"),
            ("p0p5onrR_dir", "p0p5onrR_dir"),
            ("mfe_first_dir", "mfe_first_dir"),
        ):
            if metric == "mfe_first_dir":
                is_p = r.get("mfe_first_dir")
                is_d = r.get("delta_mfe_first_dir")
                v_p, o_p = v.get("mfe_first_dir"), o.get("mfe_first_dir")
                v_d, o_d = v.get("delta_mfe_first_dir"), o.get("delta_mfe_first_dir")
                is_n = r.get("mfe_first_dir_n")
                resolved_key = None
            else:
                is_p = r.get(key)
                is_d = r.get(f"delta_{key}")
                v_p, o_p = v.get(key), o.get(key)
                v_d = v.get(f"delta_{key}")
                o_d = o.get(f"delta_{key}")
                is_n = r.get(f"{key}_n")
                resolved_key = key.replace("_dir", "_resolved")

            if not (isinstance(is_p, (int, float)) and np.isfinite(is_p)):
                continue
            if not (isinstance(is_n, (int, float)) and is_n >= 80):
                continue

            dir_win = r.get("dir_win")
            near_coin = (
                isinstance(dir_win, (int, float))
                and np.isfinite(dir_win)
                and 0.45 <= dir_win <= 0.55
            )
            is_resolved = float(r.get(resolved_key, np.nan)) if resolved_key else np.nan

            soft = (
                is_p >= 0.53
                and isinstance(is_d, (int, float))
                and np.isfinite(is_d)
                and is_d >= 0.03
                and isinstance(v_p, (int, float))
                and isinstance(o_p, (int, float))
                and isinstance(v_d, (int, float))
                and isinstance(o_d, (int, float))
                and v_d > 0
                and o_d > 0
                and v_p >= 0.50
                and o_p >= 0.50
            )
            # Strong requires aggregate Val/OOS AND will be year-checked later
            strong_agg = (
                is_p >= 0.55
                and isinstance(is_d, (int, float))
                and np.isfinite(is_d)
                and is_d >= 0.05
                and isinstance(v_p, (int, float))
                and v_p >= 0.52
                and isinstance(o_p, (int, float))
                and o_p >= 0.52
                and isinstance(v_d, (int, float))
                and isinstance(o_d, (int, float))
                and v_d > 0
                and o_d > 0
            )
            abs_edge = (
                is_p >= 0.58
                and isinstance(v_p, (int, float))
                and isinstance(o_p, (int, float))
                and v_p >= 0.55
                and o_p >= 0.55
            )

            if strong_agg or soft or abs_edge:
                candidates.append(
                    {
                        "condition": cname,
                        "T_offset": off,
                        "horizon": H,
                        "metric": metric,
                        "tier": "strong_agg" if strong_agg else ("abs_edge" if abs_edge else "soft"),
                        "near_coin_dir": bool(near_coin),
                        "IS_n": int(r["n"]),
                        "IS_resolved_n": int(is_n) if is_n == is_n else 0,
                        "IS_resolved_rate": float(is_resolved) if np.isfinite(is_resolved) else None,
                        "IS_rate": float(r["rate"]),
                        "IS_p": float(is_p),
                        "IS_delta": float(is_d) if isinstance(is_d, (int, float)) and np.isfinite(is_d) else None,
                        "IS_dir_win": float(dir_win) if isinstance(dir_win, (int, float)) and np.isfinite(dir_win) else None,
                        "Val_p": float(v_p) if isinstance(v_p, (int, float)) and np.isfinite(v_p) else None,
                        "Val_delta": float(v_d) if isinstance(v_d, (int, float)) and np.isfinite(v_d) else None,
                        "OOS_p": float(o_p) if isinstance(o_p, (int, float)) and np.isfinite(o_p) else None,
                        "OOS_delta": float(o_d) if isinstance(o_d, (int, float)) and np.isfinite(o_d) else None,
                        "IS_mean_mfe_dir_R": float(r["mean_mfe_dir_R"]) if np.isfinite(r["mean_mfe_dir_R"]) else None,
                        "IS_mean_mae_dir_R": float(r["mean_mae_dir_R"]) if np.isfinite(r["mean_mae_dir_R"]) else None,
                    }
                )

    # Year-stability gate for promoting strong_agg → strong
    def metric_col(metric: str, H: int) -> str:
        if metric == "mfe_first_dir":
            return f"mfe_before_mae_dir_{H}"
        if metric.startswith("p") and metric.endswith("_dir"):
            # p1R_dir / p0p5onrR_dir → hit_p1R_dir_H
            return f"hit_{metric}_{H}"
        return f"hit_{metric}_{H}"

    for c in candidates:
        sub = panel[
            (panel["T_offset"] == c["T_offset"]) & (panel["year"].isin([2025, 2026]))
        ].copy()
        y_rates = {}
        if len(sub) and c["condition"] in conditions_for(sub, c["T_offset"]):
            mask = conditions_for(sub, c["T_offset"])[c["condition"]]
            hit = sub.loc[mask.to_numpy()]
            col = metric_col(c["metric"], c["horizon"])
            if col in hit.columns:
                for y in (2025, 2026):
                    rr = rate_of(hit.loc[hit["year"] == y, col])
                    y_rates[y] = rr
        c["y2025"] = y_rates.get(2025, {}).get("rate")
        c["y2025_n"] = y_rates.get(2025, {}).get("n", 0)
        c["y2026"] = y_rates.get(2026, {}).get("rate")
        c["y2026_n"] = y_rates.get(2026, {}).get("n", 0)
        year_ok = (
            isinstance(c["y2025"], (int, float))
            and isinstance(c["y2026"], (int, float))
            and np.isfinite(c["y2025"])
            and np.isfinite(c["y2026"])
            and c["y2025"] >= 0.52
            and c["y2026"] >= 0.52
            and c["y2025_n"] >= 20
            and c["y2026_n"] >= 20
        )
        c["year_stable"] = bool(year_ok)
        if c["tier"] == "strong_agg" and year_ok:
            c["tier"] = "strong"
        elif c["tier"] == "strong_agg":
            c["tier"] = "soft"  # demote: aggregate OOS hid year flip

    for c in candidates:
        floor = min(x for x in (c["IS_p"], c["Val_p"], c["OOS_p"]) if x is not None)
        c["score"] = floor

    tier_rank = {"strong": 0, "abs_edge": 1, "soft": 2, "strong_agg": 3}
    candidates.sort(key=lambda x: (tier_rank.get(x["tier"], 9), -x["score"], -x["IS_n"]))

    # Unconditional baselines at key clocks
    unc_baselines = []
    for off in (5, 15, 30, 60, 90):
        for H in (15, 30):
            u = res_df[
                (res_df["condition"] == "UNCONDITIONAL")
                & (res_df["T_offset"] == off)
                & (res_df["horizon"] == H)
                & (res_df["split"] == "IS")
            ]
            if len(u) == 0:
                continue
            uu = u.iloc[0]
            unc_baselines.append(
                {
                    "T_offset": off,
                    "horizon": H,
                    "n": int(uu["n"]),
                    "dir_win": uu.get("dir_win"),
                    "p0p5R_dir": uu.get("p0p5R_dir"),
                    "p1R_dir": uu.get("p1R_dir"),
                    "p0p5onrR_dir": uu.get("p0p5onrR_dir"),
                    "p1onrR_dir": uu.get("p1onrR_dir"),
                    "mfe_first_dir": uu.get("mfe_first_dir"),
                    "p1R_resolved": uu.get("p1R_resolved"),
                    "p1onrR_resolved": uu.get("p1onrR_resolved"),
                    "vol_unit_med": uu.get("vol_unit_med"),
                    "onr_R_med": uu.get("onr_R_med"),
                }
            )

    # OOS year break for top candidates (reuse fields already on candidates)
    year_breaks = []
    for c in candidates[:15]:
        year_breaks.append(
            {
                "condition": c["condition"],
                "T_offset": c["T_offset"],
                "horizon": c["horizon"],
                "metric": c["metric"],
                "year": 2025,
                "n": c.get("y2025_n"),
                "rate": c.get("y2025"),
            }
        )
        year_breaks.append(
            {
                "condition": c["condition"],
                "T_offset": c["T_offset"],
                "horizon": c["horizon"],
                "metric": c["metric"],
                "year": 2026,
                "n": c.get("y2026_n"),
                "rate": c.get("y2026"),
            }
        )

    # Compare quiet_wait resolution vs unconditional (local R and structural onrR)
    wait_compare = []
    for off in DECISION_OFFSETS:
        for H in (15, 30):
            q = res_df[
                (res_df["condition"] == "quiet_wait")
                & (res_df["T_offset"] == off)
                & (res_df["horizon"] == H)
                & (res_df["split"] == "IS")
            ]
            u = res_df[
                (res_df["condition"] == "UNCONDITIONAL")
                & (res_df["T_offset"] == off)
                & (res_df["horizon"] == H)
                & (res_df["split"] == "IS")
            ]
            if len(q) and len(u):
                qq, uu = q.iloc[0], u.iloc[0]
                wait_compare.append(
                    {
                        "T_offset": off,
                        "horizon": H,
                        "quiet_n": int(qq["n"]),
                        "quiet_p1R_resolved": qq.get("p1R_resolved"),
                        "unc_p1R_resolved": uu.get("p1R_resolved"),
                        "delta_p1R_resolved": (
                            float(qq["p1R_resolved"]) - float(uu["p1R_resolved"])
                            if np.isfinite(qq.get("p1R_resolved", np.nan))
                            and np.isfinite(uu.get("p1R_resolved", np.nan))
                            else None
                        ),
                        "quiet_p1onrR_resolved": qq.get("p1onrR_resolved"),
                        "unc_p1onrR_resolved": uu.get("p1onrR_resolved"),
                        "delta_p1onrR_resolved": (
                            float(qq["p1onrR_resolved"]) - float(uu["p1onrR_resolved"])
                            if np.isfinite(qq.get("p1onrR_resolved", np.nan))
                            and np.isfinite(uu.get("p1onrR_resolved", np.nan))
                            else None
                        ),
                        "quiet_p1R_dir": qq.get("p1R_dir"),
                        "unc_p1R_dir": uu.get("p1R_dir"),
                        "quiet_p1onrR_dir": qq.get("p1onrR_dir"),
                        "unc_p1onrR_dir": uu.get("p1onrR_dir"),
                    }
                )

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    abs_n = sum(1 for c in candidates if c["tier"] == "abs_edge")
    near_coin_survivors = [c for c in candidates if c.get("near_coin_dir")]
    onr_metric_hits = [c for c in candidates if "onrR" in c["metric"]]
    local_resolved_med = float(
        np.nanmedian([u.get("p1R_resolved") for u in unc_baselines if u.get("p1R_resolved") is not None])
    )
    onr_resolved_med = float(
        np.nanmedian([u.get("p1onrR_resolved") for u in unc_baselines if u.get("p1onrR_resolved") is not None])
    )

    # Hostile notes for verdict text
    hostile = []
    if np.isfinite(local_resolved_med) and local_resolved_med >= 0.90:
        hostile.append(
            f"Local-ATR +1R resolves ~{100*local_resolved_med:.0f}% within 15–30m — "
            "these are micro path flips, not rare opportunity moments."
        )
    if np.isfinite(onr_resolved_med):
        hostile.append(
            f"Structural ONR-R (0.25·ONR) +1R resolves ~{100*onr_resolved_med:.0f}% — "
            "the economically larger hurdle."
        )
    if not onr_metric_hits:
        hostile.append("No soft/strong survivors on structural ONR-R path metrics.")
    demoted = sum(1 for c in candidates if c.get("year_stable") is False and c["tier"] == "soft")
    if demoted:
        hostile.append(
            "Several aggregate-OOS 'survivors' flip between 2025 and 2026 — demoted from strong."
        )

    if strong_n > 0:
        verdict = "A_path_asymmetry_found"
        verdict_text = (
            "Observable states produce material path asymmetry (+R before −R) "
            "that survives IS→Val→OOS with year stability, while directional win stays near coin-flip."
        )
    elif soft_n > 0 or abs_n > 0:
        verdict = "B_weak_path_asymmetry"
        verdict_text = (
            "Soft path-asymmetry leftovers exist at ~53–56% but fail year-stability and/or "
            "are micro-R artifacts (local ATR almost always resolves). Not strategy-ready."
        )
    else:
        verdict = "C_no_path_asymmetry"
        verdict_text = (
            "No tested morning state produces meaningful R-normalized path asymmetry "
            "after causal cleanup. Direction and path questions both fail for this feature family."
        )
    if hostile:
        verdict_text = verdict_text + " " + " ".join(hostile)

    report = {
        "stage": "path_asymmetry_discovery",
        "verdict": verdict,
        "verdict_text": verdict_text,
        "hostile_notes": hostile,
        "protocol": {
            "decision_offsets_min": list(DECISION_OFFSETS),
            "horizons_min": list(PATH_HORIZONS),
            "R_levels": list(R_LEVELS),
            "vol_unit_local": "max(mean_TR_0930_to_T, 0.05*ONR, 1pt)",
            "vol_unit_structural": "0.25*ONR",
            "entry_clock": "next bar open after T",
            "ambiguous_same_bar": "excluded from hit rates (neither)",
            "splits": "IS 2010-21 / Val 2022-24 / OOS 2025-26",
            "thresholds": "IS terciles only",
            "strong_requires": "year-stable 2025&2026 both >=52% with n>=20",
        },
        "panel": {"rows": int(len(panel)), "days": int(n_days)},
        "unc_baselines_IS": unc_baselines,
        "n_candidates": len(candidates),
        "n_strong": strong_n,
        "n_soft": soft_n,
        "n_abs_edge": abs_n,
        "n_near_coin_survivors": len(near_coin_survivors),
        "n_onrR_metric_survivors": len(onr_metric_hits),
        "top_candidates": candidates[:25],
        "year_breaks_top": year_breaks,
        "wait_compare_IS": wait_compare[:20],
        "kill_criteria": {
            "strong": (
                "IS p>=0.55, delta_unc>=0.05, Val&OOS p>=0.52, positive deltas, "
                "n_resolved>=80, AND 2025&2026 both >=0.52 with n>=20"
            ),
            "soft": "IS p>=0.53, delta>=0.03, Val&OOS delta>0 and p>=0.50",
            "abs_edge": "IS p>=0.58, Val&OOS p>=0.55",
        },
    }
    with open(art("ny_open_path_asym_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Markdown report
    md = []
    md.append("# NQ Path-Asymmetry Discovery")
    md.append("")
    md.append(f"**Verdict: `{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    md.append(
        "Prior kills (do not reopen): named strategy · level confirmation · "
        "simple state→direction / raw-point magnitude."
    )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Question")
    md.append("")
    md.append(
        "> Are there observable states (09:30–11:00) where the future price path is "
        "meaningfully asymmetric in R-space — e.g. P(+1R before −1R) ≫ 50% — "
        "even when directional accuracy stays near 50%?"
    )
    md.append("")
    md.append("## Protocol")
    md.append("")
    md.append("| Rule | Implementation |")
    md.append("|------|----------------|")
    md.append("| Clocks T | every 5m from 09:35–11:00 |")
    md.append("| State | bars with `ny_min <= T` only |")
    md.append("| Path start | **next bar open** after T |")
    md.append("| Local R | `max(mean TR 09:30→T, 0.05·ONR, 1pt)` |")
    md.append("| Structural R | `0.25·ONR` (rarer / economically larger) |")
    md.append("| Metrics | MFE≺MAE; P(+0.5R≺−0.5R); P(+1R≺−1R); excursions; time-to-MFE/MAE |")
    md.append("| Ambiguous bar | both sides same 1m → excluded from hit rates |")
    md.append("| Strong bar | also requires 2025 **and** 2026 ≥52% (n≥20) |")
    md.append("| Thresholds | IS terciles frozen |")
    md.append("| Splits | IS 2010–21 / Val 2022–24 / OOS 2025–26 |")
    md.append("")
    md.append(f"Panel: **{len(panel):,}** rows · **{n_days:,}** days.")
    md.append("")
    md.append("## Unconditional IS baselines")
    md.append("")
    md.append(
        "| T+ | H | n | dir win | local P(+1R≺) | local resolved | onr P(+1R≺) | onr resolved | med local R |"
    )
    md.append(
        "|----|---|---|---------|---------------|----------------|-------------|--------------|-------------|"
    )

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    for u in unc_baselines:
        vu = u.get("vol_unit_med")
        vu_s = f"{vu:.1f}" if isinstance(vu, (int, float)) and np.isfinite(vu) else "—"
        md.append(
            f"| +{u['T_offset']}m | {u['horizon']} | {u['n']} | {pct(u.get('dir_win'))} | "
            f"{pct(u.get('p1R_dir'))} | {pct(u.get('p1R_resolved'))} | "
            f"{pct(u.get('p1onrR_dir'))} | {pct(u.get('p1onrR_resolved'))} | {vu_s} |"
        )
    md.append("")
    md.append("## Hostile finding on local R")
    md.append("")
    md.append(
        "Local-ATR R almost always resolves inside 15–30 minutes. "
        "A ~55% P(+0.5R before −0.5R) on that scale is a **microstructure** result, "
        "not evidence of rare 1–2/day opportunity structure."
    )
    md.append("")
    md.append("Structural `0.25·ONR` is the harder / more tradable hurdle.")
    md.append("")
    md.append("## Candidates")
    md.append("")
    md.append(
        f"Strong (year-stable): **{strong_n}** · Soft: **{soft_n}** · Abs-edge: **{abs_n}** · "
        f"Near-coin-dir: **{len(near_coin_survivors)}** · Structural-ONR-R survivors: **{len(onr_metric_hits)}**"
    )
    md.append("")
    if not candidates:
        md.append("**None** cleared soft / strong / abs-edge bars.")
    else:
        md.append(
            "| Tier | State | T+ | H | Metric | IS n | IS p | Δunc | dir | Val | OOS | 2025 | 2026 |"
        )
        md.append(
            "|------|-------|----|---|--------|------|------|------|-----|-----|-----|------|------|"
        )
        for c in candidates[:20]:
            dlt = f"{100 * c['IS_delta']:.1f}pp" if c["IS_delta"] is not None else "—"
            dw = pct(c["IS_dir_win"])
            md.append(
                f"| {c['tier']} | `{c['condition']}` | +{c['T_offset']}m | {c['horizon']} | "
                f"{c['metric']} | {c['IS_n']} | {pct(c['IS_p'])} | {dlt} | {dw} | "
                f"{pct(c['Val_p'])} | {pct(c['OOS_p'])} | {pct(c.get('y2025'))} | {pct(c.get('y2026'))} |"
            )
        md.append("")

    md.append("## Quiet / wait structure (IS)")
    md.append("")
    md.append(
        "Does `quiet_wait` (low range expansion ∩ weak move) reduce resolution "
        "(market says wait)?"
    )
    md.append("")
    md.append("| T+ | H | n | Δ local +1R resolved | Δ structural +1R resolved |")
    md.append("|----|---|---|----------------------|---------------------------|")
    for w in wait_compare[:12]:
        d1 = w.get("delta_p1R_resolved")
        d2 = w.get("delta_p1onrR_resolved")
        s1 = f"{100 * d1:+.1f}pp" if isinstance(d1, (int, float)) and np.isfinite(d1) else "—"
        s2 = f"{100 * d2:+.1f}pp" if isinstance(d2, (int, float)) and np.isfinite(d2) else "—"
        md.append(f"| +{w['T_offset']}m | {w['horizon']} | {w['quiet_n']} | {s1} | {s2} |")
    md.append("")
    md.append("## Stage verdict")
    md.append("")
    md.append(f"**`{verdict}`**")
    md.append("")
    md.append(verdict_text)
    md.append("")
    if hostile:
        md.append("### Hostile notes")
        md.append("")
        for h in hostile:
            md.append(f"- {h}")
        md.append("")
    md.append("### Explicit non-actions")
    md.append("")
    md.append("- Do not optimize R multiples, clocks, or terciles")
    md.append("- Do not convert soft leftovers into a strategy")
    md.append("- Do not reopen direction-prediction with more filters on these states")
    md.append("- Do not treat local-ATR ~55% path flips as 1–2/day edge")
    md.append("")
    md.append("## Artifacts")
    md.append("")
    md.append("- `artifacts/ny_open_path_asym_panel.parquet`")
    md.append("- `artifacts/ny_open_path_asym_results.csv`")
    md.append("- `artifacts/ny_open_path_asym_report.json`")
    md.append("- `artifacts/ny_open_path_asym_thresholds_IS.json`")
    md.append("- `run_ny_open_path_asymmetry.py`")
    md.append("")

    md_path = art("ny_open_path_asym_report.md")
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {md_path}", flush=True)
    print(f"VERDICT: {verdict}", flush=True)
    print(f"candidates strong/soft/abs: {strong_n}/{soft_n}/{abs_n}", flush=True)
    print(f"onrR survivors: {len(onr_metric_hits)}", flush=True)


if __name__ == "__main__":
    main()
