"""Frozen continuation P&L concentration / winner-outlier audit (Phase 20)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
ART = ROOT / "artifacts" / "30_initial_balance_breakout"


def pf(values: pd.Series) -> float:
    wins, losses = values[values > 0].sum(), values[values < 0].sum()
    return wins / abs(losses) if losses else np.nan


def concentration(x: pd.DataFrame, value: str) -> dict:
    values = x[value].sort_values(ascending=False).reset_index(drop=True)
    total = values.sum()
    winners = values[values > 0]
    row = {
        "split": x.split.iloc[0], "unit": value, "n": len(x), "total": total,
        "mean": values.mean(), "median": values.median(), "pf": pf(values),
    }
    for k in (1, 3, 5, 10):
        top = winners.head(k).sum()
        rest = values.iloc[k:]  # winners lead this descending series
        row[f"top_{k}_contribution"] = top / total if total else np.nan
        row[f"after_top_{k}_total"] = rest.sum()
        row[f"after_top_{k}_mean"] = rest.mean()
        row[f"after_top_{k}_pf"] = pf(rest)
    for threshold in (.50, .75, .90):
        target = total * threshold
        row[f"winners_for_{int(threshold*100)}pct"] = (
            int((winners.cumsum() < target).sum() + 1) if total > 0 and len(winners) else np.nan
        )
    return row


def main() -> None:
    d = pd.read_csv(ART / "nq_phase19_candidate_trades.csv")
    d["net_r"] = d.net_points / d.risk_points
    d["ib_width"] = 2 * d.risk_points
    extreme_cut = d.loc[d.split.eq("IS"), "width_vs20"].quantile(.9)
    d["extreme_open_range"] = d.width_vs20.ge(extreme_cut)
    summary = pd.DataFrame(
        concentration(x, unit)
        for _, x in d.groupby("split", sort=False)
        for unit in ("net_points", "net_r")
    )
    summary.to_csv(ART / "nq_phase20_pnl_concentration.csv", index=False)

    cols = ["split", "session_date", "year", "net_points", "net_r", "risk_points", "ib_width",
            "width_vs20", "extreme_open_range", "open_macro", "exit_kind"]
    largest = pd.concat(
        [x.nlargest(10, "net_points") for _, x in d.groupby("split", sort=False)], ignore_index=True
    )[cols].sort_values(["split", "net_points"], ascending=[True, False])
    largest.to_csv(ART / "nq_phase20_largest_winners.csv", index=False)

    md = [
        "# Phase 20 — frozen continuation P&L concentration audit",
        "",
        "The strategy is unchanged: high-volume + early IB breakout, 0.50× IB-width stop, 2R target, 1 point round-trip costs. `top_k_contribution` is the share of total net P&L supplied by the largest k winning trades. Removal removes those top k winners only.",
        "",
        "## Concentration summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Ten largest point winners per period",
        "",
        largest.to_markdown(index=False),
    ]
    (ART / "nq_phase20_pnl_concentration_report.md").write_text("\n".join(md), encoding="utf-8")
    print(summary.to_string(index=False))
    print("\nLargest winners:\n", largest.to_string(index=False))


if __name__ == "__main__":
    main()
