"""
Phase 3: stability / mechanism audit for residual OI-gamma concentration.

No threshold search. No entry/exit rules. No Sharpe hunting.
Asks *why* the residual ES RV effect exists (and whether it is coherent).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common.paths import ROOT

ART = ROOT / "artifacts" / "26_vilkov_0dte_surface"
STRAT = ROOT / "strategies" / "26_vilkov_0dte_surface"
PANEL_PATH = ART / "phase2_panel_with_prior_state.parquet"
ATM = "surf_atm_oi_gamma_abs_share"
RNG = np.random.default_rng(20260908)

# Frozen probes — not chosen by outcome maximization
SURFACE_PART_PROBES = {
    "atm_share": [ATM],
    "near_share": ["surf_near_oi_gamma_abs_share"],
    "peak_dist": ["surf_peak_abs_oi_gamma_dist"],
    "m_centroid": ["surf_oi_gamma_m_centroid"],
    "m_slope": ["surf_oi_gamma_m_slope"],
    "pc_asym": ["surf_oi_gamma_pc_asym"],
}
CHRONO_BLOCKS = [
    ("2016_2018", (2016, 2017, 2018)),
    ("2019_2021", (2019, 2020, 2021)),
    ("2022_2023", (2022, 2023)),
    ("2024", (2024,)),
]


def tod_minutes(tod: str) -> float:
    hh, mm = str(tod).split(":")[:2]
    return int(hh) * 60 + int(mm)


def add_tod(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "tod_sin" in out.columns and "tod_cos" in out.columns:
        return out
    mins = out["tod"].map(tod_minutes).astype(float)
    out["tod_sin"] = np.sin(2 * np.pi * (mins - 600.0) / 360.0)
    out["tod_cos"] = np.cos(2 * np.pi * (mins - 600.0) / 360.0)
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
    if len(tr) < 200 or len(te) < 40:
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


def discovery_tercile_cuts(series: pd.Series) -> tuple[float, float]:
    q = series.dropna().quantile([1 / 3, 2 / 3])
    return float(q.iloc[0]), float(q.iloc[1])


def assign_tercile(x: pd.Series, lo: float, hi: float) -> pd.Series:
    out = pd.Series(np.full(len(x), np.nan), index=x.index, dtype=object)
    m = x.notna()
    out.loc[m & (x <= lo)] = "low"
    out.loc[m & (x > lo) & (x <= hi)] = "mid"
    out.loc[m & (x > hi)] = "high"
    return out


def load_panel() -> pd.DataFrame:
    if not PANEL_PATH.exists():
        raise FileNotFoundError(
            f"Need {PANEL_PATH} (run Phase 2 first)."
        )
    panel = pd.read_parquet(PANEL_PATH)
    panel["decision_ts"] = pd.to_datetime(panel["decision_ts"])
    if getattr(panel["decision_ts"].dt, "tz", None) is None:
        panel["decision_ts"] = panel["decision_ts"].dt.tz_localize("America/New_York")
    return add_tod(panel)


def disc_val_oos(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = panel[panel["split"].isin(["Discovery", "Validation"])]
    test = panel[panel["split"] == "OOS"]
    return train, test


def run_iv_regime(panel: pd.DataFrame) -> pd.DataFrame:
    """Probe 1: gamma concentration × IV ATM regime (Discovery terciles)."""
    disc = panel[panel["split"] == "Discovery"]
    lo, hi = discovery_tercile_cuts(disc["surf_iv_atm"])
    p = panel.copy()
    p["iv_regime"] = assign_tercile(p["surf_iv_atm"], lo, hi)
    rows = []
    train0, test0 = disc_val_oos(p)
    for inst in ("es", "nq"):
        for h in (15, 30, 60):
            ycol = f"{inst}_rv_{h}"
            base = base_cols_for(inst)
            for regime in ("low", "mid", "high"):
                train = train0[train0["iv_regime"] == regime]
                test = test0[test0["iv_regime"] == regime]
                ev = nested_eval(train, test, ycol, base, [ATM])
                rows.append(
                    {
                        "probe": "iv_regime",
                        "regime": regime,
                        "regime_cuts": f"{lo:.6g}|{hi:.6g}",
                        "instrument": inst,
                        "horizon_m": h,
                        **ev,
                    }
                )
            # continuous interaction on full sample: A + atm + atm*z(iv)
            for split_name, train, test in [
                ("DiscVal_OOS", train0, test0),
            ]:
                need = base + [ATM, ycol]
                tr = train.dropna(subset=need).copy()
                te = test.dropna(subset=need).copy()
                if len(tr) < 200 or len(te) < 40:
                    continue
                z_iv_mu = float(tr["surf_iv_atm"].mean())
                z_iv_sd = float(tr["surf_iv_atm"].std(ddof=0)) or 1.0
                tr = tr.copy()
                te = te.copy()
                tr["atm_x_ziv"] = tr[ATM] * (tr["surf_iv_atm"] - z_iv_mu) / z_iv_sd
                te["atm_x_ziv"] = te[ATM] * (te["surf_iv_atm"] - z_iv_mu) / z_iv_sd
                ev_main = nested_eval(tr, te, ycol, base, [ATM])
                ev_int = nested_eval(tr, te, ycol, base + [ATM], ["atm_x_ziv"])
                rows.append(
                    {
                        "probe": "iv_interaction",
                        "regime": "full",
                        "regime_cuts": split_name,
                        "instrument": inst,
                        "horizon_m": h,
                        "delta_r2_main": ev_main["delta_r2"],
                        "delta_r2_interaction_extra": ev_int["delta_r2"],
                        "n_train": ev_int["n_train"],
                        "n_test": ev_int["n_test"],
                        "r2_A": ev_main["r2_A"],
                        "r2_ext": ev_main["r2_ext"],
                        "delta_r2": ev_main["delta_r2"],
                    }
                )
    return pd.DataFrame(rows)


def run_vol_regime(panel: pd.DataFrame) -> pd.DataFrame:
    """Probe 2: gamma × expanding/prior realized-vol regime."""
    rows = []
    for inst in ("es", "nq"):
        prior = f"{inst}_prior_rv30"
        disc = panel[panel["split"] == "Discovery"]
        lo, hi = discovery_tercile_cuts(disc[prior])
        p = panel.copy()
        p["vol_regime"] = assign_tercile(p[prior], lo, hi)
        # expanding vs contracting: prior_rv vs abs prior return proxy via range
        p["expanding_vol"] = (p[prior] > p[prior].groupby(p["session_date"]).transform("median")).map(
            {True: "above_day_med", False: "below_day_med"}
        )
        train0, test0 = disc_val_oos(p)
        for h in (15, 30, 60):
            ycol = f"{inst}_rv_{h}"
            base = base_cols_for(inst)
            for regime in ("low", "mid", "high"):
                ev = nested_eval(
                    train0[train0["vol_regime"] == regime],
                    test0[test0["vol_regime"] == regime],
                    ycol,
                    base,
                    [ATM],
                )
                rows.append(
                    {
                        "probe": "prior_rv_tercile",
                        "regime": regime,
                        "regime_cuts": f"{lo:.6g}|{hi:.6g}",
                        "instrument": inst,
                        "horizon_m": h,
                        **ev,
                    }
                )
            for regime in ("above_day_med", "below_day_med"):
                ev = nested_eval(
                    train0[train0["expanding_vol"] == regime],
                    test0[test0["expanding_vol"] == regime],
                    ycol,
                    base,
                    [ATM],
                )
                rows.append(
                    {
                        "probe": "vs_day_median_prior_rv",
                        "regime": regime,
                        "regime_cuts": "within_session",
                        "instrument": inst,
                        "horizon_m": h,
                        **ev,
                    }
                )
    return pd.DataFrame(rows)


def run_surface_part(panel: pd.DataFrame) -> pd.DataFrame:
    """Probe 3: which part of the 0.98–1.02 surface carries the residual."""
    train, test = disc_val_oos(panel)
    rows = []
    for inst in ("es", "nq"):
        for h in (15, 30, 60):
            ycol = f"{inst}_rv_{h}"
            base = base_cols_for(inst)
            for name, cols in SURFACE_PART_PROBES.items():
                if any(c not in panel.columns for c in cols):
                    continue
                ev = nested_eval(train, test, ycol, base, cols)
                rows.append(
                    {
                        "probe": "surface_part",
                        "part": name,
                        "instrument": inst,
                        "horizon_m": h,
                        **ev,
                    }
                )
    return pd.DataFrame(rows)


def run_es_lead_nq(panel: pd.DataFrame) -> pd.DataFrame:
    """Probe 4: ES vol lead → NQ follow; gamma residual after ES RV control."""
    train, test = disc_val_oos(panel)
    rows = []
    # Lead-lag descriptives (Spearman) on Discovery only — no optimization
    disc = panel[panel["split"] == "Discovery"]
    for es_h in (5, 15, 30):
        for nq_h in (15, 30, 60):
            a = disc[f"es_rv_{es_h}"]
            b = disc[f"nq_rv_{nq_h}"]
            m = a.notna() & b.notna()
            rho = float(a[m].corr(b[m], method="spearman")) if m.sum() > 50 else float("nan")
            rows.append(
                {
                    "probe": "es_nq_spearman",
                    "es_horizon_m": es_h,
                    "nq_horizon_m": nq_h,
                    "spearman": rho,
                    "n": int(m.sum()),
                    "delta_r2": float("nan"),
                    "r2_A": float("nan"),
                    "r2_ext": float("nan"),
                    "n_train": 0,
                    "n_test": 0,
                }
            )

    for nq_h in (15, 30, 60):
        ycol = f"nq_rv_{nq_h}"
        base_nq = base_cols_for("nq")
        for es_h in (5, 15, 30):
            es_col = f"es_rv_{es_h}"
            # Does ES short-horizon RV help NQ beyond NQ baseline?
            ev_es = nested_eval(train, test, ycol, base_nq, [es_col])
            rows.append(
                {
                    "probe": "nq_given_es_rv",
                    "es_horizon_m": es_h,
                    "nq_horizon_m": nq_h,
                    "model": "A_nq + es_rv",
                    **ev_es,
                }
            )
            # Does ATM gamma still help NQ after ES RV is in the baseline?
            base_with_es = base_nq + [es_col]
            ev_g = nested_eval(train, test, ycol, base_with_es, [ATM])
            rows.append(
                {
                    "probe": "gamma_after_es_rv",
                    "es_horizon_m": es_h,
                    "nq_horizon_m": nq_h,
                    "model": "A_nq+es_rv + atm_share",
                    **ev_g,
                }
            )
            # Symmetric: gamma for ES after controlling NQ? (falsify one-way lead story)
            y_es = f"es_rv_{nq_h}"
            base_es = base_cols_for("es")
            nq_col = f"nq_rv_{es_h}"
            ev_sym = nested_eval(train, test, y_es, base_es + [nq_col], [ATM])
            rows.append(
                {
                    "probe": "gamma_es_after_nq_rv",
                    "es_horizon_m": nq_h,
                    "nq_horizon_m": es_h,
                    "model": "A_es+nq_rv + atm_share",
                    **ev_sym,
                }
            )
    return pd.DataFrame(rows)


def run_tod_decomp(panel: pd.DataFrame) -> pd.DataFrame:
    """Probe 5: time-of-day decomposition (per half-hour stamp)."""
    rows = []
    tods = sorted(panel["tod"].dropna().unique(), key=lambda t: tod_minutes(str(t)))
    train0, test0 = disc_val_oos(panel)
    for tod in tods:
        train = train0[train0["tod"] == tod]
        test = test0[test0["tod"] == tod]
        for inst in ("es", "nq"):
            for h in (30, 60):
                ycol = f"{inst}_rv_{h}"
                ev = nested_eval(train, test, ycol, base_cols_for(inst), [ATM])
                rows.append(
                    {
                        "probe": "tod",
                        "tod": str(tod),
                        "instrument": inst,
                        "horizon_m": h,
                        **ev,
                    }
                )
    return pd.DataFrame(rows)


def run_chrono_blocks(panel: pd.DataFrame) -> pd.DataFrame:
    """Probe 6: chronological block stability (fit earlier → score later block)."""
    rows = []
    for i, (name, years) in enumerate(CHRONO_BLOCKS):
        test = panel[panel["year"].isin(years)]
        if i == 0:
            # LOO-style: fit other discovery years
            train = panel[(panel["split"] == "Discovery") & (~panel["year"].isin(years))]
            proto = "loo_other_discovery"
        else:
            earlier_years = [y for b in CHRONO_BLOCKS[:i] for y in b[1]]
            train = panel[panel["year"].isin(earlier_years)]
            proto = "fit_earlier_blocks"
        for inst in ("es", "nq"):
            for h in (15, 30, 60):
                ycol = f"{inst}_rv_{h}"
                ev = nested_eval(train, test, ycol, base_cols_for(inst), [ATM])
                rows.append(
                    {
                        "probe": "chrono_block",
                        "block": name,
                        "protocol": proto,
                        "instrument": inst,
                        "horizon_m": h,
                        "years": ",".join(str(y) for y in years),
                        **ev,
                    }
                )
    return pd.DataFrame(rows)


def _scramble_within_bins(df: pd.DataFrame, col: str, bin_col: str) -> pd.Series:
    out = df[col].to_numpy(copy=True)
    bins = df[bin_col]
    for b in bins.dropna().unique():
        idx = np.where(bins.to_numpy() == b)[0]
        if len(idx) < 2:
            continue
        out[idx] = out[idx][RNG.permutation(len(idx))]
    return pd.Series(out, index=df.index)


def run_falsification(panel: pd.DataFrame) -> pd.DataFrame:
    """Probe 7: matched synthetic / randomized surfaces (mechanism falsification)."""
    rows = []
    train0, test0 = disc_val_oos(panel)
    disc = panel[panel["split"] == "Discovery"]
    iv_lo, iv_hi = discovery_tercile_cuts(disc["surf_iv_atm"])

    hows = [
        "identity",
        "permute_global",
        "permute_within_iv_tercile",
        "permute_within_tod",
        "gaussian_match_moments",
        "residual_permute",  # residualize atm on A features, permute residual
    ]

    for inst in ("es", "nq"):
        for h in (30, 60):
            ycol = f"{inst}_rv_{h}"
            base = base_cols_for(inst)
            for how in hows:
                train = train0.copy()
                test = test0.copy()
                if how == "identity":
                    pass
                elif how == "permute_global":
                    for d in (train, test):
                        d[ATM] = RNG.permutation(d[ATM].to_numpy())
                elif how == "permute_within_iv_tercile":
                    for d in (train, test):
                        d["iv_bin"] = assign_tercile(d["surf_iv_atm"], iv_lo, iv_hi)
                        d[ATM] = _scramble_within_bins(d, ATM, "iv_bin")
                elif how == "permute_within_tod":
                    for d in (train, test):
                        d[ATM] = _scramble_within_bins(d, ATM, "tod")
                elif how == "gaussian_match_moments":
                    for d in (train, test):
                        x = d[ATM].to_numpy(float)
                        m = np.isfinite(x)
                        mu = float(np.nanmean(x))
                        sd = float(np.nanstd(x)) or 1.0
                        syn = RNG.normal(mu, sd, size=len(d))
                        syn[~m] = np.nan
                        d[ATM] = syn
                elif how == "residual_permute":
                    # Fit atm ~ base on train; replace with fitted + permuted residual
                    need = base + [ATM]
                    tr = train.dropna(subset=need)
                    if len(tr) >= 200:
                        Xtr, mu, sd = standardize_fit(tr[base].to_numpy(float))
                        beta = fit_ols(tr[ATM].to_numpy(float), Xtr)
                        if beta is not None:
                            for d in (train, test):
                                dd = d.dropna(subset=need).copy()
                                if len(dd) < 10:
                                    d[ATM] = np.nan
                                    continue
                                X = standardize_apply(dd[base].to_numpy(float), mu, sd)
                                fitted = predict_ols(beta, X)
                                resid = dd[ATM].to_numpy(float) - fitted
                                resid_p = resid[RNG.permutation(len(resid))]
                                syn = pd.Series(np.nan, index=d.index, dtype=float)
                                syn.loc[dd.index] = fitted + resid_p
                                d[ATM] = syn
                else:
                    raise ValueError(how)

                ev = nested_eval(train, test, ycol, base, [ATM])
                rows.append(
                    {
                        "probe": "falsification",
                        "how": how,
                        "instrument": inst,
                        "horizon_m": h,
                        **ev,
                    }
                )
    return pd.DataFrame(rows)


def _safe_mean(xs: list[float]) -> float:
    arr = np.asarray(xs, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if len(arr) else float("nan")


def summarize(
    iv: pd.DataFrame,
    vol: pd.DataFrame,
    parts: pd.DataFrame,
    lead: pd.DataFrame,
    tod: pd.DataFrame,
    chrono: pd.DataFrame,
    fals: pd.DataFrame,
) -> tuple[str, dict]:
    lines = [
        "# Phase 3 — Stability / mechanism audit",
        "",
        "No threshold search. No trading rules. No Sharpe hunting.",
        "",
        "Question: why does residual ATM OI-gamma concentration relate to subsequent ES RV,",
        "and is that relationship coherent / stable enough to justify a trading-rule phase?",
        "",
        "## Classification context (Phase 2)",
        "",
        "**C — Research signal, not trading edge.** Small positive ES residual ΔR²; NQ transfer weak.",
        "",
    ]

    # 1 IV regime
    lines += ["## 1. Gamma × IV regime (DiscVal→OOS, atm_share)", ""]
    iv_reg = iv[iv["probe"] == "iv_regime"]
    if len(iv_reg):
        piv = iv_reg.pivot_table(
            index=["instrument", "horizon_m"],
            columns="regime",
            values="delta_r2",
            aggfunc="first",
        )
        lines.append("```")
        lines.append(piv.to_string())
        lines.append("```")
        lines.append("")
    iv_int = iv[iv["probe"] == "iv_interaction"]
    if len(iv_int):
        lines.append("Interaction extra ΔR² (atm × z(IV) after A+atm):")
        lines.append("```")
        lines.append(
            iv_int.pivot_table(
                index=["instrument", "horizon_m"],
                values="delta_r2_interaction_extra",
                aggfunc="first",
            ).to_string()
        )
        lines.append("```")
        lines.append("")

    # 2 vol regime
    lines += ["## 2. Gamma × prior-RV regime", ""]
    vol_t = vol[vol["probe"] == "prior_rv_tercile"]
    if len(vol_t):
        lines.append("```")
        lines.append(
            vol_t.pivot_table(
                index=["instrument", "horizon_m"],
                columns="regime",
                values="delta_r2",
                aggfunc="first",
            ).to_string()
        )
        lines.append("```")
        lines.append("")

    # 3 surface part
    lines += ["## 3. Surface-part probes (which slice of 0.98–1.02)", ""]
    if len(parts):
        lines.append("```")
        lines.append(
            parts.pivot_table(
                index=["instrument", "horizon_m"],
                columns="part",
                values="delta_r2",
                aggfunc="first",
            ).to_string()
        )
        lines.append("```")
        lines.append("")

    # 4 ES→NQ
    lines += ["## 4. ES lead → NQ response", ""]
    sp = lead[lead["probe"] == "es_nq_spearman"]
    if len(sp):
        lines.append("Discovery Spearman(es_rv, nq_rv):")
        lines.append("```")
        lines.append(
            sp.pivot_table(
                index="es_horizon_m", columns="nq_horizon_m", values="spearman", aggfunc="first"
            ).to_string()
        )
        lines.append("```")
        lines.append("")
    g_after = lead[lead["probe"] == "gamma_after_es_rv"]
    if len(g_after):
        lines.append("NQ RV: ΔR² of atm_share **after** A_nq + es_rv control:")
        lines.append("```")
        lines.append(
            g_after.pivot_table(
                index="nq_horizon_m", columns="es_horizon_m", values="delta_r2", aggfunc="first"
            ).to_string()
        )
        lines.append("```")
        lines.append("")
    g_es = lead[lead["probe"] == "gamma_es_after_nq_rv"]
    if len(g_es):
        lines.append("ES RV: ΔR² of atm_share after A_es + nq_rv (symmetry check):")
        lines.append("```")
        lines.append(
            g_es.pivot_table(
                index="es_horizon_m", columns="nq_horizon_m", values="delta_r2", aggfunc="first"
            ).to_string()
        )
        lines.append("```")
        lines.append("")

    # 5 TOD
    lines += ["## 5. Time-of-day decomposition (ES RV 30m)", ""]
    tod_es = tod[(tod["instrument"] == "es") & (tod["horizon_m"] == 30)]
    if len(tod_es):
        lines.append("```")
        lines.append(tod_es[["tod", "delta_r2", "n_train", "n_test"]].to_string(index=False))
        lines.append("```")
        lines.append("")

    # 6 chrono
    lines += ["## 6. Chronological blocks (atm_share ΔR²)", ""]
    if len(chrono):
        lines.append("```")
        lines.append(
            chrono.pivot_table(
                index=["instrument", "horizon_m"],
                columns="block",
                values="delta_r2",
                aggfunc="first",
            ).to_string()
        )
        lines.append("```")
        lines.append("")

    # 7 falsification
    lines += ["## 7. Mechanism falsification (matched scramble)", ""]
    fals_es = fals[(fals["instrument"] == "es") & (fals["horizon_m"] == 30)]
    if len(fals_es):
        lines.append("ES RV 30m:")
        lines.append("```")
        lines.append(fals_es[["how", "delta_r2", "r2_A", "r2_ext", "n_test"]].to_string(index=False))
        lines.append("```")
        lines.append("")
    fals_es60 = fals[(fals["instrument"] == "es") & (fals["horizon_m"] == 60)]
    if len(fals_es60):
        lines.append("ES RV 60m:")
        lines.append("```")
        lines.append(fals_es60[["how", "delta_r2", "r2_A", "r2_ext", "n_test"]].to_string(index=False))
        lines.append("```")
        lines.append("")

    # Verdict heuristics (frozen; not tuned)
    es30_iv = iv_reg[(iv_reg["instrument"] == "es") & (iv_reg["horizon_m"] == 30)]
    es30_vol = vol_t[(vol_t["instrument"] == "es") & (vol_t["horizon_m"] == 30)]
    es_parts = parts[(parts["instrument"] == "es") & (parts["horizon_m"] == 30)]
    es_chrono = chrono[(chrono["instrument"] == "es") & (chrono["horizon_m"] == 30)]
    tod_pos = tod_es["delta_r2"].to_numpy(float) if len(tod_es) else np.array([])

    id30 = float("nan")
    matched_nulls = []
    if len(fals_es):
        if (fals_es["how"] == "identity").any():
            id30 = float(fals_es.loc[fals_es["how"] == "identity", "delta_r2"].iloc[0])
        for how in ("permute_within_iv_tercile", "permute_within_tod", "residual_permute", "gaussian_match_moments"):
            sub = fals_es.loc[fals_es["how"] == how, "delta_r2"]
            if len(sub):
                matched_nulls.append(float(sub.iloc[0]))

    atm_vs_parts = {}
    if len(es_parts):
        for part in es_parts["part"].unique():
            atm_vs_parts[part] = float(es_parts.loc[es_parts["part"] == part, "delta_r2"].iloc[0])

    # Coherence checks
    iv_spread = float("nan")
    if len(es30_iv) >= 2:
        iv_spread = float(es30_iv["delta_r2"].max() - es30_iv["delta_r2"].min())
    vol_spread = float("nan")
    if len(es30_vol) >= 2:
        vol_spread = float(es30_vol["delta_r2"].max() - es30_vol["delta_r2"].min())

    chrono_vals = es_chrono["delta_r2"].to_numpy(float) if len(es_chrono) else np.array([])
    chrono_positive_frac = float(np.mean(chrono_vals > 0.002)) if len(chrono_vals) else float("nan")
    tod_positive_frac = float(np.mean(tod_pos > 0.002)) if len(tod_pos) else float("nan")

    beats_matched = (
        np.isfinite(id30)
        and len(matched_nulls) > 0
        and id30 > (_safe_mean(matched_nulls) + 0.004)
    )
    atm_is_peak = atm_vs_parts.get("atm_share", float("nan"))
    part_ok = np.isfinite(atm_is_peak) and atm_is_peak >= max(
        (v for k, v in atm_vs_parts.items() if k != "atm_share" and np.isfinite(v)),
        default=float("-inf"),
    )

    nq_after_es = g_after[(g_after["nq_horizon_m"] == 30)]["delta_r2"].to_numpy(float) if len(g_after) else np.array([])
    nq_residual = _safe_mean(list(nq_after_es)) if len(nq_after_es) else float("nan")

    coherent = (
        beats_matched
        and np.isfinite(chrono_positive_frac)
        and chrono_positive_frac >= 0.75
        and np.isfinite(tod_positive_frac)
        and tod_positive_frac >= 0.5
        and part_ok
        and np.isfinite(id30)
        and id30 > 0.005
    )
    unstable = (not beats_matched) or (
        np.isfinite(chrono_positive_frac) and chrono_positive_frac < 0.5
    ) or (np.isfinite(id30) and id30 < 0.003)

    if coherent:
        verdict = "COHERENT_MECHANISM"
        note = (
            "Residual ES ATM-share effect survives matched falsification, is not a single-stamp "
            "artifact, and is reasonably stable across chronological blocks. Trading-rule phase "
            "may be considered — still not validated as an edge."
        )
    elif unstable:
        verdict = "UNSTABLE_OR_SPURIOUS"
        note = (
            "Phase 3 does not support a coherent, stable mechanism for the residual ES effect. "
            "Archive Strategy 26 as a well-tested research hypothesis; do not open trading-rule search."
        )
    else:
        verdict = "MIXED_MECHANISM"
        note = (
            "Some conditional structure exists, but stability / falsification / transfer checks "
            "are mixed. Do not open trading-rule search; archive or narrow only with new data."
        )

    lines += [
        "## Verdict",
        "",
        f"**{verdict}** — {note}",
        "",
        "### Headline diagnostics",
        "",
        f"- ES RV30 identity ΔR²: `{id30:.6f}`",
        f"- Mean matched-null ΔR²: `{_safe_mean(matched_nulls):.6f}`",
        f"- Beats matched nulls: `{beats_matched}`",
        f"- IV-regime ΔR² spread (ES30): `{iv_spread:.6f}`",
        f"- Prior-RV regime ΔR² spread (ES30): `{vol_spread:.6f}`",
        f"- Chrono blocks frac(ΔR²>0.002) ES30: `{chrono_positive_frac}`",
        f"- TOD stamps frac(ΔR²>0.002) ES30: `{tod_positive_frac}`",
        f"- ATM share is strongest surface-part probe (ES30): `{part_ok}`",
        f"- Mean NQ30 ΔR² after ES-RV control: `{nq_residual:.6f}`",
        "",
        "## Artifacts",
        "",
        "- `phase3_iv_regime.csv`",
        "- `phase3_vol_regime.csv`",
        "- `phase3_surface_part.csv`",
        "- `phase3_es_lead_nq.csv`",
        "- `phase3_tod.csv`",
        "- `phase3_chrono_blocks.csv`",
        "- `phase3_falsification.csv`",
        "- `phase3_verdict.json`",
        "",
    ]

    payload = {
        "phase2_class": "C_research_signal_not_trading_edge",
        "verdict": verdict,
        "note": note,
        "es_rv30_identity_delta_r2": id30,
        "es_rv30_matched_null_mean_delta_r2": _safe_mean(matched_nulls),
        "beats_matched_nulls": beats_matched,
        "iv_regime_spread_es30": iv_spread,
        "vol_regime_spread_es30": vol_spread,
        "chrono_positive_frac_es30": chrono_positive_frac,
        "tod_positive_frac_es30": tod_positive_frac,
        "atm_strongest_part_es30": part_ok,
        "nq30_delta_r2_after_es_control_mean": nq_residual,
        "surface_part_delta_r2_es30": atm_vs_parts,
        "panel_years": "2016-2024 (no 2025-26 in Vilkov data_opt)",
        "rule": "No threshold search / no trading optimization",
    }
    return "\n".join(lines), payload


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    print("loading phase2 panel with prior state...", flush=True)
    panel = load_panel()

    print("1/7 IV regime...", flush=True)
    iv = run_iv_regime(panel)
    iv.to_csv(ART / "phase3_iv_regime.csv", index=False)

    print("2/7 vol regime...", flush=True)
    vol = run_vol_regime(panel)
    vol.to_csv(ART / "phase3_vol_regime.csv", index=False)

    print("3/7 surface part...", flush=True)
    parts = run_surface_part(panel)
    parts.to_csv(ART / "phase3_surface_part.csv", index=False)

    print("4/7 ES lead -> NQ...", flush=True)
    lead = run_es_lead_nq(panel)
    lead.to_csv(ART / "phase3_es_lead_nq.csv", index=False)

    print("5/7 TOD decomposition...", flush=True)
    tod = run_tod_decomp(panel)
    tod.to_csv(ART / "phase3_tod.csv", index=False)

    print("6/7 chronological blocks...", flush=True)
    chrono = run_chrono_blocks(panel)
    chrono.to_csv(ART / "phase3_chrono_blocks.csv", index=False)

    print("7/7 mechanism falsification...", flush=True)
    fals = run_falsification(panel)
    fals.to_csv(ART / "phase3_falsification.csv", index=False)

    report, verdict = summarize(iv, vol, parts, lead, tod, chrono, fals)
    (ART / "phase3_report.md").write_text(report, encoding="utf-8")
    (ART / "phase3_verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    (STRAT / "results" / "full_report.md").write_text(report, encoding="utf-8")
    (STRAT / "conclusion.md").write_text(
        "# Conclusion\n\n"
        f"**Phase 2 class: C — Research signal, not trading edge.**\n\n"
        f"**Phase 3: {verdict['verdict']}**\n\n"
        f"{verdict['note']}\n\n"
        f"Panel years: {verdict['panel_years']}\n\n"
        "See `artifacts/26_vilkov_0dte_surface/phase3_report.md`.\n",
        encoding="utf-8",
    )
    print(json.dumps(verdict, indent=2))
    print("DONE Phase 3", flush=True)


if __name__ == "__main__":
    main()
