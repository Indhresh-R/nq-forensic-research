"""
Strategy 15 — Direction resolution: ES / NQ relative under activity gate

Critical question (research_framework/direction_resolution.md):
  Conditional on Strategy-12 HIGH activity, does ES/NQ signed info resolve
  NQ direction *better than the same resolver unconditionally*?

NOT a follow/fade-on-vol grid. NOT Strategy-07 "inside HIGH only" rehash.
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

from common.nq_session import art, load_es, load_nq, win_rate
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
HOLD_HS = (15, 30)
PRIMARY_H = 30
COST_MID = 1.0
RESOLVERS = ("follow_es", "rs_continue", "agree_follow")

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


def pct_ret(o: float, c: float) -> float:
    if not np.isfinite(o) or o == 0:
        return np.nan
    return (c - o) / o


def side_for(resolver: str, nq_ret: float, es_ret: float) -> int | None:
    if not np.isfinite(nq_ret) or not np.isfinite(es_ret):
        return None
    sn = 0 if abs(nq_ret) < 1e-12 else (1 if nq_ret > 0 else -1)
    se = 0 if abs(es_ret) < 1e-12 else (1 if es_ret > 0 else -1)
    if resolver == "follow_es":
        return se if se != 0 else None
    if resolver == "rs_continue":
        rs = nq_ret - es_ret
        if abs(rs) < 1e-12:
            return None
        return 1 if rs > 0 else -1
    if resolver == "agree_follow":
        if sn == 0 or se == 0 or sn != se:
            return None
        return sn
    return None


def fwd_pnl(after: pd.DataFrame, side: int, H: int) -> float | None:
    if len(after) < H:
        return None
    entry = float(after.iloc[0]["open"])
    px = float(after.iloc[H - 1]["close"])
    return side * (px - entry)


def summarize(pnls: np.ndarray) -> dict[str, float]:
    x = pnls[np.isfinite(pnls)]
    if len(x) == 0:
        return {"n": 0, "win": np.nan, "E": np.nan, "E_net": np.nan}
    wr = win_rate(pd.Series(x))
    return {
        "n": int(len(x)),
        "win": float(wr["rate"]),
        "E": float(np.mean(x)),
        "E_net": float(np.mean(x - COST_MID)),
    }


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pp(x: Any) -> str:
    return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pts(x: Any) -> str:
    return f"{x:+.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== Strategy 15: ES/NQ Direction Resolution (conditional lift) ===", flush=True)
    print("Gate: Strategy 12 HIGH/LOW rng_psr terciles (frozen)", flush=True)

    nq = load_nq()
    es = load_es()
    facts = build_session_facts(nq)
    facts_map = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}

    nq_bars: dict[tuple, pd.DataFrame] = {}
    es_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in nq.groupby("session_date", sort=False):
        for name in SESSION_PRIORITY:
            key = (sd, name)
            if key not in facts_map:
                continue
            b = bars_in_session(g, name)
            if len(b) >= 40:
                nq_bars[key] = b
    for sd, g in es.groupby("session_date", sort=False):
        for name in SESSION_PRIORITY:
            key = (sd, name)
            b = bars_in_session(g, name)
            if len(b) >= 30:
                es_bars[key] = b
    print(f"NQ slices={len(nq_bars)} ES slices={len(es_bars)}", flush=True)

    rows: list[dict] = []
    n_done = 0
    n_skip_es = 0
    for (sd, name), bars in nq_bars.items():
        fr = facts_map[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        esb = es_bars.get((sd, name))
        if esb is None:
            n_skip_es += 1
            continue
        es_idx = {int(m): i for i, m in enumerate(esb["ny_min"].astype(int).tolist())}
        session_open = float(fr["open"])
        es_open = float(esb.iloc[0]["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        for off in SESSION_DECISION_OFFSETS[name]:
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()) or T not in es_idx:
                continue
            st = state_at_T_session(
                bars, session=name, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            nq_c = float(bars.loc[bars["ny_min"] == T, "close"].iloc[-1])
            es_c = float(esb.iloc[es_idx[T]]["close"])
            nq_ret = pct_ret(session_open, nq_c)
            es_ret = pct_ret(es_open, es_c)
            reg = regime_of(name, off, float(st["rng_psr"]))
            after = after_bars(bars, T, name)
            if len(after) < max(HOLD_HS):
                continue
            base = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                "nq_ret": nq_ret,
                "es_ret": es_ret,
                "rng_psr": float(st["rng_psr"]),
            }
            for rname in RESOLVERS:
                side = side_for(rname, nq_ret, es_ret)
                if side is None:
                    continue
                row = {**base, "resolver": rname, "side": side}
                ok = True
                for H in HOLD_HS:
                    pnl = fwd_pnl(after, side, H)
                    if pnl is None:
                        ok = False
                        break
                    row[f"pnl_{H}"] = pnl
                if ok:
                    rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, panel={len(rows)}, skip_es~{n_skip_es}", flush=True)

    panel = pd.DataFrame(rows)
    panel_path = art("nq_dirres_esnq_panel.parquet")
    panel.to_parquet(panel_path, index=False)
    print(f"Panel rows={len(panel)} -> {panel_path} (es skips={n_skip_es})", flush=True)
    if panel.empty:
        raise SystemExit("Empty panel")

    # Metrics: resolver × session × T × H × universe × split
    results: list[dict[str, Any]] = []
    for sess in SESSION_PRIORITY:
        for rname in RESOLVERS:
            for off in SESSION_DECISION_OFFSETS[sess]:
                for H in HOLD_HS:
                    sub0 = panel[
                        (panel["session"] == sess)
                        & (panel["resolver"] == rname)
                        & (panel["T_offset"] == off)
                    ]
                    if len(sub0) < 50:
                        continue
                    col = f"pnl_{H}"
                    for univ, mask in (
                        ("ALL", pd.Series(True, index=sub0.index)),
                        ("HIGH", sub0["regime"] == "HIGH"),
                        ("LOW", sub0["regime"] == "LOW"),
                    ):
                        u = sub0.loc[mask.to_numpy()]
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
                                    "resolver": rname,
                                    "T_offset": off,
                                    "horizon": H,
                                    "universe": univ,
                                    "split": split,
                                    **m,
                                }
                            )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_dirres_esnq_results.csv"), index=False)

    def get(sess, rname, off, H, univ, split) -> dict[str, Any]:
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["resolver"] == rname)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    # Lift candidates
    candidates: list[dict[str, Any]] = []
    for sess in SESSION_PRIORITY:
        for rname in RESOLVERS:
            for off in SESSION_DECISION_OFFSETS[sess]:
                for H in HOLD_HS:
                    hi = get(sess, rname, off, H, "HIGH", "IS")
                    al = get(sess, rname, off, H, "ALL", "IS")
                    hv = get(sess, rname, off, H, "HIGH", "Validation")
                    av = get(sess, rname, off, H, "ALL", "Validation")
                    ho = get(sess, rname, off, H, "HIGH", "OOS")
                    ao = get(sess, rname, off, H, "ALL", "OOS")
                    if not hi or not al or hi.get("n", 0) < 80 or al.get("n", 0) < 80:
                        continue
                    if not hv or not av or not ho or not ao:
                        continue
                    if hv.get("n", 0) < 30 or ho.get("n", 0) < 25:
                        continue
                    lift_w_is = hi["win"] - al["win"]
                    lift_e_is = hi["E"] - al["E"]
                    lift_w_v = hv["win"] - av["win"]
                    lift_e_v = hv["E"] - av["E"]
                    lift_w_o = ho["win"] - ao["win"]
                    lift_e_o = ho["E"] - ao["E"]
                    soft_is = lift_w_is >= 0.03 or lift_e_is >= 0.5
                    strong_is = lift_w_is >= 0.05 or lift_e_is >= 1.0
                    # same-sign lift on Val+OOS (prefer win lift; allow E lift)
                    def pos(w, e):
                        return (w > 0 and abs(w) >= 0.01) or (e > 0 and abs(e) >= 0.25)

                    vo_ok = pos(lift_w_v, lift_e_v) and pos(lift_w_o, lift_e_o)
                    # HIGH itself should not be random garbage
                    high_ok = hi["win"] >= 0.52 or hi["E"] > 0
                    y25h = get(sess, rname, off, H, "HIGH", "Y2025")
                    y25a = get(sess, rname, off, H, "ALL", "Y2025")
                    y26h = get(sess, rname, off, H, "HIGH", "Y2026")
                    y26a = get(sess, rname, off, H, "ALL", "Y2026")
                    year_ok = False
                    if (
                        y25h
                        and y25a
                        and y26h
                        and y26a
                        and y25h.get("n", 0) >= 20
                        and y26h.get("n", 0) >= 20
                    ):
                        lw25 = y25h["win"] - y25a["win"]
                        lw26 = y26h["win"] - y26a["win"]
                        le25 = y25h["E"] - y25a["E"]
                        le26 = y26h["E"] - y26a["E"]
                        year_ok = pos(lw25, le25) and pos(lw26, le26)
                    soft = soft_is and vo_ok and high_ok
                    strong = strong_is and vo_ok and high_ok and year_ok
                    if soft or strong:
                        candidates.append(
                            {
                                "session": sess,
                                "resolver": rname,
                                "T_offset": off,
                                "horizon": H,
                                "tier": "strong" if strong else "soft",
                                "HIGH_IS_n": hi["n"],
                                "HIGH_IS_win": hi["win"],
                                "HIGH_IS_E": hi["E"],
                                "ALL_IS_win": al["win"],
                                "lift_win_IS": lift_w_is,
                                "lift_E_IS": lift_e_is,
                                "lift_win_Val": lift_w_v,
                                "lift_E_Val": lift_e_v,
                                "lift_win_OOS": lift_w_o,
                                "lift_E_OOS": lift_e_o,
                                "HIGH_OOS_win": ho["win"],
                                "HIGH_OOS_E": ho["E"],
                                "ALL_OOS_win": ao["win"],
                                "year_ok": year_ok,
                            }
                        )

    cand_df = pd.DataFrame(candidates) if candidates else pd.DataFrame()
    cand_df.to_csv(art("nq_dirres_esnq_candidates.csv"), index=False)

    # Multi-clock stability
    stability: list[dict] = []
    if len(cand_df):
        for (sess, rname, H, tier), g in cand_df.groupby(
            ["session", "resolver", "horizon", "tier"]
        ):
            # count clocks that are soft or strong for this key
            pass
        for (sess, rname, H), g in cand_df.groupby(["session", "resolver", "horizon"]):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            stability.append(
                {
                    "session": sess,
                    "resolver": rname,
                    "horizon": int(H),
                    "n_clocks": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "med_lift_win_IS": float(g["lift_win_IS"].median()),
                    "med_lift_win_OOS": float(g["lift_win_OOS"].median()),
                }
            )
        stability.sort(key=lambda x: (-x["n_clocks_strong"], -x["n_clocks"], -abs(x["med_lift_win_IS"])))

    # Headline: primary H30, best IS lift per session×resolver (report even if not candidate)
    lines = [
        "# Strategy 15 — ES/NQ Direction Resolution (conditional lift)",
        "",
        "## Question",
        "",
        "> Conditional on Strategy-12 activity HIGH, does ES/NQ signed information",
        "> resolve NQ direction **better than the same resolver unconditionally**?",
        "",
        "## Freeze",
        "",
        "- Activity: Strategy 12 `rng_psr` IS terciles (untouched)",
        f"- Resolvers: {', '.join(RESOLVERS)}",
        f"- Primary H={PRIMARY_H}; cost stress mid={COST_MID} pt (reported in panel E_net)",
        f"- Sessions independent: {' → '.join(SESSION_PRIORITY)}",
        f"- Panel rows: **{len(panel):,}**",
        f"- Soft candidates: **{int((cand_df['tier']=='soft').sum()) if len(cand_df) else 0}**",
        f"- Strong candidates: **{int((cand_df['tier']=='strong').sum()) if len(cand_df) else 0}**",
        "",
        "## Lift table (H30, best IS lift_win clock per session×resolver)",
        "",
        "| Session | Resolver | T+ | HIGH IS win | ALL IS win | Lift IS | Lift Val | Lift OOS | HIGH OOS win |",
        "|---------|----------|----|-------------|------------|---------|----------|----------|--------------|",
    ]

    for sess in SESSION_PRIORITY:
        for rname in RESOLVERS:
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                hi = get(sess, rname, off, PRIMARY_H, "HIGH", "IS")
                al = get(sess, rname, off, PRIMARY_H, "ALL", "IS")
                if not hi or not al or hi.get("n", 0) < 40:
                    continue
                lift = hi["win"] - al["win"]
                if best is None or lift > best["lift"]:
                    hv = get(sess, rname, off, PRIMARY_H, "HIGH", "Validation")
                    av = get(sess, rname, off, PRIMARY_H, "ALL", "Validation")
                    ho = get(sess, rname, off, PRIMARY_H, "HIGH", "OOS")
                    ao = get(sess, rname, off, PRIMARY_H, "ALL", "OOS")
                    best = {
                        "off": off,
                        "lift": lift,
                        "hi": hi,
                        "al": al,
                        "lw_v": (hv["win"] - av["win"]) if hv and av else np.nan,
                        "lw_o": (ho["win"] - ao["win"]) if ho and ao else np.nan,
                        "ho": ho,
                    }
            if best is None:
                lines.append(f"| {sess} | {rname} | — | — | — | — | — | — | — |")
            else:
                lines.append(
                    f"| {sess} | {rname} | {best['off']} | {pct(best['hi']['win'])} | "
                    f"{pct(best['al']['win'])} | {pp(best['lift'])} | {pp(best['lw_v'])} | "
                    f"{pp(best['lw_o'])} | {pct(best['ho'].get('win') if best['ho'] else np.nan)} |"
                )
    lines.append("")

    lines.append("## Multi-clock stability (candidates)")
    lines.append("")
    if not stability:
        lines.append("No soft/strong lift candidates.")
    else:
        lines.append("| Session | Resolver | H | Soft/strong clocks | Strong clocks | Med lift IS | Med lift OOS |")
        lines.append("|---------|----------|---|--------------------|---------------|-------------|--------------|")
        for s in stability[:30]:
            lines.append(
                f"| {s['session']} | {s['resolver']} | {s['horizon']} | {s['n_clocks']} | "
                f"{s['n_clocks_strong']} | {pp(s['med_lift_win_IS'])} | {pp(s['med_lift_win_OOS'])} |"
            )
    lines.append("")

    n_strong = int((cand_df["tier"] == "strong").sum()) if len(cand_df) else 0
    n_soft = int((cand_df["tier"] == "soft").sum()) if len(cand_df) else 0
    multi = [s for s in stability if s["n_clocks"] >= 2]
    multi_strong = [s for s in stability if s["n_clocks_strong"] >= 2]

    if n_strong == 0 and n_soft == 0:
        verdict = "C"
        call = (
            "No conditional-lift survivors. ES/NQ signed resolvers do not resolve "
            "direction **better inside activity than unconditionally** under frozen gates. "
            "Consistent with Strategy 07 inside-HIGH kill, now with the interaction test explicit."
        )
    elif multi_strong:
        verdict = "B_or_better"
        call = f"Multi-clock strong lift present ({len(multi_strong)} keys) — review candidates before any promotion."
    elif multi or n_soft:
        verdict = "B"
        call = "Soft / single-clock lift only — do not promote; not a trade."
    else:
        verdict = "C"
        call = "No usable lift structure."

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict}`**")
    lines.append("")
    lines.append(call)
    lines.append("")
    lines.append("### Research implication")
    lines.append("")
    if verdict == "C":
        lines.append(
            "First signed-information source (ES/NQ) fails the direction-resolution "
            "program test. Next dossier needs a **different** sign source "
            "(trapped side, inventory, options lag, etc.) — not more ES variants."
        )
    else:
        lines.append("Inspect candidates CSV; only multi-clock year-stable lift may proceed to econ card.")
    lines.append("")

    art("nq_dirres_esnq_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_dirres_esnq_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
                "stability": stability[:20],
                "call": call,
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
