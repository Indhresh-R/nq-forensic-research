"""
Strategy 57 — Event B path/timing ladder (no P&L).

Frozen prereg only. Reuses Strategy 56 events + toward_rebreak side.
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

from constants import (
    HORIZONS,
    MAX_FIRST_REBREAK,
    MIN_IS,
    MIN_OOS,
    MIN_VAL,
    PREDICTED_SIDE_RULE,
    RESULTS,
    S52_RESULTS,
    S56_EVENTS,
    S56_VERDICT,
)


def load_panel() -> pd.DataFrame:
    states = pd.read_parquet(S52_RESULTS / "market_states.parquet")
    feats = pd.read_parquet(
        S52_RESULTS / "market_state_features.parquet",
        columns=["ts", "open", "high", "low", "close"],
    )
    if len(states) != len(feats):
        raise RuntimeError("S52 length mismatch")
    panel = states.copy()
    for c in ("open", "high", "low", "close"):
        panel[c] = feats[c].to_numpy(np.float64)
    panel = panel.sort_values(["session_date", "ny_min"]).reset_index(drop=True)
    return panel


def _fwd_ok(session, seg, ny, t: int, h: int) -> bool:
    n = len(session)
    th = t + h
    if th >= n:
        return False
    if session[th] != session[t] or seg[th] != seg[t]:
        return False
    return bool(ny[th] == ny[t] + h)


def load_events() -> pd.DataFrame:
    if not S56_EVENTS.exists():
        raise FileNotFoundError(f"Missing frozen Event B ledger: {S56_EVENTS}")
    events = pd.read_parquet(S56_EVENTS)
    verdict = json.loads(S56_VERDICT.read_text(encoding="utf-8"))
    side_rule = verdict.get("trade_side_rule")
    if side_rule != PREDICTED_SIDE_RULE:
        raise RuntimeError(
            f"Expected trade_side_rule={PREDICTED_SIDE_RULE!r}, got {side_rule!r}"
        )
    return events


def measure_paths(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)

    rows: list[dict] = []
    for ev in events.itertuples(index=False):
        t = int(ev.event_idx)
        side = int(ev.break_dir)  # toward_rebreak ⇒ side == break_dir
        R = float(ev.R)
        rebreak = float(ev.rebreak_level)
        c0 = float(close[t])
        if not (np.isfinite(R) and R > 0 and np.isfinite(c0)):
            for h in HORIZONS:
                rows.append(
                    {
                        "event_id": ev.event_id,
                        "horizon": h,
                        "valid": False,
                        "split": ev.split,
                        "break_dir": side,
                        "session_year": int(ev.session_year),
                        "prog_close": np.nan,
                        "mfe_dir": np.nan,
                        "mae_dir": np.nan,
                        "hit_rebreak": False,
                        "first_rebreak_bars": pd.NA,
                    }
                )
            continue

        first_rb: int | None = None
        for j in range(1, MAX_FIRST_REBREAK + 1):
            if not _fwd_ok(session, seg, ny, t, j):
                break
            tj = t + j
            if side > 0:
                hit = high[tj] >= rebreak
            else:
                hit = low[tj] <= rebreak
            if hit:
                first_rb = j
                break

        for h in HORIZONS:
            valid = _fwd_ok(session, seg, ny, t, h) and (t + h < n)
            rec: dict = {
                "event_id": ev.event_id,
                "horizon": h,
                "valid": bool(valid),
                "split": ev.split,
                "break_dir": side,
                "session_year": int(ev.session_year),
                "first_rebreak_bars": first_rb if first_rb is not None else pd.NA,
            }
            if not valid:
                rec.update(
                    {
                        "prog_close": np.nan,
                        "mfe_dir": np.nan,
                        "mae_dir": np.nan,
                        "hit_rebreak": False,
                    }
                )
                rows.append(rec)
                continue
            sl = slice(t + 1, t + h + 1)
            hi = high[sl]
            lo = low[sl]
            c_h = float(close[t + h])
            prog = side * (c_h - c0) / R
            if side > 0:
                mfe = (float(np.max(hi)) - c0) / R
                mae = (c0 - float(np.min(lo))) / R
                hit_rb = bool(np.any(hi >= rebreak))
            else:
                mfe = (c0 - float(np.min(lo))) / R
                mae = (float(np.max(hi)) - c0) / R
                hit_rb = bool(np.any(lo <= rebreak))
            rec.update(
                {
                    "prog_close": float(prog),
                    "mfe_dir": float(mfe),
                    "mae_dir": float(mae),
                    "hit_rebreak": hit_rb,
                }
            )
            rows.append(rec)
    return pd.DataFrame(rows)


def summarize_ladder(paths: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        for h in HORIZONS:
            g = paths.loc[(paths["horizon"] == h) & (paths["valid"])]
            if split != "ALL":
                g = g.loc[g["split"] == split]
            n = len(g)
            if n == 0:
                rows.append(
                    {
                        "split": split,
                        "horizon": h,
                        "n": 0,
                        "med": np.nan,
                        "mean": np.nan,
                        "p_pos": np.nan,
                        "p_hit_rebreak": np.nan,
                        "med_mfe": np.nan,
                        "med_mae": np.nan,
                    }
                )
                continue
            pc = g["prog_close"].to_numpy(np.float64)
            rows.append(
                {
                    "split": split,
                    "horizon": h,
                    "n": n,
                    "med": float(np.nanmedian(pc)),
                    "mean": float(np.nanmean(pc)),
                    "p_pos": float(np.mean(pc > 0)),
                    "p_hit_rebreak": float(g["hit_rebreak"].mean()),
                    "med_mfe": float(np.nanmedian(g["mfe_dir"].to_numpy(np.float64))),
                    "med_mae": float(np.nanmedian(g["mae_dir"].to_numpy(np.float64))),
                }
            )
    return pd.DataFrame(rows)


def _med_map(ladder: pd.DataFrame, split: str) -> dict[int, float]:
    out: dict[int, float] = {}
    for h in HORIZONS:
        m = ladder.loc[(ladder["split"] == split) & (ladder["horizon"] == h)]
        if m.empty:
            out[h] = float("nan")
        else:
            out[h] = float(m.iloc[0]["med"])
    return out


def _n_map(ladder: pd.DataFrame, split: str) -> dict[int, int]:
    out: dict[int, int] = {}
    for h in HORIZONS:
        m = ladder.loc[(ladder["split"] == split) & (ladder["horizon"] == h)]
        out[h] = 0 if m.empty else int(m.iloc[0]["n"])
    return out


def mono_ok(meds: dict[int, float]) -> bool:
    vals = [meds[h] for h in HORIZONS]
    if any(not np.isfinite(v) for v in vals):
        return False
    return bool(vals[0] <= vals[1] <= vals[2] <= vals[3])


def classify_path(ladder: pd.DataFrame) -> dict:
    detail: dict = {}
    for split, min_n in (("IS", MIN_IS), ("Validation", MIN_VAL), ("OOS", MIN_OOS)):
        ns = _n_map(ladder, split)
        meds = _med_map(ladder, split)
        n_ok = all(ns[h] >= min_n for h in HORIZONS)
        mono = mono_ok(meds)
        med60 = meds[60]
        mid_ok = (np.isfinite(meds[15]) and meds[15] > 0) or (
            np.isfinite(meds[30]) and meds[30] > 0
        )
        end_ok = np.isfinite(med60) and med60 > 0
        detail[split] = {
            "n": ns,
            "med": {str(h): meds[h] for h in HORIZONS},
            "n_ok": n_ok,
            "mono": mono,
            "med60_pos": bool(end_ok),
            "mid_ladder_pos": bool(mid_ok),
        }

    is_d = detail["IS"]
    if not (
        is_d["n_ok"]
        and is_d["med60_pos"]
        and is_d["mono"]
        and is_d["mid_ladder_pos"]
    ):
        reasons = []
        if not is_d["n_ok"]:
            reasons.append("IS_sample")
        if not is_d["med60_pos"]:
            reasons.append("IS_med60_not_pos")
        if not is_d["mono"]:
            reasons.append("IS_not_monotonic")
        if not is_d["mid_ladder_pos"]:
            reasons.append("IS_mid_ladder_not_pos")
        return {
            "classification": "PATH_KILL",
            "stage": "STEP1",
            "reason": "+".join(reasons),
            "detail": detail,
            "predicted_side_rule": PREDICTED_SIDE_RULE,
        }

    for split in ("Validation", "OOS"):
        d = detail[split]
        if not (d["n_ok"] and d["med60_pos"] and d["mono"]):
            reasons = []
            if not d["n_ok"]:
                reasons.append(f"{split}_sample")
            if not d["med60_pos"]:
                reasons.append(f"{split}_med60_not_pos")
            if not d["mono"]:
                reasons.append(f"{split}_not_monotonic")
            return {
                "classification": "PATH_KILL",
                "stage": "STEP2",
                "reason": "+".join(reasons),
                "detail": detail,
                "predicted_side_rule": PREDICTED_SIDE_RULE,
            }

    return {
        "classification": "PATH_ADVANCE",
        "stage": "STEP2",
        "reason": "IS_VAL_OOS_path_stable",
        "detail": detail,
        "predicted_side_rule": PREDICTED_SIDE_RULE,
    }


def first_rebreak_summary(paths: pd.DataFrame) -> pd.DataFrame:
    """One row per event (from H=60 rows) for descriptive first-touch timing."""
    g = paths.loc[paths["horizon"] == 60, ["event_id", "split", "valid", "first_rebreak_bars", "hit_rebreak"]]
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        s = g if split == "ALL" else g.loc[g["split"] == split]
        hit = s.loc[s["hit_rebreak"] == True]  # noqa: E712
        fr = pd.to_numeric(hit["first_rebreak_bars"], errors="coerce")
        rows.append(
            {
                "split": split,
                "n_events_h60_valid": int(s["valid"].sum()),
                "n_hit_rebreak_by_60": int(hit.shape[0]),
                "med_first_rebreak_bars": float(fr.median()) if len(fr) else np.nan,
                "p25_first_rebreak_bars": float(fr.quantile(0.25)) if len(fr) else np.nan,
                "p75_first_rebreak_bars": float(fr.quantile(0.75)) if len(fr) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading panel + Event B ledger...", flush=True)
    panel = load_panel()
    events = load_events()
    print(f"events={len(events)} panel={len(panel)}", flush=True)

    print("Measuring path ladder...", flush=True)
    paths = measure_paths(panel, events)
    paths.to_parquet(RESULTS / "path_progress.parquet", index=False)

    ladder = summarize_ladder(paths)
    ladder.to_csv(RESULTS / "path_ladder_by_split.csv", index=False)

    fr = first_rebreak_summary(paths)
    fr.to_csv(RESULTS / "first_rebreak_timing.csv", index=False)

    verdict = classify_path(ladder)
    (RESULTS / "path_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "classification": verdict["classification"],
                "stage": verdict["stage"],
                "reason": verdict["reason"],
            },
            indent=2,
        ),
        flush=True,
    )
    print("Wrote path artifacts.", flush=True)


if __name__ == "__main__":
    main()
