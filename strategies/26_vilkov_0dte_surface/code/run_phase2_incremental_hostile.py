"""
Phase 2: incremental R² of Vilkov surface vs ordinary market info + hostile placebos.

No threshold optimization. No trading rules.
Fit coefficients on earlier splits only; score later splits (true OOS R²).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common.nq_session import load_es, load_nq
from common.paths import ROOT

ART = ROOT / "artifacts" / "26_vilkov_0dte_surface"
STRAT = ROOT / "strategies" / "26_vilkov_0dte_surface"
PANEL_PATH = ART / "phase1_panel_es_nq.parquet"
HORIZONS = (5, 15, 30, 60, 120)
RNG = np.random.default_rng(20260908)

# Frozen feature families (never tuned against outcomes)
OI_GAMMA_COLS = [
    "surf_atm_oi_gamma_abs_share",
    "surf_near_oi_gamma_abs_share",
    "surf_oi_gamma_balance",
    "surf_oi_gamma_pc_asym",
    "surf_oi_gamma_m_slope",
    "surf_peak_abs_oi_gamma_dist",
    "d30_surf_oi_gamma_sum",
    "d30_surf_oi_gamma_balance",
    "d30_surf_atm_oi_gamma_abs_share",
]
VOLG_COLS = [
    "volg_gamma_sum",
    "volg_gamma_balance",
    "d30_volg_gamma_sum",
]
SKEW_SHAPE_COLS = [
    "surf_iv_skew_wing",
    "d30_surf_iv_skew_wing",
    "surf_oi_gamma_m_centroid",
    "surf_peak_abs_oi_gamma_dist",
]
# Key single-family probe
ATM_SHARE = ["surf_atm_oi_gamma_abs_share"]


def tod_minutes(tod: str) -> float:
    hh, mm = str(tod).split(":")[:2]
    return int(hh) * 60 + int(mm)


def add_tod(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    mins = out["tod"].map(tod_minutes).astype(float)
    # RTH-ish span 10:00–16:00 → 360 minutes
    out["tod_sin"] = np.sin(2 * np.pi * (mins - 600.0) / 360.0)
    out["tod_cos"] = np.cos(2 * np.pi * (mins - 600.0) / 360.0)
    return out


def attach_prior_state(panel: pd.DataFrame, und: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Causal prior RV / range over [T-30m, T) using last bar open < T."""
    dec = pd.to_datetime(panel["decision_ts"])
    if getattr(dec.dt, "tz", None) is None:
        dec = dec.dt.tz_localize("America/New_York")
    dec_utc = dec.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")

    u = und.sort_values("ts").reset_index(drop=True)
    ts = pd.to_datetime(u["ts"], utc=True).dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")
    close = u["close"].to_numpy(dtype=np.float64)
    high = u["high"].to_numpy(dtype=np.float64)
    low = u["low"].to_numpy(dtype=np.float64)
    ret1 = np.empty_like(close)
    ret1[0] = np.nan
    ret1[1:] = close[1:] / close[:-1] - 1.0

    ix = np.searchsorted(ts, dec_utc, side="left")
    n = len(panel)
    prior_rv = np.full(n, np.nan)
    prior_range = np.full(n, np.nan)
    abs_prior = np.full(n, np.nan)
    t0 = dec_utc - np.timedelta64(30, "m")
    ix0 = np.searchsorted(ts, t0, side="left")
    for i in range(n):
        a = int(ix0[i])
        b = int(ix[i])  # bars with open < T
        if b <= a + 2:
            continue
        px = close[b - 1]
        if not np.isfinite(px) or px <= 0:
            continue
        rr = ret1[a:b]
        rr = rr[np.isfinite(rr)]
        if len(rr) >= 3:
            prior_rv[i] = float(np.std(rr, ddof=1) * np.sqrt(len(rr)))
        hh = high[a:b]
        ll = low[a:b]
        if len(hh):
            prior_range[i] = float((np.nanmax(hh) - np.nanmin(ll)) / px)
        if b - 1 > a:
            p0 = close[a]
            if np.isfinite(p0) and p0 > 0:
                abs_prior[i] = abs(px / p0 - 1.0)
    out = panel.copy()
    out[f"{prefix}_prior_rv30"] = prior_rv
    out[f"{prefix}_prior_range30"] = prior_range
    out[f"{prefix}_absret_prior30"] = abs_prior
    return out


def fit_ols(y: np.ndarray, X: np.ndarray) -> np.ndarray | None:
    Xb = np.column_stack([np.ones(len(X)), X])
    if len(y) < Xb.shape[1] + 30:
        return None
    beta, _, _, _ = np.linalg.lstsq(Xb, y, rcond=None)
    return beta


def predict_ols(beta: np.ndarray, X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X]) @ beta


def r2_score(y: np.ndarray, yhat: np.ndarray) -> float:
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    if ss_tot <= 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def standardize_fit(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mu = np.nanmean(X, axis=0)
    sd = np.nanstd(X, axis=0, ddof=0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return (X - mu) / sd, mu, sd


def standardize_apply(X: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    return (X - mu) / sd


def nested_eval(
    train: pd.DataFrame,
    test: pd.DataFrame,
    ycol: str,
    base_cols: list[str],
    extra_cols: list[str],
) -> dict:
    cols_a = list(base_cols)
    cols_b = list(base_cols) + [c for c in extra_cols if c not in base_cols]
    need = list(dict.fromkeys(cols_b + [ycol]))
    tr = train.dropna(subset=need).copy()
    te = test.dropna(subset=need).copy()
    if len(tr) < 200 or len(te) < 50:
        return {
            "n_train": int(len(tr)),
            "n_test": int(len(te)),
            "r2_A": float("nan"),
            "r2_ext": float("nan"),
            "delta_r2": float("nan"),
        }
    ytr = tr[ycol].to_numpy(float)
    yte = te[ycol].to_numpy(float)
    Xa_tr, mu_a, sd_a = standardize_fit(tr[cols_a].to_numpy(float))
    Xb_tr, mu_b, sd_b = standardize_fit(tr[cols_b].to_numpy(float))
    Xa_te = standardize_apply(te[cols_a].to_numpy(float), mu_a, sd_a)
    Xb_te = standardize_apply(te[cols_b].to_numpy(float), mu_b, sd_b)
    ba = fit_ols(ytr, Xa_tr)
    bb = fit_ols(ytr, Xb_tr)
    if ba is None or bb is None:
        return {
            "n_train": int(len(tr)),
            "n_test": int(len(te)),
            "r2_A": float("nan"),
            "r2_ext": float("nan"),
            "delta_r2": float("nan"),
        }
    r2a = r2_score(yte, predict_ols(ba, Xa_te))
    r2b = r2_score(yte, predict_ols(bb, Xb_te))
    return {
        "n_train": int(len(tr)),
        "n_test": int(len(te)),
        "r2_A": r2a,
        "r2_ext": r2b,
        "delta_r2": r2b - r2a,
        "n_feat_A": len(cols_a),
        "n_feat_ext": len(cols_b),
    }


def base_cols_for(inst: str) -> list[str]:
    return [
        "tod_sin",
        "tod_cos",
        f"{inst}_ret_prior30",
        f"{inst}_prior_rv30",
        f"{inst}_prior_range30",
        "surf_iv_atm",
    ]


def scramble_cols(df: pd.DataFrame, cols: list[str], how: str) -> pd.DataFrame:
    out = df.copy()
    cols = [c for c in cols if c in out.columns]
    if how == "permute_rows":
        idx = RNG.permutation(len(out))
        for c in cols:
            out[c] = out[c].to_numpy()[idx]
    elif how == "shift_fwd_1":
        for c in cols:
            out[c] = out.groupby("session_date", sort=False)[c].shift(-1)
    elif how == "shift_fwd_2":
        for c in cols:
            out[c] = out.groupby("session_date", sort=False)[c].shift(-2)
    elif how == "shift_back_1":
        for c in cols:
            out[c] = out.groupby("session_date", sort=False)[c].shift(1)
    elif how == "shift_back_2":
        for c in cols:
            out[c] = out.groupby("session_date", sort=False)[c].shift(2)
    elif how == "wrong_day":
        days = sorted(out["session_date"].dropna().unique(), key=str)
        if len(days) < 3:
            return out
        # fixed offset remap of calendar days
        perm = {days[i]: days[(i + 17) % len(days)] for i in range(len(days))}
        keyed = out.set_index(["session_date", "tod"])
        for c in cols:
            vals = []
            for sd, td in zip(out["session_date"], out["tod"]):
                od = perm.get(sd)
                try:
                    vals.append(float(keyed.loc[(od, td), c]))
                except Exception:
                    vals.append(np.nan)
            out[c] = vals
    else:
        raise ValueError(how)
    return out


def run_grid(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    protocols = [
        ("fit_Discovery_score_Validation", "Discovery", "Validation"),
        ("fit_Discovery_score_OOS", "Discovery", "OOS"),
        ("fit_DiscVal_score_OOS", "DiscVal", "OOS"),
    ]
    extensions = {
        "B_oi_gamma": OI_GAMMA_COLS,
        "C_volg_skew": VOLG_COLS + [c for c in SKEW_SHAPE_COLS if c not in VOLG_COLS],
        "atm_share_only": ATM_SHARE,
        "family_volg": VOLG_COLS,
        "family_skew": SKEW_SHAPE_COLS,
    }
    targets = []
    for inst in ("es", "nq"):
        for h in HORIZONS:
            for kind in ("rv", "absret", "ret"):
                targets.append((inst, h, kind, f"{inst}_{kind}_{h}"))

    for proto, train_name, test_name in protocols:
        if train_name == "DiscVal":
            train = panel[panel["split"].isin(["Discovery", "Validation"])]
        else:
            train = panel[panel["split"] == train_name]
        test = panel[panel["split"] == test_name]
        for inst, h, kind, ycol in targets:
            base = base_cols_for(inst)
            for ext_name, extras in extensions.items():
                ev = nested_eval(train, test, ycol, base, extras)
                rows.append(
                    {
                        "protocol": proto,
                        "train": train_name,
                        "test": test_name,
                        "instrument": inst,
                        "horizon_m": h,
                        "target": kind,
                        "model": ext_name,
                        **ev,
                    }
                )
            # A without IV vs full A (IV family contribution)
            base_no_iv = [c for c in base if c != "surf_iv_atm"]
            ev_iv = nested_eval(train, test, ycol, base_no_iv, ["surf_iv_atm"])
            rows.append(
                {
                    "protocol": proto,
                    "train": train_name,
                    "test": test_name,
                    "instrument": inst,
                    "horizon_m": h,
                    "target": kind,
                    "model": "family_iv_vs_no_iv",
                    **ev_iv,
                }
            )
    return pd.DataFrame(rows)


def run_year_stability(panel: pd.DataFrame) -> pd.DataFrame:
    """Fit Discovery (or Disc excluding year), score each calendar year — atm_share on RV."""
    rows = []
    years = sorted(int(y) for y in panel["year"].dropna().unique())
    for inst in ("es", "nq"):
        for h in (15, 30, 60):
            ycol = f"{inst}_rv_{h}"
            base = base_cols_for(inst)
            for y in years:
                test = panel[panel["year"] == y]
                if y <= 2021:
                    train = panel[(panel["split"] == "Discovery") & (panel["year"] != y)]
                    proto = "loo_Discovery_year"
                else:
                    train = panel[panel["split"] == "Discovery"]
                    proto = "fit_Discovery_score_year"
                for model, extras in [
                    ("atm_share_only", ATM_SHARE),
                    ("B_oi_gamma", OI_GAMMA_COLS),
                ]:
                    ev = nested_eval(train, test, ycol, base, extras)
                    rows.append(
                        {
                            "protocol": proto,
                            "year": y,
                            "instrument": inst,
                            "horizon_m": h,
                            "target": "rv",
                            "model": model,
                            **ev,
                        }
                    )
    return pd.DataFrame(rows)


def run_placebos(panel: pd.DataFrame) -> pd.DataFrame:
    """Hostile placebos on ΔR² for atm_share and B vs A — Disc→Val and DiscVal→OOS."""
    rows = []
    scramble_cols_list = list(dict.fromkeys(OI_GAMMA_COLS + VOLG_COLS + SKEW_SHAPE_COLS))
    protocols = [
        ("fit_Discovery_score_Validation", "Discovery", "Validation"),
        ("fit_DiscVal_score_OOS", "DiscVal", "OOS"),
    ]
    hows = [
        "identity",
        "permute_rows",
        "shift_fwd_1",
        "shift_fwd_2",
        "shift_back_1",
        "shift_back_2",
        "wrong_day",
    ]
    for proto, train_name, test_name in protocols:
        if train_name == "DiscVal":
            train0 = panel[panel["split"].isin(["Discovery", "Validation"])].copy()
        else:
            train0 = panel[panel["split"] == train_name].copy()
        test0 = panel[panel["split"] == test_name].copy()
        for how in hows:
            if how == "identity":
                train, test = train0, test0
            else:
                # scramble surface extras on BOTH train and test (breaks association globally)
                train = scramble_cols(train0, scramble_cols_list, how)
                test = scramble_cols(test0, scramble_cols_list, how)
            for inst in ("es", "nq"):
                for h in (15, 30, 60):
                    ycol = f"{inst}_rv_{h}"
                    base = base_cols_for(inst)
                    for model, extras in [
                        ("atm_share_only", ATM_SHARE),
                        ("B_oi_gamma", OI_GAMMA_COLS),
                    ]:
                        ev = nested_eval(train, test, ycol, base, extras)
                        rows.append(
                            {
                                "protocol": proto,
                                "placebo": how,
                                "instrument": inst,
                                "horizon_m": h,
                                "target": "rv",
                                "model": model,
                                **ev,
                            }
                        )
    return pd.DataFrame(rows)


def summarize(grid: pd.DataFrame, years: pd.DataFrame, placebos: pd.DataFrame) -> tuple[str, dict]:
    focus = grid[
        (grid["protocol"] == "fit_DiscVal_score_OOS")
        & (grid["target"] == "rv")
        & (grid["model"].isin(["atm_share_only", "B_oi_gamma", "C_volg_skew", "family_iv_vs_no_iv"]))
    ].copy()

    lines = [
        "# Phase 2 — Incremental R² + hostile placebos",
        "",
        "No optimization. Coefficients fit on earlier splits only; R² scored on later splits.",
        "",
        "## Primary question",
        "",
        "Does OI-gamma concentration (ATM share) add OOS explanatory power for forward RV "
        "after TOD + prior return/RV/range + IV ATM?",
        "",
        "## OOS ΔR² (fit Discovery+Validation → score OOS, target=RV)",
        "",
    ]
    if len(focus):
        piv = focus.pivot_table(
            index=["instrument", "horizon_m"],
            columns="model",
            values="delta_r2",
            aggfunc="first",
        )
        lines.append("```")
        lines.append(piv.to_string())
        lines.append("```")
        lines.append("")

    # Key headline numbers
    key_rows = focus[focus["model"] == "atm_share_only"]
    headline = {}
    for inst in ("nq", "es"):
        for h in (15, 30, 60):
            sub = key_rows[(key_rows["instrument"] == inst) & (key_rows["horizon_m"] == h)]
            if len(sub):
                headline[f"{inst}_rv_{h}_atm_delta_r2_oos"] = float(sub["delta_r2"].iloc[0])
                headline[f"{inst}_rv_{h}_atm_r2A_oos"] = float(sub["r2_A"].iloc[0])
                headline[f"{inst}_rv_{h}_atm_r2ext_oos"] = float(sub["r2_ext"].iloc[0])

    lines += ["## Placebos (ΔR² for atm_share_only, NQ RV 30m)", ""]
    pb = placebos[
        (placebos["instrument"] == "nq")
        & (placebos["horizon_m"] == 30)
        & (placebos["model"] == "atm_share_only")
        & (placebos["protocol"] == "fit_DiscVal_score_OOS")
    ]
    if len(pb):
        lines.append("```")
        lines.append(pb[["placebo", "delta_r2", "r2_A", "r2_ext", "n_test"]].to_string(index=False))
        lines.append("```")
        lines.append("")

    lines += [
        "## Year stability note",
        "",
        "Vilkov `data_opt` ends **2024-05-01** — **2025–2026 years are not in this panel.** "
        "Year table covers 2016–2024 only.",
        "",
    ]
    yf = years[(years["model"] == "atm_share_only") & (years["instrument"] == "nq") & (years["horizon_m"] == 30)]
    if len(yf):
        lines.append("```")
        lines.append(yf[["year", "protocol", "delta_r2", "n_test"]].to_string(index=False))
        lines.append("```")
        lines.append("")

    # Direction OOS
    dire = grid[
        (grid["protocol"] == "fit_DiscVal_score_OOS")
        & (grid["target"] == "ret")
        & (grid["model"].isin(["atm_share_only", "B_oi_gamma"]))
    ]
    lines += ["## Direction (signed ret) OOS ΔR² — expect near zero", ""]
    if len(dire):
        lines.append("```")
        lines.append(
            dire.pivot_table(
                index=["instrument", "horizon_m"], columns="model", values="delta_r2", aggfunc="first"
            ).to_string()
        )
        lines.append("```")
        lines.append("")

    # Verdict heuristic
    atm_nq = [headline.get(f"nq_rv_{h}_atm_delta_r2_oos", np.nan) for h in (15, 30, 60)]
    atm_es = [headline.get(f"es_rv_{h}_atm_delta_r2_oos", np.nan) for h in (15, 30, 60)]
    id_delta = float("nan")
    perm_delta = float("nan")
    if len(pb):
        id_delta = float(pb.loc[pb["placebo"] == "identity", "delta_r2"].iloc[0]) if (pb["placebo"] == "identity").any() else float("nan")
        perm_delta = float(pb.loc[pb["placebo"] == "permute_rows", "delta_r2"].iloc[0]) if (pb["placebo"] == "permute_rows").any() else float("nan")

    survive = (
        np.nanmean(atm_nq) > 0.005
        and np.nanmean(atm_es) > 0.005
        and np.isfinite(id_delta)
        and (not np.isfinite(perm_delta) or id_delta > perm_delta + 0.003)
    )
    if survive:
        verdict = "PASS_INCREMENTAL_VOL"
        note = (
            "ATM OI-gamma share shows positive OOS ΔR² for RV on both ES and NQ "
            "and beats permutation placebo — surface may carry info beyond IV/TOD/prior. "
            "Still not a trading strategy."
        )
    elif np.nanmean(atm_nq) > 0.002 or np.nanmean(atm_es) > 0.002:
        verdict = "WEAK_OR_UNSTABLE"
        note = (
            "Some positive incremental RV R², but small / not clearly surviving both legs "
            "and placebos. Do not promote to strategy search yet."
        )
    else:
        verdict = "NO_INCREMENTAL_EDGE"
        note = (
            "OI-gamma concentration does not add reliable OOS explanatory power for forward RV "
            "beyond TOD + prior state + IV ATM under this frozen design."
        )

    lines += ["## Verdict", "", f"**{verdict}** — {note}", ""]
    lines += [
        "## Artifacts",
        "",
        "- `phase2_incremental_r2.csv`",
        "- `phase2_year_stability.csv`",
        "- `phase2_placebos.csv`",
        "- `phase2_verdict.json`",
        "",
    ]
    payload = {
        "verdict": verdict,
        "note": note,
        "headline": headline,
        "placebo_nq_rv30_identity_delta_r2": id_delta,
        "placebo_nq_rv30_permute_delta_r2": perm_delta,
        "panel_years": "2016-2024 (no 2025-26 in Vilkov data_opt)",
    }
    return "\n".join(lines), payload


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    print("loading phase1 panel...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    panel["decision_ts"] = pd.to_datetime(panel["decision_ts"])
    if getattr(panel["decision_ts"].dt, "tz", None) is None:
        panel["decision_ts"] = panel["decision_ts"].dt.tz_localize("America/New_York")
    panel = add_tod(panel)

    print("attach prior RV/range from ES/NQ...", flush=True)
    t0 = panel["decision_ts"].min() - pd.Timedelta(days=2)
    t1 = panel["decision_ts"].max() + pd.Timedelta(days=1)
    es = load_es()
    nq = load_nq()
    es = es[(es["ts"] >= t0) & (es["ts"] <= t1)]
    nq = nq[(nq["ts"] >= t0) & (nq["ts"] <= t1)]
    panel = attach_prior_state(panel, es, "es")
    panel = attach_prior_state(panel, nq, "nq")
    panel.to_parquet(ART / "phase2_panel_with_prior_state.parquet", index=False)

    print("nested incremental grid...", flush=True)
    grid = run_grid(panel)
    grid.to_csv(ART / "phase2_incremental_r2.csv", index=False)

    print("year stability...", flush=True)
    years = run_year_stability(panel)
    years.to_csv(ART / "phase2_year_stability.csv", index=False)

    print("hostile placebos...", flush=True)
    placebos = run_placebos(panel)
    placebos.to_csv(ART / "phase2_placebos.csv", index=False)

    report, verdict = summarize(grid, years, placebos)
    (ART / "phase2_report.md").write_text(report, encoding="utf-8")
    (ART / "phase2_verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    (STRAT / "results" / "full_report.md").write_text(report, encoding="utf-8")
    (STRAT / "conclusion.md").write_text(
        "# Conclusion\n\n"
        f"**Phase 2: {verdict['verdict']}**\n\n"
        f"{verdict['note']}\n\n"
        f"Panel years: {verdict['panel_years']}\n\n"
        "See `artifacts/26_vilkov_0dte_surface/phase2_report.md`.\n",
        encoding="utf-8",
    )
    print(json.dumps(verdict, indent=2))
    print("DONE Phase 2", flush=True)


if __name__ == "__main__":
    main()
