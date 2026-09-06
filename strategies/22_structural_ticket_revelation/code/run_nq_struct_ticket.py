"""
Strategy 22 — Structural-ticket direction revelation

Frozen BEFORE results:
  Ticket = 0.25 * psr (Strategy 12 STRUCT_FRAC)
  Ref = close at T
  Horizon = 60m after T
  Same-bar both hits -> AMBIGUOUS (skip)
  Neither in horizon -> NO_REVELATION (skip)
  Entry = next open after trigger bar

Resolver-only. Lift = HIGH - ALL. Do not retune 0.25 or 60.
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
RESOLVER = "struct_ticket"
STRUCT_FRAC = 0.25
OBS_HORIZON = 60  # completed 1m bars after T

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


def close_at_T(sess: pd.DataFrame, T_ny: int) -> float | None:
    hit = sess[sess["ny_min"] == T_ny]
    if len(hit) == 0:
        return None
    return float(hit.iloc[-1]["close"])


def residual_pts(from_entry: pd.DataFrame, entry: float, H: int) -> float:
    if len(from_entry) < 1 or not np.isfinite(entry):
        return np.nan
    w = from_entry.iloc[:H]
    if len(w) == 0:
        return np.nan
    hi = float(w["high"].max())
    lo = float(w["low"].min())
    return float(max(hi - entry, entry - lo))


def reveal_ticket(
    after: pd.DataFrame, close_T: float, ticket: float, horizon: int
) -> dict[str, Any]:
    """Scan after[0:horizon] for first one-sided structural ticket."""
    up = close_T + ticket
    dn = close_T - ticket
    n = min(horizon, len(after))
    for i in range(n):
        hi = float(after.iloc[i]["high"])
        lo = float(after.iloc[i]["low"])
        hit_up = hi >= up
        hit_dn = lo <= dn
        if hit_up and hit_dn:
            return {
                "status": "AMBIGUOUS",
                "side": 0,
                "wait_bars": i + 1,
                "entry_idx": None,
            }
        if hit_up or hit_dn:
            entry_idx = i + 1
            if entry_idx >= len(after):
                return {
                    "status": "NO_ENTRY",
                    "side": 0,
                    "wait_bars": i + 1,
                    "entry_idx": None,
                }
            return {
                "status": "REVEALED",
                "side": 1 if hit_up else -1,
                "wait_bars": i + 1,
                "entry_idx": entry_idx,
            }
    return {"status": "NONE", "side": 0, "wait_bars": n, "entry_idx": None}


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
    print("=== Strategy 22: Structural-ticket revelation ===", flush=True)
    print(
        f"Frozen: ticket={STRUCT_FRAC}*psr; horizon={OBS_HORIZON}m; "
        f"ambiguous=same-bar both; outcomes={OUTCOMES}",
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
        ticket = STRUCT_FRAC * psr
        for off in SESSION_DECISION_OFFSETS[name]:
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars, session=name, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            close_T = close_at_T(bars, T)
            if close_T is None:
                continue
            after = after_bars(bars, T, name)
            # Room for late reveal (bar 60) + entry + H30; H60 nan if short
            if len(after) < OBS_HORIZON + 32:
                continue
            reg = regime_of(name, off, float(st["rng_psr"]))
            rev = reveal_ticket(after, close_T, ticket, OBS_HORIZON)

            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                "psr": psr,
                "ticket": ticket,
                "close_T": close_T,
                "status": rev["status"],
                "side": int(rev["side"]),
                "wait_bars": int(rev["wait_bars"]),
                "has_reveal": rev["status"] == "REVEALED",
            }

            if rev["status"] == "REVEALED":
                ei = int(rev["entry_idx"])
                # Need at least H30 after entry
                if len(after) < ei + 30:
                    row["has_reveal"] = False
                    row["status"] = "NO_ENTRY"
                    row["side"] = 0
                    row["entry"] = np.nan
                    row["resid_entry_30"] = np.nan
                    for outcome in OUTCOMES:
                        row[f"pnl_long_{outcome}"] = np.nan
                        row[f"pnl_{RESOLVER}_{outcome}"] = np.nan
                else:
                    entry = float(after.iloc[ei]["open"])
                    from_e = after.iloc[ei:].reset_index(drop=True)
                    closes = from_e["close"].to_numpy(float)
                    end_px = float(from_e.iloc[-1]["close"])
                    side = int(rev["side"])
                    row["entry"] = entry
                    row["resid_entry_30"] = residual_pts(from_e, entry, 30)
                    row["pnl_long_H30"] = float(closes[29]) - entry
                    row["pnl_long_H60"] = (
                        float(closes[59]) - entry if len(closes) >= 60 else np.nan
                    )
                    row["pnl_long_SESS_END"] = end_px - entry
                    for outcome in OUTCOMES:
                        long_pnl = row[f"pnl_long_{outcome}"]
                        if np.isfinite(long_pnl):
                            row[f"pnl_{RESOLVER}_{outcome}"] = side * float(long_pnl)
                        else:
                            row[f"pnl_{RESOLVER}_{outcome}"] = np.nan
            else:
                row["entry"] = np.nan
                row["resid_entry_30"] = np.nan
                for outcome in OUTCOMES:
                    row[f"pnl_long_{outcome}"] = np.nan
                    row[f"pnl_{RESOLVER}_{outcome}"] = np.nan

            rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, rows={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_struct_ticket_panel.parquet"), index=False)

    hi = panel[panel["regime"] == "HIGH"]
    print(
        f"Panel={len(panel)} HIGH%={100 * (panel['regime'] == 'HIGH').mean():.1f} "
        f"HIGH reveal%={100 * hi['has_reveal'].mean():.1f} "
        f"HIGH ambig%={100 * (hi['status'] == 'AMBIGUOUS').mean():.1f} "
        f"HIGH none%={100 * (hi['status'] == 'NONE').mean():.1f}",
        flush=True,
    )

    results = []
    for sess in SESSION_PRIORITY:
        for off in SESSION_DECISION_OFFSETS[sess]:
            for outcome in OUTCOMES:
                col = f"pnl_{RESOLVER}_{outcome}"
                base = panel[
                    (panel["session"] == sess)
                    & (panel["T_offset"] == off)
                    & panel["has_reveal"]
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
                                "resolver": RESOLVER,
                                "session": sess,
                                "T_offset": off,
                                "outcome": outcome,
                                "universe": univ,
                                "split": split,
                                **m,
                            }
                        )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_struct_ticket_results.csv"), index=False)

    def get(sess, off, outcome, univ, split):
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["T_offset"] == off)
            & (res_df["outcome"] == outcome)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    candidates = []
    for sess in SESSION_PRIORITY:
        for off in SESSION_DECISION_OFFSETS[sess]:
            for outcome in OUTCOMES:
                hb = get(sess, off, outcome, "HIGH", "IS")
                ab = get(sess, off, outcome, "ALL", "IS")
                if not hb or not ab or hb.get("n", 0) < 40 or ab.get("n", 0) < 40:
                    continue
                hv = get(sess, off, outcome, "HIGH", "Validation")
                av = get(sess, off, outcome, "ALL", "Validation")
                ho = get(sess, off, outcome, "HIGH", "OOS")
                ao = get(sess, off, outcome, "ALL", "OOS")
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
                            "resolver": RESOLVER,
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
    cand_df.to_csv(art("nq_struct_ticket_candidates.csv"), index=False)

    lines = [
        "# Strategy 22 — Structural-Ticket Direction Revelation",
        "",
        "## Freeze (locked before run)",
        "",
        f"- Ticket = **{STRUCT_FRAC} × psr** (Strategy 12 STRUCT_FRAC)",
        f"- Observation horizon = **{OBS_HORIZON}** bars after T",
        "- Same-bar both hits -> AMBIGUOUS (skip)",
        "- Neither in horizon -> NO_REVELATION (skip)",
        "- Entry = next open after trigger bar",
        "- Win-lift HIGH−ALL only; no stops/targets; do not retune 0.25 or 60",
        f"- Panel rows: **{len(panel):,}**",
        f"- Soft: **{int((cand_df['tier']=='soft').sum()) if len(cand_df) else 0}**",
        f"- Strong: **{int((cand_df['tier']=='strong').sum()) if len(cand_df) else 0}**",
        "",
        "## Reveal rates (HIGH)",
        "",
        "| Session | Split | n | Reveal% | Ambig% | None% | Med wait | Mean resid@entry H30 |",
        "|---------|-------|---|---------|--------|-------|----------|----------------------|",
    ]
    for sess in SESSION_PRIORITY:
        for split in ("IS", "Validation", "OOS"):
            sub = panel[(panel["session"] == sess) & (panel["split"] == split) & (panel["regime"] == "HIGH")]
            if len(sub) < 20:
                continue
            rev = sub[sub["has_reveal"]]
            lines.append(
                f"| {sess} | {split} | {len(sub)} | "
                f"{pct(float(sub['has_reveal'].mean()))} | "
                f"{pct(float((sub['status']=='AMBIGUOUS').mean()))} | "
                f"{pct(float((sub['status']=='NONE').mean()))} | "
                f"{pts(float(rev['wait_bars'].median()) if len(rev) else np.nan)} | "
                f"{pts(float(rev['resid_entry_30'].mean()) if len(rev) else np.nan)} |"
            )
    lines.append("")

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
        lis, lv, lo, hoo = [], [], [], []
        for sess in SESSION_PRIORITY:
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                hb = get(sess, off, outcome, "HIGH", "IS")
                ab = get(sess, off, outcome, "ALL", "IS")
                if not hb or not ab or hb.get("n", 0) < 30:
                    continue
                lift = hb["win"] - ab["win"]
                if best is None or lift > best["li"]:
                    hv = get(sess, off, outcome, "HIGH", "Validation")
                    av = get(sess, off, outcome, "ALL", "Validation")
                    ho = get(sess, off, outcome, "HIGH", "OOS")
                    ao = get(sess, off, outcome, "ALL", "OOS")
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
            int((cand_df["outcome"] == outcome).sum()) if len(cand_df) else 0
        )
        if not lis:
            lines.append(f"| `{RESOLVER}` | — | — | — | — | 0 |")
        else:
            lines.append(
                f"| `{RESOLVER}` | {pp(float(np.nanmedian(lis)))} | "
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
            "| Tier | Session | Outcome | T+ | Lift IS | Lift Val | Lift OOS | HIGH OOS | HIGH IS win |"
        )
        lines.append(
            "|------|---------|---------|----|---------|----------|----------|----------|-------------|"
        )
        show = cand_df.sort_values(["tier", "lift_win_IS"], ascending=[True, False])
        for _, r in show.iterrows():
            lines.append(
                f"| {r['tier']} | {r['session']} | {r['outcome']} | {int(r['T_offset'])} | "
                f"{pp(r['lift_win_IS'])} | {pp(r['lift_win_Val'])} | {pp(r['lift_win_OOS'])} | "
                f"{pct(r['HIGH_OOS_win'])} | {pct(r['HIGH_IS_win'])} |"
            )
    lines.append("")

    multi = []
    if len(cand_df):
        for (sess, outcome), g in cand_df.groupby(["session", "outcome"]):
            if g["T_offset"].nunique() >= 2:
                multi.append(
                    {
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
            "Kill 22. Structural-ticket revelation does not provide stable "
            "incremental direction. Stronger call: under tested information, "
            "Strategy 12 behaves as an unsigned activity detector."
        )
    elif multi_strong:
        verdict = "B_lead"
        call = (
            f"Multi-clock leads: {multi_strong}. Evidence that direction may "
            "reveal after paying the structural ticket — freeze for review; "
            "not a trade; no HOW yet."
        )
    else:
        verdict = "B->kill"
        call = (
            f"Soft/strong={n_soft + n_strong} without multi-clock strength. "
            "Do not retune 0.25 or 60m. Do not open stops/targets to rescue."
        )

    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict}`**")
    lines.append("")
    lines.append(call)
    lines.append("")
    lines.append("### Discipline")
    lines.append("")
    lines.append("- Ticket and horizon were frozen before results.")
    lines.append("- Ambiguous same-bar both = skip.")
    lines.append("- Strategy 12 remains WHEN-only.")
    lines.append("")

    art("nq_struct_ticket_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    art("nq_struct_ticket_report.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "panel_rows": int(len(panel)),
                "n_soft": n_soft,
                "n_strong": n_strong,
                "multi": multi,
                "call": call,
                "STRUCT_FRAC": STRUCT_FRAC,
                "OBS_HORIZON": OBS_HORIZON,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"Verdict: {verdict}", flush=True)
    print(call, flush=True)
    print(f"Wrote {art('nq_struct_ticket_report.md')}", flush=True)


if __name__ == "__main__":
    main()
