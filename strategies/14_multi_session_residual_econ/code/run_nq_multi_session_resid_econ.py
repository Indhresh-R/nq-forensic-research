"""
NQ Multi-session Residual Economics (Phase B) — Strategy 14

Direction-neutral. Question:
  After HIGH activates, is remaining unsigned excursion from next open large
  enough vs realistic costs to be tradeable — vs LOW / break-even?

Frozen:
  HIGH/LOW from strategy 12 IS terciles (rng_psr)
  Costs: tight=0.50, mid=1.00, wide=2.00 pts RT
  Horizons: 15, 30, 45
  Entry: next bar open; stress delay1
  Sessions independent; report order LONDON → NY_PM → NY_AM → ASIA

NO direction. NO stop/target mining. NO tercile retuning.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import art, load_nq, rate_of
from common.sessions import (
    SESSION_DECISION_OFFSETS,
    SESSION_START,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_PRIORITY = ("LONDON", "NY_PM", "NY_AM", "ASIA")
HORIZONS = (15, 30, 45)
PRIMARY_H = 30
COST_PTS = {"tight": 0.50, "mid": 1.00, "wide": 2.00}
PRIMARY_COST = "mid"
STRUCT_FRAC = 0.25

GATE = json.loads(art("frozen_multi_session_gate.json").read_text(encoding="utf-8"))
THRESH = json.loads(art("nq_multi_sess_opp_thresholds_IS.json").read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]


def th_rng(session: str, off: int) -> dict[str, float] | None:
    d = STATE_TH.get(session, {}).get(str(off)) or STATE_TH.get(session, {}).get(off)
    if not d:
        return None
    return d.get("rng_psr")


def regime_of(session: str, off: int, rng_psr: float) -> str:
    t = th_rng(session, off)
    if not t:
        return "MID"
    if float(rng_psr) >= float(t["p66"]):
        return "HIGH"
    if float(rng_psr) <= float(t["p33"]):
        return "LOW"
    return "MID"


def after_bars(sess: pd.DataFrame, T_ny: int, session: str) -> pd.DataFrame:
    if session == "ASIA":
        ord_T = T_ny if T_ny >= SESSION_START else T_ny + 24 * 60
        ord_key = np.where(
            sess["ny_min"].to_numpy(np.int64) >= SESSION_START,
            sess["ny_min"].to_numpy(np.int64),
            sess["ny_min"].to_numpy(np.int64) + 24 * 60,
        )
        return sess.loc[ord_key > ord_T].reset_index(drop=True)
    return sess[sess["ny_min"] > T_ny].reset_index(drop=True)


def residual_from(
    after: pd.DataFrame, entry_delay: int, horizons: tuple[int, ...]
) -> dict[str, float] | None:
    need = entry_delay + max(horizons)
    if len(after) < need:
        return None
    entry = float(after.iloc[entry_delay]["open"])
    out: dict[str, float] = {"entry": entry}
    highs = after["high"].to_numpy(float)
    lows = after["low"].to_numpy(float)
    start = entry_delay
    for H in horizons:
        sl = slice(start, start + H)
        hh, ll = highs[sl], lows[sl]
        if len(hh) < H:
            out[f"resid_pts_{H}"] = np.nan
            continue
        mx = max(float(hh.max() - entry), float(entry - ll.min()))
        out[f"resid_pts_{H}"] = mx
    return out


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pts(x: Any) -> str:
    return f"{x:.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pp(x: Any) -> str:
    return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== Strategy 14: Multi-session Residual Economics (Phase B) ===", flush=True)
    print(f"Costs={COST_PTS}; H={HORIZONS}; primary H={PRIMARY_H}", flush=True)

    df = load_nq()
    facts = build_session_facts(df)
    facts_map = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}

    sess_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=False):
        for name in SESSION_PRIORITY:
            key = (sd, name)
            if key not in facts_map:
                continue
            bars = bars_in_session(g, name)
            if len(bars) >= 40:
                sess_bars[key] = bars

    rows: list[dict] = []
    n_done = 0
    for (sd, name), bars in sess_bars.items():
        fr = facts_map[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        for off in SESSION_DECISION_OFFSETS[name]:
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars,
                session=name,
                T_ny=T,
                session_open=session_open,
                psr=psr,
            )
            if st is None:
                continue
            reg = regime_of(name, off, float(st["rng_psr"]))
            after = after_bars(bars, T, name)
            # pre-excursion from session open to T (latency context)
            pre = float(st["abs_move_psr"]) * psr
            for delay_name, delay in (("next_open", 0), ("delay1", 1)):
                res = residual_from(after, delay, HORIZONS)
                if res is None:
                    continue
                row: dict[str, Any] = {
                    "session_date": str(sd),
                    "session": name,
                    "year": year,
                    "split": split,
                    "T_offset": off,
                    "regime": reg,
                    "psr": psr,
                    "rng_psr": float(st["rng_psr"]),
                    "pre_exc_pts": pre,
                    "pre_exc_psr": float(st["abs_move_psr"]),
                    "entry_mode": delay_name,
                }
                for H in HORIZONS:
                    rpts = res[f"resid_pts_{H}"]
                    row[f"resid_pts_{H}"] = rpts
                    row[f"resid_psr_{H}"] = (
                        rpts / psr if np.isfinite(rpts) and psr > 0 else np.nan
                    )
                    row[f"struct_{H}"] = (
                        1.0
                        if np.isfinite(rpts) and rpts >= STRUCT_FRAC * psr
                        else (0.0 if np.isfinite(rpts) else np.nan)
                    )
                    for cname, cpts in COST_PTS.items():
                        row[f"cover_{cname}_{H}"] = (
                            1.0
                            if np.isfinite(rpts) and rpts >= cpts
                            else (0.0 if np.isfinite(rpts) else np.nan)
                        )
                        row[f"net_{cname}_{H}"] = (
                            rpts - cpts if np.isfinite(rpts) else np.nan
                        )
                        # R vs break-even (cost as 1R unit for econ framing)
                        row[f"netR_{cname}_{H}"] = (
                            (rpts - cpts) / cpts if np.isfinite(rpts) and cpts > 0 else np.nan
                        )
                rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, panel={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel_path = art("nq_multi_sess_resid_panel.parquet")
    panel.to_parquet(panel_path, index=False)
    print(f"Panel rows: {len(panel)} -> {panel_path}", flush=True)
    if panel.empty:
        raise SystemExit("Empty residual panel")

    results: list[dict[str, Any]] = []
    for sess in SESSION_PRIORITY:
        for delay_name in ("next_open", "delay1"):
            for H in HORIZONS:
                for split in ("IS", "Validation", "OOS", "Y2025", "Y2026"):
                    if split.startswith("Y"):
                        base = panel[
                            (panel["session"] == sess)
                            & (panel["entry_mode"] == delay_name)
                            & (panel["year"] == int(split[1:]))
                        ]
                    else:
                        base = panel[
                            (panel["session"] == sess)
                            & (panel["entry_mode"] == delay_name)
                            & (panel["split"] == split)
                        ]
                    if len(base) < 20:
                        continue
                    for reg in ("HIGH", "LOW", "ALL"):
                        sub = base if reg == "ALL" else base[base["regime"] == reg]
                        if len(sub) < 15:
                            continue
                        col = f"resid_pts_{H}"
                        rr = sub[col].to_numpy(float)
                        rr = rr[np.isfinite(rr)]
                        if len(rr) < 15:
                            continue
                        row: dict[str, Any] = {
                            "session": sess,
                            "entry_mode": delay_name,
                            "horizon": H,
                            "split": split,
                            "regime": reg,
                            "n": int(len(rr)),
                            "mean_resid": float(np.mean(rr)),
                            "median_resid": float(np.median(rr)),
                            "p_struct": float(np.mean(sub[f"struct_{H}"].dropna())),
                            "mean_pre_exc": float(np.nanmean(sub["pre_exc_pts"])),
                            "mean_pre_psr": float(np.nanmean(sub["pre_exc_psr"])),
                        }
                        for cname, cpts in COST_PTS.items():
                            cover = rate_of(sub[f"cover_{cname}_{H}"])
                            net = sub[f"net_{cname}_{H}"].to_numpy(float)
                            net = net[np.isfinite(net)]
                            netR = sub[f"netR_{cname}_{H}"].to_numpy(float)
                            netR = netR[np.isfinite(netR)]
                            row[f"cover_{cname}"] = cover["rate"]
                            row[f"mean_net_{cname}"] = float(np.mean(net)) if len(net) else np.nan
                            row[f"mean_netR_{cname}"] = float(np.mean(netR)) if len(netR) else np.nan
                            row[f"p_net_pos_{cname}"] = (
                                float(np.mean(net > 0)) if len(net) else np.nan
                            )
                            row[f"breakeven_pts"] = cpts  # last write ok; also store per
                        results.append(row)

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_multi_sess_resid_results.csv"), index=False)

    def get(
        sess: str,
        reg: str,
        split: str,
        H: int = PRIMARY_H,
        delay: str = "next_open",
    ) -> dict[str, Any]:
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["regime"] == reg)
            & (res_df["split"] == split)
            & (res_df["horizon"] == H)
            & (res_df["entry_mode"] == delay)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    def verdict_session(sess: str) -> str:
        """Net residual econ gate (direction-neutral)."""
        h_is = get(sess, "HIGH", "IS")
        h_val = get(sess, "HIGH", "Validation")
        h_oos = get(sess, "HIGH", "OOS")
        l_oos = get(sess, "LOW", "OOS")
        if not h_is or not h_oos:
            return "INCONCLUSIVE"
        # lift vs LOW on cover mid
        lift_oos = (
            h_oos.get("cover_mid", np.nan) - l_oos.get("cover_mid", np.nan)
            if l_oos
            else np.nan
        )
        net_is = h_is.get("mean_net_mid", np.nan)
        net_val = h_val.get("mean_net_mid", np.nan)
        net_oos = h_oos.get("mean_net_mid", np.nan)
        # Gross opportunity exists but net?
        if not (np.isfinite(net_oos) and net_oos > 0):
            if np.isfinite(h_oos.get("mean_resid", np.nan)) and h_oos["mean_resid"] > COST_PTS["mid"]:
                # mean resid above cost but mean_net should then be >0 — if not, data issue
                pass
            return "REJECT_COSTS_OR_FLAT"
        if not (np.isfinite(net_is) and net_is > 0 and np.isfinite(net_val) and net_val > 0):
            return "REJECT_IS_ONLY" if (np.isfinite(net_is) and net_is > 0) else "NO_TRADE"
        y25 = get(sess, "HIGH", "Y2025")
        y26 = get(sess, "HIGH", "Y2026")
        year_ok = (
            y25
            and y26
            and y25.get("n", 0) >= 20
            and y26.get("n", 0) >= 20
            and y25.get("mean_net_mid", -1) > 0
            and y26.get("mean_net_mid", -1) > 0
        )
        # Require some lift vs LOW on OOS cover (not just absolute)
        if np.isfinite(lift_oos) and lift_oos < 0.02:
            return "NO_EDGE_VS_LOW"
        if year_ok and np.isfinite(lift_oos) and lift_oos >= 0.05:
            return "STRONG_CANDIDATE"
        if np.isfinite(lift_oos) and lift_oos >= 0.02:
            return "PROMISING"
        return "PROMISING_WEAK_LIFT"

    lines = [
        "# Strategy 14 — Multi-session Residual Economics (Phase B)",
        "",
        "## Freeze",
        "",
        f"- Residual = max(MFE, MAE) from entry over H; entry = next open (stress delay1)",
        f"- Costs RT pts: {COST_PTS}",
        f"- Primary: H={PRIMARY_H}, cost={PRIMARY_COST}",
        f"- HIGH/LOW: frozen IS `rng_psr` terciles from strategy 12",
        f"- Sessions independent; order: {' → '.join(SESSION_PRIORITY)}",
        "",
        "## Stack (conceptual)",
        "",
        "```text",
        "Gross residual opportunity",
        "     − spread/slippage/fees (cost scenarios)",
        "     − entry delay stress",
        "     → Net residual / Net R vs break-even",
        "     → OOS stability + HIGH vs LOW lift",
        "```",
        "",
        "## Primary (HIGH, next_open, H30, mid cost)",
        "",
        "| Session | Split | n | Mean resid | Cover mid | Mean net | Mean netR | P(net>0) | Pre-exc pts |",
        "|---------|-------|---|------------|-----------|----------|-----------|----------|-------------|",
    ]

    verdicts = []
    for sess in SESSION_PRIORITY:
        for split in ("IS", "Validation", "OOS"):
            h = get(sess, "HIGH", split)
            if not h:
                lines.append(f"| {sess} | {split} | — | — | — | — | — | — | — |")
                continue
            lines.append(
                f"| {sess} | {split} | {h['n']} | {pts(h['mean_resid'])} | "
                f"{pct(h['cover_mid'])} | {pts(h['mean_net_mid'])} | "
                f"{h['mean_netR_mid']:+.2f} | {pct(h['p_net_pos_mid'])} | "
                f"{pts(h['mean_pre_exc'])} |"
            )
        v = verdict_session(sess)
        h_oos = get(sess, "HIGH", "OOS")
        l_oos = get(sess, "LOW", "OOS")
        lift = (
            h_oos.get("cover_mid", np.nan) - l_oos.get("cover_mid", np.nan)
            if h_oos and l_oos
            else np.nan
        )
        verdicts.append(
            {
                "session": sess,
                "verdict": v,
                "OOS_mean_resid": h_oos.get("mean_resid"),
                "OOS_mean_net_mid": h_oos.get("mean_net_mid"),
                "OOS_cover_mid": h_oos.get("cover_mid"),
                "OOS_cover_lift_vs_LOW": lift,
                "OOS_mean_pre_exc": h_oos.get("mean_pre_exc"),
            }
        )
        lines.append("")

    lines.append("## HIGH vs LOW cover lift (OOS, H30, mid)")
    lines.append("")
    lines.append("| Session | HIGH cover | LOW cover | Δ | Mean net HIGH | Mean net LOW |")
    lines.append("|---------|------------|-----------|---|---------------|--------------|")
    for sess in SESSION_PRIORITY:
        h = get(sess, "HIGH", "OOS")
        l = get(sess, "LOW", "OOS")
        if not h or not l:
            lines.append(f"| {sess} | — | — | — | — | — |")
            continue
        lift = h["cover_mid"] - l["cover_mid"]
        lines.append(
            f"| {sess} | {pct(h['cover_mid'])} | {pct(l['cover_mid'])} | {pp(lift)} | "
            f"{pts(h['mean_net_mid'])} | {pts(l['mean_net_mid'])} |"
        )
    lines.append("")

    lines.append("## Cost / delay stress (HIGH, H30, OOS mean net)")
    lines.append("")
    lines.append("| Session | tight | mid | wide | delay1 mid |")
    lines.append("|---------|-------|-----|------|------------|")
    for sess in SESSION_PRIORITY:
        h = get(sess, "HIGH", "OOS")
        hd = get(sess, "HIGH", "OOS", delay="delay1")
        if not h:
            lines.append(f"| {sess} | — | — | — | — |")
            continue
        lines.append(
            f"| {sess} | {pts(h.get('mean_net_tight'))} | {pts(h.get('mean_net_mid'))} | "
            f"{pts(h.get('mean_net_wide'))} | {pts(hd.get('mean_net_mid') if hd else np.nan)} |"
        )
    lines.append("")

    lines.append("## Per-session verdicts")
    lines.append("")
    lines.append("| Session | Verdict | OOS net mid | Cover lift vs LOW |")
    lines.append("|---------|---------|-------------|-------------------|")
    for v in verdicts:
        lines.append(
            f"| {v['session']} | **{v['verdict']}** | {pts(v['OOS_mean_net_mid'])} | "
            f"{pp(v['OOS_cover_lift_vs_LOW'])} |"
        )
    lines.append("")
    n_good = sum(
        1
        for v in verdicts
        if v["verdict"] in ("PROMISING", "STRONG_CANDIDATE", "PROMISING_WEAK_LIFT")
    )
    if n_good == 0:
        lines.append(
            "**Program call:** residual exists in the activity sense, but under frozen "
            "costs / latency it does **not** clear a tradeable Phase B econ gate "
            "(or fails vs LOW). Same failure mode family as strategy 11 is possible."
        )
    else:
        lines.append(f"**Survivors (econ framing):** {n_good} session(s) — still not a direction edge.")
    lines.append("")

    art("nq_multi_sess_resid_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pd.DataFrame(verdicts).to_csv(art("nq_multi_sess_resid_verdicts.csv"), index=False)
    art("nq_multi_sess_resid_report.json").write_text(
        json.dumps(
            {
                "panel_rows": int(len(panel)),
                "verdicts": verdicts,
                "primary_H": PRIMARY_H,
                "primary_cost": PRIMARY_COST,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print("Report written.", flush=True)
    for v in verdicts:
        print(f"  {v['session']}: {v['verdict']}", flush=True)


if __name__ == "__main__":
    main()
