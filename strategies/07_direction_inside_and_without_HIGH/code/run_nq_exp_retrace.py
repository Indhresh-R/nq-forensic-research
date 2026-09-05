"""
NQ Intrinsic Directional Discovery — Family 4: Expansion → Retracement

NO HIGH. Liquid RTH 09:30-15:30.

Question: After a genuine range expansion, does the subsequent retracement
have a predictable directional/path structure that is NOT just another
failed-extension / exhaustion disguise?

CRITICAL distinctions vs Family 3 (failed movement):
  - Expansion is a COMPLETED range at T_e (high-low), not "expected extension miss"
  - Signal uses retracement RATIO of that completed expansion (ρ = giveback / E)
  - No "target extension" level; ratios are pre-frozen Fib-style cuts

FROZEN BEFORE RESULTS (do not sweep):
  EXP_L ∈ {15, 30}
  OBS_W = 15
  SHALLOW_MAX = 0.25      # ρ < this → minimal retrace → continuation
  SHALLOW_HI  = 0.50      # [0.25, 0.50) → shallow → continuation
  DEEP_MIN    = 0.50      # ρ >= this → deep → reversal
  DEEP618     = 0.618
  FAST_BARS   = 5         # hit ρ>=0.33 within first 5m of OBS → fast retrace
  RHO_MARK    = 0.33      # mark for time-to-retrace / speed
  EXP_Q       = 0.66      # IS E/vol quantile for "genuine expansion"

Timeline (causal; all known at T):
  [EXP_L bars] → T_e (expansion complete: E, D)
  [OBS_W bars] → T   (measure ρ, time-to-mark, speed ratio)
  outcomes from T+1 open

Hostile: IS→Val→OOS→2025/2026, multi-clock required, no rescue.
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
EXP_LS = (15, 30)
OBS_W = 15
SHALLOW_MAX = 0.25
SHALLOW_HI = 0.50
DEEP_MIN = 0.50
DEEP618 = 0.618
FAST_BARS = 5
RHO_MARK = 0.33
EXP_Q = 0.66
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


def retrace_stats(
    h: np.ndarray,
    l: np.ndarray,
    i_te: int,
    i_t: int,
    exp_high: float,
    exp_low: float,
    E: float,
    direction: int,
) -> dict[str, float]:
    """Retracement of completed expansion over (i_te, i_t]. Observable at T."""
    if E <= 0 or direction == 0 or i_t <= i_te:
        return {
            "rho": np.nan,
            "t_mark": np.nan,
            "speed_ratio": np.nan,
            "retrace_pts": np.nan,
        }

    max_retrace = 0.0
    t_mark = None
    mark_pts = RHO_MARK * E
    for i in range(i_te + 1, i_t + 1):
        if direction > 0:
            # giveback from expansion high
            r = float(exp_high - l[i])
        else:
            r = float(h[i] - exp_low)
        if r > max_retrace:
            max_retrace = r
        if t_mark is None and r >= mark_pts:
            t_mark = i - i_te

    rho = max_retrace / E
    # expansion "speed" proxy: full expansion over EXP window length is encoded by caller via L
    # retrace speed to mark: RHO_MARK / t_mark (fraction of E per bar)
    # speed_ratio = (RHO_MARK / t_mark) / (1 / L_exp) = RHO_MARK * L_exp / t_mark
    # L_exp passed via scaling outside — store t_mark; speed_ratio filled by caller with L
    return {
        "rho": float(rho),
        "t_mark": float(t_mark) if t_mark is not None else np.nan,
        "speed_ratio": np.nan,  # filled with L below
        "retrace_pts": float(max_retrace),
    }


def main() -> None:
    print("=== Expansion -> Retracement (NO HIGH) ===", flush=True)
    print(
        "FROZEN: "
        f"SHALLOW<{SHALLOW_MAX}, shallow-cont=[{SHALLOW_MAX},{SHALLOW_HI}), "
        f"deep>={DEEP_MIN}, deep618>={DEEP618}, FAST_BARS={FAST_BARS}, "
        f"RHO_MARK={RHO_MARK}, OBS={OBS_W}, EXP_Q={EXP_Q}",
        flush=True,
    )
    panel_path = art("nq_exp_retrace_panel.parquet")
    rebuild = True
    if panel_path.exists():
        probe = pd.read_parquet(panel_path)
        need = {"x_cont_min_15", "x_rev_deep_15", "x_rev_fast_15", "fwd_15", "rho_15", "E_z_15"}
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

                T_e = T - OBS_W
                if T_e not in idx or T_e < NY_OPEN:
                    continue
                i_te = idx[T_e]
                i_t = j

                atr_te = float(np.mean(tr[max(0, i_te - 29) : i_te + 1]))
                vol_te = max(atr_te, 0.25 * prior_atr, 0.25)
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
                    "vol_te": vol_te,
                    "vol": vol_t,
                }

                for L in EXP_LS:
                    a0_ny = T_e - L + 1
                    if a0_ny not in idx or a0_ny < NY_OPEN:
                        for k in (
                            f"E_{L}",
                            f"E_z_{L}",
                            f"exp_dir_{L}",
                            f"rho_{L}",
                            f"t_mark_{L}",
                            f"speed_ratio_{L}",
                        ):
                            row[k] = np.nan
                        continue

                    i0 = idx[a0_ny]
                    # Completed expansion range over [i0, i_te]
                    seg_h = h[i0 : i_te + 1]
                    seg_l = l[i0 : i_te + 1]
                    exp_high = float(seg_h.max())
                    exp_low = float(seg_l.min())
                    E = exp_high - exp_low
                    net = float(c[i_te] - o[i0])
                    direction = 1 if net > 0 else (-1 if net < 0 else 0)
                    # if flat net but range exists, use close vs midpoint
                    if direction == 0 and E > 0:
                        mid = 0.5 * (exp_high + exp_low)
                        direction = 1 if c[i_te] >= mid else -1

                    E_z = E / vol_te if vol_te > 0 else np.nan
                    st = retrace_stats(h, l, i_te, i_t, exp_high, exp_low, E, direction)
                    t_mark = st["t_mark"]
                    # speed_ratio = (RHO_MARK / t_mark) / (1/L) = RHO_MARK * L / t_mark
                    if np.isfinite(t_mark) and t_mark > 0:
                        speed_ratio = (RHO_MARK * L) / t_mark
                    else:
                        speed_ratio = np.nan  # never hit mark in OBS → "slow / no retrace"

                    row[f"E_{L}"] = E
                    row[f"E_z_{L}"] = E_z
                    row[f"exp_dir_{L}"] = direction
                    row[f"rho_{L}"] = st["rho"]
                    row[f"t_mark_{L}"] = t_mark
                    row[f"speed_ratio_{L}"] = speed_ratio

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

        thresholds: dict[str, dict[int, float]] = {}
        is_p = panel[panel["split"] == "IS"]
        for L in EXP_LS:
            key = f"E_z_{L}"
            thresholds[key] = {}
            for off in DECISION_OFFSETS:
                s = is_p.loc[is_p["T_offset"] == off, key].dropna()
                if len(s) < 100:
                    continue
                thresholds[key][off] = float(s.quantile(EXP_Q))

        meta = {
            "frozen_definitions": {
                "expansion": "E = high-low over EXP_L ending T_e; genuine if E/vol_te >= IS p66",
                "direction": "sign(close_Te - open_start); midpoint tie-break",
                "rho": "max giveback from expansion extreme over OBS / E",
                "shallow_max": SHALLOW_MAX,
                "shallow_hi": SHALLOW_HI,
                "deep_min": DEEP_MIN,
                "deep618": DEEP618,
                "rho_mark": RHO_MARK,
                "fast_bars": FAST_BARS,
                "obs_w": OBS_W,
                "speed_ratio": "RHO_MARK * EXP_L / t_to_mark",
                "not_failed_movement": (
                    "No expected-extension target; signal is retracement structure "
                    "of a completed range, not miss of a forward target."
                ),
            },
            "thresholds": thresholds,
        }
        with open(art("nq_exp_retrace_thresholds_IS.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        labs = []
        for _, r in panel.iterrows():
            off = int(r["T_offset"])
            lab: dict[str, Any] = {}
            for L in EXP_LS:
                Ez = float(r[f"E_z_{L}"])
                d = int(r[f"exp_dir_{L}"]) if np.isfinite(r[f"exp_dir_{L}"]) else 0
                rho = float(r[f"rho_{L}"])
                t_mark = float(r[f"t_mark_{L}"])
                spd = float(r[f"speed_ratio_{L}"])
                th = thresholds.get(f"E_z_{L}", {}).get(off)
                is_exp = th is not None and np.isfinite(Ez) and Ez >= th and d != 0 and np.isfinite(rho)

                # expansion → continuation (minimal retrace)
                cont_min = is_exp and rho < SHALLOW_MAX
                # expansion → shallow retrace → continuation
                cont_shallow = is_exp and (SHALLOW_MAX <= rho < SHALLOW_HI)
                # expansion → deep retrace → reversal
                rev_deep = is_exp and rho >= DEEP_MIN
                rev_618 = is_exp and rho >= DEEP618
                # fast retrace (time): hit mark within FAST_BARS → reversal
                rev_fast = is_exp and np.isfinite(t_mark) and t_mark <= FAST_BARS
                # slow / holds: never hit RHO_MARK in OBS → continuation
                cont_slow = is_exp and not np.isfinite(t_mark)
                # speed: retrace much faster than expansion pace → reversal
                # frozen cut: speed_ratio >= 2.0 (pre-specified)
                rev_fast_spd = is_exp and np.isfinite(spd) and spd >= 2.0

                lab[f"x_cont_min_{L}"] = d if cont_min else 0
                lab[f"x_cont_shallow_{L}"] = d if cont_shallow else 0
                lab[f"x_rev_deep_{L}"] = (-d) if rev_deep else 0
                lab[f"x_rev_618_{L}"] = (-d) if rev_618 else 0
                lab[f"x_rev_fast_{L}"] = (-d) if rev_fast else 0
                lab[f"x_cont_slow_{L}"] = d if cont_slow else 0
                lab[f"x_rev_fastspd_{L}"] = (-d) if rev_fast_spd else 0
                lab[f"is_exp_{L}"] = 1 if is_exp else 0
            labs.append(lab)

        panel = pd.concat([panel.reset_index(drop=True), pd.DataFrame(labs)], axis=1)
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)} days~{panel['session_date'].nunique()}", flush=True)
    else:
        thresholds = json.loads((art("nq_exp_retrace_thresholds_IS.json")).read_text(encoding="utf-8"))[
            "thresholds"
        ]

    mechanisms: list[tuple[str, str]] = []
    for L in EXP_LS:
        mechanisms.extend(
            [
                (f"cont_min_{L}", f"x_cont_min_{L}"),
                (f"cont_shallow_{L}", f"x_cont_shallow_{L}"),
                (f"rev_deep_{L}", f"x_rev_deep_{L}"),
                (f"rev_618_{L}", f"x_rev_618_{L}"),
                (f"rev_fast_{L}", f"x_rev_fast_{L}"),
                (f"cont_slow_{L}", f"x_cont_slow_{L}"),
                (f"rev_fastspd_{L}", f"x_rev_fastspd_{L}"),
            ]
        )

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

                    L = int(mech.rsplit("_", 1)[-1])
                    rho = s[f"rho_{L}"].to_numpy(float)
                    t_mark = s[f"t_mark_{L}"].to_numpy(float)
                    spd = s[f"speed_ratio_{L}"].to_numpy(float)
                    rho_f = rho[np.isfinite(rho)]
                    t_f = t_mark[np.isfinite(t_mark)]
                    spd_f = spd[np.isfinite(spd)]

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
                            "med_rho": float(np.median(rho_f)) if len(rho_f) else np.nan,
                            "med_t_mark": float(np.median(t_f)) if len(t_f) else np.nan,
                            "med_speed_ratio": float(np.median(spd_f)) if len(spd_f) else np.nan,
                            "unc_win": unc_win,
                            "unc_mean": unc_mean,
                            "delta_win_vs_unc": st["win"] - unc_win,
                            "delta_mean_vs_unc": st["mean"] - unc_mean,
                            "delta_win_vs_50": st["win"] - 0.5,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_exp_retrace_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

    # Path diagnostics on expansions (IS): rho / time / speed distributions
    path_diag = []
    is_all = panel[panel["split"] == "IS"]
    for L in EXP_LS:
        for off in EVAL_OFFSETS:
            s = is_all[(is_all["T_offset"] == off) & (is_all[f"is_exp_{L}"] == 1)]
            if len(s) < 80:
                continue
            rho = s[f"rho_{L}"].to_numpy(float)
            t_mark = s[f"t_mark_{L}"].to_numpy(float)
            path_diag.append(
                {
                    "L": L,
                    "T_offset": off,
                    "n_exp": int(len(s)),
                    "med_rho": float(np.nanmedian(rho)),
                    "p_rho_lt_025": float(np.nanmean(rho < SHALLOW_MAX)),
                    "p_rho_shallow": float(np.nanmean((rho >= SHALLOW_MAX) & (rho < SHALLOW_HI))),
                    "p_rho_deep": float(np.nanmean(rho >= DEEP_MIN)),
                    "p_rho_618": float(np.nanmean(rho >= DEEP618)),
                    "p_hit_mark": float(np.nanmean(np.isfinite(t_mark))),
                    "med_t_mark_if_hit": float(np.nanmedian(t_mark[np.isfinite(t_mark)]))
                    if np.isfinite(t_mark).any()
                    else np.nan,
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
                    "IS_med_rho": float(r["med_rho"]) if np.isfinite(r.get("med_rho", np.nan)) else None,
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
            "Expansion→retracement produces multi-clock year-stable forward asymmetry "
            "(continuation and/or reversal by retrace structure)."
        )
        kill = False
        stop_tree = False
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Weak/inconsistent expansion→retracement leftovers; no multi-clock strong effect. "
            "Kill for promotion."
        )
        kill = True
        stop_tree = True
    else:
        verdict = "C"
        verdict_text = (
            "No forward distribution asymmetry from expansion→retracement structure "
            "(min/shallow/deep/fast/slow all fail hostile gates)."
        )
        kill = True
        stop_tree = True

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
                "IS_med_rho": float(g["med_rho"].median()) if "med_rho" in g.columns else np.nan,
            }
        )
    mech_summary.sort(key=lambda x: -abs(x["IS_med_d50"]))

    report = {
        "stage": "expansion_retracement",
        "family": "expansion_retracement",
        "verdict": verdict,
        "kill_family": kill,
        "stop_directional_family_tree": stop_tree,
        "verdict_text": verdict_text,
        "scope": (
            f"RTH 09:30-15:30; NO HIGH; EXP_L={EXP_LS}; OBS={OBS_W}; "
            f"rho cuts {SHALLOW_MAX}/{SHALLOW_HI}/{DEEP_MIN}/{DEEP618}; outcomes T+1"
        ),
        "frozen_cuts": {
            "SHALLOW_MAX": SHALLOW_MAX,
            "SHALLOW_HI": SHALLOW_HI,
            "DEEP_MIN": DEEP_MIN,
            "DEEP618": DEEP618,
            "FAST_BARS": FAST_BARS,
            "RHO_MARK": RHO_MARK,
            "speed_ratio_cut": 2.0,
            "EXP_Q": EXP_Q,
        },
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_clock_strong": len(multi_strong),
        "mechanism_IS_summary": mech_summary,
        "path_diagnostics_IS": path_diag[:40],
        "top_candidates": candidates[:20],
        "stability": stability,
        "program_implication": (
            "If killed: stop intrinsic OHLC directional-family tree. "
            "Do not invent Family #6 momentum/reversal transforms. "
            "Next research pivot = event-driven / different market mechanism. "
            "Frozen HIGH remains valid opportunity-timing only."
        ),
        "pivot_doc": "artifacts/research_pivot_independent_direction.md",
    }
    with open(art("nq_exp_retrace_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# NQ Expansion → Retracement — Minimal Report (NO HIGH)")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(
        f"Kill family: **{kill}**. Stop directional tree: **{stop_tree}**. "
        f"Signal = retracement structure of a **completed** expansion (ρ = giveback/E), "
        f"not missed forward extension."
    )
    md.append("")
    md.append(
        f"Frozen cuts: min ρ<{SHALLOW_MAX}; shallow[{SHALLOW_MAX},{SHALLOW_HI}); "
        f"deep≥{DEEP_MIN}; 618≥{DEEP618}; fast mark≤{FAST_BARS}m; OBS={OBS_W}."
    )
    md.append("")
    md.append(f"Strong: {strong_n} · Soft: {soft_n} · Multi-clock strong: {len(multi_strong)}")
    md.append("")
    md.append("## Mechanism IS summary (median across clocks/horizons)")
    md.append("")
    md.append("| Mechanism | med n | win | Δ50 | mean z | MFE>MAE | P(+1R≺) | med ρ |")
    md.append("|-----------|-------|-----|-----|--------|---------|---------|-------|")
    for m in mech_summary:
        md.append(
            f"| `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | "
            f"{pp(m['IS_med_d50'])} | {m['IS_med_mean_z']:+.3f} | "
            f"{pct(m['IS_med_mfe_gt_mae'])} | {pct(m['IS_med_p_hit'])} | "
            f"{m['IS_med_rho']:.2f} |"
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
        md.append("Kill expansion→retracement family.")
        md.append("")
        md.append("### STOP — intrinsic directional-family tree complete")
        md.append("")
        md.append(
            "All four planned families from NQ's own price/vol path failed to produce "
            "stable short-horizon direction. **Do not invent Family #6** as another "
            "momentum/reversal transform of the same OHLC."
        )
        md.append("")
        md.append("| Family | Result |")
        md.append("|--------|--------|")
        md.append("| Serial dependence | killed |")
        md.append("| Vol-standardized extremes | killed |")
        md.append("| Failed movement / exhaustion | killed |")
        md.append("| Expansion → retracement | killed |")
        md.append("| Frozen HIGH | opportunity timing only (kept) |")
        md.append("")
        md.append(
            "Genuine next pivot: **event-driven information or a different market mechanism**, "
            "not another filter on recent NQ bars."
        )
    else:
        md.append("Only after this: test whether frozen HIGH improves timing of the surviving phenomenon.")
    md.append("")
    (art("nq_exp_retrace_report.md")).write_text("\n".join(md), encoding="utf-8")

    # Update pivot doc with terminal status
    pivot = art("research_pivot_independent_direction.md")
    if pivot.exists():
        stop_note = (
            "\n\n## Terminal status (2026-09-05)\n\n"
            f"Family 4 expansion→retracement: **{verdict}** (kill={kill}).\n\n"
            "All four intrinsic OHLC directional families killed. "
            "**Stop the current directional-family tree.** "
            "Do not invent another momentum/reversal transform. "
            "Next: event-driven / different mechanism. HIGH remains timing-only.\n"
        )
        text = pivot.read_text(encoding="utf-8")
        if "## Terminal status" not in text:
            pivot.write_text(text.rstrip() + stop_note, encoding="utf-8")

    print(f"VERDICT: {verdict} kill={kill} stop_tree={stop_tree}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n} multi_strong: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
