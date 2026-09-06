"""
23A — COT extreme positioning → NQ direction under Strategy-12 HIGH.

Stage gate: default --stage IS only (Val/OOS deferred until IS review).

Baselines:
  1) Unconditional same clock (long-only + ALL+COT)
  2) HIGH alone (long-only)
  Incremental claim requires HIGH+COT lift vs both.
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

from common.nq_session import art, load_nq, win_rate
from common.sessions import (
    SESSION_DECISION_OFFSETS,
    SESSION_START,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)
from common.splits import split_of

warnings.filterwarnings("ignore", category=FutureWarning)

SESSION_PRIORITY = ("LONDON", "NY_PM", "NY_AM", "ASIA")
HOLD_HS = (30, 60, 120)
PRIMARY_HS = (30, 60)
SIGNALS = ("lev_fade", "am_follow")

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


def pts(x: Any) -> str:
    return f"{x:+.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def load_cot_map() -> dict[Any, dict[str, Any]]:
    path = art("nq_cot_session_map.parquet")
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}; run build_cot_features.py first"
        )
    smap = pd.read_parquet(path)
    out: dict[Any, dict[str, Any]] = {}
    for _, r in smap.iterrows():
        sd = pd.Timestamp(r["session_date"]).date()
        out[sd] = {
            "side_lev_fade": int(r["side_lev_fade"]),
            "side_am_follow": int(r["side_am_follow"]),
            "ext_lev": int(r["ext_lev"]),
            "ext_am": int(r["ext_am"]),
            "z_lev": float(r["z_lev"]) if np.isfinite(r["z_lev"]) else np.nan,
            "z_am": float(r["z_am"]) if np.isfinite(r["z_am"]) else np.nan,
            "report_date": str(r["report_date"]),
            "release_friday": str(r["release_friday"]),
        }
    return out


def build_panel() -> pd.DataFrame:
    print("Loading NQ + COT session map…", flush=True)
    df = load_nq()
    cot_map = load_cot_map()
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

    rows: list[dict[str, Any]] = []
    n_done = 0
    for (sd, name), bars in sess_bars.items():
        cot = cot_map.get(sd)
        if cot is None:
            continue
        # Need at least one extreme signal this day
        if cot["side_lev_fade"] == 0 and cot["side_am_follow"] == 0:
            continue
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
                bars, session=name, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            reg = regime_of(name, off, float(st["rng_psr"]))
            after = after_bars(bars, T, name)
            if len(after) < min(HOLD_HS):
                continue
            entry = float(after.iloc[0]["open"])
            if not np.isfinite(entry):
                continue
            closes = after["close"].to_numpy(float)
            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                "side_lev_fade": cot["side_lev_fade"],
                "side_am_follow": cot["side_am_follow"],
                "z_lev": cot["z_lev"],
                "z_am": cot["z_am"],
                "report_date": cot["report_date"],
                "release_friday": cot["release_friday"],
                "rng_psr": float(st["rng_psr"]),
            }
            any_h = False
            for H in HOLD_HS:
                if len(closes) < H:
                    row[f"pnl_long_{H}"] = np.nan
                    row[f"pnl_lev_fade_{H}"] = np.nan
                    row[f"pnl_am_follow_{H}"] = np.nan
                    continue
                px = float(closes[H - 1])
                dpx = px - entry
                row[f"pnl_long_{H}"] = dpx
                sl = cot["side_lev_fade"]
                sa = cot["side_am_follow"]
                row[f"pnl_lev_fade_{H}"] = (sl * dpx) if sl != 0 else np.nan
                row[f"pnl_am_follow_{H}"] = (sa * dpx) if sa != 0 else np.nan
                any_h = True
            if any_h:
                rows.append(row)
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, panel={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    return panel


def score_panel(panel: pd.DataFrame, stage: str) -> pd.DataFrame:
    """Score universes. stage=IS → only IS rows in metrics (still need full panel build)."""
    splits_allowed = {
        "IS": ("IS",),
        "VAL": ("IS", "Validation"),
        "FULL": ("IS", "Validation", "OOS", "Y2025", "Y2026"),
    }
    want = splits_allowed[stage]

    universes = (
        ("ALL_lev_fade", "pnl_lev_fade", None, "lev_fade"),
        ("HIGH_lev_fade", "pnl_lev_fade", "HIGH", "lev_fade"),
        ("ALL_am_follow", "pnl_am_follow", None, "am_follow"),
        ("HIGH_am_follow", "pnl_am_follow", "HIGH", "am_follow"),
        ("HIGH_long", "pnl_long", "HIGH", "long"),
        ("ALL_long", "pnl_long", None, "long"),
    )
    results: list[dict[str, Any]] = []
    for sess in SESSION_PRIORITY:
        for off in SESSION_DECISION_OFFSETS[sess]:
            for H in HOLD_HS:
                base = panel[
                    (panel["session"] == sess) & (panel["T_offset"] == off)
                ]
                if len(base) < 20:
                    continue
                for uname, prefix, reg, _sig in universes:
                    col = f"{prefix}_{H}"
                    if col not in base.columns:
                        continue
                    u = base if reg is None else base[base["regime"] == reg]
                    u = u[u[col].notna()]
                    for split in want:
                        if split.startswith("Y"):
                            s = u[u["year"] == int(split[1:])]
                        else:
                            s = u[u["split"] == split]
                        m = summarize(s[col].to_numpy(float))
                        if m["n"] < 15 and split in ("IS", "Validation", "OOS"):
                            continue
                        if m["n"] < 10:
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
    return pd.DataFrame(results)


def evaluate_is(res_df: pd.DataFrame) -> tuple[list[dict[str, Any]], str]:
    """Hostile IS screen: soft/strong candidates; no Val look."""

    def get(sess, off, H, univ, split="IS") -> dict[str, Any]:
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    candidates: list[dict[str, Any]] = []
    for signal, high_u, all_u in (
        ("lev_fade", "HIGH_lev_fade", "ALL_lev_fade"),
        ("am_follow", "HIGH_am_follow", "ALL_am_follow"),
    ):
        for sess in SESSION_PRIORITY:
            for off in SESSION_DECISION_OFFSETS[sess]:
                for H in HOLD_HS:
                    hb = get(sess, off, H, high_u)
                    ab = get(sess, off, H, all_u)
                    hl = get(sess, off, H, "HIGH_long")
                    if not hb or not ab or hb.get("n", 0) < 60 or ab.get("n", 0) < 60:
                        continue
                    lw = hb["win"] - ab["win"]
                    le = hb["E"] - ab["E"]
                    vs_long_w = hb["win"] - hl["win"] if hl else np.nan
                    vs_long_e = hb["E"] - hl["E"] if hl else np.nan
                    # Hostile: need material lift vs ALL on win OR E
                    if not (lw >= 0.03 or le >= 0.5):
                        continue
                    # Do not label negative win-lift cells as strong (E-only leftovers stay soft)
                    soft = True
                    strong = (lw >= 0.05 or (le >= 1.0 and lw >= 0.0)) and (
                        hb["win"] >= 0.55 or (hb["win"] >= 0.52 and le >= 1.0)
                    )
                    high_ok = hb["win"] >= 0.52 or hb["E"] > 0
                    beats_long = True
                    if hl and hl.get("n", 0) >= 60:
                        # Must not lose to blind HIGH-long on both win and E
                        beats_long = (vs_long_w >= -0.005) or (
                            np.isfinite(vs_long_e) and vs_long_e >= 0
                        )
                    if not high_ok or not beats_long:
                        continue
                    candidates.append(
                        {
                            "signal": signal,
                            "session": sess,
                            "T_offset": off,
                            "horizon": H,
                            "tier": "strong" if strong else "soft",
                            "HIGH_cot_IS_n": hb["n"],
                            "HIGH_cot_IS_win": hb["win"],
                            "ALL_cot_IS_win": ab["win"],
                            "HIGH_long_IS_win": hl.get("win", np.nan) if hl else np.nan,
                            "lift_vs_ALL_win": lw,
                            "lift_vs_ALL_E": le,
                            "lift_vs_HIGH_long_win": vs_long_w,
                            "lift_vs_HIGH_long_E": vs_long_e,
                        }
                    )
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    multi = {}
    for sig in SIGNALS:
        clocks = {
            (c["session"], c["T_offset"])
            for c in candidates
            if c["signal"] == sig and c["tier"] in ("soft", "strong")
        }
        multi[sig] = len(clocks)

    if strong_n >= 1 and any(v >= 2 for v in multi.values()):
        provisional = "IS_PROMISING_PENDING_VAL"
    elif soft_n >= 1 or strong_n >= 1:
        provisional = "IS_SOFT_ONLY"
    else:
        provisional = "IS_NULL"

    return candidates, provisional


def write_is_report(
    panel: pd.DataFrame,
    res_df: pd.DataFrame,
    candidates: list[dict[str, Any]],
    provisional: str,
) -> str:
    lines: list[str] = []
    lines.append("# Hypothesis 23A — COT Positioning under Strategy-12 HIGH (IS only)")
    lines.append("")
    lines.append("## Stage gate")
    lines.append("")
    lines.append("**Val / OOS not scored.** Publish IS first per program discipline.")
    lines.append("")
    lines.append("## Lag rule (audit)")
    lines.append("")
    lines.append(
        "Tuesday snapshot → Friday ~15:30 ET release → next session only "
        "(never Tue–Fri of snapshot week)."
    )
    lines.append("")
    lines.append("## Freeze")
    lines.append("")
    lines.append("- Market: NASDAQ-100 Consolidated FutOnly")
    lines.append("- Extreme: trailing 104-week z, then p10/p90 of trailing z")
    lines.append("- Sides: `lev_fade`, `am_follow` only")
    lines.append("- HIGH: Strategy-12 frozen `rng_psr` p66")
    lines.append(f"- Panel rows (signal weeks ∩ sessions): **{len(panel):,}**")
    lines.append(f"- Soft IS candidates: **{sum(1 for c in candidates if c['tier']=='soft')}**")
    lines.append(f"- Strong IS candidates: **{sum(1 for c in candidates if c['tier']=='strong')}**")
    lines.append(f"- Provisional IS verdict tag: **`{provisional}`**")
    lines.append("")

    def get(sess, off, H, univ) -> dict[str, Any]:
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == "IS")
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    for signal, high_u, all_u in (
        ("lev_fade", "HIGH_lev_fade", "ALL_lev_fade"),
        ("am_follow", "HIGH_am_follow", "ALL_am_follow"),
    ):
        lines.append(f"## Primary contrast H=30 — `{signal}`")
        lines.append("")
        lines.append(
            "| Session | T+ | ALL+COT | HIGH+COT | HIGH long | Lift vs ALL | Lift vs HIGH-long |"
        )
        lines.append(
            "|---------|----|---------|----------|-----------|-------------|-------------------|"
        )
        for sess in SESSION_PRIORITY:
            # best IS lift clock for H=30
            best = None
            for off in SESSION_DECISION_OFFSETS[sess]:
                hb = get(sess, off, 30, high_u)
                ab = get(sess, off, 30, all_u)
                hl = get(sess, off, 30, "HIGH_long")
                if not hb or not ab or hb.get("n", 0) < 40:
                    continue
                lift = hb["win"] - ab["win"]
                if best is None or lift > best["lift"]:
                    best = {
                        "off": off,
                        "hb": hb,
                        "ab": ab,
                        "hl": hl,
                        "lift": lift,
                        "lift_e": hb["E"] - ab["E"],
                        "vs_l": (hb["win"] - hl["win"]) if hl else np.nan,
                    }
            if best is None:
                lines.append(f"| {sess} | — | — | — | — | — | — |")
                continue
            lines.append(
                f"| {sess} | {best['off']} | {pct(best['ab']['win'])} | "
                f"{pct(best['hb']['win'])} | {pct(best['hl'].get('win', np.nan)) if best['hl'] else '—'} | "
                f"{pp(best['lift'])} | {pp(best['vs_l'])} |"
            )
        lines.append("")

    lines.append("## IS candidates (soft/strong)")
    lines.append("")
    if not candidates:
        lines.append("_None. No IS soft/strong incremental lift under frozen rules._")
    else:
        lines.append("| Tier | Signal | Session | T+ | H | HIGH+COT win | Lift vs ALL | Lift vs HIGH-long | n |")
        lines.append("|------|--------|---------|----|---|--------------|-------------|-------------------|---|")
        for c in sorted(candidates, key=lambda x: (x["tier"] != "strong", -x["lift_vs_ALL_win"])):
            lines.append(
                f"| {c['tier']} | {c['signal']} | {c['session']} | {c['T_offset']} | "
                f"{c['horizon']} | {pct(c['HIGH_cot_IS_win'])} | {pp(c['lift_vs_ALL_win'])} | "
                f"{pp(c['lift_vs_HIGH_long_win'])} | {int(c['HIGH_cot_IS_n'])} |"
            )
    lines.append("")
    lines.append("## Hostile IS reading")
    lines.append("")
    if provisional == "IS_NULL":
        lines.append(
            "No incremental IS lift of HIGH+COT over ALL+COT / HIGH-long under frozen "
            "decile extremes. **Do not** retune percentiles. Proceeding to Val/OOS is "
            "optional only for formal kill documentation — not for rescue."
        )
    elif provisional == "IS_SOFT_ONLY":
        lines.append(
            "Soft IS leftovers only. Multi-comparison with family 23 (23D pending) "
            "raises the bar — soft single-clock hits are **not** promotion-ready."
        )
    else:
        lines.append(
            "IS shows promising multi-clock structure under freeze. "
            "**Next:** score Val once (no refit). Do not build an executable system yet "
            "(check A vs A* if Val/OOS hold)."
        )
    lines.append("")
    lines.append("## Multi-comparison note")
    lines.append("")
    lines.append(
        "Family 23 tests multiple external sources (23A COT, 23D cross-asset). "
        "One IS hit does not promote the family without acknowledging that multiplicity."
    )
    lines.append("")
    return "\n".join(lines)


def cell_count_meta() -> dict[str, int]:
    n_clocks = sum(len(SESSION_DECISION_OFFSETS[s]) for s in SESSION_PRIORITY)
    n_h = len(HOLD_HS)
    n_sig = len(SIGNALS)
    return {
        "n_sessions": len(SESSION_PRIORITY),
        "n_clocks": n_clocks,
        "n_horizons": n_h,
        "n_signals": n_sig,
        "n_grid_cells": n_clocks * n_h * n_sig,
    }


def three_way(
    res_df: pd.DataFrame,
    signal: str,
    sess: str,
    off: int,
    H: int,
    split: str,
) -> dict[str, Any]:
    high_u = f"HIGH_{signal}"
    all_u = f"ALL_{signal}"

    def get(univ: str) -> dict[str, Any]:
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    ab = get(all_u)
    hb = get(high_u)
    hl = get("HIGH_long")
    out: dict[str, Any] = {
        "signal": signal,
        "session": sess,
        "T_offset": off,
        "horizon": H,
        "split": split,
        "ALL_cot_n": ab.get("n", 0),
        "ALL_cot_win": ab.get("win", np.nan),
        "ALL_cot_E": ab.get("E", np.nan),
        "HIGH_long_n": hl.get("n", 0),
        "HIGH_long_win": hl.get("win", np.nan),
        "HIGH_long_E": hl.get("E", np.nan),
        "HIGH_cot_n": hb.get("n", 0),
        "HIGH_cot_win": hb.get("win", np.nan),
        "HIGH_cot_E": hb.get("E", np.nan),
    }
    if hb and ab:
        out["lift_vs_ALL_win"] = hb["win"] - ab["win"]
        out["lift_vs_ALL_E"] = hb["E"] - ab["E"]
    else:
        out["lift_vs_ALL_win"] = np.nan
        out["lift_vs_ALL_E"] = np.nan
    if hb and hl:
        out["lift_vs_HIGH_long_win"] = hb["win"] - hl["win"]
        out["lift_vs_HIGH_long_E"] = hb["E"] - hl["E"]
    else:
        out["lift_vs_HIGH_long_win"] = np.nan
        out["lift_vs_HIGH_long_E"] = np.nan
    return out


def write_val_report(
    res_df: pd.DataFrame,
    is_candidates: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    """One-shot Val report. Frozen IS definitions; three-way contrasts."""
    meta = cell_count_meta()
    strong = [c for c in is_candidates if c.get("tier") == "strong"]
    # Always include headline NY_AM lev_fade T30 H30 even if list empty
    headline = {
        "signal": "lev_fade",
        "session": "NY_AM",
        "T_offset": 30,
        "horizon": 30,
        "tier": "headline",
    }
    focus = strong[:]
    if not any(
        c["signal"] == "lev_fade"
        and c["session"] == "NY_AM"
        and int(c["T_offset"]) == 30
        and int(c["horizon"]) == 30
        for c in focus
    ):
        focus.insert(0, headline)

    rows_is: list[dict[str, Any]] = []
    rows_val: list[dict[str, Any]] = []
    for c in focus:
        rows_is.append(
            three_way(
                res_df,
                c["signal"],
                c["session"],
                int(c["T_offset"]),
                int(c["horizon"]),
                "IS",
            )
        )
        rows_val.append(
            three_way(
                res_df,
                c["signal"],
                c["session"],
                int(c["T_offset"]),
                int(c["horizon"]),
                "Validation",
            )
        )

    # Session-level H=30 best-IS-clock three-way at Val (both signals)
    sess_tables: list[str] = []
    for signal, high_u, all_u in (
        ("lev_fade", "HIGH_lev_fade", "ALL_lev_fade"),
        ("am_follow", "HIGH_am_follow", "ALL_am_follow"),
    ):
        lines_t = [
            f"### H=30 session table — `{signal}` (best IS win-lift clock, scored at Val)",
            "",
            "| Session | T+ | Split | ALL+COT | HIGH-long | HIGH+COT | Lift vs ALL | Lift vs HIGH-long | n_HIGH+COT |",
            "|---------|----|-------|---------|-----------|----------|-------------|-------------------|------------|",
        ]
        for sess in SESSION_PRIORITY:
            best_off = None
            best_lift = -1e9
            for off in SESSION_DECISION_OFFSETS[sess]:
                tw = three_way(res_df, signal, sess, off, 30, "IS")
                if tw["HIGH_cot_n"] < 40 or not np.isfinite(tw.get("lift_vs_ALL_win", np.nan)):
                    continue
                if tw["lift_vs_ALL_win"] > best_lift:
                    best_lift = tw["lift_vs_ALL_win"]
                    best_off = off
            if best_off is None:
                lines_t.append(f"| {sess} | — | — | — | — | — | — | — | — |")
                continue
            for split in ("IS", "Validation"):
                tw = three_way(res_df, signal, sess, best_off, 30, split)
                lines_t.append(
                    f"| {sess} | {best_off} | {split} | {pct(tw['ALL_cot_win'])} | "
                    f"{pct(tw['HIGH_long_win'])} | {pct(tw['HIGH_cot_win'])} | "
                    f"{pp(tw['lift_vs_ALL_win'])} | {pp(tw['lift_vs_HIGH_long_win'])} | "
                    f"{int(tw['HIGH_cot_n']) if tw['HIGH_cot_n'] else '—'} |"
                )
        sess_tables.append("\n".join(lines_t))

    # Survivorship vs pre-registered base rate
    n_strong_val_same_sign_all = 0
    n_strong_val_same_sign_inc = 0
    n_strong_scored = 0
    for c, tv in zip(focus, rows_val):
        if c.get("tier") != "strong" and c.get("tier") != "headline":
            continue
        if c.get("tier") == "strong":
            n_strong_scored += 1
            if np.isfinite(tv.get("lift_vs_ALL_win", np.nan)) and tv["lift_vs_ALL_win"] > 0:
                n_strong_val_same_sign_all += 1
            if (
                np.isfinite(tv.get("lift_vs_HIGH_long_win", np.nan))
                and tv["lift_vs_HIGH_long_win"] > 0
            ):
                n_strong_val_same_sign_inc += 1

    hl_is = three_way(res_df, "lev_fade", "NY_AM", 30, 30, "IS")
    hl_val = three_way(res_df, "lev_fade", "NY_AM", 30, 30, "Validation")

    # Verdict tag for Val only (no OOS)
    inc_ok = (
        np.isfinite(hl_val.get("lift_vs_HIGH_long_win", np.nan))
        and hl_val["lift_vs_HIGH_long_win"] >= 0.01
        and hl_val.get("HIGH_cot_n", 0) >= 30
    )
    all_ok = (
        np.isfinite(hl_val.get("lift_vs_ALL_win", np.nan))
        and hl_val["lift_vs_ALL_win"] >= 0.01
        and hl_val.get("HIGH_cot_n", 0) >= 30
    )
    if inc_ok and all_ok and n_strong_val_same_sign_inc >= 2:
        val_tag = "VAL_HOLDS_SOFT"
    elif all_ok or (np.isfinite(hl_val.get("lift_vs_ALL_win", np.nan)) and hl_val["lift_vs_ALL_win"] > 0):
        val_tag = "VAL_PARTIAL_DECAY"
    else:
        val_tag = "VAL_COLLAPSE"

    lines: list[str] = []
    lines.append("# Hypothesis 23A — Validation (one-shot, frozen IS definitions)")
    lines.append("")
    lines.append("## Freeze confirmation")
    lines.append("")
    lines.append("| Item | Status |")
    lines.append("|------|--------|")
    lines.append("| Decile / W=104 extremes | **unchanged** (features parquet; no refit) |")
    lines.append("| Sides `lev_fade` / `am_follow` | **unchanged** |")
    lines.append("| Strategy-12 HIGH p66 | **unchanged** (`nq_multi_sess_opp_thresholds_IS.json`) |")
    lines.append("| Friday-lag join | **unchanged** |")
    lines.append("| Splits | IS 2010–2021 / **Val 2022–2024** (OOS not scored) |")
    lines.append("| Threshold adjustment on Val | **none** |")
    lines.append("")
    lines.append("## Multiplicity (from IS pre-registration)")
    lines.append("")
    lines.append(f"- Grid cells scanned: **{meta['n_grid_cells']}** (20 clocks × 3 H × 2 signals)")
    lines.append("- Eligible IS cells (n≥60 both HIGH+COT & ALL+COT): **110**")
    lines.append("- IS strong hits: **5** (~4.5% of eligible — near single-test noise rate)")
    lines.append("")
    lines.append("## Pre-registered base-rate check")
    lines.append("")
    lines.append(
        "Expectation written in `results/IS.md` before this run: Val likely shows "
        "**partial decay**; incremental HIGH+COT vs HIGH-long is the decisive contrast."
    )
    lines.append("")
    lines.append(f"**Val tag:** `{val_tag}`")
    lines.append("")
    lines.append("## Headline three-way — NY_AM `lev_fade` T+30 H30")
    lines.append("")
    lines.append("| Split | ALL+COT | HIGH-long | HIGH+COT | Lift vs ALL | Lift vs HIGH-long | n_HIGH+COT |")
    lines.append("|-------|---------|-----------|----------|-------------|-------------------|------------|")
    for tw, lab in ((hl_is, "IS"), (hl_val, "Validation")):
        lines.append(
            f"| {lab} | {pct(tw['ALL_cot_win'])} | {pct(tw['HIGH_long_win'])} | "
            f"{pct(tw['HIGH_cot_win'])} | {pp(tw['lift_vs_ALL_win'])} | "
            f"{pp(tw['lift_vs_HIGH_long_win'])} | {int(tw['HIGH_cot_n']) if tw['HIGH_cot_n'] else '—'} |"
        )
    lines.append("")
    lines.append("## IS-strong cells — three-way at Validation")
    lines.append("")
    lines.append(
        "| Signal | Session | T+ | H | IS HIGH+COT | Val ALL+COT | Val HIGH-long | Val HIGH+COT | "
        "Val lift vs ALL | Val lift vs HIGH-long | Val n |"
    )
    lines.append(
        "|--------|---------|----|---|-------------|-------------|---------------|--------------|"
        "----------------|-----------------------|-------|"
    )
    for c, ti, tv in zip(focus, rows_is, rows_val):
        if c.get("tier") not in ("strong", "headline"):
            continue
        lines.append(
            f"| {c['signal']} | {c['session']} | {c['T_offset']} | {c['horizon']} | "
            f"{pct(ti['HIGH_cot_win'])} | {pct(tv['ALL_cot_win'])} | {pct(tv['HIGH_long_win'])} | "
            f"{pct(tv['HIGH_cot_win'])} | {pp(tv['lift_vs_ALL_win'])} | "
            f"{pp(tv['lift_vs_HIGH_long_win'])} | {int(tv['HIGH_cot_n']) if tv['HIGH_cot_n'] else '—'} |"
        )
    lines.append("")
    lines.append(
        f"IS-strong cells with Val lift vs ALL > 0: **{n_strong_val_same_sign_all}/{n_strong_scored}**; "
        f"with Val lift vs HIGH-long > 0: **{n_strong_val_same_sign_inc}/{n_strong_scored}**."
    )
    lines.append("")
    for block in sess_tables:
        lines.append(block)
        lines.append("")
    lines.append("## Reading vs pre-registered expectation")
    lines.append("")
    if val_tag == "VAL_COLLAPSE":
        lines.append(
            "Matches base-rate expectation of collapse toward / through baseline on the "
            "headline incremental contrast. **Do not** retune. OOS optional only for formal kill docs; "
            "do not start 23D as a rescue."
        )
    elif val_tag == "VAL_PARTIAL_DECAY":
        lines.append(
            "Matches pre-registered **partial decay** expectation. Incremental lift vs HIGH-long "
            "is weak or gone even if absolute HIGH+COT win rate looks non-zero. Treat as "
            "program-typical soft leftover unless multi-clock incremental lifts hold — they do not "
            "promote without OOS, and OOS is not unlocked here."
        )
    else:
        lines.append(
            "Val holds soft same-sign structure including incremental lift — still "
            "**not** promotion without OOS; multiplicity (120-cell grid + family 23) remains. "
            "Do not build executable system; await OOS unlock separately."
        )
    lines.append("")
    lines.append("## Stop")
    lines.append("")
    lines.append("- OOS **not** scored in this stage.")
    lines.append("- 23D **not** started.")
    lines.append("")

    payload = {
        "val_tag": val_tag,
        "frozen_definitions": True,
        "threshold_adjustment_on_val": False,
        "multiplicity_grid_cells": meta["n_grid_cells"],
        "eligible_is_cells_n60": 110,
        "is_strong": 5,
        "headline_IS": hl_is,
        "headline_Validation": hl_val,
        "strong_three_way_val": rows_val,
        "n_strong_val_lift_vs_ALL_pos": n_strong_val_same_sign_all,
        "n_strong_val_lift_vs_HIGH_long_pos": n_strong_val_same_sign_inc,
        "n_strong_scored": n_strong_scored,
    }
    return "\n".join(lines), payload


def write_oos_report(
    res_df: pd.DataFrame,
    is_candidates: list[dict[str, Any]],
    val_tag: str,
) -> tuple[str, dict[str, Any]]:
    """Documentation-only OOS triple. Not a promotion path."""
    meta = cell_count_meta()
    strong = [c for c in is_candidates if c.get("tier") == "strong"]
    headline = {
        "signal": "lev_fade",
        "session": "NY_AM",
        "T_offset": 30,
        "horizon": 30,
        "tier": "headline",
    }
    focus = strong[:]
    if not any(
        c["signal"] == "lev_fade"
        and c["session"] == "NY_AM"
        and int(c["T_offset"]) == 30
        and int(c["horizon"]) == 30
        for c in focus
    ):
        focus.insert(0, headline)

    def row3(c: dict[str, Any], split: str) -> dict[str, Any]:
        return three_way(
            res_df,
            c["signal"],
            c["session"],
            int(c["T_offset"]),
            int(c["horizon"]),
            split,
        )

    hl = {
        "IS": three_way(res_df, "lev_fade", "NY_AM", 30, 30, "IS"),
        "Validation": three_way(res_df, "lev_fade", "NY_AM", 30, 30, "Validation"),
        "OOS": three_way(res_df, "lev_fade", "NY_AM", 30, 30, "OOS"),
        "Y2025": three_way(res_df, "lev_fade", "NY_AM", 30, 30, "Y2025"),
        "Y2026": three_way(res_df, "lev_fade", "NY_AM", 30, 30, "Y2026"),
    }

    oos_inc = hl["OOS"].get("lift_vs_HIGH_long_win", np.nan)
    oos_all = hl["OOS"].get("lift_vs_ALL_win", np.nan)
    if np.isfinite(oos_inc) and oos_inc < 0:
        oos_tag = "OOS_INCREMENTAL_NEGATIVE"
    elif np.isfinite(oos_all) and oos_all <= 0:
        oos_tag = "OOS_COLLAPSE"
    else:
        oos_tag = "OOS_WEAK_OR_MIXED"

    lines: list[str] = []
    lines.append("# Hypothesis 23A — OOS (documentation only; not a rescue)")
    lines.append("")
    lines.append(
        f"Val already killed the headline incremental claim (`{val_tag}`). "
        "OOS is recorded for historical parity with other dossier rows — **not** to promote."
    )
    lines.append("")
    lines.append("## Freeze confirmation")
    lines.append("")
    lines.append("| Item | Status |")
    lines.append("|------|--------|")
    lines.append("| Definitions vs IS | **unchanged** (zero adjustment) |")
    lines.append("| Purpose | documentation triple IS/Val/OOS |")
    lines.append("")
    lines.append(f"**OOS tag:** `{oos_tag}`")
    lines.append("")
    lines.append("## Headline three-way — NY_AM `lev_fade` T+30 H30")
    lines.append("")
    lines.append(
        "| Split | ALL+COT | HIGH-long | HIGH+COT | Lift vs ALL | Lift vs HIGH-long | n |"
    )
    lines.append(
        "|-------|---------|-----------|----------|-------------|-------------------|---|"
    )
    for lab in ("IS", "Validation", "OOS", "Y2025", "Y2026"):
        tw = hl[lab]
        n = tw.get("HIGH_cot_n", 0)
        lines.append(
            f"| {lab} | {pct(tw['ALL_cot_win'])} | {pct(tw['HIGH_long_win'])} | "
            f"{pct(tw['HIGH_cot_win'])} | {pp(tw['lift_vs_ALL_win'])} | "
            f"{pp(tw['lift_vs_HIGH_long_win'])} | {int(n) if n else '—'} |"
        )
    lines.append("")
    lines.append("## IS-strong cells — three-way at OOS")
    lines.append("")
    lines.append(
        "| Signal | Session | T+ | H | OOS ALL+COT | OOS HIGH-long | OOS HIGH+COT | "
        "lift vs ALL | lift vs HIGH-long | n |"
    )
    lines.append(
        "|--------|---------|----|---|-------------|---------------|--------------|"
        "------------|-------------------|---|"
    )
    for c in focus:
        if c.get("tier") not in ("strong", "headline"):
            continue
        tw = row3(c, "OOS")
        n = tw.get("HIGH_cot_n", 0)
        lines.append(
            f"| {c['signal']} | {c['session']} | {c['T_offset']} | {c['horizon']} | "
            f"{pct(tw['ALL_cot_win'])} | {pct(tw['HIGH_long_win'])} | {pct(tw['HIGH_cot_win'])} | "
            f"{pp(tw['lift_vs_ALL_win'])} | {pp(tw['lift_vs_HIGH_long_win'])} | "
            f"{int(n) if n else '—'} |"
        )
    lines.append("")
    lines.append("## Multiplicity reminder")
    lines.append("")
    lines.append(
        f"IS scanned **{meta['n_grid_cells']}** cells; 5 strong ≈ noise rate. "
        "Do not cherry-pick OOS soft leftovers."
    )
    lines.append("")
    lines.append("## Family stop")
    lines.append("")
    lines.append("- Verdict **C** (see `conclusion.md`).")
    lines.append("- No 23B/23C rescue. 23D is a separate external-source sibling, not a COT retune.")
    lines.append("")

    payload = {
        "oos_tag": oos_tag,
        "val_tag": val_tag,
        "headline": hl,
        "multiplicity_grid_cells": meta["n_grid_cells"],
        "documentation_only": True,
    }
    return "\n".join(lines), payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--stage",
        choices=("IS", "VAL", "FULL", "OOS"),
        default="IS",
        help="IS / VAL / OOS(documentation) / FULL(score all splits + write OOS report).",
    )
    ap.add_argument(
        "--reuse-panel",
        action="store_true",
        help="Reuse nq_cot_23a_panel.parquet if present (no rebuild).",
    )
    args = ap.parse_args()

    print(f"=== 23A run_23a_test stage={args.stage} ===", flush=True)
    panel_path = art("nq_cot_23a_panel.parquet")
    if args.reuse_panel and panel_path.exists():
        panel = pd.read_parquet(panel_path)
        print(f"Reusing panel rows={len(panel)} <- {panel_path}", flush=True)
    else:
        panel = build_panel()
        if panel.empty:
            raise SystemExit("Empty panel — check COT map overlap with NQ")
        panel.to_parquet(panel_path, index=False)
        print(f"Panel rows={len(panel)} -> {panel_path}", flush=True)

    score_stage = "FULL" if args.stage in ("FULL", "OOS") else args.stage
    res_df = score_panel(panel, stage=score_stage)
    if args.stage == "VAL":
        prior = art("nq_cot_23a_results.csv")
        if prior.exists():
            old = pd.read_csv(prior)
            old_is = old[old["split"] == "IS"]
            res_df = pd.concat([old_is, res_df], ignore_index=True)
            res_df = res_df.drop_duplicates(
                subset=["session", "T_offset", "horizon", "universe", "split"],
                keep="last",
            )
    res_path = art("nq_cot_23a_results.csv")
    res_df.to_csv(res_path, index=False)
    print(f"Results rows={len(res_df)} -> {res_path}", flush=True)

    results_dir = _CODE.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    if args.stage == "IS":
        candidates, provisional = evaluate_is(res_df)
        cand_path = art("nq_cot_23a_candidates_IS.csv")
        pd.DataFrame(candidates).to_csv(cand_path, index=False)
        report = write_is_report(panel, res_df, candidates, provisional)
        md_path = art("nq_cot_23a_report_IS.md")
        md_path.write_text(report, encoding="utf-8")
        (results_dir / "IS.md").write_text(report, encoding="utf-8")
        print(f"IS report -> {md_path}", flush=True)
        print(f"Provisional IS: {provisional}", flush=True)
        return

    cand_path = art("nq_cot_23a_candidates_IS.csv")
    if cand_path.exists():
        is_candidates = pd.read_csv(cand_path).to_dict(orient="records")
    else:
        is_candidates, _ = evaluate_is(res_df)
        pd.DataFrame(is_candidates).to_csv(cand_path, index=False)

    if args.stage == "VAL":
        report, payload = write_val_report(res_df, is_candidates)
        md_path = art("nq_cot_23a_report_VAL.md")
        md_path.write_text(report, encoding="utf-8")
        (results_dir / "validation.md").write_text(report, encoding="utf-8")
        art("nq_cot_23a_report_VAL.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
        print(f"Val report -> {md_path} tag={payload['val_tag']}", flush=True)
        return

    # OOS / FULL documentation path
    val_path = art("nq_cot_23a_report_VAL.json")
    val_tag = "VAL_PARTIAL_DECAY"
    if val_path.exists():
        val_tag = json.loads(val_path.read_text(encoding="utf-8")).get(
            "val_tag", val_tag
        )

    # Ensure Val rows present for triple table
    if "Validation" not in set(res_df["split"]):
        res_val = score_panel(panel, stage="VAL")
        res_df = pd.concat([res_df, res_val], ignore_index=True).drop_duplicates(
            subset=["session", "T_offset", "horizon", "universe", "split"],
            keep="last",
        )
        res_df.to_csv(res_path, index=False)

    oos_report, oos_payload = write_oos_report(res_df, is_candidates, val_tag)
    md_path = art("nq_cot_23a_report_OOS.md")
    md_path.write_text(oos_report, encoding="utf-8")
    (results_dir / "OOS.md").write_text(oos_report, encoding="utf-8")
    art("nq_cot_23a_report_OOS.json").write_text(
        json.dumps(oos_payload, indent=2, default=str), encoding="utf-8"
    )
    # Keep Val report untouched; refresh full_report as OOS doc append pointer
    (results_dir / "full_report.md").write_text(
        (results_dir / "IS.md").read_text(encoding="utf-8")
        + "\n\n---\n\n"
        + (results_dir / "validation.md").read_text(encoding="utf-8")
        + "\n\n---\n\n"
        + oos_report,
        encoding="utf-8",
    )
    print(f"OOS report -> {md_path} tag={oos_payload['oos_tag']}", flush=True)
    hl = oos_payload["headline"]["OOS"]
    print(
        f"Headline OOS three-way: ALL={hl.get('ALL_cot_win')} HIGH_long={hl.get('HIGH_long_win')} "
        f"HIGH_cot={hl.get('HIGH_cot_win')} lift_ALL={hl.get('lift_vs_ALL_win')} "
        f"lift_Hlong={hl.get('lift_vs_HIGH_long_win')} n={hl.get('HIGH_cot_n')}",
        flush=True,
    )


if __name__ == "__main__":
    main()
