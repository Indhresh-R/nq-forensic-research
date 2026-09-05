"""
E2 — Scheduled Information Events → NQ Intraday Directional Asymmetry

NO HIGH. Events tested SEPARATELY (no combinations).

Question: Does a scheduled US macro release create a persistent directional
asymmetry in NQ — not merely higher volatility?

Pre-registered (frozen before scoring):
  Events: CPI, NFP, FOMC, PPI, CLAIMS  (ISM unavailable in calendar source)
  Release time: Investing matchedAt when present; else conventional ET clock
  Impulse window IMPULSE_W = 5m after release (fully known before outcomes)
  Outcomes from next bar after impulse end; horizons 5,10,15,30,45,60m

Mechanisms per event (independent):
  1) impulse_cont  — follow first 5m release impulse
  2) impulse_fade  — fade first 5m release impulse
  3) surprise_dir  — frozen surprise→NQ map (information content)
  4) evt_long      — unconditional long at post-impulse (drift)

Surprise maps (frozen):
  CPI/PPI hot surprise (+) → short
  NFP strong surprise (+) → short (hawkish channel)
  CLAIMS high surprise (+) → short
  FOMC higher rate surprise (+) → short

Control: non-event weekdays at the SAME release TOD, same impulse construction.
Promotion requires multi-horizon (>=3) year-stable edge AND lift vs control
for impulse mechanisms.

If all events fail → kill scheduled-events family. No rescue combinations.
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
from typing import Any

import numpy as np
import pandas as pd

from common.nq_session import art, ART, load_nq

warnings.filterwarnings("ignore", category=FutureWarning)

IMPULSE_W = 5
FWD_HORIZONS = (5, 10, 15, 30, 45, 60)
PATH_R = 1.0
IS_Y = set(range(2010, 2022))
VAL_Y = {2022, 2023, 2024}
OOS_Y = {2025, 2026}

# Conventional ET release minutes (fallback when matchedAt missing)
CONV_NY_MIN = {
    "CPI": 8 * 60 + 30,
    "NFP": 8 * 60 + 30,
    "PPI": 8 * 60 + 30,
    "CLAIMS": 8 * 60 + 30,
    "FOMC": 14 * 60 + 0,
}

# trade_dir = SURPRISE_SIGN[event] * sign(surprise)
SURPRISE_SIGN = {
    "CPI": -1,
    "PPI": -1,
    "NFP": -1,
    "CLAIMS": -1,
    "FOMC": -1,
}

EVENTS = ("CPI", "NFP", "FOMC", "PPI", "CLAIMS")


def split_of(y: int) -> str:
    if y in IS_Y:
        return "IS"
    if y in VAL_Y:
        return "Validation"
    if y in OOS_Y:
        return "OOS"
    return "OTHER"


def first_hit(highs: np.ndarray, lows: np.ndarray, entry: float, thr: float) -> float:
    t_up = t_dn = None
    for i in range(len(highs)):
        up = highs[i] >= entry + thr
        dn = lows[i] <= entry - thr
        if up and dn:
            return np.nan
        if up and t_up is None:
            t_up = i
        if dn and t_dn is None:
            t_dn = i
        if t_up is not None and t_dn is not None:
            break
    if t_up is not None and (t_dn is None or t_up < t_dn):
        return 1.0
    if t_dn is not None and (t_up is None or t_dn < t_up):
        return 0.0
    return np.nan


def build_event_calendar() -> pd.DataFrame:
    raw = pd.read_parquet(art("macro_events_raw.parquet"))
    raw = raw[raw["matchedAt"].notna()].copy()
    raw["ts"] = pd.to_datetime(raw["matchedAt"], utc=True).dt.tz_convert("America/New_York")
    raw = raw[raw["ts"] >= "2010-01-01"].copy()
    raw["event_date"] = raw["ts"].dt.date
    raw["ny_min"] = raw["ts"].dt.hour * 60 + raw["ts"].dt.minute
    # one row per event per calendar date (prefer row with surprise)
    raw["has_surp"] = raw["surprise"].notna().astype(int)
    raw = raw.sort_values(["event", "event_date", "has_surp", "ts"]).drop_duplicates(
        ["event", "event_date"], keep="last"
    )
    cal = raw[
        ["event", "event_date", "ts", "ny_min", "surprise", "actual", "forecast", "seriesId"]
    ].copy()
    cal["year"] = cal["ts"].dt.year
    cal["split"] = cal["year"].map(split_of)
    cal["time_source"] = "matchedAt"
    return cal.reset_index(drop=True)


def index_nq_by_minute(
    df: pd.DataFrame,
) -> tuple[dict[Any, dict[int, int]], dict[Any, pd.DataFrame]]:
    """NY calendar date -> ({ny_min: row index}, day frame)."""
    df = df.copy()
    df["ny_date"] = df["ts"].dt.date
    out: dict[Any, dict[int, int]] = {}
    frames: dict[Any, pd.DataFrame] = {}
    for d, g in df.groupby("ny_date", sort=True):
        g = g.reset_index(drop=True)
        frames[d] = g
        out[d] = {int(m): i for i, m in enumerate(g["ny_min"].to_numpy(int))}
    return out, frames


def path_metrics(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    entry_i: int,
    H: int,
    vol: float,
) -> dict[str, float]:
    end_i = entry_i + H - 1
    if end_i >= len(c) or entry_i >= len(c):
        return {k: np.nan for k in ("fwd", "fwd_z", "mfe", "mae", "hit1R")}
    entry = float(o[entry_i])
    hh = h[entry_i : end_i + 1]
    ll = l[entry_i : end_i + 1]
    fwd = float(c[end_i] - entry)
    return {
        "fwd": fwd,
        "fwd_z": fwd / vol if vol > 0 else np.nan,
        "mfe": float(hh.max() - entry),
        "mae": float(entry - ll.min()),
        "hit1R": first_hit(hh, ll, entry, PATH_R * vol),
    }


def build_rows_for_timestamps(
    frames: dict[Any, pd.DataFrame],
    idx_maps: dict[Any, dict[int, int]],
    stamps: pd.DataFrame,
    kind: str,
) -> pd.DataFrame:
    """
    stamps columns: event (or CONTROL), event_date, ny_min, year, split, surprise (opt)
    kind: 'event' or 'control'
    """
    rows: list[dict] = []
    for _, r in stamps.iterrows():
        d = r["event_date"]
        if d not in frames:
            continue
        g = frames[d]
        imap = idx_maps[d]
        rel_min = int(r["ny_min"])
        if rel_min not in imap:
            # try nearest within 2 minutes
            found = None
            for adj in range(0, 3):
                if rel_min + adj in imap:
                    found = rel_min + adj
                    break
                if rel_min - adj in imap:
                    found = rel_min - adj
                    break
            if found is None:
                continue
            rel_min = found
        i_rel = imap[rel_min]
        i_imp_end = i_rel + IMPULSE_W - 1
        if i_imp_end >= len(g) - max(FWD_HORIZONS) - 1:
            continue

        o = g["open"].to_numpy(float)
        h = g["high"].to_numpy(float)
        l = g["low"].to_numpy(float)
        c = g["close"].to_numpy(float)

        # impulse over [i_rel, i_imp_end]
        impulse = float(c[i_imp_end] - o[i_rel])
        if impulse == 0:
            continue
        impulse_dir = 1 if impulse > 0 else -1

        # vol: mean TR of 30m before release (causal)
        prev_c = np.concatenate([[o[0]], c[:-1]])
        tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
        vol = float(np.mean(tr[max(0, i_rel - 29) : i_rel + 1]))
        vol = max(vol, 0.25)

        # outcomes start at next bar after impulse
        entry_i = i_imp_end + 1
        surp = float(r["surprise"]) if "surprise" in r and pd.notna(r.get("surprise")) else np.nan
        evt = str(r["event"])

        surp_dir = 0
        if np.isfinite(surp) and surp != 0 and evt in SURPRISE_SIGN:
            surp_dir = int(SURPRISE_SIGN[evt] * (1 if surp > 0 else -1))

        row: dict[str, Any] = {
            "kind": kind,
            "event": evt,
            "event_date": str(d),
            "year": int(r["year"]),
            "split": str(r["split"]),
            "ny_min": rel_min,
            "impulse": impulse,
            "impulse_dir": impulse_dir,
            "impulse_z": impulse / vol,
            "surprise": surp,
            "surprise_dir": surp_dir,
            "vol": vol,
            "x_cont": impulse_dir,
            "x_fade": -impulse_dir,
            "x_surprise": surp_dir,
            "x_long": 1,
        }
        for H in FWD_HORIZONS:
            pm = path_metrics(o, h, l, c, entry_i, H, vol)
            row[f"fwd_{H}"] = pm["fwd"]
            row[f"fwd_z_{H}"] = pm["fwd_z"]
            row[f"mfe_{H}"] = pm["mfe"]
            row[f"mae_{H}"] = pm["mae"]
            row[f"hit1R_long_{H}"] = pm["hit1R"]
        rows.append(row)
    return pd.DataFrame(rows)


def score_signed(df: pd.DataFrame, col: str, H: int) -> dict[str, float]:
    s = df[df[col] != 0]
    if len(s) == 0:
        return {"n": 0}
    dirc = s[col].to_numpy(float)
    signed = (s[f"fwd_{H}"] * s[col]).to_numpy(float)
    signed_z = (s[f"fwd_z_{H}"] * s[col]).to_numpy(float)
    mfe = s[f"mfe_{H}"].to_numpy(float)
    mae = s[f"mae_{H}"].to_numpy(float)
    mfe_d = np.where(dirc > 0, mfe, mae)
    mae_d = np.where(dirc > 0, mae, mfe)
    hit_long = s[f"hit1R_long_{H}"].to_numpy(float)
    hit_d = np.where(dirc > 0, hit_long, 1.0 - hit_long)
    hit_d = np.where(np.isfinite(hit_long), hit_d, np.nan)
    signed = signed[np.isfinite(signed)]
    if len(signed) == 0:
        return {"n": 0}
    out = {
        "n": int(len(signed)),
        "win": float(np.mean(signed > 0)),
        "mean": float(np.mean(signed)),
        "median": float(np.median(signed)),
        "mean_z": float(np.nanmean(signed_z)),
        "mfe_gt_mae": float(np.mean(mfe_d[np.isfinite(mfe_d)] > mae_d[np.isfinite(mae_d)]))
        if np.isfinite(mfe_d).any()
        else np.nan,
        "p_hit_plus_first": float(np.nanmean(hit_d)),
    }
    return out


def main() -> None:
    print("=== E2: Scheduled Events -> NQ Intraday Direction (NO HIGH) ===", flush=True)
    print(
        f"FROZEN: IMPULSE_W={IMPULSE_W}m; events={EVENTS}; ISM unavailable; "
        f"surprise maps={SURPRISE_SIGN}",
        flush=True,
    )

    cal = build_event_calendar()
    cal.to_parquet(art("nq_e2_event_calendar.parquet"), index=False)
    print("Calendar counts:", cal.groupby("event").size().to_dict(), flush=True)

    print("Loading NQ...", flush=True)
    df = load_nq()
    idx_maps, frames = index_nq_by_minute(df)
    print(f"NQ NY days indexed: {len(frames)}", flush=True)

    # Event rows
    event_panel = build_rows_for_timestamps(frames, idx_maps, cal, kind="event")
    print(f"Event panel rows={len(event_panel)}", flush=True)

    # Control: non-event weekdays at each event-type's typical TOD
    event_dates_by_tod: dict[int, set] = {}
    for evt in EVENTS:
        sub = cal[cal["event"] == evt]
        if len(sub) == 0:
            continue
        tod = int(sub["ny_min"].mode().iloc[0])
        event_dates_by_tod.setdefault(tod, set()).update(sub["event_date"].tolist())

    ctrl_stamps = []
    # Build control universe once per unique TOD used by events
    all_dates = sorted(frames.keys())
    for tod, edates in event_dates_by_tod.items():
        for d in all_dates:
            if d in edates:
                continue
            # weekday only
            if pd.Timestamp(d).dayofweek >= 5:
                continue
            if d not in idx_maps or tod not in idx_maps[d]:
                continue
            y = pd.Timestamp(d).year
            ctrl_stamps.append(
                {
                    "event": f"CTRL_{tod}",
                    "event_date": d,
                    "ny_min": tod,
                    "year": y,
                    "split": split_of(y),
                    "surprise": np.nan,
                }
            )
    ctrl_df = pd.DataFrame(ctrl_stamps)
    # downsample controls for speed: keep ~8x event count per TOD stratified by year — but freeze rule:
    # use ALL controls (no cherry-pick). Claims TOD shared with CPI - OK.
    print(f"Control stamps={len(ctrl_df)}", flush=True)
    control_panel = build_rows_for_timestamps(frames, idx_maps, ctrl_df, kind="control")
    print(f"Control panel rows={len(control_panel)}", flush=True)

    panel = pd.concat([event_panel, control_panel], ignore_index=True)
    panel.to_parquet(art("nq_e2_events_panel.parquet"), index=False)

    mechanisms = [
        ("impulse_cont", "x_cont"),
        ("impulse_fade", "x_fade"),
        ("surprise_dir", "x_surprise"),
        ("evt_long", "x_long"),
    ]

    results: list[dict[str, Any]] = []

    for evt in EVENTS:
        e_sub = panel[(panel["kind"] == "event") & (panel["event"] == evt)]
        if len(e_sub) < 20:
            print(f"  skip {evt}: n={len(e_sub)}", flush=True)
            continue
        tod = int(e_sub["ny_min"].mode().iloc[0])
        c_sub = panel[(panel["kind"] == "control") & (panel["ny_min"] == tod)]
        for split in ("IS", "Validation", "OOS"):
            eb = e_sub[e_sub["split"] == split]
            cb = c_sub[c_sub["split"] == split]
            if len(eb) < 15:
                continue
            for H in FWD_HORIZONS:
                # control baselines for cont/fade/long at this TOD
                ctrl_stats = {}
                for mech, col in mechanisms:
                    if mech == "surprise_dir":
                        continue
                    st = score_signed(cb, col, H)
                    ctrl_stats[mech] = st

                for mech, col in mechanisms:
                    st = score_signed(eb, col, H)
                    if st.get("n", 0) < 15:
                        continue
                    cst = ctrl_stats.get(mech, {"n": 0})
                    unc_win = float(np.nanmean(eb[f"fwd_{H}"] > 0))
                    row = {
                        "event": evt,
                        "mechanism": mech,
                        "horizon": H,
                        "split": split,
                        "ny_min": tod,
                        "n": st["n"],
                        "win": st["win"],
                        "mean": st["mean"],
                        "median": st["median"],
                        "mean_z": st["mean_z"],
                        "mfe_gt_mae": st.get("mfe_gt_mae", np.nan),
                        "p_hit_plus_first": st.get("p_hit_plus_first", np.nan),
                        "delta_win_vs_50": st["win"] - 0.5,
                        "unc_long_win": unc_win,
                        "delta_win_vs_unc_long": st["win"] - unc_win,
                        "ctrl_n": cst.get("n", 0),
                        "ctrl_win": cst.get("win", np.nan),
                        "delta_win_vs_ctrl": st["win"] - cst["win"]
                        if cst.get("n", 0) >= 30 and np.isfinite(cst.get("win", np.nan))
                        else np.nan,
                    }
                    results.append(row)

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_e2_events_results.csv"), index=False)
    print(f"Result rows={len(res_df)}", flush=True)

    def year_stats(evt: str, col: str, H: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for y in (2025, 2026):
            s = panel[(panel["kind"] == "event") & (panel["event"] == evt) & (panel["year"] == y)]
            st = score_signed(s, col, H)
            out[f"y{y}_n"] = st.get("n", 0)
            out[f"y{y}_win"] = st.get("win", np.nan)
            out[f"y{y}_mean"] = st.get("mean", np.nan)
        return out

    candidates: list[dict[str, Any]] = []
    is_rows = res_df[res_df["split"] == "IS"]
    for _, r in is_rows.iterrows():
        evt, mech, H = str(r["event"]), str(r["mechanism"]), int(r["horizon"])
        col = next(c for m, c in mechanisms if m == mech)
        if int(r["n"]) < 40:
            continue
        # FOMC exception: allow n>=25 on IS due to sparse meetings, still need Val/OOS
        if evt == "FOMC" and int(r["n"]) < 25:
            continue
        val = res_df[
            (res_df["event"] == evt)
            & (res_df["mechanism"] == mech)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "Validation")
        ]
        oos = res_df[
            (res_df["event"] == evt)
            & (res_df["mechanism"] == mech)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "OOS")
        ]
        if len(val) == 0 or len(oos) == 0:
            continue
        v, o = val.iloc[0], oos.iloc[0]
        min_val, min_oos = (20, 15) if evt == "FOMC" else (30, 25)
        if int(v["n"]) < min_val or int(o["n"]) < min_oos:
            continue

        yrs = year_stats(evt, col, H)
        is_win, v_win, o_win = float(r["win"]), float(v["win"]), float(o["win"])
        is_d = float(r["delta_win_vs_50"])
        v_d = float(v["delta_win_vs_50"])
        o_d = float(o["delta_win_vs_50"])
        is_mean, v_mean, o_mean = float(r["mean"]), float(v["mean"]), float(o["mean"])
        is_mz = float(r["mean_z"]) if np.isfinite(r["mean_z"]) else np.nan
        y25, y26 = yrs.get("y2025_win"), yrs.get("y2026_win")
        y25n, y26n = yrs.get("y2025_n", 0), yrs.get("y2026_n", 0)

        # Year gate: require 2025; 2026 if n>=8 else skip 2026 requirement but flag
        year_ok = (
            isinstance(y25, (int, float))
            and np.isfinite(y25)
            and y25n >= 8
            and y25 >= 0.50
        )
        if y26n >= 8:
            year_ok = (
                year_ok
                and isinstance(y26, (int, float))
                and np.isfinite(y26)
                and y26 >= 0.50
                and abs(y25 - y26) <= 0.15
            )

        # vs control for impulse mechanisms
        need_ctrl = mech in ("impulse_cont", "impulse_fade", "evt_long")
        ctrl_ok = True
        if need_ctrl:
            is_dc = float(r["delta_win_vs_ctrl"]) if np.isfinite(r.get("delta_win_vs_ctrl", np.nan)) else np.nan
            v_dc = float(v["delta_win_vs_ctrl"]) if np.isfinite(v.get("delta_win_vs_ctrl", np.nan)) else np.nan
            o_dc = float(o["delta_win_vs_ctrl"]) if np.isfinite(o.get("delta_win_vs_ctrl", np.nan)) else np.nan
            ctrl_ok = (
                np.isfinite(is_dc)
                and np.isfinite(v_dc)
                and np.isfinite(o_dc)
                and is_dc >= 0.02
                and v_dc > 0
                and o_dc > 0
            )

        lift_ok = is_d >= 0.03 and v_d > 0 and o_d > 0
        abs_ok = is_win >= 0.53 and v_win >= 0.52 and o_win >= 0.52
        payoff_ok = is_mean > 0 and v_mean > 0 and o_mean > 0 and (not np.isfinite(is_mz) or is_mz > 0)
        path_ok = (
            np.isfinite(r.get("mfe_gt_mae", np.nan))
            and float(r["mfe_gt_mae"]) >= 0.52
            and np.isfinite(r.get("p_hit_plus_first", np.nan))
            and float(r["p_hit_plus_first"]) >= 0.52
        )
        strong = lift_ok and abs_ok and year_ok and payoff_ok and path_ok and ctrl_ok and is_d >= 0.04
        soft = (
            ((lift_ok and is_d >= 0.025) or (abs_ok and is_win >= 0.54))
            and year_ok
            and v_win >= 0.50
            and o_win >= 0.50
            and (payoff_ok or path_ok)
            and (ctrl_ok if need_ctrl else True)
        )
        if strong or soft:
            candidates.append(
                {
                    "event": evt,
                    "mechanism": mech,
                    "horizon": H,
                    "tier": "strong" if strong else "soft",
                    "IS_n": int(r["n"]),
                    "IS_win": is_win,
                    "IS_d50": is_d,
                    "IS_mean_z": is_mz,
                    "IS_d_ctrl": float(r["delta_win_vs_ctrl"])
                    if np.isfinite(r.get("delta_win_vs_ctrl", np.nan))
                    else None,
                    "Val_win": v_win,
                    "OOS_win": o_win,
                    "y2025_win": y25,
                    "y2026_win": y26,
                    "y2025_n": y25n,
                    "y2026_n": y26n,
                }
            )

    candidates.sort(key=lambda x: (0 if x["tier"] == "strong" else 1, -x["IS_d50"]))

    # Multi-horizon stability (events are single-clock by nature)
    stability = []
    if candidates:
        cdf = pd.DataFrame(candidates)
        for (evt, mech), g in cdf.groupby(["event", "mechanism"]):
            hs = sorted(g["horizon"].unique().tolist())
            strong_hs = sorted(g.loc[g["tier"] == "strong", "horizon"].unique().tolist())
            stability.append(
                {
                    "event": evt,
                    "mechanism": mech,
                    "n_horizons": len(hs),
                    "n_horizons_strong": len(strong_hs),
                    "horizons": hs,
                    "median_IS_win": float(g["IS_win"].median()),
                }
            )

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    multi_strong = [s for s in stability if s["n_horizons_strong"] >= 3]
    events_with_multi = sorted({s["event"] for s in multi_strong})

    # Per-event IS median summary
    event_summary = []
    for evt in EVENTS:
        for mech, _ in mechanisms:
            g = is_rows[(is_rows["event"] == evt) & (is_rows["mechanism"] == mech)]
            if len(g) == 0:
                continue
            event_summary.append(
                {
                    "event": evt,
                    "mechanism": mech,
                    "IS_med_n": float(g["n"].median()),
                    "IS_med_win": float(g["win"].median()),
                    "IS_med_d50": float(g["delta_win_vs_50"].median()),
                    "IS_med_d_ctrl": float(g["delta_win_vs_ctrl"].median())
                    if g["delta_win_vs_ctrl"].notna().any()
                    else np.nan,
                    "IS_med_mean_z": float(g["mean_z"].median()),
                    "IS_med_mfe_gt_mae": float(g["mfe_gt_mae"].median()),
                    "IS_med_p_hit": float(g["p_hit_plus_first"].median()),
                }
            )
    event_summary.sort(key=lambda x: -abs(x["IS_med_d50"]))

    if multi_strong:
        verdict = "A"
        verdict_text = (
            f"Scheduled event(s) produce multi-horizon year-stable directional asymmetry: "
            f"{events_with_multi}."
        )
        kill = False
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Weak/inconsistent event-direction leftovers; no multi-horizon strong effect. "
            "Kill scheduled-events family (do not combine events)."
        )
        kill = True
    else:
        verdict = "C"
        verdict_text = (
            "No persistent directional asymmetry from CPI/NFP/FOMC/PPI/CLAIMS "
            "(impulse cont/fade, surprise, and event-long all fail vs 50% and/or same-TOD control)."
        )
        kill = True

    report = {
        "stage": "E2_scheduled_information_events",
        "family": "scheduled_information_events",
        "verdict": verdict,
        "kill_family": kill,
        "verdict_text": verdict_text,
        "ism_status": "unavailable_in_calendar_source",
        "frozen": {
            "impulse_w": IMPULSE_W,
            "surprise_sign": SURPRISE_SIGN,
            "events": list(EVENTS),
            "no_HIGH": True,
            "no_event_combinations": True,
        },
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_horizon_strong": len(multi_strong),
        "events_with_multi_horizon_strong": events_with_multi,
        "event_IS_summary": event_summary,
        "top_candidates": candidates[:25],
        "stability": stability,
        "next_if_killed": (
            "Reconsider whether a short-horizon directional engine is realistic; "
            "do not invent another OHLC/options transform. HIGH remains timing-only."
        ),
        "pivot_doc": "artifacts/research_pivot_external_direction.md",
    }
    with open(art("nq_e2_events_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# E2 — Scheduled Information Events → NQ Intraday Direction (NO HIGH)")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(
        f"Kill scheduled-events family: **{kill}**. Events tested **separately**. "
        "ISM unavailable in source calendar. No HIGH. Not a vol/opportunity test."
    )
    md.append("")
    md.append(
        f"Frozen: impulse={IMPULSE_W}m after release; mechanisms=cont/fade/surprise/long; "
        f"surprise maps={SURPRISE_SIGN}."
    )
    md.append("")
    md.append(f"Strong cells: {strong_n} · Soft: {soft_n} · Multi-horizon strong: {len(multi_strong)}")
    md.append("")
    md.append("## Per-event IS summary (median across horizons)")
    md.append("")
    md.append("| Event | Mechanism | med n | win | Δ50 | Δctrl | mean z | MFE>MAE | P(+1R≺) |")
    md.append("|-------|-----------|-------|-----|-----|-------|--------|---------|---------|")
    for m in event_summary:
        md.append(
            f"| `{m['event']}` | `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | "
            f"{pp(m['IS_med_d50'])} | {pp(m['IS_med_d_ctrl'])} | {m['IS_med_mean_z']:+.3f} | "
            f"{pct(m['IS_med_mfe_gt_mae'])} | {pct(m['IS_med_p_hit'])} |"
        )
    md.append("")
    md.append("## Surviving cells")
    md.append("")
    if not candidates:
        md.append("None.")
    else:
        md.append("| Tier | Event | X | H | n | IS | Δ50 | Δctrl | Val | OOS | 2025 | 2026 |")
        md.append("|------|-------|---|---|---|----|-----|-------|-----|-----|------|------|")
        for c in candidates[:20]:
            md.append(
                f"| {c['tier']} | `{c['event']}` | `{c['mechanism']}` | {c['horizon']} | "
                f"{c['IS_n']} | {pct(c['IS_win'])} | {pp(c['IS_d50'])} | {pp(c.get('IS_d_ctrl'))} | "
                f"{pct(c['Val_win'])} | {pct(c['OOS_win'])} | "
                f"{pct(c.get('y2025_win'))} | {pct(c.get('y2026_win'))} |"
            )
        if not multi_strong:
            md.append("")
            md.append("No multi-horizon strong event mechanism — not promotable.")
    md.append("")
    md.append("## Stability (horizons stand in for clocks)")
    md.append("")
    if not stability:
        md.append("n/a")
    else:
        for s in stability:
            md.append(
                f"- `{s['event']}` `{s['mechanism']}`: {s['n_horizons']} horizons "
                f"({s['n_horizons_strong']} strong) {s['horizons']}"
            )
    md.append("")
    md.append(f"## Final: **{verdict}**")
    md.append("")
    if kill:
        md.append("**Kill scheduled-information-events family.** Do not combine dead events.")
        md.append("")
        md.append(
            "This was the last major fundamentally different information family queued. "
            "Reconsider whether a short-horizon **directional engine** is realistic given: "
            "OHLC ❌, EOD options ❌, scheduled events ❌, while frozen HIGH opportunity timing ✅."
        )
        md.append("HIGH remains untouched (timing only).")
    else:
        md.append(
            f"Investigate mechanism for surviving event(s) only: {events_with_multi}. "
            "Then — and only then — test frozen HIGH as timing enhancer."
        )
    md.append("")
    (art("nq_e2_events_report.md")).write_text("\n".join(md), encoding="utf-8")

    pivot = art("research_pivot_external_direction.md")
    if pivot.exists():
        note = (
            f"\n\n## E2 result (2026-09-05)\n\n"
            f"Scheduled information events → intraday direction: **{verdict}** (kill={kill}).\n"
            f"ISM unavailable in calendar source.\n"
        )
        text = pivot.read_text(encoding="utf-8")
        if "## E2 result" not in text:
            pivot.write_text(text.rstrip() + note, encoding="utf-8")

    print(f"VERDICT: {verdict} kill={kill}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n} multi_horizon_strong: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
