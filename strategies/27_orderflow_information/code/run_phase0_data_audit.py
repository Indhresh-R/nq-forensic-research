"""
Strategy 27 Phase 0 — data audit + freeze definitions.

PROXY STUDY ONLY. Local series are OHLCV; there is no aggressor-signed order flow.
No thresholds, optimization, costs, or trading rules.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from common.nq_session import NY_OPEN, load_es, load_nq
from common.paths import ROOT
from common.splits import IS_YEARS, OOS_YEARS, VAL_YEARS

ART = ROOT / "artifacts" / "27_orderflow_information"
RTH_END = 16 * 60  # 16:00 ET exclusive end for last bar open 15:59
HORIZONS = (1, 5, 15, 30, 60)
DISC_YEARS = IS_YEARS  # 2010–2021


def split_of(year: int) -> str:
    if year in DISC_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def prepare(df: pd.DataFrame, name: str) -> pd.DataFrame:
    out = df.sort_values("ts").reset_index(drop=True).copy()
    out["instrument"] = name
    close = out["close"].to_numpy(np.float64)
    prev = np.roll(close, 1)
    prev[0] = np.nan
    # invalidate return across calendar gaps > 1 minute
    ts = out["ts"]
    dt_min = ts.diff().dt.total_seconds().to_numpy() / 60.0
    ret = close / prev - 1.0
    ret[0] = np.nan
    ret[~np.isfinite(dt_min) | (dt_min > 1.01) | (dt_min <= 0)] = np.nan
    out["ret_1m"] = ret
    out["absret_1m"] = np.abs(ret)
    rng = (out["high"].to_numpy(np.float64) - out["low"].to_numpy(np.float64)) / close
    rng[~np.isfinite(rng) | (close <= 0)] = np.nan
    out["range_pct"] = rng
    vol = out["volume"].to_numpy(np.float64)
    out["volume_f"] = vol
    # signed_vol_proxy: sign(close-to-close 1m return) * volume; 0 if ret==0; NaN if ret NaN
    sgn = np.sign(ret)
    sv = sgn * vol
    sv[~np.isfinite(ret)] = np.nan
    out["signed_vol_proxy"] = sv
    with np.errstate(divide="ignore", invalid="ignore"):
        out["ret_per_vol"] = np.where(vol > 0, ret / vol, np.nan)
        out["absret_per_vol"] = np.where(vol > 0, np.abs(ret) / vol, np.nan)
        out["range_per_vol"] = np.where(vol > 0, rng / vol, np.nan)
    out["vol_x_range"] = vol * rng
    dvol = np.diff(vol, prepend=np.nan)
    out["d_volume"] = dvol
    out["vol_accel"] = np.diff(dvol, prepend=np.nan)
    out["split"] = [split_of(int(y)) for y in out["year"].to_numpy()]
    return out


def rth_mask(ny_min: np.ndarray) -> np.ndarray:
    return (ny_min >= NY_OPEN) & (ny_min < RTH_END)


def spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    if n < 50:
        return float("nan"), n
    xr = pd.Series(x[m]).rank().to_numpy()
    yr = pd.Series(y[m]).rank().to_numpy()
    return float(np.corrcoef(xr, yr)[0, 1]), n


def ols_resid(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """y residual after projecting on columns of X (with intercept). NaNs dropped row-wise then remapped."""
    m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    resid = np.full(len(y), np.nan, dtype=np.float64)
    if m.sum() < 50:
        return resid
    yv = y[m]
    Xv = np.column_stack([np.ones(m.sum()), X[m]])
    beta, _, _, _ = np.linalg.lstsq(Xv, yv, rcond=None)
    resid[m] = yv - Xv @ beta
    return resid


def audit_series(raw_path: Path, prep: pd.DataFrame, name: str) -> dict:
    ts = prep["ts"]
    vol = prep["volume"].to_numpy()
    tab = pq.read_table(raw_path, columns=["ts_event", "symbol", "volume"])
    symbols = tab["symbol"].to_pandas()
    switches = int((symbols != symbols.shift(1)).sum())
    # RTH gap rate: fraction of RTH minutes where next bar is not +1m
    rth = prep[rth_mask(prep["ny_min"].to_numpy())].copy()
    rth_dt = rth["ts"].diff().dt.total_seconds().to_numpy() / 60.0
    gap_frac = float(np.mean((rth_dt > 1.01) & np.isfinite(rth_dt))) if len(rth_dt) else float("nan")
    roll_days = 0
    # approximate: symbol changes in raw aligned by position
    # use calendar date of symbol change
    sym_change = symbols != symbols.shift(1)
    roll_days = int(pd.to_datetime(tab["ts_event"].to_pandas(), utc=True).dt.tz_convert("America/New_York").dt.date[sym_change].nunique())

    return {
        "instrument": name,
        "path": str(raw_path),
        "n_rows": int(len(prep)),
        "ts_min": str(ts.iloc[0]),
        "ts_max": str(ts.iloc[-1]),
        "n_unique_symbols": int(symbols.nunique()),
        "n_symbol_switches": switches,
        "n_roll_calendar_days_approx": roll_days,
        "volume_min": float(np.min(vol)),
        "volume_median": float(np.median(vol)),
        "volume_p99": float(np.percentile(vol, 99)),
        "volume_max": float(np.max(vol)),
        "volume_eq_0_count": int((vol == 0).sum()),
        "volume_eq_0_pct": float((vol == 0).mean()),
        "rth_rows": int(len(rth)),
        "rth_gap_frac_gt_1m": gap_frac,
        "discovery_rows": int((prep["split"] == "Discovery").sum()),
        "validation_rows": int((prep["split"] == "Validation").sum()),
        "oos_rows": int((prep["split"] == "OOS").sum()),
    }


def proxy_vs_ohlcv_test(prep: pd.DataFrame) -> list[dict]:
    """Critical: is signed_vol_proxy just disguised return/range/vol?"""
    disc = prep[(prep["split"] == "Discovery") & rth_mask(prep["ny_min"].to_numpy())]
    rows = []
    sv = disc["signed_vol_proxy"].to_numpy(np.float64)
    pairs = [
        ("ret_1m", disc["ret_1m"].to_numpy(np.float64)),
        ("absret_1m", disc["absret_1m"].to_numpy(np.float64)),
        ("range_pct", disc["range_pct"].to_numpy(np.float64)),
        ("volume", disc["volume_f"].to_numpy(np.float64)),
        ("ret_per_vol", disc["ret_per_vol"].to_numpy(np.float64)),
        ("absret_per_vol", disc["absret_per_vol"].to_numpy(np.float64)),
        ("vol_x_range", disc["vol_x_range"].to_numpy(np.float64)),
    ]
    for name, arr in pairs:
        rho, n = spearman(sv, arr)
        rows.append({"proxy": "signed_vol_proxy", "vs": name, "spearman": rho, "n": n, "split": "Discovery", "window": "RTH"})

    # residual after return, abs return, range
    X = np.column_stack(
        [
            disc["ret_1m"].to_numpy(np.float64),
            disc["absret_1m"].to_numpy(np.float64),
            disc["range_pct"].to_numpy(np.float64),
        ]
    )
    resid = ols_resid(sv, X)
    for name, arr in [
        ("volume", disc["volume_f"].to_numpy(np.float64)),
        ("absret_1m", disc["absret_1m"].to_numpy(np.float64)),
        ("ret_1m", disc["ret_1m"].to_numpy(np.float64)),
    ]:
        rho, n = spearman(resid, arr)
        rows.append(
            {
                "proxy": "signed_vol_proxy_resid_ret_abs_range",
                "vs": name,
                "spearman": rho,
                "n": n,
                "split": "Discovery",
                "window": "RTH",
            }
        )
    # how much variance of |signed_vol| explained by |ret| * volume scale vs volume alone
    # R^2 of |sv| ~ |ret| and |sv| ~ volume
    y = np.abs(sv)
    for label, x in [("absret_1m", disc["absret_1m"].to_numpy(np.float64)), ("volume", disc["volume_f"].to_numpy(np.float64))]:
        m = np.isfinite(y) & np.isfinite(x)
        if m.sum() < 50:
            r2 = float("nan")
        else:
            Xv = np.column_stack([np.ones(m.sum()), x[m]])
            beta, _, _, _ = np.linalg.lstsq(Xv, y[m], rcond=None)
            pred = Xv @ beta
            ss_res = float(np.sum((y[m] - pred) ** 2))
            ss_tot = float(np.sum((y[m] - np.mean(y[m])) ** 2))
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        rows.append(
            {
                "proxy": "abs_signed_vol_proxy",
                "vs": f"ols_r2_on_{label}",
                "spearman": r2,
                "n": int(m.sum()),
                "split": "Discovery",
                "window": "RTH",
            }
        )
    return rows


def freeze_document() -> dict:
    return {
        "study_type": "PROXY_STUDY_NOT_ORDER_FLOW",
        "naming_ban": [
            "Do not write 'order flow predicts' for OHLCV-derived fields.",
            "Use signed_vol_proxy, vol_z_tod, etc.",
        ],
        "source": {
            "vendor": "Databento GLBX.MDP3 ohlcv-1m",
            "construction": (
                "Volume-based front-month continuous: per calendar date keep the single-contract "
                "symbol with maximum daily volume; drop spreads (symbols containing '-'); "
                "no back-adjustment of prices across rolls "
                "(see archive/legacy_scripts/build_continuous_data.py)."
            ),
            "es_path": "data/es_1m_continuous.parquet",
            "nq_path": "data/nq_1m_continuous.parquet",
            "columns": ["ts_event", "open", "high", "low", "close", "volume", "symbol"],
            "absent": [
                "buy_volume",
                "sell_volume",
                "aggressor_side",
                "trader_type",
                "bid",
                "ask",
                "depth",
            ],
        },
        "clocks": {
            "bar_open_ts": "ts_event (UTC) = start of 1-minute bucket",
            "timezone_session_logic": "America/New_York",
            "session_date_roll": "18:00 ET (SESSION_START=1080)",
            "rth_feature_window": "bar open ny_min in [09:30, 16:00)",
            "decision_T": (
                "End of completed bar with open=ts. Features use that bar's OHLCV and history "
                "with open < ts+1m. Outcomes use closes after this bar."
            ),
        },
        "volume_definition": (
            "Databento OHLCV-1m contract volume for the selected front-month symbol in that minute. "
            "Unsigned. Continuous series has volume_min=1 (no zeros observed in audit)."
        ),
        "missing_zero_handling": {
            "volume_eq_0": "If ever present: impact ratios NaN; signed_vol_proxy uses sign(ret)*0=0 when ret finite",
            "ret_across_gap": "ret_1m set NaN when prior bar gap > 1.01 minutes",
            "roll_days": "Symbol changes retained; returns across gaps NaN; document roll contamination risk",
            "no_price_ffill": True,
        },
        "contemporaneous_vs_lagged": {
            "features_at_T": "OHLCV of bar ending at T (includes same-bar ret_1m inside signed_vol_proxy)",
            "outcomes": "close[T+h]/close[T]-1 and path stats on (T, T+h] — excludes using future bars as features",
            "strict": "Do not use outcome-horizon returns as features",
        },
        "proxies_frozen": {
            "ret_1m": "close_t/close_{t-1}-1 if gap<=1m else NaN",
            "absret_1m": "|ret_1m|",
            "range_pct": "(high-low)/close",
            "volume": "unsigned 1m volume",
            "d_volume": "volume_t - volume_{t-1}",
            "vol_accel": "d_volume_t - d_volume_{t-1}",
            "vol_z_tod": (
                "(volume - Discovery mean volume at same ny_min) / Discovery std at same ny_min; "
                "RTH only; Discovery years only for moments; applied unchanged to Val/OOS"
            ),
            "signed_vol_proxy": "sign(ret_1m)*volume; sign(0)=0; NaN if ret_1m NaN. NOT aggressor flow.",
            "signed_vol_proxy_sum_5": "sum of signed_vol_proxy over bars t-4..t (same session, require 5 finite)",
            "signed_vol_proxy_resid": (
                "residual of signed_vol_proxy ~ ret_1m + absret_1m + range_pct with intercept; "
                "coefficients fit on Discovery RTH only; applied to all splits"
            ),
            "ret_per_vol": "ret_1m/volume if volume>0",
            "absret_per_vol": "|ret_1m|/volume if volume>0",
            "range_per_vol": "range_pct/volume if volume>0",
            "vol_x_range": "volume * range_pct",
            "es_nq_rel_ret_1m": "ES ret_1m - NQ ret_1m on aligned minute (secondary)",
        },
        "outcomes_frozen": {
            "horizons_minutes": list(HORIZONS),
            "ret_h": "close[t+h]/close[t]-1 if both bars exist and span is usable",
            "absret_h": "|ret_h|",
            "rv_h": "std of 1m returns on (t, t+h] * sqrt(n), require n>=3",
            "mfe_h": "max(high path)/close[t]-1 on bars with open in (t, t+h]",
            "mae_h": "min(low path)/close[t]-1 on bars with open in (t, t+h]",
        },
        "splits": {
            "Discovery": "2010–2021 (IS_YEARS)",
            "Validation": "2022–2024",
            "OOS": "2025–2026",
            "tercile_cuts": "Discovery RTH equal-frequency only; applied unchanged",
        },
        "hard_bans": [
            "no strategy thresholds",
            "no optimization",
            "no trading costs yet",
            "no rule construction",
            "no Delta-R2 until Phase 1 descriptives reviewed",
            "no calling proxies order flow",
        ],
    }


def write_report(meta: dict, audits: list[dict], collinearity: list[dict]) -> str:
    lines = [
        "# Strategy 27 — Phase 0 data audit",
        "",
        "## Classification",
        "",
        "**PROXY STUDY — NOT AN ORDER-FLOW STUDY.**",
        "",
        "Local ES/NQ continuous 1m bars are OHLCV only. Phase 1 measures OHLCV-derived "
        "**volume-pressure proxies**. Never report results as “order flow predicts …”.",
        "",
        "## Continuous series",
        "",
        meta["source"]["construction"],
        "",
        f"- Vendor: `{meta['source']['vendor']}`",
        f"- Absent fields: `{', '.join(meta['source']['absent'])}`",
        "",
        "## Series audit",
        "",
    ]
    for a in audits:
        lines += [
            f"### {a['instrument']}",
            "",
            f"- Rows: **{a['n_rows']:,}** | {a['ts_min']} -> {a['ts_max']}",
            f"- Symbols: {a['n_unique_symbols']} | switches: {a['n_symbol_switches']} | "
            f"approx roll calendar days: {a['n_roll_calendar_days_approx']}",
            f"- Volume min/median/p99/max: {a['volume_min']:.0f} / {a['volume_median']:.0f} / "
            f"{a['volume_p99']:.0f} / {a['volume_max']:.0f}",
            f"- Volume==0: {a['volume_eq_0_count']} ({100*a['volume_eq_0_pct']:.4f}%)",
            f"- RTH rows: {a['rth_rows']:,} | RTH gap>1m fraction: {a['rth_gap_frac_gt_1m']:.6f}",
            f"- Split rows Disc/Val/OOS: {a['discovery_rows']:,} / {a['validation_rows']:,} / {a['oos_rows']:,}",
            "",
        ]
    lines += [
        "## Critical collinearity test (Discovery RTH)",
        "",
        "Question: can `signed_vol_proxy` contain information beyond disguised return/range/vol?",
        "",
        "| Proxy | vs | Spearman or R² | n |",
        "|-------|----|----------------|---|",
    ]
    for r in collinearity:
        lines.append(
            f"| `{r['proxy']}` | `{r['vs']}` | {r['spearman']:.4f} | {r['n']:,} |"
        )
    # interpretation hook from numbers
    by = { (r["proxy"], r["vs"]): r["spearman"] for r in collinearity }
    sv_ret = by.get(("signed_vol_proxy", "ret_1m"), float("nan"))
    sv_vol = by.get(("signed_vol_proxy", "volume"), float("nan"))
    abs_r2_ret = by.get(("abs_signed_vol_proxy", "ols_r2_on_absret_1m"), float("nan"))
    abs_r2_vol = by.get(("abs_signed_vol_proxy", "ols_r2_on_volume"), float("nan"))
    lines += [
        "",
        "### Freeze interpretation",
        "",
        f"- Spearman(`signed_vol_proxy`, `ret_1m`) = **{sv_ret:.4f}** "
        "(mechanical co-movement with signed return is expected).",
        f"- Spearman(`signed_vol_proxy`, `volume`) = **{sv_vol:.4f}**.",
        f"- R²(|signed_vol_proxy| ~ |ret|) = **{abs_r2_ret:.4f}**; "
        f"R²(|signed_vol_proxy| ~ volume) = **{abs_r2_vol:.4f}**.",
        "",
        "Phase 1 **must** report `signed_vol_proxy_resid` (orthogonal to ret, |ret|, range) "
        "alongside the raw proxy. If only the raw proxy associates with outcomes and the residual does not, "
        "treat the proxy as a **relabeled OHLCV transform**, not volume-pressure information.",
        "",
        "## Frozen items",
        "",
        "- Clocks, continuous construction, volume definition, proxy formulas, outcomes, splits: "
        "see `phase0_freeze.json`.",
        "- Hard bans: no thresholds / optimization / costs / rules / delta-R2 until Phase 1 reviewed.",
        "",
        "## Gate",
        "",
        "**Phase 0 PASS — freeze locked. Proceed to Phase 1 descriptives only.**",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    freeze = freeze_document()
    (ART / "phase0_freeze.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")

    print("loading ES/NQ...", flush=True)
    es = prepare(load_es(), "ES")
    nq = prepare(load_nq(), "NQ")

    es_path = ROOT / "data" / "es_1m_continuous.parquet"
    nq_path = ROOT / "data" / "nq_1m_continuous.parquet"
    audits = [
        audit_series(es_path, es, "ES"),
        audit_series(nq_path, nq, "NQ"),
    ]
    (ART / "phase0_series_audit.json").write_text(json.dumps(audits, indent=2), encoding="utf-8")

    print("collinearity test ES Discovery RTH...", flush=True)
    coll_es = proxy_vs_ohlcv_test(es)
    for r in coll_es:
        r["instrument"] = "ES"
    print("collinearity test NQ Discovery RTH...", flush=True)
    coll_nq = proxy_vs_ohlcv_test(nq)
    for r in coll_nq:
        r["instrument"] = "NQ"
    coll = coll_es + coll_nq
    pd.DataFrame(coll).to_csv(ART / "phase0_proxy_vs_ohlcv.csv", index=False)

    report = write_report(freeze, audits, coll_es)
    (ART / "phase0_report.md").write_text(report, encoding="utf-8")
    print("Phase 0 PASS - freeze locked. See artifacts/27_orderflow_information/phase0_report.md", flush=True)
    print(f"wrote {ART}", flush=True)


if __name__ == "__main__":
    main()
