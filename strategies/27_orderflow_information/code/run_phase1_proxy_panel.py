"""
Strategy 27 Phase 1 — OHLCV volume-pressure PROXY panel + descriptives.

PROXY STUDY ONLY. No ΔR², thresholds, optimization, costs, or trading rules.
Requires Phase 0 freeze (artifacts/27_orderflow_information/phase0_freeze.json).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common.nq_session import NY_OPEN, load_es, load_nq
from common.paths import ROOT
from common.splits import IS_YEARS, OOS_YEARS, VAL_YEARS

ART = ROOT / "artifacts" / "27_orderflow_information"
RTH_END = 16 * 60
HORIZONS = (1, 5, 15, 30, 60)
DISC_YEARS = IS_YEARS

FEATURE_COLS = [
    "volume",
    "d_volume",
    "vol_accel",
    "vol_z_tod",
    "signed_vol_proxy",
    "signed_vol_proxy_sum_5",
    "signed_vol_proxy_resid",
    "ret_per_vol",
    "absret_per_vol",
    "range_per_vol",
    "vol_x_range",
    # baseline OHLCV transforms (for comparison — not "flow")
    "ret_1m",
    "absret_1m",
    "range_pct",
]


def split_of(year: int) -> str:
    if year in DISC_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def base_frame(df: pd.DataFrame, name: str) -> pd.DataFrame:
    out = df.sort_values("ts").reset_index(drop=True).copy()
    out["instrument"] = name
    close = out["close"].to_numpy(np.float64)
    prev = np.roll(close, 1)
    prev[0] = np.nan
    dt_min = out["ts"].diff().dt.total_seconds().to_numpy() / 60.0
    ret = close / prev - 1.0
    ret[0] = np.nan
    ret[~np.isfinite(dt_min) | (dt_min > 1.01) | (dt_min <= 0)] = np.nan
    out["ret_1m"] = ret
    out["absret_1m"] = np.abs(ret)
    rng = (out["high"].to_numpy(np.float64) - out["low"].to_numpy(np.float64)) / close
    rng[~np.isfinite(rng) | (close <= 0)] = np.nan
    out["range_pct"] = rng
    vol = out["volume"].to_numpy(np.float64)
    out["volume"] = vol
    sgn = np.sign(ret)
    sv = sgn * vol
    sv[~np.isfinite(ret)] = np.nan
    out["signed_vol_proxy"] = sv
    with np.errstate(divide="ignore", invalid="ignore"):
        out["ret_per_vol"] = np.where(vol > 0, ret / vol, np.nan)
        out["absret_per_vol"] = np.where(vol > 0, np.abs(ret) / vol, np.nan)
        out["range_per_vol"] = np.where(vol > 0, rng / vol, np.nan)
    out["vol_x_range"] = vol * rng
    dvol = np.empty_like(vol)
    dvol[0] = np.nan
    dvol[1:] = vol[1:] - vol[:-1]
    out["d_volume"] = dvol
    accel = np.empty_like(vol)
    accel[:2] = np.nan
    accel[2:] = dvol[2:] - dvol[1:-1]
    out["vol_accel"] = accel
    out["year"] = out["year"].astype(np.int16)
    out["split"] = [split_of(int(y)) for y in out["year"].to_numpy()]
    return out


def rth_only(df: pd.DataFrame) -> pd.DataFrame:
    m = (df["ny_min"].to_numpy() >= NY_OPEN) & (df["ny_min"].to_numpy() < RTH_END)
    return df.loc[m].copy()


def attach_tod_z(df: pd.DataFrame) -> dict:
    disc = df[df["split"] == "Discovery"]
    g = disc.groupby("ny_min", sort=True)["volume"]
    moments = g.agg(["mean", "std", "count"]).reset_index()
    moments = moments[moments["count"] >= 50]
    merged = df[["ny_min"]].merge(moments, on="ny_min", how="left")
    vol = df["volume"].to_numpy(np.float64)
    mu = merged["mean"].to_numpy(np.float64)
    sd = merged["std"].to_numpy(np.float64)
    z = (vol - mu) / sd
    z[~np.isfinite(z) | (sd <= 0)] = np.nan
    df["vol_z_tod"] = z
    return {
        "ny_min": moments["ny_min"].astype(int).tolist(),
        "mean": moments["mean"].astype(float).tolist(),
        "std": moments["std"].astype(float).tolist(),
    }


def attach_resid_and_sum5(df: pd.DataFrame) -> dict:
    disc = df[df["split"] == "Discovery"]
    y = disc["signed_vol_proxy"].to_numpy(np.float64)
    X = np.column_stack(
        [
            disc["ret_1m"].to_numpy(np.float64),
            disc["absret_1m"].to_numpy(np.float64),
            disc["range_pct"].to_numpy(np.float64),
        ]
    )
    m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    beta = np.full(4, np.nan)
    if m.sum() >= 100:
        Xv = np.column_stack([np.ones(m.sum()), X[m]])
        beta, _, _, _ = np.linalg.lstsq(Xv, y[m], rcond=None)
    y_all = df["signed_vol_proxy"].to_numpy(np.float64)
    X_all = np.column_stack(
        [
            np.ones(len(df)),
            df["ret_1m"].to_numpy(np.float64),
            df["absret_1m"].to_numpy(np.float64),
            df["range_pct"].to_numpy(np.float64),
        ]
    )
    resid = np.full(len(df), np.nan)
    ok = np.isfinite(y_all) & np.all(np.isfinite(X_all), axis=1) & np.all(np.isfinite(beta))
    resid[ok] = y_all[ok] - X_all[ok] @ beta
    df["signed_vol_proxy_resid"] = resid

    # sum of last 5 signed proxies within session_date
    sv = df["signed_vol_proxy"].to_numpy(np.float64)
    sess = df["session_date"].to_numpy()
    sum5 = np.full(len(df), np.nan)
    i = 0
    n = len(df)
    while i < n:
        j = i
        while j < n and sess[j] == sess[i]:
            j += 1
        # window [i, j)
        for k in range(i, j):
            a = k - 4
            if a < i:
                continue
            w = sv[a : k + 1]
            if np.isfinite(w).sum() == 5:
                sum5[k] = float(np.nansum(w))
        i = j
    df["signed_vol_proxy_sum_5"] = sum5
    return {
        "intercept": float(beta[0]) if np.isfinite(beta[0]) else None,
        "ret_1m": float(beta[1]) if np.isfinite(beta[1]) else None,
        "absret_1m": float(beta[2]) if np.isfinite(beta[2]) else None,
        "range_pct": float(beta[3]) if np.isfinite(beta[3]) else None,
        "n_fit": int(m.sum()),
    }


def attach_outcomes_session(df: pd.DataFrame, prefix: str = "") -> pd.DataFrame:
    """
    Per-session forward outcomes. Decision at bar t; ret_h = close[t+h]/close[t]-1.
    Requires exact h-minute clock span within the same session_date.
    """
    df = df.reset_index(drop=True)
    g = df.groupby("session_date", sort=False)
    close = df["close"]
    ts = df["ts"]
    parts: dict[str, pd.Series] = {}
    for h in HORIZONS:
        fwd_close = g["close"].shift(-h)
        fwd_ts = g["ts"].shift(-h)
        delta = (fwd_ts - ts).dt.total_seconds() / 60.0
        ok = delta.sub(float(h)).abs() <= 0.01
        ret = fwd_close / close - 1.0
        ret = ret.where(ok & close.gt(0))
        parts[f"{prefix}ret_{h}"] = ret
        parts[f"{prefix}absret_{h}"] = ret.abs()

        stack = [g["ret_1m"].shift(-k) for k in range(1, h + 1)]
        mat = pd.concat(stack, axis=1)
        cnt = mat.notna().sum(axis=1)
        rv = mat.std(axis=1, ddof=1) * np.sqrt(cnt.clip(lower=0))
        parts[f"{prefix}rv_{h}"] = rv.where(ok & (cnt >= 3))

    # MFE/MAE via compact per-session numpy (path highs/lows on t+1..t+h)
    n = len(df)
    high = df["high"].to_numpy(np.float64)
    low = df["low"].to_numpy(np.float64)
    close_a = df["close"].to_numpy(np.float64)
    ts_a = df["ts"].to_numpy()
    sess = df["session_date"].to_numpy()
    for h in HORIZONS:
        mfe = np.full(n, np.nan)
        mae = np.full(n, np.nan)
        i = 0
        while i < n:
            j = i
            while j < n and sess[j] == sess[i]:
                j += 1
            for k in range(i, j - h):
                delta_m = (ts_a[k + h] - ts_a[k]) / np.timedelta64(1, "m")
                if not np.isfinite(delta_m) or abs(float(delta_m) - h) > 0.01:
                    continue
                px = close_a[k]
                if not np.isfinite(px) or px <= 0:
                    continue
                hh = high[k + 1 : k + h + 1]
                ll = low[k + 1 : k + h + 1]
                mfe[k] = float(np.nanmax(hh) / px - 1.0)
                mae[k] = float(np.nanmin(ll) / px - 1.0)
            i = j
        parts[f"{prefix}mfe_{h}"] = mfe
        parts[f"{prefix}mae_{h}"] = mae

    return pd.concat([df, pd.DataFrame(parts)], axis=1)


def discovery_terciles(panel: pd.DataFrame, cols: list[str]) -> dict:
    disc = panel[panel["split"] == "Discovery"]
    cuts = {}
    for c in cols:
        s = disc[c].dropna()
        if len(s) < 500:
            continue
        cuts[c] = {
            "q33": float(s.quantile(1 / 3)),
            "q66": float(s.quantile(2 / 3)),
            "n": int(len(s)),
        }
    return cuts


def assign_tercile(s: pd.Series, q33: float, q66: float) -> pd.Series:
    out = pd.Series(np.array(["mid"] * len(s), dtype=object), index=s.index)
    out[s <= q33] = "low"
    out[s > q66] = "high"
    out[s.isna()] = None
    return out


def conditional_tables(panel: pd.DataFrame, cuts: dict) -> pd.DataFrame:
    rows = []
    p = panel
    for feat, cut in cuts.items():
        bins = assign_tercile(p[feat], cut["q33"], cut["q66"])
        for split in ("Discovery", "Validation", "OOS"):
            d = p[p["split"] == split]
            b = bins.loc[d.index]
            for h in HORIZONS:
                col = f"ret_{h}"
                abscol = f"absret_{h}"
                rvcol = f"rv_{h}"
                for lab in ("low", "mid", "high"):
                    sub = d[b == lab]
                    r = sub[col].to_numpy(dtype=float)
                    r = r[np.isfinite(r)]
                    a = sub[abscol].to_numpy(dtype=float)
                    a = a[np.isfinite(a)]
                    v = sub[rvcol].to_numpy(dtype=float)
                    v = v[np.isfinite(v)]
                    if len(r) < 50:
                        continue
                    rows.append(
                        {
                            "feature": feat,
                            "split": split,
                            "horizon_m": h,
                            "tercile": lab,
                            "n": int(len(r)),
                            "ret_mean": float(np.mean(r)),
                            "ret_median": float(np.median(r)),
                            "absret_mean": float(np.mean(a)) if len(a) else None,
                            "rv_mean": float(np.mean(v)) if len(v) else None,
                            "up_rate": float(np.mean(r > 0)),
                        }
                    )
    return pd.DataFrame(rows)


def corr_tables(panel: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for split in ("Discovery", "Validation", "OOS"):
        d = panel[panel["split"] == split]
        for h in HORIZONS:
            for feat in cols:
                for target, tname in [
                    (f"ret_{h}", "ret"),
                    (f"absret_{h}", "absret"),
                    (f"rv_{h}", "rv"),
                ]:
                    x = d[feat].to_numpy(dtype=float)
                    y = d[target].to_numpy(dtype=float)
                    m = np.isfinite(x) & np.isfinite(y)
                    if m.sum() < 200:
                        continue
                    xr = pd.Series(x[m]).rank().to_numpy()
                    yr = pd.Series(y[m]).rank().to_numpy()
                    rho = float(np.corrcoef(xr, yr)[0, 1])
                    rows.append(
                        {
                            "split": split,
                            "horizon_m": h,
                            "feature": feat,
                            "target": tname,
                            "n": int(m.sum()),
                            "spearman": rho,
                        }
                    )
    return pd.DataFrame(rows)


def write_phase1_report(
    instrument: str,
    n_rows: int,
    beta: dict,
    corr: pd.DataFrame,
    cond: pd.DataFrame,
) -> str:
    lines = [
        f"# Strategy 27 — Phase 1 descriptives ({instrument})",
        "",
        "**PROXY STUDY - NOT ORDER FLOW.** No delta-R2. No rules.",
        "",
        f"- Panel rows (RTH): **{n_rows:,}**",
        f"- Residual OLS (Discovery): {json.dumps(beta)}",
        "",
        "## Headline Spearman (Validation + OOS emphasis)",
        "",
        "Compare `signed_vol_proxy` vs `signed_vol_proxy_resid` vs raw `ret_1m` / `volume`.",
        "",
    ]
    focus_feats = [
        "signed_vol_proxy",
        "signed_vol_proxy_resid",
        "signed_vol_proxy_sum_5",
        "volume",
        "vol_z_tod",
        "ret_1m",
        "absret_1m",
        "vol_x_range",
        "absret_per_vol",
    ]
    sub = corr[corr["feature"].isin(focus_feats) & (corr["horizon_m"].isin([5, 15, 30]))]
    lines += [
        "| Split | H | Feature | Target | Spearman | n |",
        "|-------|---|---------|--------|----------|---|",
    ]
    for _, r in sub.sort_values(["split", "horizon_m", "target", "feature"]).iterrows():
        lines.append(
            f"| {r['split']} | {int(r['horizon_m'])} | `{r['feature']}` | {r['target']} | "
            f"{r['spearman']:.4f} | {int(r['n']):,} |"
        )

    # key contrast table: ret_15 association
    lines += ["", "## Proxy vs disguised-return check (target=ret, H=15)", ""]
    for split in ("Discovery", "Validation", "OOS"):
        lines.append(f"### {split}")
        lines.append("")
        for feat in ["ret_1m", "signed_vol_proxy", "signed_vol_proxy_resid", "volume", "vol_z_tod"]:
            row = corr[(corr["split"] == split) & (corr["feature"] == feat) & (corr["horizon_m"] == 15) & (corr["target"] == "ret")]
            if len(row):
                lines.append(f"- `{feat}`: Spearman={float(row.iloc[0]['spearman']):.4f} (n={int(row.iloc[0]['n']):,})")
        lines.append("")

    lines += [
        "## Interpretation gate (descriptive only)",
        "",
        "- If `signed_vol_proxy` tracks future returns similarly to `ret_1m`, and "
        "`signed_vol_proxy_resid` collapses toward ~0 association, the proxy is largely a "
        "**relabeled return transform** — do not call it order-flow information.",
        "- Unsigned `volume` / `vol_z_tod` associations with future `|ret|`/`rv` are activity/vol state, "
        "not signed pressure.",
        "- Phase 2 delta-R2 only if residuals or unsigned activity show non-trivial, stable descriptive signal "
        "beyond raw return/range.",
        "",
        f"Artifacts: `phase1_panel_{instrument.lower()}.parquet`, `phase1_spearman_{instrument.lower()}.csv`, "
        f"`phase1_conditional_terciles_{instrument.lower()}.csv`.",
        "",
    ]
    _ = cond  # available for later expansion
    return "\n".join(lines)


def build_instrument(name: str, loader) -> None:
    print(f"=== Phase 1 {name} ===", flush=True)
    df = rth_only(base_frame(loader(), name))
    print(f"RTH rows {len(df):,}", flush=True)
    tod_moments = attach_tod_z(df)
    beta = attach_resid_and_sum5(df)
    print("attaching outcomes (per session)...", flush=True)
    panel = attach_outcomes_session(df)
    out_path = ART / f"phase1_panel_{name.lower()}.parquet"
    # drop bulky unused object cols if any
    panel.to_parquet(out_path, index=False)
    print(f"wrote {out_path} cols={len(panel.columns)}", flush=True)

    cuts = discovery_terciles(panel, FEATURE_COLS)
    (ART / f"phase1_tercile_cuts_discovery_{name.lower()}.json").write_text(json.dumps(cuts, indent=2), encoding="utf-8")
    (ART / f"phase1_tod_volume_moments_{name.lower()}.json").write_text(json.dumps(tod_moments), encoding="utf-8")
    (ART / f"phase1_resid_ols_discovery_{name.lower()}.json").write_text(json.dumps(beta, indent=2), encoding="utf-8")

    print("spearman...", flush=True)
    corr = corr_tables(panel, FEATURE_COLS)
    corr.to_csv(ART / f"phase1_spearman_{name.lower()}.csv", index=False)
    print("terciles...", flush=True)
    cond = conditional_tables(panel, cuts)
    cond.to_csv(ART / f"phase1_conditional_terciles_{name.lower()}.csv", index=False)

    report = write_phase1_report(name, len(panel), beta, corr, cond)
    (ART / f"phase1_report_{name.lower()}.md").write_text(report, encoding="utf-8")
    # also write combined pointer
    print(report.encode("ascii", errors="replace").decode("ascii")[:2500], flush=True)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    freeze_path = ART / "phase0_freeze.json"
    if not freeze_path.exists():
        raise SystemExit("Phase 0 freeze missing — run run_phase0_data_audit.py first")
    # ES first (priority), then NQ
    build_instrument("ES", load_es)
    build_instrument("NQ", load_nq)
    summary = [
        "# Strategy 27 — Phase 1 summary",
        "",
        "**PROXY STUDY.** See `phase1_report_es.md` and `phase1_report_nq.md`.",
        "",
        "No delta-R2 in this phase.",
        "",
    ]
    (ART / "phase1_report.md").write_text("\n".join(summary), encoding="utf-8")
    print("Phase 1 complete", flush=True)


if __name__ == "__main__":
    main()
