"""
Strategy 17 — Session extreme tag-and-fail (trapped side) under Strategy-12 HIGH

Resolver-only. Vulnerability class — not static HTF bias.

Frozen:
  W=15m, thr=max(0.50, 0.05*psr)
  Buyers trapped (tag SH, close back) -> side=-1
  Sellers trapped (tag SL, close back) -> side=+1
  Strategy 12 terciles untouched.
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

from common.nq_session import art, load_nq, win_rate
from common.sessions import (
    SESSION_DECISION_OFFSETS,
    SESSION_START,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    elapsed_from_session_open,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_PRIORITY = ("LONDON", "NY_PM", "NY_AM", "ASIA")
HOLD_HS = (15, 30, 60, 90, 120)
PRIMARY_HS = (30, 60)
LOOKBACK_W = 15  # minutes — frozen

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


def bars_to_T(sess: pd.DataFrame, T_ny: int, session: str) -> pd.DataFrame:
    if session == "ASIA":
        ord_T = T_ny if T_ny >= SESSION_START else T_ny + 24 * 60
        ord_key = np.where(
            sess["ny_min"].to_numpy(np.int64) >= SESSION_START,
            sess["ny_min"].to_numpy(np.int64),
            sess["ny_min"].to_numpy(np.int64) + 24 * 60,
        )
        return sess.loc[ord_key <= ord_T].reset_index(drop=True)
    return sess[sess["ny_min"] <= T_ny].reset_index(drop=True)


def recent_window(to_T: pd.DataFrame, session: str, T_ny: int, W: int) -> pd.DataFrame:
    """Last W minutes of bars ending at T (causal)."""
    if len(to_T) == 0:
        return to_T
    elapsed = elapsed_from_session_open(session, T_ny)
    # take last min(W, elapsed) bars by count approx 1 bar/min
    n = min(int(W), len(to_T))
    return to_T.iloc[-n:].reset_index(drop=True)


def trap_side(to_T: pd.DataFrame, recent: pd.DataFrame, psr: float) -> tuple[int | None, str]:
    if len(to_T) < 5 or len(recent) < 3 or not np.isfinite(psr) or psr <= 0:
        return None, "none"
    sh = float(to_T["high"].max())
    sl = float(to_T["low"].min())
    close_T = float(to_T.iloc[-1]["close"])
    thr = max(0.50, 0.05 * psr)
    rh = float(recent["high"].max())
    rl = float(recent["low"].min())
    buyers = rh >= sh - 1e-9 and close_T <= sh - thr
    sellers = rl <= sl + 1e-9 and close_T >= sl + thr
    if buyers and not sellers:
        return -1, "buyers_trapped"
    if sellers and not buyers:
        return 1, "sellers_trapped"
    return None, "none"


def summarize(pnls: np.ndarray) -> dict[str, float]:
    x = pnls[np.isfinite(pnls)]
    if len(x) == 0:
        return {"n": 0, "win": np.nan, "E": np.nan}
    return {
        "n": int(len(x)),
        "win": float(win_rate(pd.Series(x))["rate"]),
        "E": float(np.mean(x)),
    }


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pp(x: Any) -> str:
    return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== Strategy 17: Session extreme trap (trapped side) ===", flush=True)
    print(
        f"W={LOOKBACK_W}m thr=max(0.50,0.05*psr); H={HOLD_HS}; Strategy 12 frozen",
        flush=True,
    )

    df = load_nq()
    facts = build_session_facts(df)
    facts_map = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}

    sess_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=False):
        for name in SESSION_PRIORITY:
            key = (sd, name)
            if key not in facts_map:
                continue
            b = bars_in_session(g, name)
            if len(b) >= 40:
                sess_bars[key] = b

    rows: list[dict] = []
    n_done = 0
    n_trap = 0
    for (sd, name), bars in sess_bars.items():
        fr = facts_map[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        for off in SESSION_DECISION_OFFSETS[name]:
            if off < LOOKBACK_W:
                continue  # need room for lookback inside session
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars, session=name, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            to_T = bars_to_T(bars, T, name)
            recent = recent_window(to_T, name, T, LOOKBACK_W)
            side, trap = trap_side(to_T, recent, psr)
            if side is None:
                continue
            n_trap += 1
            reg = regime_of(name, off, float(st["rng_psr"]))
            after = after_bars(bars, T, name)
            if len(after) < min(HOLD_HS):
                continue
            entry = float(after.iloc[0]["open"])
            closes = after["close"].to_numpy(float)
            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                "side_trap": side,
                "trap": trap,
                "rng_psr": float(st["rng_psr"]),
                "psr": psr,
            }
            any_h = False
            for H in HOLD_HS:
                if len(closes) < H:
                    row[f"pnl_trap_{H}"] = np.nan
                    row[f"pnl_long_{H}"] = np.nan
                    continue
                px = float(closes[H - 1])
                row[f"pnl_trap_{H}"] = side * (px - entry)
                row[f"pnl_long_{H}"] = px - entry
                any_h = True
            if any_h:
                rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, panel={len(rows)}, traps~{n_trap}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_dirres_trap17_panel.parquet"), index=False)
    print(f"Panel rows={len(panel)}", flush=True)
    if panel.empty:
        raise SystemExit("Empty panel — trap definition too strict?")

    results: list[dict[str, Any]] = []
    universes = (
        ("ALL_trap", "pnl_trap", None),
        ("HIGH_trap", "pnl_trap", "HIGH"),
        ("LOW_trap", "pnl_trap", "LOW"),
        ("HIGH_long", "pnl_long", "HIGH"),
    )
    for sess in SESSION_PRIORITY:
        for off in SESSION_DECISION_OFFSETS[sess]:
            if off < LOOKBACK_W:
                continue
            for H in HOLD_HS:
                col_check = f"pnl_trap_{H}"
                base = panel[
                    (panel["session"] == sess)
                    & (panel["T_offset"] == off)
                    & panel[col_check].notna()
                ]
                if len(base) < 40:
                    continue
                for uname, prefix, reg in universes:
                    col = f"{prefix}_{H}"
                    u = base if reg is None else base[base["regime"] == reg]
                    for split in ("IS", "Validation", "OOS", "Y2025", "Y2026"):
                        if split.startswith("Y"):
                            s = u[u["year"] == int(split[1:])]
                        else:
                            s = u[u["split"] == split]
                        m = summarize(s[col].to_numpy(float))
                        if m["n"] < 15 and split in ("IS", "Validation", "OOS"):
                            continue
                        results.append(
                            {
                                "session": sess,
                                "T_offset": off,
                                "horizon": H,
                                "universe": uname,
                                "split": split,
                                **m,
                            }
                        )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_dirres_trap17_results.csv"), index=False)

    def get(sess, off, H, univ, split) -> dict[str, Any]:
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    def pos_lift(w: float, e: float) -> bool:
        return (np.isfinite(w) and w > 0 and abs(w) >= 0.01) or (
            np.isfinite(e) and e > 0 and abs(e) >= 0.25
        )

    candidates: list[dict[str, Any]] = []
    for sess in SESSION_PRIORITY:
        for off in SESSION_DECISION_OFFSETS[sess]:
            if off < LOOKBACK_W:
                continue
            for H in HOLD_HS:
                hb = get(sess, off, H, "HIGH_trap", "IS")
                ab = get(sess, off, H, "ALL_trap", "IS")
                if not hb or not ab or hb.get("n", 0) < 60 or ab.get("n", 0) < 60:
                    continue
                hv = get(sess, off, H, "HIGH_trap", "Validation")
                av = get(sess, off, H, "ALL_trap", "Validation")
                ho = get(sess, off, H, "HIGH_trap", "OOS")
                ao = get(sess, off, H, "ALL_trap", "OOS")
                if not hv or not av or not ho or not ao:
                    continue
                if hv.get("n", 0) < 25 or ho.get("n", 0) < 20:
                    continue
                lw_is = hb["win"] - ab["win"]
                le_is = hb["E"] - ab["E"]
                lw_v = hv["win"] - av["win"]
                le_v = hv["E"] - av["E"]
                lw_o = ho["win"] - ao["win"]
                le_o = ho["E"] - ao["E"]
                soft_is = lw_is >= 0.03 or le_is >= 0.5
                strong_is = lw_is >= 0.05 or le_is >= 1.0
                vo_ok = pos_lift(lw_v, le_v) and pos_lift(lw_o, le_o)
                high_ok = hb["win"] >= 0.52 or hb["E"] > 0
                y25h = get(sess, off, H, "HIGH_trap", "Y2025")
                y25a = get(sess, off, H, "ALL_trap", "Y2025")
                y26h = get(sess, off, H, "HIGH_trap", "Y2026")
                y26a = get(sess, off, H, "ALL_trap", "Y2026")
                year_ok = False
                if (
                    y25h
                    and y25a
                    and y26h
                    and y26a
                    and y25h.get("n", 0) >= 15
                    and y26h.get("n", 0) >= 15
                ):
                    year_ok = pos_lift(
                        y25h["win"] - y25a["win"], y25h["E"] - y25a["E"]
                    ) and pos_lift(y26h["win"] - y26a["win"], y26h["E"] - y26a["E"])
                soft = soft_is and vo_ok and high_ok
                strong = strong_is and vo_ok and high_ok and year_ok
                if soft or strong:
                    candidates.append(
                        {
                            "session": sess,
                            "T_offset": off,
                            "horizon": H,
                            "tier": "strong" if strong else "soft",
                            "HIGH_trap_IS_n": hb["n"],
                            "HIGH_trap_IS_win": hb["win"],
                            "ALL_trap_IS_win": ab["win"],
                            "lift_win_IS": lw_is,
                            "lift_E_IS": le_is,
                            "lift_win_Val": lw_v,
                            "lift_win_OOS": lw_o,
                            "HIGH_trap_OOS_win": ho["win"],
                            "year_ok": year_ok,
                        }
                    )

    cand_df = pd.DataFrame(candidates) if candidates else pd.DataFrame()
    cand_df.to_csv(art("nq_dirres_trap17_candidates.csv"), index=False)

    stability: list[dict] = []
    if len(cand_df):
        for (sess, H), g in cand_df.groupby(["session", "horizon"]):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            stability.append(
                {
                    "session": sess,
                    "horizon": int(H),
                    "n_clocks": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "med_lift_win_IS": float(g["lift_win_IS"].median()),
                    "med_lift_win_OOS": float(g["lift_win_OOS"].median()),
                }
            )
        stability.sort(key=lambda x: (-x["n_clocks_strong"], -x["n_clocks"]))

    lines = [
        "# Strategy 17 — Session Extreme Trap (resolver-only)",
        "",
        "## Question",
        "",
        "> Conditional on Strategy-12 HIGH, does fading a recent session-extreme",
        "> tag-and-fail (trapped side) resolve NQ direction better than unconditionally?",
        "",
        "## Freeze",
        "",
        f"- W={LOOKBACK_W}m; thr=max(0.50, 0.05*psr)",
        "- Buyers trapped -> short; sellers trapped -> long",
        "- Strategy 12 untouched",
        f"- H={list(HOLD_HS)}",
        f"- Panel rows: **{len(panel):,}**",
        f"- Soft: **{int((cand_df['tier']=='soft').sum()) if len(cand_df) else 0}**",
        f"- Strong: **{int((cand_df['tier']=='strong').sum()) if len(cand_df) else 0}**",
        "",
    ]

    # Trap mix
    if "trap" in panel.columns:
        mix = panel["trap"].value_counts(normalize=True)
        lines.append("## Trap mix (panel)")
        lines.append("")
        for k, v in mix.items():
            lines.append(f"- `{k}`: {100*v:.1f}%")
        lines.append("")

    for H in PRIMARY_HS:
        lines.append(f"## Primary contrast H={H} (best IS lift clock per session)")
        lines.append("")
        lines.append(
            "| Session | T+ | ALL+trap | HIGH+trap | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+trap OOS |"
        )
        lines.append(
            "|---------|----|----------|-----------|-----------|-------------|----------|----------|----------------|"
        )
        for sess in SESSION_PRIORITY:
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < LOOKBACK_W:
                    continue
                hb = get(sess, off, H, "HIGH_trap", "IS")
                ab = get(sess, off, H, "ALL_trap", "IS")
                if not hb or not ab or hb.get("n", 0) < 30:
                    continue
                lift = hb["win"] - ab["win"]
                if best is None or lift > best["lift"]:
                    hl = get(sess, off, H, "HIGH_long", "IS")
                    hv = get(sess, off, H, "HIGH_trap", "Validation")
                    av = get(sess, off, H, "ALL_trap", "Validation")
                    ho = get(sess, off, H, "HIGH_trap", "OOS")
                    ao = get(sess, off, H, "ALL_trap", "OOS")
                    best = {
                        "off": off,
                        "lift": lift,
                        "ab": ab,
                        "hb": hb,
                        "hl": hl,
                        "lw_v": (hv["win"] - av["win"]) if hv and av else np.nan,
                        "lw_o": (ho["win"] - ao["win"]) if ho and ao else np.nan,
                        "ho": ho,
                    }
            if best is None:
                lines.append(f"| {sess} | — | — | — | — | — | — | — | — |")
            else:
                hlw = best["hl"]["win"] if best["hl"] else np.nan
                lines.append(
                    f"| {sess} | {best['off']} | {pct(best['ab']['win'])} | "
                    f"{pct(best['hb']['win'])} | {pct(hlw)} | {pp(best['lift'])} | "
                    f"{pp(best['lw_v'])} | {pp(best['lw_o'])} | "
                    f"{pct(best['ho'].get('win') if best['ho'] else np.nan)} |"
                )
        lines.append("")

    lines.append("## London lift vs ALL by H (best IS clock per H)")
    lines.append("")
    lines.append("| H | T+ | HIGH+trap IS | ALL+trap IS | Lift IS | Lift Val | Lift OOS |")
    lines.append("|---|----|--------------|-------------|---------|----------|----------|")
    for H in HOLD_HS:
        best = None
        for off in SESSION_DECISION_OFFSETS["LONDON"]:
            if off < LOOKBACK_W:
                continue
            hb = get("LONDON", off, H, "HIGH_trap", "IS")
            ab = get("LONDON", off, H, "ALL_trap", "IS")
            if not hb or not ab or hb.get("n", 0) < 30:
                continue
            lift = hb["win"] - ab["win"]
            if best is None or lift > best["lift"]:
                hv = get("LONDON", off, H, "HIGH_trap", "Validation")
                av = get("LONDON", off, H, "ALL_trap", "Validation")
                ho = get("LONDON", off, H, "HIGH_trap", "OOS")
                ao = get("LONDON", off, H, "ALL_trap", "OOS")
                best = {
                    "off": off,
                    "lift": lift,
                    "hb": hb,
                    "ab": ab,
                    "lw_v": (hv["win"] - av["win"]) if hv and av else np.nan,
                    "lw_o": (ho["win"] - ao["win"]) if ho and ao else np.nan,
                }
        if best is None:
            lines.append(f"| {H} | — | — | — | — | — | — |")
        else:
            lines.append(
                f"| {H} | {best['off']} | {pct(best['hb']['win'])} | {pct(best['ab']['win'])} | "
                f"{pp(best['lift'])} | {pp(best['lw_v'])} | {pp(best['lw_o'])} |"
            )
    lines.append("")

    lines.append("## Multi-clock stability (candidates)")
    lines.append("")
    if not stability:
        lines.append("No soft/strong lift candidates.")
    else:
        lines.append("| Session | H | Soft/strong clocks | Strong clocks | Med lift IS | Med lift OOS |")
        lines.append("|---------|---|--------------------|---------------|-------------|--------------|")
        for s in stability:
            lines.append(
                f"| {s['session']} | {s['horizon']} | {s['n_clocks']} | {s['n_clocks_strong']} | "
                f"{pp(s['med_lift_win_IS'])} | {pp(s['med_lift_win_OOS'])} |"
            )
    lines.append("")

    n_strong = int((cand_df["tier"] == "strong").sum()) if len(cand_df) else 0
    n_soft = int((cand_df["tier"] == "soft").sum()) if len(cand_df) else 0
    multi_strong = [s for s in stability if s["n_clocks_strong"] >= 2]

    if n_strong == 0 and n_soft == 0:
        verdict = "C"
        call = (
            "Kill 17. Session extreme tag-and-fail does not resolve direction "
            "conditionally inside Strategy-12 HIGH vs unconditional."
        )
    elif multi_strong:
        verdict = "B_review"
        call = (
            f"Multi-clock strong lift keys={len(multi_strong)}. Scientific interest — "
            "freeze; do not retune W/thr or Strategy 12."
        )
    elif n_soft or n_strong:
        verdict = "B->kill"
        call = (
            "Soft or single-clock only. Do not promote. Do not retune W/thr to rescue."
        )
    else:
        verdict = "C"
        call = "No usable structure."

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict}`**")
    lines.append("")
    lines.append(call)
    lines.append("")
    lines.append("### Discipline")
    lines.append("")
    lines.append("- Vulnerability class first test; 16A/16B stay dead.")
    lines.append("- Strategy 12 remains WHEN-only.")
    lines.append("")

    art("nq_dirres_trap17_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_dirres_trap17_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
                "lookback_W": LOOKBACK_W,
                "call": call,
                "stability": stability,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"Verdict: {verdict}", flush=True)
    print(call, flush=True)


if __name__ == "__main__":
    main()
