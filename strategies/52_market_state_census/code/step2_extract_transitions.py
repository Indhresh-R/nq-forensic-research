"""
Step 2 — first causal origin→NORMAL transition after episode onset + path geometry.

No trades. Event definition does not use post-event information.
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

from constants import RESULTS
from step1_constants import CELL_A, CELL_B, CELL_C, CELL_D, HORIZONS
from step1_extract_paths import (
    R_COMP,
    R_EXP,
    R_MID,
    D_HIGH,
    D_LOW,
    _dir_code,
    _range_code,
    assign_cell_code,
    build_panel,
)
from step2_constants import (
    CENSOR_CELL_SWITCH,
    CENSOR_EVENT,
    CENSOR_NO_NORMAL,
    CENSOR_OPPOSITE_RANGE,
    CENSOR_SESSION_END,
    FAMILY_COMP_EXIT,
    FAMILY_EXP_EXIT,
    ORIGIN_COMP,
    ORIGIN_EXP,
)


def _family_and_origin_range(cell: str) -> tuple[str, int, int]:
    """Return (family, origin_range_code, opposite_range_code)."""
    if cell in ORIGIN_COMP:
        return FAMILY_COMP_EXIT, R_COMP, R_EXP
    if cell in ORIGIN_EXP:
        return FAMILY_EXP_EXIT, R_EXP, R_COMP
    raise ValueError(cell)


def find_transition_events(
    panel: pd.DataFrame, episodes: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    range_c = _range_code(panel["range_state"].to_numpy(dtype=object))
    dir_c = _dir_code(panel["directionality_state"].to_numpy(dtype=object))
    cell_c = assign_cell_code(range_c, dir_c)

    ny = panel["ny_min"].to_numpy(np.int16)
    seg = panel["segment_id"].to_numpy(np.int64)
    session = panel["session_date"].to_numpy()
    close = panel["close"].to_numpy(np.float64)
    atr = panel["atr_30"].to_numpy(np.float64)
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    n = len(panel)

    # Map cell name -> code for switch detection
    name_to_code = {CELL_A: 0, CELL_B: 1, CELL_C: 2, CELL_D: 3}

    events = []
    funnel = {
        "n_onsets": int(len(episodes)),
        "n_events": 0,
        "censored": {
            CENSOR_SESSION_END: 0,
            CENSOR_OPPOSITE_RANGE: 0,
            CENSOR_CELL_SWITCH: 0,
            CENSOR_NO_NORMAL: 0,
        },
        "events_by_origin": {CELL_A: 0, CELL_B: 0, CELL_C: 0, CELL_D: 0},
        "censored_by_origin": {
            CELL_A: 0,
            CELL_B: 0,
            CELL_C: 0,
            CELL_D: 0,
        },
    }

    i0s = episodes["panel_idx"].to_numpy(np.int64)
    cells = episodes["cell"].to_numpy(dtype=object)
    ep_ids = episodes["episode_id"].to_numpy(dtype=object)
    years = episodes["session_year"].to_numpy(np.int16)

    for k in range(len(episodes)):
        i0 = int(i0s[k])
        cell = str(cells[k])
        origin_code = name_to_code[cell]
        family, origin_r, opposite_r = _family_and_origin_range(cell)

        te = -1
        reason = CENSOR_NO_NORMAL
        i = i0
        while True:
            j = i + 1
            if j >= n:
                reason = CENSOR_SESSION_END
                break
            if session[j] != session[i0] or seg[j] != seg[i0] or ny[j] != ny[i] + 1:
                reason = CENSOR_SESSION_END
                break

            rc = int(range_c[j])
            cc = int(cell_c[j])

            if rc == R_MID:
                te = j
                reason = CENSOR_EVENT
                break
            if rc == opposite_r:
                reason = CENSOR_OPPOSITE_RANGE
                break
            if cc >= 0 and cc != origin_code:
                # switched to a different A/B/C/D cell before NORMAL
                reason = CENSOR_CELL_SWITCH
                break
            # still in origin range (and typically same cell); continue
            if rc != origin_r:
                # unexpected residual range (e.g. OTHER) — treat as abort
                reason = CENSOR_OPPOSITE_RANGE
                break
            i = j

        if reason != CENSOR_EVENT:
            funnel["censored"][reason] = funnel["censored"].get(reason, 0) + 1
            funnel["censored_by_origin"][cell] += 1
            continue

        funnel["n_events"] += 1
        funnel["events_by_origin"][cell] += 1
        wait = int(te - i0)
        events.append(
            {
                "event_id": f"{ep_ids[k]}_to_NORMAL_{int(ny[te])}",
                "episode_id": ep_ids[k],
                "family": family,
                "origin_cell": cell,
                "session_date": session[te],
                "session_year": int(years[k]),
                "split": split_of(int(years[k])),
                "onset_panel_idx": i0,
                "event_panel_idx": int(te),
                "onset_ny_min": int(ny[i0]),
                "event_ny_min": int(ny[te]),
                "wait_to_event": wait,
                "close_e": float(close[te]),
                "atr_e": float(atr[te]),
                "high_e": float(high[te]),
                "low_e": float(low[te]),
                "dir_at_event": int(dir_c[te]),
                "segment_id": int(seg[te]),
            }
        )

    ev = pd.DataFrame(events)
    return ev, funnel


def compute_event_paths(
    panel: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    range_c = _range_code(panel["range_state"].to_numpy(dtype=object))
    dir_c = _dir_code(panel["directionality_state"].to_numpy(dtype=object))
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    ny = panel["ny_min"].to_numpy(np.int16)
    seg = panel["segment_id"].to_numpy(np.int64)
    session = panel["session_date"].to_numpy()
    n = len(panel)

    records: list[dict] = []
    for ev in events.itertuples(index=False):
        te = int(ev.event_panel_idx)
        c_e = float(ev.close_e)
        atr_e = float(ev.atr_e)
        atr_ok = np.isfinite(atr_e) and atr_e > 0
        origin = str(ev.origin_cell)
        family = str(ev.family)
        _, origin_r, opposite_r = _family_and_origin_range(origin)

        for h in HORIZONS:
            i1 = te + h
            valid = (
                i1 < n
                and session[i1] == session[te]
                and seg[i1] == seg[te]
                and bool(np.all(np.diff(ny[te : i1 + 1]) == 1))
            )
            rec = {
                "event_id": ev.event_id,
                "family": family,
                "origin_cell": origin,
                "session_year": int(ev.session_year),
                "split": ev.split,
                "wait_to_event": int(ev.wait_to_event),
                "horizon": h,
                "valid": bool(valid),
            }
            if not valid:
                records.append(rec)
                continue

            sl = slice(te + 1, i1 + 1)
            hi = high[sl]
            lo = low[sl]
            cl = close[sl]
            rs = range_c[sl]
            ds = dir_c[sl]

            prev = np.empty(h, dtype=np.float64)
            prev[0] = c_e
            if h > 1:
                prev[1:] = cl[:-1]
            abs_path = float(np.sum(np.abs(cl - prev)))
            net = float(cl[-1] - c_e)
            max_up = float(hi.max() - c_e)
            max_down = float(c_e - lo.min())
            max_range = float(hi.max() - lo.min())
            er_fwd = abs(net) / abs_path if abs_path > 0 else np.nan

            is_origin = rs == origin_r
            is_opp = rs == opposite_r
            is_norm = rs == R_MID
            not_norm = rs != R_MID

            def first_true(mask: np.ndarray) -> float:
                w = np.flatnonzero(mask)
                return float(w[0] + 1) if len(w) else np.nan

            terminal_r = int(rs[-1])
            terminal_d = int(ds[-1])

            rec.update(
                {
                    "net_move": net,
                    "abs_net": abs(net),
                    "abs_net_atr": abs(net) / atr_e if atr_ok else np.nan,
                    "max_up": max_up,
                    "max_down": max_down,
                    "max_up_atr": max_up / atr_e if atr_ok else np.nan,
                    "max_down_atr": max_down / atr_e if atr_ok else np.nan,
                    "max_range": max_range,
                    "max_range_atr": max_range / atr_e if atr_ok else np.nan,
                    "er_forward": er_fwd,
                    "still_normal": bool(terminal_r == R_MID),
                    "returned_to_origin_range": bool(np.any(is_origin)),
                    "reached_opposite_range": bool(np.any(is_opp)),
                    "time_to_leave_normal": first_true(not_norm),
                    "time_to_origin_range": first_true(is_origin),
                    "time_to_opposite_range": first_true(is_opp),
                    "terminal_dir_high": bool(terminal_d == D_HIGH),
                    "terminal_dir_low": bool(terminal_d == D_LOW),
                    "path_dir_high_share": float(np.mean(ds == D_HIGH)),
                    "path_dir_low_share": float(np.mean(ds == D_LOW)),
                    "p_terminal_normal": float(terminal_r == R_MID),
                    "p_terminal_origin": float(terminal_r == origin_r),
                    "p_terminal_opposite": float(terminal_r == opposite_r),
                }
            )
            records.append(rec)

    return pd.DataFrame(records)


def main() -> None:
    print("Loading panel + Step 1 episodes…", flush=True)
    panel = build_panel()
    episodes = pd.read_parquet(RESULTS / "step1_episodes.parquet")
    # safety: drop any residual null cells from older artifacts
    episodes = episodes.loc[episodes["cell"].isin([CELL_A, CELL_B, CELL_C, CELL_D])].copy()
    print(f"panel={len(panel):,} onsets={len(episodes):,}", flush=True)

    print("Finding first ->NORMAL transitions…", flush=True)
    events, funnel = find_transition_events(panel, episodes)
    print(f"events={len(events):,} funnel={funnel}", flush=True)
    events.to_parquet(RESULTS / "step2_events.parquet", index=False)
    (RESULTS / "step2_funnel.json").write_text(
        json.dumps(funnel, indent=2, default=str), encoding="utf-8"
    )

    print("Computing post-event paths…", flush=True)
    metrics = compute_event_paths(panel, events)
    metrics.to_parquet(RESULTS / "step2_path_metrics.parquet", index=False)
    print(
        f"metric rows={len(metrics):,} valid={int(metrics['valid'].sum()):,}",
        flush=True,
    )


if __name__ == "__main__":
    main()
