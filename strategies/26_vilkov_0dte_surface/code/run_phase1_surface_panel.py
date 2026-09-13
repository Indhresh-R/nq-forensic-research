"""
Phase 1: freeze 30m SPXW surface features + join ES/NQ forward outcomes.

No threshold search. No trading rules.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common.nq_session import load_es, load_nq
from common.paths import ROOT

DATA = ROOT / "data" / "vilkov"
ART = ROOT / "artifacts" / "26_vilkov_0dte_surface"

FEATURE_TIMES = {
    "10:00:00",
    "10:30:00",
    "11:00:00",
    "11:30:00",
    "12:00:00",
    "12:30:00",
    "13:00:00",
    "13:30:00",
    "14:00:00",
    "14:30:00",
    "15:00:00",
    "15:30:00",
    "16:00:00",
}
HORIZONS = (5, 15, 30, 60, 120)
DISC_YEARS = set(range(2016, 2022))
VAL_YEARS = {2022, 2023}
OOS_YEARS = {2024}

ATM_LO, ATM_HI = 0.995, 1.005
NEAR_LO, NEAR_HI = 0.99, 1.01


def split_of(year: int) -> str:
    if year in DISC_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def _wavg(x: pd.Series, w: pd.Series) -> float:
    ww = w.to_numpy(dtype=float)
    xx = x.to_numpy(dtype=float)
    m = np.isfinite(xx) & np.isfinite(ww) & (ww > 0)
    if not m.any():
        m = np.isfinite(xx)
        if not m.any():
            return float("nan")
        return float(np.mean(xx[m]))
    return float(np.sum(xx[m] * ww[m]) / np.sum(ww[m]))


def aggregate_stamp(g: pd.DataFrame) -> dict:
    m = g["mnes_rel"].to_numpy(dtype=float)
    is_c = g["option_type"].to_numpy() == "C"
    is_p = g["option_type"].to_numpy() == "P"
    atm = (m >= ATM_LO) & (m <= ATM_HI)
    near = (m >= NEAR_LO) & (m <= NEAR_HI)
    otm_c = is_c & (m > 1.0)
    otm_p = is_p & (m < 1.0)

    oi_g = g["oi_gamma"].to_numpy(dtype=float)
    oi_ga = g["oi_gamma_abs"].to_numpy(dtype=float)
    oi_gu = g["oi_gamma_usd"].to_numpy(dtype=float)
    vol_g = g["trade_volume_gamma"].to_numpy(dtype=float)
    vol_gu = g["trade_volume_gamma_usd"].to_numpy(dtype=float)
    gamma = g["gamma"].to_numpy(dtype=float)
    iv = g["implied_volatility"].to_numpy(dtype=float)
    delta = g["delta"].to_numpy(dtype=float)
    vega = g["vega"].to_numpy(dtype=float)
    oi = g["open_interest"].to_numpy(dtype=float)
    vol = g["trade_volume"].to_numpy(dtype=float)
    spot = float(np.nanmedian(g["active_underlying_price"].to_numpy(dtype=float)))

    def _sum(mask: np.ndarray, arr: np.ndarray) -> float:
        if not mask.any():
            return float("nan")
        return float(np.nansum(arr[mask]))

    # gamma concentration / slope on moneyness using oi_gamma_abs weights
    w = np.where(np.isfinite(oi_ga) & (oi_ga > 0), oi_ga, np.nan)
    if np.isfinite(w).any():
        m_bar = float(np.nansum(m * np.nan_to_num(w)) / np.nansum(np.nan_to_num(w)))
        # slope: cov(m, oi_gamma) / var(m) simple
        mg = oi_g
        mm = m - np.nanmean(m)
        gg = mg - np.nanmean(mg)
        denom = np.nansum(mm * mm)
        slope = float(np.nansum(mm * gg) / denom) if denom > 0 else float("nan")
        # peak |oi_gamma| moneyness
        j = int(np.nanargmax(oi_ga)) if np.isfinite(oi_ga).any() else -1
        peak_m = float(m[j]) if j >= 0 else float("nan")
        peak_dist = peak_m - 1.0 if np.isfinite(peak_m) else float("nan")
    else:
        m_bar = slope = peak_m = peak_dist = float("nan")

    atm_share = _sum(atm, oi_ga) / _sum(np.ones(len(g), dtype=bool), oi_ga) if np.nansum(oi_ga) > 0 else float("nan")
    near_share = _sum(near, oi_ga) / np.nansum(oi_ga) if np.nansum(oi_ga) > 0 else float("nan")

    iv_call = _wavg(g.loc[is_c, "implied_volatility"], g.loc[is_c, "open_interest"])
    iv_put = _wavg(g.loc[is_p, "implied_volatility"], g.loc[is_p, "open_interest"])
    # skew proxy: OTM put IV - OTM call IV (mnes ~ 0.99 vs 1.01)
    put_wing = is_p & (m <= 0.99)
    call_wing = is_c & (m >= 1.01)
    iv_put_wing = float(np.nanmean(iv[put_wing])) if put_wing.any() else float("nan")
    iv_call_wing = float(np.nanmean(iv[call_wing])) if call_wing.any() else float("nan")

    return {
        "spot_opt": spot,
        "n_nodes": int(len(g)),
        "surf_oi_gamma_sum": float(np.nansum(oi_g)),
        "surf_oi_gamma_abs_sum": float(np.nansum(oi_ga)),
        "surf_oi_gamma_usd_sum": float(np.nansum(oi_gu)),
        "surf_oi_gamma_call": _sum(is_c, oi_g),
        "surf_oi_gamma_put": _sum(is_p, oi_g),
        "surf_oi_gamma_pc_asym": _sum(is_p, oi_g) - _sum(is_c, oi_g),
        "surf_oi_gamma_balance": float(np.nansum(oi_g) / (np.nansum(oi_ga) + 1.0)),
        "surf_atm_oi_gamma_abs_share": float(atm_share) if np.isfinite(atm_share) else float("nan"),
        "surf_near_oi_gamma_abs_share": float(near_share) if np.isfinite(near_share) else float("nan"),
        "surf_oi_gamma_m_centroid": m_bar,
        "surf_oi_gamma_m_slope": slope,
        "surf_peak_abs_oi_gamma_mnes": peak_m,
        "surf_peak_abs_oi_gamma_dist": peak_dist,
        "volg_gamma_sum": float(np.nansum(vol_g)),
        "volg_gamma_usd_sum": float(np.nansum(vol_gu)),
        "volg_gamma_balance": float(np.nansum(vol_g) / (np.nansum(np.abs(vol_g)) + 1.0)),
        "surf_gamma_sum": float(np.nansum(gamma)),
        "surf_delta_oi_sum": float(np.nansum(delta * np.nan_to_num(oi))),
        "surf_vega_oi_sum": float(np.nansum(vega * np.nan_to_num(oi))),
        "surf_iv_atm": float(np.nanmean(iv[atm])) if atm.any() else float("nan"),
        "surf_iv_call_oi": iv_call,
        "surf_iv_put_oi": iv_put,
        "surf_iv_skew_wing": iv_put_wing - iv_call_wing if np.isfinite(iv_put_wing) and np.isfinite(iv_call_wing) else float("nan"),
        "surf_oi_sum": float(np.nansum(oi)),
        "surf_volume_sum": float(np.nansum(vol)),
    }


def build_feature_panel() -> pd.DataFrame:
    cols = [
        "quote_date",
        "quote_time",
        "option_type",
        "mnes_rel",
        "oi_gamma",
        "oi_gamma_abs",
        "oi_gamma_usd",
        "trade_volume_gamma",
        "trade_volume_gamma_usd",
        "gamma",
        "delta",
        "vega",
        "implied_volatility",
        "open_interest",
        "trade_volume",
        "active_underlying_price",
    ]
    print("loading data_opt...", flush=True)
    raw = pd.read_parquet(DATA / "data_opt.parquet", columns=cols)
    raw["qt"] = raw["quote_time"].astype(str)
    raw = raw[raw["qt"].isin(FEATURE_TIMES)].copy()
    raw = raw[(raw["mnes_rel"] >= 0.98) & (raw["mnes_rel"] <= 1.02)].copy()
    raw["session_date"] = pd.to_datetime(raw["quote_date"], utc=True).dt.tz_convert("America/New_York").dt.date
    print(f"rows after clock/mnes filter: {len(raw)}", flush=True)

    print("aggregating stamps...", flush=True)
    grouped = raw.groupby(["session_date", "qt"], sort=True)
    rows = []
    for i, ((d, t), g) in enumerate(grouped):
        feat = aggregate_stamp(g)
        ts = pd.Timestamp(f"{d} {str(t)[:5]}:00").tz_localize("America/New_York")
        feat["decision_ts"] = ts
        feat["session_date"] = d
        feat["quote_time"] = str(t)[:5]
        feat["year"] = int(ts.year)
        feat["split"] = split_of(int(ts.year))
        feat["tod"] = str(t)[:5]
        rows.append(feat)
        if (i + 1) % 2000 == 0:
            print(f"stamps {i+1}", flush=True)

    feat = pd.DataFrame(rows).sort_values("decision_ts").reset_index(drop=True)
    # changes vs previous stamp (same session)
    key_cols = [
        "surf_oi_gamma_sum",
        "surf_oi_gamma_balance",
        "surf_atm_oi_gamma_abs_share",
        "surf_iv_atm",
        "surf_iv_skew_wing",
        "volg_gamma_sum",
        "spot_opt",
    ]
    for c in key_cols:
        prev = feat.groupby("session_date", sort=False)[c].shift(1)
        feat[f"d30_{c}"] = feat[c] - prev
    print(f"feature stamps: {len(feat)}", flush=True)
    return feat


def prepare_und(df: pd.DataFrame, name: str) -> pd.DataFrame:
    out = df.sort_values("ts").reset_index(drop=True)
    out["instrument"] = name
    return out[["ts", "open", "high", "low", "close", "volume", "session_date", "ny_min", "year"]]


def attach_outcomes(feat: pd.DataFrame, und: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Conservative join: px = close of last bar with open < T; path uses bars in [T, T+h)."""
    dec = pd.to_datetime(feat["decision_ts"], utc=False)
    # ensure timezone-aware ET then convert to UTC ns for searchsorted against und ts
    if dec.dt.tz is None:
        dec = dec.dt.tz_localize("America/New_York")
    dec_utc = dec.dt.tz_convert("UTC")
    u = und.copy()
    ts_u_utc = pd.to_datetime(u["ts"], utc=True)
    u["ts_utc"] = ts_u_utc
    u = u.sort_values("ts_utc").reset_index(drop=True)
    ts_u = u["ts_utc"].to_numpy(dtype="datetime64[ns]")
    close = u["close"].to_numpy(dtype=np.float64)
    high = u["high"].to_numpy(dtype=np.float64)
    low = u["low"].to_numpy(dtype=np.float64)
    ret1 = np.empty_like(close)
    ret1[0] = np.nan
    ret1[1:] = close[1:] / close[:-1] - 1.0

    dec_np = dec_utc.dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")
    ix = np.searchsorted(ts_u, dec_np, side="left")
    ix_px = ix - 1

    out = {}
    n = len(feat)
    px = np.full(n, np.nan)
    valid = (ix_px >= 0) & (ix_px < len(close))
    px[valid] = close[ix_px[valid]]
    out[f"{prefix}_px"] = px
    t_prior = dec_np - np.timedelta64(30, "m")
    ix_prior = np.searchsorted(ts_u, t_prior, side="left") - 1
    prev_px = np.full(n, np.nan)
    okp = (ix_prior >= 0) & (ix_prior < len(close)) & valid
    prev_px[okp] = close[ix_prior[okp]]
    out[f"{prefix}_ret_prior30"] = px / prev_px - 1.0

    for h in HORIZONS:
        t_end = dec_np + np.timedelta64(h, "m")
        ix_end = np.searchsorted(ts_u, t_end, side="left")
        ix_term = ix_end - 1
        term = np.full(n, np.nan)
        ok = valid & (ix_term >= 0) & (ix_term < len(close)) & (ix_term > ix_px)
        term[ok] = close[ix_term[ok]]
        ret = term / px - 1.0
        out[f"{prefix}_ret_{h}"] = ret
        out[f"{prefix}_absret_{h}"] = np.abs(ret)

        mfe = np.full(n, np.nan)
        mae = np.full(n, np.nan)
        rv = np.full(n, np.nan)
        for i in np.where(ok)[0]:
            a = int(ix[i])
            b = int(ix_end[i])
            if b <= a or not np.isfinite(px[i]):
                continue
            hh = high[a:b]
            ll = low[a:b]
            if len(hh) == 0:
                continue
            mfe[i] = (np.nanmax(hh) / px[i]) - 1.0
            mae[i] = (np.nanmin(ll) / px[i]) - 1.0
            rr = ret1[a:b]
            rr = rr[np.isfinite(rr)]
            if len(rr) >= 3:
                rv[i] = float(np.std(rr, ddof=1) * np.sqrt(len(rr)))
        out[f"{prefix}_mfe_{h}"] = mfe
        out[f"{prefix}_mae_{h}"] = mae
        out[f"{prefix}_rv_{h}"] = rv
        prior = out[f"{prefix}_ret_prior30"]
        out[f"{prefix}_cont_{h}"] = np.sign(prior) * np.sign(ret)

    return pd.concat([feat.reset_index(drop=True), pd.DataFrame(out)], axis=1)


def discovery_terciles(panel: pd.DataFrame, cols: list[str]) -> dict:
    disc = panel[panel["split"] == "Discovery"]
    cuts = {}
    for c in cols:
        s = disc[c].dropna()
        if len(s) < 100:
            continue
        q1, q2 = float(s.quantile(1 / 3)), float(s.quantile(2 / 3))
        cuts[c] = {"q33": q1, "q66": q2, "n": int(len(s))}
    return cuts


def assign_tercile(s: pd.Series, q33: float, q66: float) -> pd.Series:
    out = pd.Series(np.array(["mid"] * len(s), dtype=object), index=s.index)
    out[s <= q33] = "low"
    out[s > q66] = "high"
    out[s.isna()] = None
    return out


def conditional_tables(panel: pd.DataFrame, cuts: dict, feature_cols: list[str]) -> pd.DataFrame:
    rows = []
    for feat in feature_cols:
        if feat not in cuts:
            continue
        q33, q66 = cuts[feat]["q33"], cuts[feat]["q66"]
        panel = panel.copy()
        panel["_bin"] = assign_tercile(panel[feat], q33, q66)
        for split in ("Discovery", "Validation", "OOS"):
            d = panel[panel["split"] == split]
            for instrument in ("es", "nq"):
                for h in HORIZONS:
                    for b in ("low", "mid", "high"):
                        sub = d[d["_bin"] == b]
                        col = f"{instrument}_ret_{h}"
                        abscol = f"{instrument}_absret_{h}"
                        rvcol = f"{instrument}_rv_{h}"
                        if col not in sub.columns or len(sub) < 20:
                            continue
                        r = sub[col].to_numpy(dtype=float)
                        r = r[np.isfinite(r)]
                        a = sub[abscol].to_numpy(dtype=float)
                        a = a[np.isfinite(a)]
                        v = sub[rvcol].to_numpy(dtype=float) if rvcol in sub else np.array([])
                        v = v[np.isfinite(v)]
                        rows.append(
                            {
                                "feature": feat,
                                "split": split,
                                "instrument": instrument,
                                "horizon_m": h,
                                "tercile": b,
                                "n": int(len(r)),
                                "ret_mean": float(np.mean(r)) if len(r) else None,
                                "ret_median": float(np.median(r)) if len(r) else None,
                                "absret_mean": float(np.mean(a)) if len(a) else None,
                                "rv_mean": float(np.mean(v)) if len(v) else None,
                                "up_rate": float(np.mean(r > 0)) if len(r) else None,
                            }
                        )
    return pd.DataFrame(rows)


def corr_tables(panel: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    rows = []
    for split in ("Discovery", "Validation", "OOS"):
        d = panel[panel["split"] == split]
        for instrument in ("es", "nq"):
            for h in HORIZONS:
                for feat in feature_cols:
                    for target_suf, tname in [
                        (f"ret_{h}", "ret"),
                        (f"absret_{h}", "absret"),
                        (f"rv_{h}", "rv"),
                    ]:
                        ycol = f"{instrument}_{target_suf}"
                        if feat not in d.columns or ycol not in d.columns:
                            continue
                        x = d[feat].to_numpy(dtype=float)
                        y = d[ycol].to_numpy(dtype=float)
                        m = np.isfinite(x) & np.isfinite(y)
                        if m.sum() < 50:
                            continue
                        # Spearman via rank pearson
                        xr = pd.Series(x[m]).rank().to_numpy()
                        yr = pd.Series(y[m]).rank().to_numpy()
                        rho = float(np.corrcoef(xr, yr)[0, 1])
                        rows.append(
                            {
                                "split": split,
                                "instrument": instrument,
                                "horizon_m": h,
                                "feature": feat,
                                "target": tname,
                                "n": int(m.sum()),
                                "spearman": rho,
                            }
                        )
    return pd.DataFrame(rows)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    feat_path = ART / "surface_features_30m.parquet"
    if feat_path.exists():
        print(f"reusing {feat_path}", flush=True)
        feat = pd.read_parquet(feat_path)
        feat["decision_ts"] = pd.to_datetime(feat["decision_ts"])
        if getattr(feat["decision_ts"].dt, "tz", None) is None:
            feat["decision_ts"] = feat["decision_ts"].dt.tz_localize("America/New_York")
    else:
        feat = build_feature_panel()
        feat.to_parquet(feat_path, index=False)

    print("loading ES/NQ...", flush=True)
    es = prepare_und(load_es(), "ES")
    nq = prepare_und(load_nq(), "NQ")
    # restrict range
    t0, t1 = feat["decision_ts"].min() - pd.Timedelta(days=2), feat["decision_ts"].max() + pd.Timedelta(days=1)
    es = es[(es["ts"] >= t0) & (es["ts"] <= t1)].copy()
    nq = nq[(nq["ts"] >= t0) & (nq["ts"] <= t1)].copy()

    print("attach ES outcomes...", flush=True)
    panel = attach_outcomes(feat, es, "es")
    print("attach NQ outcomes...", flush=True)
    # attach_outcomes expects feat-like first arg; pass panel but only keep feat cols + nq outs
    feat_cols = list(feat.columns)
    nq_part = attach_outcomes(panel[feat_cols], nq, "nq")
    nq_new = [c for c in nq_part.columns if c.startswith("nq_")]
    panel = pd.concat([panel.reset_index(drop=True), nq_part[nq_new].reset_index(drop=True)], axis=1)

    panel.to_parquet(ART / "phase1_panel_es_nq.parquet", index=False)
    print(f"panel rows={len(panel)} cols={len(panel.columns)}", flush=True)

    feature_cols = [
        "surf_oi_gamma_sum",
        "surf_oi_gamma_balance",
        "surf_oi_gamma_pc_asym",
        "surf_atm_oi_gamma_abs_share",
        "surf_near_oi_gamma_abs_share",
        "surf_oi_gamma_m_slope",
        "surf_peak_abs_oi_gamma_dist",
        "volg_gamma_sum",
        "volg_gamma_balance",
        "surf_iv_atm",
        "surf_iv_skew_wing",
        "surf_delta_oi_sum",
        "surf_vega_oi_sum",
        "d30_surf_oi_gamma_sum",
        "d30_surf_oi_gamma_balance",
        "d30_surf_atm_oi_gamma_abs_share",
        "d30_surf_iv_atm",
        "d30_surf_iv_skew_wing",
        "d30_volg_gamma_sum",
    ]
    cuts = discovery_terciles(panel, feature_cols)
    (ART / "phase1_tercile_cuts_discovery.json").write_text(json.dumps(cuts, indent=2), encoding="utf-8")

    cond = conditional_tables(panel, cuts, feature_cols)
    cond.to_csv(ART / "phase1_conditional_terciles.csv", index=False)
    corr = corr_tables(panel, feature_cols)
    corr.to_csv(ART / "phase1_spearman_corr.csv", index=False)

    # short markdown summary: top |spearman| on Discovery absret/rv for NQ
    lines = [
        "# Phase 1 — Frozen surface features + raw conditionals",
        "",
        "No optimization. Terciles frozen on Discovery only.",
        "",
        f"- Feature stamps: `{len(feat)}`",
        f"- Panel rows: `{len(panel)}`",
        f"- Date range: `{feat['decision_ts'].min()}` → `{feat['decision_ts'].max()}`",
        f"- Splits: Discovery years {sorted(DISC_YEARS)[0]}-{sorted(DISC_YEARS)[-1]}, "
        f"Validation {sorted(VAL_YEARS)}, OOS {sorted(OOS_YEARS)}",
        "",
        "## Top |Spearman| (Discovery, NQ, absret/rv)",
    ]
    disc = corr[(corr["split"] == "Discovery") & (corr["instrument"] == "nq") & (corr["target"].isin(["absret", "rv"]))]
    if len(disc):
        disc = disc.assign(abs_rho=disc["spearman"].abs()).sort_values("abs_rho", ascending=False).head(25)
        lines.append(disc.to_string(index=False))
    lines += ["", "## Artifacts", "- `surface_features_30m.parquet`", "- `phase1_panel_es_nq.parquet`",
              "- `phase1_conditional_terciles.csv`", "- `phase1_spearman_corr.csv`",
              "- `phase1_tercile_cuts_discovery.json`"]
    (ART / "phase1_report.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "strategies" / "26_vilkov_0dte_surface" / "results" / "full_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("DONE Phase 1", flush=True)


if __name__ == "__main__":
    main()
