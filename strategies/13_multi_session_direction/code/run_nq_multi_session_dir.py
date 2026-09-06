"""
NQ Multi-session Direction (Phase B) — Strategy 13

Frozen from strategy 12. NO threshold retuning. NO stop/target mining.

Signal families (independent):
  HIGH_FOLLOW — vol_expansion_high; side = sign(close_T - session_open)
  HIGH_FADE   — vol_expansion_high; side = opposite
  BLIND_FOLLOW / BLIND_FADE — same direction rules without HIGH gate

Trade card (frozen a priori):
  Entry: next bar open after T (causal); stress delay = +1 extra bar
  Stop:  0.25 * psr
  Target: 0.25 * psr   (1R)
  Max hold: 15 / 30 / 45 minutes (primary report = 30)
  Same-bar stop+target: STOP FIRST
  Costs (round-trip pts): tight=0.50, mid=1.00, wide=2.00  [execution_assumptions.md]

Sessions evaluated independently. Report order: LONDON → NY_PM → NY_AM → ASIA.
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

# Report / eval order (not a combine)
SESSION_PRIORITY = ("LONDON", "NY_PM", "NY_AM", "ASIA")

HOLD_HS = (15, 30, 45)
PRIMARY_H = 30
STOP_FRAC = 0.25
TARGET_FRAC = 0.25
COST_PTS = {"tight": 0.50, "mid": 1.00, "wide": 2.00}
PRIMARY_COST = "mid"

GATE = json.loads(art("frozen_multi_session_gate.json").read_text(encoding="utf-8"))
THRESH = json.loads(art("nq_multi_sess_opp_thresholds_IS.json").read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]


def th_rng(session: str, off: int) -> dict[str, float] | None:
    d = STATE_TH.get(session, {}).get(str(off)) or STATE_TH.get(session, {}).get(off)
    if not d:
        return None
    return d.get("rng_psr")


def is_high(session: str, off: int, rng_psr: float) -> bool:
    t = th_rng(session, off)
    return bool(t) and float(rng_psr) >= float(t["p66"])


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


def simulate_trade(
    after: pd.DataFrame,
    side: int,
    entry_delay: int,
    stop_pts: float,
    target_pts: float,
    max_hold: int,
) -> dict[str, float] | None:
    """
    side: +1 long / -1 short.
    entry_delay: 0 = first after bar open; 1 = skip one bar (adverse delay stress).
    """
    need = entry_delay + max_hold
    if len(after) < need + 1:
        return None
    entry = float(after.iloc[entry_delay]["open"])
    if side > 0:
        stop_px = entry - stop_pts
        target_px = entry + target_pts
    else:
        stop_px = entry + stop_pts
        target_px = entry - target_pts

    path = after.iloc[entry_delay + 1 : entry_delay + 1 + max_hold]
    if len(path) == 0:
        return None
    highs = path["high"].to_numpy(float)
    lows = path["low"].to_numpy(float)
    closes = path["close"].to_numpy(float)
    exit_px = float(closes[-1])
    exit_reason = "time"
    bars_held = int(len(closes))
    for i in range(len(closes)):
        hi, lo = highs[i], lows[i]
        hit_stop = (lo <= stop_px) if side > 0 else (hi >= stop_px)
        hit_tgt = (hi >= target_px) if side > 0 else (lo <= target_px)
        if hit_stop and hit_tgt:
            exit_px = stop_px
            exit_reason = "stop_both"
            bars_held = i + 1
            break
        if hit_stop:
            exit_px = stop_px
            exit_reason = "stop"
            bars_held = i + 1
            break
        if hit_tgt:
            exit_px = target_px
            exit_reason = "target"
            bars_held = i + 1
            break

    gross = side * (exit_px - entry)
    return {
        "entry": entry,
        "exit": exit_px,
        "gross_pts": gross,
        "bars_held": float(bars_held),
        "exit_reason": 0.0
        if exit_reason == "time"
        else (1.0 if exit_reason.startswith("stop") else 2.0),
        "hit_stop": 1.0 if exit_reason.startswith("stop") else 0.0,
        "hit_target": 1.0 if exit_reason == "target" else 0.0,
    }


def summarize(trades: pd.DataFrame, cost: float) -> dict[str, float]:
    if len(trades) == 0:
        return {
            "n": 0,
            "win": np.nan,
            "E_gross": np.nan,
            "E_net": np.nan,
            "E_R_net": np.nan,
            "PF_net": np.nan,
        }
    g = trades["gross_pts"].to_numpy(float)
    net = g - cost
    stop = float(trades["stop_pts"].iloc[0]) if "stop_pts" in trades.columns else np.nan
    wins = net[net > 0]
    losses = net[net <= 0]
    pf = (
        float(wins.sum() / abs(losses.sum()))
        if len(losses) and abs(losses.sum()) > 0
        else (np.inf if len(wins) else np.nan)
    )
    wr = win_rate(pd.Series(net))
    return {
        "n": int(len(trades)),
        "win": float(wr["rate"]),
        "E_gross": float(np.mean(g)),
        "E_net": float(np.mean(net)),
        "E_R_net": float(np.mean(net / stop)) if np.isfinite(stop) and stop > 0 else np.nan,
        "PF_net": float(pf) if np.isfinite(pf) else np.nan,
    }


def verdict_row(is_m: dict, val_m: dict, oos_m: dict, y25: dict, y26: dict) -> str:
    """Decision gate from user brief."""
    if not is_m["n"] or not oos_m["n"]:
        return "INCONCLUSIVE"
    # direction random-ish
    if abs(is_m["win"] - 0.5) < 0.02 and abs(oos_m.get("win", 0.5) - 0.5) < 0.03:
        if not (np.isfinite(oos_m["E_net"]) and oos_m["E_net"] > 0):
            return "NO_TRADE"
    if np.isfinite(is_m["E_net"]) and is_m["E_net"] > 0:
        if not (np.isfinite(val_m["E_net"]) and val_m["E_net"] > 0):
            return "REJECT_IS_ONLY"
        if not (np.isfinite(oos_m["E_net"]) and oos_m["E_net"] > 0):
            return "REJECT_OOS"
        # costs already in E_net; if gross+ but net-
        if np.isfinite(oos_m["E_gross"]) and oos_m["E_gross"] > 0 and oos_m["E_net"] <= 0:
            return "REJECT_COSTS"
        year_ok = (
            np.isfinite(y25.get("E_net", np.nan))
            and np.isfinite(y26.get("E_net", np.nan))
            and y25["E_net"] > 0
            and y26["E_net"] > 0
            and y25.get("n", 0) >= 20
            and y26.get("n", 0) >= 20
        )
        if year_ok:
            return "STRONG_CANDIDATE"
        return "PROMISING"
    return "NO_TRADE"


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pts(x: Any) -> str:
    return f"{x:+.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== Strategy 13: Multi-session Direction (Phase B) ===", flush=True)
    print(
        f"Freeze: stop=target={STOP_FRAC}*psr; H={HOLD_HS}; costs={COST_PTS}; "
        f"primary H={PRIMARY_H} cost={PRIMARY_COST}",
        flush=True,
    )
    print(f"Gate sessions: {GATE['promoted_sessions']}", flush=True)

    df = load_nq()
    facts = build_session_facts(df)
    facts_map = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}

    sess_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=False):
        for name in SESSION_PRIORITY:
            key = (sd, name)
            if key not in facts_map:
                continue
            bars = bars_in_session(g, name)
            if len(bars) >= 40:
                sess_bars[key] = bars
    print(f"Session slices: {len(sess_bars)}", flush=True)

    rows: list[dict] = []
    n_done = 0
    for (sd, name), bars in sess_bars.items():
        fr = facts_map[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        stop_pts = STOP_FRAC * psr
        target_pts = TARGET_FRAC * psr
        for off in SESSION_DECISION_OFFSETS[name]:
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars,
                session=name,
                T_ny=T,
                session_open=session_open,
                psr=psr,
            )
            if st is None:
                continue
            dir_sign = int(st["dir_sign"])
            if dir_sign == 0:
                continue
            high = is_high(name, off, float(st["rng_psr"]))
            after = after_bars(bars, T, name)
            if len(after) < max(HOLD_HS) + 2:
                continue

            families = [("BLIND_FOLLOW", dir_sign, True), ("BLIND_FADE", -dir_sign, True)]
            if high:
                families.extend(
                    [("HIGH_FOLLOW", dir_sign, True), ("HIGH_FADE", -dir_sign, True)]
                )

            for fam, side, _ in families:
                for delay_name, delay in (("next_open", 0), ("delay1", 1)):
                    for H in HOLD_HS:
                        sim = simulate_trade(
                            after, side, delay, stop_pts, target_pts, H
                        )
                        if sim is None:
                            continue
                        rows.append(
                            {
                                "session_date": str(sd),
                                "session": name,
                                "year": year,
                                "split": split,
                                "T_offset": off,
                                "T_ny": T,
                                "family": fam,
                                "entry_mode": delay_name,
                                "hold_H": H,
                                "side": side,
                                "psr": psr,
                                "stop_pts": stop_pts,
                                "target_pts": target_pts,
                                "rng_psr": float(st["rng_psr"]),
                                "high": int(high),
                                **sim,
                            }
                        )
        n_done += 1
        if n_done % 1000 == 0:
            print(f"  session-days {n_done}, trades~{len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel_path = art("nq_multi_sess_dir_panel.parquet")
    panel.to_parquet(panel_path, index=False)
    print(f"Trade rows: {len(panel)} -> {panel_path}", flush=True)
    if panel.empty:
        raise SystemExit("Empty direction panel")

    # Metrics
    results: list[dict[str, Any]] = []
    for sess in SESSION_PRIORITY:
        for fam in ("HIGH_FOLLOW", "HIGH_FADE", "BLIND_FOLLOW", "BLIND_FADE"):
            for delay_name in ("next_open", "delay1"):
                for H in HOLD_HS:
                    for cost_name, cost in COST_PTS.items():
                        for split in ("IS", "Validation", "OOS"):
                            sub = panel[
                                (panel["session"] == sess)
                                & (panel["family"] == fam)
                                & (panel["entry_mode"] == delay_name)
                                & (panel["hold_H"] == H)
                                & (panel["split"] == split)
                            ]
                            m = summarize(sub, cost)
                            results.append(
                                {
                                    "session": sess,
                                    "family": fam,
                                    "entry_mode": delay_name,
                                    "hold_H": H,
                                    "cost": cost_name,
                                    "cost_pts": cost,
                                    "split": split,
                                    **m,
                                }
                            )
                        # year break on OOS years
                        for y in (2025, 2026):
                            sub = panel[
                                (panel["session"] == sess)
                                & (panel["family"] == fam)
                                & (panel["entry_mode"] == delay_name)
                                & (panel["hold_H"] == H)
                                & (panel["year"] == y)
                            ]
                            m = summarize(sub, cost)
                            results.append(
                                {
                                    "session": sess,
                                    "family": fam,
                                    "entry_mode": delay_name,
                                    "hold_H": H,
                                    "cost": cost_name,
                                    "cost_pts": cost,
                                    "split": f"Y{y}",
                                    **m,
                                }
                            )

    res_df = pd.DataFrame(results)
    res_path = art("nq_multi_sess_dir_results.csv")
    res_df.to_csv(res_path, index=False)

    def get_m(sess, fam, split, H=PRIMARY_H, delay="next_open", cost=PRIMARY_COST):
        s = res_df[
            (res_df["session"] == sess)
            & (res_df["family"] == fam)
            & (res_df["split"] == split)
            & (res_df["hold_H"] == H)
            & (res_df["entry_mode"] == delay)
            & (res_df["cost"] == cost)
        ]
        if len(s) == 0:
            return {"n": 0, "win": np.nan, "E_gross": np.nan, "E_net": np.nan, "E_R_net": np.nan, "PF_net": np.nan}
        return s.iloc[0].to_dict()

    # Verdicts primary card
    verdicts: list[dict[str, Any]] = []
    lines = [
        "# Strategy 13 — Multi-session Direction (Phase B)",
        "",
        "## Freeze",
        "",
        f"- Stop = Target = **{STOP_FRAC} × psr** (1R)",
        f"- Max hold primary **{PRIMARY_H}m** (also 15/45)",
        f"- Entry: next open; stress **delay1**",
        f"- Costs primary **{PRIMARY_COST}={COST_PTS[PRIMARY_COST]} pts** RT",
        f"- Same-bar ambiguity: **stop first**",
        f"- Sessions independent; order: {' → '.join(SESSION_PRIORITY)}",
        "",
        "## Primary card (HIGH_FOLLOW / HIGH_FADE, next_open, H30, mid cost)",
        "",
    ]

    for sess in SESSION_PRIORITY:
        lines.append(f"### {sess}")
        lines.append("")
        lines.append(
            "| Family | IS n | IS win | IS E_net | Val E_net | OOS E_net | OOS win | Y25 E_net | Y26 E_net | Verdict |"
        )
        lines.append(
            "|--------|------|--------|----------|-----------|-----------|---------|-----------|-----------|---------|"
        )
        for fam in ("HIGH_FOLLOW", "HIGH_FADE", "BLIND_FOLLOW", "BLIND_FADE"):
            is_m = get_m(sess, fam, "IS")
            val_m = get_m(sess, fam, "Validation")
            oos_m = get_m(sess, fam, "OOS")
            y25 = get_m(sess, fam, "Y2025")
            y26 = get_m(sess, fam, "Y2026")
            v = verdict_row(is_m, val_m, oos_m, y25, y26)
            verdicts.append(
                {
                    "session": sess,
                    "family": fam,
                    "verdict": v,
                    "IS_n": is_m["n"],
                    "IS_win": is_m["win"],
                    "IS_E_net": is_m["E_net"],
                    "Val_E_net": val_m["E_net"],
                    "OOS_E_net": oos_m["E_net"],
                    "OOS_win": oos_m["win"],
                    "Y2025_E_net": y25["E_net"],
                    "Y2026_E_net": y26["E_net"],
                }
            )
            lines.append(
                f"| {fam} | {is_m['n']} | {pct(is_m['win'])} | {pts(is_m['E_net'])} | "
                f"{pts(val_m['E_net'])} | {pts(oos_m['E_net'])} | {pct(oos_m['win'])} | "
                f"{pts(y25['E_net'])} | {pts(y26['E_net'])} | **{v}** |"
            )
        lines.append("")

    # Cost kill check: OOS gross+ net-
    lines.append("## Cost sensitivity (HIGH families, H30, next_open, OOS E_net)")
    lines.append("")
    lines.append("| Session | Family | tight | mid | wide |")
    lines.append("|---------|--------|-------|-----|------|")
    for sess in SESSION_PRIORITY:
        for fam in ("HIGH_FOLLOW", "HIGH_FADE"):
            cells = []
            for c in ("tight", "mid", "wide"):
                cells.append(pts(get_m(sess, fam, "OOS", cost=c)["E_net"]))
            lines.append(f"| {sess} | {fam} | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines.append("")

    # Delay stress
    lines.append("## Entry delay stress (HIGH, H30, mid, OOS E_net)")
    lines.append("")
    lines.append("| Session | Family | next_open | delay1 |")
    lines.append("|---------|--------|-----------|--------|")
    for sess in SESSION_PRIORITY:
        for fam in ("HIGH_FOLLOW", "HIGH_FADE"):
            a = pts(get_m(sess, fam, "OOS", delay="next_open")["E_net"])
            b = pts(get_m(sess, fam, "OOS", delay="delay1")["E_net"])
            lines.append(f"| {sess} | {fam} | {a} | {b} |")
    lines.append("")

    # Overall
    vdf = pd.DataFrame(verdicts)
    n_promising = int(
        (vdf["verdict"].isin(["PROMISING", "STRONG_CANDIDATE"])).sum()
    )
    lines.append("## Gate summary")
    lines.append("")
    lines.append(f"- Cells PROMISING/STRONG: **{n_promising}** / {len(vdf)}")
    if n_promising == 0:
        lines.append("- **Program call: no executable directional edge under frozen card.**")
    else:
        good = vdf[vdf["verdict"].isin(["PROMISING", "STRONG_CANDIDATE"])]
        lines.append("- Survivors:")
        for _, r in good.iterrows():
            lines.append(
                f"  - {r['session']} {r['family']}: {r['verdict']} "
                f"(OOS E_net={pts(r['OOS_E_net'])})"
            )
    lines.append("")

    report_path = art("nq_multi_sess_dir_report.md")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    vdf.to_csv(art("nq_multi_sess_dir_verdicts.csv"), index=False)
    art("nq_multi_sess_dir_report.json").write_text(
        json.dumps(
            {
                "n_trades": int(len(panel)),
                "primary_H": PRIMARY_H,
                "stop_frac": STOP_FRAC,
                "cost_primary": PRIMARY_COST,
                "n_promising": n_promising,
                "verdicts": verdicts,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"Report -> {report_path}", flush=True)
    print(f"Promising/strong cells: {n_promising}", flush=True)


if __name__ == "__main__":
    main()
