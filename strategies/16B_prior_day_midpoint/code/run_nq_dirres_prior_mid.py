"""
Hypothesis 16B — Prior Globex day midpoint LOCATION as resolver under Strategy-12 HIGH

Resolver-only. One frozen rule:
  side = sign(close_T - prior_mid), prior_mid = (prior_high + prior_low) / 2

NOT 16A candle color. NOT PDH/PDL fishing. No stops/targets.
Strategy 12 terciles frozen (WHEN only — do not retune).
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
HOLD_HS = (15, 30, 60, 90, 120)
PRIMARY_HS = (30, 60)

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


def build_globex_daily(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for sd, g in df.groupby("session_date", sort=True):
        if len(g) < 60:
            continue
        g = g.sort_values("ts")
        o = float(g.iloc[0]["open"])
        h = float(g["high"].max())
        l = float(g["low"].min())
        c = float(g.iloc[-1]["close"])
        rows.append(
            {
                "session_date": sd,
                "day_open": o,
                "day_high": h,
                "day_low": l,
                "day_close": c,
                "day_range": h - l,
                "day_mid": 0.5 * (h + l),
            }
        )
    daily = pd.DataFrame(rows).sort_values("session_date").reset_index(drop=True)
    daily["prior_mid"] = daily["day_mid"].shift(1)
    daily["prior_high"] = daily["day_high"].shift(1)
    daily["prior_low"] = daily["day_low"].shift(1)
    daily["prior_range"] = daily["day_range"].shift(1)
    return daily


def loc_side(close_T: float, prior_mid: float, prior_range: float) -> int | None:
    if not np.isfinite(close_T) or not np.isfinite(prior_mid) or not np.isfinite(prior_range):
        return None
    if prior_range <= 0:
        return None
    eps = max(0.25, 0.01 * prior_range)
    d = close_T - prior_mid
    if abs(d) < eps:
        return None
    return 1 if d > 0 else -1


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
    print("=== Hypothesis 16B: Prior-day midpoint LOCATION under Strategy-12 HIGH ===", flush=True)
    print(f"H={HOLD_HS}; side=sign(close_T - prior_mid); Strategy 12 frozen", flush=True)

    df = load_nq()
    daily = build_globex_daily(df)
    art("nq_dirres_midB_globex_days.parquet").parent  # ensure via art
    daily.to_parquet(art("nq_dirres_midB_globex_days.parquet"), index=False)
    daily_map = {r["session_date"]: r for _, r in daily.iterrows()}

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
    for (sd, name), bars in sess_bars.items():
        fr = facts_map[(sd, name)]
        dr = daily_map.get(sd)
        if dr is None:
            continue
        prior_mid = dr["prior_mid"]
        prior_range = dr["prior_range"]
        if not np.isfinite(prior_mid) or not np.isfinite(prior_range):
            continue
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
            close_T = float(bars.loc[bars["ny_min"] == T, "close"].iloc[-1])
            side = loc_side(close_T, float(prior_mid), float(prior_range))
            if side is None:
                continue
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
                "side_loc": side,
                "close_T": close_T,
                "prior_mid": float(prior_mid),
                "prior_range": float(prior_range),
                "loc_frac": (close_T - float(prior_mid)) / float(prior_range),
                "rng_psr": float(st["rng_psr"]),
            }
            any_h = False
            for H in HOLD_HS:
                if len(closes) < H:
                    row[f"pnl_loc_{H}"] = np.nan
                    row[f"pnl_long_{H}"] = np.nan
                    continue
                px = float(closes[H - 1])
                row[f"pnl_loc_{H}"] = side * (px - entry)
                row[f"pnl_long_{H}"] = px - entry
                any_h = True
            if any_h:
                rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, panel={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_dirres_midB_panel.parquet"), index=False)
    print(f"Panel rows={len(panel)}", flush=True)
    if panel.empty:
        raise SystemExit("Empty panel")

    results: list[dict[str, Any]] = []
    universes = (
        ("ALL_loc", "pnl_loc", None),
        ("HIGH_loc", "pnl_loc", "HIGH"),
        ("LOW_loc", "pnl_loc", "LOW"),
        ("HIGH_long", "pnl_long", "HIGH"),
    )
    for sess in SESSION_PRIORITY:
        for off in SESSION_DECISION_OFFSETS[sess]:
            for H in HOLD_HS:
                col_check = f"pnl_loc_{H}"
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
    res_df.to_csv(art("nq_dirres_midB_results.csv"), index=False)

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
            for H in HOLD_HS:
                hb = get(sess, off, H, "HIGH_loc", "IS")
                ab = get(sess, off, H, "ALL_loc", "IS")
                hl = get(sess, off, H, "HIGH_long", "IS")
                if not hb or not ab or hb.get("n", 0) < 80 or ab.get("n", 0) < 80:
                    continue
                hv = get(sess, off, H, "HIGH_loc", "Validation")
                av = get(sess, off, H, "ALL_loc", "Validation")
                ho = get(sess, off, H, "HIGH_loc", "OOS")
                ao = get(sess, off, H, "ALL_loc", "OOS")
                if not hv or not av or not ho or not ao:
                    continue
                if hv.get("n", 0) < 30 or ho.get("n", 0) < 25:
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
                y25h = get(sess, off, H, "HIGH_loc", "Y2025")
                y25a = get(sess, off, H, "ALL_loc", "Y2025")
                y26h = get(sess, off, H, "HIGH_loc", "Y2026")
                y26a = get(sess, off, H, "ALL_loc", "Y2026")
                year_ok = False
                if (
                    y25h
                    and y25a
                    and y26h
                    and y26a
                    and y25h.get("n", 0) >= 20
                    and y26h.get("n", 0) >= 20
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
                            "HIGH_loc_IS_n": hb["n"],
                            "HIGH_loc_IS_win": hb["win"],
                            "ALL_loc_IS_win": ab["win"],
                            "HIGH_long_IS_win": hl.get("win", np.nan) if hl else np.nan,
                            "lift_win_IS": lw_is,
                            "lift_E_IS": le_is,
                            "lift_win_Val": lw_v,
                            "lift_win_OOS": lw_o,
                            "HIGH_loc_OOS_win": ho["win"],
                            "ALL_loc_OOS_win": ao["win"],
                            "year_ok": year_ok,
                        }
                    )

    cand_df = pd.DataFrame(candidates) if candidates else pd.DataFrame()
    cand_df.to_csv(art("nq_dirres_midB_candidates.csv"), index=False)

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
        "# Hypothesis 16B — Prior-Day Midpoint Location (resolver-only)",
        "",
        "## Question",
        "",
        "> Conditional on Strategy-12 HIGH, does sign(price_T - prior Globex day mid)",
        "> resolve NQ direction better than the same rule unconditionally?",
        "",
        "## Freeze",
        "",
        "- Strategy 12 activity gate: **untouched** (WHEN only)",
        "- `prior_mid = (prior_high + prior_low) / 2` of previous `session_date`",
        "- Flat skip: `abs(close_T - mid) < max(0.25, 0.01 * prior_range)`",
        f"- H = {list(HOLD_HS)} (pre-specified)",
        "- No stops / targets / PDH-PDL variants",
        f"- Panel rows: **{len(panel):,}**",
        f"- Soft candidates: **{int((cand_df['tier']=='soft').sum()) if len(cand_df) else 0}**",
        f"- Strong candidates: **{int((cand_df['tier']=='strong').sum()) if len(cand_df) else 0}**",
        "",
    ]

    for H in PRIMARY_HS:
        lines.append(f"## Primary contrast H={H} (best IS lift clock per session)")
        lines.append("")
        lines.append(
            "| Session | T+ | ALL+loc | HIGH+loc | HIGH long | Lift vs ALL | Lift Val | Lift OOS | HIGH+loc OOS |"
        )
        lines.append(
            "|---------|----|---------|----------|-----------|-------------|----------|----------|--------------|"
        )
        for sess in SESSION_PRIORITY:
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                hb = get(sess, off, H, "HIGH_loc", "IS")
                ab = get(sess, off, H, "ALL_loc", "IS")
                if not hb or not ab or hb.get("n", 0) < 40:
                    continue
                lift = hb["win"] - ab["win"]
                if best is None or lift > best["lift"]:
                    hl = get(sess, off, H, "HIGH_long", "IS")
                    hv = get(sess, off, H, "HIGH_loc", "Validation")
                    av = get(sess, off, H, "ALL_loc", "Validation")
                    ho = get(sess, off, H, "HIGH_loc", "OOS")
                    ao = get(sess, off, H, "ALL_loc", "OOS")
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
    lines.append("| H | T+ | HIGH+loc IS | ALL+loc IS | Lift IS | Lift Val | Lift OOS |")
    lines.append("|---|----|-------------|------------|---------|----------|----------|")
    for H in HOLD_HS:
        best = None
        for off in SESSION_DECISION_OFFSETS["LONDON"]:
            hb = get("LONDON", off, H, "HIGH_loc", "IS")
            ab = get("LONDON", off, H, "ALL_loc", "IS")
            if not hb or not ab or hb.get("n", 0) < 40:
                continue
            lift = hb["win"] - ab["win"]
            if best is None or lift > best["lift"]:
                hv = get("LONDON", off, H, "HIGH_loc", "Validation")
                av = get("LONDON", off, H, "ALL_loc", "Validation")
                ho = get("LONDON", off, H, "HIGH_loc", "OOS")
                ao = get("LONDON", off, H, "ALL_loc", "OOS")
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
            "Kill 16B. Prior-day midpoint location does not resolve direction "
            "conditionally inside Strategy-12 HIGH vs unconditional baseline."
        )
    elif multi_strong:
        verdict = "B_review"
        call = (
            f"Multi-clock strong lift keys={len(multi_strong)}. Scientific interest only — "
            "freeze before any execution card. Strategy 12 still not retuned."
        )
    elif n_soft:
        verdict = "B->kill"
        call = (
            "Soft/single-clock lift only. Do not promote. Do not expand to PDH/PDL "
            "variants to rescue this pass."
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
    lines.append("- Resolver-only (WHEN / WHICH WAY / HOW still separated).")
    lines.append("- Strategy 12 remains a frozen opportunity regime detector.")
    lines.append("")

    art("nq_dirres_midB_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_dirres_midB_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
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
