"""Diagnostic excursion/target-realism audit for the frozen IB continuation candidate."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_nq

ART = ROOT / "artifacts" / "30_initial_balance_breakout"
FLAT_OPEN = 15 * 60 + 55


def first_hit(path: pd.DataFrame, side: float, entry: float, risk: float, level_r: float) -> float:
    hit = (path.high.to_numpy() >= entry + level_r * risk) if side > 0 else (path.low.to_numpy() <= entry - level_r * risk)
    ix = np.flatnonzero(hit)
    return float(ix[0]) if len(ix) else np.nan


def analyse(t: pd.Series, g: pd.DataFrame) -> dict:
    side, entry, risk = (1.0 if t.side == "long" else -1.0), float(t.entry), float(t.risk_points)
    path = g.loc[int(t.entry_ny_min):FLAT_OPEN - 1]
    stop, target = entry - side * risk, entry + side * 2 * risk
    hit_stop = (path.low.to_numpy() <= stop) if side > 0 else (path.high.to_numpy() >= stop)
    hit_target = (path.high.to_numpy() >= target) if side > 0 else (path.low.to_numpy() <= target)
    si, ti = np.flatnonzero(hit_stop), np.flatnonzero(hit_target)
    if len(si) and (not len(ti) or si[0] <= ti[0]):
        terminal_i, terminal = int(si[0]), "stop"
    elif len(ti):
        terminal_i, terminal = int(ti[0]), "target"
    else:
        terminal_i, terminal = len(path) - 1, "time"
    pre = path.iloc[:terminal_i + 1]
    favorable = (pre.high.max() - entry) if side > 0 else (entry - pre.low.min())
    adverse = (entry - pre.low.min()) if side > 0 else (pre.high.max() - entry)
    full_favorable = (path.high.max() - entry) if side > 0 else (entry - path.low.min())
    full_adverse = (entry - path.low.min()) if side > 0 else (path.high.max() - entry)
    # First 0.25R directional move. A same-minute collision is explicitly labelled ambiguous.
    up = (path.high.to_numpy() >= entry + .25 * risk) if side > 0 else (path.low.to_numpy() <= entry - .25 * risk)
    down = (path.low.to_numpy() <= entry - .25 * risk) if side > 0 else (path.high.to_numpy() >= entry + .25 * risk)
    ui, di = np.flatnonzero(up), np.flatnonzero(down)
    first = "none"
    if len(ui) and (not len(di) or ui[0] < di[0]): first = "favorable"
    elif len(di) and (not len(ui) or di[0] < ui[0]): first = "adverse"
    elif len(ui) and len(di): first = "ambiguous_same_minute"
    result = t.to_dict()
    result.update({
        "recomputed_exit": terminal, "mfe_r_to_exit": favorable / risk, "mae_r_to_exit": adverse / risk,
        "mfe_r_full_rth": full_favorable / risk, "mae_r_full_rth": full_adverse / risk,
        "first_025r_move": first,
        **{f"minutes_to_{str(level).replace('.', '_')}r": first_hit(pre, side, entry, risk, level) for level in (.25, .5, 1., 1.5, 2.)},
    })
    return result


def distribution(x: pd.DataFrame, label: str) -> dict:
    row = {"group": label, "n": len(x), "mean_mfe_r": x.mfe_r_to_exit.mean(), "median_mfe_r": x.mfe_r_to_exit.median(),
           "p75_mfe_r": x.mfe_r_to_exit.quantile(.75), "mean_mae_r": x.mae_r_to_exit.mean(), "median_mae_r": x.mae_r_to_exit.median()}
    for r in (.25, .5, 1., 1.5, 2.):
        name = str(r).replace('.', '_')
        row[f"mfe_ge_{name}r"] = (x.mfe_r_to_exit >= r).mean()
        row[f"hit_{name}r_before_exit"] = x[f"minutes_to_{name}r"].notna().mean()
        row[f"median_minutes_to_{name}r"] = x.loc[x[f"minutes_to_{name}r"].notna(), f"minutes_to_{name}r"].median()
    return row


def main() -> None:
    candidates = pd.read_csv(ART / "nq_phase19_candidate_trades.csv")
    base = pd.read_csv(ART / "nq_baseline_trades.csv")
    d = candidates[["session_date", "risk_points", "exit_kind", "net_points"]].merge(base[["session_date", "split", "year", "side", "entry", "entry_ny_min"]], on="session_date", validate="one_to_one")
    nq = load_nq()
    sessions = {str(date): g[(g.ny_min >= 570) & (g.ny_min <= FLAT_OPEN)].sort_values("ny_min").set_index("ny_min") for date, g in nq.groupby("session_date", sort=False)}
    out = pd.DataFrame(analyse(t, sessions[str(t.session_date)]) for _, t in d.iterrows())
    out["outcome"] = np.where(out.net_points > 0, "winner", "loser_or_flat")
    rows = []
    for split, x in out.groupby("split", sort=False):
        rows.append(distribution(x, split + " all"))
        rows.append(distribution(x[x.outcome.eq("winner")], split + " winners"))
        rows.append(distribution(x[x.outcome.eq("loser_or_flat")], split + " losers_or_flat"))
    summary = pd.DataFrame(rows)
    first = pd.crosstab([out.split, out.outcome], out.first_025r_move, normalize="index").reset_index()
    out.to_csv(ART / "nq_phase21_excursion_trades.csv", index=False)
    summary.to_csv(ART / "nq_phase21_excursion_summary.csv", index=False)
    first.to_csv(ART / "nq_phase21_first_move.csv", index=False)
    report = ["# Phase 21 — frozen continuation excursion / target-realism audit", "",
              "Unchanged candidate: high-volume + early IB breakout, 0.50× IB-width stop, 2R target, 1 point round-trip costs. MFE/MAE are measured through the frozen trade exit; `full_rth` columns in the trade file extend through 15:54 for diagnostic context. Same-minute stop/target collision follows the existing stop-first rule. A first ±0.25R move on the same one-minute bar is labelled ambiguous rather than inferred.", "", "## MFE/MAE and threshold timing", "", summary.to_markdown(index=False), "", "## First meaningful (±0.25R) move", "", first.to_markdown(index=False)]
    (ART / "nq_phase21_excursion_report.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False)); print("\n", first.to_string(index=False))


if __name__ == "__main__": main()
