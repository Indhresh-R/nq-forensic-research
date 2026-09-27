"""
Strategy 59 — Opening Range Break first-passage.

Frozen prereg only. Target + adverse co-defined. No retuning.
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

from common.splits import split_of

from constants import (
    COST_RT,
    DELTA_FP_IS,
    DELTA_FP_VAL,
    H_CAP,
    H_WAIT,
    MAE_PTS_MAX,
    MAE_R_FRAC,
    MIN_IS,
    MIN_OOS,
    MIN_TRADES_SPLIT,
    MIN_VAL,
    NY_OPEN,
    P_TARGET_IS,
    P_TARGET_OOS,
    P_TARGET_VAL,
    RESULTS,
    S52_RESULTS,
    TARGET_R_MULT,
    W_OR,
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
    panel["split"] = [split_of(int(y)) for y in panel["session_year"].to_numpy()]
    return panel


def _fwd_ok(session, seg, ny, t: int, h: int) -> bool:
    n = len(session)
    th = t + h
    if th >= n:
        return False
    if session[th] != session[t] or seg[th] != seg[t]:
        return False
    return bool(ny[th] == ny[t] + h)


def extract_events(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    eligible = panel["census_eligible"].to_numpy(bool)
    split = panel["split"].to_numpy(dtype=object)
    year = panel["session_year"].to_numpy(np.int16)
    n = len(panel)

    or_end = NY_OPEN + W_OR  # 600
    search_end = or_end + H_WAIT  # 690

    funnel = {
        "n_sessions_seen": 0,
        "n_or_ok": 0,
        "n_events": 0,
        "n_no_break": 0,
        "n_or_incomplete": 0,
    }

    rows: list[dict] = []
    # group by session_date indices
    dates, starts = np.unique(session, return_index=True)
    starts = list(starts) + [n]
    funnel["n_sessions_seen"] = int(len(dates))

    for s in range(len(dates)):
        i0, i1 = starts[s], starts[s + 1]
        ny_s = ny[i0:i1]
        # map ny_min -> local index for OR window
        or_mask = (ny_s >= NY_OPEN) & (ny_s < or_end)
        or_idx = np.flatnonzero(or_mask)
        if len(or_idx) != W_OR:
            funnel["n_or_incomplete"] += 1
            continue
        # require exact minutes and contiguous
        or_ny = ny_s[or_idx]
        if or_ny[0] != NY_OPEN or or_ny[-1] != or_end - 1:
            funnel["n_or_incomplete"] += 1
            continue
        if not np.all(np.diff(or_ny) == 1):
            funnel["n_or_incomplete"] += 1
            continue
        # same segment for OR
        or_seg = seg[i0 + or_idx]
        if not np.all(or_seg == or_seg[0]):
            funnel["n_or_incomplete"] += 1
            continue

        glo = i0 + or_idx
        or_high = float(np.max(high[glo]))
        or_low = float(np.min(low[glo]))
        R = or_high - or_low
        if not (np.isfinite(R) and R > 0):
            funnel["n_or_incomplete"] += 1
            continue
        or_mid = 0.5 * (or_high + or_low)
        funnel["n_or_ok"] += 1

        # search first break
        search_mask = (ny_s >= or_end) & (ny_s < search_end)
        search_loc = np.flatnonzero(search_mask)
        found = False
        t_event = -1
        break_dir = 0
        for loc in search_loc:
            g = i0 + loc
            if not eligible[g]:
                continue
            # continuity from OR end: require same segment as OR
            if seg[g] != or_seg[0]:
                continue
            c = close[g]
            up = c > or_high
            dn = c < or_low
            if not (up or dn):
                continue
            # onset: prior close not already outside same side
            if g == 0 or session[g] != session[g - 1] or seg[g] != seg[g - 1] or ny[g] != ny[g - 1] + 1:
                continue
            prev_c = close[g - 1]
            if up and dn:
                # gap through both — prefer close vs mid
                if c >= or_mid:
                    if prev_c > or_high:
                        continue
                    break_dir = 1
                else:
                    if prev_c < or_low:
                        continue
                    break_dir = -1
            elif up:
                if prev_c > or_high:
                    continue
                break_dir = 1
            else:
                if prev_c < or_low:
                    continue
                break_dir = -1
            t_event = g
            found = True
            break

        if not found:
            funnel["n_no_break"] += 1
            continue

        funnel["n_events"] += 1
        if break_dir > 0:
            target = or_high + TARGET_R_MULT * R
            adverse = or_mid
        else:
            target = or_low - TARGET_R_MULT * R
            adverse = or_mid

        rows.append(
            {
                "event_id": f"{session[t_event]}_{int(ny[t_event])}",
                "event_idx": int(t_event),
                "break_dir": int(break_dir),
                "OR_high": or_high,
                "OR_low": or_low,
                "OR_mid": or_mid,
                "R": R,
                "target": float(target),
                "adverse": float(adverse),
                "split": split[t_event],
                "session_date": session[t_event],
                "session_year": int(year[t_event]),
                "ny_min": int(ny[t_event]),
            }
        )

    return pd.DataFrame(rows), funnel


def measure_first_passage(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    open_ = panel["open"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    n = len(panel)

    rows = []
    for ev in events.itertuples(index=False):
        t = int(ev.event_idx)
        d = int(ev.break_dir)
        target = float(ev.target)
        adverse = float(ev.adverse)
        R = float(ev.R)
        c0 = float(close[t])

        outcome = "unresolved"
        t_resolve = None
        exit_px = None
        mae = np.nan
        max_fav = 0.0
        max_adv = 0.0

        for j in range(1, H_CAP + 1):
            if not _fwd_ok(session, seg, ny, t, j):
                break
            tj = t + j
            hi = high[tj]
            lo = low[tj]
            if d > 0:
                hit_t = hi >= target
                hit_a = lo <= adverse
                fav = hi - c0
                adv = c0 - lo
            else:
                hit_t = lo <= target
                hit_a = hi >= adverse
                fav = c0 - lo
                adv = hi - c0
            max_fav = max(max_fav, float(fav))
            max_adv = max(max_adv, float(adv))

            if hit_t and hit_a:
                outcome = "adverse_first"  # conservative same-bar
                t_resolve = j
                exit_px = float(adverse)
                mae = max_adv
                break
            if hit_a:
                outcome = "adverse_first"
                t_resolve = j
                exit_px = float(adverse)
                mae = max_adv
                break
            if hit_t:
                outcome = "target_first"
                t_resolve = j
                exit_px = float(target)
                mae = max_adv  # MAE accumulated before/at target bar
                break

        if outcome == "unresolved":
            # time stop at last valid bar within H_cap
            last_j = 0
            for j in range(1, H_CAP + 1):
                if _fwd_ok(session, seg, ny, t, j):
                    last_j = j
                else:
                    break
            if last_j > 0:
                exit_px = float(close[t + last_j])
                t_resolve = last_j
                mae = max_adv

        rows.append(
            {
                "event_id": ev.event_id,
                "split": ev.split,
                "break_dir": d,
                "R": R,
                "outcome": outcome,
                "hit_target_first": outcome == "target_first",
                "hit_adverse_first": outcome == "adverse_first",
                "unresolved": outcome == "unresolved",
                "bars_to_resolve": t_resolve if t_resolve is not None else pd.NA,
                "mae_before_resolve": float(mae) if np.isfinite(mae) else np.nan,
                "mae_over_R": float(mae / R) if np.isfinite(mae) and R > 0 else np.nan,
                "mfe_before_resolve": float(max_fav),
                "c0": c0,
                "exit_px_barrier": exit_px if exit_px is not None else np.nan,
                "session_year": int(ev.session_year),
                "event_idx": t,
            }
        )
    return pd.DataFrame(rows)


def summarize_first_passage(fp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        g = fp if split == "ALL" else fp.loc[fp["split"] == split]
        n = len(g)
        if n == 0:
            rows.append(
                {
                    "split": split,
                    "n": 0,
                    "p_target_first": np.nan,
                    "p_adverse_first": np.nan,
                    "p_unresolved": np.nan,
                    "delta_fp": np.nan,
                }
            )
            continue
        p_t = float(g["hit_target_first"].mean())
        p_a = float(g["hit_adverse_first"].mean())
        p_u = float(g["unresolved"].mean())
        rows.append(
            {
                "split": split,
                "n": n,
                "p_target_first": p_t,
                "p_adverse_first": p_a,
                "p_unresolved": p_u,
                "delta_fp": p_t - p_a,
            }
        )
    return pd.DataFrame(rows)


def classify_step1(summary: pd.DataFrame) -> dict:
    def row(split: str):
        m = summary.loc[summary["split"] == split]
        return None if m.empty else m.iloc[0]

    detail = {}
    for split in ("IS", "Validation", "OOS"):
        r = row(split)
        if r is None:
            detail[split] = {"ok": False}
            continue
        detail[split] = {
            "n": int(r["n"]),
            "p_target_first": float(r["p_target_first"]),
            "p_adverse_first": float(r["p_adverse_first"]),
            "p_unresolved": float(r["p_unresolved"]),
            "delta_fp": float(r["delta_fp"]),
        }

    is_r = row("IS")
    if is_r is None or int(is_r["n"]) < MIN_IS:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "IS_sample",
            "detail": detail,
            "advance": False,
        }
    p_t = float(is_r["p_target_first"])
    d_fp = float(is_r["delta_fp"])
    if p_t < P_TARGET_IS or d_fp < DELTA_FP_IS:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "IS_first_passage",
            "detail": detail,
            "advance": False,
        }

    val_r = row("Validation")
    if val_r is None or int(val_r["n"]) < MIN_VAL:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "VAL_sample",
            "detail": detail,
            "advance": False,
        }
    if (
        float(val_r["p_target_first"]) < P_TARGET_VAL
        or float(val_r["delta_fp"]) < DELTA_FP_VAL
        or float(val_r["delta_fp"]) <= 0
    ):
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "VAL_first_passage",
            "detail": detail,
            "advance": False,
        }

    oos_r = row("OOS")
    if oos_r is None or int(oos_r["n"]) < MIN_OOS:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "OOS_sample",
            "detail": detail,
            "advance": False,
        }
    if float(oos_r["delta_fp"]) <= 0 or float(oos_r["p_target_first"]) < P_TARGET_OOS:
        return {
            "classification": "KILL",
            "stage": "STEP1",
            "reason": "OOS_first_passage",
            "detail": detail,
            "advance": False,
        }

    return {
        "classification": "ADVANCE_TO_MAE",
        "stage": "STEP1",
        "reason": "IS_VAL_OOS_first_passage_ok",
        "detail": detail,
        "advance": True,
    }


def summarize_mae(fp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        g = fp.loc[fp["hit_target_first"]]
        if split != "ALL":
            g = g.loc[g["split"] == split]
        n = len(g)
        if n == 0:
            rows.append(
                {
                    "split": split,
                    "n_target_first": 0,
                    "med_mae": np.nan,
                    "med_mae_over_R": np.nan,
                    "p75_mae": np.nan,
                    "pass_mae_r": False,
                    "pass_mae_pts": False,
                }
            )
            continue
        mae = g["mae_before_resolve"].to_numpy(np.float64)
        mae_r = g["mae_over_R"].to_numpy(np.float64)
        med_mae = float(np.nanmedian(mae))
        med_r = float(np.nanmedian(mae_r))
        rows.append(
            {
                "split": split,
                "n_target_first": n,
                "med_mae": med_mae,
                "med_mae_over_R": med_r,
                "p75_mae": float(np.nanpercentile(mae, 75)),
                "pass_mae_r": bool(med_r <= MAE_R_FRAC),
                "pass_mae_pts": bool(med_mae <= MAE_PTS_MAX),
            }
        )
    return pd.DataFrame(rows)


def classify_step2(mae_sum: pd.DataFrame, fp: pd.DataFrame) -> dict:
    detail = {}
    mins = {"IS": MIN_IS, "Validation": MIN_VAL, "OOS": MIN_OOS}
    # prereg: n_hit_target_first meets same min-n as Step 1
    ok_all = True
    reasons = []
    for split, min_n in mins.items():
        r = mae_sum.loc[mae_sum["split"] == split]
        if r.empty:
            detail[split] = {"ok": False}
            ok_all = False
            reasons.append(f"{split}_missing")
            continue
        row = r.iloc[0]
        n_ok = int(row["n_target_first"]) >= min_n
        # Also need enough target-first relative to events — use absolute min_n
        passed = (
            n_ok
            and bool(row["pass_mae_r"])
            and bool(row["pass_mae_pts"])
        )
        detail[split] = {
            "n_target_first": int(row["n_target_first"]),
            "med_mae": float(row["med_mae"]),
            "med_mae_over_R": float(row["med_mae_over_R"]),
            "pass_mae_r": bool(row["pass_mae_r"]),
            "pass_mae_pts": bool(row["pass_mae_pts"]),
            "n_ok": n_ok,
            "pass": passed,
        }
        if not passed:
            ok_all = False
            reasons.append(f"{split}_mae")

    if not ok_all:
        return {
            "classification": "KILL",
            "stage": "STEP2",
            "reason": "+".join(reasons) if reasons else "MAE_fail",
            "detail": detail,
            "advance": False,
        }
    return {
        "classification": "ADVANCE_TO_TRADE",
        "stage": "STEP2",
        "reason": "IS_VAL_OOS_mae_ok",
        "detail": detail,
        "advance": True,
    }


def summarize_time(fp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        for outcome in ("target_first", "adverse_first", "unresolved"):
            g = fp.loc[fp["outcome"] == outcome]
            if split != "ALL":
                g = g.loc[g["split"] == split]
            bars = pd.to_numeric(g["bars_to_resolve"], errors="coerce")
            rows.append(
                {
                    "split": split,
                    "outcome": outcome,
                    "n": int(len(g)),
                    "med_bars": float(bars.median()) if len(bars) else np.nan,
                    "p25": float(bars.quantile(0.25)) if len(bars) else np.nan,
                    "p75": float(bars.quantile(0.75)) if len(bars) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def run_trade(panel: pd.DataFrame, events: pd.DataFrame, fp: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    open_ = panel["open"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    session = panel["session_date"].to_numpy()
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    _ = fp  # fp reserved for future join; trade path recomputed from barriers

    rows = []
    for ev in events.itertuples(index=False):
        t = int(ev.event_idx)
        d = int(ev.break_dir)
        target = float(ev.target)
        adverse = float(ev.adverse)
        if not _fwd_ok(session, seg, ny, t, 1):
            continue
        entry_i = t + 1
        entry = float(open_[entry_i])

        exit_px = None
        exit_reason = "time"
        for j in range(1, H_CAP + 1):
            if not _fwd_ok(session, seg, ny, t, j):
                break
            tj = t + j
            hi = high[tj]
            lo = low[tj]
            if d > 0:
                hit_t = hi >= target
                hit_a = lo <= adverse
            else:
                hit_t = lo <= target
                hit_a = hi >= adverse
            if hit_t and hit_a:
                exit_px = adverse
                exit_reason = "adverse"
                break
            if hit_a:
                exit_px = adverse
                exit_reason = "adverse"
                break
            if hit_t:
                exit_px = target
                exit_reason = "target"
                break
        if exit_px is None:
            last_j = 0
            for j in range(1, H_CAP + 1):
                if _fwd_ok(session, seg, ny, t, j):
                    last_j = j
                else:
                    break
            if last_j == 0:
                continue
            exit_px = float(close[t + last_j])
            exit_reason = "time"

        gross = d * (float(exit_px) - entry)
        net = gross - COST_RT
        rows.append(
            {
                "event_id": ev.event_id,
                "split": ev.split,
                "break_dir": d,
                "gross": gross,
                "net": net,
                "exit_reason": exit_reason,
            }
        )
    trades = pd.DataFrame(rows)
    sum_rows = []
    for split in ("IS", "Validation", "OOS", "ALL"):
        g = trades if split == "ALL" else trades.loc[trades["split"] == split]
        n_t = len(g)
        if n_t == 0:
            sum_rows.append(
                {
                    "split": split,
                    "n_trades": 0,
                    "mean_gross": np.nan,
                    "mean_net": np.nan,
                    "median_net": np.nan,
                    "hit_rate": np.nan,
                    "eligible": False,
                }
            )
            continue
        sum_rows.append(
            {
                "split": split,
                "n_trades": n_t,
                "mean_gross": float(g["gross"].mean()),
                "mean_net": float(g["net"].mean()),
                "median_net": float(g["net"].median()),
                "hit_rate": float((g["net"] > 0).mean()),
                "eligible": n_t >= MIN_TRADES_SPLIT,
            }
        )
    return trades, pd.DataFrame(sum_rows)


def classify_trade(trade_summary: pd.DataFrame) -> dict:
    detail = {}
    ok = True
    for split in ("IS", "Validation", "OOS"):
        r = trade_summary.loc[trade_summary["split"] == split]
        if r.empty:
            detail[split] = {"pass": False}
            ok = False
            continue
        row = r.iloc[0]
        passed = bool(row["eligible"]) and float(row["mean_net"]) > 0
        detail[split] = {
            "n_trades": int(row["n_trades"]),
            "mean_net": float(row["mean_net"]),
            "pass": passed,
        }
        ok = ok and passed
    return {
        "classification": "ADVANCE" if ok else "KILL",
        "stage": "TRADE",
        "detail": detail,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading panel...", flush=True)
    panel = load_panel()
    print(f"panel={len(panel)}", flush=True)

    print("Extracting ORB events...", flush=True)
    events, funnel = extract_events(panel)
    events.to_parquet(RESULTS / "orb_events.parquet", index=False)
    (RESULTS / "funnel.json").write_text(json.dumps(funnel, indent=2), encoding="utf-8")
    print(json.dumps(funnel, indent=2), flush=True)

    print("First-passage...", flush=True)
    fp = measure_first_passage(panel, events)
    fp.to_parquet(RESULTS / "first_passage_paths.parquet", index=False)
    fp_sum = summarize_first_passage(fp)
    fp_sum.to_csv(RESULTS / "first_passage_by_split.csv", index=False)

    step1 = classify_step1(fp_sum)
    verdict: dict = {
        "step1": step1,
        "step2": None,
        "trade": None,
        "final": step1["classification"],
    }

    # always write time descriptive
    summarize_time(fp).to_csv(RESULTS / "time_to_resolve.csv", index=False)

    if step1.get("advance"):
        print("MAE before target...", flush=True)
        mae_sum = summarize_mae(fp)
        mae_sum.to_csv(RESULTS / "mae_before_target_by_split.csv", index=False)
        step2 = classify_step2(mae_sum, fp)
        verdict["step2"] = step2
        verdict["final"] = step2["classification"]

        if step2.get("advance"):
            print("Trade...", flush=True)
            trades, trade_sum = run_trade(panel, events, fp)
            trades.to_parquet(RESULTS / "trades.parquet", index=False)
            trade_sum.to_csv(RESULTS / "trade_summary.csv", index=False)
            trade_v = classify_trade(trade_sum)
            verdict["trade"] = trade_v
            verdict["final"] = (
                "ADVANCE" if trade_v["classification"] == "ADVANCE" else "KILL_AFTER_TRADE"
            )
    else:
        # still write MAE descriptive for report completeness? prereg says only if step1 advance
        # write empty/skip — report handles
        pass

    (RESULTS / "verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "step1": step1.get("classification"),
                "step2": (verdict["step2"] or {}).get("classification"),
                "trade": (verdict["trade"] or {}).get("classification"),
                "final": verdict["final"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
