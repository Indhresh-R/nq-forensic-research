"""Render actual OOS NQ baseline examples as TradingView-style charts."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from common.nq_session import load_nq  # noqa: E402

ART = ROOT / "artifacts" / "30_initial_balance_breakout"


def render(trade: pd.Series, out: Path) -> None:
    nq = load_nq()
    day = nq[(nq.session_date.astype(str) == str(trade.session_date)) & (nq.ny_min >= 570) & (nq.ny_min <= 959)].copy()
    # Five-minute visual bars, retaining 1m backtest levels/prices from `trade`.
    day["bucket"] = (day.ny_min - 570) // 5
    b = day.groupby("bucket", as_index=False).agg(
        ny_min=("ny_min", "first"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")
    )
    fig, ax = plt.subplots(figsize=(15, 8), facecolor="#131722")
    ax.set_facecolor("#131722")
    width = 0.72
    for i, r in b.iterrows():
        color = "#26a69a" if r.close >= r.open else "#ef5350"
        ax.vlines(i, r.low, r.high, color=color, linewidth=1)
        body_low, body_h = min(r.open, r.close), max(abs(r.close - r.open), 0.08)
        ax.add_patch(Rectangle((i - width / 2, body_low), width, body_h, facecolor=color, edgecolor=color))

    def x_for(minute: int) -> float:
        return float((minute - 570) / 5)
    x_entry, x_exit = x_for(int(trade.entry_ny_min)), x_for(int(trade.exit_ny_min))
    ax.axhspan(float(trade.stop), float(trade.target), xmin=x_entry / max(len(b) - 1, 1), xmax=x_exit / max(len(b) - 1, 1), color="#2962ff", alpha=0.07)
    ax.hlines(float(trade.entry), x_entry, x_exit, colors="#ffab00", linewidth=1.6, linestyles="--", label=f"Entry {trade.entry:.2f}")
    ax.hlines(float(trade.stop), x_entry, x_exit, colors="#ef5350", linewidth=1.6, linestyles="--", label=f"Stop {trade.stop:.2f}")
    ax.hlines(float(trade.target), x_entry, x_exit, colors="#26a69a", linewidth=1.6, linestyles="--", label=f"Target {trade.target:.2f}")
    ax.scatter(x_entry, float(trade.entry), s=90, marker="^" if trade.side == "long" else "v", color="#ffab00", zorder=5, label="Entry")
    exit_color = "#26a69a" if trade.net_points > 0 else "#ef5350"
    ax.scatter(x_exit, float(trade.exit), s=90, marker="o", color=exit_color, zorder=5, label=f"Exit ({trade.exit_kind})")
    ib_end = x_for(629)
    ax.axvspan(0, ib_end, color="#5c6bc0", alpha=0.12)
    ax.hlines([float(trade.ib_high), float(trade.ib_low)], 0, ib_end, colors="#8b95a5", linewidth=1, linestyles=":")
    ax.text(ib_end / 2, b.high.max(), "Initial Balance\n09:30–10:30 ET", color="#b0bec5", ha="center", va="top", fontsize=9)

    labels = [f"{m // 60:02d}:{m % 60:02d}" for m in b.ny_min]
    ticks = list(range(0, len(b), 12))
    ax.set_xticks(ticks, [labels[i] for i in ticks])
    ax.grid(color="#2a2e39", alpha=0.7, linewidth=0.6)
    ax.tick_params(colors="#b2b5be")
    for spine in ax.spines.values(): spine.set_color("#363a45")
    ax.yaxis.tick_right()
    ax.set_title(f"NQ Initial Balance baseline — {trade.session_date} {trade.side.upper()} — {trade.exit_kind.upper()}\n"
                 f"Net: {trade.net_points:+.2f} points after 1.0-point round-trip cost", color="white", loc="left", fontsize=13, fontweight="bold")
    leg = ax.legend(loc="upper left", facecolor="#1e222d", edgecolor="#363a45", labelcolor="white")
    for text in leg.get_texts(): text.set_color("white")
    fig.tight_layout()
    fig.savefig(out, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(ART / "nq_baseline_trades.csv")
    examples = {
        "nq_oos_initial_balance_loss.png": trades.query("split == 'OOS' and exit_kind == 'stop'").iloc[0],
        "nq_oos_initial_balance_win.png": trades.query("split == 'OOS' and exit_kind == 'target'").iloc[0],
    }
    for filename, trade in examples.items():
        render(trade, ART / filename)
        print(f"wrote {filename}: {trade.session_date} {trade.side} {trade.exit_kind}")


if __name__ == "__main__":
    main()
