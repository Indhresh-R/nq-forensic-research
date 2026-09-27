"""Persistence and transition analysis for Strategy 52 (descriptive only)."""
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


STATE_COLS = (
    "directionality_state",
    "volatility_state",
    "volume_state",
    "range_state",
    "composite_primary",
)


def _episode_stats(states: np.ndarray, durations: np.ndarray) -> pd.DataFrame:
    rows = []
    for s in pd.unique(states):
        if s is None or (isinstance(s, float) and np.isnan(s)):
            continue
        d = durations[states == s]
        if len(d) == 0:
            continue
        rows.append(
            {
                "state": s,
                "n_episodes": int(len(d)),
                "median_duration_min": float(np.median(d)),
                "mean_duration_min": float(np.mean(d)),
                "p25_duration_min": float(np.quantile(d, 0.25)),
                "p75_duration_min": float(np.quantile(d, 0.75)),
                "max_duration_min": float(np.max(d)),
                "total_minutes": int(np.sum(d)),
            }
        )
    return pd.DataFrame(rows).sort_values("n_episodes", ascending=False)


def episodes_for_column(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Episode durations within each session_date (do not bridge overnight).
    Each consecutive run of the same label is one episode; duration in minutes.
    """
    e = df.loc[df["census_eligible"] & df[col].notna(), ["session_date", "ny_min", col]].copy()
    e = e.sort_values(["session_date", "ny_min"]).reset_index(drop=True)

    ep_states: list = []
    ep_durs: list[int] = []
    transitions: list[tuple] = []

    for _, g in e.groupby("session_date", sort=False):
        labels = g[col].to_numpy()
        if len(labels) == 0:
            continue
        # runs
        change = np.empty(len(labels), dtype=bool)
        change[0] = True
        change[1:] = labels[1:] != labels[:-1]
        run_ids = np.cumsum(change) - 1
        for rid in range(int(run_ids.max()) + 1):
            mask = run_ids == rid
            ep_states.append(labels[mask][0])
            ep_durs.append(int(mask.sum()))
        # bar-to-bar transitions (same session)
        for a, b in zip(labels[:-1], labels[1:]):
            transitions.append((a, b))

    stats = _episode_stats(np.array(ep_states, dtype=object), np.array(ep_durs, dtype=np.int64))
    if transitions:
        tr = pd.DataFrame(transitions, columns=["from_state", "to_state"])
        mat = (
            tr.groupby(["from_state", "to_state"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        totals = mat.groupby("from_state")["count"].transform("sum")
        mat["pct_of_from"] = 100.0 * mat["count"] / totals
    else:
        mat = pd.DataFrame(columns=["from_state", "to_state", "count", "pct_of_from"])
    stats.insert(0, "dimension", col)
    mat.insert(0, "dimension", col)
    return stats, mat


def compression_then_expansion(df: pd.DataFrame) -> dict:
    """
    Descriptive sequence fact: among range-state bar transitions,
    how often COMPRESSION is followed by EXPANSION (direct next bar),
    and how often a COMPRESSION episode is next followed by an EXPANSION episode.
    """
    e = df.loc[
        df["census_eligible"] & df["range_state"].notna(),
        ["session_date", "ny_min", "range_state"],
    ].sort_values(["session_date", "ny_min"])

    direct = 0
    from_comp = 0
    ep_comp = 0
    ep_comp_to_exp = 0

    for _, g in e.groupby("session_date", sort=False):
        labels = g["range_state"].to_numpy()
        for a, b in zip(labels[:-1], labels[1:]):
            if a == "COMPRESSION":
                from_comp += 1
                if b == "EXPANSION":
                    direct += 1
        change = np.empty(len(labels), dtype=bool)
        change[0] = True
        change[1:] = labels[1:] != labels[:-1]
        runs = labels[change]
        for a, b in zip(runs[:-1], runs[1:]):
            if a == "COMPRESSION":
                ep_comp += 1
                if b == "EXPANSION":
                    ep_comp_to_exp += 1

    return {
        "direct_bar_compression_to_expansion": direct,
        "direct_bar_from_compression": from_comp,
        "direct_pct": 100.0 * direct / from_comp if from_comp else None,
        "episode_compression_followed_by_expansion": ep_comp_to_exp,
        "episode_compression_count": ep_comp,
        "episode_pct": 100.0 * ep_comp_to_exp / ep_comp if ep_comp else None,
    }


def main() -> None:
    df = pd.read_parquet(RESULTS / "market_states.parquet")
    print(f"Loaded states rows={len(df):,}")

    all_stats = []
    all_trans = []
    for col in STATE_COLS:
        print(f"  episodes: {col}")
        stats, mat = episodes_for_column(df, col)
        all_stats.append(stats)
        all_trans.append(mat)

    stats_df = pd.concat(all_stats, ignore_index=True)
    trans_df = pd.concat(all_trans, ignore_index=True)
    stats_df.to_csv(RESULTS / "table8_persistence.csv", index=False)
    trans_df.to_csv(RESULTS / "table9_transitions.csv", index=False)

    # Wide transition matrices for key dimensions
    for col in ("composite_primary", "range_state", "directionality_state"):
        sub = trans_df[trans_df["dimension"] == col]
        if sub.empty:
            continue
        pivot = sub.pivot_table(
            index="from_state", columns="to_state", values="pct_of_from", aggfunc="sum"
        ).fillna(0.0)
        pivot.to_csv(RESULTS / f"transition_matrix_{col}.csv")

    cxe = compression_then_expansion(df)
    (RESULTS / "compression_expansion_sequences.json").write_text(
        json.dumps(cxe, indent=2), encoding="utf-8"
    )
    print("Persistence / transition tables written.")


if __name__ == "__main__":
    main()
