"""TradingView-style charts for two frozen 2026 trades, with entry evidence marked."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.gridspec import GridSpec

ART = Path("artifacts") / "charts"
ART.mkdir(parents=True, exist_ok=True)

# Two readable 2026 trades (opposite sides, both actually reached target).
PICKS = [
    dict(day_id="2026-01-20", trade_type="SHORT", entry_time="2026-01-20 14:52:00+00:00"),
    dict(day_id="2026-05-11", trade_type="LONG", entry_time="2026-05-11 14:33:00+00:00"),
]

BG = "#131722"
GRID = "#1e222d"
FG = "#d1d4dc"
MUTED = "#787b86"
UP = "#089981"
DN = "#f23645"
ORB = "#ff9800"
VWAP_C = "#f5d76e"
BAND = "#5b8def"
SMT_C = "#26c6da"
ENTRY_C = "#00e5ff"
SL_C = "#ef5350"
TP_C = "#26a69a"


def load_session() -> pd.DataFrame:
    df = pd.read_parquet("session_cached.parquet")
    df["ts"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert("America/New_York")
    df["day_id"] = df["day_id"].astype(str)
    df["vwap"] = (df["upper1"].astype(float) + df["lower1"].astype(float)) * 0.5
    return df


def orb_history(df: pd.DataFrame) -> pd.DataFrame:
    orb = (
        df[df["ny_minutes"].between(570, 584)]
        .groupby("day_id", sort=False)
        .agg(oh=("high_nq", "max"), ol=("low_nq", "min"), n=("high_nq", "size"))
    )
    orb = orb[orb["n"] >= 15].copy()
    orb["rng"] = orb["oh"] - orb["ol"]
    hist = orb["rng"].tolist()
    sma = []
    for i, r in enumerate(hist):
        prior = hist[max(0, i - 20) : i]
        sma.append(float(np.mean(prior)) if len(prior) >= 5 else 35.0)
    orb["sma20"] = sma
    orb["wide"] = (orb["rng"] > 1.10 * orb["sma20"]) | (orb["rng"] > 40.0)
    return orb


def smt_walk(day: pd.DataFrame) -> dict:
    high_nq = day["high_nq"].to_numpy(np.float64)
    low_nq = day["low_nq"].to_numpy(np.float64)
    high_es = day["high_es"].to_numpy(np.float64)
    low_es = day["low_es"].to_numpy(np.float64)
    upper = day["upper1"].to_numpy(np.float64)
    lower = day["lower1"].to_numpy(np.float64)
    ny = day["ny_minutes"].to_numpy()
    nan = float("nan")
    q1h_n = q1l_n = q1h_e = q1l_e = nan
    q2h_n = q2l_n = q2h_e = q2l_e = nan
    q3h_n = q3l_n = q3h_e = q3l_e = nan
    ch_n = cl_n = ch_e = cl_e = nan
    u1h = u1l = u2h = u2l = u3h = u3l = False
    prev_q = 0
    setup = 0
    setup_i = -1
    events = []
    active = np.zeros(len(day), dtype=np.int8)
    levels = {}

    for i in range(len(day)):
        m = int(ny[i])
        cq = 1 if m < 450 else 2 if m < 540 else 3 if m < 630 else 4
        if cq != prev_q:
            if cq == 2:
                q1h_n, q1l_n, q1h_e, q1l_e = ch_n, cl_n, ch_e, cl_e
                levels["Q1"] = dict(hn=q1h_n, ln=q1l_n, he=q1h_e, le=q1l_e, i=i)
            elif cq == 3:
                q2h_n, q2l_n, q2h_e, q2l_e = ch_n, cl_n, ch_e, cl_e
                levels["Q2"] = dict(hn=q2h_n, ln=q2l_n, he=q2h_e, le=q2l_e, i=i)
            elif cq == 4:
                q3h_n, q3l_n, q3h_e, q3l_e = ch_n, cl_n, ch_e, cl_e
                levels["Q3"] = dict(hn=q3h_n, ln=q3l_n, he=q3h_e, le=q3l_e, i=i)
            ch_n, cl_n, ch_e, cl_e = high_nq[i], low_nq[i], high_es[i], low_es[i]
        else:
            ch_n = max(ch_n, high_nq[i]) if ch_n == ch_n else high_nq[i]
            cl_n = min(cl_n, low_nq[i]) if cl_n == cl_n else low_nq[i]
            ch_e = max(ch_e, high_es[i]) if ch_e == ch_e else high_es[i]
            cl_e = min(cl_e, low_es[i]) if cl_e == cl_e else low_es[i]
        prev_q = cq

        bear = bull = False
        ob, os_ = high_nq[i] >= upper[i], low_nq[i] <= lower[i]
        checks = [
            (2, "Q1", "high", q1h_n, q1h_e, high_nq[i], high_es[i], ob, "u1h"),
            (2, "Q1", "low", q1l_n, q1l_e, low_nq[i], low_es[i], os_, "u1l"),
            (3, "Q2", "high", q2h_n, q2h_e, high_nq[i], high_es[i], ob, "u2h"),
            (3, "Q2", "low", q2l_n, q2l_e, low_nq[i], low_es[i], os_, "u2l"),
            (4, "Q3", "high", q3h_n, q3h_e, high_nq[i], high_es[i], ob, "u3h"),
            (4, "Q3", "low", q3l_n, q3l_e, low_nq[i], low_es[i], os_, "u3l"),
        ]
        used = {"u1h": u1h, "u1l": u1l, "u2h": u2h, "u2l": u2l, "u3h": u3h, "u3l": u3l}
        for need_q, qname, side, qn, qe, nq_px, es_px, extreme, flag in checks:
            if cq < need_q or not (qn == qn) or used[flag]:
                continue
            nq_brk = (nq_px > qn) if side == "high" else (nq_px < qn)
            es_brk = (es_px > qe) if side == "high" else (es_px < qe)
            if (nq_brk ^ es_brk) and extreme:
                if side == "high":
                    bear = True
                else:
                    bull = True
                used[flag] = True
                events.append(
                    dict(
                        i=i,
                        q=qname,
                        side=side,
                        dir="BEAR" if side == "high" else "BULL",
                        qn=float(qn),
                        qe=float(qe),
                        nq_px=float(nq_px),
                        es_px=float(es_px),
                        nq_brk=bool(nq_brk),
                        es_brk=bool(es_brk),
                        ts=day["ts"].iloc[i],
                    )
                )
        u1h, u1l, u2h, u2l, u3h, u3l = (
            used["u1h"], used["u1l"], used["u2h"], used["u2l"], used["u3h"], used["u3l"],
        )
        if bear:
            setup, setup_i = -1, i
        elif bull:
            setup, setup_i = 1, i
        if setup and i - setup_i > 30:
            setup = 0
        active[i] = setup

    return dict(active=active, events=events, levels=levels)


def draw_candles(ax, x, o, h, l, c, width=0.7, alpha=1.0):
    up = c >= o
    dn = ~up
    ax.vlines(x[up], l[up], h[up], color=UP, lw=0.9, alpha=alpha)
    ax.vlines(x[dn], l[dn], h[dn], color=DN, lw=0.9, alpha=alpha)
    body_u = np.maximum(c[up] - o[up], 0.25)
    body_d = np.maximum(o[dn] - c[dn], 0.25)
    ax.bar(x[up], body_u, width=width, bottom=o[up], color=UP, align="center", zorder=3, alpha=alpha)
    ax.bar(x[dn], body_d, width=width, bottom=c[dn], color=DN, align="center", zorder=3, alpha=alpha)


def fmt_px(x: float) -> str:
    return f"{x:,.2f}"


def evidence_text(trade, orb_row, smt_ev, fill_open, signal_ts, exit_px, tp_px) -> str:
    side = trade["trade_type"]
    rng = float(orb_row["rng"])
    sma = float(orb_row["sma20"])
    wide_why = f"{rng:.1f} > 40  or  {rng:.1f} > 1.10 x {sma:.1f} = {1.10 * sma:.1f}"
    from_entry = abs(float(trade["entry_price"]) - tp_px)
    lines = [
        f"{side}   {trade['day_id']}",
        f"{trade['exit_reason']}   {trade['pnl_pts']:+.2f} pts   ${trade['pnl_usd']:+,.0f}",
        "",
        "WHY THIS TRADE FIRED",
        "All four must be true on the signal bar.",
        "",
        f"1  WIDE ORB",
        f"   range {rng:.1f} pts",
        f"   {wide_why}",
        f"   PASS",
        "",
        f"2  ORB TOUCH",
        f"   {'tagged ORB HIGH' if side == 'SHORT' else 'tagged ORB LOW'}",
        f"   H {fmt_px(orb_row['oh'])}   L {fmt_px(orb_row['ol'])}",
        "",
        f"3  VWAP +/- 1.28 sd",
        f"   {'high >= upper band' if side == 'SHORT' else 'low <= lower band'}",
        "",
    ]
    if smt_ev is None:
        lines += ["4  SMT  (active from earlier bar)", "   30-min confirmation window"]
    else:
        who = "NQ" if smt_ev["nq_brk"] else "ES"
        other = "ES" if smt_ev["nq_brk"] else "NQ"
        lines += [
            f"4  SMT {smt_ev['dir']}  {smt_ev['q']} {smt_ev['side']}",
            f"   {who} broke {smt_ev['q']} {smt_ev['side']}",
            f"   {other} did NOT  (divergence)",
            f"   NQ {fmt_px(smt_ev['nq_px'])} vs {fmt_px(smt_ev['qn'])}",
            f"   ES {fmt_px(smt_ev['es_px'])} vs {fmt_px(smt_ev['qe'])}",
            f"   + VWAP extreme on that bar",
        ]
    slip = "open - 1.0" if side == "SHORT" else "open + 1.0"
    lines += [
        "",
        "EXECUTION  (frozen)",
        f"   signal  {signal_ts.strftime('%H:%M')} NY",
        f"   fill    {pd.to_datetime(trade['entry_time']).tz_convert('America/New_York').strftime('%H:%M')} NY",
        f"   next-bar open, slip {slip}",
        f"   fill px {fmt_px(trade['entry_price'])}  (open {fmt_px(fill_open)})",
        "",
        "EXITS  (actual engine)",
        f"   SL = ORB extreme +/- 15",
        f"   TP = opposite ORB inset 20% R",
        f"   NOT entry +/- 20% ORB",
        f"   SHORT: ol+0.20R  LONG: oh-0.20R",
        f"   TP price {fmt_px(tp_px)}",
        f"   distance entry->TP {from_entry:.1f} pts",
        f"   (20% of R is only {0.20 * rng:.1f} inset)",
        f"   exit {fmt_px(exit_px)}  {trade['exit_reason']}",
        f"   realized {trade['pnl_pts']:+.1f} pts",
    ]
    return "\n".join(lines)


def plot_one(df: pd.DataFrame, orb_hist: pd.DataFrame, trade: pd.Series, out_path: Path):
    day = df[df["day_id"] == trade["day_id"]].copy().reset_index(drop=True)
    if len(day) == 0:
        raise SystemExit(f"no session bars for {trade['day_id']}")

    smt = smt_walk(day)
    orb_row = orb_hist.loc[trade["day_id"]]
    oh, ol, rng = float(orb_row["oh"]), float(orb_row["ol"]), float(orb_row["rng"])
    side = trade["trade_type"]
    if side == "SHORT":
        sl, tp = oh + 15.0, ol + 0.20 * rng
        exit_px = float(trade["entry_price"]) - float(trade["pnl_pts"])
        want_smt = -1
    else:
        sl, tp = ol - 15.0, oh - 0.20 * rng
        exit_px = float(trade["entry_price"]) + float(trade["pnl_pts"])
        want_smt = 1

    entry_ts = pd.to_datetime(trade["entry_time"], utc=True).tz_convert("America/New_York")
    exit_ts = pd.to_datetime(trade["exit_time"], utc=True).tz_convert("America/New_York")
    fill_i = int((day["ts"] - entry_ts).abs().values.argmin())
    sig_i = max(fill_i - 1, 0)
    exit_i = int((day["ts"] - exit_ts).abs().values.argmin())
    fill_open = float(day["open_nq"].iloc[fill_i])

    # SMT event that is still active at signal (last event of matching dir within 30 bars)
    smt_ev = None
    for ev in reversed(smt["events"]):
        if ev["dir"] == ("BEAR" if side == "SHORT" else "BULL") and 0 <= sig_i - ev["i"] <= 30:
            smt_ev = ev
            break
    if smt_ev is None and smt["events"]:
        for ev in reversed(smt["events"]):
            if ev["dir"] == ("BEAR" if side == "SHORT" else "BULL"):
                smt_ev = ev
                break

    # Window: a bit before SMT / 08:00 through a bit after exit
    start_min = 480
    if smt_ev is not None:
        start_min = min(start_min, int(day["ny_minutes"].iloc[smt_ev["i"]]) - 20)
    start_min = max(360, start_min)
    end_min = min(720, int(day["ny_minutes"].iloc[exit_i]) + 25)
    vis = day[(day["ny_minutes"] >= start_min) & (day["ny_minutes"] <= end_min)].copy()
    vis = vis.reset_index(drop=True)
    # remap indices into vis
    def remap(i_day: int) -> int:
        ts = day["ts"].iloc[i_day]
        return int((vis["ts"] - ts).abs().values.argmin())

    x = np.arange(len(vis))
    o = vis["open_nq"].to_numpy(float)
    h = vis["high_nq"].to_numpy(float)
    l = vis["low_nq"].to_numpy(float)
    c = vis["close_nq"].to_numpy(float)
    oe = vis["open_es"].to_numpy(float)
    he = vis["high_es"].to_numpy(float)
    le = vis["low_es"].to_numpy(float)
    ce = vis["close_es"].to_numpy(float)

    fig = plt.figure(figsize=(18.5, 10.2), facecolor=BG)
    gs = GridSpec(2, 2, width_ratios=[4.05, 1.28], height_ratios=[3.15, 1.12],
                  hspace=0.08, wspace=0.04, left=0.04, right=0.985, top=0.93, bottom=0.07)
    ax = fig.add_subplot(gs[0, 0])
    ax_es = fig.add_subplot(gs[1, 0], sharex=ax)
    ax_info = fig.add_subplot(gs[:, 1])
    for a in (ax, ax_es, ax_info):
        a.set_facecolor(BG)
        for sp in a.spines.values():
            sp.set_color("#2a2e39")

    draw_candles(ax, x, o, h, l, c, width=0.72)
    draw_candles(ax_es, x, oe, he, le, ce, width=0.72)

    ax.plot(x, vis["vwap"], color=VWAP_C, lw=1.15, zorder=4, label="VWAP")
    ax.plot(x, vis["upper1"], color=BAND, lw=0.95, ls="--", zorder=4)
    ax.plot(x, vis["lower1"], color=BAND, lw=0.95, ls="--", zorder=4)
    ax.fill_between(x, vis["lower1"], vis["upper1"], color=BAND, alpha=0.07, zorder=1)

    orb_mask = vis["ny_minutes"].between(570, 584)
    if orb_mask.any():
        x0, x1 = x[orb_mask.values][0] - 0.5, x[orb_mask.values][-1] + 0.5
        ax.add_patch(Rectangle((x0, ol), x1 - x0, oh - ol, facecolor=ORB, alpha=0.16, zorder=0, edgecolor=ORB, lw=1.1))
        ax.axvline(x0, color=ORB, lw=0.6, alpha=0.7)
        ax.axvline(x1, color=ORB, lw=0.6, alpha=0.7)
        ax.text((x0 + x1) / 2, oh, "  15m ORB  9:30-9:44", color=ORB, fontsize=8.5, va="bottom", ha="center", fontweight="bold")

    ax.axhline(oh, color=ORB, lw=1.0, ls="-")
    ax.axhline(ol, color=ORB, lw=1.0, ls="-")
    ax.axhline(sl, color=SL_C, lw=1.15, ls=":")
    ax.axhline(tp, color=TP_C, lw=1.15, ls=":")
    ax.axhline(float(trade["entry_price"]), color=ENTRY_C, lw=1.15, ls="-")

    labels = [
        (oh, f"ORB H  {fmt_px(oh)}", ORB),
        (ol, f"ORB L  {fmt_px(ol)}", ORB),
        (sl, f"SL  {fmt_px(sl)}", SL_C),
        (tp, f"TP  {fmt_px(tp)}", TP_C),
        (float(trade["entry_price"]), f"ENTRY  {fmt_px(trade['entry_price'])}", ENTRY_C),
    ]
    labels.sort(key=lambda z: z[0])
    ys = [z[0] for z in labels]
    span = max(h.max(), sl, tp, oh) - min(l.min(), sl, tp, ol)
    gap = max(span * 0.035, 12.0)
    placed = [ys[0]]
    for i in range(1, len(ys)):
        placed.append(max(ys[i], placed[-1] + gap))
    for (_, text, color), y in zip(labels, placed):
        ax.text(len(vis) - 1, y, "  " + text, color=color, fontsize=8, va="center", ha="left",
                fontweight="bold", clip_on=False)

    sig_x = remap(sig_i)
    fill_x = remap(fill_i)
    exit_x = remap(exit_i)
    ax.axvspan(sig_x - 0.5, sig_x + 0.5, color=SMT_C, alpha=0.18, zorder=0)
    ax.scatter([fill_x], [trade["entry_price"]], marker="v" if side == "SHORT" else "^",
               s=110, color=ENTRY_C, zorder=6, edgecolor="white", lw=0.5)
    ax.scatter([exit_x], [exit_px], marker="X", s=90, color=TP_C if trade["pnl_pts"] > 0 else SL_C, zorder=6)
    ax.annotate(
        f"SIGNAL\n{vis['ts'].iloc[sig_x].strftime('%H:%M')}\ntouch ORB + VWAP\n+ SMT",
        xy=(sig_x, float(vis["high_nq"].iloc[sig_x]) if side == "SHORT" else float(vis["low_nq"].iloc[sig_x])),
        xytext=(sig_x - max(18, int(0.12 * len(vis))), (oh + sl) / 2 if side == "SHORT" else (ol + sl) / 2),
        color=FG, fontsize=8, ha="right",
        arrowprops=dict(arrowstyle="->", color=SMT_C, lw=1.1),
        bbox=dict(boxstyle="round,pad=0.35", fc="#1b2130", ec=SMT_C, lw=0.8),
    )
    ax.annotate(
        f"{side} IN\n{fmt_px(trade['entry_price'])}",
        xy=(fill_x, trade["entry_price"]),
        xytext=(fill_x + 8, trade["entry_price"] + (25 if side == "LONG" else -25)),
        color=ENTRY_C, fontsize=8.5, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=ENTRY_C, lw=1.0),
    )
    ax.annotate(
        f"EXIT {trade['exit_reason']}\n{fmt_px(exit_px)}\n{trade['pnl_pts']:+.1f} pts",
        xy=(exit_x, exit_px),
        xytext=(min(exit_x + 14, len(vis) - 8), exit_px + (40 if side == "LONG" else -40)),
        color=TP_C if trade["pnl_pts"] > 0 else SL_C, fontsize=8.5, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=TP_C if trade["pnl_pts"] > 0 else SL_C, lw=1.0),
    )

    # SMT marker + swept level on both panes
    if smt_ev is not None:
        sx = remap(smt_ev["i"])
        ax.scatter([sx], [smt_ev["nq_px"]], marker="*", s=160, color=SMT_C, zorder=7, edgecolor="white", lw=0.4)
        ax.axhline(smt_ev["qn"], color=SMT_C, lw=0.9, ls="-.", alpha=0.85)
        ax_es.axhline(smt_ev["qe"], color=SMT_C, lw=0.9, ls="-.", alpha=0.85)
        ax_es.scatter([sx], [smt_ev["es_px"]], marker="*", s=140, color=SMT_C, zorder=7, edgecolor="white", lw=0.4)
        who = "NQ broke, ES did not" if smt_ev["nq_brk"] else "ES broke, NQ did not"
        ax.text(sx, smt_ev["qn"], f"  SMT {smt_ev['dir']} {smt_ev['q']} {smt_ev['side']}\n  {who}",
                color=SMT_C, fontsize=8, va="bottom", fontweight="bold")
        ax_es.text(sx, smt_ev["qe"], f"  ES {smt_ev['q']} {smt_ev['side']}  {fmt_px(smt_ev['qe'])}",
                   color=SMT_C, fontsize=8, va="bottom")

    # trade path shade
    y0, y1 = sorted([float(trade["entry_price"]), exit_px])
    ax.add_patch(Rectangle((fill_x, y0), max(exit_x - fill_x, 0.8), max(y1 - y0, 1),
                           facecolor=TP_C if trade["pnl_pts"] > 0 else SL_C, alpha=0.10, zorder=0))

    ax.set_xlim(-1, len(vis) + 18)
    pad = max((h.max() - l.min()) * 0.08, 20)
    ax.set_ylim(min(l.min(), sl, tp, ol) - pad, max(h.max(), sl, tp, oh) + pad)
    ax_es.set_ylim(le.min() - 4, he.max() + 4)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax_es.tick_params(colors=MUTED, labelsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    ax_es.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    ax.grid(True, color=GRID, lw=0.6)
    ax_es.grid(True, color=GRID, lw=0.6)
    ax.set_ylabel("NQ  1m", color=FG, fontsize=9)
    ax_es.set_ylabel("ES  1m  (SMT)", color=FG, fontsize=9)
    plt.setp(ax.get_xticklabels(), visible=False)

    ticks = list(range(0, len(vis), max(1, len(vis) // 8)))
    ax_es.set_xticks(ticks)
    ax_es.set_xticklabels([vis["ts"].iloc[i].strftime("%H:%M") for i in ticks], color=MUTED, fontsize=8)
    ax_es.set_xlabel("New York time", color=MUTED, fontsize=8)

    ny_day = vis["ts"].iloc[0].strftime("%A  %b %d, %Y")
    ax.set_title(
        f"NQ  {ny_day}     {side}     next-bar open + 1pt slip     "
        f"ORB {rng:.1f} pts  (SMA20 {float(orb_row['sma20']):.1f})     "
        f"{trade['exit_reason']}  {trade['pnl_pts']:+.1f} pts",
        color=FG, fontsize=12, loc="left", pad=10, fontweight="bold",
    )

    # evidence card
    ax_info.set_xticks([])
    ax_info.set_yticks([])
    ax_info.set_xlim(0, 1)
    ax_info.set_ylim(0, 1)
    card = FancyBboxPatch((0.04, 0.02), 0.92, 0.96, boxstyle="round,pad=0.02,rounding_size=0.02",
                          facecolor="#0f131b", edgecolor="#2a2e39", lw=1.0, transform=ax_info.transAxes)
    ax_info.add_patch(card)
    txt = evidence_text(trade, orb_row, smt_ev, fill_open, vis["ts"].iloc[sig_x], exit_px, tp)
    ax_info.text(0.10, 0.97, txt, va="top", ha="left", family="Consolas", fontsize=8.1,
                 color=FG, transform=ax_info.transAxes, linespacing=1.28)

    legend_els = [
        Line2D([0], [0], color=VWAP_C, lw=1.3, label="VWAP"),
        Line2D([0], [0], color=BAND, lw=1.1, ls="--", label="VWAP +/- 1.28 sd"),
        Line2D([0], [0], color=ORB, lw=1.3, label="ORB high / low"),
        Line2D([0], [0], color=ENTRY_C, lw=1.3, label="Entry (w/ slip)"),
        Line2D([0], [0], color=SL_C, lw=1.2, ls=":", label="Stop  (ORB +/- 15)"),
        Line2D([0], [0], color=TP_C, lw=1.2, ls=":", label="TP  (opp. ORB -/+ 20% R)"),
        Line2D([0], [0], color=SMT_C, marker="*", lw=0, markersize=10, label="SMT divergence"),
    ]
    ax.legend(handles=legend_els, loc="upper left", frameon=True, facecolor="#0f131b",
              edgecolor="#2a2e39", labelcolor=FG, fontsize=8, ncol=2)

    fig.savefig(out_path, dpi=160, facecolor=BG)
    plt.close(fig)
    print(f"saved {out_path}", flush=True)


def main():
    print("loading session cache...", flush=True)
    df = load_session()
    print("building ORB history...", flush=True)
    ohist = orb_history(df)
    trades = pd.read_csv(ART.parent / "regime_trades_enriched.csv")
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    for pick in PICKS:
        et = pd.to_datetime(pick["entry_time"], utc=True)
        hit = trades[
            (trades["day_id"] == pick["day_id"])
            & (trades["trade_type"] == pick["trade_type"])
            & (trades["entry_time"] == et)
        ]
        if hit.empty:
            raise SystemExit(f"trade not found: {pick}")
        tr = hit.iloc[0]
        name = f"trade_{pick['day_id']}_{pick['trade_type']}.png"
        plot_one(df, ohist, tr, ART / name)


if __name__ == "__main__":
    main()
