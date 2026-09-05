"""
Exit-reason + same-bar forensic for frozen 20% opposite-ORB target book.

Classifies every trade and stress-tests:
  - through-stop fills (entry already beyond ORB-extreme stop)
  - same-bar SL+TP ambiguity (engine is pessimistic: SL_SAME)
  - optimistic same-bar (TP first) and cancel-on-ambiguity
"""
from __future__ import annotations

from common.paths import art

import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_orb_vwap_smt_edge_report import ART, FRICTION, POINT_VAL, compute_smt_active, load, metrics, p
from run_regime_validation import ENTRY_SLIP, extended_backtest, extended_metrics, build_daily_features

ORB_PCT = 0.8452380952380952
TARGET_FRAC = 0.20
SL_PTS = 15.0
OUT = art("exit_forensic_report.json")
OUT_CSV = art("exit_forensic_trades.csv")
OUT_TABLE = art("exit_forensic_tables.csv")


def pf_of(g: pd.DataFrame) -> float:
    if len(g) == 0:
        return 0.0
    gp = float(g.loc[g["pnl_usd"] > 0, "pnl_usd"].sum())
    gl = abs(float(g.loc[g["pnl_usd"] <= 0, "pnl_usd"].sum()))
    return round(gp / gl, 2) if gl > 0 else (0.0 if gp == 0 else float("inf"))


def row_metrics(g: pd.DataFrame, total_pnl: float | None = None) -> dict:
    if len(g) == 0:
        return dict(trades=0, pct=0.0, pnl=0.0, pf=0.0, avg=0.0, wr=0.0)
    m = metrics(g)
    pct = round(100 * len(g) / total_pnl, 1) if total_pnl and total_pnl > 0 else 0.0
    # total_pnl arg misused — pass n_total separately
    return dict(
        trades=int(len(g)),
        pnl=round(float(g["pnl_usd"].sum()), 2),
        pf=m["pf"],
        avg=round(float(g["pnl_usd"].mean()), 2),
        wr=m["wr"],
    )


def classify_book(trades: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Attach ORB levels, stop/target, geometry flags, same-bar flags."""
    day_orb = (
        df[df["ny_minutes"].between(570, 584)]
        .groupby("day_id")
        .agg(orb_hi=("high_nq", "max"), orb_lo=("low_nq", "min"), n=("high_nq", "size"))
    )
    day_orb = day_orb[day_orb["n"] >= 15].copy()
    day_orb["orb_r"] = day_orb["orb_hi"] - day_orb["orb_lo"]

    t = trades.copy()
    t["day_id"] = t["day_id"].astype(str)
    t = t.merge(day_orb[["orb_hi", "orb_lo", "orb_r"]], left_on="day_id", right_index=True, how="left")

    # Structural levels
    is_short = t["trade_type"] == "SHORT"
    t["stop_px"] = np.where(is_short, t["orb_hi"] + SL_PTS, t["orb_lo"] - SL_PTS)
    t["tp_px"] = np.where(
        is_short,
        t["orb_lo"] + TARGET_FRAC * t["orb_r"],
        t["orb_hi"] - TARGET_FRAC * t["orb_r"],
    )
    t["risk_from_entry"] = np.where(
        is_short,
        t["stop_px"] - t["entry_price"],
        t["entry_price"] - t["stop_px"],
    )
    t["reward_to_tp"] = np.where(
        is_short,
        t["entry_price"] - t["tp_px"],
        t["tp_px"] - t["entry_price"],
    )
    # Through-stop: entry already on the wrong side of stop (favorable if stopped immediately)
    t["through_stop_at_entry"] = t["risk_from_entry"] <= 0

    # Join exit bar OHLC
    bars = df[["ts_event", "open_nq", "high_nq", "low_nq", "close_nq", "day_id"]].copy()
    bars["ts_event"] = pd.to_datetime(bars["ts_event"], utc=True)
    t["entry_time"] = pd.to_datetime(t["entry_time"], utc=True)
    t["exit_time"] = pd.to_datetime(t["exit_time"], utc=True)

    ent = bars.rename(
        columns={
            "ts_event": "entry_time",
            "open_nq": "fill_open",
            "high_nq": "fill_high",
            "low_nq": "fill_low",
            "close_nq": "fill_close",
        }
    )
    t = t.merge(
        ent[["entry_time", "fill_open", "fill_high", "fill_low", "fill_close"]],
        on="entry_time",
        how="left",
    )
    ex = bars.rename(
        columns={
            "ts_event": "exit_time",
            "open_nq": "exit_open",
            "high_nq": "exit_high",
            "low_nq": "exit_low",
            "close_nq": "exit_close",
        }
    )
    t = t.merge(
        ex[["exit_time", "exit_open", "exit_high", "exit_low", "exit_close"]],
        on="exit_time",
        how="left",
    )

    # Did exit bar contain both stop and target?
    t["exit_bar_hits_stop"] = np.where(
        is_short,
        t["exit_high"] >= t["stop_px"],
        t["exit_low"] <= t["stop_px"],
    )
    t["exit_bar_hits_tp"] = np.where(
        is_short,
        t["exit_low"] <= t["tp_px"],
        t["exit_high"] >= t["tp_px"],
    )
    t["same_bar_ambiguous"] = t["exit_bar_hits_stop"] & t["exit_bar_hits_tp"]
    t["exit_on_fill_bar"] = t["entry_time"] == t["exit_time"]

    # Classification
    def classify(r):
        er = r["exit_reason"]
        if er == "TP":
            return "structural_TP"
        if er == "SESSION":
            return "session_time"
        if er == "SL_SAME":
            return "same_bar_SL_pessimistic"
        if er in ("SL", "SL_SAME"):
            if r["through_stop_at_entry"]:
                return "favorable_through_stop"
            if r["same_bar_ambiguous"]:
                return "same_bar_ambiguous_labeled_SL"
            if r["pnl_usd"] > 0:
                return "stop_but_profitable_other"
            return "adverse_stop"
        return "other"

    t["exit_class"] = t.apply(classify, axis=1)
    return t


def table_for(t: pd.DataFrame, label: str) -> list[dict]:
    n = len(t)
    tot = float(t["pnl_usd"].sum()) if n else 0.0
    rows = []
    order = [
        "structural_TP",
        "adverse_stop",
        "favorable_through_stop",
        "same_bar_SL_pessimistic",
        "same_bar_ambiguous_labeled_SL",
        "stop_but_profitable_other",
        "session_time",
        "other",
    ]
    for cls in order:
        g = t[t["exit_class"] == cls]
        if len(g) == 0:
            continue
        m = metrics(g)
        rows.append(
            dict(
                book=label,
                exit_class=cls,
                trades=int(len(g)),
                pct_trades=round(100 * len(g) / n, 1),
                pnl=round(float(g["pnl_usd"].sum()), 2),
                pct_pnl=round(100 * float(g["pnl_usd"].sum()) / tot, 1) if tot else 0.0,
                pf=m["pf"],
                avg=round(float(g["pnl_usd"].mean()), 2),
                wr=m["wr"],
            )
        )
    # also raw exit_reason rollup
    for er, g in t.groupby("exit_reason"):
        rows.append(
            dict(
                book=label,
                exit_class=f"raw_{er}",
                trades=int(len(g)),
                pct_trades=round(100 * len(g) / n, 1),
                pnl=round(float(g["pnl_usd"].sum()), 2),
                pct_pnl=round(100 * float(g["pnl_usd"].sum()) / tot, 1) if tot else 0.0,
                pf=metrics(g)["pf"],
                avg=round(float(g["pnl_usd"].mean()), 2),
                wr=metrics(g)["wr"],
            )
        )
    return rows


def stress_backtest(df, smt, mode: str) -> pd.DataFrame:
    """
    mode:
      baseline          — current engine
      reject_through    — skip fill if open already through stop
      clip_through      — if open through stop, fill at stop (0 risk/0 reward scratch-ish)
      same_bar_optimistic — both hit -> TP
      same_bar_cancel   — both hit -> flat at entry (0 pts before friction)
    """
    high = df["high_nq"].to_numpy(np.float64)
    low = df["low_nq"].to_numpy(np.float64)
    close = df["close_nq"].to_numpy(np.float64)
    opn = df["open_nq"].to_numpy(np.float64)
    upper = df["upper1"].to_numpy(np.float64)
    lower = df["lower1"].to_numpy(np.float64)
    ny = df["ny_minutes"].to_numpy()
    years = df["year"].to_numpy()
    ts = df["ts_event"].to_numpy()
    day = df["day_id"].to_numpy()
    splits = np.where(day[:-1] != day[1:])[0] + 1
    bounds = np.concatenate(([0], splits, [len(df)]))

    trades = []
    orb_hist = []
    for di in range(len(bounds) - 1):
        s, e = int(bounds[di]), int(bounds[di + 1])
        if years[s] < 2010 or years[s] > 2026:
            continue
        orb_bars = [k for k in range(s, e) if 570 <= ny[k] < 585]
        if len(orb_bars) < 15:
            continue
        oh = max(high[k] for k in orb_bars)
        ol = min(low[k] for k in orb_bars)
        rng_orb = oh - ol
        avg = float(np.mean(orb_hist[-20:])) if len(orb_hist) >= 5 else 35.0
        orb_hist.append(rng_orb)
        if not (rng_orb > 1.10 * avg or rng_orb > 40.0):
            continue

        pos = 0
        ep = stop = tgt = 0.0
        tt = ""
        pending = None
        n_day = 0
        eb = -1

        for i in [k for k in range(s, e) if ny[k] >= 585]:
            if pending and pos == 0:
                side = -1 if pending == "S" else 1
                stop_i = oh + SL_PTS if side == -1 else ol - SL_PTS
                tgt_i = ol + TARGET_FRAC * rng_orb if side == -1 else oh - TARGET_FRAC * rng_orb
                raw_ep = opn[i] + ENTRY_SLIP * side
                # through-stop handling
                through = (side == -1 and raw_ep >= stop_i) or (side == 1 and raw_ep <= stop_i)
                if through and mode == "reject_through":
                    pending = None
                    continue
                if through and mode == "clip_through":
                    ep = stop_i
                else:
                    ep = raw_ep
                pos = side
                stop, tgt = stop_i, tgt_i
                tt = "SHORT" if side == -1 else "LONG"
                eb = i
                pending = None
                n_day += 1

            if ny[i] >= 930:
                if pos:
                    pnl = (close[i] - ep) if pos == 1 else (ep - close[i])
                    trades.append(dict(
                        entry_time=ts[eb], exit_time=ts[i], trade_type=tt,
                        entry_price=ep, pnl_pts=pnl, year=int(years[i]),
                        exit_reason="SESSION", orb_range=rng_orb, day_id=str(day[s]),
                    ))
                    pos = 0
                break

            if pos:
                xp = reason = None
                if pos == 1:
                    hsl, htp = low[i] <= stop, high[i] >= tgt
                    if hsl and htp:
                        if mode == "same_bar_optimistic":
                            xp, reason = tgt, "TP_SAME"
                        elif mode == "same_bar_cancel":
                            xp, reason = ep, "CANCEL_SAME"
                        else:
                            xp, reason = stop, "SL_SAME"
                    elif hsl:
                        xp, reason = stop, "SL"
                    elif htp:
                        xp, reason = tgt, "TP"
                    if xp is not None:
                        trades.append(dict(
                            entry_time=ts[eb], exit_time=ts[i], trade_type=tt,
                            entry_price=ep, pnl_pts=xp - ep, year=int(years[i]),
                            exit_reason=reason, orb_range=rng_orb, day_id=str(day[s]),
                        ))
                        pos = 0
                else:
                    hsl, htp = high[i] >= stop, low[i] <= tgt
                    if hsl and htp:
                        if mode == "same_bar_optimistic":
                            xp, reason = tgt, "TP_SAME"
                        elif mode == "same_bar_cancel":
                            xp, reason = ep, "CANCEL_SAME"
                        else:
                            xp, reason = stop, "SL_SAME"
                    elif hsl:
                        xp, reason = stop, "SL"
                    elif htp:
                        xp, reason = tgt, "TP"
                    if xp is not None:
                        trades.append(dict(
                            entry_time=ts[eb], exit_time=ts[i], trade_type=tt,
                            entry_price=ep, pnl_pts=ep - xp, year=int(years[i]),
                            exit_reason=reason, orb_range=rng_orb, day_id=str(day[s]),
                        ))
                        pos = 0

            if pos == 0 and n_day < 2 and pending is None:
                sc = (high[i] >= oh) and (high[i] >= upper[i]) and (smt[i] == -1)
                lc = (low[i] <= ol) and (low[i] <= lower[i]) and (smt[i] == 1)
                if sc:
                    pending = "S"
                elif lc:
                    pending = "L"

    t = pd.DataFrame(trades)
    if len(t):
        t["pnl_usd"] = t["pnl_pts"] * POINT_VAL - FRICTION * POINT_VAL
        t["entry_time"] = pd.to_datetime(t["entry_time"], utc=True)
    return t


def summarize_stress(t: pd.DataFrame, daily: pd.DataFrame, name: str) -> dict:
    if len(t) == 0:
        return dict(mode=name, OOS={}, OOS_orb={}, live_2026_orb={})
    feat = daily[["session_date", "orb_pct_252"]].copy()
    feat["session_date"] = pd.to_datetime(feat["session_date"]).dt.date
    t = t.copy()
    t["session_date"] = pd.to_datetime(t["day_id"]).dt.date
    t = t.merge(feat, on="session_date", how="left")
    oos = t[t["year"] >= 2024]
    oos_orb = oos[oos["orb_pct_252"] >= ORB_PCT]
    y26 = t[(t["year"] == 2026) & (t["orb_pct_252"] >= ORB_PCT)]
    return dict(
        mode=name,
        OOS=extended_metrics(oos),
        OOS_orb=extended_metrics(oos_orb),
        live_2026_orb=extended_metrics(y26),
        exit_reasons=t["exit_reason"].value_counts().to_dict(),
    )


def main():
    p("=" * 78)
    p(" EXIT FORENSIC — frozen 20% opposite-ORB target")
    p(" Same-bar rule in engine: BOTH hit -> SL (pessimistic SL_SAME)")
    p("=" * 78)

    # Use existing frozen book
    trades = pd.read_csv(art("regime_trades_enriched.csv"))
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["exit_time"] = pd.to_datetime(trades["exit_time"], utc=True)

    df = load()
    df["day_id"] = df["day_id"].astype(str)
    daily = build_daily_features()

    p("Classifying trade geometry...")
    t = classify_book(trades, df)
    t.to_csv(OUT_CSV, index=False)

    books = {
        "ALL": t,
        "IS": t[t["year"] <= 2023],
        "OOS": t[t["year"] >= 2024],
        "OOS_orb_gate": t[(t["year"] >= 2024) & (t["orb_pct_252"] >= ORB_PCT)],
        "live_2026_orb": t[(t["year"] == 2026) & (t["orb_pct_252"] >= ORB_PCT)],
    }

    tables = []
    for name, g in books.items():
        p(f"\n--- {name} N={len(g)} ---")
        rows = table_for(g, name)
        tables.extend(rows)
        for r in rows:
            if r["exit_class"].startswith("raw_"):
                continue
            p(
                f"  {r['exit_class']:32s} N={r['trades']:4d} ({r['pct_trades']:5.1f}%)  "
                f"PnL=${r['pnl']:10,.0f} ({r['pct_pnl']:5.1f}%)  PF={r['pf']:5.2f}  avg=${r['avg']:7.2f}"
            )

    pd.DataFrame(tables).to_csv(OUT_TABLE, index=False)

    # Critical geometry stats
    oos = books["OOS_orb_gate"]
    geom = {
        "oos_orb_through_stop_pct": round(100 * oos["through_stop_at_entry"].mean(), 1) if len(oos) else 0,
        "oos_orb_exit_on_fill_bar_pct": round(100 * oos["exit_on_fill_bar"].mean(), 1) if len(oos) else 0,
        "oos_orb_same_bar_ambiguous_pct": round(100 * oos["same_bar_ambiguous"].mean(), 1) if len(oos) else 0,
        "oos_orb_same_bar_ambiguous_n": int(oos["same_bar_ambiguous"].sum()) if len(oos) else 0,
        "oos_orb_med_risk_from_entry": round(float(oos["risk_from_entry"].median()), 2) if len(oos) else 0,
        "oos_orb_med_reward_to_tp": round(float(oos["reward_to_tp"].median()), 2) if len(oos) else 0,
        "engine_same_bar_rule": "If stop AND target both inside bar high/low -> exit at STOP (pessimistic). Label SL_SAME.",
        "note_no_SL_SAME_in_csv": int((t["exit_reason"] == "SL_SAME").sum()),
    }
    p("\nGEOMETRY (OOS ORB gate):")
    for k, v in geom.items():
        p(f"  {k}: {v}")

    # Stress suite
    p("\nRunning stress backtests (same entries/rules, alternate exit/fill handling)...")
    smt = compute_smt_active(df)
    stress_modes = [
        "baseline",
        "reject_through",
        "clip_through",
        "same_bar_optimistic",
        "same_bar_cancel",
    ]
    stress = []
    for mode in stress_modes:
        p(f"  mode={mode}...")
        bt = stress_backtest(df, smt, mode)
        s = summarize_stress(bt, daily, mode)
        stress.append(s)
        o = s["OOS_orb"]
        p(
            f"    OOS_orb N={o.get('trades', 0)} PF={o.get('pf', 0)} exp=${o.get('exp', 0)} "
            f"PnL=${o.get('pnl', 0):,} MDD=${o.get('mdd', 0)}"
        )

    # PnL attribution headline
    oos_rows = [r for r in tables if r["book"] == "OOS_orb_gate" and not r["exit_class"].startswith("raw_")]
    tp_pnl = next((r["pnl"] for r in oos_rows if r["exit_class"] == "structural_TP"), 0)
    thru_pnl = next((r["pnl"] for r in oos_rows if r["exit_class"] == "favorable_through_stop"), 0)
    adv_pnl = next((r["pnl"] for r in oos_rows if r["exit_class"] == "adverse_stop"), 0)
    tot = float(oos["pnl_usd"].sum()) if len(oos) else 1.0

    if thru_pnl / tot > 0.5:
        verdict = (
            "CRITICAL — majority of OOS gated PnL comes from favorable through-stop "
            "fills (entry already beyond ORB+/-15), not from structural cross-ORB TP. "
            "Treat reported PF as contaminated by fill geometry until reject/clip stress is adopted."
        )
    elif tp_pnl / tot < 0.25 and thru_pnl / tot > 0.25:
        verdict = (
            "MATERIAL — structural TP is a minority of PnL; through-stop and other "
            "non-TP exits dominate. Edge hypothesis should be reframed toward short-horizon "
            "exhaustion after extreme+VWAP+SMT, with hard rules for through-stop fills."
        )
    else:
        verdict = (
            "Structural TP contributes meaningfully; still review through-stop share "
            "and same-bar policy before production."
        )

    report = {
        "frozen": {
            "target": "opposite ORB extreme inset 20% R",
            "stop": "15-point ORB-extreme stop",
            "orb_pct_gate": ORB_PCT,
        },
        "geometry": geom,
        "tables": tables,
        "stress": stress,
        "oos_orb_pnl_share": {
            "structural_TP": round(100 * tp_pnl / tot, 1),
            "favorable_through_stop": round(100 * thru_pnl / tot, 1),
            "adverse_stop": round(100 * adv_pnl / tot, 1),
        },
        "verdict": verdict,
    }
    with open(OUT, "w") as f:
        json.dump(report, f, indent=2, default=str)

    p("\n" + "=" * 78)
    p(" VERDICT")
    p("=" * 78)
    p(verdict)
    p(f"Saved {OUT}")
    p(f"Saved {OUT_CSV}")
    p(f"Saved {OUT_TABLE}")
    return report


if __name__ == "__main__":
    main()
