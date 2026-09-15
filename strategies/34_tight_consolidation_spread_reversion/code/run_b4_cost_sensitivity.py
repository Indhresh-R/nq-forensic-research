"""Post-registration cost-only diagnostic for the frozen B4 trade paths."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts" / "34_tight_consolidation_spread_reversion"
SOURCE = OUT / "all_candidate_trades.csv"
BASE_COST, STOP = 4.0, 150.0


def metrics(x: pd.DataFrame) -> dict:
    wins, losses = x[x.net_dollars > 0], x[x.net_dollars <= 0]
    n = len(x)
    payoff = wins.net_dollars.mean() / abs(losses.net_dollars.mean()) if len(wins) and len(losses) else np.nan
    return {
        "n": n,
        "net_dollars": float(x.net_dollars.sum()),
        "win_rate": len(wins) / n if n else np.nan,
        "payoff": float(payoff),
        "profit_factor": float(wins.net_dollars.sum() / abs(losses.net_dollars.sum())) if len(losses) else np.nan,
    }


def main() -> None:
    trades = pd.read_csv(SOURCE)
    b4 = trades[(trades.candidate == "B4_zmean_nearer_1p5R") & trades.period.isin(["Train", "Inner Validation"])].copy()
    # The source P&L is gross spread P&L less the frozen $4 combined cost.
    b4["gross_dollars"] = b4.net_dollars + BASE_COST
    rows = []
    for cost in (0.0, 2.0, 4.0):
        x = b4.copy(); x["net_dollars"] = x.gross_dollars - cost
        m = metrics(x)
        required = (1 + 1500 / (m["n"] * STOP)) / (m["payoff"] + 1)
        rows.append({"candidate": "B4_zmean_nearer_1p5R", "combined_round_trip_cost": cost,
                     "required_win_rate": required, "clears_feasibility": m["win_rate"] >= required, **m})
    result = pd.DataFrame(rows)
    result.to_csv(OUT / "b4_cost_sensitivity.csv", index=False)
    report = [
        "# B4 cost-sensitivity diagnostic",
        "",
        "This is a post-registration diagnostic, not a new candidate search or a re-selection. Entries, signals, targets, stops, and all trade paths are exactly those in the frozen B4 results. Only the combined round-trip cost is changed.",
        "",
        result.to_markdown(index=False),
        "",
        "The feasibility requirement is recalculated from each scenario's realized net payoff using the locked formula. This diagnostic cannot change the original Step 2 selection result.",
    ]
    (OUT / "B4_COST_SENSITIVITY.md").write_text("\n".join(report), encoding="utf-8")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
