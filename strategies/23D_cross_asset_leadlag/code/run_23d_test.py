"""
23D — Overnight ES vs NQ relative strength → NQ direction under Strategy-12 HIGH.

Pre-registered grid (BEFORE any performance look): 24 cells
  NY_AM × clocks{15,30,60,90} × H{15,30,60} × signals{es_follow, es_fade}

Three-way from the start: ALL+signal / HIGH-long / HIGH+signal.
ZN/ZB unavailable — not tested.

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

from common.nq_session import NY_OPEN, art, load_es, load_nq, win_rate
from common.sessions import (
    SESSION_DECISION_OFFSETS,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

# --- FROZEN GRID (do not expand after look) ---
SESSION = "NY_AM"
CLOCKS = SESSION_DECISION_OFFSETS[SESSION]  # (15, 30, 60, 90)
HOLD_HS = (15, 30, 60)
SIGNALS = ("es_follow", "es_fade")
GRID_CELLS = len(CLOCKS) * len(HOLD_HS) * len(SIGNALS)  # 24
RTH_CLOSE_MIN = 16 * 60
PRIOR_CLOSE_MAX_NY = RTH_CLOSE_MIN  # <= 16:00

THRESH = json.loads(art("nq_multi_sess_opp_thresholds_IS.json").read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]

assert GRID_CELLS == 24, "grid drift — update methodology.md before scanning"


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


def after_bars(sess: pd.DataFrame, T_ny: int) -> pd.DataFrame:
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


def last_rth_close(day: pd.DataFrame) -> float:
    """Last close with ny_min <= 16:00."""
    d = day[day["ny_min"] <= PRIOR_CLOSE_MAX_NY]
    if len(d) == 0:
        return np.nan
    return float(d.sort_values("ny_min").iloc[-1]["close"])


def open_930(day: pd.DataFrame) -> float:
    exact = day[day["ny_min"] == NY_OPEN]
    if len(exact):
        return float(exact.iloc[0]["open"])
    later = day[day["ny_min"] > NY_OPEN].sort_values("ny_min")
    if len(later):
        return float(later.iloc[0]["open"])
    return np.nan


def build_overnight_rs(nq: pd.DataFrame, es: pd.DataFrame) -> pd.DataFrame:
    """One row per session_date with causal overnight RS (ES − NQ)."""
    nq_days = {sd: g for sd, g in nq.groupby("session_date", sort=True)}
    es_days = {sd: g for sd, g in es.groupby("session_date", sort=True)}
    sds = sorted(set(nq_days) & set(es_days))
    rows: list[dict[str, Any]] = []
    for i, sd in enumerate(sds):
        if i == 0:
            continue
        prev = sds[i - 1]
        nq_prev_c = last_rth_close(nq_days[prev])
        es_prev_c = last_rth_close(es_days[prev])
        nq_o = open_930(nq_days[sd])
        es_o = open_930(es_days[sd])
        if not all(np.isfinite(x) and x != 0 for x in (nq_prev_c, es_prev_c, nq_o, es_o)):
            continue
        nq_on = nq_o / nq_prev_c - 1.0
        es_on = es_o / es_prev_c - 1.0
        rs = es_on - nq_on
        if abs(rs) < 1e-15:
            side_follow = 0
        else:
            side_follow = 1 if rs > 0 else -1
        rows.append(
            {
                "session_date": sd,
                "prior_session_date": prev,
                "nq_prior_close": nq_prev_c,
                "es_prior_close": es_prev_c,
                "nq_open_930": nq_o,
                "es_open_930": es_o,
                "nq_overnight_ret": nq_on,
                "es_overnight_ret": es_on,
                "rs_es_nq": rs,
                "side_es_follow": side_follow,
                "side_es_fade": -side_follow if side_follow != 0 else 0,
                "zn_zb_status": "UNAVAILABLE",
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
        if int(rs_map[sd]["side_es_follow"]) == 0:
            continue
        b = bars_in_session(g, SESSION)
        if len(b) >= 40:
            sess_bars[sd] = b

    rows: list[dict[str, Any]] = []
    for sd, bars in sess_bars.items():
        fr = facts_map[sd]
        cot = rs_map[sd]  # overnight feature row
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        sf = int(cot["side_es_follow"])
        sd_fade = int(cot["side_es_fade"])
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
                "year": year,
                "split": split,
                "T_offset": off,
                "regime": reg,
                "side_es_follow": sf,
                "side_es_fade": sd_fade,
                "rs_es_nq": float(cot["rs_es_nq"]),
                "rng_psr": float(st["rng_psr"]),
            }
            any_h = False
            for H in HOLD_HS:
                if len(closes) < H:
                    row[f"pnl_long_{H}"] = np.nan
                    row[f"pnl_es_follow_{H}"] = np.nan
                    row[f"pnl_es_fade_{H}"] = np.nan
                    continue
                dpx = float(closes[H - 1]) - entry
                row[f"pnl_long_{H}"] = dpx
                row[f"pnl_es_follow_{H}"] = sf * dpx
                row[f"pnl_es_fade_{H}"] = sd_fade * dpx
                any_h = True
            if any_h:
                rows.append(row)
    return pd.DataFrame(rows)


def score_panel(panel: pd.DataFrame, stage: str) -> pd.DataFrame:
    splits = {
        "IS": ("IS",),
        "VAL": ("IS", "Validation"),
        "FULL": ("IS", "Validation", "OOS", "Y2025", "Y2026"),
        "OOS": ("IS", "Validation", "OOS", "Y2025", "Y2026"),
    }[stage]
    universes = (
        ("ALL_es_follow", "pnl_es_follow", None),
        ("HIGH_es_follow", "pnl_es_follow", "HIGH"),
        ("ALL_es_fade", "pnl_es_fade", None),
        ("HIGH_es_fade", "pnl_es_fade", "HIGH"),
        ("HIGH_long", "pnl_long", "HIGH"),
        ("ALL_long", "pnl_long", None),
    )
    results: list[dict[str, Any]] = []
    for off in CLOCKS:
        for H in HOLD_HS:
            base = panel[panel["T_offset"] == off]
            for uname, prefix, reg in universes:
                col = f"{prefix}_{H}"
                u = base if reg is None else base[base["regime"] == reg]
                u = u[u[col].notna()]
                for split in splits:
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
                            "session": SESSION,
                            "T_offset": off,
                            "horizon": H,
                            "universe": uname,
                            "split": split,
                            **m,
                        }
                    )
    return pd.DataFrame(results)


def three_way(
    res_df: pd.DataFrame, signal: str, off: int, H: int, split: str
) -> dict[str, Any]:
    def get(univ: str) -> dict[str, Any]:
        s = res_df[
            (res_df["T_offset"] == off)
            & (res_df["horizon"] == H)
            & (res_df["universe"] == univ)
            & (res_df["split"] == split)
        ]
        return s.iloc[0].to_dict() if len(s) else {}

    ab = get(f"ALL_{signal}")
    hb = get(f"HIGH_{signal}")
    hl = get("HIGH_long")
    out = {
        "signal": signal,
        "T_offset": off,
        "horizon": H,
        "split": split,
        "ALL_win": ab.get("win", np.nan),
        "ALL_E": ab.get("E", np.nan),
        "ALL_n": ab.get("n", 0),
        "HIGH_long_win": hl.get("win", np.nan),
        "HIGH_long_E": hl.get("E", np.nan),
        "HIGH_long_n": hl.get("n", 0),
        "HIGH_sig_win": hb.get("win", np.nan),
        "HIGH_sig_E": hb.get("E", np.nan),
        "HIGH_sig_n": hb.get("n", 0),
    }
    if hb and ab:
        out["lift_vs_ALL_win"] = hb["win"] - ab["win"]
        out["lift_vs_ALL_E"] = hb["E"] - ab["E"]
    else:
        out["lift_vs_ALL_win"] = out["lift_vs_ALL_E"] = np.nan
    if hb and hl:
        out["lift_vs_HIGH_long_win"] = hb["win"] - hl["win"]
        out["lift_vs_HIGH_long_E"] = hb["E"] - hl["E"]
    else:
        out["lift_vs_HIGH_long_win"] = out["lift_vs_HIGH_long_E"] = np.nan
    return out


def evaluate_is(res_df: pd.DataFrame) -> tuple[list[dict[str, Any]], str]:
    candidates: list[dict[str, Any]] = []
    for signal in SIGNALS:
        for off in CLOCKS:
            for H in HOLD_HS:
                tw = three_way(res_df, signal, off, H, "IS")
                if tw["HIGH_sig_n"] < 80 or tw["ALL_n"] < 80:
                    continue
                lw = tw["lift_vs_ALL_win"]
                le = tw["lift_vs_ALL_E"]
                inc_w = tw["lift_vs_HIGH_long_win"]
                inc_e = tw["lift_vs_HIGH_long_E"]
                if not (lw >= 0.03 or le >= 0.5):
                    continue
                if not (tw["HIGH_sig_win"] >= 0.52 or tw["HIGH_sig_E"] > 0):
                    continue
                # Must not lose to HIGH-long on both metrics
                if not (
                    (np.isfinite(inc_w) and inc_w >= -0.005)
                    or (np.isfinite(inc_e) and inc_e >= 0)
                ):
                    continue
                strong = (lw >= 0.05 or (le >= 1.0 and lw >= 0)) and (
                    tw["HIGH_sig_win"] >= 0.55
                    or (tw["HIGH_sig_win"] >= 0.52 and le >= 1.0)
                )
                # Strong also needs non-negative incremental vs HIGH-long win
                if strong and not (np.isfinite(inc_w) and inc_w >= 0):
                    strong = False
                candidates.append(
                    {
                        "signal": signal,
                        "session": SESSION,
                        "T_offset": off,
                        "horizon": H,
                        "tier": "strong" if strong else "soft",
                        "HIGH_sig_IS_win": tw["HIGH_sig_win"],
                        "ALL_IS_win": tw["ALL_win"],
                        "HIGH_long_IS_win": tw["HIGH_long_win"],
                        "lift_vs_ALL_win": lw,
                        "lift_vs_HIGH_long_win": inc_w,
                        "HIGH_sig_IS_n": tw["HIGH_sig_n"],
                    }
                )
    soft_n = sum(1 for c in candidates if c["tier"] == "soft")
    strong_n = sum(1 for c in candidates if c["tier"] == "strong")
    strong_clocks = {
        c["T_offset"] for c in candidates if c["tier"] == "strong"
    }
    if strong_n >= 1 and len(strong_clocks) >= 2:
        tag = "IS_PROMISING_PENDING_VAL"
    elif soft_n or strong_n:
        tag = "IS_SOFT_ONLY"
    else:
        tag = "IS_NULL"
    return candidates, tag


def write_is_report(
    panel: pd.DataFrame,
    res_df: pd.DataFrame,
    candidates: list[dict[str, Any]],
    tag: str,
) -> str:
    lines: list[str] = []
    lines.append("# Hypothesis 23D — Overnight ES/NQ RS under Strategy-12 HIGH (IS only)")
    lines.append("")
    lines.append("## Pre-registered grid (before scan)")
    lines.append("")
    lines.append(f"- Cells: **{GRID_CELLS}** = NY_AM × 4 clocks × 3 H × 2 signals")
    lines.append("- Expected false strong @~5%: **~1.2**")
    lines.append("- ZN/ZB: **UNAVAILABLE** (not tested)")
    lines.append("- Primary metric: HIGH+signal vs **HIGH-long** (incremental)")
    lines.append("")
    lines.append("## Freeze")
    lines.append("")
    lines.append(f"- Panel rows: **{len(panel):,}**")
    lines.append(f"- Soft / strong: **{sum(1 for c in candidates if c['tier']=='soft')}** / "
                 f"**{sum(1 for c in candidates if c['tier']=='strong')}**")
    lines.append(f"- Provisional IS tag: **`{tag}`**")
    lines.append("")
    lines.append("## Three-way H=30 (every clock)")
    lines.append("")
    for signal in SIGNALS:
        lines.append(f"### `{signal}`")
        lines.append("")
        lines.append(
            "| T+ | ALL+sig | HIGH-long | HIGH+sig | vs ALL | vs HIGH-long | n |"
        )
        lines.append(
            "|----|---------|-----------|----------|--------|--------------|---|"
        )
        for off in CLOCKS:
            tw = three_way(res_df, signal, off, 30, "IS")
            lines.append(
                f"| {off} | {pct(tw['ALL_win'])} | {pct(tw['HIGH_long_win'])} | "
                f"{pct(tw['HIGH_sig_win'])} | {pp(tw['lift_vs_ALL_win'])} | "
                f"{pp(tw['lift_vs_HIGH_long_win'])} | "
                f"{int(tw['HIGH_sig_n']) if tw['HIGH_sig_n'] else '—'} |"
            )
        lines.append("")
    lines.append("## IS candidates")
    lines.append("")
    if not candidates:
        lines.append("_None under frozen rules._")
    else:
        lines.append(
            "| Tier | Signal | T+ | H | HIGH+sig | vs ALL | vs HIGH-long | n |"
        )
        lines.append(
            "|------|--------|----|---|----------|--------|--------------|---|"
        )
        for c in sorted(
            candidates, key=lambda x: (x["tier"] != "strong", -x["lift_vs_HIGH_long_win"])
        ):
            lines.append(
                f"| {c['tier']} | {c['signal']} | {c['T_offset']} | {c['horizon']} | "
                f"{pct(c['HIGH_sig_IS_win'])} | {pp(c['lift_vs_ALL_win'])} | "
                f"{pp(c['lift_vs_HIGH_long_win'])} | {int(c['HIGH_sig_IS_n'])} |"
            )
    lines.append("")
    lines.append("## Pre-registered Val expectation (before Val look)")
    lines.append("")
    lines.append(
        "Per 23A base rate: 2–6pp IS lifts on this program usually show Val decay / "
        "incremental flip. With only 24 cells, even 1–2 strong hits are near noise. "
        "Decisive check remains HIGH+sig vs HIGH-long."
    )
    lines.append("")
    lines.append("## Multi-comparison")
    lines.append("")
    lines.append(
        "Family 23: 23A already **C**. This is a second external draw — do not promote "
        "on soft IS alone."
    )
    lines.append("")
    lines.append("## Stop")
    lines.append("")
    lines.append("- Val/OOS not scored.")
    lines.append("- Do not add ZN/ZB as a post-hoc expansion.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("IS", "VAL", "FULL", "OOS"), default="IS")
    args = ap.parse_args()
    if args.stage != "IS":
        raise SystemExit(
            f"Stage {args.stage} locked until IS review for 23D (grid={GRID_CELLS})."
        )

    print(f"=== 23D run_23d_test stage=IS grid={GRID_CELLS} ===", flush=True)
    print("Loading NQ + ES…", flush=True)
    nq = load_nq()
    es = load_es()
    rs = build_overnight_rs(nq, es)
    rs_path = art("nq_xasset_overnight_rs.parquet")
    rs.to_parquet(rs_path, index=False)
    print(f"Overnight RS days={len(rs)} -> {rs_path}", flush=True)

    panel = build_panel(nq, rs)
    if panel.empty:
        raise SystemExit("Empty 23D panel")
    panel_path = art("nq_xasset_23d_panel.parquet")
    panel.to_parquet(panel_path, index=False)
    print(f"Panel rows={len(panel)} -> {panel_path}", flush=True)

    res_df = score_panel(panel, stage="IS")
    res_df.to_csv(art("nq_xasset_23d_results.csv"), index=False)
    candidates, tag = evaluate_is(res_df)
    pd.DataFrame(candidates).to_csv(art("nq_xasset_23d_candidates_IS.csv"), index=False)

    report = write_is_report(panel, res_df, candidates, tag)
    art("nq_xasset_23d_report_IS.md").write_text(report, encoding="utf-8")
    results_dir = _CODE.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "IS.md").write_text(report, encoding="utf-8")
    (results_dir / "full_report.md").write_text(report, encoding="utf-8")
    (results_dir / "validation.md").write_text(
        "# Validation — 23D\n\n**Not scored.** Awaiting IS review.\n", encoding="utf-8"
    )
    (results_dir / "OOS.md").write_text(
        "# OOS — 23D\n\n**Not scored.**\n", encoding="utf-8"
    )

    payload = {
        "stage": "IS",
        "provisional_IS": tag,
        "grid_cells_preregistered": GRID_CELLS,
        "expected_false_strong_approx": round(0.05 * GRID_CELLS, 2),
        "n_panel": int(len(panel)),
        "n_soft": int(sum(1 for c in candidates if c["tier"] == "soft")),
        "n_strong": int(sum(1 for c in candidates if c["tier"] == "strong")),
        "zn_zb": "UNAVAILABLE",
        "candidates": candidates,
        "val_oos_scored": False,
    }
    art("nq_xasset_23d_report_IS.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    (_CODE.parent / "conclusion.md").write_text(
        "\n".join(
            [
                "# Conclusion — 23D",
                "",
                f"**Provisional IS tag:** `{tag}`",
                "",
                f"Grid pre-registered at **{GRID_CELLS}** cells. ZN/ZB unavailable.",
                "Val/OOS not scored.",
                "",
                "See `results/IS.md`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(
        f"IS tag={tag} soft={payload['n_soft']} strong={payload['n_strong']} "
        f"(grid={GRID_CELLS}, ~noise {payload['expected_false_strong_approx']})",
        flush=True,
    )


if __name__ == "__main__":
    main()
