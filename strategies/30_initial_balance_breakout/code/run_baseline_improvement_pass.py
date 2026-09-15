"""Single-pass, pre-registered baseline-improvement test for NQ IB breakout."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.nq_session import load_nq

ART = ROOT / "artifacts" / "30_initial_balance_breakout" / "baseline_improvement_pass_20260914"
OPEN, IB_END, LAST_SIGNAL_CLOSE, FLAT_OPEN = 570, 630, 929, 955
COST, TICK = 1.0, 0.25
GATES = {"Train": range(2010, 2019), "Inner Validation": range(2019, 2022), "Validation": range(2022, 2025), "OOS": range(2025, 2027)}
CANDIDATES = {
    "baseline_control": {"label": "#1 Baseline control", "stop_mode": "opposite", "target_r": 1.0, "latest_signal": LAST_SIGNAL_CLOSE},
    "half_ib_stop": {"label": "#2 Half-IB stop", "stop_mode": "half_ib", "target_r": 1.0, "latest_signal": LAST_SIGNAL_CLOSE},
    "target_1_5r": {"label": "#3 1.5R target", "stop_mode": "opposite", "target_r": 1.5, "latest_signal": LAST_SIGNAL_CLOSE},
    "early_breakout": {"label": "#4 Early-breakout filter", "stop_mode": "opposite", "target_r": 1.0, "latest_signal": 719},
    "half_ib_early": {"label": "#5 Half-IB stop + early-breakout filter", "stop_mode": "half_ib", "target_r": 1.0, "latest_signal": 719},
}


def simulate_day(g0: pd.DataFrame, spec: dict) -> dict | None:
    g = g0[(g0.ny_min >= OPEN) & (g0.ny_min <= FLAT_OPEN)].sort_values("ny_min").set_index("ny_min")
    required = pd.Index(range(OPEN, FLAT_OPEN + 1))
    if not g.index.is_unique or not required.isin(g.index).all():
        return None
    g = g.loc[required]
    ib = g.loc[OPEN:IB_END - 1]
    ib_high, ib_low = float(ib.high.max()), float(ib.low.min())
    ib_width = ib_high - ib_low
    if ib_width <= 0:
        return None
    signal_min, side = None, 0
    for close_min in range(IB_END + 4, min(LAST_SIGNAL_CLOSE, spec["latest_signal"]) + 1, 5):
        close = float(g.at[close_min, "close"])
        if close >= ib_high + TICK:
            signal_min, side = close_min, 1
            break
        if close <= ib_low - TICK:
            signal_min, side = close_min, -1
            break
    if signal_min is None:
        return None
    entry_min = signal_min + 1
    entry = float(g.at[entry_min, "open"])
    if spec["stop_mode"] == "opposite":
        stop = ib_low if side > 0 else ib_high
    else:
        stop = entry - side * 0.5 * ib_width
    risk = side * (entry - stop)
    if risk <= 0:
        return None
    target = entry + side * spec["target_r"] * risk
    exit_kind, exit_min, exit_price = "time", FLAT_OPEN, float(g.at[FLAT_OPEN, "open"])
    for minute in range(entry_min, FLAT_OPEN):
        hi, lo = float(g.at[minute, "high"]), float(g.at[minute, "low"])
        if (lo <= stop if side > 0 else hi >= stop):
            exit_kind, exit_min, exit_price = "stop", minute, stop
            break
        if (hi >= target if side > 0 else lo <= target):
            exit_kind, exit_min, exit_price = "target", minute, target
            break
    gross = side * (exit_price - entry)
    return {"session_date": str(g0.session_date.iloc[0]), "year": int(g0.year.iloc[0]), "side": side,
            "signal_min": signal_min, "entry": entry, "stop": stop, "target": target, "risk_points": risk,
            "exit_kind": exit_kind, "net_points": gross - COST}


def trades_for_years(df: pd.DataFrame, spec: dict, years: range) -> pd.DataFrame:
    work = df[df.year.isin(years)]
    return pd.DataFrame(r for _, g in work.groupby("session_date", sort=True) if (r := simulate_day(g, spec)))


def metrics(t: pd.DataFrame) -> dict:
    if t.empty:
        return {"trades": 0, "net_points": 0.0, "avg_net_points": np.nan, "profit_factor": np.nan, "max_drawdown_points": np.nan, "avg_risk_points": np.nan}
    p = t.net_points.to_numpy(float); wins, losses = p[p > 0], p[p < 0]
    equity = np.cumsum(p); dd = equity - np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return {"trades": len(t), "net_points": float(p.sum()), "avg_net_points": float(p.mean()),
            "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) else np.nan,
            "max_drawdown_points": float(dd.min()), "avg_risk_points": float(t.risk_points.mean())}


def save_json(name: str, payload: object) -> None:
    (ART / name).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")


def stage_train_inner(df: pd.DataFrame) -> None:
    rows, detail = [], {}
    for name, spec in CANDIDATES.items():
        train, inner = trades_for_years(df, spec, GATES["Train"]), trades_for_years(df, spec, GATES["Inner Validation"])
        tm, im = metrics(train), metrics(inner)
        comb = pd.concat([train, inner], ignore_index=True)
        cm = metrics(comb)
        eligible = tm["trades"] >= 100 and im["trades"] >= 50
        rows.append({"candidate": name, "label": spec["label"], "eligible": eligible, **{f"train_{k}": v for k,v in tm.items()}, **{f"inner_{k}": v for k,v in im.items()}, **{f"combined_{k}": v for k,v in cm.items()}})
        detail[name] = {"train": tm, "inner_validation": im, "combined": cm}
    ranking = pd.DataFrame(rows).sort_values(["eligible", "combined_profit_factor", "combined_avg_net_points", "combined_trades"], ascending=[False, False, False, False], na_position="last").reset_index(drop=True)
    ranking.insert(0, "rank", range(1, len(ranking) + 1))
    selected = ranking.loc[ranking.eligible, "candidate"].iloc[0] if ranking.eligible.any() else None
    ranking.to_csv(ART / "step2_train_inner_ranking.csv", index=False)
    save_json("step2_selection.json", {"selection_rule": "combined Train + Inner Validation profit factor; eligibility Train >=100 and Inner Validation >=50; ties combined average net points then trade count", "selected_candidate": selected, "ranking": ranking.to_dict(orient="records"), "details": detail})
    print(ranking[["rank", "candidate", "eligible", "combined_trades", "combined_profit_factor", "combined_avg_net_points"]].to_string(index=False))


def stage_confirmation(df: pd.DataFrame, gate: str) -> None:
    selection = json.loads((ART / "step2_selection.json").read_text(encoding="utf-8"))
    selected = selection["selected_candidate"]
    if selected is None:
        raise RuntimeError("No eligible candidate was selected.")
    years = GATES[gate]
    chosen, base = trades_for_years(df, CANDIDATES[selected], years), trades_for_years(df, CANDIDATES["baseline_control"], years)
    cm, bm = metrics(chosen), metrics(base)
    min_trades = 100 if gate == "Validation" else 80
    passed = cm["trades"] >= min_trades and cm["profit_factor"] > 1.0 and cm["avg_net_points"] > bm["avg_net_points"]
    payload = {"gate": gate, "selected_candidate": selected, "selected_metrics": cm, "baseline_metrics": bm, "pass": bool(passed), "criteria": {"min_trades": min_trades, "profit_factor_gt": 1.0, "avg_net_points_strictly_gt_baseline": True}}
    save_json(f"step{4 if gate == 'Validation' else 5}_{gate.lower().replace(' ', '_')}.json", payload)
    chosen.assign(candidate=selected).to_csv(ART / f"{gate.lower().replace(' ', '_')}_selected_trades.csv", index=False)
    print(json.dumps(payload, indent=2, allow_nan=False))


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--stage", choices=("train-inner", "validation", "oos"), required=True); args = p.parse_args()
    ART.mkdir(parents=True, exist_ok=True)
    if args.stage == "oos":
        validation = json.loads((ART / "step4_validation.json").read_text(encoding="utf-8"))
        if not validation["pass"]:
            raise RuntimeError("Validation did not pass; OOS is prohibited by preregistration.")
    df = load_nq()
    if args.stage == "train-inner": stage_train_inner(df)
    elif args.stage == "validation": stage_confirmation(df, "Validation")
    else: stage_confirmation(df, "OOS")


if __name__ == "__main__":
    main()
