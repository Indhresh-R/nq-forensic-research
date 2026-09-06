"""
Strategy 21 — First post-HIGH directional displacement (revelation)

Frozen BEFORE results:
  bar1_follow: first 1m bar after T; side=sign(c-o); entry=next open
  bar5_follow: first 5m block after T; side=sign(c-o); entry=next open

Resolver-only. Lift = HIGH - ALL, win-lift gates.
Residual-left is diagnostic only — never selects the window.
Strategy 12 frozen.
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
OUTCOMES = ("H30", "H60", "SESS_END")
RESOLVERS = ("bar1_follow", "bar5_follow")

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


def residual_pts(after_from_entry: pd.DataFrame, entry: float, H: int) -> float:
    if len(after_from_entry) < 1 or not np.isfinite(entry):
        return np.nan
    w = after_from_entry.iloc[:H]
    if len(w) == 0:
        return np.nan
    hi = float(w["high"].max())
    lo = float(w["low"].min())
    return float(max(hi - entry, entry - lo))


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


def pts(x: Any) -> str:
    return f"{x:.1f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== Strategy 21: First post-HIGH directional displacement ===", flush=True)
    print(
        "Frozen: bar1_follow (1m) + bar5_follow (5m block); "
        f"outcomes={OUTCOMES}; residual diagnostic only",
        flush=True,
    )

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
        for off in SESSION_DECISION_OFFSETS[name]:
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars, session=name, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            after = after_bars(bars, T, name)
            # Need room for bar5 entry + H60
            if len(after) < 70:
                continue
            reg = regime_of(name, off, float(st["rng_psr"]))

            # Immediate residual from first open after T (diagnostic burn baseline)
            t_entry = float(after.iloc[0]["open"])
            resid_T_30 = residual_pts(after, t_entry, 30)

            # --- bar1 ---
            b1 = after.iloc[0]
            d1 = float(b1["close"]) - float(b1["open"])
            side1 = 1 if d1 > 0 else (-1 if d1 < 0 else 0)
            e1 = float(after.iloc[1]["open"])
            from1 = after.iloc[1:].reset_index(drop=True)
            c1 = from1["close"].to_numpy(float)
            end1 = float(from1.iloc[-1]["close"])
            resid1_30 = residual_pts(from1, e1, 30)
            resid1_45 = residual_pts(from1, e1, 45)

            # --- bar5 ---
            o5 = float(after.iloc[0]["open"])
            c5 = float(after.iloc[4]["close"])
            d5 = c5 - o5
            side5 = 1 if d5 > 0 else (-1 if d5 < 0 else 0)
            e5 = float(after.iloc[5]["open"])
            from5 = after.iloc[5:].reset_index(drop=True)
            c5a = from5["close"].to_numpy(float)
            end5 = float(from5.iloc[-1]["close"])
            resid5_30 = residual_pts(from5, e5, 30)
            resid5_45 = residual_pts(from5, e5, 45)

            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                "psr": psr,
                "rng_psr": float(st["rng_psr"]),
                "resid_T_30": resid_T_30,
                "side_bar1": side1,
                "has_bar1": side1 != 0,
                "entry_bar1": e1,
                "resid_bar1_30": resid1_30,
                "resid_bar1_45": resid1_45,
                "resid_burn_bar1": (
                    resid_T_30 - resid1_30
                    if np.isfinite(resid_T_30) and np.isfinite(resid1_30)
                    else np.nan
                ),
                "side_bar5": side5,
                "has_bar5": side5 != 0,
                "entry_bar5": e5,
                "resid_bar5_30": resid5_30,
                "resid_bar5_45": resid5_45,
                "resid_burn_bar5": (
                    resid_T_30 - resid5_30
                    if np.isfinite(resid_T_30) and np.isfinite(resid5_30)
                    else np.nan
                ),
            }

            # Long pnls from each entry; signed applied later
            row["pnl_long_bar1_H30"] = float(c1[29]) - e1 if len(c1) >= 30 else np.nan
            row["pnl_long_bar1_H60"] = float(c1[59]) - e1 if len(c1) >= 60 else np.nan
            row["pnl_long_bar1_SESS_END"] = end1 - e1
            row["pnl_long_bar5_H30"] = float(c5a[29]) - e5 if len(c5a) >= 30 else np.nan
            row["pnl_long_bar5_H60"] = float(c5a[59]) - e5 if len(c5a) >= 60 else np.nan
            row["pnl_long_bar5_SESS_END"] = end5 - e5

            for outcome in OUTCOMES:
                long1 = row[f"pnl_long_bar1_{outcome}"]
                long5 = row[f"pnl_long_bar5_{outcome}"]
                if side1 != 0 and np.isfinite(long1):
                    row[f"pnl_bar1_follow_{outcome}"] = side1 * float(long1)
                else:
                    row[f"pnl_bar1_follow_{outcome}"] = np.nan
                if side5 != 0 and np.isfinite(long5):
                    row[f"pnl_bar5_follow_{outcome}"] = side5 * float(long5)
                else:
                    row[f"pnl_bar5_follow_{outcome}"] = np.nan

            rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, rows={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_posthigh_first_panel.parquet"), index=False)
    print(
        f"Panel={len(panel)} HIGH%={100 * (panel['regime'] == 'HIGH').mean():.1f} "
        f"bar1_nonzero%={100 * panel['has_bar1'].mean():.1f} "
        f"bar5_nonzero%={100 * panel['has_bar5'].mean():.1f}",
        flush=True,
    )

    results = []
    for rid, col_prefix, has_col in (
        ("bar1_follow", "pnl_bar1_follow", "has_bar1"),
        ("bar5_follow", "pnl_bar5_follow", "has_bar5"),
    ):
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
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
    res_df.to_csv(art("nq_posthigh_first_results.csv"), index=False)

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
                                "tier": "strong" if strong else "soft",
                                "resolver": rid,
                                "session": sess,
                                "T_offset": off,
                                "outcome": outcome,
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
    cand_df.to_csv(art("nq_posthigh_first_candidates.csv"), index=False)

    # Residual diagnostic (HIGH only) — not used for resolver selection
    resid_lines = [
        "## Residual left at revelation entry (HIGH, diagnostic)",
        "",
        "| Resolver | Session | Split | n | Mean resid@T H30 | Mean resid@entry H30 | Mean burn | Mean resid/psr |",
        "|----------|---------|-------|---|------------------|----------------------|-----------|----------------|",
    ]
    for rid, side_col, resid_col in (
        ("bar1_follow", "has_bar1", "resid_bar1_30"),
        ("bar5_follow", "has_bar5", "resid_bar5_30"),
    ):
        for sess in SESSION_PRIORITY:
            for split in ("IS", "Validation", "OOS"):
                sub = panel[
                    (panel["session"] == sess)
                    & (panel["split"] == split)
                    & (panel["regime"] == "HIGH")
                    & panel[side_col]
                ]
                if len(sub) < 30:
                    continue
                rt = sub["resid_T_30"]
                re = sub[resid_col]
                burn = sub[f"resid_burn_{'bar1' if 'bar1' in rid else 'bar5'}"]
                resid_lines.append(
                    f"| `{rid}` | {sess} | {split} | {len(sub)} | "
                    f"{pts(float(rt.mean()))} | {pts(float(re.mean()))} | "
                    f"{pts(float(burn.mean()))} | "
                    f"{pts(float((re / sub['psr']).mean()))} |"
                )
    resid_lines.append("")

    lines = [
        "# Strategy 21 — First Post-HIGH Directional Displacement",
        "",
        "## Freeze (locked before run)",
        "",
        "- `bar1_follow`: first 1m bar after T; entry next open",
        "- `bar5_follow`: first 5m block after T; entry next open",
        "- Outcomes from entry: H30 / H60 / SESS_END",
        "- Win-lift HIGH−ALL only; Strategy 12 untouched",
        "- Residual-left tables are diagnostic — **not** used to pick 1m vs 5m",
        f"- Panel rows: **{len(panel):,}**",
        f"- Soft: **{int((cand_df['tier']=='soft').sum()) if len(cand_df) else 0}**",
        f"- Strong: **{int((cand_df['tier']=='strong').sum()) if len(cand_df) else 0}**",
        "",
    ]

    for outcome in OUTCOMES:
        lines.append(
            f"## Scoreboard {outcome} (best IS win-lift clock per session -> median)"
        )
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
                    f"| `{rid}` | {pp(float(np.nanmedian(lis)))} | "
                    f"{pp(float(np.nanmedian(lv)))} | {pp(float(np.nanmedian(lo)))} | "
                    f"{pct(float(np.nanmax(hoo)))} | {ncell} |"
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
    lines.extend(resid_lines)

    multi = []
    if len(cand_df):
        for (rid, sess, outcome), g in cand_df.groupby(
            ["resolver", "session", "outcome"]
        ):
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
            "Kill 21. First post-HIGH bar displacement does not provide stable "
            "conditional direction on the remaining path."
        )
    elif multi_strong:
        verdict = "B_lead"
        call = (
            f"Multi-clock leads: {multi_strong}. Freeze for review — not a trade. "
            "Residual-left is still diagnostic only; no HOW yet."
        )
    else:
        verdict = "B->kill"
        call = (
            f"Soft/strong={n_soft + n_strong} without multi-clock strength. "
            "Do not retune 1m/5m from residuals. Do not open stops/targets to rescue."
        )

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict}`**")
    lines.append("")
    lines.append(call)
    lines.append("")
    lines.append("### Discipline")
    lines.append("")
    lines.append("- Revelation class: information only after HIGH.")
    lines.append("- Residual tables did not select the window.")
    lines.append("- Strategy 12 remains WHEN-only.")
    lines.append("")

    art("nq_posthigh_first_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_posthigh_first_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
                "multi": multi,
                "call": call,
                "resolvers": list(RESOLVERS),
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"Verdict: {verdict}", flush=True)
    print(call, flush=True)
    print(f"Wrote {art('nq_posthigh_first_report.md')}", flush=True)


if __name__ == "__main__":
    main()
