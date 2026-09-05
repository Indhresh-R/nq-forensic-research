"""
NQ Intrinsic Directional Discovery — Family 3: Failed Movement / Exhaustion

NO HIGH. Liquid RTH 09:30-15:30.
Question: After a directional attempt fails to achieve a pre-specified
vol-normalized extension within a fixed observation window, does the
forward return distribution become asymmetric (fade of the attempt)?

CRITICAL: Failure is fully observable at signal timestamp T.
Do NOT define failure from the eventual post-T reversal.

Timeline (causal):
  [attempt L bars] → T_a (attempt end)
  [OBS_W bars]     → T   (signal: extension missed / rejected / weak)
  outcomes from T+1 open onward

Hostile: next-bar outcomes, IS-frozen attempt thresholds, no HIGH,
no levels/VWAP/ES/volume, no sweep, no strategy construction.
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

from common.nq_session import art, ART, NY_OPEN, load_nq

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_END = 15 * 60 + 30
DECISION_OFFSETS = tuple(range(0, SESSION_END - NY_OPEN + 1, 5))
EVAL_OFFSETS = tuple(range(0, SESSION_END - NY_OPEN + 1, 15))
ATTEMPT_LS = (10, 15, 30)
OBS_W = 15  # fixed observation window after attempt end (pre-specified)
EXT_MULT = 0.75  # expected extension in vol units (pre-specified, not swept)
REJECT_ADV_MULT = 0.50  # adverse fraction of EXT for rejection-first
WEAK_RATIO = 0.50  # MFE/EXT < this ⇒ weak excursion
ATTEMPT_Q = 0.66  # IS |attempt_z| quantile (pre-specified)
FWD_HORIZONS = (5, 10, 15, 30, 45, 60)
PATH_R = 1.0
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


def first_hit(highs: np.ndarray, lows: np.ndarray, entry: float, thr: float) -> float:
    """1 if +thr before -thr, 0 if -thr before +thr, nan if neither/ambiguous."""
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


def obs_path_stats(
    h: np.ndarray,
    l: np.ndarray,
    i0: int,
    i1: int,
    ref: float,
    direction: int,
    ext: float,
    adv: float,
) -> dict[str, float]:
    """
    Path stats on bars (i0, i1] relative to ref, in attempt direction.
    All observables by T = bar i1.
    """
    if i1 <= i0 or direction == 0 or ext <= 0:
        return {
            "hit_ext": np.nan,
            "t_ext": np.nan,
            "t_adv": np.nan,
            "mfe": np.nan,
            "mae": np.nan,
            "exc_ratio": np.nan,
            "reject_first": np.nan,
        }

    mfe = 0.0
    mae = 0.0
    t_ext = None
    t_adv = None
    for i in range(i0 + 1, i1 + 1):
        if direction > 0:
            fav = float(h[i] - ref)
            adv_x = float(ref - l[i])
            hit_e = h[i] >= ref + ext
            hit_a = l[i] <= ref - adv
        else:
            fav = float(ref - l[i])
            adv_x = float(h[i] - ref)
            hit_e = l[i] <= ref - ext
            hit_a = h[i] >= ref + adv

        if fav > mfe:
            mfe = fav
        if adv_x > mae:
            mae = adv_x
        if hit_e and t_ext is None:
            t_ext = i - i0
        if hit_a and t_adv is None:
            t_adv = i - i0

    hit_ext = 1.0 if t_ext is not None else 0.0
    reject_first = np.nan
    if t_adv is not None and (t_ext is None or t_adv < t_ext):
        reject_first = 1.0
    elif t_ext is not None and (t_adv is None or t_ext < t_adv):
        reject_first = 0.0
    # if neither level hit: not a rejection-first event
    elif t_ext is None and t_adv is None:
        reject_first = 0.0

    return {
        "hit_ext": hit_ext,
        "t_ext": float(t_ext) if t_ext is not None else np.nan,
        "t_adv": float(t_adv) if t_adv is not None else np.nan,
        "mfe": mfe,
        "mae": mae,
        "exc_ratio": mfe / ext if ext > 0 else np.nan,
        "reject_first": reject_first,
    }


def main() -> None:
    print("=== Failed Movement / Exhaustion (NO HIGH) ===", flush=True)
    panel_path = art("nq_failed_move_panel.parquet")
    rebuild = True
    if panel_path.exists():
        probe = pd.read_parquet(panel_path)
        need = {"x_fade_fail_15", "x_fade_reject_15", "x_fade_weak_15", "fwd_15", "attempt_z_15"}
        if need.issubset(probe.columns) and len(probe) > 50000:
            panel = probe
            rebuild = False
            print(f"Reusing panel rows={len(panel)}", flush=True)

    if rebuild:
        df = load_nq()
        print("Indexing RTH...", flush=True)
        rows: list[dict] = []
        n_days = 0
        atr_hist: list[float] = []

        for sd, g in df.groupby("session_date", sort=True):
            rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 16 * 60)].reset_index(drop=True)
            if len(rth) < 220:
                continue
            n_days += 1
            year = int(rth.iloc[0]["year"])
            dow = int(rth.iloc[0]["dow"])
            split = split_of(year)

            o = rth["open"].to_numpy(float)
            h = rth["high"].to_numpy(float)
            l = rth["low"].to_numpy(float)
            c = rth["close"].to_numpy(float)
            ny = rth["ny_min"].to_numpy(int)
            idx = {int(n): i for i, n in enumerate(ny)}

            prev_c = np.concatenate([[o[0]], c[:-1]])
            tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
            prior_atr = float(np.median(atr_hist[-20:])) if len(atr_hist) >= 5 else float(np.mean(tr[:30]))

            day_trs: list[float] = []
            for off in DECISION_OFFSETS:
                T = NY_OPEN + off
                if T not in idx:
                    continue
                j = idx[T]
                after = np.where(ny > T)[0]
                if len(after) < max(FWD_HORIZONS):
                    continue

                # T must allow attempt + OBS fully before T
                T_a = T - OBS_W
                if T_a not in idx or T_a < NY_OPEN:
                    continue
                i_ta = idx[T_a]
                i_t = j

                atr_ta = float(np.mean(tr[max(0, i_ta - 29) : i_ta + 1]))
                vol_ta = max(atr_ta, 0.25 * prior_atr, 0.25)
                atr_t = float(np.mean(tr[max(0, j - 29) : j + 1]))
                vol_t = max(atr_t, 0.25 * prior_atr, 0.25)

                entry_i = int(after[0])
                entry = float(o[entry_i])

                row: dict[str, Any] = {
                    "session_date": str(sd),
                    "year": year,
                    "dow": dow,
                    "split": split,
                    "T_offset": off,
                    "T_ny": T,
                    "vol_ta": vol_ta,
                    "vol": vol_t,
                }

                ext = EXT_MULT * vol_ta
                adv = REJECT_ADV_MULT * ext
                ref = float(c[i_ta])

                for L in ATTEMPT_LS:
                    a0_ny = T_a - L + 1
                    if a0_ny not in idx or a0_ny < NY_OPEN:
                        row[f"attempt_z_{L}"] = np.nan
                        row[f"attempt_dir_{L}"] = 0
                        row[f"hit_ext_{L}"] = np.nan
                        row[f"t_ext_{L}"] = np.nan
                        row[f"t_adv_{L}"] = np.nan
                        row[f"exc_ratio_{L}"] = np.nan
                        row[f"reject_first_{L}"] = np.nan
                        row[f"mfe_obs_{L}"] = np.nan
                        row[f"mae_obs_{L}"] = np.nan
                        continue

                    i_a0 = idx[a0_ny]
                    attempt_ret = float(c[i_ta] - o[i_a0])
                    attempt_z = attempt_ret / vol_ta
                    direction = 1 if attempt_ret > 0 else (-1 if attempt_ret < 0 else 0)
                    row[f"attempt_z_{L}"] = attempt_z
                    row[f"attempt_dir_{L}"] = direction

                    st = obs_path_stats(h, l, i_ta, i_t, ref, direction, ext, adv)
                    row[f"hit_ext_{L}"] = st["hit_ext"]
                    row[f"t_ext_{L}"] = st["t_ext"]
                    row[f"t_adv_{L}"] = st["t_adv"]
                    row[f"exc_ratio_{L}"] = st["exc_ratio"]
                    row[f"reject_first_{L}"] = st["reject_first"]
                    row[f"mfe_obs_{L}"] = st["mfe"]
                    row[f"mae_obs_{L}"] = st["mae"]

                for H in FWD_HORIZONS:
                    end_i = entry_i + H - 1
                    if end_i >= len(c):
                        for key in (
                            f"fwd_{H}",
                            f"fwd_z_{H}",
                            f"mfe_{H}",
                            f"mae_{H}",
                            f"hit1R_long_{H}",
                        ):
                            row[key] = np.nan
                        continue
                    hh = h[entry_i : end_i + 1]
                    ll = l[entry_i : end_i + 1]
                    fwd = float(c[end_i] - entry)
                    row[f"fwd_{H}"] = fwd
                    row[f"fwd_z_{H}"] = fwd / vol_t
                    row[f"mfe_{H}"] = float(hh.max() - entry)
                    row[f"mae_{H}"] = float(entry - ll.min())
                    row[f"hit1R_long_{H}"] = first_hit(hh, ll, entry, PATH_R * vol_t)

                rows.append(row)
                day_trs.append(float(tr[j]))

            if day_trs:
                atr_hist.append(float(np.mean(day_trs)))
            if n_days % 500 == 0:
                print(f"  days={n_days} rows={len(rows)}", flush=True)

        panel = pd.DataFrame(rows)

        # IS attempt thresholds: |attempt_z| >= p66 at each (L, T_offset)
        thresholds: dict[str, dict[int, float]] = {}
        is_p = panel[panel["split"] == "IS"]
        for L in ATTEMPT_LS:
            key = f"attempt_z_{L}"
            thresholds[key] = {}
            for off in DECISION_OFFSETS:
                s = is_p.loc[is_p["T_offset"] == off, key].abs().dropna()
                if len(s) < 100:
                    continue
                thresholds[key][off] = float(s.quantile(ATTEMPT_Q))

        meta = {
            "attempt_abs_z_quantile": ATTEMPT_Q,
            "obs_window_min": OBS_W,
            "ext_mult_vol": EXT_MULT,
            "reject_adv_mult_of_ext": REJECT_ADV_MULT,
            "weak_exc_ratio": WEAK_RATIO,
            "path_R_vol_units": PATH_R,
            "vol_def": "max(mean TR last 30m to T_a/T, 0.25*prior_day_ATR, 0.25)",
            "failure_rule": (
                "At T=T_a+OBS_W: attempt |z|>=IS_p66 at T_a; "
                "failure = expected extension EXT_MULT*vol_ta NOT hit in (T_a,T]; "
                "reject = adverse REJECT_ADV*EXT hit before extension; "
                "weak = exc_ratio < WEAK_RATIO (and no extension hit). "
                "All known at T; outcomes from T+1."
            ),
            "thresholds": thresholds,
        }
        with open(art("nq_failed_move_thresholds_IS.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        labs = []
        for _, r in panel.iterrows():
            off = int(r["T_offset"])
            lab: dict[str, Any] = {}
            for L in ATTEMPT_LS:
                z = float(r[f"attempt_z_{L}"])
                d = int(r[f"attempt_dir_{L}"])
                th = thresholds.get(f"attempt_z_{L}", {}).get(off)
                is_attempt = th is not None and np.isfinite(z) and abs(z) >= th and d != 0
                hit = float(r[f"hit_ext_{L}"])
                rej = float(r[f"reject_first_{L}"])
                ratio = float(r[f"exc_ratio_{L}"])

                failed = is_attempt and np.isfinite(hit) and hit < 0.5
                rejected = is_attempt and np.isfinite(rej) and rej > 0.5
                weak = (
                    is_attempt
                    and np.isfinite(hit)
                    and hit < 0.5
                    and np.isfinite(ratio)
                    and ratio < WEAK_RATIO
                )

                # Fade of failed bullish attempt → short (-1); failed bearish → long (+1)
                lab[f"x_fade_fail_{L}"] = (-d) if failed else 0
                lab[f"x_fade_reject_{L}"] = (-d) if rejected else 0
                lab[f"x_fade_weak_{L}"] = (-d) if weak else 0
                lab[f"is_attempt_{L}"] = 1 if is_attempt else 0
                lab[f"is_fail_{L}"] = 1 if failed else 0
                # bull/bear split flags for diagnostics
                lab[f"fail_bull_{L}"] = 1 if failed and d > 0 else 0
                lab[f"fail_bear_{L}"] = 1 if failed and d < 0 else 0
            labs.append(lab)

        panel = pd.concat([panel.reset_index(drop=True), pd.DataFrame(labs)], axis=1)
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)} days~{panel['session_date'].nunique()}", flush=True)
    else:
        thresholds = json.loads((art("nq_failed_move_thresholds_IS.json")).read_text(encoding="utf-8"))[
            "thresholds"
        ]

    mechanisms: list[tuple[str, str]] = []
    for L in ATTEMPT_LS:
        mechanisms.append((f"fade_fail_{L}", f"x_fade_fail_{L}"))
        mechanisms.append((f"fade_reject_{L}", f"x_fade_reject_{L}"))
        mechanisms.append((f"fade_weak_{L}", f"x_fade_weak_{L}"))

    results: list[dict[str, Any]] = []

    def dist_stats(signed: np.ndarray, mfe_d: np.ndarray, mae_d: np.ndarray, hit_d: np.ndarray) -> dict[str, float]:
        signed = signed[np.isfinite(signed)]
        if len(signed) == 0:
            return {"n": 0}
        out: dict[str, float] = {
            "n": int(len(signed)),
            "win": float(np.mean(signed > 0)),
            "mean": float(np.mean(signed)),
            "median": float(np.median(signed)),
        }
        mfe_d = mfe_d[np.isfinite(mfe_d)]
        mae_d = mae_d[np.isfinite(mae_d)]
        if len(mfe_d) and len(mae_d) and len(mfe_d) == len(mae_d):
            out["mean_mfe"] = float(np.mean(mfe_d))
            out["mean_mae"] = float(np.mean(mae_d))
            out["mfe_gt_mae"] = float(np.mean(mfe_d > mae_d))
        hit = hit_d[np.isfinite(hit_d)]
        if len(hit):
            out["p_hit_plus_first"] = float(np.mean(hit))
            out["hit_n"] = int(len(hit))
        return out

    for off in EVAL_OFFSETS:
        sub = panel[panel["T_offset"] == off]
        if len(sub) < 200:
            continue
        for split in ("IS", "Validation", "OOS"):
            base = sub[sub["split"] == split]
            if len(base) < 80:
                continue
            for H in FWD_HORIZONS:
                fwd = base[f"fwd_{H}"].to_numpy(float)
                fz = base[f"fwd_z_{H}"].to_numpy(float)
                results.append(
                    {
                        "mechanism": "UNCOND_LONG",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(np.isfinite(fwd).sum()),
                        "rate": 1.0,
                        "win": float(np.nanmean(fwd > 0)),
                        "mean": float(np.nanmean(fwd)),
                        "median": float(np.nanmedian(fwd)),
                        "mean_z": float(np.nanmean(fz)),
                        "mean_mfe": float(np.nanmean(base[f"mfe_{H}"])),
                        "mean_mae": float(np.nanmean(base[f"mae_{H}"])),
                        "mfe_gt_mae": float(np.nanmean(base[f"mfe_{H}"] > base[f"mae_{H}"])),
                        "p_hit_plus_first": float(np.nanmean(base[f"hit1R_long_{H}"])),
                        "delta_win_vs_unc": 0.0,
                        "delta_mean_vs_unc": 0.0,
                    }
                )
                unc_win = float(np.nanmean(fwd > 0))
                unc_mean = float(np.nanmean(fwd))

                for mech, col in mechanisms:
                    s = base[base[col] != 0].copy()
                    if len(s) < 40:
                        continue
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

                    st = dist_stats(signed, mfe_d, mae_d, hit_d)
                    if st.get("n", 0) < 40:
                        continue
                    sz = signed_z[np.isfinite(signed_z)]
                    st["mean_z"] = float(np.mean(sz)) if len(sz) else np.nan

                    # failure-path descriptors (pre-T)
                    L = int(mech.rsplit("_", 1)[-1])
                    exc = s[f"exc_ratio_{L}"].to_numpy(float) if f"exc_ratio_{L}" in s.columns else np.array([])
                    hit_pre = s[f"hit_ext_{L}"].to_numpy(float) if f"hit_ext_{L}" in s.columns else np.array([])
                    t_adv = s[f"t_adv_{L}"].to_numpy(float) if f"t_adv_{L}" in s.columns else np.array([])
                    exc_f = exc[np.isfinite(exc)]
                    t_adv_f = t_adv[np.isfinite(t_adv)]
                    hit_pre_f = hit_pre[np.isfinite(hit_pre)]

                    results.append(
                        {
                            "mechanism": mech,
                            "T_offset": off,
                            "horizon": H,
                            "split": split,
                            "n": st["n"],
                            "n_base": int(len(base)),
                            "rate": float(len(s) / len(base)),
                            "win": st["win"],
                            "mean": st["mean"],
                            "median": st["median"],
                            "mean_z": st["mean_z"],
                            "mean_mfe": st.get("mean_mfe", np.nan),
                            "mean_mae": st.get("mean_mae", np.nan),
                            "mfe_gt_mae": st.get("mfe_gt_mae", np.nan),
                            "p_hit_plus_first": st.get("p_hit_plus_first", np.nan),
                            "hit_n": st.get("hit_n", 0),
                            "med_exc_ratio": float(np.median(exc_f)) if len(exc_f) else np.nan,
                            "med_t_adv": float(np.median(t_adv_f)) if len(t_adv_f) else np.nan,
                            "frac_hit_ext_pre": float(np.mean(hit_pre_f > 0.5)) if len(hit_pre_f) else np.nan,
                            "unc_win": unc_win,
                            "unc_mean": unc_mean,
                            "delta_win_vs_unc": st["win"] - unc_win,
                            "delta_mean_vs_unc": st["mean"] - unc_mean,
                            "delta_win_vs_50": st["win"] - 0.5,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_failed_move_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

    # Attempt-level diagnostics: time-to-ext among hits vs failure rate (IS)
    attempt_diag = []
    is_all = panel[panel["split"] == "IS"]
    for L in ATTEMPT_LS:
        for off in EVAL_OFFSETS:
            s = is_all[(is_all["T_offset"] == off) & (is_all[f"is_attempt_{L}"] == 1)]
            if len(s) < 80:
                continue
            hit = s[f"hit_ext_{L}"].to_numpy(float)
            t_ext = s[f"t_ext_{L}"].to_numpy(float)
            ratio = s[f"exc_ratio_{L}"].to_numpy(float)
            hit_mask = np.isfinite(hit) & (hit > 0.5)
            fail_mask = np.isfinite(hit) & (hit < 0.5)
            t_hit = t_ext[hit_mask & np.isfinite(t_ext)]
            attempt_diag.append(
                {
                    "L": L,
                    "T_offset": off,
                    "n_attempt": int(len(s)),
                    "p_fail": float(fail_mask.mean()) if len(s) else np.nan,
                    "p_reject_first": float(np.nanmean(s[f"reject_first_{L}"])) if len(s) else np.nan,
                    "med_t_ext_if_hit": float(np.median(t_hit)) if len(t_hit) else np.nan,
                    "med_exc_ratio_fail": float(np.nanmedian(ratio[fail_mask])) if fail_mask.any() else np.nan,
                    "med_exc_ratio_hit": float(np.nanmedian(ratio[hit_mask])) if hit_mask.any() else np.nan,
                }
            )

    def year_stats(col: str, off: int, H: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for y in (2025, 2026):
            s = panel[(panel["T_offset"] == off) & (panel["year"] == y) & (panel[col] != 0)]
            signed = (s[f"fwd_{H}"] * s[col]).to_numpy(float)
            signed = signed[np.isfinite(signed)]
            out[f"y{y}_n"] = int(len(signed))
            out[f"y{y}_win"] = float(np.mean(signed > 0)) if len(signed) else np.nan
            out[f"y{y}_mean"] = float(np.mean(signed)) if len(signed) else np.nan
        return out

    candidates: list[dict[str, Any]] = []
    is_rows = res_df[(res_df["split"] == "IS") & (res_df["mechanism"] != "UNCOND_LONG")]
    for _, r in is_rows.iterrows():
        mech = str(r["mechanism"])
        off, H = int(r["T_offset"]), int(r["horizon"])
        if int(r["n"]) < 100:
            continue
        val = res_df[
            (res_df["mechanism"] == mech)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "Validation")
        ]
        oos = res_df[
            (res_df["mechanism"] == mech)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["split"] == "OOS")
        ]
        if len(val) == 0 or len(oos) == 0:
            continue
        v, o = val.iloc[0], oos.iloc[0]
        if int(v["n"]) < 50 or int(o["n"]) < 40:
            continue

        col = next(c for m, c in mechanisms if m == mech)
        yrs = year_stats(col, off, H)
        is_win, v_win, o_win = float(r["win"]), float(v["win"]), float(o["win"])
        is_d = float(r["delta_win_vs_50"])
        v_d = float(v["delta_win_vs_50"])
        o_d = float(o["delta_win_vs_50"])
        is_du = float(r["delta_win_vs_unc"])
        v_du = float(v["delta_win_vs_unc"])
        o_du = float(o["delta_win_vs_unc"])
        is_mean, v_mean, o_mean = float(r["mean"]), float(v["mean"]), float(o["mean"])
        is_mz = float(r["mean_z"]) if np.isfinite(r["mean_z"]) else np.nan
        y25, y26 = yrs.get("y2025_win"), yrs.get("y2026_win")
        y25n, y26n = yrs.get("y2025_n", 0), yrs.get("y2026_n", 0)

        year_ok = (
            isinstance(y25, (int, float))
            and isinstance(y26, (int, float))
            and np.isfinite(y25)
            and np.isfinite(y26)
            and y25n >= 25
            and y26n >= 25
            and y25 >= 0.50
            and y26 >= 0.50
            and abs(y25 - y26) <= 0.12
        )
        lift_ok = is_d >= 0.03 and v_d > 0 and o_d > 0 and is_du > 0 and v_du > 0 and o_du > 0
        abs_ok = is_win >= 0.53 and v_win >= 0.52 and o_win >= 0.52
        payoff_ok = is_mean > 0 and v_mean > 0 and o_mean > 0 and (not np.isfinite(is_mz) or is_mz > 0)
        path_ok = (
            np.isfinite(r.get("mfe_gt_mae", np.nan))
            and float(r["mfe_gt_mae"]) >= 0.52
            and np.isfinite(r.get("p_hit_plus_first", np.nan))
            and float(r["p_hit_plus_first"]) >= 0.52
        )
        strong = lift_ok and abs_ok and year_ok and payoff_ok and is_d >= 0.04 and path_ok
        soft = (
            ((lift_ok and is_d >= 0.025) or (abs_ok and is_win >= 0.54))
            and year_ok
            and v_win >= 0.50
            and o_win >= 0.50
            and (payoff_ok or path_ok)
        )
        if strong or soft:
            candidates.append(
                {
                    "mechanism": mech,
                    "T_offset": off,
                    "horizon": H,
                    "tier": "strong" if strong else "soft",
                    "IS_n": int(r["n"]),
                    "IS_win": is_win,
                    "IS_mean": is_mean,
                    "IS_mean_z": is_mz,
                    "IS_d50": is_d,
                    "IS_d_unc": is_du,
                    "IS_mfe_gt_mae": float(r["mfe_gt_mae"]) if np.isfinite(r.get("mfe_gt_mae", np.nan)) else None,
                    "IS_p_hit": float(r["p_hit_plus_first"]) if np.isfinite(r.get("p_hit_plus_first", np.nan)) else None,
                    "IS_med_exc_ratio": float(r["med_exc_ratio"])
                    if np.isfinite(r.get("med_exc_ratio", np.nan))
                    else None,
                    "Val_win": v_win,
                    "Val_d50": v_d,
                    "Val_mean": v_mean,
                    "OOS_win": o_win,
                    "OOS_d50": o_d,
                    "OOS_mean": o_mean,
                    "y2025_win": y25,
                    "y2026_win": y26,
                    "y2025_n": y25n,
                    "y2026_n": y26n,
                }
            )

    candidates.sort(
        key=lambda x: (0 if x["tier"] == "strong" else 1, -(x["IS_d50"] if np.isfinite(x["IS_d50"]) else 0))
    )

    stability = []
    if candidates:
        cdf = pd.DataFrame(candidates)
        for (mech, H), g in cdf.groupby(["mechanism", "horizon"]):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            stability.append(
                {
                    "mechanism": mech,
                    "horizon": int(H),
                    "n_clocks": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "median_IS_d50": float(g["IS_d50"].median()),
                    "median_IS_win": float(g["IS_win"].median()),
                }
            )

    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    multi_strong = [s for s in stability if s["n_clocks_strong"] >= 3]

    if multi_strong:
        verdict = "A"
        verdict_text = (
            "Failed-movement / exhaustion produces multi-clock year-stable forward fade asymmetry."
        )
        kill = False
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Weak/inconsistent failed-movement leftovers; no multi-clock strong effect. Kill for promotion."
        )
        kill = True
    else:
        verdict = "C"
        verdict_text = (
            "No forward distribution asymmetry after observable failed extension "
            "(fail / reject / weak all fail hostile gates)."
        )
        kill = True

    mech_summary = []
    is_only = res_df[(res_df["split"] == "IS") & (res_df["mechanism"] != "UNCOND_LONG")]
    for mech, _ in mechanisms:
        g = is_only[is_only["mechanism"] == mech]
        if len(g) == 0:
            continue
        mech_summary.append(
            {
                "mechanism": mech,
                "IS_med_n": float(g["n"].median()),
                "IS_med_win": float(g["win"].median()),
                "IS_med_d50": float(g["delta_win_vs_50"].median()),
                "IS_med_mean_z": float(g["mean_z"].median()),
                "IS_med_mfe_gt_mae": float(g["mfe_gt_mae"].median()),
                "IS_med_p_hit": float(g["p_hit_plus_first"].median()),
                "IS_med_exc_ratio": float(g["med_exc_ratio"].median())
                if "med_exc_ratio" in g.columns
                else np.nan,
            }
        )
    mech_summary.sort(key=lambda x: -abs(x["IS_med_d50"]))

    # Bull vs bear failure fade (IS median) — same signal construction, split by attempt dir
    side_summary = []
    for L in ATTEMPT_LS:
        for side, flag in (("bull_fail_fade", f"fail_bull_{L}"), ("bear_fail_fade", f"fail_bear_{L}")):
            wins = []
            for off in EVAL_OFFSETS:
                for H in FWD_HORIZONS:
                    s = is_all[(is_all["T_offset"] == off) & (is_all[flag] == 1)]
                    if len(s) < 40:
                        continue
                    # fade dir = -attempt_dir; bull fail → short; bear fail → long
                    dirc = -s[f"attempt_dir_{L}"].to_numpy(float)
                    signed = (s[f"fwd_{H}"].to_numpy(float) * dirc)
                    signed = signed[np.isfinite(signed)]
                    if len(signed) < 40:
                        continue
                    wins.append(float(np.mean(signed > 0)))
            if wins:
                side_summary.append(
                    {
                        "side": f"{side}_{L}",
                        "IS_med_win": float(np.median(wins)),
                        "IS_med_d50": float(np.median(wins) - 0.5),
                        "n_cells": len(wins),
                    }
                )

    report = {
        "stage": "failed_movement_exhaustion",
        "family": "failed_movement_exhaustion",
        "verdict": verdict,
        "kill_family": kill,
        "verdict_text": verdict_text,
        "scope": (
            f"RTH 09:30-15:30; NO HIGH; attempt L={ATTEMPT_LS}; OBS={OBS_W}m; "
            f"EXT={EXT_MULT}·vol; fail known at T; outcomes T+1"
        ),
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_clock_strong": len(multi_strong),
        "mechanism_IS_summary": mech_summary,
        "side_IS_summary": side_summary,
        "attempt_path_diagnostics_IS": attempt_diag[:40],
        "top_candidates": candidates[:20],
        "stability": stability,
        "next_if_killed": "expansion_retracement family (last planned intrinsic family)",
        "pivot_doc": "artifacts/research_pivot_independent_direction.md",
    }
    with open(art("nq_failed_move_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# NQ Failed Movement / Exhaustion — Minimal Report (NO HIGH)")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(
        f"Kill family: **{kill}**. Failure = missed `{EXT_MULT}·vol` extension within "
        f"`{OBS_W}m` after IS-qualified attempt — **fully known at T**. Outcomes from T+1."
    )
    md.append("")
    md.append(f"Strong: {strong_n} · Soft: {soft_n} · Multi-clock strong: {len(multi_strong)}")
    md.append("")
    md.append("## Mechanism IS summary (median across clocks/horizons)")
    md.append("")
    md.append("| Mechanism | med n | win | Δ50 | mean z | MFE>MAE | P(+1R≺) | med exc |")
    md.append("|-----------|-------|-----|-----|--------|---------|---------|---------|")
    for m in mech_summary:
        md.append(
            f"| `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | "
            f"{pp(m['IS_med_d50'])} | {m['IS_med_mean_z']:+.3f} | "
            f"{pct(m['IS_med_mfe_gt_mae'])} | {pct(m['IS_med_p_hit'])} | "
            f"{m['IS_med_exc_ratio']:.2f} |"
        )
    md.append("")
    md.append("## Bull vs bear failure → fade (IS median win)")
    md.append("")
    if not side_summary:
        md.append("Insufficient side samples.")
    else:
        md.append("| Side | med win | Δ50 | cells |")
        md.append("|------|---------|-----|-------|")
        for s in side_summary:
            md.append(
                f"| `{s['side']}` | {pct(s['IS_med_win'])} | {pp(s['IS_med_d50'])} | {s['n_cells']} |"
            )
    md.append("")
    md.append("## Surviving cells")
    md.append("")
    if not candidates:
        md.append("None.")
    else:
        md.append("| Tier | X | T+ | H | n | IS | Δ50 | mean z | Val | OOS | 2025 | 2026 |")
        md.append("|------|---|----|---|---|----|-----|--------|-----|-----|------|------|")
        for c in candidates[:15]:
            md.append(
                f"| {c['tier']} | `{c['mechanism']}` | +{c['T_offset']} | {c['horizon']} | "
                f"{c['IS_n']} | {pct(c['IS_win'])} | {pp(c['IS_d50'])} | "
                f"{c['IS_mean_z']:+.3f} | {pct(c['Val_win'])} | {pct(c['OOS_win'])} | "
                f"{pct(c.get('y2025_win'))} | {pct(c.get('y2026_win'))} |"
            )
        if not multi_strong:
            md.append("")
            md.append("No multi-clock strong mechanism — not promotable.")
    md.append("")
    md.append("## Stability")
    md.append("")
    if not stability:
        md.append("n/a")
    else:
        for s in stability:
            md.append(
                f"- `{s['mechanism']}` H{s['horizon']}: {s['n_clocks']} clocks "
                f"({s['n_clocks_strong']} strong) {s['clocks']}"
            )
    md.append("")
    md.append(f"## Final: **{verdict}**")
    md.append("")
    if kill:
        md.append("Kill failed-movement / exhaustion family.")
        md.append("Next: **expansion → retracement** (last planned intrinsic family).")
        md.append("HIGH remains frozen for later timing-only tests.")
    else:
        md.append("Only after this: test whether frozen HIGH improves timing of the surviving phenomenon.")
    md.append("")
    (art("nq_failed_move_report.md")).write_text("\n".join(md), encoding="utf-8")
    print(f"VERDICT: {verdict} kill={kill}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n} multi_strong: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
