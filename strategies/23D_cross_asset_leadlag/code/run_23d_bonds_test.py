"""
23D-ZN — Overnight ZN vs NQ relative strength under Strategy-12 HIGH.

PRE-REGISTERED (methodology_bonds_preregister.md) BEFORE any performance look:
  Grid = 24 cells (NY_AM × 4 clocks × 3 H × zn_follow/zn_fade)
  ZB still UNAVAILABLE (duplicate ZN dumps are not ZB)
  Hard stop in direction_resolution.md

Default --stage IS only.
"""
from __future__ import annotations

import argparse
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

from common.nq_session import NY_OPEN, art, load_nq, load_zn, win_rate
from common.sessions import (
    SESSION_DECISION_OFFSETS,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION = "NY_AM"
CLOCKS = SESSION_DECISION_OFFSETS[SESSION]
HOLD_HS = (15, 30, 60)
SIGNALS = ("zn_follow", "zn_fade")
GRID_CELLS = len(CLOCKS) * len(HOLD_HS) * len(SIGNALS)  # 24
PRIOR_CLOSE_MAX_NY = 16 * 60

THRESH = json.loads(art("nq_multi_sess_opp_thresholds_IS.json").read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]
assert GRID_CELLS == 24


def th_rng(session: str, off: int) -> dict[str, float] | None:
    d = STATE_TH.get(session, {}).get(str(off)) or STATE_TH.get(session, {}).get(off)
    return None if not d else d.get("rng_psr")


def regime_of(session: str, off: int, rng_psr: float) -> str:
    t = th_rng(session, off)
    if not t:
        return "MID"
    if float(rng_psr) >= float(t["p66"]):
        return "HIGH"
    if float(rng_psr) <= float(t["p33"]):
        return "LOW"
    return "MID"


def after_bars(sess: pd.DataFrame, T_ny: int) -> pd.DataFrame:
    return sess[sess["ny_min"] > T_ny].reset_index(drop=True)


def summarize(pnls: np.ndarray) -> dict[str, float]:
    x = pnls[np.isfinite(pnls)]
    if len(x) == 0:
        return {"n": 0, "win": np.nan, "E": np.nan}
    return {"n": int(len(x)), "win": float(win_rate(pd.Series(x))["rate"]), "E": float(np.mean(x))}


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pp(x: Any) -> str:
    return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def last_rth_close(day: pd.DataFrame) -> float:
    d = day[day["ny_min"] <= PRIOR_CLOSE_MAX_NY]
    if len(d) == 0:
        return np.nan
    return float(d.sort_values("ny_min").iloc[-1]["close"])


def open_930(day: pd.DataFrame) -> float:
    exact = day[day["ny_min"] == NY_OPEN]
    if len(exact):
        return float(exact.iloc[0]["open"])
    later = day[day["ny_min"] > NY_OPEN].sort_values("ny_min")
    return float(later.iloc[0]["open"]) if len(later) else np.nan


def build_overnight_rs(nq: pd.DataFrame, zn: pd.DataFrame) -> pd.DataFrame:
    nq_days = {sd: g for sd, g in nq.groupby("session_date", sort=True)}
    zn_days = {sd: g for sd, g in zn.groupby("session_date", sort=True)}
    sds = sorted(set(nq_days) & set(zn_days))
    rows: list[dict[str, Any]] = []
    for i, sd in enumerate(sds):
        if i == 0:
            continue
        prev = sds[i - 1]
        nq_pc, zn_pc = last_rth_close(nq_days[prev]), last_rth_close(zn_days[prev])
        nq_o, zn_o = open_930(nq_days[sd]), open_930(zn_days[sd])
        if not all(np.isfinite(x) and x != 0 for x in (nq_pc, zn_pc, nq_o, zn_o)):
            continue
        nq_on = nq_o / nq_pc - 1.0
        zn_on = zn_o / zn_pc - 1.0
        rs = zn_on - nq_on
        side = 0 if abs(rs) < 1e-15 else (1 if rs > 0 else -1)
        rows.append(
            {
                "session_date": sd,
                "prior_session_date": prev,
                "nq_overnight_ret": nq_on,
                "zn_overnight_ret": zn_on,
                "rs_zn_nq": rs,
                "side_zn_follow": side,
                "side_zn_fade": -side if side else 0,
                "zb_status": "UNAVAILABLE",
            }
        )
    return pd.DataFrame(rows)


def build_panel(nq: pd.DataFrame, rs: pd.DataFrame) -> pd.DataFrame:
    rs_map = {r["session_date"]: r for _, r in rs.iterrows()}
    facts = build_session_facts(nq)
    facts = facts[facts["session"] == SESSION]
    facts_map = {r["session_date"]: r for _, r in facts.iterrows()}
    sess_bars: dict[Any, pd.DataFrame] = {}
    for sd, g in nq.groupby("session_date", sort=False):
        if sd not in facts_map or sd not in rs_map:
            continue
        if int(rs_map[sd]["side_zn_follow"]) == 0:
            continue
        b = bars_in_session(g, SESSION)
        if len(b) >= 40:
            sess_bars[sd] = b

    rows: list[dict[str, Any]] = []
    for sd, bars in sess_bars.items():
        fr, feat = facts_map[sd], rs_map[sd]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        sf, sd_fade = int(feat["side_zn_follow"]), int(feat["side_zn_fade"])
        for off in CLOCKS:
            T = decision_ny_min(SESSION, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars, session=SESSION, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            reg = regime_of(SESSION, off, float(st["rng_psr"]))
            after = after_bars(bars, T)
            if len(after) < min(HOLD_HS):
                continue
            entry = float(after.iloc[0]["open"])
            closes = after["close"].to_numpy(float)
            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": SESSION,
                "year": int(fr["year"]),
                "split": str(fr["split"]),
                "T_offset": off,
                "regime": reg,
                "side_zn_follow": sf,
                "side_zn_fade": sd_fade,
                "rs_zn_nq": float(feat["rs_zn_nq"]),
                "rng_psr": float(st["rng_psr"]),
            }
            any_h = False
            for H in HOLD_HS:
                if len(closes) < H:
                    row[f"pnl_long_{H}"] = np.nan
                    row[f"pnl_zn_follow_{H}"] = np.nan
                    row[f"pnl_zn_fade_{H}"] = np.nan
                    continue
                dpx = float(closes[H - 1]) - entry
                row[f"pnl_long_{H}"] = dpx
                row[f"pnl_zn_follow_{H}"] = sf * dpx
                row[f"pnl_zn_fade_{H}"] = sd_fade * dpx
                any_h = True
            if any_h:
                rows.append(row)
    return pd.DataFrame(rows)


def score_panel(panel: pd.DataFrame) -> pd.DataFrame:
    universes = (
        ("ALL_zn_follow", "pnl_zn_follow", None),
        ("HIGH_zn_follow", "pnl_zn_follow", "HIGH"),
        ("ALL_zn_fade", "pnl_zn_fade", None),
        ("HIGH_zn_fade", "pnl_zn_fade", "HIGH"),
        ("HIGH_long", "pnl_long", "HIGH"),
    )
    results: list[dict[str, Any]] = []
    for off in CLOCKS:
        for H in HOLD_HS:
            base = panel[panel["T_offset"] == off]
            for uname, prefix, reg in universes:
                col = f"{prefix}_{H}"
                u = base if reg is None else base[base["regime"] == reg]
                u = u[u[col].notna()]
                s = u[u["split"] == "IS"]
                m = summarize(s[col].to_numpy(float))
                if m["n"] < 15:
                    continue
                results.append(
                    {
                        "session": SESSION,
                        "T_offset": off,
                        "horizon": H,
                        "universe": uname,
                        "split": "IS",
                        **m,
                    }
                )
    return pd.DataFrame(results)


def three_way(res_df: pd.DataFrame, signal: str, off: int, H: int) -> dict[str, Any]:
    def get(univ: str) -> dict[str, Any]:
        s = res_df[
            (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == "IS")
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    ab, hb, hl = get(f"ALL_{signal}"), get(f"HIGH_{signal}"), get("HIGH_long")
    out = {
        "signal": signal,
        "T_offset": off,
        "horizon": H,
        "ALL_win": ab.get("win", np.nan),
        "HIGH_long_win": hl.get("win", np.nan),
        "HIGH_sig_win": hb.get("win", np.nan),
        "ALL_n": ab.get("n", 0),
        "HIGH_sig_n": hb.get("n", 0),
        "HIGH_sig_E": hb.get("E", np.nan),
        "ALL_E": ab.get("E", np.nan),
        "HIGH_long_E": hl.get("E", np.nan),
    }
    out["lift_vs_ALL_win"] = (
        hb["win"] - ab["win"] if hb and ab else np.nan
    )
    out["lift_vs_ALL_E"] = hb["E"] - ab["E"] if hb and ab else np.nan
    out["lift_vs_HIGH_long_win"] = (
        hb["win"] - hl["win"] if hb and hl else np.nan
    )
    out["lift_vs_HIGH_long_E"] = hb["E"] - hl["E"] if hb and hl else np.nan
    return out


def evaluate_is(res_df: pd.DataFrame) -> tuple[list[dict[str, Any]], str, bool]:
    """Returns candidates, tag, hard_stop_fire."""
    candidates: list[dict[str, Any]] = []
    for signal in SIGNALS:
        for off in CLOCKS:
            for H in HOLD_HS:
                tw = three_way(res_df, signal, off, H)
                if tw["HIGH_sig_n"] < 80 or tw["ALL_n"] < 80:
                    continue
                lw, le = tw["lift_vs_ALL_win"], tw["lift_vs_ALL_E"]
                inc_w, inc_e = tw["lift_vs_HIGH_long_win"], tw["lift_vs_HIGH_long_E"]
                if not (lw >= 0.03 or le >= 0.5):
                    continue
                if not (tw["HIGH_sig_win"] >= 0.52 or tw["HIGH_sig_E"] > 0):
                    continue
                if not (
                    (np.isfinite(inc_w) and inc_w >= -0.005)
                    or (np.isfinite(inc_e) and inc_e >= 0)
                ):
                    continue
                strong = (lw >= 0.05 or (le >= 1.0 and lw >= 0)) and (
                    tw["HIGH_sig_win"] >= 0.55
                    or (tw["HIGH_sig_win"] >= 0.52 and le >= 1.0)
                )
                if strong and not (np.isfinite(inc_w) and inc_w >= 0):
                    strong = False
                candidates.append(
                    {
                        "signal": signal,
                        "T_offset": off,
                        "horizon": H,
                        "tier": "strong" if strong else "soft",
                        "HIGH_sig_IS_win": tw["HIGH_sig_win"],
                        "lift_vs_ALL_win": lw,
                        "lift_vs_HIGH_long_win": inc_w,
                        "HIGH_sig_IS_n": tw["HIGH_sig_n"],
                    }
                )
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    strong_clocks = {c["T_offset"] for c in candidates if c["tier"] == "strong"}

    # Hard-stop sensors (pre-registered)
    h30_inc = [
        three_way(res_df, sig, off, 30)["lift_vs_HIGH_long_win"]
        for sig in SIGNALS
        for off in CLOCKS
    ]
    all_h30_neg = all(np.isfinite(x) and x < 0 for x in h30_inc) if h30_inc else True
    hard_stop = strong_n == 0 or all_h30_neg

    if strong_n >= 1 and len(strong_clocks) >= 2:
        tag = "IS_PROMISING_PENDING_VAL"
    elif soft_n or strong_n:
        tag = "IS_SOFT_ONLY"
    else:
        tag = "IS_NULL"
    if hard_stop:
        tag = "IS_HARD_STOP_FAMILY_23"
    return candidates, tag, hard_stop


def write_report(
    panel: pd.DataFrame,
    res_df: pd.DataFrame,
    candidates: list[dict[str, Any]],
    tag: str,
    hard_stop: bool,
) -> str:
    lines = [
        "# Hypothesis 23D-ZN — Overnight ZN/NQ RS under Strategy-12 HIGH (IS only)",
        "",
        "## Pre-registration (before look)",
        "",
        f"- Grid: **{GRID_CELLS}** cells",
        "- ZB: **UNAVAILABLE** (duplicate ZN dumps ≠ ZB)",
        "- Hard stop: 0 strong OR ES/23A-like all-clock negative incremental → close family 23",
        "",
        f"- Panel rows: **{len(panel):,}**",
        f"- Soft / strong: **{sum(1 for c in candidates if c['tier']=='soft')}** / "
        f"**{sum(1 for c in candidates if c['tier']=='strong')}**",
        f"- Tag: **`{tag}`**",
        f"- Hard stop fired: **{'YES' if hard_stop else 'NO'}**",
        "",
        "## Three-way H=30",
        "",
    ]
    for signal in SIGNALS:
        lines += [
            f"### `{signal}`",
            "",
            "| T+ | ALL+sig | HIGH-long | HIGH+sig | vs ALL | vs HIGH-long | n |",
            "|----|---------|-----------|----------|--------|--------------|---|",
        ]
        for off in CLOCKS:
            tw = three_way(res_df, signal, off, 30)
            lines.append(
                f"| {off} | {pct(tw['ALL_win'])} | {pct(tw['HIGH_long_win'])} | "
                f"{pct(tw['HIGH_sig_win'])} | {pp(tw['lift_vs_ALL_win'])} | "
                f"{pp(tw['lift_vs_HIGH_long_win'])} | "
                f"{int(tw['HIGH_sig_n']) if tw['HIGH_sig_n'] else '—'} |"
            )
        lines.append("")
    lines += ["## Candidates", ""]
    if not candidates:
        lines.append("_None._")
    else:
        lines.append("| Tier | Signal | T+ | H | HIGH+sig | vs ALL | vs HIGH-long | n |")
        lines.append("|------|--------|----|---|----------|--------|--------------|---|")
        for c in sorted(candidates, key=lambda x: (x["tier"] != "strong", x["T_offset"])):
            lines.append(
                f"| {c['tier']} | {c['signal']} | {c['T_offset']} | {c['horizon']} | "
                f"{pct(c['HIGH_sig_IS_win'])} | {pp(c['lift_vs_ALL_win'])} | "
                f"{pp(c['lift_vs_HIGH_long_win'])} | {int(c['HIGH_sig_IS_n'])} |"
            )
    lines += [
        "",
        "## Family stop reading",
        "",
        (
            "Hard stop **FIRED**. Close Strategy 23 family. Do not open VIX/skew/order-flow "
            "without a new argument. ZB remaining absent is a data gap — **not** a rescue path "
            "after this ZN kill. Next: HOW (size on Strategy 12 WHEN) or stop."
            if hard_stop
            else "Hard stop did not fire — unlock Val triple with frozen defs (no expansion)."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("IS",), default="IS")
    args = ap.parse_args()
    print(f"=== 23D-ZN IS grid={GRID_CELLS} (ZB still UNAVAILABLE) ===", flush=True)
    nq, zn = load_nq(), load_zn()
    rs = build_overnight_rs(nq, zn)
    art("nq_xasset_zn_overnight_rs.parquet").parent.mkdir(parents=True, exist_ok=True)
    rs.to_parquet(art("nq_xasset_zn_overnight_rs.parquet"), index=False)
    print(f"Overnight RS days={len(rs)}", flush=True)
    panel = build_panel(nq, rs)
    if panel.empty:
        raise SystemExit("Empty 23D-ZN panel")
    panel.to_parquet(art("nq_xasset_23d_zn_panel.parquet"), index=False)
    print(f"Panel rows={len(panel)}", flush=True)
    res_df = score_panel(panel)
    res_df.to_csv(art("nq_xasset_23d_zn_results.csv"), index=False)
    candidates, tag, hard_stop = evaluate_is(res_df)
    pd.DataFrame(candidates).to_csv(art("nq_xasset_23d_zn_candidates_IS.csv"), index=False)
    report = write_report(panel, res_df, candidates, tag, hard_stop)
    art("nq_xasset_23d_zn_report_IS.md").write_text(report, encoding="utf-8")
    results = _CODE.parent / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "IS_bonds_ZN.md").write_text(report, encoding="utf-8")
    payload = {
        "leg": "23D-ZN",
        "zb_status": "UNAVAILABLE",
        "grid_cells": GRID_CELLS,
        "provisional_IS": tag,
        "hard_stop_fired": hard_stop,
        "n_soft": int(sum(1 for c in candidates if c["tier"] == "soft")),
        "n_strong": int(sum(1 for c in candidates if c["tier"] == "strong")),
        "n_panel": int(len(panel)),
        "candidates": candidates,
    }
    art("nq_xasset_23d_zn_report_IS.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    print(
        f"Tag={tag} hard_stop={hard_stop} soft={payload['n_soft']} strong={payload['n_strong']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
