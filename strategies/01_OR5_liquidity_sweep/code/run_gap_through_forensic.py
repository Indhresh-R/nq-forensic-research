"""
Hostile causal forensic: PARKED gap-through mean-reversion hypothesis ONLY.
Optimized: one bar-walk per event, all structures evaluated on that path.
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

from common.paths import art


import json

import numpy as np
import pandas as pd

from run_orb_vwap_smt_edge_report import ART, FRICTION, POINT_VAL, compute_smt_active, load, p

IS_END = 2021
VAL_START, VAL_END = 2022, 2024
OOS_START, OOS_END = 2025, 2026
ORB_THRU = 15.0
ENTRY_SLIP = 1.0
WIDE_MULT, FIXED_THRESH = 1.10, 40.0
EXIT_MIN = 930
MAX_TRADES_DAY = 2

RAW = dict(name="RAW_SL15_TP1R", sl=15.0, tp_mode="R", tp_val=1.0)
PRIMARY = dict(name="PRIMARY_SL15_TP50pct_gap", sl=15.0, tp_mode="gap_frac", tp_val=0.50)

GRID = []
for sl in (10.0, 15.0, 20.0, 30.0):
    for r in (1.0, 1.5, 2.0):
        GRID.append(dict(name=f"SL{sl:g}_R{r:g}", sl=sl, tp_mode="R", tp_val=r))
    for gf in (0.25, 0.50, 0.75, 1.00):
        GRID.append(dict(name=f"SL{sl:g}_GAP{int(gf*100)}", sl=sl, tp_mode="gap_frac", tp_val=gf))
    GRID.append(dict(name=f"SL{sl:g}_TO_THRESH", sl=sl, tp_mode="to_threshold", tp_val=1.0))

OUT_JSON = art("gap_through_forensic_report.json")
OUT_TRADES = art("gap_through_trades.csv")
OUT_GRID = art("gap_through_grid.csv")
OUT_BUCKETS = art("gap_through_gap_buckets.csv")


def period_of(year: int) -> str:
    if year <= IS_END:
        return "IS"
    if VAL_START <= year <= VAL_END:
        return "VAL"
    if OOS_START <= year <= OOS_END:
        return "OOS"
    return "OTHER"


def metrics_plus(t: pd.DataFrame) -> dict:
    if t is None or len(t) == 0:
        return dict(
            trades=0, wr=0.0, pf=0.0, exp=0.0, pnl=0.0, mdd=0.0,
            losing_streak=0, months_pos=0, months_total=0, monthly_pos_pct=0.0,
            years_pos=0, years_total=0, tp_pct=0.0, sl_pct=0.0, session_pct=0.0,
        )
    d = t.sort_values("entry_time")
    n = len(d)
    w = d[d["pnl_usd"] > 0]
    l = d[d["pnl_usd"] <= 0]
    pnl = float(d["pnl_usd"].sum())
    gp, gl = float(w["pnl_usd"].sum()), abs(float(l["pnl_usd"].sum()))
    cum = d["pnl_usd"].cumsum()
    mdd = float((cum.cummax() - cum).max()) if n else 0.0
    streak = mx = 0
    for x in d["pnl_usd"].to_numpy():
        if x <= 0:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
    et = pd.to_datetime(d["entry_time"], utc=True)
    monthly = d.groupby(et.dt.tz_convert("America/New_York").dt.strftime("%Y-%m"))["pnl_usd"].sum()
    yearly = d.groupby(d["year"])["pnl_usd"].sum()
    return dict(
        trades=n,
        wr=round(100 * len(w) / n, 2),
        pf=round(gp / gl, 2) if gl > 0 else 0.0,
        exp=round(pnl / n, 2),
        pnl=round(pnl, 2),
        mdd=round(mdd, 2),
        losing_streak=int(mx),
        months_pos=int((monthly > 0).sum()),
        months_total=int(len(monthly)),
        monthly_pos_pct=round(100 * float((monthly > 0).mean()), 1) if len(monthly) else 0.0,
        years_pos=int((yearly > 0).sum()),
        years_total=int(len(yearly)),
        tp_pct=round(100 * (d["exit_reason"] == "TP").mean(), 1),
        sl_pct=round(100 * (d["exit_reason"].isin(["SL", "SL_SAME"])).mean(), 1),
        session_pct=round(100 * (d["exit_reason"] == "SESSION").mean(), 1),
    )


def collect_events(df: pd.DataFrame, smt: np.ndarray) -> pd.DataFrame:
    high = df["high_nq"].to_numpy(np.float64)
    low = df["low_nq"].to_numpy(np.float64)
    opn = df["open_nq"].to_numpy(np.float64)
    upper = df["upper1"].to_numpy(np.float64)
    lower = df["lower1"].to_numpy(np.float64)
    ny = df["ny_minutes"].to_numpy()
    years = df["year"].to_numpy()
    ts = df["ts_event"].to_numpy()
    day = df["day_id"].to_numpy()
    splits = np.where(day[:-1] != day[1:])[0] + 1
    bounds = np.concatenate(([0], splits, [len(df)]))

    events = []
    orb_hist = []

    for di in range(len(bounds) - 1):
        s, e = int(bounds[di]), int(bounds[di + 1])
        y = int(years[s])
        if y < 2010 or y > OOS_END:
            continue
        orb_bars = [k for k in range(s, e) if 570 <= ny[k] < 585]
        if len(orb_bars) < 15:
            continue
        oh = max(high[k] for k in orb_bars)
        ol = min(low[k] for k in orb_bars)
        rng = oh - ol
        avg = float(np.mean(orb_hist[-20:])) if len(orb_hist) >= 5 else 35.0
        orb_hist.append(rng)
        if not (rng > WIDE_MULT * avg or rng > FIXED_THRESH):
            continue

        thr_s = oh + ORB_THRU
        thr_l = ol - ORB_THRU
        pending = None
        sig_i = -1
        n_day = 0

        for i in range(s, e):
            if ny[i] < 585:
                continue
            if pending is not None and n_day < MAX_TRADES_DAY:
                side = -1 if pending == "S" else 1
                o = float(opn[i])
                is_gap = (side == -1 and o >= thr_s) or (side == 1 and o <= thr_l)
                if is_gap:
                    ep = o + ENTRY_SLIP if side == 1 else o - ENTRY_SLIP
                    gap = (o - thr_s) if side == -1 else (thr_l - o)
                    events.append((
                        str(day[s]), y, period_of(y), side, sig_i, i,
                        ts[sig_i], ts[i], oh, ol, rng,
                        thr_s if side == -1 else thr_l, o, ep, float(gap), s, e,
                    ))
                    n_day += 1
                pending = None

            if ny[i] >= EXIT_MIN:
                break

            if pending is None and n_day < MAX_TRADES_DAY:
                if high[i] >= oh and high[i] >= upper[i] and smt[i] == -1:
                    pending, sig_i = "S", i
                elif low[i] <= ol and low[i] <= lower[i] and smt[i] == 1:
                    pending, sig_i = "L", i

    cols = [
        "day_id", "year", "period", "side", "signal_i", "fill_i",
        "signal_time", "entry_time", "orb_hi", "orb_lo", "orb_range",
        "threshold", "raw_open", "entry_price", "gap_pts", "day_start", "day_end",
    ]
    return pd.DataFrame(events, columns=cols)


def levels_for(side, ep, thr, gap, sl, tp_mode, tp_val):
    if side == -1:
        stop = ep + sl
        if tp_mode == "R":
            tgt = ep - sl * tp_val
        elif tp_mode == "gap_frac":
            tgt = max(ep - tp_val * gap, thr)
        else:  # to_threshold
            tgt = thr
        reward = ep - tgt
    else:
        stop = ep - sl
        if tp_mode == "R":
            tgt = ep + sl * tp_val
        elif tp_mode == "gap_frac":
            tgt = min(ep + tp_val * gap, thr)
        else:
            tgt = thr
        reward = tgt - ep
    return stop, tgt, reward


def simulate_event_multi(high, low, close, ny, ts, ev, configs):
    """One path walk; return list of trade dicts for all valid configs."""
    side = int(ev.side)
    ep = float(ev.entry_price)
    gap = float(ev.gap_pts)
    thr = float(ev.threshold)
    i0 = int(ev.fill_i)
    e = int(ev.day_end)

    # prep structure states
    states = []
    for cfg in configs:
        stop, tgt, reward = levels_for(side, ep, thr, gap, cfg["sl"], cfg["tp_mode"], cfg["tp_val"])
        if reward <= 0:
            continue
        states.append([cfg, stop, tgt, reward, False])  # done flag

    if not states:
        return []

    mae = 0.0
    mfe = 0.0
    bars_to_mfe = 0
    rev_25 = rev_50 = rev_100 = False
    results_partial = {}  # name -> exit info when done
    path_end_i = i0
    path_end_px = float(close[i0])
    path_reason = "SESSION"

    for i in range(i0, e):
        path_end_i = i
        if ny[i] >= EXIT_MIN:
            path_end_px = float(close[i])
            path_reason = "SESSION"
            break
        hi, lo = float(high[i]), float(low[i])
        bars = i - i0
        if side == -1:
            mae = max(mae, hi - ep)
            fav = ep - lo
            if fav > mfe:
                mfe, bars_to_mfe = fav, bars
            if lo <= ep - 0.25 * gap:
                rev_25 = True
            if lo <= ep - 0.50 * gap:
                rev_50 = True
            if lo <= thr:
                rev_100 = True
            for st in states:
                if st[4]:
                    continue
                cfg, stop, tgt, reward, _ = st
                hit_sl, hit_tp = hi >= stop, lo <= tgt
                if hit_sl and hit_tp:
                    results_partial[cfg["name"]] = (i, stop, "SL_SAME", cfg, stop, tgt, reward)
                    st[4] = True
                elif hit_sl:
                    results_partial[cfg["name"]] = (i, stop, "SL", cfg, stop, tgt, reward)
                    st[4] = True
                elif hit_tp:
                    results_partial[cfg["name"]] = (i, tgt, "TP", cfg, stop, tgt, reward)
                    st[4] = True
        else:
            mae = max(mae, ep - lo)
            fav = hi - ep
            if fav > mfe:
                mfe, bars_to_mfe = fav, bars
            if hi >= ep + 0.25 * gap:
                rev_25 = True
            if hi >= ep + 0.50 * gap:
                rev_50 = True
            if hi >= thr:
                rev_100 = True
            for st in states:
                if st[4]:
                    continue
                cfg, stop, tgt, reward, _ = st
                hit_sl, hit_tp = lo <= stop, hi >= tgt
                if hit_sl and hit_tp:
                    results_partial[cfg["name"]] = (i, stop, "SL_SAME", cfg, stop, tgt, reward)
                    st[4] = True
                elif hit_sl:
                    results_partial[cfg["name"]] = (i, stop, "SL", cfg, stop, tgt, reward)
                    st[4] = True
                elif hit_tp:
                    results_partial[cfg["name"]] = (i, tgt, "TP", cfg, stop, tgt, reward)
                    st[4] = True
        if all(st[4] for st in states):
            break
    else:
        path_end_i = e - 1
        path_end_px = float(close[e - 1])
        path_reason = "SESSION"

    # unfinished -> session
    for st in states:
        cfg = st[0]
        if cfg["name"] not in results_partial:
            results_partial[cfg["name"]] = (
                path_end_i, path_end_px, path_reason, cfg, st[1], st[2], st[3]
            )

    base = dict(
        day_id=ev.day_id, year=int(ev.year), period=ev.period,
        trade_type="SHORT" if side == -1 else "LONG",
        signal_time=ev.signal_time, entry_time=ev.entry_time,
        orb_hi=float(ev.orb_hi), orb_lo=float(ev.orb_lo), orb_range=float(ev.orb_range),
        threshold=thr, raw_open=float(ev.raw_open), entry_price=ep,
        gap_pts=gap, side=side,
        mae_pts=mae, mfe_pts=mfe, bars_to_mfe=bars_to_mfe,
        rev_25=rev_25, rev_50=rev_50, rev_100=rev_100,
        mfe_over_gap=round(mfe / gap, 3) if gap > 0 else 0.0,
    )
    out = []
    for name, (xi, xp, reason, cfg, stop, tgt, reward) in results_partial.items():
        pnl_pts = (xp - ep) if side == 1 else (ep - xp)
        out.append(dict(
            **base,
            structure=name,
            sl_pts=cfg["sl"], tp_mode=cfg["tp_mode"], tp_val=cfg["tp_val"],
            stop_px=stop, target_px=tgt, reward_pts=reward,
            exit_time=ts[xi], exit_price=xp, exit_reason=reason,
            bars_held=xi - i0,
            pnl_pts=pnl_pts,
            pnl_usd=pnl_pts * POINT_VAL - FRICTION * POINT_VAL,
            mae_over_sl=round(mae / cfg["sl"], 3) if cfg["sl"] else 0.0,
            entry_slip=ENTRY_SLIP,
        ))
    return out


def run_all(df, events, configs):
    high = df["high_nq"].to_numpy(np.float64)
    low = df["low_nq"].to_numpy(np.float64)
    close = df["close_nq"].to_numpy(np.float64)
    ny = df["ny_minutes"].to_numpy()
    ts = df["ts_event"].to_numpy()
    rows = []
    for ev in events.itertuples(index=False):
        rows.extend(simulate_event_multi(high, low, close, ny, ts, ev, configs))
    return pd.DataFrame(rows)


def gap_analytics(trades: pd.DataFrame, label: str) -> dict:
    if len(trades) == 0:
        return dict(label=label, n=0)
    g = trades
    return dict(
        label=label, n=int(len(g)),
        gap_median=round(float(g["gap_pts"].median()), 2),
        gap_mean=round(float(g["gap_pts"].mean()), 2),
        gap_p90=round(float(g["gap_pts"].quantile(0.9)), 2),
        mae_median=round(float(g["mae_pts"].median()), 2),
        mfe_median=round(float(g["mfe_pts"].median()), 2),
        mfe_over_gap_median=round(float(g["mfe_over_gap"].median()), 3),
        pct_rev_25=round(100 * g["rev_25"].mean(), 1),
        pct_rev_50=round(100 * g["rev_50"].mean(), 1),
        pct_rev_100=round(100 * g["rev_100"].mean(), 1),
        med_bars_to_mfe=round(float(g["bars_to_mfe"].median()), 1),
        med_bars_held=round(float(g["bars_held"].median()), 1),
    )


def gap_buckets(trades: pd.DataFrame) -> pd.DataFrame:
    if len(trades) == 0:
        return pd.DataFrame()
    d = trades.copy()
    bins = [0, 5, 15, 30, 50, 100, 1000]
    labels = ["0-5", "5-15", "15-30", "30-50", "50-100", "100+"]
    d["gap_bucket"] = pd.cut(d["gap_pts"], bins=bins, labels=labels, right=False)
    rows = []
    for b, g in d.groupby("gap_bucket", observed=False):
        if len(g) == 0:
            continue
        m = metrics_plus(g)
        rows.append(dict(
            gap_bucket=str(b), **m,
            gap_mean=round(float(g["gap_pts"].mean()), 2),
            mfe_med=round(float(g["mfe_pts"].median()), 2),
            mae_med=round(float(g["mae_pts"].median()), 2),
            pct_rev_50=round(100 * g["rev_50"].mean(), 1),
        ))
    return pd.DataFrame(rows)


def slip_stress_primary(df, events, slips=(0.5, 1.0, 2.0, 3.0)):
    high = df["high_nq"].to_numpy(np.float64)
    low = df["low_nq"].to_numpy(np.float64)
    close = df["close_nq"].to_numpy(np.float64)
    ny = df["ny_minutes"].to_numpy()
    ts = df["ts_event"].to_numpy()
    cfg = PRIMARY
    out = []
    for slip in slips:
        rows = []
        for ev in events.itertuples(index=False):
            # mutate entry adversely
            class E: pass
            e = E()
            for c in events.columns:
                setattr(e, c, getattr(ev, c))
            o = float(ev.raw_open)
            e.entry_price = o + slip if int(ev.side) == 1 else o - slip
            rows.extend(simulate_event_multi(high, low, close, ny, ts, e, [cfg]))
        t = pd.DataFrame(rows)
        for period in ("IS", "VAL", "OOS"):
            m = metrics_plus(t[t["period"] == period] if len(t) else t)
            out.append(dict(slip=slip, period=period, **m))
    return out


def main():
    p("=" * 78)
    p(" GAP-THROUGH FORENSIC — parked hypothesis only")
    p(f" IS 2010-{IS_END} | VAL {VAL_START}-{VAL_END} | OOS {OOS_START}-{OOS_END}")
    p(f" Adverse slip | friction {FRICTION} | stop FROM ENTRY | pessimistic SL_SAME")
    p(f" Primary: {PRIMARY['name']}")
    p("=" * 78)

    df = load()
    df["day_id"] = df["day_id"].astype(str)
    smt = compute_smt_active(df)
    p("Collecting gap-through events...")
    events = collect_events(df, smt)
    p(f"  Events: {len(events):,} IS={(events.period=='IS').sum()} "
      f"VAL={(events.period=='VAL').sum()} OOS={(events.period=='OOS').sum()}")
    p(f"  Gap median={events.gap_pts.median():.1f} mean={events.gap_pts.mean():.1f}")

    # unique configs
    seen, configs = set(), []
    for cfg in [RAW, PRIMARY] + GRID:
        if cfg["name"] not in seen:
            seen.add(cfg["name"])
            configs.append(cfg)

    p(f"Simulating {len(configs)} structures on {len(events)} events (one path walk each)...")
    all_tr = run_all(df, events, configs)
    p(f"  Trade rows: {len(all_tr):,}")

    raw_tr = all_tr[all_tr["structure"] == RAW["name"]]
    prim_tr = all_tr[all_tr["structure"] == PRIMARY["name"]].copy()

    p("\n--- RAW UNFILTERED (SL15, TP=1R) ---")
    raw_by = {}
    for period in ("IS", "VAL", "OOS"):
        m = metrics_plus(raw_tr[raw_tr.period == period])
        raw_by[period] = m
        p(f"  {period:4s} N={m['trades']:4d} WR={m['wr']:5.1f}% PF={m['pf']:5.2f} "
          f"exp=${m['exp']:7.2f} PnL=${m['pnl']:10,.0f} MDD=${m['mdd']:8,.0f} "
          f"streak={m['losing_streak']} mos+={m['months_pos']}/{m['months_total']} "
          f"yr+={m['years_pos']}/{m['years_total']} TP%={m['tp_pct']} SL%={m['sl_pct']} SES%={m['session_pct']}")

    p(f"\n--- PRIMARY {PRIMARY['name']} ---")
    prim_by = {}
    for period in ("IS", "VAL", "OOS"):
        sub = prim_tr[prim_tr.period == period]
        m = metrics_plus(sub)
        prim_by[period] = m
        p(f"  {period:4s} N={m['trades']:4d} WR={m['wr']:5.1f}% PF={m['pf']:5.2f} "
          f"exp=${m['exp']:7.2f} PnL=${m['pnl']:10,.0f} MDD=${m['mdd']:8,.0f} "
          f"streak={m['losing_streak']} mos+={m['months_pos']}/{m['months_total']} "
          f"yr+={m['years_pos']}/{m['years_total']} TP%={m['tp_pct']} SL%={m['sl_pct']} SES%={m['session_pct']}")
        if len(sub):
            p(f"       exits: {sub['exit_reason'].value_counts().to_dict()}")

    analytics = {k: gap_analytics(prim_tr[prim_tr.period == k] if k != "ALL" else prim_tr, k)
                 for k in ("ALL", "IS", "VAL", "OOS")}
    p("\n--- GAP / MAE / MFE / REVERSION (PRIMARY) ---")
    for k, a in analytics.items():
        p(f"  {a}")

    bucket_frames = []
    for period in ("IS", "VAL", "OOS"):
        b = gap_buckets(prim_tr[prim_tr.period == period])
        if len(b):
            b["period"] = period
            bucket_frames.append(b)
            p(f"\n  Buckets {period}:")
            p(b.to_string(index=False))
    if bucket_frames:
        pd.concat(bucket_frames, ignore_index=True).to_csv(OUT_BUCKETS, index=False)

    p("\n--- GRID ---")
    grid_rows = []
    for name in sorted(all_tr["structure"].unique()):
        tr = all_tr[all_tr["structure"] == name]
        for period in ("IS", "VAL", "OOS"):
            m = metrics_plus(tr[tr.period == period])
            cfg = next(c for c in configs if c["name"] == name)
            grid_rows.append(dict(structure=name, period=period, **m,
                                  sl=cfg["sl"], tp_mode=cfg["tp_mode"], tp_val=cfg["tp_val"]))
        oos_m = metrics_plus(tr[tr.period == "OOS"])
        p(f"  {name:28s} OOS PF={oos_m['pf']:5.2f} exp=${oos_m['exp']:7.2f} N={oos_m['trades']}")
    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(OUT_GRID, index=False)

    piv = grid_df.pivot_table(index="structure", columns="period", values="pf")
    robust, robust_oos = [], []
    for name in piv.index:
        is_pf = float(piv.loc[name]["IS"]) if "IS" in piv.columns else 0.0
        val_pf = float(piv.loc[name]["VAL"]) if "VAL" in piv.columns else 0.0
        oos_pf = float(piv.loc[name]["OOS"]) if "OOS" in piv.columns else 0.0
        row = dict(structure=name, IS_pf=round(is_pf, 2), VAL_pf=round(val_pf, 2), OOS_pf=round(oos_pf, 2))
        if is_pf >= 1.2 and val_pf >= 1.2:
            robust.append(row)
            if oos_pf >= 1.1:
                robust_oos.append(row)
    p(f"\nRobust IS&VAL PF>=1.2: {len(robust)}")
    p(f"Also OOS PF>=1.1: {len(robust_oos)}")
    for r in robust_oos[:15]:
        p(f"  {r}")

    p("\n--- SLIP STRESS PRIMARY ---")
    slip_rows = slip_stress_primary(df, events)
    for r in slip_rows:
        if r["period"] == "OOS":
            p(f"  slip={r['slip']} OOS N={r['trades']} PF={r['pf']} exp=${r['exp']} PnL=${r['pnl']:,}")

    prim_tr.to_csv(OUT_TRADES, index=False)

    oos = prim_by["OOS"]
    broad = len(robust_oos) >= 3
    if oos["trades"] < 20 or oos["pf"] < 1.1 or oos["exp"] <= 0:
        status = "FAILED"
        verdict = (
            "FAILED — gap-through exhaustion hypothesis shows no genuine executable OOS edge "
            f"under pre-committed PRIMARY ({PRIMARY['name']}). "
            "Untouched 2025-2026 does not support a tradable edge. Stop. Do not optimize further."
        )
    elif broad and oos["pf"] >= 1.2 and oos["exp"] > 0:
        status = "ROBUST_CANDIDATE"
        verdict = (
            "PRIMARY OOS profitable and multiple nearby pre-specified structures also OOS-positive. "
            "Research candidate only — not production."
        )
    else:
        status = "FAILED"
        verdict = (
            "FAILED — OOS PRIMARY not sufficiently strong and/or no broad robust region. "
            "Stop optimization."
        )

    # If primary failed but list robust_oos, still FAILED per protocol (no cherry-pick)
    if status != "ROBUST_CANDIDATE" and robust_oos:
        verdict += (
            f" Note: {len(robust_oos)} grid cells were OOS-positive after the fact — "
            "not admissible as evidence without pre-commitment."
        )

    report = {
        "hypothesis": "Gap-through ORB+VWAP+SMT mean reversion from actual fill",
        "status": status,
        "verdict": verdict,
        "not_the_failed_strategy": True,
        "design": {
            "data": "session_cached built from raw NQ/ES 1m continuous",
            "orb": "09:30-09:45 NY (570-584)",
            "gap_through": "next open beyond ORB±15",
            "entry": "actual open + ADVERSE slip",
            "stop": "FROM ENTRY never ORB-extreme",
            "same_bar": "pessimistic SL_SAME",
            "primary": PRIMARY,
            "raw": RAW,
            "splits": {"IS": "2010-2021", "VAL": "2022-2024", "OOS": "2025-2026"},
        },
        "event_counts": {
            "ALL": int(len(events)),
            "IS": int((events.period == "IS").sum()),
            "VAL": int((events.period == "VAL").sum()),
            "OOS": int((events.period == "OOS").sum()),
            "gap_median": round(float(events.gap_pts.median()), 2),
            "gap_mean": round(float(events.gap_pts.mean()), 2),
        },
        "raw_unfiltered": raw_by,
        "primary": prim_by,
        "gap_path_analytics": analytics,
        "robust_is_val": robust,
        "robust_also_oos": robust_oos,
        "slip_stress_primary": slip_rows,
        "exit_reasons_primary": {
            period: prim_tr[prim_tr.period == period]["exit_reason"].value_counts().to_dict()
            for period in ("IS", "VAL", "OOS") if len(prim_tr[prim_tr.period == period])
        },
    }
    with open(OUT_JSON, "w") as f:
        json.dump(report, f, indent=2, default=str)

    p("\n" + "=" * 78)
    p(f" STATUS: {status}")
    p(verdict)
    p(f"Saved {OUT_JSON}")
    p(f"Saved {OUT_TRADES}")
    p(f"Saved {OUT_GRID}")
    return report


if __name__ == "__main__":
    main()
