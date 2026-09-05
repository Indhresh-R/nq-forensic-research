"""
ORB / VWAP / SMT edge retest on session_cached (matches prior Inverse ORB tests).
Fill models: close (original) and next_open (causal, no gap-stop-at-entry).
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
import time
from pathlib import Path

import numpy as np
import pandas as pd

from common.paths import art, ART, DATA, ROOT
ART.mkdir(exist_ok=True)
POINT_VAL = 6.0
FRICTION = 0.25


def p(*a):
    print(*a, flush=True)


def load():
    t0 = time.time()
    candidates = [
        DATA / "session_cached.parquet",
        ROOT / "session_cached.parquet",
    ]
    src = next((c for c in candidates if c.exists()), None)
    if src is None:
        raise FileNotFoundError("session_cached.parquet not found under data/ or repo root")
    df = pd.read_parquet(src)
    # RTH for ORB; keep premarket for SMT quarters via full cache days
    p(f"Loaded session_cached {len(df):,} rows from {src.name} in {time.time()-t0:.1f}s")
    return df


def metrics(t: pd.DataFrame) -> dict:
    if t is None or len(t) == 0:
        return dict(trades=0, wr=0.0, pnl=0.0, pf=0.0, exp=0.0, mdd=0.0, win_days=0.0)
    d = t.copy()
    if "pnl_usd" not in d.columns:
        d["pnl_usd"] = d["pnl_pts"] * POINT_VAL - FRICTION * POINT_VAL
    n = len(d)
    w = d[d["pnl_pts"] > 0]
    l = d[d["pnl_pts"] <= 0]
    pnl = float(d["pnl_usd"].sum())
    gp, gl = float(w["pnl_usd"].sum()), abs(float(l["pnl_usd"].sum()))
    cum = d["pnl_usd"].cumsum()
    daily = d.groupby(pd.to_datetime(d["entry_time"]).dt.date)["pnl_usd"].sum()
    return dict(
        trades=n,
        wr=round(100 * len(w) / n, 2),
        pnl=round(pnl, 2),
        pf=round(gp / gl, 2) if gl > 0 else 0.0,
        exp=round(pnl / n, 2),
        mdd=round(float((cum.cummax() - cum).max()), 2),
        win_days=round(100 * float((daily > 0).mean()), 1),
    )


def yearly(t: pd.DataFrame) -> pd.DataFrame:
    if t is None or len(t) == 0:
        return pd.DataFrame()
    rows = [{"year": int(y), **metrics(g)} for y, g in t.groupby("year")]
    return pd.DataFrame(rows)


def compute_smt_active(df: pd.DataFrame, confirm_bars: int = 30):
    high_nq = df["high_nq"].to_numpy(np.float64)
    low_nq = df["low_nq"].to_numpy(np.float64)
    high_es = df["high_es"].to_numpy(np.float64)
    low_es = df["low_es"].to_numpy(np.float64)
    upper = df["upper1"].to_numpy(np.float64)
    lower = df["lower1"].to_numpy(np.float64)
    ny = df["ny_minutes"].to_numpy()
    day = df["day_id"].to_numpy()
    splits = np.where(day[:-1] != day[1:])[0] + 1
    bounds = np.concatenate(([0], splits, [len(df)]))
    active = np.zeros(len(df), dtype=np.int8)
    nan = float("nan")

    for di in range(len(bounds) - 1):
        s, e = int(bounds[di]), int(bounds[di + 1])
        q1h_n = q1l_n = q1h_e = q1l_e = nan
        q2h_n = q2l_n = q2h_e = q2l_e = nan
        q3h_n = q3l_n = q3h_e = q3l_e = nan
        ch_n = cl_n = ch_e = cl_e = nan
        u1h = u1l = u2h = u2l = u3h = u3l = False
        prev_q = 0
        setup = 0
        setup_i = -1
        for i in range(s, e):
            m = int(ny[i])
            cq = 1 if m < 450 else 2 if m < 540 else 3 if m < 630 else 4
            if cq != prev_q:
                if cq == 2:
                    q1h_n, q1l_n, q1h_e, q1l_e = ch_n, cl_n, ch_e, cl_e
                elif cq == 3:
                    q2h_n, q2l_n, q2h_e, q2l_e = ch_n, cl_n, ch_e, cl_e
                elif cq == 4:
                    q3h_n, q3l_n, q3h_e, q3l_e = ch_n, cl_n, ch_e, cl_e
                ch_n, cl_n, ch_e, cl_e = high_nq[i], low_nq[i], high_es[i], low_es[i]
            else:
                ch_n = max(ch_n, high_nq[i]) if ch_n == ch_n else high_nq[i]
                cl_n = min(cl_n, low_nq[i]) if cl_n == cl_n else low_nq[i]
                ch_e = max(ch_e, high_es[i]) if ch_e == ch_e else high_es[i]
                cl_e = min(cl_e, low_es[i]) if cl_e == cl_e else low_es[i]
            prev_q = cq

            bear = bull = False
            ob, os_ = high_nq[i] >= upper[i], low_nq[i] <= lower[i]
            if cq >= 2 and q1h_n == q1h_n and not u1h and ((high_nq[i] > q1h_n) ^ (high_es[i] > q1h_e)) and ob:
                bear, u1h = True, True
            if cq >= 2 and q1l_n == q1l_n and not u1l and ((low_nq[i] < q1l_n) ^ (low_es[i] < q1l_e)) and os_:
                bull, u1l = True, True
            if cq >= 3 and q2h_n == q2h_n and not u2h and ((high_nq[i] > q2h_n) ^ (high_es[i] > q2h_e)) and ob:
                bear, u2h = True, True
            if cq >= 3 and q2l_n == q2l_n and not u2l and ((low_nq[i] < q2l_n) ^ (low_es[i] < q2l_e)) and os_:
                bull, u2l = True, True
            if cq == 4 and q3h_n == q3h_n and not u3h and ((high_nq[i] > q3h_n) ^ (high_es[i] > q3h_e)) and ob:
                bear, u3h = True, True
            if cq == 4 and q3l_n == q3l_n and not u3l and ((low_nq[i] < q3l_n) ^ (low_es[i] < q3l_e)) and os_:
                bull, u3l = True, True

            if bear:
                setup, setup_i = -1, i
            elif bull:
                setup, setup_i = 1, i
            if setup and i - setup_i > confirm_bars:
                setup = 0
            active[i] = setup
    return active


def backtest(
    df,
    smt_active,
    *,
    fill="close",  # close | next_open
    orb_filter="wide",
    vwap_filter=True,
    orb_touch=True,
    require_smt=False,
    direction="normal",
    random_seed=42,
    start_year=2010,
    end_year=2026,
    entry_slippage=0.0,
    max_trades=2,
    sl_pts=15.0,
    target_frac=0.20,
    wide_mult=1.10,
    fixed_thresh=40.0,
    exit_min=930,
):
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
    rng = np.random.default_rng(random_seed)

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

        pos = 0
        ep = 0.0
        eb = -1
        stop = tgt = 0.0
        tt = ""
        pending = None
        n_day = 0
        post = [k for k in range(s, e) if ny[k] >= 585]

        for i in post:
            # fill pending next-open
            if pending and pos == 0 and fill == "next_open":
                side = -1 if pending == "S" else 1
                if direction == "opposite":
                    side *= -1
                elif direction == "random":
                    side = int(rng.choice([-1, 1]))
                pos = side
                ep = opn[i] + entry_slippage * side
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
                    trades.append(dict(entry_time=ts[eb], exit_time=ts[i], trade_type=tt,
                                       pnl_pts=pnl, year=int(years[i]), exit_reason="SESSION"))
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
                        trades.append(dict(entry_time=ts[eb], exit_time=ts[i], trade_type=tt,
                                           pnl_pts=xp - ep, year=int(years[i]), exit_reason=reason))
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
                        trades.append(dict(entry_time=ts[eb], exit_time=ts[i], trade_type=tt,
                                           pnl_pts=ep - xp, year=int(years[i]), exit_reason=reason))
                        pos = 0

            if pos == 0 and n_day < max_trades and is_wide and pending is None:
                sc = (high[i] >= oh) if orb_touch else True
                lc = (low[i] <= ol) if orb_touch else True
                if vwap_filter:
                    sc = sc and high[i] >= upper[i]
                    lc = lc and low[i] <= lower[i]
                if require_smt:
                    sc = sc and smt_active[i] == -1
                    lc = lc and smt_active[i] == 1

                side = None
                if sc:
                    side = -1
                elif lc:
                    side = 1
                if side is None:
                    continue
                if direction == "opposite":
                    side *= -1
                elif direction == "random":
                    side = int(rng.choice([-1, 1]))

                if fill == "close":
                    # Match original test_15m_orb_strategy: enter at close, manage from subsequent bars
                    pos = side
                    ep = close[i] + entry_slippage * side
                    eb = i
                    if pos == -1:
                        stop, tgt, tt = oh + sl_pts, ol + target_frac * rng_orb, "SHORT"
                    else:
                        stop, tgt, tt = ol - sl_pts, oh - target_frac * rng_orb, "LONG"
                    n_day += 1
                else:
                    pending = "S" if side == -1 else "L"

    t = pd.DataFrame(trades)
    if len(t):
        t["pnl_usd"] = t["pnl_pts"] * POINT_VAL - FRICTION * POINT_VAL
    return t


def smt_native(df):
    from run_complete_suite import run_sim_numpy
    day = df["day_id"].to_numpy()
    splits = np.where(day[:-1] != day[1:])[0] + 1
    bounds = np.concatenate(([0], splits, [len(df)]))
    data = {
        "high_nq": df["high_nq"].to_numpy(np.float64),
        "low_nq": df["low_nq"].to_numpy(np.float64),
        "close_nq": df["close_nq"].to_numpy(np.float64),
        "high_es": df["high_es"].to_numpy(np.float64),
        "low_es": df["low_es"].to_numpy(np.float64),
        "upper1": df["upper1"].to_numpy(np.float64),
        "lower1": df["lower1"].to_numpy(np.float64),
        "upper2": df["upper2"].to_numpy(np.float64),
        "lower2": df["lower2"].to_numpy(np.float64),
        "upper3": df["upper3"].to_numpy(np.float64),
        "lower3": df["lower3"].to_numpy(np.float64),
        "bearish_mss": df["bearish_mss"].to_numpy(),
        "bullish_mss": df["bullish_mss"].to_numpy(),
        "bearish_ifvg": df["bearish_ifvg"].to_numpy(),
        "bullish_ifvg": df["bullish_ifvg"].to_numpy(),
        "ny_minutes": df["ny_minutes"].to_numpy(),
        "years": df["year"].to_numpy(),
        "timestamps": df["ts_event"].to_numpy(),
        "day_bounds": bounds,
    }
    t = run_sim_numpy(data, band_choice="SD1", confirm_bars=30, confirmation="MSS Only",
                      stop_points=20.0, target_points=30.0, friction_pts=0.25)
    if len(t) == 0:
        return t
    t = t.copy()
    t["pnl_usd"] = t["pnl_pts"] * POINT_VAL  # rescale from $20/pt engine to $6/pt
    t["trade_type"] = t["type"]
    return t


def main():
    p("=" * 78)
    p(" ORB / VWAP / SMT EDGE RETEST (session_cached, original close-fill + causal next-open)")
    p(" Params: 15m ORB | wide 1.10x/40 | SD1.28 | SL15 | tgt 0.20 ORB | exit 15:30 | 3xMNQ")
    p("=" * 78)
    df = load()
    p("SMT flags...")
    t0 = time.time()
    smt = compute_smt_active(df)
    p(f"  active={(smt != 0).sum():,} in {time.time()-t0:.1f}s")

    cores = [
        ("ORB_only", dict(orb_filter="wide", vwap_filter=False, orb_touch=True, require_smt=False)),
        ("VWAP_only", dict(orb_filter="none", vwap_filter=True, orb_touch=False, require_smt=False)),
        ("ORB_VWAP", dict(orb_filter="wide", vwap_filter=True, orb_touch=True, require_smt=False)),
        ("ORB_SMT", dict(orb_filter="wide", vwap_filter=False, orb_touch=True, require_smt=True)),
        ("VWAP_SMT", dict(orb_filter="none", vwap_filter=True, orb_touch=False, require_smt=True)),
        ("ORB_VWAP_SMT", dict(orb_filter="wide", vwap_filter=True, orb_touch=True, require_smt=True)),
    ]
    controls = [
        ("ORB_VWAP_opposite", dict(orb_filter="wide", vwap_filter=True, orb_touch=True, require_smt=False, direction="opposite")),
        ("ORB_VWAP_random", dict(orb_filter="wide", vwap_filter=True, orb_touch=True, require_smt=False, direction="random")),
    ]

    rows = []
    yearly_frames = []
    for fill in ("close", "next_open"):
        for name, kw in cores + (controls if fill == "close" else []):
            label = f"{fill}__{name}"
            p(f"Running {label}...")
            t0 = time.time()
            t = backtest(df, smt, fill=fill, **kw)
            m = metrics(t)
            p(f"  {m} ({time.time()-t0:.1f}s)")
            rows.append({"fill": fill, "variant": name, **m})
            y = yearly(t)
            if len(y):
                y.insert(0, "fill", fill)
                y.insert(1, "variant", name)
                yearly_frames.append(y)
            if name == "ORB_VWAP" and fill == "close" and len(t):
                t.to_csv(art("edge_close_ORB_VWAP_trades.csv"), index=False)

    p("SMT native (MSS confirm)...")
    t0 = time.time()
    t_smt = smt_native(df)
    m = metrics(t_smt)
    p(f"  {m} ({time.time()-t0:.1f}s)")
    rows.append({"fill": "native", "variant": "SMT_only", **m})
    y = yearly(t_smt)
    if len(y):
        y.insert(0, "fill", "native")
        y.insert(1, "variant", "SMT_only")
        yearly_frames.append(y)

    # Slippage on close ORB_VWAP
    p("Slippage (close ORB_VWAP)...")
    slip_rows = []
    for slip in [0, 0.5, 1, 2, 3, 5]:
        t = backtest(df, smt, fill="close", orb_filter="wide", vwap_filter=True, orb_touch=True,
                     require_smt=False, entry_slippage=slip)
        slip_rows.append({"slippage_pts": slip, **metrics(t)})
        p(f"  slip={slip}: {slip_rows[-1]}")

    # Subperiods close fill
    p("Subperiods...")
    sub_rows = []
    for a, b in [(2010, 2014), (2015, 2018), (2019, 2021), (2022, 2024), (2025, 2026)]:
        for name, kw in [
            ("ORB_only", dict(orb_filter="wide", vwap_filter=False, orb_touch=True, require_smt=False)),
            ("VWAP_only", dict(orb_filter="none", vwap_filter=True, orb_touch=False, require_smt=False)),
            ("ORB_VWAP", dict(orb_filter="wide", vwap_filter=True, orb_touch=True, require_smt=False)),
            ("ORB_VWAP_SMT", dict(orb_filter="wide", vwap_filter=True, orb_touch=True, require_smt=True)),
        ]:
            t = backtest(df, smt, fill="close", start_year=a, end_year=b, **kw)
            sub_rows.append({"period": f"{a}-{b}", "variant": name, **metrics(t)})

    df_sum = pd.DataFrame(rows)
    df_year = pd.concat(yearly_frames, ignore_index=True) if yearly_frames else pd.DataFrame()
    df_slip = pd.DataFrame(slip_rows)
    df_sub = pd.DataFrame(sub_rows)
    df_sum.to_csv(art("edge_variant_summary.csv"), index=False)
    df_year.to_csv(art("edge_variant_yearly.csv"), index=False)
    df_slip.to_csv(art("edge_slippage_orb_vwap.csv"), index=False)
    df_sub.to_csv(art("edge_subperiod.csv"), index=False)

    def get(fill, variant):
        return next(r for r in rows if r["fill"] == fill and r["variant"] == variant)

    base = get("close", "ORB_VWAP")
    base_open = get("next_open", "ORB_VWAP")
    opp = get("close", "ORB_VWAP_opposite")
    rnd = get("close", "ORB_VWAP_random")
    orb = get("close", "ORB_only")
    vwap = get("close", "VWAP_only")
    combo_smt = get("close", "ORB_VWAP_SMT")
    smt_only = next(r for r in rows if r["variant"] == "SMT_only")

    yb = df_year[(df_year["fill"] == "close") & (df_year["variant"] == "ORB_VWAP")]
    early = df_sub[(df_sub["variant"] == "ORB_VWAP") & (df_sub["period"].isin(["2010-2014", "2015-2018"]))]
    late = df_sub[(df_sub["variant"] == "ORB_VWAP") & (df_sub["period"].isin(["2022-2024", "2025-2026"]))]
    slip1 = next(r for r in slip_rows if r["slippage_pts"] == 1)
    early_pf = float(early["pf"].mean()) if len(early) else 0.0
    late_pf = float(late["pf"].mean()) if len(late) else 0.0

    if base["pf"] > 1.5 and slip1["pf"] > 1.1 and early_pf >= 1.1 and base_open["pf"] > 1.2:
        practical = "YES — edge survives fill model and early eras (validate live costs)."
    elif base["pf"] > 1.5 and (early_pf < 1.1 or base_open["pf"] < 1.1):
        practical = (
            "CONDITIONAL — close-fill backtest shows strong PF, but edge is regime-heavy "
            "and/or fill-sensitive. Not a stable forever edge; size as discretionary/regime filter."
        )
    elif base["pf"] > 1.2:
        practical = "WEAK — some signal content, not production-grade."
    else:
        practical = "NO — no reliable edge under original test assumptions."

    # Hostile note from prior run
    hostile_note = (
        "Prior hostile next-open + gap-stop-at-entry engine: ~4261 trades, WR~14.5%, PF~0.35, "
        "PnL ~-$238k. That kill-switch is mostly SL_GAP_ENTRY (~37% of trades), not a fair "
        "measure of the original close-fill Inverse ORB design."
    )

    verdict = {
        "close_fill_orb_vwap": base,
        "next_open_orb_vwap": base_open,
        "signal_beats_opposite": bool(base["pf"] > opp["pf"]),
        "signal_beats_random": bool(base["pf"] > rnd["pf"]),
        "orb_adds_vs_vwap_alone": bool(base["pf"] > vwap["pf"] and base["exp"] > vwap["exp"]),
        "vwap_adds_vs_orb_alone": bool(base["pf"] > orb["pf"] and base["exp"] > orb["exp"]),
        "smt_filter_on_orb_vwap": {
            "improves_exp": bool(combo_smt["exp"] > base["exp"]),
            "improves_pf": bool(combo_smt["pf"] > base["pf"]),
            "baseline": base,
            "with_smt": combo_smt,
            "smt_only": smt_only,
        },
        "years_profitable_close_orb_vwap": f"{int((yb['pnl']>0).sum())}/{len(yb)}",
        "early_2010_2018_avg_pf": round(early_pf, 2),
        "late_2022_2026_avg_pf": round(late_pf, 2),
        "slippage_1pt_pf": slip1["pf"],
        "hostile_gap_stop_note": hostile_note,
        "practical_edge_verdict": practical,
    }

    report = {
        "params": dict(orb="15m", wide_mult=1.10, thresh=40, sigma=1.28, sl=15, target_frac=0.20, exit="15:30"),
        "sizing": dict(point_value=POINT_VAL, friction_pts=FRICTION, note="3x MNQ"),
        "summary": rows,
        "slippage": slip_rows,
        "subperiods": sub_rows,
        "verdict": verdict,
    }
    with open(art("edge_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    p("\n" + "=" * 78)
    p(" SUMMARY")
    p("=" * 78)
    p(df_sum.to_string(index=False))
    p("\nSLIPPAGE close ORB+VWAP:")
    p(df_slip.to_string(index=False))
    p("\nSUBPERIODS (close):")
    p(df_sub.to_string(index=False))
    p("\nYEARLY close ORB+VWAP:")
    p(yb.to_string(index=False))
    p("\nVERDICT:")
    p(json.dumps(verdict, indent=2, default=str))
    p("\nSaved artifacts/edge_report.json")


if __name__ == "__main__":
    main()
