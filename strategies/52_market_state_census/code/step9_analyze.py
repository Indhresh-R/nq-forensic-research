"""
Step 9 — One simple executable hypothesis (D fade-to-mid, 15m horizon).

Frozen before P&L. No optimization. No extra filters.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import RESULTS
from step1_constants import CELL_C, CELL_D
from step2_constants import FAMILY_EXP_EXIT
from step7_analyze import load_low_er_cut
from step8_analyze import verify_population

COST_RT = 1.0
HOLD_MINUTES = 15
MIN_TRADES_SPLIT = 200


def build_trade_panel() -> pd.DataFrame:
    """Panel with open/high/low/close for next-open fills (census-eligible rows)."""
    states = pd.read_parquet(RESULTS / "market_states.parquet")
    feats = pd.read_parquet(
        RESULTS / "market_state_features.parquet",
        columns=["ts", "open", "high", "low", "close"],
    )
    if len(states) != len(feats):
        raise RuntimeError("market_states and features row counts differ")
    panel = states.copy()
    for c in ("open", "high", "low", "close"):
        panel[c] = feats[c].to_numpy(np.float64)
    return (
        panel.loc[panel["census_eligible"]]
        .sort_values(["session_date", "ny_min"])
        .reset_index(drop=True)
    )


def _path_ok(session, seg, ny, te: int, i1: int) -> bool:
    n = len(session)
    if i1 >= n or i1 <= te:
        return False
    if session[i1] != session[te] or seg[i1] != seg[te]:
        return False
    return bool(np.all(np.diff(ny[te : i1 + 1]) == 1))


def last_valid_exit_idx(session, seg, ny, te: int, target: int) -> int | None:
    """Largest i in (te, target] with contiguous session path from te, or None."""
    n = len(session)
    last = None
    for i in range(te + 1, min(target, n - 1) + 1):
        if not _path_ok(session, seg, ny, te, i):
            break
        last = i
    return last


def simulate_trades(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    open_ = panel["open"].to_numpy(np.float64)
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)

    rows = []
    for ev in events.itertuples(index=False):
        i0 = int(ev.onset_panel_idx)
        te = int(ev.event_panel_idx)
        if te <= i0:
            continue

        # origin envelope [i0, te)
        sl = slice(i0, te)
        p_high = float(high[sl].max())
        p_low = float(low[sl].min())
        r = p_high - p_low
        if not np.isfinite(r) or r <= 0:
            continue
        p_mid = 0.5 * (p_high + p_low)
        p_event = float(close[te])

        if p_event < p_mid:
            side = 1
        elif p_event > p_mid:
            side = -1
        else:
            continue  # skip exactly at mid

        entry_i = te + 1
        if not _path_ok(session, seg, ny, te, entry_i):
            continue
        entry = float(open_[entry_i])
        if not np.isfinite(entry):
            continue

        target_i = te + HOLD_MINUTES
        exit_i = last_valid_exit_idx(session, seg, ny, te, target_i)
        if exit_i is None:
            continue
        exit_px = float(close[exit_i])
        hold = int(exit_i - te)
        gross = side * (exit_px - entry)
        net = gross - COST_RT

        rows.append(
            {
                "event_id": ev.event_id,
                "origin_cell": ev.origin_cell,
                "arm": "PRIMARY_D" if ev.origin_cell == CELL_D else "CONTROL_C",
                "split": ev.split,
                "session_year": int(ev.session_year),
                "side": side,
                "p_event": p_event,
                "p_mid": p_mid,
                "p_high": p_high,
                "p_low": p_low,
                "entry_price": entry,
                "exit_price": exit_px,
                "hold_minutes": hold,
                "full_horizon": hold == HOLD_MINUTES,
                "gross_pts": gross,
                "net_pts": net,
                "cost_rt": COST_RT,
            }
        )
    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for arm in ("PRIMARY_D", "CONTROL_C"):
        for split in ("IS", "Validation", "OOS", "ALL"):
            g = trades.loc[trades["arm"] == arm]
            if split != "ALL":
                g = g.loc[g["split"] == split]
            n = len(g)
            rows.append(
                {
                    "arm": arm,
                    "split": split,
                    "n_trades": n,
                    "n_long": int((g["side"] == 1).sum()) if n else 0,
                    "n_short": int((g["side"] == -1).sum()) if n else 0,
                    "mean_gross": float(g["gross_pts"].mean()) if n else np.nan,
                    "mean_net": float(g["net_pts"].mean()) if n else np.nan,
                    "median_net": float(g["net_pts"].median()) if n else np.nan,
                    "hit_rate_net_gt_0": float((g["net_pts"] > 0).mean()) if n else np.nan,
                    "sum_net": float(g["net_pts"].sum()) if n else np.nan,
                    "frac_full_horizon": float(g["full_horizon"].mean()) if n else np.nan,
                    "eligible_gate": n >= MIN_TRADES_SPLIT,
                }
            )
    return pd.DataFrame(rows)


def classify(summary: pd.DataFrame) -> dict:
    prim = summary.loc[summary["arm"] == "PRIMARY_D"]
    detail = {}
    ok = True
    for sp in ("IS", "Validation", "OOS"):
        row = prim.loc[prim["split"] == sp]
        if row.empty:
            detail[sp] = {"ok": False, "reason": "missing"}
            ok = False
            continue
        r = row.iloc[0]
        e_net = float(r["mean_net"])
        n = int(r["n_trades"])
        eligible = bool(r["eligible_gate"])
        pass_sp = eligible and np.isfinite(e_net) and e_net > 0
        detail[sp] = {
            "n_trades": n,
            "mean_net": e_net,
            "eligible": eligible,
            "pass": pass_sp,
        }
        if not pass_sp:
            ok = False

    ctrl = {}
    for sp in ("IS", "Validation", "OOS", "ALL"):
        row = summary.loc[(summary["arm"] == "CONTROL_C") & (summary["split"] == sp)]
        if len(row):
            ctrl[sp] = {
                "n_trades": int(row.iloc[0]["n_trades"]),
                "mean_net": float(row.iloc[0]["mean_net"]),
            }

    return {
        "classification": "PROMOTE_CANDIDATE" if ok else "KILL",
        "decision": (
            "PROCEED_TO_PROP_RISK_EVAL"
            if ok
            else "STOP_DO_NOT_BUILD_STRATEGY"
        ),
        "hypothesis": (
            f"Low-ER ExpExit D: fade toward P_mid; entry open[te+1]; "
            f"exit close[te+{HOLD_MINUTES}]; cost {COST_RT} pt RT; no SL/TP"
        ),
        "cost_rt": COST_RT,
        "hold_minutes": HOLD_MINUTES,
        "min_trades_split": MIN_TRADES_SPLIT,
        "primary_gate": detail,
        "control_c": ctrl,
        "research_question_answer": (
            "Yes — primary D arm has positive net expectancy on IS, Validation, and OOS."
            if ok
            else "No — primary D arm fails the preregistered expectancy gate; kill."
        ),
    }


def main() -> None:
    print("Loading frozen Step7 population…", flush=True)
    pop = pd.read_parquet(RESULTS / "step7_population.parquet")
    check = verify_population(pop)
    if not check["ok"]:
        raise RuntimeError(f"Population mismatch: {check}")
    cut = load_low_er_cut()
    if not (pop["te_er_60"] <= cut + 1e-12).all():
        raise RuntimeError("te_er_60 above frozen cut")

    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    events = events.loc[events["event_id"].isin(pop["event_id"])].copy()
    events = events.loc[events["family"] == FAMILY_EXP_EXIT]
    if len(events) != len(pop):
        raise RuntimeError(f"event join mismatch {len(events)} vs {len(pop)}")

    print("Building panel + simulating H1…", flush=True)
    panel = build_trade_panel()
    trades = simulate_trades(panel, events)
    trades.to_parquet(RESULTS / "step9_trades.parquet", index=False)

    summary = summarize(trades)
    summary.to_csv(RESULTS / "step9_summary.csv", index=False)

    verdict = classify(summary)
    verdict["population_check"] = check
    verdict["n_trades_total"] = int(len(trades))
    verdict["n_trades_primary_d"] = int((trades["arm"] == "PRIMARY_D").sum())
    verdict["n_trades_control_c"] = int((trades["arm"] == "CONTROL_C").sum())
    (RESULTS / "step9_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(f"Verdict: {verdict['classification']}", flush=True)
    for sp, d in verdict["primary_gate"].items():
        print(
            f"  D {sp}: n={d.get('n_trades')} E_net={d.get('mean_net')} pass={d.get('pass')}",
            flush=True,
        )


if __name__ == "__main__":
    main()
