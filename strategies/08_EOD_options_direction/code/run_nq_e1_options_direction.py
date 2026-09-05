"""
E1 — Prior-day EOD options state → next-day intraday NQ direction

NO HIGH. Pre-registered only. No feature sweep / combinations / rescue.

Question: Does causally available prior-session QQQ options positioning
create an asymmetric NQ intraday forward return distribution?

Information set:
  Options EOD on calendar date D (~16:15 ET) is available for NQ session_date S
  only if D < S (strict). Implemented via merge_asof(backward, allow_exact_matches=False).

Frozen features (3) × follow/fade:
  1) net_gex_proxy extreme |gex| >= IS p66 of |net_gex|
  2) near2_pc_imb extreme |imb| >= IS p80 of |near2_pc_imb|
  3) delta_put_oi_z20 extreme |z| >= 1.0 (pre-specified; z already causal)

Direction:
  follow: sign(feature) mapped to NQ trade dir
    gex:     +net_gex → long,  -net_gex → short
    pc_imb:  +put-heavy imb → short, -imb → long   (follow fear/greed)
    put_z:   +put OI buildup z → short, -z → long
  fade: opposite

Outcomes: T+1 open, horizons 5..60m. IS→Val→OOS→2025/2026.
Multi-clock strong required. Else kill entire EOD-options-for-direction family.
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
EVAL_OFFSETS = tuple(range(0, SESSION_END - NY_OPEN + 1, 15))
FWD_HORIZONS = (5, 10, 15, 30, 45, 60)
PATH_R = 1.0
IS_Y = set(range(2010, 2022))
VAL_Y = {2022, 2023, 2024}
OOS_Y = {2025, 2026}

GEX_ABS_Q = 0.66  # IS |net_gex| quantile
PC_ABS_Q = 0.80  # IS |near2_pc_imb| quantile
PUT_Z_THR = 1.0  # frozen absolute z threshold

POS_PATH = r"d:\NQ\nq_data\research\options_positioning_changes\options_positioning_features_daily.parquet"
GEX_PATH = r"d:\NQ\nq_data\data\processed\research\daily_gamma_gex_features.parquet"


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


def load_options_daily() -> pd.DataFrame:
    pos = pd.read_parquet(POS_PATH)
    gex = pd.read_parquet(GEX_PATH)
    pos["opt_date"] = pd.to_datetime(pos["date"]).dt.normalize()
    gex["opt_date"] = pd.to_datetime(gex["date"]).dt.normalize()
    gex = gex[["opt_date", "net_gex_proxy", "net_gex_2pct"]].copy()
    keep = [
        "opt_date",
        "near2_pc_imb",
        "pc_oi_ratio",
        "delta_put_oi_z20",
        "delta_call_oi_z20",
        "delta_total_oi_z20",
        "delta_near2_pc_imb",
    ]
    pos = pos[keep].copy()
    out = pos.merge(gex, on="opt_date", how="inner")
    out = out.sort_values("opt_date").drop_duplicates("opt_date")
    return out


def build_nq_panel() -> pd.DataFrame:
    """Reuse extreme-asym panel if present; else build minimal fwd panel."""
    reuse = art("nq_extreme_asym_panel.parquet")
    if reuse.exists():
        p = pd.read_parquet(reuse)
        need = {"session_date", "year", "split", "T_offset", "fwd_15", "fwd_z_15", "mfe_15", "mae_15", "hit1R_long_15", "vol"}
        if need.issubset(p.columns) and len(p) > 50000:
            print(f"Reusing NQ panel rows={len(p)}", flush=True)
            return p

    print("Building NQ RTH panel...", flush=True)
    df = load_nq()
    rows: list[dict] = []
    n_days = 0
    atr_hist: list[float] = []
    decision_offsets = tuple(range(0, SESSION_END - NY_OPEN + 1, 5))

    for sd, g in df.groupby("session_date", sort=True):
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 16 * 60)].reset_index(drop=True)
        if len(rth) < 220:
            continue
        n_days += 1
        year = int(rth.iloc[0]["year"])
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

        for off in decision_offsets:
            T = NY_OPEN + off
            if T not in idx:
                continue
            j = idx[T]
            after = np.where(ny > T)[0]
            if len(after) < max(FWD_HORIZONS):
                continue
            atr_so_far = float(np.mean(tr[max(0, j - 29) : j + 1]))
            vol = max(atr_so_far, 0.25 * prior_atr, 0.25)
            entry_i = int(after[0])
            entry = float(o[entry_i])
            row: dict[str, Any] = {
                "session_date": str(sd),
                "year": year,
                "dow": int(rth.iloc[0]["dow"]),
                "split": split_of(year),
                "T_offset": off,
                "vol": vol,
            }
            for H in FWD_HORIZONS:
                end_i = entry_i + H - 1
                if end_i >= len(c):
                    for key in (f"fwd_{H}", f"fwd_z_{H}", f"mfe_{H}", f"mae_{H}", f"hit1R_long_{H}"):
                        row[key] = np.nan
                    continue
                hh = h[entry_i : end_i + 1]
                ll = l[entry_i : end_i + 1]
                fwd = float(c[end_i] - entry)
                row[f"fwd_{H}"] = fwd
                row[f"fwd_z_{H}"] = fwd / vol
                row[f"mfe_{H}"] = float(hh.max() - entry)
                row[f"mae_{H}"] = float(entry - ll.min())
                row[f"hit1R_long_{H}"] = first_hit(hh, ll, entry, PATH_R * vol)
            rows.append(row)
            day_trs.append(float(tr[j]))
        if day_trs:
            atr_hist.append(float(np.mean(day_trs)))
        if n_days % 500 == 0:
            print(f"  days={n_days} rows={len(rows)}", flush=True)

    return pd.DataFrame(rows)


def main() -> None:
    print("=== E1: Prior-day EOD Options -> Next-day Intraday NQ Direction (NO HIGH) ===", flush=True)
    print(
        f"FROZEN: GEX |net|>=IS_p{int(GEX_ABS_Q*100)}; "
        f"PC |imb|>=IS_p{int(PC_ABS_Q*100)}; put_z |z|>={PUT_Z_THR}; follow+fade only",
        flush=True,
    )

    panel = build_nq_panel()
    opt = load_options_daily()
    print(f"Options days={len(opt)} GEX/PC coverage {opt['opt_date'].min().date()}..{opt['opt_date'].max().date()}", flush=True)

    # Daily session keys for causal merge
    panel["session_dt"] = pd.to_datetime(panel["session_date"]).dt.normalize()
    sessions = (
        panel[["session_date", "session_dt", "year", "split"]]
        .drop_duplicates("session_date")
        .sort_values("session_dt")
        .reset_index(drop=True)
    )
    opt_m = opt.sort_values("opt_date")
    merged = pd.merge_asof(
        sessions,
        opt_m,
        left_on="session_dt",
        right_on="opt_date",
        direction="backward",
        allow_exact_matches=False,
    )
    # lag days sanity
    merged["opt_lag_days"] = (merged["session_dt"] - merged["opt_date"]).dt.days
    n_ok = merged["net_gex_proxy"].notna().sum()
    print(
        f"Sessions with prior options: {n_ok}/{len(merged)}; "
        f"med lag days={merged['opt_lag_days'].median()}",
        flush=True,
    )

    # IS thresholds on unique days with features
    is_days = merged[(merged["split"] == "IS") & merged["net_gex_proxy"].notna()]
    gex_thr = float(is_days["net_gex_proxy"].abs().quantile(GEX_ABS_Q))
    pc_thr = float(is_days["near2_pc_imb"].abs().quantile(PC_ABS_Q))
    meta = {
        "family": "E1_eod_options_intraday_direction",
        "causality": "options opt_date < session_date (merge_asof backward, no exact match)",
        "frozen": {
            "gex_abs_quantile_IS": GEX_ABS_Q,
            "gex_abs_threshold_IS": gex_thr,
            "pc_imb_abs_quantile_IS": PC_ABS_Q,
            "pc_imb_abs_threshold_IS": pc_thr,
            "put_z_abs_threshold": PUT_Z_THR,
            "direction_maps": {
                "gex_follow": "sign(net_gex_proxy)",
                "pc_follow": "-sign(near2_pc_imb)  # put-heavy -> short",
                "putz_follow": "-sign(delta_put_oi_z20)  # put buildup -> short",
                "fade": "opposite of follow",
            },
        },
        "no_HIGH": True,
        "sources": {"pos": POS_PATH, "gex": GEX_PATH},
    }
    with open(art("nq_e1_options_dir_thresholds_IS.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)
    print(f"IS thr |gex|={gex_thr:.3e} |pc_imb|={pc_thr:.4f} |put_z|={PUT_Z_THR}", flush=True)

    # Labels on daily table
    def sgn(x: float) -> int:
        if not np.isfinite(x) or x == 0:
            return 0
        return 1 if x > 0 else -1

    labs = []
    for _, r in merged.iterrows():
        gex = float(r["net_gex_proxy"]) if pd.notna(r["net_gex_proxy"]) else np.nan
        pc = float(r["near2_pc_imb"]) if pd.notna(r["near2_pc_imb"]) else np.nan
        pz = float(r["delta_put_oi_z20"]) if pd.notna(r["delta_put_oi_z20"]) else np.nan

        gex_ext = np.isfinite(gex) and abs(gex) >= gex_thr
        pc_ext = np.isfinite(pc) and abs(pc) >= pc_thr
        pz_ext = np.isfinite(pz) and abs(pz) >= PUT_Z_THR

        gex_dir = sgn(gex)
        pc_dir = -sgn(pc)  # put-heavy (+) -> short
        pz_dir = -sgn(pz)  # put buildup (+) -> short

        labs.append(
            {
                "session_date": r["session_date"],
                "opt_date": str(r["opt_date"].date()) if pd.notna(r["opt_date"]) else None,
                "opt_lag_days": float(r["opt_lag_days"]) if pd.notna(r["opt_lag_days"]) else np.nan,
                "net_gex_proxy": gex,
                "near2_pc_imb": pc,
                "delta_put_oi_z20": pz,
                "x_gex_follow": gex_dir if gex_ext and gex_dir != 0 else 0,
                "x_gex_fade": (-gex_dir) if gex_ext and gex_dir != 0 else 0,
                "x_pc_follow": pc_dir if pc_ext and pc_dir != 0 else 0,
                "x_pc_fade": (-pc_dir) if pc_ext and pc_dir != 0 else 0,
                "x_putz_follow": pz_dir if pz_ext and pz_dir != 0 else 0,
                "x_putz_fade": (-pz_dir) if pz_ext and pz_dir != 0 else 0,
            }
        )
    lab_df = pd.DataFrame(labs)
    panel = panel.merge(lab_df, on="session_date", how="left")
    for col in (
        "x_gex_follow",
        "x_gex_fade",
        "x_pc_follow",
        "x_pc_fade",
        "x_putz_follow",
        "x_putz_fade",
    ):
        panel[col] = panel[col].fillna(0).astype(int)

    panel_path = art("nq_e1_options_dir_panel.parquet")
    panel.to_parquet(panel_path, index=False)
    print(f"Panel rows={len(panel)} days={panel['session_date'].nunique()}", flush=True)

    mechanisms = [
        ("gex_follow", "x_gex_follow"),
        ("gex_fade", "x_gex_fade"),
        ("pc_follow", "x_pc_follow"),
        ("pc_fade", "x_pc_fade"),
        ("putz_follow", "x_putz_follow"),
        ("putz_fade", "x_putz_fade"),
    ]

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
                unc_win = float(np.nanmean(fwd > 0))
                unc_mean = float(np.nanmean(fwd))
                results.append(
                    {
                        "mechanism": "UNCOND_LONG",
                        "T_offset": off,
                        "horizon": H,
                        "split": split,
                        "n": int(np.isfinite(fwd).sum()),
                        "rate": 1.0,
                        "win": unc_win,
                        "mean": unc_mean,
                        "median": float(np.nanmedian(fwd)),
                        "mean_z": float(np.nanmean(fz)),
                        "mfe_gt_mae": float(np.nanmean(base[f"mfe_{H}"] > base[f"mae_{H}"])),
                        "p_hit_plus_first": float(np.nanmean(base[f"hit1R_long_{H}"])),
                        "delta_win_vs_unc": 0.0,
                        "delta_win_vs_50": unc_win - 0.5,
                    }
                )
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
                            "unc_win": unc_win,
                            "unc_mean": unc_mean,
                            "delta_win_vs_unc": st["win"] - unc_win,
                            "delta_mean_vs_unc": st["mean"] - unc_mean,
                            "delta_win_vs_50": st["win"] - 0.5,
                        }
                    )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_e1_options_dir_results.csv"), index=False)
    print(f"Result rows: {len(res_df)}", flush=True)

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
            "Prior-day EOD options state produces multi-clock year-stable intraday directional asymmetry."
        )
        kill = False
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Weak/inconsistent EOD-options directional leftovers; no multi-clock strong effect. "
            "Kill EOD-options-for-direction family."
        )
        kill = True
    else:
        verdict = "C"
        verdict_text = (
            "No intraday directional asymmetry from prior-day EOD GEX / PC-imbalance / put-OI-z states "
            "(follow and fade both fail hostile gates)."
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
            }
        )
    mech_summary.sort(key=lambda x: -abs(x["IS_med_d50"]))

    # Coverage note for 2026
    cov = {
        "y2025_sessions_with_opt": int(
            panel[(panel["year"] == 2025) & (panel["x_gex_follow"] != 0)].session_date.nunique()
            + panel[(panel["year"] == 2025) & (panel["x_gex_fade"] != 0)].session_date.nunique()
        ),
        "y2026_sessions_any_signal": int(
            panel.loc[
                (panel["year"] == 2026)
                & (
                    (panel["x_gex_follow"] != 0)
                    | (panel["x_pc_follow"] != 0)
                    | (panel["x_putz_follow"] != 0)
                ),
                "session_date",
            ].nunique()
        ),
        "opt_last_date": str(opt["opt_date"].max().date()),
    }

    report = {
        "stage": "E1_eod_options_intraday_direction",
        "family": "eod_options_for_direction",
        "verdict": verdict,
        "kill_family": kill,
        "verdict_text": verdict_text,
        "scope": "Prior-day EOD QQQ options → next-day NQ RTH clocks; NO HIGH; intraday direction only",
        "n_strong_cells": strong_n,
        "n_soft_cells": soft_n,
        "n_multi_clock_strong": len(multi_strong),
        "coverage": cov,
        "mechanism_IS_summary": mech_summary,
        "top_candidates": candidates[:20],
        "stability": stability,
        "next_if_killed": "scheduled_information_events",
        "pivot_doc": "artifacts/research_pivot_external_direction.md",
    }
    with open(art("nq_e1_options_dir_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# E1 — Prior-day EOD Options → Next-day Intraday NQ Direction (NO HIGH)")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(
        f"Kill EOD-options-for-direction family: **{kill}**. "
        "Tests **intraday direction**, not next-day range/vol. No HIGH."
    )
    md.append("")
    md.append(
        f"Frozen: `|gex|≥IS p{int(GEX_ABS_Q*100)}` thr={gex_thr:.3e}; "
        f"`|pc_imb|≥IS p{int(PC_ABS_Q*100)}` thr={pc_thr:.4f}; `|put_z|≥{PUT_Z_THR}`."
    )
    md.append("")
    md.append(
        f"Options last date: `{cov['opt_last_date']}`; "
        f"2026 sessions with any signal: {cov['y2026_sessions_any_signal']}."
    )
    md.append("")
    md.append(f"Strong: {strong_n} · Soft: {soft_n} · Multi-clock strong: {len(multi_strong)}")
    md.append("")
    md.append("## Mechanism IS summary (median across clocks/horizons)")
    md.append("")
    md.append("| Mechanism | med n | win | Δ50 | mean z | MFE>MAE | P(+1R≺) |")
    md.append("|-----------|-------|-----|-----|--------|---------|---------|")
    for m in mech_summary:
        md.append(
            f"| `{m['mechanism']}` | {m['IS_med_n']:.0f} | {pct(m['IS_med_win'])} | "
            f"{pp(m['IS_med_d50'])} | {m['IS_med_mean_z']:+.3f} | "
            f"{pct(m['IS_med_mfe_gt_mae'])} | {pct(m['IS_med_p_hit'])} |"
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
        md.append("**Kill entire EOD-options-for-direction family.**")
        md.append("Do not rescue with more options feature engineering.")
        md.append("Next: **scheduled information events**.")
        md.append("HIGH remains frozen for later timing-only tests.")
    else:
        md.append("Only after this: test whether frozen HIGH improves timing of the surviving phenomenon.")
    md.append("")
    (art("nq_e1_options_dir_report.md")).write_text("\n".join(md), encoding="utf-8")

    # Update external pivot
    pivot = art("research_pivot_external_direction.md")
    if pivot.exists():
        note = (
            f"\n\n## E1 result (2026-09-05)\n\n"
            f"Prior-day EOD options → next-day intraday direction: **{verdict}** (kill={kill}).\n\n"
            + (
                "Kill EOD-options-for-direction. Next: scheduled information events.\n"
                if kill
                else "Promoted candidate exists — proceed to HIGH timing test only after confirming multi-clock A.\n"
            )
        )
        text = pivot.read_text(encoding="utf-8")
        if "## E1 result" not in text:
            pivot.write_text(text.rstrip() + note, encoding="utf-8")

    print(f"VERDICT: {verdict} kill={kill}", flush=True)
    print(f"strong/soft: {strong_n}/{soft_n} multi_strong: {len(multi_strong)}", flush=True)


if __name__ == "__main__":
    main()
