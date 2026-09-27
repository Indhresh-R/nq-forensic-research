"""Predeclared risk/target grid for the frozen NQ Initial Balance entry signal.

Selection is made from Discovery only. Validation and OOS are printed solely
for confirmation, never used by this script to choose a parameter.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_nq  # noqa: E402

ART = ROOT / "artifacts" / "30_initial_balance_breakout"
FLAT_OPEN = 15 * 60 + 55
COST = 1.0  # NQ round-trip points; deliberately identical to Phase 1

# All choices declared before examining this phase's grid output.
STOPS: tuple[tuple[str, float | None], ...] = (
    ("opposite_ib", None),
    ("0.25x_ib_width", 0.25),
    ("0.50x_ib_width", 0.50),
    ("0.75x_ib_width", 0.75),
    ("1.00x_ib_width", 1.00),
)
TARGET_R = (0.75, 1.00, 1.50, 2.00)


def outcome(t: pd.Series, g: pd.DataFrame, stop_name: str, fraction: float | None, target_r: float) -> dict:
    side = 1.0 if t.side == "long" else -1.0
    entry, entry_min = float(t.entry), int(t.entry_ny_min)
    distance = abs(entry - float(t.stop)) if stop_name == "opposite_ib" else float(t.ib_width) * float(fraction)
    stop, target = entry - side * distance, entry + side * distance * target_r
    # Entry minute is included: entry happens at its open; the remaining range can hit either level.
    path = g.loc[entry_min : FLAT_OPEN - 1]
    hi, lo = path.high.to_numpy(float), path.low.to_numpy(float)
    hit_stop = lo <= stop if side > 0 else hi >= stop
    hit_target = hi >= target if side > 0 else lo <= target
    stop_i = np.flatnonzero(hit_stop)
    target_i = np.flatnonzero(hit_target)
    # If both occur in one minute, stop_i <= target_i gives the adverse stop.
    if len(stop_i) and (not len(target_i) or stop_i[0] <= target_i[0]):
        exit_kind, exit_price = "stop", stop
    elif len(target_i):
        exit_kind, exit_price = "target", target
    else:
        exit_kind, exit_price = "time", float(g.at[FLAT_OPEN, "open"])
    return {"session_date": t.session_date, "stop_rule": stop_name, "target_r": target_r, "split": t.split, "year": t.year,
            "risk_points": distance, "exit_kind": exit_kind, "net_points": side * (exit_price - entry) - COST}


def metrics(x: pd.DataFrame) -> dict:
    pnl = x.net_points.to_numpy(float)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    return {"trades": len(x), "avg_net_points": pnl.mean(), "win_rate": (pnl > 0).mean(),
            "profit_factor": wins.sum() / abs(losses.sum()) if len(losses) else np.nan,
            "median_risk_points": x.risk_points.median(), "max_risk_points": x.risk_points.max(),
            "target_rate": (x.exit_kind == "target").mean(), "stop_rate": (x.exit_kind == "stop").mean()}


def main() -> None:
    trades = pd.read_csv(ART / "nq_baseline_trades.csv")
    nq = load_nq()
    sessions = {}
    for session_date, g0 in nq.groupby("session_date", sort=False):
        g = g0[(g0.ny_min >= 570) & (g0.ny_min <= FLAT_OPEN)].sort_values("ny_min").set_index("ny_min")
        if g.index.is_unique and pd.Index(range(570, FLAT_OPEN + 1)).isin(g.index).all():
            sessions[str(session_date)] = g
    rows = []
    for _, t in trades.iterrows():
        g = sessions.get(str(t.session_date))
        if g is None:
            continue
        for stop_name, fraction in STOPS:
            for target_r in TARGET_R:
                rows.append(outcome(t, g, stop_name, fraction, target_r))
    detail = pd.DataFrame(rows)
    summary_rows = []
    for (stop_rule, target_r, split), x in detail.groupby(["stop_rule", "target_r", "split"], sort=False):
        summary_rows.append({"stop_rule": stop_rule, "target_r": target_r, "split": split, **metrics(x)})
    summary = pd.DataFrame(summary_rows)
    grid = summary.pivot(index=["stop_rule", "target_r"], columns="split", values="avg_net_points").reset_index()
    for col in ("IS", "Validation", "OOS"):
        if col not in grid: grid[col] = np.nan
    # Explicitly chosen on IS alone; kept small to prevent a hidden OOS selection step.
    selected = grid.sort_values("IS", ascending=False).head(5).copy()
    selected["selection_basis"] = "top_5 Discovery avg_net_points only"
    detail.to_csv(ART / "nq_phase2_risk_grid_trades.csv", index=False)
    summary.to_csv(ART / "nq_phase2_risk_grid_summary.csv", index=False)
    grid.to_csv(ART / "nq_phase2_risk_grid.csv", index=False)
    selected.to_csv(ART / "nq_phase2_discovery_selected.csv", index=False)
    report = ["# NQ IB — Phase 2 risk/target grid", "",
              "All stop and target alternatives were declared in code before this grid was run. Candidates below were selected using Discovery only; Validation and OOS are confirmation columns.", "",
              "## Full grid: mean net NQ points per trade", "", grid.to_markdown(index=False), "",
              "## Discovery-only selected candidates", "", selected.to_markdown(index=False), "",
              "Risk rules: opposite IB edge, or a fixed 0.25/0.50/0.75/1.00 × IB-width stop from entry. Targets are 0.75/1.00/1.50/2.00R. Same-minute collisions use stop first. Cost is 1.0 point round trip."]
    (ART / "nq_phase2_risk_grid_report.md").write_text("\n".join(report), encoding="utf-8")
    print(selected.to_string(index=False))


if __name__ == "__main__":
    main()
