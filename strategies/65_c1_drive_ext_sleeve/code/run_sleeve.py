"""
Strategy 65 — C1_DRIVE_EXT continuation sleeve.

Frozen under CHARTER_C1_DRIVE_EXT_SLEEVE.md.
NO promote without verdict rules. Cost 1.0 pt RT.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))

from constants import (  # noqa: E402
    BARS_PATH,
    COST_RT,
    ENTRY_MIN,
    EXIT_MIN,
    GATE_CHARACTER,
    GATE_CLOCK,
    IS_YEARS,
    LABELS_PATH,
    OOS_YEARS,
    RESULTS,
    STOP_FLOOR,
    STOP_RANGE_FRAC,
    VAL_YEARS,
)

NY = "America/New_York"
SESSION_START_MIN = 18 * 60


def _as_date(v) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    return date.fromisoformat(str(v)[:10])


def split_of(year: int) -> str:
    if year in IS_YEARS:
        return "IS"
    if year in VAL_YEARS:
        return "Val"
    if year in OOS_YEARS:
        return "OOS"
    return "Other"


def load_gates() -> pd.DataFrame:
    lab = pd.read_parquet(LABELS_PATH)
    lab["session_date"] = lab["session_date"].map(_as_date)
    g = lab.loc[
        (lab["clock"] == GATE_CLOCK) & (lab["character"] == GATE_CHARACTER)
    ].copy()
    g = g.loc[g["axis_L"].isin(["L_ABOVE", "L_BELOW"])]
    return g.reset_index(drop=True)


def load_morning_bars() -> pd.DataFrame:
    df = pd.read_parquet(BARS_PATH, columns=["ts_event", "open", "high", "low", "close", "volume"])
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    out = pd.DataFrame(
        {
            "ts": ts,
            "open": df["open"].to_numpy(np.float64),
            "high": df["high"].to_numpy(np.float64),
            "low": df["low"].to_numpy(np.float64),
            "close": df["close"].to_numpy(np.float64),
        }
    )
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    cal = out["ts"].dt.date
    out["session_date"] = np.where(
        out["ny_min"].to_numpy() >= SESSION_START_MIN,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    out["session_date"] = out["session_date"].map(_as_date)
    # entry window through time exit
    return out.loc[(out["ny_min"] >= ENTRY_MIN) & (out["ny_min"] <= EXIT_MIN + 5)].copy()


def simulate_trade(side: str, entry: float, stop_dist: float, bars: pd.DataFrame) -> dict:
    """side: 'long' or 'short'. bars sorted by ny_min, starting at entry bar."""
    if bars.empty:
        return {
            "exit_reason": "no_bars",
            "exit_px": np.nan,
            "gross": np.nan,
            "mfe": np.nan,
            "mae": np.nan,
            "n_bars_held": 0,
        }
    stop_px = entry - stop_dist if side == "long" else entry + stop_dist
    mfe = 0.0
    mae = 0.0
    for i in range(len(bars)):
        row = bars.iloc[i]
        o = float(row["open"])
        h = float(row["high"])
        l = float(row["low"])
        ny = int(row["ny_min"])

        if ny >= EXIT_MIN:
            # Time flat at this bar's open. If open already through stop, that fill.
            if side == "long":
                stopped_at_open = o <= stop_px
                fill = stop_px if stopped_at_open else o
            else:
                stopped_at_open = o >= stop_px
                fill = stop_px if stopped_at_open else o
            gross = (fill - entry) if side == "long" else (entry - fill)
            return {
                "exit_reason": "stop" if stopped_at_open else "time",
                "exit_px": float(fill),
                "gross": float(gross),
                "mfe": float(mfe),
                "mae": float(mae),
                "n_bars_held": i + 1,
            }

        if side == "long":
            mfe = max(mfe, h - entry)
            mae = max(mae, entry - l)
            stopped = l <= stop_px
        else:
            mfe = max(mfe, entry - l)
            mae = max(mae, h - entry)
            stopped = h >= stop_px
        if stopped:
            fill = stop_px
            gross = (fill - entry) if side == "long" else (entry - fill)
            return {
                "exit_reason": "stop",
                "exit_px": float(fill),
                "gross": float(gross),
                "mfe": float(mfe),
                "mae": float(mae),
                "n_bars_held": i + 1,
            }

    last = bars.iloc[-1]
    fill = float(last["close"])
    gross = (fill - entry) if side == "long" else (entry - fill)
    return {
        "exit_reason": "session_end",
        "exit_px": fill,
        "gross": float(gross),
        "mfe": float(mfe),
        "mae": float(mae),
        "n_bars_held": len(bars),
    }


def run_trades(gates: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    by_sess = {s: g.sort_values("ny_min") for s, g in bars.groupby("session_date", sort=False)}
    rows = []
    for _, gate in gates.iterrows():
        sess = gate["session_date"]
        if sess not in by_sess:
            continue
        g = by_sess[sess]
        entry_bars = g.loc[g["ny_min"] >= ENTRY_MIN]
        if entry_bars.empty:
            continue
        entry_row = entry_bars.iloc[0]
        if int(entry_row["ny_min"]) > ENTRY_MIN + 5:
            # too late / gap — skip
            continue
        entry = float(entry_row["open"])
        side = "long" if gate["axis_L"] == "L_ABOVE" else "short"
        stop_dist = max(STOP_FLOOR, STOP_RANGE_FRAC * float(gate["prefix_range"]))
        path = entry_bars.copy()
        sim = simulate_trade(side, entry, stop_dist, path)
        year = sess.year
        rows.append(
            {
                "session_date": sess,
                "year": year,
                "split": split_of(year),
                "axis_L": gate["axis_L"],
                "side": side,
                "prefix_range": float(gate["prefix_range"]),
                "stop_dist": stop_dist,
                "entry_px": entry,
                "entry_ny_min": int(entry_row["ny_min"]),
                **sim,
                "net": float(sim["gross"] - COST_RT) if np.isfinite(sim["gross"]) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame, label: str) -> dict:
    t = trades.loc[trades["gross"].notna()]
    n = len(t)
    if n == 0:
        return {"split": label, "n": 0}
    med_mfe = float(t["mfe"].median())
    med_mae = float(t["mae"].median())
    rel = (med_mfe - med_mae) / max(med_mae, 1e-9)
    return {
        "split": label,
        "n": n,
        "mean_gross": float(t["gross"].mean()),
        "mean_net": float(t["net"].mean()),
        "med_net": float(t["net"].median()),
        "stop_rate": float((t["exit_reason"] == "stop").mean()),
        "time_exit_rate": float((t["exit_reason"] == "time").mean()),
        "med_mfe": med_mfe,
        "med_mae": med_mae,
        "mfe_mae_rel_diff": float(rel),
        "win_rate_net": float((t["net"] > 0).mean()),
    }


def decide(summary: pd.DataFrame) -> dict:
    is_row = summary.loc[summary["split"] == "IS"]
    val_row = summary.loc[summary["split"] == "Val"]
    oos_row = summary.loc[summary["split"] == "OOS"]
    if is_row.empty or int(is_row.iloc[0]["n"]) < 200:
        return {
            "verdict": "KILL",
            "reason": "IS n < 200 or missing",
        }
    is_ = is_row.iloc[0]
    if float(is_["mean_net"]) <= 0:
        return {
            "verdict": "KILL",
            "reason": f"IS mean_net={is_['mean_net']:.4f} ≤ 0",
        }
    if float(is_["mfe_mae_rel_diff"]) < 0.25:
        return {
            "verdict": "KILL",
            "reason": f"IS path gate fail mfe_mae_rel_diff={is_['mfe_mae_rel_diff']:.4f} < 0.25",
        }
    val_ok = (not val_row.empty) and float(val_row.iloc[0]["mean_net"]) > 0
    oos_ok = (not oos_row.empty) and float(oos_row.iloc[0]["mean_net"]) > 0
    if val_ok and oos_ok:
        return {
            "verdict": "ADVANCE_RISK_DESIGN",
            "reason": "IS net>0, path gate pass, Val and OOS mean_net>0 — trails only under new charter",
        }
    return {
        "verdict": "INCONCLUSIVE",
        "reason": "IS cleared cost+path but Val/OOS did not both show mean_net>0",
    }


def write_report(summary: pd.DataFrame, verdict: dict, audit: dict) -> None:
    lines = [
        "# Strategy 65 — C1 Drive-Exterior Continuation Sleeve",
        "",
        "**Gate:** C1_DRIVE_EXT @ 10:30 → with-trend → stop / 12:00 time exit. Cost 1.0 pt RT.",
        "",
        f"**Verdict: `{verdict['verdict']}`**",
        "",
        verdict["reason"],
        "",
        "## Freeze",
        "",
        "```json",
        json.dumps(audit, indent=2, default=str),
        "```",
        "",
        "## Summary by split",
        "",
        summary.to_string(index=False),
        "",
        "## Interpretation",
        "",
        "- KILL → do not trail / do not shop characters.",
        "- INCONCLUSIVE → no risk-design follow-on.",
        "- ADVANCE_RISK_DESIGN → new charter only (trails), not live.",
        "",
        "**No live trading from this run.**",
        "",
    ]
    (RESULTS / "SLEEVE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("loading gates...", flush=True)
    gates = load_gates()
    print(f"  gate sessions={len(gates)}", flush=True)
    print("loading bars...", flush=True)
    bars = load_morning_bars()
    print(f"  path bars={len(bars)}", flush=True)
    trades = run_trades(gates, bars)
    trades.to_parquet(RESULTS / "trades.parquet", index=False)
    print(f"  trades={len(trades)}", flush=True)

    rows = [summarize(trades, "All")]
    for sp in ["IS", "Val", "OOS"]:
        rows.append(summarize(trades.loc[trades["split"] == sp], sp))
    summary = pd.DataFrame(rows)
    summary.to_csv(RESULTS / "summary_by_split.csv", index=False)

    verdict = decide(summary)
    audit = {
        "GATE_CLOCK": GATE_CLOCK,
        "GATE_CHARACTER": GATE_CHARACTER,
        "ENTRY_MIN": ENTRY_MIN,
        "EXIT_MIN": EXIT_MIN,
        "STOP_RANGE_FRAC": STOP_RANGE_FRAC,
        "STOP_FLOOR": STOP_FLOOR,
        "COST_RT": COST_RT,
        "NO_TARGET": True,
        "NO_TRAIL": True,
        "NOT_ORB": True,
        "NOT_VA_FADE": True,
        "n_gates": int(len(gates)),
        "n_trades": int(len(trades)),
    }
    out = {
        "verdict": verdict["verdict"],
        "reason": verdict["reason"],
        "promote": False,
        "summary": summary.to_dict(orient="records"),
    }
    (RESULTS / "verdict.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    (RESULTS / "audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    write_report(summary, verdict, audit)
    print(json.dumps(out, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
