"""
SPX 0DTE dealer-gamma → ES/NQ intraday experiment.

Hostile / causal design:
- Discovery 2022–2023, Validation 2024, OOS 2025–2026 (chronological)
- Gamma lagged 1 minute (conservative: minute label treated as end-of-minute info)
- No threshold optimization on OOS; regimes frozen on Discovery only
- Multiple-testing Benjamini–Hochberg across pre-registered tests
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from common.nq_session import load_es, load_nq
from common.paths import ROOT, art

warnings.filterwarnings("ignore", category=FutureWarning)

FT_PARQUET = ROOT / "data" / "firmtape" / "processed" / "firmtape_minutes.parquet"
FT_SESS = ROOT / "data" / "firmtape" / "processed" / "firmtape_sessions.parquet"
ART_DIR = ROOT / "artifacts" / "25_spx_0dte_dealer_gamma"

DISC_YEARS = {2022, 2023}
VAL_YEARS = {2024}
OOS_YEARS = {2025, 2026}

RET_H = (1, 5, 10, 15, 30, 60)
RV_H = (5, 15, 30, 60)
MR_H = (5, 10, 15, 30)

# Predefined absolute distance-to-flip bins (fraction of spot); NOT optimized
FLIP_BINS = (-np.inf, -0.004, -0.0015, 0.0015, 0.004, np.inf)
FLIP_LABELS = ("far_below", "mod_below", "near", "mod_above", "far_above")

# Predefined TOD buckets (ny_min inclusive start)
TOD_EDGES = [
    (9 * 60 + 30, 9 * 60 + 35, "09:30-09:35"),
    (9 * 60 + 35, 9 * 60 + 45, "09:35-09:45"),
    (9 * 60 + 45, 10 * 60, "09:45-10:00"),
    (10 * 60, 10 * 60 + 30, "10:00-10:30"),
    (10 * 60 + 30, 11 * 60, "10:30-11:00"),
    (11 * 60, 12 * 60, "11:00-12:00"),
    (12 * 60, 14 * 60, "12:00-14:00"),
    (14 * 60, 15 * 60, "14:00-15:00"),
    (15 * 60, 15 * 60 + 30, "15:00-15:30"),
    (15 * 60 + 30, 16 * 60, "15:30-16:00"),
]

# Cost assumptions (one-way, points). ES=0.25pt tick; NQ=0.25pt tick.
# Round-trip used for expectancy: 2 * one_way.
COST_ES_ONEWAY = 0.25  # 1 tick round-ish friction proxy (conservative half)
COST_NQ_ONEWAY = 0.50


def bh_adjust(pvals: np.ndarray) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order]
    adj = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        val = ranked[i] * n / (i + 1)
        prev = min(prev, val)
        adj[order[i]] = min(prev, 1.0)
    return adj


def split_of(year: int) -> str:
    if year in DISC_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def tod_bucket(ny_min: np.ndarray) -> np.ndarray:
    out = np.array(["other"] * len(ny_min), dtype=object)
    for a, b, name in TOD_EDGES:
        out[(ny_min >= a) & (ny_min < b)] = name
    return out


def load_firmtape() -> pd.DataFrame:
    df = pd.read_parquet(FT_PARQUET)
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("America/New_York")
    df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
    return df


def prepare_underlying(df: pd.DataFrame, name: str, date_min=None, date_max=None) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values("ts").reset_index(drop=True)
    if "dow" not in out.columns:
        out["dow"] = out["ts"].dt.dayofweek.astype(np.int8)
    # Restrict early to save memory (FirmTape starts Apr 2022)
    if date_min is not None:
        out = out[out["ts"] >= pd.Timestamp(date_min, tz="America/New_York")].copy()
    if date_max is not None:
        out = out[out["ts"] <= pd.Timestamp(date_max, tz="America/New_York") + pd.Timedelta(days=1)].copy()
    # Keep RTH + a little pad for overnight features not required here
    rth_pad = (out["ny_min"] >= 9 * 60) & (out["ny_min"] < 16 * 60 + 5)
    out = out.loc[rth_pad].reset_index(drop=True)

    out["ret_1m"] = out["close"].pct_change()
    for h in RET_H:
        out[f"fwd_ret_{h}"] = out["close"].shift(-h) / out["close"] - 1.0
    r = out["ret_1m"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    n = len(r)
    for h in RV_H:
        rv = np.full(n, np.nan)
        eff = np.full(n, np.nan)
        if n > h + 1:
            # windows of ret[t+1 : t+1+h]
            windows = np.lib.stride_tricks.sliding_window_view(r[1:], h)  # len n-h
            # align to index t = 0 .. n-h-1
            m = windows.shape[0]
            with np.errstate(invalid="ignore"):
                rv[:m] = np.nanstd(windows, axis=1, ddof=1) * np.sqrt(h)
                path = np.nansum(np.abs(windows), axis=1)
                net = np.abs(close[h : h + m] / close[:m] - 1.0)
                eff[:m] = np.where(path > 0, net / path, np.nan)
        out[f"fwd_rv_{h}"] = rv
        out[f"fwd_eff_{h}"] = eff
    for h in (1, 5, 15):
        out[f"prev_ret_{h}"] = out["close"] / out["close"].shift(h) - 1.0
    out["prev_rv_15"] = out["ret_1m"].rolling(15, min_periods=8).std(ddof=1) * np.sqrt(15)
    rth = (out["ny_min"] >= 9 * 60 + 30) & (out["ny_min"] < 16 * 60)
    out["rth"] = rth
    tp = (out["high"] + out["low"] + out["close"]) / 3.0
    cum_pv = (tp * out["volume"]).where(rth).groupby(out["session_date"]).cumsum()
    cum_v = out["volume"].where(rth).groupby(out["session_date"]).cumsum()
    out["vwap"] = cum_pv / cum_v.replace(0, np.nan)
    out["dist_vwap"] = (out["close"] - out["vwap"]) / out["close"]
    or_mask = (out["ny_min"] >= 9 * 60 + 30) & (out["ny_min"] < 9 * 60 + 35)
    or_high = out["high"].where(or_mask).groupby(out["session_date"]).transform("max")
    or_low = out["low"].where(or_mask).groupby(out["session_date"]).transform("min")
    out["or_high"] = or_high
    out["or_low"] = or_low
    out["dist_or_mid"] = (out["close"] - 0.5 * (or_high + or_low)) / out["close"]
    out["instrument"] = name
    return out


def merge_panel(ft: pd.DataFrame, und: pd.DataFrame) -> pd.DataFrame:
    # Align on session_date + ny_min (minute label)
    u = und.copy()
    u["session_date"] = pd.to_datetime(u["session_date"]).dt.date
    cols_u = [
        "ts",
        "session_date",
        "ny_min",
        "year",
        "dow",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "rth",
        "ret_1m",
        "vwap",
        "dist_vwap",
        "dist_or_mid",
        "prev_ret_1",
        "prev_ret_5",
        "prev_ret_15",
        "prev_rv_15",
        "instrument",
    ]
    for h in RET_H:
        cols_u.append(f"fwd_ret_{h}")
    for h in RV_H:
        cols_u += [f"fwd_rv_{h}", f"fwd_eff_{h}"]
    u = u[[c for c in cols_u if c in u.columns]]

    f = ft.copy()
    # Conservative lag: gamma known at labeled minute M is usable only from M+1
    f = f.sort_values(["session_date", "ny_min"]).reset_index(drop=True)
    gcols = [
        "spot",
        "flip",
        "gpct",
        "ngv_meas",
        "ngv_conv",
        "ngv_vol",
        "charm",
        "dex",
        "vex",
        "vanna",
        "atmiv",
        "rvi15",
        "rvi30",
        "rvi60",
        "flowvel",
        "pos_gamma_peak",
        "neg_gamma_peak",
        "cr0",
        "ps0",
        "hold_lo",
        "hold_hi",
        "vwap",
    ]
    gcols = [c for c in gcols if c in f.columns]
    lagged = f.groupby("session_date", sort=False)[gcols].shift(1)
    lagged.columns = [f"g_{c}" for c in gcols]
    f2 = pd.concat(
        [
            f[["session_date", "ny_min", "year", "ts"]].rename(columns={"ts": "ft_ts", "year": "ft_year"}),
            lagged,
        ],
        axis=1,
    )
    # also keep contemporaneous (for leakage diagnostics only)
    for c in ("ngv_meas", "flip", "spot"):
        if c in f.columns:
            f2[f"raw_{c}"] = f[c].to_numpy()

    m = u.merge(f2, on=["session_date", "ny_min"], how="inner")
    m = m[m["rth"]].copy()
    m["split"] = m["year"].map(split_of)
    m["tod"] = tod_bucket(m["ny_min"].to_numpy())

    # Features from lagged gamma
    m["gamma"] = pd.to_numeric(m["g_ngv_meas"], errors="coerce")
    m["gamma_conv"] = pd.to_numeric(m["g_ngv_conv"], errors="coerce")
    m["gamma_vol"] = pd.to_numeric(m["g_ngv_vol"], errors="coerce")
    m["g_flip"] = pd.to_numeric(m["g_flip"], errors="coerce")
    m["g_spot"] = pd.to_numeric(m["g_spot"], errors="coerce")
    m["dist_flip"] = (m["g_spot"] - m["g_flip"]) / m["g_spot"]
    m["flip_bin"] = pd.cut(m["dist_flip"], bins=FLIP_BINS, labels=FLIP_LABELS)
    # flip cross using lagged spot path within day
    m["side_flip"] = np.sign(m["g_spot"] - m["g_flip"])
    m["side_flip_prev"] = m.groupby("session_date")["side_flip"].shift(1)
    m["cross_up"] = (m["side_flip_prev"] < 0) & (m["side_flip"] > 0)
    m["cross_dn"] = (m["side_flip_prev"] > 0) & (m["side_flip"] < 0)
    return m


def freeze_regimes(disc: pd.DataFrame) -> dict[str, Any]:
    """Predefine regime thresholds on Discovery only (quintiles of lagged measured gamma)."""
    g = disc["gamma"].dropna()
    # Absolute sign strength via Discovery quintiles
    qs = g.quantile([0.2, 0.4, 0.6, 0.8]).to_dict()
    # Normalized: gamma / (spot * atmiv proxy) if available; else rank within Discovery hist
    # Use rolling expanding percentile would leak future days within Discovery — OK for IS.
    # Freeze cutpoints as fixed Discovery quantiles applied OOS.
    g_norm = disc["gamma"] / disc["g_spot"].replace(0, np.nan)
    qn = g_norm.dropna().quantile([0.2, 0.4, 0.6, 0.8]).to_dict()
    # Also freeze |gamma| extremes for interaction tests
    abs_q = g.abs().quantile([0.5, 0.8, 0.9]).to_dict()
    return {
        "gamma_q": {str(k): float(v) for k, v in qs.items()},
        "gamma_norm_q": {str(k): float(v) for k, v in qn.items()},
        "abs_gamma_q": {str(k): float(v) for k, v in abs_q.items()},
        "n_disc": int(len(g)),
    }


def assign_regime(g: pd.Series, cuts: dict[str, float], prefix: str = "") -> pd.Series:
    q20, q40, q60, q80 = cuts["0.2"], cuts["0.4"], cuts["0.6"], cuts["0.8"]
    out = pd.Series(np.array(["C"] * len(g), dtype=object), index=g.index)
    out[g <= q20] = "E"  # strong negative
    out[(g > q20) & (g <= q40)] = "D"
    out[(g > q40) & (g <= q60)] = "C"
    out[(g > q60) & (g <= q80)] = "B"
    out[g > q80] = "A"  # strong positive
    out[g.isna()] = None
    return out


def _mean_ci(x: np.ndarray) -> tuple[float, float, float, float, int]:
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float("nan"), float("nan"), float("nan"), float("nan"), n
    m = float(np.mean(x))
    se = float(np.std(x, ddof=1) / np.sqrt(n))
    tcrit = float(stats.t.ppf(0.975, n - 1))
    return m, float(np.median(x)), m - tcrit * se, m + tcrit * se, n


def test_group_diff(a: np.ndarray, b: np.ndarray, name: str) -> dict[str, Any]:
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 30 or len(b) < 30:
        return {
            "test": name,
            "n_a": len(a),
            "n_b": len(b),
            "mean_a": float(np.mean(a)) if len(a) else None,
            "mean_b": float(np.mean(b)) if len(b) else None,
            "diff": None,
            "effect_cohen_d": None,
            "p_raw": None,
            "stat": None,
        }
    # Welch t
    stat, p = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    # Cohen's d (unequal n)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = np.sqrt((va + vb) / 2.0)
    d = (np.mean(a) - np.mean(b)) / pooled if pooled > 0 else np.nan
    return {
        "test": name,
        "n_a": int(len(a)),
        "n_b": int(len(b)),
        "mean_a": float(np.mean(a)),
        "mean_b": float(np.mean(b)),
        "diff": float(np.mean(a) - np.mean(b)),
        "effect_cohen_d": float(d),
        "p_raw": float(p),
        "stat": float(stat),
    }


def run_vol_hypothesis(panel: pd.DataFrame, split: str) -> list[dict]:
    """Pos gamma → lower fwd RV; Neg gamma → higher fwd RV."""
    d = panel[panel["split"] == split]
    pos = d[d["regime"].isin(["A", "B"])]
    neg = d[d["regime"].isin(["D", "E"])]
    rows = []
    for h in RV_H:
        col = f"fwd_rv_{h}"
        rows.append(test_group_diff(neg[col].to_numpy(), pos[col].to_numpy(), f"{split}|rv{h}|neg_vs_pos"))
        # strong only
        rows.append(
            test_group_diff(
                d.loc[d["regime"] == "E", col].to_numpy(),
                d.loc[d["regime"] == "A", col].to_numpy(),
                f"{split}|rv{h}|E_vs_A",
            )
        )
    return rows


def run_momentum_reversal(panel: pd.DataFrame, split: str) -> list[dict]:
    d = panel[panel["split"] == split].copy()
    rows = []
    for h in MR_H:
        prev = d[f"prev_ret_{5 if h >= 5 else 1}" if h != 5 else "prev_ret_5"]
        # standardize: always use matching lookback
        look = min(h, 15)
        if look == 1:
            prev = d["prev_ret_1"]
        elif look == 5:
            prev = d["prev_ret_5"]
        else:
            prev = d["prev_ret_15"] if look >= 15 else d["prev_ret_5"]
        fut = d[f"fwd_ret_{h}"]
        # classify previous move using Discovery-frozen? Use zero threshold (predefined)
        up = prev > 0
        dn = prev < 0
        for regime_set, label, expect_rev in [
            (d["regime"].isin(["A", "B"]), "pos", True),
            (d["regime"].isin(["D", "E"]), "neg", False),
        ]:
            # continuation = sign(prev)==sign(fut)
            mask = regime_set & (up | dn) & fut.notna() & prev.notna()
            if mask.sum() < 50:
                rows.append(
                    {
                        "test": f"{split}|mr{h}|{label}",
                        "n": int(mask.sum()),
                        "cont_rate": None,
                        "rev_rate": None,
                        "p_raw": None,
                    }
                )
                continue
            cont = np.sign(prev[mask]) == np.sign(fut[mask])
            cont = cont & (fut[mask] != 0)
            cont_rate = float(cont.mean())
            # binomial vs 0.5
            k = int(cont.sum())
            n = int(cont.notna().sum())
            p = float(stats.binomtest(k, n, 0.5, alternative="two-sided").pvalue)
            rows.append(
                {
                    "test": f"{split}|mr{h}|{label}",
                    "n": n,
                    "cont_rate": cont_rate,
                    "rev_rate": 1.0 - cont_rate,
                    "expect_reversal": expect_rev,
                    "aligned_with_theory": (cont_rate < 0.5) if expect_rev else (cont_rate > 0.5),
                    "p_raw": p,
                    "mean_fut_given_up": float(fut[mask & up].mean()) if (mask & up).sum() else None,
                    "mean_fut_given_dn": float(fut[mask & dn].mean()) if (mask & dn).sum() else None,
                }
            )
    return rows


def run_flip_cross(panel: pd.DataFrame, split: str) -> list[dict]:
    d = panel[panel["split"] == split]
    base = d[~d["cross_up"] & ~d["cross_dn"]]
    rows = []
    for direction, mask in [("cross_up", d["cross_up"]), ("cross_dn", d["cross_dn"])]:
        sub = d[mask]
        for h in (1, 5, 10, 15, 30):
            col = f"fwd_ret_{h}"
            rows.append(
                test_group_diff(sub[col].to_numpy(), base[col].to_numpy(), f"{split}|flip_{direction}|ret{h}_vs_base")
            )
            if h in RV_H:
                rows.append(
                    test_group_diff(
                        sub[f"fwd_rv_{h}"].to_numpy(),
                        base[f"fwd_rv_{h}"].to_numpy(),
                        f"{split}|flip_{direction}|rv{h}_vs_base",
                    )
                )
    return rows


def run_distance_bins(panel: pd.DataFrame, split: str) -> list[dict]:
    d = panel[panel["split"] == split]
    rows = []
    for h in (5, 15, 30):
        # ANOVA-like: compare near vs far |dist|
        near = d[d["flip_bin"] == "near"][f"fwd_rv_{h}"].to_numpy()
        far = d[d["flip_bin"].isin(["far_below", "far_above"])][f"fwd_rv_{h}"].to_numpy()
        rows.append(test_group_diff(near, far, f"{split}|dist|rv{h}|near_vs_far"))
        near_r = d[d["flip_bin"] == "near"][f"fwd_ret_{h}"].abs().to_numpy()
        far_r = d[d["flip_bin"].isin(["far_below", "far_above"])][f"fwd_ret_{h}"].abs().to_numpy()
        rows.append(test_group_diff(near_r, far_r, f"{split}|dist|absret{h}|near_vs_far"))
    return rows


def run_interactions(panel: pd.DataFrame, split: str, thr: dict) -> list[dict]:
    d = panel[panel["split"] == split].copy()
    abs80 = thr["abs_gamma_q"]["0.8"]
    d["g_ext"] = d["gamma"].abs() >= abs80
    d["near_flip"] = d["flip_bin"] == "near"
    d["vol_exp"] = d["prev_rv_15"] >= d.loc[d["split"] == split, "prev_rv_15"].median() if False else (
        d["prev_rv_15"] >= d["prev_rv_15"].median()
    )
    # Fix: use split-local median (OK — descriptive within split; not a frozen threshold for trading)
    med_rv = d["prev_rv_15"].median()
    d["vol_exp"] = d["prev_rv_15"] >= med_rv
    rows = []
    for h in (5, 15, 30):
        # extreme gamma × near flip vs other
        a = d[d["g_ext"] & d["near_flip"]][f"fwd_rv_{h}"].to_numpy()
        b = d[~(d["g_ext"] & d["near_flip"])][f"fwd_rv_{h}"].to_numpy()
        rows.append(test_group_diff(a, b, f"{split}|ix|rv{h}|ext_near_vs_rest"))
        a2 = d[d["g_ext"] & d["vol_exp"]][f"fwd_rv_{h}"].to_numpy()
        b2 = d[~(d["g_ext"] & d["vol_exp"])][f"fwd_rv_{h}"].to_numpy()
        rows.append(test_group_diff(a2, b2, f"{split}|ix|rv{h}|ext_volexp_vs_rest"))
        # signed: gamma * prev_ret predicting fut_ret (correlation)
        x = (d["gamma"] * d["prev_ret_5"]).to_numpy()
        y = d[f"fwd_ret_{h}"].to_numpy()
        msk = np.isfinite(x) & np.isfinite(y)
        if msk.sum() > 100:
            r, p = stats.pearsonr(x[msk], y[msk])
            rows.append(
                {
                    "test": f"{split}|ix|corr|g_x_prev5_vs_fwd{h}",
                    "n_a": int(msk.sum()),
                    "n_b": 0,
                    "mean_a": float(r),
                    "mean_b": 0.0,
                    "diff": float(r),
                    "effect_cohen_d": float(r),
                    "p_raw": float(p),
                    "stat": float(r),
                }
            )
    return rows


def run_tod(panel: pd.DataFrame, split: str) -> list[dict]:
    d = panel[panel["split"] == split]
    rows = []
    for tod, g in d.groupby("tod"):
        if tod == "other" or len(g) < 100:
            continue
        pos = g[g["regime"].isin(["A", "B"])]["fwd_rv_15"].to_numpy()
        neg = g[g["regime"].isin(["D", "E"])]["fwd_rv_15"].to_numpy()
        rows.append(test_group_diff(neg, pos, f"{split}|tod|{tod}|rv15_neg_vs_pos"))
    return rows


def run_book_compare(panel: pd.DataFrame, split: str, thr: dict) -> list[dict]:
    """Does measured / vol / conv gamma explain RV differently?"""
    d = panel[panel["split"] == split].copy()
    rows = []
    for col, label in [("gamma", "meas"), ("gamma_conv", "conv"), ("gamma_vol", "vol")]:
        if col not in d.columns or d[col].notna().sum() < 500:
            continue
        # use Discovery cuts only for meas; for others use split-local sign (predefined: sign)
        pos = d[d[col] > 0]["fwd_rv_15"].to_numpy()
        neg = d[d[col] < 0]["fwd_rv_15"].to_numpy()
        rows.append(test_group_diff(neg, pos, f"{split}|book|{label}|rv15_neg_vs_pos_sign"))
    return rows


def incremental_r2(panel: pd.DataFrame, split: str) -> dict[str, Any]:
    """Baseline price/vol/TOD vs +gamma features — OLS R^2 on fwd_ret_5 and fwd_rv_15."""
    d = panel[panel["split"] == split].dropna(subset=["fwd_ret_5", "fwd_rv_15", "prev_ret_1", "prev_ret_5", "prev_ret_15", "prev_rv_15"]).copy()
    if len(d) < 500:
        return {"split": split, "error": "insufficient"}
    # encode TOD as cyclic
    d["tod_sin"] = np.sin(2 * np.pi * (d["ny_min"] - 570) / 390)
    d["tod_cos"] = np.cos(2 * np.pi * (d["ny_min"] - 570) / 390)
    base_cols = [
        "prev_ret_1",
        "prev_ret_5",
        "prev_ret_15",
        "prev_rv_15",
        "dist_vwap",
        "dist_or_mid",
        "tod_sin",
        "tod_cos",
        "dow",
    ]
    gamma_cols = base_cols + [
        "gamma",
        "dist_flip",
        "gamma_x_rv",
        "gamma_x_prev",
    ]
    d["gamma_x_rv"] = d["gamma"] * d["prev_rv_15"]
    d["gamma_x_prev"] = d["gamma"] * d["prev_ret_5"]
    # regime dummies
    for r in ["A", "B", "C", "D", "E"]:
        d[f"reg_{r}"] = (d["regime"] == r).astype(float)
    gamma_cols = gamma_cols + [f"reg_{r}" for r in ["A", "B", "D", "E"]]  # C baseline

    def _r2(y: np.ndarray, X: np.ndarray) -> float:
        # add intercept
        X = np.column_stack([np.ones(len(X)), X])
        m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
        y, X = y[m], X[m]
        if len(y) < X.shape[1] + 50:
            return float("nan")
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        yhat = X @ beta
        ss_res = np.sum((y - yhat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        return float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

    out = {"split": split, "n": int(len(d))}
    for target in ["fwd_ret_5", "fwd_rv_15"]:
        y = d[target].to_numpy(float)
        Xb = d[base_cols].to_numpy(float)
        Xg = d[[c for c in gamma_cols if c in d.columns]].to_numpy(float)
        rb = _r2(y, Xb)
        rg = _r2(y, Xg)
        out[f"r2_base_{target}"] = rb
        out[f"r2_gamma_{target}"] = rg
        out[f"delta_r2_{target}"] = (rg - rb) if np.isfinite(rb) and np.isfinite(rg) else None
    return out


def hostile_tests(panel: pd.DataFrame, thr: dict) -> list[dict]:
    """Time-shift, shuffle, wrong-day placebos on Discovery."""
    d = panel[panel["split"] == "Discovery"].copy()
    rows = []
    # A. time-shift gamma
    for shift in (1, 5, 15, 30):
        # positive shift = use future gamma (should inflate if leakage)
        g = d.groupby("session_date")["gamma"].shift(-shift)  # future
        tmp = d.copy()
        tmp["gamma"] = g
        tmp["regime"] = assign_regime(tmp["gamma"], thr["gamma_q"])
        pos = tmp[tmp["regime"].isin(["A", "B"])]["fwd_rv_15"].to_numpy()
        neg = tmp[tmp["regime"].isin(["D", "E"])]["fwd_rv_15"].to_numpy()
        rows.append(test_group_diff(neg, pos, f"placebo|future_shift_{-shift}|rv15_neg_vs_pos"))
        g2 = d.groupby("session_date")["gamma"].shift(shift)  # further past
        tmp2 = d.copy()
        tmp2["gamma"] = g2
        tmp2["regime"] = assign_regime(tmp2["gamma"], thr["gamma_q"])
        pos = tmp2[tmp2["regime"].isin(["A", "B"])]["fwd_rv_15"].to_numpy()
        neg = tmp2[tmp2["regime"].isin(["D", "E"])]["fwd_rv_15"].to_numpy()
        rows.append(test_group_diff(neg, pos, f"placebo|past_shift_{shift}|rv15_neg_vs_pos"))

    # B. shuffle gamma within day
    rng = np.random.default_rng(42)
    tmp = d.copy()
    tmp["gamma"] = tmp.groupby("session_date")["gamma"].transform(
        lambda s: pd.Series(rng.permutation(s.to_numpy()), index=s.index)
    )
    tmp["regime"] = assign_regime(tmp["gamma"], thr["gamma_q"])
    rows.append(
        test_group_diff(
            tmp[tmp["regime"].isin(["D", "E"])]["fwd_rv_15"].to_numpy(),
            tmp[tmp["regime"].isin(["A", "B"])]["fwd_rv_15"].to_numpy(),
            "placebo|shuffle_within_day|rv15_neg_vs_pos",
        )
    )

    # C. wrong-day gamma
    days = tmp["session_date"].drop_duplicates().tolist()
    perm = {days[i]: days[(i + 17) % len(days)] for i in range(len(days))}
    # map gamma from other day by ny_min
    key = d.set_index(["session_date", "ny_min"])["gamma"]
    wrong = []
    for sd, nm, g in zip(d["session_date"], d["ny_min"], d["gamma"]):
        od = perm.get(sd)
        try:
            wrong.append(float(key.loc[(od, nm)]))
        except Exception:
            wrong.append(np.nan)
    tmp = d.copy()
    tmp["gamma"] = wrong
    tmp["regime"] = assign_regime(pd.Series(tmp["gamma"]), thr["gamma_q"])
    rows.append(
        test_group_diff(
            tmp[tmp["regime"].isin(["D", "E"])]["fwd_rv_15"].to_numpy(),
            tmp[tmp["regime"].isin(["A", "B"])]["fwd_rv_15"].to_numpy(),
            "placebo|wrong_day|rv15_neg_vs_pos",
        )
    )
    return rows


def economic_eval(panel: pd.DataFrame, split: str, instrument: str) -> list[dict]:
    """
    Simple non-optimized rules frozen a priori:
    1) Fade 5m move in strong positive gamma (A)
    2) Follow 5m move in strong negative gamma (E)
    Hold 5 minutes. Costs applied.
    """
    d = panel[(panel["split"] == split) & (panel["instrument"] == instrument)].copy()
    cost = COST_ES_ONEWAY * 2 if instrument == "ES" else COST_NQ_ONEWAY * 2
    # convert cost in points to return approx using price level
    px = d["close"].median()
    cost_ret = cost / px if px else np.nan
    rows = []
    for rule, mask, signal in [
        ("fade_A", d["regime"] == "A", -np.sign(d["prev_ret_5"])),
        ("follow_E", d["regime"] == "E", np.sign(d["prev_ret_5"])),
    ]:
        m = mask & (d["prev_ret_5"].abs() > 0) & d["fwd_ret_5"].notna()
        if m.sum() < 30:
            rows.append({"split": split, "instrument": instrument, "rule": rule, "n": int(m.sum())})
            continue
        sig = signal[m].to_numpy(dtype=float)
        ret = d.loc[m, "fwd_ret_5"].to_numpy(dtype=float)
        pnl = sig * ret
        # point pnl ≈ return * price level at decision
        move_pts = pnl * d.loc[m, "close"].to_numpy(dtype=float)
        hit = float((pnl > 0).mean())
        mean_r = float(np.nanmean(pnl))
        med_r = float(np.nanmedian(pnl))
        pos = pnl[pnl > 0]
        neg = pnl[pnl < 0]
        payoff = float(pos.mean() / abs(neg.mean())) if len(pos) and len(neg) else None
        rows.append(
            {
                "split": split,
                "instrument": instrument,
                "rule": rule,
                "n": int(m.sum()),
                "hit_rate": hit,
                "mean_ret": mean_r,
                "median_ret": med_r,
                "mean_pts": float(np.nanmean(move_pts)),
                "median_pts": float(np.nanmedian(move_pts)),
                "payoff_ratio": payoff,
                "cost_rt_pts": cost,
                "cost_rt_ret": float(cost_ret),
                "expectancy_ret_after_cost": mean_r - cost_ret,
                "expectancy_pts_after_cost": float(np.nanmean(move_pts) - cost),
                "turnover_per_day": float(m.sum() / max(d.loc[m, "session_date"].nunique(), 1)),
            }
        )
    return rows


def year_stability(panel: pd.DataFrame) -> list[dict]:
    rows = []
    for y, g in panel.groupby("year"):
        pos = g[g["regime"].isin(["A", "B"])]["fwd_rv_15"].to_numpy()
        neg = g[g["regime"].isin(["D", "E"])]["fwd_rv_15"].to_numpy()
        rows.append(test_group_diff(neg, pos, f"year|{y}|rv15_neg_vs_pos"))
    return rows


def data_audit(ft: pd.DataFrame, sess: pd.DataFrame, es: pd.DataFrame, nq: pd.DataFrame) -> dict[str, Any]:
    days = sorted(ft["session_date"].unique())
    # expected business days Apr 2022 onward rough
    all_days = pd.bdate_range(days[0], days[-1])
    missing = sorted(set(all_days.date) - set(days))
    # holiday-heavy — report count only
    freq = ft.groupby("session_date").size()
    dup = int(ft.duplicated(["session_date", "ny_min"]).sum())
    audit = {
        "firmtape_sessions": int(len(days)),
        "first_date": str(days[0]),
        "last_date": str(days[-1]),
        "n_observations": int(len(ft)),
        "minutes_per_session_median": float(freq.median()),
        "minutes_per_session_min": int(freq.min()),
        "minutes_per_session_max": int(freq.max()),
        "sessions_not_390": int((freq != 390).sum()),
        "duplicate_timestamps": dup,
        "timezone": "America/New_York",
        "calendar_bdays_in_span": int(len(all_days)),
        "missing_vs_bdays_count": int(len(missing)),
        "missing_vs_bdays_sample": [str(x) for x in missing[:20]],
        "es_range": [str(es["ts"].min()), str(es["ts"].max())],
        "nq_range": [str(nq["ts"].min()), str(nq["ts"].max())],
        "gamma_timing_interpretation": (
            "Minute label HH:MM treated as end-of-minute snapshot. "
            "Signals use gamma lagged by 1 minute (g[t-1] at bar t). "
            "Forward returns from close[t] to close[t+h]."
        ),
        "ga_backfill_note": (
            "Archive JSON may include ga_backfill metadata; conventional OI gamma "
            "may be reconstructed after the session. Primary tests use ngv_meas (tape-measured)."
        ),
        "underlying": "ES continuous 1m as S&P 500 proxy; NQ for transmission",
        "timestamp_convention_underlying": "Databento ts_event = bar open; OHLC within minute",
    }
    return audit


def write_report(audit: dict, results: dict, verdict: str, path: Path) -> None:
    lines = []
    lines.append("# SPX 0DTE Dealer Gamma → S&P 500 / NQ Experiment — Final Report\n")
    lines.append(f"**Verdict: `{verdict}`**\n")
    lines.append("Data sourced from FirmTape (https://firmtape.com/).\n")
    lines.append("## 1. Data audit\n")
    for k, v in audit.items():
        lines.append(f"- **{k}**: `{v}`")
    lines.append("\n## 2. Causal integrity\n")
    lines.append(results.get("causal_notes", ""))
    lines.append("\n## 3. Replication of known literature\n")
    lines.append(results.get("literature", ""))
    lines.append("\n## 4. Gamma flip\n")
    lines.append(results.get("flip", ""))
    lines.append("\n## 5. Incremental information\n")
    lines.append(results.get("incremental", ""))
    lines.append("\n## 6. NQ transmission\n")
    lines.append(results.get("nq", ""))
    lines.append("\n## 7. OOS results\n")
    lines.append(results.get("oos", ""))
    lines.append("\n## 8. Economic significance\n")
    lines.append(results.get("econ", ""))
    lines.append("\n## 9. Failure modes\n")
    lines.append(results.get("failures", ""))
    lines.append("\n## 10. Final verdict\n")
    lines.append(f"`{verdict}` — {results.get('verdict_text', '')}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize_theory(tests: pd.DataFrame, split: str) -> str:
    sub = tests[tests["test"].str.startswith(f"{split}|rv") & tests["test"].str.contains("neg_vs_pos|E_vs_A")]
    lines = [f"### {split}"]
    for _, r in sub.iterrows():
        lines.append(
            f"- `{r['test']}`: diff={r.get('diff')} d={r.get('effect_cohen_d')} "
            f"p={r.get('p_raw')} p_adj={r.get('p_adj')} n={r.get('n_a')}/{r.get('n_b')}"
        )
    mr = tests[tests["test"].str.startswith(f"{split}|mr")]
    for _, r in mr.iterrows():
        lines.append(
            f"- `{r['test']}`: cont={r.get('cont_rate')} rev={r.get('rev_rate')} "
            f"theory_ok={r.get('aligned_with_theory')} p={r.get('p_raw')} p_adj={r.get('p_adj')} n={r.get('n')}"
        )
    return "\n".join(lines) if len(lines) > 1 else f"### {split}\n(no rows)"


def decide_verdict(
    tests: pd.DataFrame,
    incr: list[dict],
    econ: pd.DataFrame,
    hostile: pd.DataFrame,
    n_sessions: int,
    years_present: set[int],
) -> tuple[str, str]:
    """Hostile-first verdict logic."""
    if n_sessions < 200 or not (DISC_YEARS & years_present) or not (VAL_YEARS & years_present):
        return (
            "E",
            "Invalid for confirmatory claim: FirmTape minute archive incomplete "
            f"(sessions={n_sessions}, years={sorted(years_present)}). "
            "Bulk snapshot download blocked by FirmTape visitor limit — see DATA_BLOCKER.md.",
        )
    # Core theory on OOS: neg RV > pos RV with p_adj < 0.05 and correct sign
    oos_rv = tests[
        tests["test"].str.startswith("OOS|rv")
        & tests["test"].str.contains("neg_vs_pos|E_vs_A")
        & tests["p_adj"].notna()
    ]
    theory_ok = False
    if len(oos_rv):
        good = oos_rv[(oos_rv["diff"] > 0) & (oos_rv["p_adj"] < 0.05)]
        theory_ok = len(good) >= 2

    # Placebos should be weaker / null
    sham = hostile[hostile["test"].str.contains("shuffle|wrong_day")]
    sham_sig = sham[(sham["p_raw"].notna()) & (sham["p_raw"] < 0.05)] if len(sham) else sham
    leakage = False
    fut = hostile[hostile["test"].str.contains("future_shift")]
    base = tests[tests["test"] == "Discovery|rv15|neg_vs_pos"]
    if len(fut) and len(base) and base.iloc[0]["p_raw"] is not None:
        # if future shift is stronger than contemporaneous lagged, suspicious
        if fut["p_raw"].min() is not None and base.iloc[0]["diff"] is not None:
            if fut["effect_cohen_d"].abs().max() > abs(base.iloc[0]["effect_cohen_d"] or 0) * 1.5:
                leakage = True

    incr_oos = next((x for x in incr if x.get("split") == "OOS"), {})
    delta = incr_oos.get("delta_r2_fwd_rv_15") or 0
    incr_ok = isinstance(delta, (int, float)) and delta > 0.005

    econ_oos = econ[(econ["split"] == "OOS") & (econ["expectancy_pts_after_cost"].notna())]
    econ_ok = bool(len(econ_oos) and (econ_oos["expectancy_pts_after_cost"] > 0).any())

    if leakage:
        return "E", "Future-gamma shifts look suspiciously strong vs lagged signal — possible leakage/timing ambiguity."
    if theory_ok and incr_ok and econ_ok:
        return "B", "OOS vol/regime relationship + incremental R² + post-cost expectancy on a frozen rule."
    if theory_ok and incr_ok and not econ_ok:
        return "C", "OOS statistical relationship and incremental info, but frozen rules fail after costs."
    if theory_ok and not incr_ok:
        return "C", "Some OOS regime-vol association, but little incremental power beyond price/vol/TOD."
    # Discovery-only curiosity
    disc = tests[tests["test"].str.startswith("Discovery|rv15|neg_vs_pos")]
    if len(disc) and disc.iloc[0].get("p_adj") is not None and disc.iloc[0]["p_adj"] < 0.05:
        return "D", "Discovery association does not survive as a robust OOS / incremental / economic edge."
    return "D", "No robust causal evidence that dealer-gamma regimes change tradable conditional distributions."


def main() -> None:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading FirmTape + underlyings...", flush=True)
    ft = load_firmtape()
    sess = pd.read_parquet(FT_SESS) if FT_SESS.exists() else pd.DataFrame()
    dmin = pd.Timestamp(str(ft["session_date"].min()))
    dmax = pd.Timestamp(str(ft["session_date"].max()))
    # pad a few days for prev returns
    es = prepare_underlying(
        load_es(),
        "ES",
        date_min=(dmin - pd.Timedelta(days=5)).strftime("%Y-%m-%d"),
        date_max=dmax.strftime("%Y-%m-%d"),
    )
    nq = prepare_underlying(
        load_nq(),
        "NQ",
        date_min=(dmin - pd.Timedelta(days=5)).strftime("%Y-%m-%d"),
        date_max=dmax.strftime("%Y-%m-%d"),
    )

    audit = data_audit(ft, sess, es, nq)
    (ART_DIR / "data_audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    print(json.dumps(audit, indent=2, default=str), flush=True)

    print("Building ES panel...", flush=True)
    es_p = merge_panel(ft, es)
    print("Building NQ panel...", flush=True)
    nq_p = merge_panel(ft, nq)

    thr = freeze_regimes(es_p[es_p["split"] == "Discovery"])
    (ART_DIR / "regime_thresholds_discovery.json").write_text(json.dumps(thr, indent=2), encoding="utf-8")

    for p in (es_p, nq_p):
        p["regime"] = assign_regime(p["gamma"], thr["gamma_q"])
        p["regime_norm"] = assign_regime(
            p["gamma"] / p["g_spot"].replace(0, np.nan), thr["gamma_norm_q"]
        )

    es_p.to_parquet(ART_DIR / "panel_es.parquet", index=False)
    nq_p.to_parquet(ART_DIR / "panel_nq.parquet", index=False)
    print(f"ES panel rows={len(es_p)} NQ panel rows={len(nq_p)}", flush=True)

    all_tests: list[dict] = []
    for split in ("Discovery", "Validation", "OOS"):
        print(f"Tests {split}...", flush=True)
        all_tests += run_vol_hypothesis(es_p, split)
        all_tests += run_momentum_reversal(es_p, split)
        all_tests += run_flip_cross(es_p, split)
        all_tests += run_distance_bins(es_p, split)
        all_tests += run_interactions(es_p, split, thr)
        all_tests += run_tod(es_p, split)
        all_tests += run_book_compare(es_p, split, thr)
        # NQ transmission
        all_tests += run_vol_hypothesis(nq_p.assign(instrument="NQ"), split)
        # tag nq tests
        for t in all_tests[::-1]:
            if t["test"].startswith(f"{split}|") and "nqtag" not in t:
                # only newly added unmarked — simpler: re-run dedicated
                break
        nq_vol = run_vol_hypothesis(nq_p, split)
        for t in nq_vol:
            t["test"] = t["test"].replace(f"{split}|", f"{split}|NQ|", 1)
        all_tests += nq_vol
        nq_mr = run_momentum_reversal(nq_p, split)
        for t in nq_mr:
            t["test"] = t["test"].replace(f"{split}|", f"{split}|NQ|", 1)
        all_tests += nq_mr

    all_tests += year_stability(es_p)
    print("Hostile placebos...", flush=True)
    hostile = hostile_tests(es_p, thr)
    all_tests += hostile

    tdf = pd.DataFrame(all_tests)
    # BH across tests with p_raw
    p = tdf["p_raw"].to_numpy(dtype=float)
    mask = np.isfinite(p)
    adj = np.full(len(tdf), np.nan)
    adj[mask] = bh_adjust(p[mask])
    tdf["p_adj"] = adj
    tdf.to_csv(ART_DIR / "all_tests.csv", index=False)

    incr = [incremental_r2(es_p, s) for s in ("Discovery", "Validation", "OOS")]
    incr += [incremental_r2(nq_p, s) | {"instrument": "NQ"} for s in ("Discovery", "Validation", "OOS")]
    (ART_DIR / "incremental_r2.json").write_text(json.dumps(incr, indent=2), encoding="utf-8")

    econ_rows = []
    for split in ("Discovery", "Validation", "OOS"):
        econ_rows += economic_eval(es_p.assign(instrument="ES"), split, "ES")
        econ_rows += economic_eval(nq_p.assign(instrument="NQ"), split, "NQ")
    edf = pd.DataFrame(econ_rows)
    edf.to_csv(ART_DIR / "economic_rules.csv", index=False)

    hdf = pd.DataFrame(hostile)
    if len(hdf) and "p_raw" in hdf.columns:
        # already in tdf
        pass

    # Descriptive regime table
    desc = []
    for split in ("Discovery", "Validation", "OOS"):
        d = es_p[es_p["split"] == split]
        for reg, g in d.groupby("regime"):
            row = {"split": split, "regime": reg, "n": len(g)}
            for h in RET_H:
                m, med, lo, hi, n = _mean_ci(g[f"fwd_ret_{h}"].to_numpy())
                row[f"ret{h}_mean"] = m
                row[f"ret{h}_n"] = n
            for h in RV_H:
                m, med, lo, hi, n = _mean_ci(g[f"fwd_rv_{h}"].to_numpy())
                row[f"rv{h}_mean"] = m
            desc.append(row)
    pd.DataFrame(desc).to_csv(ART_DIR / "regime_descriptives.csv", index=False)

    n_sessions = int(es_p["session_date"].nunique())
    years_present = set(int(y) for y in es_p["year"].dropna().unique())
    verdict, vtext = decide_verdict(tdf, incr, edf, pd.DataFrame(hostile), n_sessions, years_present)

    lit = "\n".join(summarize_theory(tdf, s) for s in ("Discovery", "Validation", "OOS"))
    flip_lines = tdf[tdf["test"].str.contains(r"\|flip_", regex=True)].head(40)
    flip_txt = flip_lines.to_string(index=False) if len(flip_lines) else "(none)"
    incr_txt = json.dumps(incr, indent=2)
    nq_txt = tdf[tdf["test"].str.contains(r"\|NQ\|", regex=True)].head(30).to_string(index=False)
    oos_txt = tdf[tdf["test"].str.startswith("OOS")].head(50).to_string(index=False)
    econ_txt = edf.to_string(index=False)
    fail_txt = (
        "- FirmTape measured gamma is a reconstruction, not exchange-verified dealer books.\n"
        "- Conventional OI gamma may include post-session backfill (`ga_backfill`).\n"
        "- ES futures ≠ SPX cash; basis and roll effects remain.\n"
        "- Minute timestamp semantics assumed end-of-minute; 1-minute lag is conservative but may blunt true effects.\n"
        "- Many correlated tests; BH controls FDR but not all dependence.\n"
        "- Economic rules are illustrative frozen heuristics, not optimized strategies.\n"
        "- Placebo battery:\n"
        + pd.DataFrame(hostile).to_string(index=False)
    )

    results_txt = {
        "causal_notes": (
            "Gamma features lagged by 1 minute within session. "
            "No same-minute gamma used for decisions. "
            "Forward outcomes use close[t]→close[t+h]. "
            f"Thresholds frozen on Discovery only: {json.dumps(thr)}"
        ),
        "literature": lit,
        "flip": flip_txt,
        "incremental": incr_txt,
        "nq": nq_txt,
        "oos": oos_txt,
        "econ": econ_txt,
        "failures": fail_txt,
        "verdict_text": vtext,
    }
    report_path = ART_DIR / "final_report.md"
    write_report(audit, results_txt, verdict, report_path)
    # also dossier results
    dossier = ROOT / "strategies" / "25_spx_0dte_dealer_gamma" / "results" / "full_report.md"
    dossier.write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")
    (ART_DIR / "verdict.json").write_text(
        json.dumps({"verdict": verdict, "text": vtext}, indent=2), encoding="utf-8"
    )
    print(f"VERDICT {verdict}: {vtext}", flush=True)
    print(f"Report: {report_path}", flush=True)


if __name__ == "__main__":
    main()
