"""Predeclared causal post-entry path-state audit for the frozen continuation trade."""
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
HORIZONS = (5, 10, 15, 30, 45, 60)
LEVELS = (.25, .5, .75, 1.0)


def first_index(a: np.ndarray) -> int | None:
    ix = np.flatnonzero(a)
    return int(ix[0]) if len(ix) else None


def path_record(t: pd.Series, g: pd.DataFrame) -> list[dict]:
    side = 1.0 if t.side == "long" else -1.0
    entry, risk = float(t.entry), float(t.risk_points)
    p = g.loc[int(t.entry_ny_min):FLAT_OPEN - 1]
    hi, lo = p.high.to_numpy(float), p.low.to_numpy(float)
    fav = (hi - entry) / risk if side > 0 else (entry - lo) / risk
    adv = (entry - lo) / risk if side > 0 else (hi - entry) / risk
    stop_i = first_index(adv >= 1.0)
    target_i = first_index(fav >= 2.0)
    exit_i = min([x for x in (stop_i, target_i) if x is not None], default=len(p) - 1)
    terminal = "stop" if stop_i is not None and (target_i is None or stop_i <= target_i) else ("target" if target_i is not None else "time")
    records = []
    for h in HORIZONS:
        # A decision at h is meaningful only when the original trade has neither stopped nor hit 2R.
        live = exit_i >= h and terminal == "time" or (exit_i >= h and terminal in ("stop", "target"))
        # `exit_i == h` occurs after the h-minute observation; keep it live until that bar completes.
        live = exit_i >= h
        prefix_fav, prefix_adv = fav[:h], adv[:h]
        row = {"session_date": t.session_date, "split": t.split, "year": t.year, "horizon_min": h,
               "live_at_h": live, "terminal": terminal, "eventual_2r_target": terminal == "target",
               "mfe_r_h": prefix_fav.max(), "mae_r_h": prefix_adv.max()}
        for level in LEVELS:
            row[f"mfe_ge_{level}"] = prefix_fav.max() >= level
            row[f"mae_ge_{level}"] = prefix_adv.max() >= level
        # Ordered trajectory, using a meaningful recovery level after an initial adverse move.
        a25, f25, f50 = first_index(adv >= .25), first_index(fav >= .25), first_index(fav >= .5)
        if a25 is not None and f50 is not None and a25 < f50:
            row["trajectory"] = "adverse_025_then_recover_050"
        elif f50 is not None and (a25 is None or f50 < a25):
            row["trajectory"] = "favorable_050_before_adverse_025"
        elif a25 is not None:
            row["trajectory"] = "adverse_025_no_recovery_050"
        else:
            row["trajectory"] = "no_025_adverse"
        records.append(row)
    return records


def rate(x: pd.DataFrame) -> dict:
    return {"n": len(x), "eventual_2r_rate": x.eventual_2r_target.mean(), "eventual_2r_n": x.eventual_2r_target.sum()}


def main() -> None:
    c = pd.read_csv(ART / "nq_phase19_candidate_trades.csv")
    b = pd.read_csv(ART / "nq_baseline_trades.csv")
    d = c[["session_date", "risk_points"]].merge(b[["session_date", "split", "year", "side", "entry", "entry_ny_min"]], on="session_date", validate="one_to_one")
    nq = load_nq()
    sessions = {str(date): g[(g.ny_min >= 570) & (g.ny_min <= FLAT_OPEN)].sort_values("ny_min").set_index("ny_min") for date, g in nq.groupby("session_date", sort=False)}
    states = pd.DataFrame(r for _, t in d.iterrows() for r in path_record(t, sessions[str(t.session_date)]))
    live = states[states.live_at_h].copy()
    rows = []
    # State A/B/C: every declared horizon and excursion level, reported without selection.
    for h in HORIZONS:
        z = live[live.horizon_min.eq(h)]
        for split, x in z.groupby("split", sort=False):
            rows.append({"family": "live_base", "horizon_min": h, "state": "all_live", "split": split, **rate(x)})
            for level in LEVELS:
                for col, label in ((f"mae_ge_{level}", f"MAE>={level}R"), (f"mfe_ge_{level}", f"MFE>={level}R"), (f"mfe_ge_{level}", f"no_MFE>={level}R")):
                    y = x[~x[col]] if label.startswith("no_") else x[x[col]]
                    rows.append({"family": "state_grid", "horizon_min": h, "state": label, "split": split, **rate(y)})
            for trajectory, y in x.groupby("trajectory", sort=False):
                rows.append({"family": "trajectory", "horizon_min": h, "state": trajectory, "split": split, **rate(y)})
    summary = pd.DataFrame(rows)
    states.to_csv(ART / "nq_phase22_path_states.csv", index=False)
    summary.to_csv(ART / "nq_phase22_path_summary.csv", index=False)
    report = ["# Phase 22 — frozen continuation causal path-dependency audit", "",
              "No strategy rule changes. Predeclared horizons: 5, 10, 15, 30, 45, 60 minutes; predeclared excursion levels: 0.25, 0.50, 0.75, 1.00R. Rows use only information available through the stated horizon and include only trades still live at that time; the outcome is eventual 2R target before the frozen stop. This avoids treating a trade that already stopped or hit its target as an actionable later state. All Train, Validation, and OOS rows are reported; no row is selected as a rule.", "", "## State probabilities of eventual 2R", "", summary.to_markdown(index=False)]
    (ART / "nq_phase22_path_report.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__": main()
