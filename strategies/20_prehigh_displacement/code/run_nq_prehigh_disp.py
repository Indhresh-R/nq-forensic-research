"""
Strategy 20 — Pre-HIGH unusual displacement / initiative

Not ordinary momentum follow. Only when |disp|/psr or |path_imb|/psr
>= IS p66 (session x offset), side = sign(metric).

Lift = HIGH - ALL, win-lift gates. Strategy 12 frozen. W=30 frozen.
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
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_PRIORITY = ("LONDON", "NY_PM", "NY_AM", "ASIA")
W = 30
OUTCOMES = ("H30", "H60", "SESS_END")
RESOLVERS = ("disp_follow", "path_follow")

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


def pre_metrics(to_T: pd.DataFrame, psr: float, W: int) -> dict[str, float] | None:
    if len(to_T) < W + 2 or not np.isfinite(psr) or psr <= 0:
        return None
    c = to_T["close"].to_numpy(float)
    close_T = float(c[-1])
    close_w = float(c[-(W + 1)])
    disp = close_T - close_w
    d = np.diff(c[-(W + 1) :])
    up = float(np.sum(d[d > 0]))
    dn = float(np.sum(-d[d < 0]))
    path_imb = up - dn
    return {
        "disp": disp,
        "disp_psr": disp / psr,
        "abs_disp_psr": abs(disp) / psr,
        "path_imb": path_imb,
        "path_imb_psr": path_imb / psr,
        "abs_path_psr": abs(path_imb) / psr,
    }


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
    print("=== Strategy 20: Pre-HIGH unusual displacement ===", flush=True)
    print(f"W={W}; unusual=IS p66 |metric|/psr; outcomes={OUTCOMES}", flush=True)

    df = load_nq()
    facts = build_session_facts(df)
    facts_idx = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}

    sess_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=False):
        for name in SESSION_PRIORITY:
            key = (sd, name)
            if key not in facts_idx:
                continue
            b = bars_in_session(g, name)
            if len(b) >= 50:
                sess_bars[key] = b

    raw_rows: list[dict] = []
    n_done = 0
    for (sd, name), bars in sess_bars.items():
        fr = facts_idx[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        for off in SESSION_DECISION_OFFSETS[name]:
            if off < W:
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
            met = pre_metrics(to_T, psr, W)
            if met is None:
                continue
            after = after_bars(bars, T, name)
            if len(after) < 30:
                continue
            entry = float(after.iloc[0]["open"])
            closes = after["close"].to_numpy(float)
            end_px = float(after.iloc[-1]["close"])
            reg = regime_of(name, off, float(st["rng_psr"]))
            row = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                **met,
                "pnl_long_H30": float(closes[29]) - entry,
                "pnl_long_H60": (
                    float(closes[59]) - entry if len(closes) >= 60 else np.nan
                ),
                "pnl_long_SESS_END": end_px - entry,
            }
            raw_rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, raw={len(raw_rows)}", flush=True)

    raw = pd.DataFrame(raw_rows)
    print(f"Raw panel={len(raw)}", flush=True)

    # IS p66 thresholds per session x offset
    unusual_thr: dict[str, dict[int, dict[str, float]]] = {}
    is_p = raw[raw["split"] == "IS"]
    for sess in SESSION_PRIORITY:
        unusual_thr[sess] = {}
        for off in SESSION_DECISION_OFFSETS[sess]:
            if off < W:
                continue
            sub = is_p[(is_p["session"] == sess) & (is_p["T_offset"] == off)]
            if len(sub) < 80:
                continue
            unusual_thr[sess][off] = {
                "abs_disp_psr": float(sub["abs_disp_psr"].quantile(0.66)),
                "abs_path_psr": float(sub["abs_path_psr"].quantile(0.66)),
            }
    art("nq_prehigh_disp_thresholds_IS.json").write_text(
        json.dumps(
            {s: {str(k): v for k, v in d.items()} for s, d in unusual_thr.items()},
            indent=2,
        ),
        encoding="utf-8",
    )

    # Apply unusual flags + signed pnls
    rows = []
    for _, r in raw.iterrows():
        sess = r["session"]
        off = int(r["T_offset"])
        thr = unusual_thr.get(sess, {}).get(off)
        if not thr:
            continue
        disp_u = float(r["abs_disp_psr"]) >= thr["abs_disp_psr"]
        path_u = float(r["abs_path_psr"]) >= thr["abs_path_psr"]
        side_disp = (
            (1 if r["disp"] > 0 else -1) if disp_u and abs(r["disp"]) >= 0.25 else None
        )
        side_path = (
            (1 if r["path_imb"] > 0 else -1)
            if path_u and abs(r["path_imb"]) >= 0.25
            else None
        )
        out = {
            "session_date": r["session_date"],
            "session": sess,
            "year": int(r["year"]),
            "split": r["split"],
            "T_offset": off,
            "regime": r["regime"],
            "disp_unusual": int(disp_u),
            "path_unusual": int(path_u),
            "side_disp": side_disp if side_disp is not None else 0,
            "side_path": side_path if side_path is not None else 0,
            "has_disp": side_disp is not None,
            "has_path": side_path is not None,
        }
        for outcome, long_col in (
            ("H30", "pnl_long_H30"),
            ("H60", "pnl_long_H60"),
            ("SESS_END", "pnl_long_SESS_END"),
        ):
            long_pnl = r[long_col]
            out[f"pnl_long_{outcome}"] = long_pnl
            if side_disp is not None and np.isfinite(long_pnl):
                out[f"pnl_disp_follow_{outcome}"] = side_disp * long_pnl
            else:
                out[f"pnl_disp_follow_{outcome}"] = np.nan
            if side_path is not None and np.isfinite(long_pnl):
                out[f"pnl_path_follow_{outcome}"] = side_path * long_pnl
            else:
                out[f"pnl_path_follow_{outcome}"] = np.nan
        rows.append(out)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_prehigh_disp_panel.parquet"), index=False)
    print(
        f"Panel={len(panel)} disp_unusual%={100*panel['disp_unusual'].mean():.1f} "
        f"path_unusual%={100*panel['path_unusual'].mean():.1f}",
        flush=True,
    )

    results = []
    for rid, col_prefix, has_col in (
        ("disp_follow", "pnl_disp_follow", "has_disp"),
        ("path_follow", "pnl_path_follow", "has_path"),
    ):
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < W:
                    continue
                for outcome in OUTCOMES:
                    col = f"{col_prefix}_{outcome}"
                    base = panel[
                        (panel["session"] == sess)
                        & (panel["T_offset"] == off)
                        & panel[has_col]
                        & panel[col].notna()
                    ]
                    if len(base) < 30:
                        continue
                    for univ, mask in (
                        ("ALL", pd.Series(True, index=base.index)),
                        ("HIGH", base["regime"] == "HIGH"),
                    ):
                        u = base.loc[mask.to_numpy()]
                        for split in ("IS", "Validation", "OOS"):
                            s = u[u["split"] == split]
                            m = summarize(s[col].to_numpy(float))
                            if m["n"] < 15:
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
    res_df.to_csv(art("nq_prehigh_disp_results.csv"), index=False)

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

    candidates = []
    for rid in RESOLVERS:
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
                if off < W:
                    continue
                for outcome in OUTCOMES:
                    hb = get(rid, sess, off, outcome, "HIGH", "IS")
                    ab = get(rid, sess, off, outcome, "ALL", "IS")
                    if not hb or not ab or hb.get("n", 0) < 40 or ab.get("n", 0) < 40:
                        continue
                    hv = get(rid, sess, off, outcome, "HIGH", "Validation")
                    av = get(rid, sess, off, outcome, "ALL", "Validation")
                    ho = get(rid, sess, off, outcome, "HIGH", "OOS")
                    ao = get(rid, sess, off, outcome, "ALL", "OOS")
                    if not hv or not av or not ho or not ao:
                        continue
                    if hv.get("n", 0) < 15 or ho.get("n", 0) < 12:
                        continue
                    lw_is = hb["win"] - ab["win"]
                    lw_v = hv["win"] - av["win"]
                    lw_o = ho["win"] - ao["win"]
                    soft = (
                        lw_is >= 0.03
                        and lw_v >= 0.01
                        and lw_o >= 0.01
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
                                "HIGH_IS_n": hb["n"],
                                "HIGH_IS_win": hb["win"],
                                "ALL_IS_win": ab["win"],
                                "lift_win_IS": lw_is,
                                "lift_win_Val": lw_v,
                                "lift_win_OOS": lw_o,
                                "HIGH_OOS_win": ho["win"],
                            }
                        )

    cand_df = pd.DataFrame(candidates) if candidates else pd.DataFrame()
    cand_df.to_csv(art("nq_prehigh_disp_candidates.csv"), index=False)

    lines = [
        "# Strategy 20 — Pre-HIGH Unusual Displacement",
        "",
        "## Freeze",
        "",
        f"- W={W}m into T; unusual = IS p66 of |metric|/psr",
        "- Resolvers: `disp_follow`, `path_follow` (skip if not unusual)",
        f"- Outcomes: {list(OUTCOMES)}",
        "- Win-lift gates only; Strategy 12 untouched",
        f"- Panel rows: **{len(panel):,}**",
        f"- Soft: **{int((cand_df['tier']=='soft').sum()) if len(cand_df) else 0}**",
        f"- Strong: **{int((cand_df['tier']=='strong').sum()) if len(cand_df) else 0}**",
        "",
    ]

    for outcome in OUTCOMES:
        lines.append(f"## Scoreboard {outcome} (best IS win-lift → median across sessions)")
        lines.append("")
        lines.append(
            "| Resolver | Med lift IS | Med lift Val | Med lift OOS | Best HIGH OOS | Cells |"
        )
        lines.append(
            "|----------|-------------|--------------|--------------|---------------|-------|"
        )
        for rid in RESOLVERS:
            lis, lv, lo, hoo = [], [], [], []
            for sess in SESSION_PRIORITY:
                best = None
                for off in SESSION_DECISION_OFFSETS[sess]:
                    if off < W:
                        continue
                    hb = get(rid, sess, off, outcome, "HIGH", "IS")
                    ab = get(rid, sess, off, outcome, "ALL", "IS")
                    if not hb or not ab or hb.get("n", 0) < 30:
                        continue
                    lift = hb["win"] - ab["win"]
                    if best is None or lift > best["li"]:
                        hv = get(rid, sess, off, outcome, "HIGH", "Validation")
                        av = get(rid, sess, off, outcome, "ALL", "Validation")
                        ho = get(rid, sess, off, outcome, "HIGH", "OOS")
                        ao = get(rid, sess, off, outcome, "ALL", "OOS")
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
                int(
                    (
                        (cand_df["resolver"] == rid) & (cand_df["outcome"] == outcome)
                    ).sum()
                )
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

    lines.append("## Candidates")
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
    multi_strong = [m for m in multi if m["n_clocks"] >= 2 and m["n_strong"] >= 1]

    if n_strong == 0 and n_soft == 0:
        verdict = "C"
        call = (
            "Kill 20. Unusual pre-HIGH displacement/path initiative does not "
            "provide stable conditional direction vs unconditional."
        )
    elif multi_strong:
        verdict = "B_lead"
        call = f"Multi-clock leads: {multi_strong}. Freeze for review — not a trade yet."
    else:
        verdict = "B->kill"
        call = (
            f"Soft/strong={n_soft + n_strong} without multi-clock strength. "
            "Do not retune W/p66. Do not fall back to ordinary mom follow."
        )

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict}`**")
    lines.append("")
    lines.append(call)
    lines.append("")
    lines.append("### Discipline")
    lines.append("")
    lines.append("- This is initiative-*unusual*, not generic follow.")
    lines.append("- Strategy 12 remains WHEN-only.")
    lines.append("")

    art("nq_prehigh_disp_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_prehigh_disp_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
                "multi": multi,
                "call": call,
                "W": W,
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
