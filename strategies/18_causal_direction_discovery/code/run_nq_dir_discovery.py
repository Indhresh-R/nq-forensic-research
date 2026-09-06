"""
Strategy 18 — Causal direction discovery scan

Frozen menu of sign resolvers. Score conditional lift inside Strategy-12 HIGH
vs ALL. No feature invention after OOS. No stops/targets.

Excluded (already killed as dedicated dossiers): ES/NQ, prior-day color,
prior-day mid, session extreme trap.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import art, load_nq, win_rate
from common.sessions import (
    PRIOR_SESSION,
    SESSION_DECISION_OFFSETS,
    SESSION_ORDER,
    SESSION_START,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_PRIORITY = ("LONDON", "NY_PM", "NY_AM", "ASIA")
HOLD_HS = (30, 60)
PRIMARY_H = 30
RESOLVER_IDS = (
    "mom5_follow",
    "mom15_follow",
    "mom15_fade",
    "vwap_follow",
    "vwap_fade",
    "ext_fade",
    "prior_sess_mid",
    "gap_follow",
    "path30_follow",
    "path30_fade",
)

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


def build_globex_daily(df: pd.DataFrame) -> dict:
    rows = []
    for sd, g in df.groupby("session_date", sort=True):
        if len(g) < 60:
            continue
        g = g.sort_values("ts")
        rows.append(
            {
                "session_date": sd,
                "day_close": float(g.iloc[-1]["close"]),
                "day_high": float(g["high"].max()),
                "day_low": float(g["low"].min()),
            }
        )
    daily = pd.DataFrame(rows).sort_values("session_date")
    daily["prior_close"] = daily["day_close"].shift(1)
    return {r["session_date"]: r for _, r in daily.iterrows()}


def sgn(x: float, eps: float = 1e-9) -> int | None:
    if not np.isfinite(x) or abs(x) < eps:
        return None
    return 1 if x > 0 else -1


def session_vwap(to_T: pd.DataFrame) -> float | None:
    if len(to_T) < 3:
        return None
    tp = (to_T["high"].to_numpy(float) + to_T["low"].to_numpy(float) + to_T["close"].to_numpy(float)) / 3.0
    vol = to_T["volume"].to_numpy(float) if "volume" in to_T.columns else np.ones(len(to_T))
    if np.nansum(vol) <= 0:
        return float(np.nanmean(tp))
    return float(np.nansum(tp * vol) / np.nansum(vol))


def resolve_sides(
    to_T: pd.DataFrame,
    session: str,
    session_open: float,
    prior_sess_mid: float | None,
    prior_day_close: float | None,
) -> dict[str, int | None]:
    c = to_T["close"].to_numpy(float)
    h = to_T["high"].to_numpy(float)
    l = to_T["low"].to_numpy(float)
    close_T = float(c[-1])
    out: dict[str, int | None] = {k: None for k in RESOLVER_IDS}

    if len(c) > 5:
        out["mom5_follow"] = sgn(close_T - float(c[-6]))
    if len(c) > 15:
        m15 = sgn(close_T - float(c[-16]))
        out["mom15_follow"] = m15
        out["mom15_fade"] = (-m15) if m15 is not None else None

    vw = session_vwap(to_T)
    if vw is not None:
        vs = sgn(close_T - vw)
        out["vwap_follow"] = vs
        out["vwap_fade"] = (-vs) if vs is not None else None

    sh, sl = float(h.max()), float(l.min())
    if sh > sl:
        d_hi = sh - close_T
        d_lo = close_T - sl
        if abs(d_hi - d_lo) >= 0.25:
            out["ext_fade"] = -1 if d_hi < d_lo else 1

    if prior_sess_mid is not None and np.isfinite(prior_sess_mid):
        out["prior_sess_mid"] = sgn(close_T - float(prior_sess_mid), eps=0.25)

    if prior_day_close is not None and np.isfinite(prior_day_close):
        out["gap_follow"] = sgn(session_open - float(prior_day_close), eps=0.25)

    if len(c) > 30:
        d = np.diff(c[-31:])
        up = float(np.sum(d[d > 0]))
        dn = float(np.sum(-d[d < 0]))
        imb = sgn(up - dn)
        out["path30_follow"] = imb
        out["path30_fade"] = (-imb) if imb is not None else None

    return out


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
    print("=== Strategy 18: Causal direction discovery scan ===", flush=True)
    print(f"Resolvers={RESOLVER_IDS}", flush=True)
    print("Strategy 12 gate frozen; no post-hoc features", flush=True)

    df = load_nq()
    daily_map = build_globex_daily(df)
    facts = build_session_facts(df)
    # prior session mid from facts range/high/low
    facts_idx = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}
    dates = sorted(facts["session_date"].unique(), key=lambda d: str(d))
    date_i = {d: i for i, d in enumerate(dates)}

    def prior_session_mid(sd, name: str) -> float | None:
        prior_name = PRIOR_SESSION[name]
        if name == "ASIA":
            i = date_i.get(sd)
            if i is None or i == 0:
                return None
            prev = dates[i - 1]
            fr = facts_idx.get((prev, "NY_PM"))
        else:
            fr = facts_idx.get((sd, prior_name))
        if fr is None:
            return None
        return 0.5 * (float(fr["high"]) + float(fr["low"]))

    sess_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=False):
        for name in SESSION_PRIORITY:
            key = (sd, name)
            if key not in facts_idx:
                continue
            b = bars_in_session(g, name)
            if len(b) >= 40:
                sess_bars[key] = b

    rows: list[dict] = []
    n_done = 0
    for (sd, name), bars in sess_bars.items():
        fr = facts_idx[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        psm = prior_session_mid(sd, name)
        dr = daily_map.get(sd)
        pdc = float(dr["prior_close"]) if dr is not None and np.isfinite(dr.get("prior_close", np.nan)) else None
        for off in SESSION_DECISION_OFFSETS[name]:
            if off < 15:
                continue
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars, session=name, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            to_T = bars_to_T(bars, T, name)
            if len(to_T) < 20:
                continue
            sides = resolve_sides(to_T, name, session_open, psm, pdc)
            if all(v is None for v in sides.values()):
                continue
            reg = regime_of(name, off, float(st["rng_psr"]))
            after = after_bars(bars, T, name)
            if len(after) < max(HOLD_HS):
                continue
            entry = float(after.iloc[0]["open"])
            closes = after["close"].to_numpy(float)
            # raw long pnl for baseline skew
            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
            }
            for H in HOLD_HS:
                px = float(closes[H - 1])
                row[f"pnl_long_{H}"] = px - entry
                for rid, side in sides.items():
                    if side is None:
                        row[f"pnl_{rid}_{H}"] = np.nan
                    else:
                        row[f"pnl_{rid}_{H}"] = side * (px - entry)
            rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, panel={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_dir_discovery_panel.parquet"), index=False)
    print(f"Panel rows={len(panel)}", flush=True)
    if panel.empty:
        raise SystemExit("Empty panel")

    # Baseline: is HIGH forward return directional at all?
    base_lines = ["# Strategy 18 — Causal Direction Discovery", "", "## HIGH forward skew (no resolver)", ""]
    base_lines.append("| Session | Split | H | n | P(up) | E[pts] |")
    base_lines.append("|---------|-------|---|---|-------|--------|")
    for sess in SESSION_PRIORITY:
        for split in ("IS", "Validation", "OOS"):
            for H in HOLD_HS:
                sub = panel[
                    (panel["session"] == sess)
                    & (panel["split"] == split)
                    & (panel["regime"] == "HIGH")
                ]
                col = f"pnl_long_{H}"
                m = summarize(sub[col].to_numpy(float))
                if m["n"] < 30:
                    continue
                base_lines.append(
                    f"| {sess} | {split} | {H} | {m['n']} | {pct(m['win'])} | {m['E']:+.2f} |"
                )
    base_lines.append("")

    results: list[dict] = []
    for rid in RESOLVER_IDS:
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < 15:
                    continue
                for H in HOLD_HS:
                    col = f"pnl_{rid}_{H}"
                    if col not in panel.columns:
                        continue
                    base = panel[
                        (panel["session"] == sess)
                        & (panel["T_offset"] == off)
                        & panel[col].notna()
                    ]
                    if len(base) < 40:
                        continue
                    for univ, mask in (
                        ("ALL", pd.Series(True, index=base.index)),
                        ("HIGH", base["regime"] == "HIGH"),
                    ):
                        u = base.loc[mask.to_numpy()]
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
                                    "resolver": rid,
                                    "session": sess,
                                    "T_offset": off,
                                    "horizon": H,
                                    "universe": univ,
                                    "split": split,
                                    **m,
                                }
                            )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_dir_discovery_results.csv"), index=False)

    def get(rid, sess, off, H, univ, split):
        s = res_df[
            (res_df["resolver"] == rid)
            & (res_df["session"] == sess)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    def pos_lift(w, e):
        return (np.isfinite(w) and w > 0 and abs(w) >= 0.01) or (
            np.isfinite(e) and e > 0 and abs(e) >= 0.25
        )

    candidates = []
    for rid in RESOLVER_IDS:
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < 15:
                    continue
                for H in HOLD_HS:
                    hb = get(rid, sess, off, H, "HIGH", "IS")
                    ab = get(rid, sess, off, H, "ALL", "IS")
                    if not hb or not ab or hb.get("n", 0) < 60 or ab.get("n", 0) < 60:
                        continue
                    hv = get(rid, sess, off, H, "HIGH", "Validation")
                    av = get(rid, sess, off, H, "ALL", "Validation")
                    ho = get(rid, sess, off, H, "HIGH", "OOS")
                    ao = get(rid, sess, off, H, "ALL", "OOS")
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
                    soft = soft_is and vo_ok and high_ok
                    strong = strong_is and vo_ok and high_ok
                    if soft or strong:
                        candidates.append(
                            {
                                "resolver": rid,
                                "session": sess,
                                "T_offset": off,
                                "horizon": H,
                                "tier": "strong" if strong else "soft",
                                "HIGH_IS_win": hb["win"],
                                "ALL_IS_win": ab["win"],
                                "lift_win_IS": lw_is,
                                "lift_win_Val": lw_v,
                                "lift_win_OOS": lw_o,
                                "HIGH_OOS_win": ho["win"],
                                "HIGH_IS_n": hb["n"],
                            }
                        )

    cand_df = pd.DataFrame(candidates) if candidates else pd.DataFrame()
    cand_df.to_csv(art("nq_dir_discovery_candidates.csv"), index=False)

    # Scoreboard: best IS lift per resolver at H30 (median across sessions' best clocks)
    lines = base_lines
    lines.append("## Resolver scoreboard (H=30, best IS lift clock per session — then median)")
    lines.append("")
    lines.append("| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS win | Survives gate? |")
    lines.append("|----------|-------------|--------------|--------------|-------------------|----------------|")

    survivors = []
    for rid in RESOLVER_IDS:
        lifts_is, lifts_v, lifts_o, oos_wins = [], [], [], []
        for sess in SESSION_PRIORITY:
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < 15:
                    continue
                hb = get(rid, sess, off, PRIMARY_H, "HIGH", "IS")
                ab = get(rid, sess, off, PRIMARY_H, "ALL", "IS")
                if not hb or not ab or hb.get("n", 0) < 40:
                    continue
                lift = hb["win"] - ab["win"]
                if best is None or lift > best["li"]:
                    hv = get(rid, sess, off, PRIMARY_H, "HIGH", "Validation")
                    av = get(rid, sess, off, PRIMARY_H, "ALL", "Validation")
                    ho = get(rid, sess, off, PRIMARY_H, "HIGH", "OOS")
                    ao = get(rid, sess, off, PRIMARY_H, "ALL", "OOS")
                    best = {
                        "li": lift,
                        "lv": (hv["win"] - av["win"]) if hv and av else np.nan,
                        "lo": (ho["win"] - ao["win"]) if ho and ao else np.nan,
                        "ho": ho["win"] if ho else np.nan,
                    }
            if best:
                lifts_is.append(best["li"])
                lifts_v.append(best["lv"])
                lifts_o.append(best["lo"])
                oos_wins.append(best["ho"])
        if not lifts_is:
            lines.append(f"| `{rid}` | — | — | — | — | no |")
            continue
        med_is = float(np.nanmedian(lifts_is))
        med_v = float(np.nanmedian(lifts_v))
        med_o = float(np.nanmedian(lifts_o))
        best_oos = float(np.nanmax(oos_wins)) if oos_wins else np.nan
        n_cand = int(((cand_df["resolver"] == rid).sum()) if len(cand_df) else 0)
        surv = "YES" if n_cand > 0 else "no"
        if n_cand > 0:
            survivors.append(rid)
        lines.append(
            f"| `{rid}` | {pp(med_is)} | {pp(med_v)} | {pp(med_o)} | {pct(best_oos)} | {surv} |"
        )
    lines.append("")

    # Multi-clock survivors
    lines.append("## Candidates (lift gate)")
    lines.append("")
    if len(cand_df) == 0:
        lines.append("**None.** No resolver cleared IS soft/strong + same-sign Val/OOS lift.")
    else:
        lines.append("| Tier | Resolver | Session | T+ | H | Lift IS | Lift Val | Lift OOS | HIGH OOS |")
        lines.append("|------|----------|---------|----|---|---------|----------|----------|----------|")
        show = cand_df.sort_values(["tier", "lift_win_IS"], ascending=[True, False])
        for _, r in show.iterrows():
            lines.append(
                f"| {r['tier']} | `{r['resolver']}` | {r['session']} | {int(r['T_offset'])} | "
                f"{int(r['horizon'])} | {pp(r['lift_win_IS'])} | {pp(r['lift_win_Val'])} | "
                f"{pp(r['lift_win_OOS'])} | {pct(r['HIGH_OOS_win'])} |"
            )
    lines.append("")

    # Stability by resolver
    multi = []
    if len(cand_df):
        for (rid, sess, H), g in cand_df.groupby(["resolver", "session", "horizon"]):
            if g["T_offset"].nunique() >= 2:
                multi.append((rid, sess, int(H), int(g["T_offset"].nunique())))

    n_strong = int((cand_df["tier"] == "strong").sum()) if len(cand_df) else 0
    n_soft = int((cand_df["tier"] == "soft").sum()) if len(cand_df) else 0

    if n_strong == 0 and n_soft == 0:
        verdict = "C_null"
        call = (
            "Clean null on this frozen menu. No causal sign rule in the scan "
            "beats unconditional inside Strategy-12 HIGH with Val/OOS lift. "
            "WHICH WAY is not recoverable from these observables without new information."
        )
    elif multi:
        verdict = "B_lead"
        call = (
            f"Leads with multi-clock candidates: {multi[:8]}. "
            "Promote only as a dedicated dossier — do not trade yet."
        )
    else:
        verdict = "B->kill"
        call = (
            f"Soft/strong cells={n_soft + n_strong} but no multi-clock stability. "
            "Do not promote; do not expand the menu ad hoc to rescue."
        )

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict}`**")
    lines.append("")
    lines.append(call)
    lines.append("")
    lines.append("### What this means")
    lines.append("")
    lines.append("- Strategy 12 (WHEN) remains valid.")
    lines.append("- This scan does not authorize a direction strategy.")
    if verdict == "C_null":
        lines.append(
            "- Next: new data/modality (inventory proxies, auction, options with lag) "
            "or accept that activity gating alone cannot yield direction here."
        )
    lines.append("")

    art("nq_dir_discovery_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_dir_discovery_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
                "survivors": survivors,
                "multi_clock": multi,
                "call": call,
                "menu": list(RESOLVER_IDS),
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
