"""Strategy 28 Phase 0 — ES/NQ sync audit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _panel import ART, WINDOWS, build_synced_panel, window_mask  # noqa: E402


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    panel = build_synced_panel()
    panel.to_parquet(ART / "synced_panel_1m.parquet", index=False)

    ny = panel["ny_min"].to_numpy(np.int16)
    rows = []
    for wname in WINDOWS:
        m = window_mask(ny, wname)
        sub = panel.loc[m]
        for split, g in sub.groupby("split"):
            rows.append(
                {
                    "window": wname,
                    "split": split,
                    "n_bars": int(len(g)),
                    "n_sessions": int(g["session_date"].nunique()),
                    "es_ret_finite": int(np.isfinite(g["es_ret_1m"]).sum()),
                    "nq_ret_finite": int(np.isfinite(g["nq_ret_1m"]).sum()),
                    "both_ret_finite": int(
                        (np.isfinite(g["es_ret_1m"]) & np.isfinite(g["nq_ret_1m"])).sum()
                    ),
                }
            )
    cov = pd.DataFrame(rows).sort_values(["window", "split"])
    cov.to_csv(ART / "phase0_coverage.csv", index=False)

    # contemporaneous contamination baseline (RTH Discovery)
    rth = panel.loc[window_mask(ny, "RTH") & (panel["split"] == "Discovery")]
    a = rth["es_ret_1m"].to_numpy(np.float64)
    b = rth["nq_ret_1m"].to_numpy(np.float64)
    ok = np.isfinite(a) & np.isfinite(b)
    spearman_same = float(pd.Series(a[ok]).corr(pd.Series(b[ok]), method="spearman")) if ok.sum() > 100 else float("nan")

    freeze = {
        "n_synced_bars": int(len(panel)),
        "n_sessions": int(panel["session_date"].nunique()),
        "ts_min": str(panel["ts"].min()),
        "ts_max": str(panel["ts"].max()),
        "windows": {k: list(v) for k, v in WINDOWS.items()},
        "discovery_rth_spearman_es_nq_same_bar": spearman_same,
        "splits": {
            s: int((panel["split"] == s).sum()) for s in ("Discovery", "Validation", "OOS", "OTHER")
        },
    }
    (ART / "phase0_freeze.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")

    md = [
        "# Strategy 28 — Phase 0 sync audit",
        "",
        f"- Synced bars: **{freeze['n_synced_bars']:,}**",
        f"- Sessions: **{freeze['n_sessions']:,}**",
        f"- Range: {freeze['ts_min']} → {freeze['ts_max']}",
        f"- Discovery RTH same-bar Spearman(ES,NQ) ret: **{spearman_same:.3f}**",
        "",
        "## Coverage by window × split",
        "",
        cov.to_markdown(index=False),
        "",
        "Freeze locked. Proceed to Phase 1.",
    ]
    (ART / "phase0_report.md").write_text("\n".join(md), encoding="utf-8")

    notes = [
        "# DATA_NOTES — Strategy 28",
        "",
        f"Synced panel: `{ART / 'synced_panel_1m.parquet'}`",
        f"n_bars={freeze['n_synced_bars']}, n_sessions={freeze['n_sessions']}",
        f"Same-bar ES↔NQ Spearman (Discovery RTH) = {spearman_same:.3f} (expected high).",
        "Lead/lag claims must beat this contamination baseline at lag ≥ 1.",
        "",
    ]
    (Path(__file__).resolve().parents[1] / "DATA_NOTES.md").write_text(
        "\n".join(notes), encoding="utf-8"
    )
    print(json.dumps(freeze, indent=2))
    print("Wrote", ART)


if __name__ == "__main__":
    main()
