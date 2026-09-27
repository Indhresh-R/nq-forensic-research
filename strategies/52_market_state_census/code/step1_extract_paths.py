"""
Step 1 — extract four-cell episode onsets and measure forward path geometry.

No trades. No P&L. Horizons use strictly subsequent bars only.
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
    DIR_HIGH,
    DIR_LOW,
    DIR_MID,
    RESULTS,
    RNG_COMP,
    RNG_EXP,
    RNG_MID,
)
from step1_constants import (
    CELL_A,
    CELL_B,
    CELL_C,
    CELL_D,
    CELLS,
    HORIZONS,
)

# Integer codes for fast path scans
R_COMP, R_MID, R_EXP, R_OTHER = 0, 1, 2, -1
D_LOW, D_MID, D_HIGH, D_OTHER = 0, 1, 2, -1
CELL_CODE = {CELL_A: 0, CELL_B: 1, CELL_C: 2, CELL_D: 3}
CELL_NAME = {0: CELL_A, 1: CELL_B, 2: CELL_C, 3: CELL_D}


def _range_code(s: np.ndarray) -> np.ndarray:
    out = np.full(len(s), R_OTHER, dtype=np.int8)
    out[s == RNG_COMP] = R_COMP
    out[s == RNG_MID] = R_MID
    out[s == RNG_EXP] = R_EXP
    return out


def _dir_code(s: np.ndarray) -> np.ndarray:
    out = np.full(len(s), D_OTHER, dtype=np.int8)
    out[s == DIR_LOW] = D_LOW
    out[s == DIR_MID] = D_MID
    out[s == DIR_HIGH] = D_HIGH
    return out


def assign_cell_code(range_c: np.ndarray, dir_c: np.ndarray) -> np.ndarray:
    """Return cell code 0..3 or -1 if outside A–D."""
    out = np.full(len(range_c), -1, dtype=np.int8)
    comp = range_c == R_COMP
    exp = range_c == R_EXP
    out[comp & (dir_c == D_LOW)] = 0  # A
    out[comp & ((dir_c == D_MID) | (dir_c == D_HIGH))] = 1  # B
    out[exp & (dir_c == D_HIGH)] = 2  # C
    out[exp & (dir_c == D_LOW)] = 3  # D
    return out


def build_panel() -> pd.DataFrame:
    states = pd.read_parquet(RESULTS / "market_states.parquet")
    feats = pd.read_parquet(
        RESULTS / "market_state_features.parquet",
        columns=["ts", "high", "low", "close"],
    )
    if len(states) != len(feats):
        raise RuntimeError("market_states and features row counts differ")
    panel = states.copy()
    panel["high"] = feats["high"].to_numpy(np.float64)
    panel["low"] = feats["low"].to_numpy(np.float64)
    panel = (
        panel.loc[panel["census_eligible"]]
        .sort_values(["session_date", "ny_min"])
        .reset_index(drop=True)
    )
    return panel


def extract_episodes(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    n = len(panel)
    range_c = _range_code(panel["range_state"].to_numpy(dtype=object))
    dir_c = _dir_code(panel["directionality_state"].to_numpy(dtype=object))
    cell_c = assign_cell_code(range_c, dir_c)

    session = panel["session_date"].to_numpy()
    # onset when session changes OR cell code changes
    onset = np.empty(n, dtype=bool)
    onset[0] = True
    onset[1:] = (session[1:] != session[:-1]) | (cell_c[1:] != cell_c[:-1])

    mask = onset & (cell_c >= 0)
    idx = np.flatnonzero(mask)

    years = panel["session_year"].to_numpy(np.int16)
    episodes = pd.DataFrame(
        {
            "episode_id": [
                f"{session[i]}_{int(panel['ny_min'].iloc[i])}_{CELL_NAME[int(cell_c[i])]}"
                for i in idx
            ],
            "session_date": session[idx],
            "session_year": years[idx],
            "split": [split_of(int(y)) for y in years[idx]],
            "ts": panel["ts"].to_numpy()[idx],
            "ny_min": panel["ny_min"].to_numpy(np.int16)[idx],
            "dow": panel["dow"].to_numpy(np.int8)[idx],
            "segment_id": panel["segment_id"].to_numpy(np.int64)[idx],
            "cell": [CELL_NAME[int(cell_c[i])] for i in idx],
            "cell_code": cell_c[idx].astype(np.int8),
            "panel_idx": idx.astype(np.int64),
            "close0": panel["close"].to_numpy(np.float64)[idx],
            "atr0": panel["atr_30"].to_numpy(np.float64)[idx],
            "er60_0": panel["er_60"].to_numpy(np.float64)[idx],
            "range_state0": panel["range_state"].to_numpy(dtype=object)[idx],
            "dir_state0": panel["directionality_state"].to_numpy(dtype=object)[idx],
        }
    )

    meta = {
        "n_eligible_bars": int(n),
        "n_bars_in_four_cells": int((cell_c >= 0).sum()),
        "n_bars_residual": int((cell_c < 0).sum()),
        "n_episodes": int(len(episodes)),
        "episodes_by_cell": episodes["cell"].value_counts().to_dict(),
    }
    return episodes, meta, range_c, dir_c


def compute_path_metrics(
    panel: pd.DataFrame,
    episodes: pd.DataFrame,
    range_c: np.ndarray,
    dir_c: np.ndarray,
) -> pd.DataFrame:
    high = panel["high"].to_numpy(np.float64)
    low = panel["low"].to_numpy(np.float64)
    close = panel["close"].to_numpy(np.float64)
    ny = panel["ny_min"].to_numpy(np.int16)
    seg = panel["segment_id"].to_numpy(np.int64)
    session = panel["session_date"].to_numpy()
    n = len(panel)

    i0s = episodes["panel_idx"].to_numpy(np.int64)
    cells = episodes["cell"].to_numpy(dtype=object)
    years = episodes["session_year"].to_numpy(np.int16)
    splits = episodes["split"].to_numpy(dtype=object)
    ep_ids = episodes["episode_id"].to_numpy(dtype=object)
    close0 = episodes["close0"].to_numpy(np.float64)
    atr0 = episodes["atr0"].to_numpy(np.float64)
    n_ep = len(episodes)

    records: list[dict] = []

    for h in HORIZONS:
        print(f"  horizon {h}…", flush=True)
        for k in range(n_ep):
            i0 = int(i0s[k])
            i1 = i0 + h
            c0 = close0[k]
            a0 = atr0[k]
            atr_ok = np.isfinite(a0) and a0 > 0

            valid = (
                i1 < n
                and session[i1] == session[i0]
                and seg[i1] == seg[i0]
                and bool(np.all(np.diff(ny[i0 : i1 + 1]) == 1))
            )
            rec = {
                "episode_id": ep_ids[k],
                "cell": cells[k],
                "session_year": int(years[k]),
                "split": splits[k],
                "horizon": h,
                "valid": bool(valid),
            }
            if not valid:
                records.append(rec)
                continue

            sl = slice(i0 + 1, i1 + 1)
            hi = high[sl]
            lo = low[sl]
            cl = close[sl]
            rs = range_c[sl]
            ds = dir_c[sl]

            prev = np.empty(h, dtype=np.float64)
            prev[0] = c0
            if h > 1:
                prev[1:] = cl[:-1]
            abs_path = float(np.sum(np.abs(cl - prev)))
            net = float(cl[-1] - c0)
            max_up = float(hi.max() - c0)
            max_down = float(c0 - lo.min())
            max_range = float(hi.max() - lo.min())
            er_fwd = abs(net) / abs_path if abs_path > 0 else np.nan

            # first-hit times
            is_mid = rs == R_MID
            is_exp = rs == R_EXP
            not_comp = rs != R_COMP
            not_exp = rs != R_EXP

            def first_true(mask: np.ndarray) -> float:
                w = np.flatnonzero(mask)
                return float(w[0] + 1) if len(w) else np.nan

            time_to_normal = first_true(is_mid)
            time_to_exp = first_true(is_exp)
            time_to_leave_comp = first_true(not_comp)
            time_to_leave_exp = first_true(not_exp)

            exp_dir = np.nan
            exp_two = np.nan
            if np.isfinite(time_to_exp):
                j = int(time_to_exp) - 1
                exp_dir = 1.0 if ds[j] == D_HIGH else 0.0
                exp_two = 1.0 if ds[j] == D_LOW else 0.0

            terminal_r = int(rs[-1])
            cell_name = cells[k]
            left_expansion = (
                bool(np.any(not_exp)) if cell_name in (CELL_C, CELL_D) else np.nan
            )
            rec.update(
                {
                    "net_move": net,
                    "abs_net": abs(net),
                    "abs_net_atr": abs(net) / a0 if atr_ok else np.nan,
                    "max_up": max_up,
                    "max_down": max_down,
                    "max_up_atr": max_up / a0 if atr_ok else np.nan,
                    "max_down_atr": max_down / a0 if atr_ok else np.nan,
                    "max_range": max_range,
                    "max_range_atr": max_range / a0 if atr_ok else np.nan,
                    "er_forward": er_fwd,
                    "still_compressed": bool(terminal_r == R_COMP),
                    "still_expanded": bool(terminal_r == R_EXP),
                    "reached_normal": bool(np.any(is_mid)),
                    "reached_expansion": bool(np.any(is_exp)),
                    "left_expansion": left_expansion,
                    "time_to_normal": time_to_normal,
                    "time_to_expansion": time_to_exp,
                    "time_to_leave_compression": time_to_leave_comp,
                    "time_to_leave_expansion": time_to_leave_exp,
                    "expansion_is_directional": exp_dir,
                    "expansion_is_two_sided": exp_two,
                    "p_terminal_normal": float(terminal_r == R_MID),
                    "p_terminal_expansion": float(terminal_r == R_EXP),
                    "p_terminal_compression": float(terminal_r == R_COMP),
                }
            )
            records.append(rec)

    return pd.DataFrame(records)


def main() -> None:
    print("Building eligible panel…", flush=True)
    panel = build_panel()
    print(f"panel rows={len(panel):,}", flush=True)

    print("Extracting episodes…", flush=True)
    episodes, meta, range_c, dir_c = extract_episodes(panel)
    print(f"episodes={len(episodes):,} by_cell={meta['episodes_by_cell']}", flush=True)
    episodes.to_parquet(RESULTS / "step1_episodes.parquet", index=False)
    (RESULTS / "step1_episode_meta.json").write_text(
        json.dumps(meta, indent=2, default=str), encoding="utf-8"
    )

    print("Computing path metrics…", flush=True)
    metrics = compute_path_metrics(panel, episodes, range_c, dir_c)
    metrics.to_parquet(RESULTS / "step1_path_metrics.parquet", index=False)
    print(f"metric rows={len(metrics):,} valid={int(metrics['valid'].sum()):,}", flush=True)


if __name__ == "__main__":
    main()
