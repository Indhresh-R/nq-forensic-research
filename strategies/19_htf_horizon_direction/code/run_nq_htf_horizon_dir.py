"""
Strategy 19 — Longer-horizon direction under Strategy-12 HIGH

Outcomes (frozen): H240, SESS_END
Sign menu (frozen): gap_follow, prior_day_color, prior_sess_mid,
  sess_open_follow, vwap_follow, mom15_follow

Lift = HIGH - ALL. No stops/targets. Strategy 12 untouched.
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
    PRIOR_SESSION,
    SESSION_DECISION_OFFSETS,
    SESSION_START,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_PRIORITY = ("LONDON", "NY_PM", "NY_AM", "ASIA")
OUTCOMES = ("H240", "SESS_END")
RESOLVERS = (
    "gap_follow",
    "prior_day_color",
    "prior_sess_mid",
    "sess_open_follow",
    "vwap_follow",
    "mom15_follow",
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


def sgn(x: float, eps: float = 0.25) -> int | None:
    if not np.isfinite(x) or abs(x) < eps:
        return None
    return 1 if x > 0 else -1


def session_vwap(to_T: pd.DataFrame) -> float | None:
    if len(to_T) < 3:
        return None
    tp = (
        to_T["high"].to_numpy(float)
        + to_T["low"].to_numpy(float)
        + to_T["close"].to_numpy(float)
    ) / 3.0
    vol = to_T["volume"].to_numpy(float) if "volume" in to_T.columns else np.ones(len(to_T))
    if np.nansum(vol) <= 0:
        return float(np.nanmean(tp))
    return float(np.nansum(tp * vol) / np.nansum(vol))


def build_daily(df: pd.DataFrame) -> dict:
    rows = []
    for sd, g in df.groupby("session_date", sort=True):
        if len(g) < 60:
            continue
        g = g.sort_values("ts")
        o = float(g.iloc[0]["open"])
        c = float(g.iloc[-1]["close"])
        rows.append({"session_date": sd, "day_open": o, "day_close": c})
    daily = pd.DataFrame(rows).sort_values("session_date")
    daily["prior_open"] = daily["day_open"].shift(1)
    daily["prior_close"] = daily["day_close"].shift(1)
    daily["prior_color"] = np.sign(daily["prior_close"] - daily["prior_open"])
    return {r["session_date"]: r for _, r in daily.iterrows()}


def summarize(x: np.ndarray) -> dict[str, float]:
    v = x[np.isfinite(x)]
    if len(v) == 0:
        return {"n": 0, "win": np.nan, "E": np.nan}
    return {
        "n": int(len(v)),
        "win": float(win_rate(pd.Series(v))["rate"]),
        "E": float(np.mean(v)),
    }


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pp(x: Any) -> str:
    return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== Strategy 19: Longer-horizon direction (H240 / SESS_END) ===", flush=True)
    df = load_nq()
    daily_map = build_daily(df)
    facts = build_session_facts(df)
    facts_idx = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}
    dates = sorted(facts["session_date"].unique(), key=lambda d: str(d))
    date_i = {d: i for i, d in enumerate(dates)}

    def prior_sess_mid(sd, name: str) -> float | None:
        if name == "ASIA":
            i = date_i.get(sd)
            if i is None or i == 0:
                return None
            fr = facts_idx.get((dates[i - 1], "NY_PM"))
        else:
            fr = facts_idx.get((sd, PRIOR_SESSION[name]))
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
        psm = prior_sess_mid(sd, name)
        dr = daily_map.get(sd)
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
            close_T = float(to_T.iloc[-1]["close"])
            c = to_T["close"].to_numpy(float)
            sides: dict[str, int | None] = {
                "sess_open_follow": sgn(close_T - session_open),
                "prior_sess_mid": sgn(close_T - float(psm)) if psm is not None else None,
                "mom15_follow": sgn(close_T - float(c[-16])) if len(c) > 15 else None,
            }
            vw = session_vwap(to_T)
            sides["vwap_follow"] = sgn(close_T - vw) if vw is not None else None
            if dr is not None and np.isfinite(dr.get("prior_close", np.nan)):
                sides["gap_follow"] = sgn(session_open - float(dr["prior_close"]))
                pc = dr.get("prior_color", 0)
                sides["prior_day_color"] = (
                    int(pc) if abs(float(pc)) > 0.5 else None
                )
            else:
                sides["gap_follow"] = None
                sides["prior_day_color"] = None

            after = after_bars(bars, T, name)
            if len(after) < 5:
                continue
            entry = float(after.iloc[0]["open"])
            end_px = float(after.iloc[-1]["close"])
            reg = regime_of(name, off, float(st["rng_psr"]))
            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                "pnl_long_SESS_END": end_px - entry,
                "pnl_long_H240": (
                    float(after.iloc[239]["close"]) - entry
                    if len(after) >= 240
                    else np.nan
                ),
            }
            for rid in RESOLVERS:
                side = sides.get(rid)
                if side is None:
                    row[f"pnl_{rid}_SESS_END"] = np.nan
                    row[f"pnl_{rid}_H240"] = np.nan
                else:
                    row[f"pnl_{rid}_SESS_END"] = side * (end_px - entry)
                    row[f"pnl_{rid}_H240"] = (
                        side * (float(after.iloc[239]["close"]) - entry)
                        if len(after) >= 240
                        else np.nan
                    )
            rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, panel={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_htf_horizon_panel.parquet"), index=False)
    print(f"Panel rows={len(panel)}", flush=True)
    if panel.empty:
        raise SystemExit("Empty panel")

    # HIGH long skew at long horizons
    lines = [
        "# Strategy 19 — Longer-Horizon Direction under Strategy-12 HIGH",
        "",
        "## HIGH forward skew (no resolver)",
        "",
        "| Session | Outcome | Split | n | P(up) | E[pts] |",
        "|---------|---------|-------|---|-------|--------|",
    ]
    for sess in SESSION_PRIORITY:
        for outcome in OUTCOMES:
            for split in ("IS", "Validation", "OOS"):
                col = f"pnl_long_{outcome}"
                sub = panel[
                    (panel["session"] == sess)
                    & (panel["split"] == split)
                    & (panel["regime"] == "HIGH")
                    & panel[col].notna()
                ]
                m = summarize(sub[col].to_numpy(float))
                if m["n"] < 25:
                    continue
                lines.append(
                    f"| {sess} | {outcome} | {split} | {m['n']} | {pct(m['win'])} | {m['E']:+.2f} |"
                )
    lines.append("")

    results: list[dict] = []
    for rid in RESOLVERS:
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < 15:
                    continue
                for outcome in OUTCOMES:
                    col = f"pnl_{rid}_{outcome}"
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
                        for split in ("IS", "Validation", "OOS"):
                            s = u[u["split"] == split]
                            m = summarize(s[col].to_numpy(float))
                            if m["n"] < 20 and split in ("IS", "Validation", "OOS"):
                                continue
                            results.append(
                                {
                                    "resolver": rid,
                                    "session": sess,
                                    "T_offset": off,
                                    "outcome": outcome,
                                    "universe": univ,
                                    "split": split,
                                    **m,
                                }
                            )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_htf_horizon_results.csv"), index=False)

    def get(rid, sess, off, outcome, univ, split):
        s = res_df[
            (res_df["resolver"] == rid)
            & (res_df["session"] == sess)
            & (res_df["T_offset"] == off)
            & (res_df["outcome"] == outcome)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    def pos_win_lift(w: float) -> bool:
        return np.isfinite(w) and w >= 0.01

    candidates = []
    for rid in RESOLVERS:
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < 15:
                    continue
                for outcome in OUTCOMES:
                    hb = get(rid, sess, off, outcome, "HIGH", "IS")
                    ab = get(rid, sess, off, outcome, "ALL", "IS")
                    if not hb or not ab or hb.get("n", 0) < 50 or ab.get("n", 0) < 50:
                        continue
                    hv = get(rid, sess, off, outcome, "HIGH", "Validation")
                    av = get(rid, sess, off, outcome, "ALL", "Validation")
                    ho = get(rid, sess, off, outcome, "HIGH", "OOS")
                    ao = get(rid, sess, off, outcome, "ALL", "OOS")
                    if not hv or not av or not ho or not ao:
                        continue
                    if hv.get("n", 0) < 20 or ho.get("n", 0) < 15:
                        continue
                    lw_is = hb["win"] - ab["win"]
                    lw_v = hv["win"] - av["win"]
                    lw_o = ho["win"] - ao["win"]
                    # Win-lift only (tighter than discovery E-gate)
                    soft = (
                        lw_is >= 0.03
                        and pos_win_lift(lw_v)
                        and pos_win_lift(lw_o)
                        and hb["win"] >= 0.52
                    )
                    strong = (
                        lw_is >= 0.05
                        and lw_v >= 0.02
                        and lw_o >= 0.02
                        and hb["win"] >= 0.53
                    )
                    if soft or strong:
                        candidates.append(
                            {
                                "resolver": rid,
                                "session": sess,
                                "T_offset": off,
                                "outcome": outcome,
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
    cand_df.to_csv(art("nq_htf_horizon_candidates.csv"), index=False)

    lines.append("## Scoreboard — SESS_END (best IS win-lift clock per session, then median)")
    lines.append("")
    lines.append("| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Gate cells |")
    lines.append("|----------|-------------|--------------|--------------|---------------|------------|")
    for rid in RESOLVERS:
        lis, lv, lo, hoo = [], [], [], []
        for sess in SESSION_PRIORITY:
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < 15:
                    continue
                hb = get(rid, sess, off, "SESS_END", "HIGH", "IS")
                ab = get(rid, sess, off, "SESS_END", "ALL", "IS")
                if not hb or not ab or hb.get("n", 0) < 40:
                    continue
                lift = hb["win"] - ab["win"]
                if best is None or lift > best["li"]:
                    hv = get(rid, sess, off, "SESS_END", "HIGH", "Validation")
                    av = get(rid, sess, off, "SESS_END", "ALL", "Validation")
                    ho = get(rid, sess, off, "SESS_END", "HIGH", "OOS")
                    ao = get(rid, sess, off, "SESS_END", "ALL", "OOS")
                    best = {
                        "li": lift,
                        "lv": (hv["win"] - av["win"]) if hv and av else np.nan,
                        "lo": (ho["win"] - ao["win"]) if ho and ao else np.nan,
                        "ho": ho["win"] if ho else np.nan,
                    }
            if best:
                lis.append(best["li"])
                lv.append(best["lv"])
                lo.append(best["lo"])
                hoo.append(best["ho"])
        ncell = int((cand_df["resolver"] == rid).sum()) if len(cand_df) else 0
        if not lis:
            lines.append(f"| `{rid}` | — | — | — | — | 0 |")
        else:
            lines.append(
                f"| `{rid}` | {pp(float(np.nanmedian(lis)))} | {pp(float(np.nanmedian(lv)))} | "
                f"{pp(float(np.nanmedian(lo)))} | {pct(float(np.nanmax(hoo)))} | {ncell} |"
            )
    lines.append("")

    lines.append("## Scoreboard — H240 (same)")
    lines.append("")
    lines.append("| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Gate cells |")
    lines.append("|----------|-------------|--------------|--------------|---------------|------------|")
    for rid in RESOLVERS:
        lis, lv, lo, hoo = [], [], [], []
        for sess in SESSION_PRIORITY:
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < 15:
                    continue
                hb = get(rid, sess, off, "H240", "HIGH", "IS")
                ab = get(rid, sess, off, "H240", "ALL", "IS")
                if not hb or not ab or hb.get("n", 0) < 40:
                    continue
                lift = hb["win"] - ab["win"]
                if best is None or lift > best["li"]:
                    hv = get(rid, sess, off, "H240", "HIGH", "Validation")
                    av = get(rid, sess, off, "H240", "ALL", "Validation")
                    ho = get(rid, sess, off, "H240", "HIGH", "OOS")
                    ao = get(rid, sess, off, "H240", "ALL", "OOS")
                    best = {
                        "li": lift,
                        "lv": (hv["win"] - av["win"]) if hv and av else np.nan,
                        "lo": (ho["win"] - ao["win"]) if ho and ao else np.nan,
                        "ho": ho["win"] if ho else np.nan,
                    }
            if best:
                lis.append(best["li"])
                lv.append(best["lv"])
                lo.append(best["lo"])
                hoo.append(best["ho"])
        ncell = (
            int(((cand_df["resolver"] == rid) & (cand_df["outcome"] == "H240")).sum())
            if len(cand_df)
            else 0
        )
        if not lis:
            lines.append(f"| `{rid}` | — | — | — | — | 0 |")
        else:
            lines.append(
                f"| `{rid}` | {pp(float(np.nanmedian(lis)))} | {pp(float(np.nanmedian(lv)))} | "
                f"{pp(float(np.nanmedian(lo)))} | {pct(float(np.nanmax(hoo)))} | {ncell} |"
            )
    lines.append("")

    lines.append("## Candidates (win-lift gate only)")
    lines.append("")
    if len(cand_df) == 0:
        lines.append("**None.**")
    else:
        lines.append(
            "| Tier | Resolver | Session | Outcome | T+ | Lift IS | Lift Val | Lift OOS | HIGH OOS |"
        )
        lines.append(
            "|------|----------|---------|---------|----|---------|----------|----------|----------|"
        )
        show = cand_df.sort_values(["tier", "lift_win_IS"], ascending=[True, False])
        for _, r in show.iterrows():
            lines.append(
                f"| {r['tier']} | `{r['resolver']}` | {r['session']} | {r['outcome']} | "
                f"{int(r['T_offset'])} | {pp(r['lift_win_IS'])} | {pp(r['lift_win_Val'])} | "
                f"{pp(r['lift_win_OOS'])} | {pct(r['HIGH_OOS_win'])} |"
            )
    lines.append("")

    multi = []
    if len(cand_df):
        for (rid, sess, outcome), g in cand_df.groupby(["resolver", "session", "outcome"]):
            if g["T_offset"].nunique() >= 2:
                multi.append(
                    {
                        "resolver": rid,
                        "session": sess,
                        "outcome": outcome,
                        "n_clocks": int(g["T_offset"].nunique()),
                        "n_strong": int((g["tier"] == "strong").sum()),
                    }
                )

    n_strong = int((cand_df["tier"] == "strong").sum()) if len(cand_df) else 0
    n_soft = int((cand_df["tier"] == "soft").sum()) if len(cand_df) else 0
    multi_strong = [m for m in multi if m["n_strong"] >= 1 and m["n_clocks"] >= 2]

    if n_strong == 0 and n_soft == 0:
        verdict = "C_null"
        call = (
            "Longer horizons do not unlock WHICH WAY for this frozen menu. "
            "HIGH remains roughly undirected even to session end / H240."
        )
    elif multi_strong:
        verdict = "B_lead"
        call = (
            f"Multi-clock leads: {multi_strong}. Dedicated follow-up dossier only — not a trade."
        )
    else:
        verdict = "B->kill"
        call = (
            f"Soft/strong cells={n_soft + n_strong} without multi-clock strength. Do not promote."
        )

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict}`**")
    lines.append("")
    lines.append(call)
    lines.append("")
    lines.append("### Discipline")
    lines.append("")
    lines.append("- Win-lift gates only (no E-lift rescue).")
    lines.append("- Strategy 12 untouched.")
    lines.append("")

    art("nq_htf_horizon_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_htf_horizon_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
                "multi": multi,
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
