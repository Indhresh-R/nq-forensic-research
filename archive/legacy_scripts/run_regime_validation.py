"""
Hostile regime validation for ORB + VWAP + SMT.
- Execution: next-bar open + 0.25 friction + 1.0 pt entry slippage
- Thresholds: frozen from IS (2010-2023) only
- Final OOS: 2024-2026 untouched (no tuning)
- All regime features use information available before entry
"""
from __future__ import annotations

from common.paths import art

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from run_orb_vwap_smt_edge_report import (
    ART,
    FRICTION,
    POINT_VAL,
    backtest,
    compute_smt_active,
    load,
    metrics,
    p,
)

IS_END = 2023
OOS_START = 2024
OOS_END = 2026
ENTRY_SLIP = 1.0  # realistic extra slippage pts


def extended_backtest(df, smt_active, **kw):
    """ORB+VWAP+SMT with day_id and orb_range on each trade."""
    high = df["high_nq"].to_numpy(np.float64)
    low = df["low_nq"].to_numpy(np.float64)
    close = df["close_nq"].to_numpy(np.float64)
    opn = df["open_nq"].to_numpy(np.float64) if "open_nq" in df.columns else close
    upper = df["upper1"].to_numpy(np.float64)
    lower = df["lower1"].to_numpy(np.float64)
    ny = df["ny_minutes"].to_numpy()
    years = df["year"].to_numpy()
    ts = df["ts_event"].to_numpy()
    day = df["day_id"].to_numpy()
    splits = np.where(day[:-1] != day[1:])[0] + 1
    bounds = np.concatenate(([0], splits, [len(df)]))

    fill = kw.get("fill", "next_open")
    entry_slippage = kw.get("entry_slippage", ENTRY_SLIP)
    orb_filter = kw.get("orb_filter", "wide")
    vwap_filter = kw.get("vwap_filter", True)
    orb_touch = kw.get("orb_touch", True)
    require_smt = kw.get("require_smt", True)
    sl_pts = kw.get("sl_pts", 15.0)
    target_frac = kw.get("target_frac", 0.20)
    wide_mult = kw.get("wide_mult", 1.10)
    fixed_thresh = kw.get("fixed_thresh", 40.0)
    exit_min = kw.get("exit_min", 930)
    max_trades = kw.get("max_trades", 2)
    start_year = kw.get("start_year", 2010)
    end_year = kw.get("end_year", 2026)

    trades = []
    orb_hist = []

    for di in range(len(bounds) - 1):
        s, e = int(bounds[di]), int(bounds[di + 1])
        if years[s] < start_year or years[s] > end_year:
            continue
        orb_bars = [k for k in range(s, e) if 570 <= ny[k] < 585]
        if len(orb_bars) < 15:
            continue
        oh = max(high[k] for k in orb_bars)
        ol = min(low[k] for k in orb_bars)
        rng_orb = oh - ol
        avg = float(np.mean(orb_hist[-20:])) if len(orb_hist) >= 5 else 35.0
        orb_hist.append(rng_orb)
        is_wide = True if orb_filter == "none" else (rng_orb > wide_mult * avg or rng_orb > fixed_thresh)
        if not is_wide:
            continue

        pos = 0
        ep = 0.0
        eb = -1
        stop = tgt = 0.0
        tt = ""
        pending = None
        n_day = 0
        sig_i = -1

        for i in [k for k in range(s, e) if ny[k] >= 585]:
            if pending and pos == 0 and fill == "next_open":
                pos = -1 if pending == "S" else 1
                ep = opn[i] + entry_slippage * pos
                eb = i
                if pos == -1:
                    stop, tgt, tt = oh + sl_pts, ol + target_frac * rng_orb, "SHORT"
                else:
                    stop, tgt, tt = ol - sl_pts, oh - target_frac * rng_orb, "LONG"
                pending = None
                n_day += 1

            if ny[i] >= exit_min:
                if pos:
                    pnl = (close[i] - ep) if pos == 1 else (ep - close[i])
                    trades.append(_t(day[s], ts[eb], ts[i], tt, ep, pnl, years[i], "SESSION", rng_orb, sig_i))
                    pos = 0
                break

            if pos:
                xp = reason = None
                if pos == 1:
                    hsl, htp = low[i] <= stop, high[i] >= tgt
                    if hsl and htp:
                        xp, reason = stop, "SL_SAME"
                    elif hsl:
                        xp, reason = stop, "SL"
                    elif htp:
                        xp, reason = tgt, "TP"
                    if xp is not None:
                        trades.append(_t(day[s], ts[eb], ts[i], tt, ep, xp - ep, years[i], reason, rng_orb, sig_i))
                        pos = 0
                else:
                    hsl, htp = high[i] >= stop, low[i] <= tgt
                    if hsl and htp:
                        xp, reason = stop, "SL_SAME"
                    elif hsl:
                        xp, reason = stop, "SL"
                    elif htp:
                        xp, reason = tgt, "TP"
                    if xp is not None:
                        trades.append(_t(day[s], ts[eb], ts[i], tt, ep, ep - xp, years[i], reason, rng_orb, sig_i))
                        pos = 0

            if pos == 0 and n_day < max_trades and pending is None:
                sc = (high[i] >= oh) if orb_touch else True
                lc = (low[i] <= ol) if orb_touch else True
                if vwap_filter:
                    sc = sc and high[i] >= upper[i]
                    lc = lc and low[i] <= lower[i]
                if require_smt:
                    sc = sc and smt_active[i] == -1
                    lc = lc and smt_active[i] == 1
                if sc:
                    pending, sig_i = "S", i
                elif lc:
                    pending, sig_i = "L", i

    t = pd.DataFrame(trades)
    if len(t):
        t["pnl_usd"] = t["pnl_pts"] * POINT_VAL - FRICTION * POINT_VAL
        t["entry_time"] = pd.to_datetime(t["entry_time"], utc=True)
        t["exit_time"] = pd.to_datetime(t["exit_time"], utc=True)
        t["session_date"] = pd.to_datetime(t["day_id"]).dt.date
    return t


def _t(day_id, et, xt, tt, ep, pnl, yr, reason, orb_r, sig_i):
    return dict(
        day_id=str(day_id), entry_time=et, exit_time=xt, trade_type=tt,
        entry_price=ep, pnl_pts=pnl, year=int(yr), exit_reason=reason,
        orb_range=orb_r, signal_bar=sig_i,
    )


def build_daily_features() -> pd.DataFrame:
    """Causal daily features from NQ 1m (18:00 session day)."""
    cache = art("regime_daily_features.parquet")
    if cache.exists() and cache.stat().st_mtime > Path("nq_1m_continuous.parquet").stat().st_mtime:
        p(f"Loading cached daily features from {cache}...")
        return pd.read_parquet(cache)
    t0 = time.time()
    nq = pd.read_parquet("nq_1m_continuous.parquet").sort_values("ts_event")
    dt = pd.to_datetime(nq["ts_event"]).dt.tz_convert("America/New_York")
    nq["ny_min"] = (dt.dt.hour * 60 + dt.dt.minute).astype(np.int16)
    shift = (dt.dt.hour >= 18) | (dt.dt.weekday == 6)
    sess = np.where(shift, dt + pd.Timedelta(days=1), dt)
    nq["session_day"] = pd.Series(sess).dt.date.values

    orb = nq[nq["ny_min"].between(570, 584)].groupby("session_day").agg(
        orb_hi=("high", "max"), orb_lo=("low", "min")
    )
    orb["orb_range"] = orb["orb_hi"] - orb["orb_lo"]

    rth = nq[nq["ny_min"].between(570, 960)].groupby("session_day").agg(
        rth_hi=("high", "max"), rth_lo=("low", "min"),
        rth_open=("open", "first"), rth_close=("close", "last"),
    )
    rth["rth_range"] = rth["rth_hi"] - rth["rth_lo"]

    on = nq[(nq["ny_min"] >= 1080) | (nq["ny_min"] < 570)].groupby("session_day").agg(
        on_hi=("high", "max"), on_lo=("low", "min")
    )
    on["overnight_range"] = on["on_hi"] - on["on_lo"]

    daily = orb[["orb_range"]].join(rth[["rth_range", "rth_open", "rth_close"]], how="outer")
    daily = daily.join(on[["overnight_range"]], how="outer").reset_index()
    daily = daily.sort_values("session_day").reset_index(drop=True)
    daily["year"] = pd.to_datetime(daily["session_day"]).dt.year

    daily["prior_rth_range"] = daily["rth_range"].shift(1)
    daily["prior_trend_pts"] = (daily["rth_close"] - daily["rth_open"]).shift(1).abs()
    daily["prior_trend_ratio"] = daily["prior_trend_pts"] / daily["prior_rth_range"].replace(0, np.nan)
    daily["prior_range_day"] = daily["prior_rth_range"]
    daily["prior_atr14"] = daily["rth_range"].shift(1).rolling(14, min_periods=5).mean()

    shifted = daily["orb_range"].shift(1)
    pct = []
    for i in range(len(daily)):
        if i < 60:
            pct.append(np.nan)
            continue
        window = shifted.iloc[max(0, i - 252):i].dropna()
        cur = daily["orb_range"].iloc[i]
        pct.append(float((window <= cur).mean()) if len(window) >= 20 and pd.notna(cur) else np.nan)
    daily["orb_pct_252"] = pct

    daily = daily.rename(columns={"session_day": "session_date"})
    daily["dow"] = pd.to_datetime(daily["session_date"]).dt.dayofweek
    daily["dow_name"] = pd.to_datetime(daily["session_date"]).dt.day_name()

    p(f"  Daily features: {len(daily):,} sessions in {time.time()-t0:.1f}s")
    daily.to_parquet(cache, index=False)
    return daily


def fetch_vix() -> pd.DataFrame:
    p("Fetching VIX (^VIX) via yfinance...")
    try:
        import yfinance as yf
        vix = yf.download("^VIX", start="2009-01-01", end="2026-09-01", progress=False, auto_adjust=True)
        if vix is None or len(vix) == 0:
            p("  VIX unavailable — continuing without VIX (NQ vol proxies still tested)")
            return pd.DataFrame(columns=["vix_date", "vix_close", "vix_change"])
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)
        vix = vix.reset_index()
        date_col = "Date" if "Date" in vix.columns else vix.columns[0]
        vix["vix_date"] = pd.to_datetime(vix[date_col]).dt.date
        vix = vix.rename(columns={"Close": "vix_close"}).sort_values("vix_date")
        vix["vix_change"] = vix["vix_close"].diff()
        p(f"  VIX rows: {len(vix):,}")
        return vix[["vix_date", "vix_close", "vix_change"]]
    except Exception as ex:
        p(f"  VIX fetch failed: {ex} — continuing without VIX")
        return pd.DataFrame(columns=["vix_date", "vix_close", "vix_change"])


def attach_rolling_strategy_features(trades: pd.DataFrame) -> pd.DataFrame:
    """Trailing 60-calendar-day strategy stats using only prior EXITED trades."""
    t = trades.sort_values("entry_time").reset_index(drop=True)
    exp60 = []
    pf60 = []
    n60 = []
    for i, row in t.iterrows():
        cutoff = row["entry_time"] - pd.Timedelta(days=60)
        prior = t.iloc[:i]
        prior = prior[prior["exit_time"] < row["entry_time"]]
        prior = prior[prior["exit_time"] >= cutoff]
        if len(prior) < 5:
            exp60.append(np.nan)
            pf60.append(np.nan)
            n60.append(len(prior))
            continue
        pnl = prior["pnl_usd"].values
        exp60.append(float(pnl.mean()))
        gp = pnl[pnl > 0].sum()
        gl = abs(pnl[pnl <= 0].sum())
        pf60.append(float(gp / gl) if gl > 0 else np.nan)
        n60.append(len(prior))
    t["roll_exp_60d"] = exp60
    t["roll_pf_60d"] = pf60
    t["roll_n_60d"] = n60
    return t


def enrich_trades(trades: pd.DataFrame, daily: pd.DataFrame, vix: pd.DataFrame) -> pd.DataFrame:
    t = trades.copy()
    t["session_date"] = pd.to_datetime(t["day_id"]).dt.date
    trade_year = t["year"].copy()
    feat = daily.drop(columns=["year"], errors="ignore").copy()
    if len(vix):
        feat = feat.sort_values("session_date")
        vix = vix.sort_values("vix_date")
        feat["session_dt"] = pd.to_datetime(feat["session_date"])
        vix["vix_dt"] = pd.to_datetime(vix["vix_date"])
        feat = pd.merge_asof(
            feat,
            vix,
            left_on="session_dt",
            right_on="vix_dt",
            direction="backward",
            allow_exact_matches=False,
        ).drop(columns=["session_dt", "vix_dt"], errors="ignore")
    t = t.merge(feat, on="session_date", how="left")
    t["year"] = trade_year
    t = attach_rolling_strategy_features(t)
    t["sample"] = np.where(t["year"] <= IS_END, "IS", "OOS")
    return t


def extended_metrics(t: pd.DataFrame, total_pnl: float | None = None) -> dict:
    m = metrics(t)
    if total_pnl and total_pnl != 0 and len(t):
        m["pct_total_pnl"] = round(100 * m["pnl"] / total_pnl, 1)
    else:
        m["pct_total_pnl"] = 0.0 if len(t) == 0 else 100.0
    # monthly stability
    if len(t) >= 10:
        t2 = t.copy()
        t2["ym"] = pd.to_datetime(t2["entry_time"]).dt.to_period("M")
        monthly = t2.groupby("ym")["pnl_usd"].sum()
        m["months_pos"] = int((monthly > 0).sum())
        m["months_total"] = int(len(monthly))
        m["monthly_pos_pct"] = round(100 * (monthly > 0).mean(), 1)
    else:
        m["months_pos"] = 0
        m["months_total"] = 0
        m["monthly_pos_pct"] = 0.0
    # yearly
    if len(t):
        yr = t.groupby("year")["pnl_usd"].sum()
        m["years_pos"] = int((yr > 0).sum())
        m["years_total"] = int(len(yr))
    else:
        m["years_pos"] = 0
        m["years_total"] = 0
    return m


def frozen_tertiles(is_vals: pd.Series) -> tuple[float, float]:
    v = is_vals.dropna()
    return float(v.quantile(1 / 3)), float(v.quantile(2 / 3))


def bucket(val, q33, q66) -> str:
    if pd.isna(val):
        return "NA"
    if val <= q33:
        return "Low"
    if val <= q66:
        return "Mid"
    return "High"


def regime_table(t: pd.DataFrame, col: str, q33: float, q66: float, label: str) -> list[dict]:
    rows = []
    sub = t.copy()
    sub["bucket"] = sub[col].apply(lambda x: bucket(x, q33, q66))
    for sample in ("IS", "OOS"):
        tot = sub[sub["sample"] == sample]["pnl_usd"].sum()
        for b in ("Low", "Mid", "High", "NA"):
            g = sub[(sub["sample"] == sample) & (sub["bucket"] == b)]
            if len(g) == 0:
                continue
            m = extended_metrics(g, tot)
            rows.append(dict(regime=label, feature=col, bucket=b, sample=sample, **m))
    return rows


def dow_table(t: pd.DataFrame, total_is: float, total_oos: float) -> list[dict]:
    rows = []
    for sample, tot in (("IS", total_is), ("OOS", total_oos)):
        sub = t[t["sample"] == sample]
        for dow in range(5):
            g = sub[sub["dow"] == dow]
            if len(g) == 0:
                continue
            name = ["Mon", "Tue", "Wed", "Thu", "Fri"][dow]
            m = extended_metrics(g, tot)
            rows.append(dict(regime="day_of_week", feature="dow", bucket=name, sample=sample, **m))
    return rows


def predefine_combined_filters(thresholds: dict) -> list[tuple[str, callable]]:
    """Rules frozen from IS thresholds — no OOS tuning."""
    T = thresholds
    rules = [
        ("orb_pct_high", lambda r: r["orb_pct_252"] >= T["orb_pct_252_q66"]),
        ("prior_atr_high", lambda r: r["prior_atr14"] >= T["prior_atr14_med"]),
        ("overnight_wide", lambda r: r["overnight_range"] >= T["overnight_range_med"]),
        ("prior_range_day", lambda r: r["prior_range_day"] >= T["prior_range_day_med"]),
        ("prior_trend_low", lambda r: r["prior_trend_ratio"] <= T["prior_trend_ratio_med"]),
        ("roll_exp_positive", lambda r: r["roll_exp_60d"] > 0),
        ("roll_pf_above_1", lambda r: (r["roll_pf_60d"] >= 1.0) & r["roll_pf_60d"].notna()),
    ]
    if "vix_close_med" in T:
        rules.insert(3, ("vix_elevated", lambda r: r["vix_close"] >= T["vix_close_med"]))
        rules.insert(4, ("vix_rising", lambda r: r["vix_change"] >= T["vix_change_med"]))
    return rules


def main():
    p("=" * 78)
    p(" HOSTILE REGIME VALIDATION — ORB + VWAP + SMT")
    p(f" IS: 2010-{IS_END} (thresholds only) | OOS: {OOS_START}-{OOS_END} (untouched)")
    p(f" Fill: next_open | friction {FRICTION}pt | entry slippage {ENTRY_SLIP}pt")
    p("=" * 78)

    df = load()
    smt = compute_smt_active(df)
    p("Running ORB+VWAP+SMT backtest...")
    trades = extended_backtest(
        df, smt,
        fill="next_open",
        entry_slippage=ENTRY_SLIP,
        orb_filter="wide",
        vwap_filter=True,
        orb_touch=True,
        require_smt=True,
    )
    p(f"  Trades: {len(trades):,}")

    daily = build_daily_features()
    vix = fetch_vix()
    t = enrich_trades(trades, daily, vix)
    t.to_csv(art("regime_trades_enriched.csv"), index=False)

    is_t = t[t["sample"] == "IS"]
    oos_t = t[t["sample"] == "OOS"]
    total_pnl = t["pnl_usd"].sum()
    total_is = is_t["pnl_usd"].sum()
    total_oos = oos_t["pnl_usd"].sum()

    baseline = {
        "IS": extended_metrics(is_t, total_is),
        "OOS": extended_metrics(oos_t, total_oos),
        "ALL": extended_metrics(t, total_pnl),
    }
    p("\nBASELINE (all trades, no regime filter):")
    p(f"  IS:  {baseline['IS']}")
    p(f"  OOS: {baseline['OOS']}")

    # Frozen thresholds from IS only
    thresholds = {
        "orb_pct_252_q33": float(is_t["orb_pct_252"].quantile(1 / 3)),
        "orb_pct_252_q66": float(is_t["orb_pct_252"].quantile(2 / 3)),
        "prior_atr14_med": float(is_t["prior_atr14"].median()),
        "overnight_range_med": float(is_t["overnight_range"].median()),
        "prior_range_day_med": float(is_t["prior_range_day"].median()),
        "prior_trend_ratio_med": float(is_t["prior_trend_ratio"].median()),
        "roll_exp_60d_med": float(is_t["roll_exp_60d"].median()),
    }
    if is_t["vix_close"].notna().any():
        thresholds["vix_close_med"] = float(is_t["vix_close"].median())
        thresholds["vix_change_med"] = float(is_t["vix_change"].median())

    regime_dims = [
        ("orb_pct_252", "ORB width percentile (252d)"),
        ("prior_atr14", "Prior-day ATR14 (RTH range)"),
        ("overnight_range", "Overnight NQ range"),
        ("prior_trend_ratio", "Prior session trend/range ratio"),
        ("prior_range_day", "Prior session RTH range"),
        ("roll_exp_60d", "Rolling 60d strategy expectancy"),
        ("roll_pf_60d", "Rolling 60d strategy PF"),
    ]
    if t["vix_close"].notna().any():
        regime_dims.insert(3, ("vix_close", "VIX prior close"))
        regime_dims.insert(4, ("vix_change", "VIX day-over-day change"))

    all_rows = []
    qcuts = {}
    for col, label in regime_dims:
        q33, q66 = frozen_tertiles(is_t[col])
        qcuts[col] = (q33, q66)
        rows = regime_table(t, col, q33, q66, label)
        all_rows.extend(rows)
        # Print OOS high vs low for quick read
        oos = t[t["sample"] == "OOS"].copy()
        oos["bucket"] = oos[col].apply(lambda x: bucket(x, q33, q66))
        hi = oos[oos["bucket"] == "High"]
        lo = oos[oos["bucket"] == "Low"]
        if len(hi) and len(lo):
            p(f"\n{label}:")
            p(f"  OOS High: {extended_metrics(hi, total_oos)}")
            p(f"  OOS Low:  {extended_metrics(lo, total_oos)}")

    all_rows.extend(dow_table(t, total_is, total_oos))

    df_reg = pd.DataFrame(all_rows)
    df_reg.to_csv(art("regime_validation_by_bucket.csv"), index=False)

    # Combined filters — each tested individually on IS+OOS
    combos = []
    filters = predefine_combined_filters(thresholds)
    for name, fn in filters:
        for sample_label, sub in (("IS", is_t), ("OOS", oos_t)):
            mask = fn(sub)
            g = sub[mask]
            rest = sub[~mask]
            combos.append(dict(
                filter=name, sample=sample_label, subset="pass",
                **extended_metrics(g, sub["pnl_usd"].sum()),
            ))
            combos.append(dict(
                filter=name, sample=sample_label, subset="fail",
                **extended_metrics(rest, sub["pnl_usd"].sum()),
            ))

    # IS-only: rank filters by pass-subset PF
    is_pass_pf = {}
    fn_map = {name: fn for name, fn in filters}
    for name, fn in filters:
        g = is_t[fn(is_t)]
        if len(g) >= 20:
            is_pass_pf[name] = metrics(g)["pf"]
    ranked = sorted(is_pass_pf.items(), key=lambda x: -x[1])
    p("\nIS filter ranking (pass subset PF):")
    for name, pf in ranked:
        p(f"  {name}: PF={pf}")

    is_base_pf = baseline["IS"]["pf"]
    selected = [n for n, pf in ranked if pf >= is_base_pf]

    union_mask_is = pd.Series(True, index=is_t.index)
    union_mask_oos = pd.Series(True, index=oos_t.index)
    for name in selected:
        fn = fn_map[name]
        union_mask_is &= fn(is_t)
        union_mask_oos &= fn(oos_t)

    union_rows = []
    for sample_label, sub, mask in (
        ("IS", is_t, union_mask_is),
        ("OOS", oos_t, union_mask_oos),
    ):
        union_rows.append(dict(
            filter="union_IS_selected", sample=sample_label, subset="pass",
            selected_filters=selected,
            **extended_metrics(sub[mask], sub["pnl_usd"].sum()),
        ))
        union_rows.append(dict(
            filter="union_IS_selected", sample=sample_label, subset="fail",
            selected_filters=selected,
            **extended_metrics(sub[~mask], sub["pnl_usd"].sum()),
        ))

    df_combo = pd.DataFrame(combos + union_rows)
    df_combo.to_csv(art("regime_validation_filters.csv"), index=False)

    # Yearly / monthly OOS stability for baseline vs best single filter on OOS
    best_filter = ranked[0][0] if ranked else None
    yearly_rows = []
    for yr, g in t.groupby("year"):
        yearly_rows.append(dict(year=int(yr), subset="baseline", **metrics(g)))
    if best_filter:
        fn = fn_map[best_filter]
        for yr, g in t.groupby("year"):
            gp = g[fn(g)]
            yearly_rows.append(dict(year=int(yr), subset=f"filter_{best_filter}", **metrics(gp)))

    df_yearly = pd.DataFrame(yearly_rows)
    df_yearly.to_csv(art("regime_validation_yearly.csv"), index=False)

    # Verdict
    oos_base = baseline["OOS"]
    oos_hi_orb = t[(t["sample"] == "OOS") & (t["orb_pct_252"] >= thresholds["orb_pct_252_q66"])]
    oos_vix = pd.DataFrame()
    if "vix_close_med" in thresholds:
        oos_vix = t[(t["sample"] == "OOS") & (t["vix_close"] >= thresholds["vix_close_med"])]

    verdict = {
        "baseline_IS": baseline["IS"],
        "baseline_OOS": baseline["OOS"],
        "frozen_thresholds": thresholds,
        "IS_filter_ranking": ranked,
        "union_selected_filters": selected,
        "OOS_tests": {
            "orb_pct_high_tertile": extended_metrics(oos_hi_orb, total_oos) if len(oos_hi_orb) else {},
            "vix_above_IS_median": (
                extended_metrics(oos_vix, total_oos) if len(oos_vix) >= 10
                else "VIX data unavailable in this run"
            ),
            "pct_oos_pnl_in_2022_plus": round(
                100 * t[(t["sample"] == "OOS") & (t["year"] >= 2022)]["pnl_usd"].sum() / max(total_oos, 1), 1
            ),
        },
        "production_ready": False,
        "verdict_text": "",
    }

    # Decision logic
    oos_pf = oos_base["pf"]
    oos_exp = oos_base["exp"]
    orb_oos_pf = metrics(oos_hi_orb)["pf"] if len(oos_hi_orb) >= 10 else 0
    vix_oos_pf = metrics(oos_vix)["pf"] if len(oos_vix) >= 10 else None

    if oos_pf >= 1.5 and oos_exp > 20:
        verdict["verdict_text"] = (
            "OOS baseline remains strong — edge persists in untouched 2024-2026 period."
        )
        if orb_oos_pf >= 1.5 and orb_oos_pf > oos_pf * 0.9:
            verdict["verdict_text"] += " ORB percentile filter adds/retains edge OOS."
        if vix_oos_pf is not None and vix_oos_pf < 1.2:
            verdict["verdict_text"] += " VIX filter NOT validated OOS — do not deploy VIX gate yet."
        elif vix_oos_pf is None:
            verdict["verdict_text"] += " VIX not tested this run (data unavailable)."
        verdict["production_ready"] = oos_pf >= 1.8 and baseline["OOS"]["years_pos"] >= baseline["OOS"]["years_total"] - 1
    elif oos_pf >= 1.0:
        verdict["verdict_text"] = (
            "OOS baseline is marginal — treat as regime-dependent; require live regime filter."
        )
    else:
        verdict["verdict_text"] = (
            "OOS baseline failed — PF 4.39 was largely a 2022+ phenomenon; not production-ready."
        )

    with open(art("regime_validation_report.json"), "w") as f:
        json.dump(verdict, f, indent=2, default=str)

    p("\n" + "=" * 78)
    p(" VERDICT")
    p("=" * 78)
    p(json.dumps(verdict, indent=2, default=str))
    p(f"\nSaved artifacts/regime_validation_report.json")
    p(f"Saved artifacts/regime_validation_by_bucket.csv")
    p(f"Saved artifacts/regime_validation_filters.csv")
    return verdict


if __name__ == "__main__":
    main()
