"""Strategy 28 Phase 1 — minute lead/lag descriptives by TOD window."""
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

from _panel import ART, WINDOWS, forward_close_ret, window_mask  # noqa: E402

HORIZONS = (0, 1, 5, 15, 30)  # 0 = contemporaneous contamination
PAIRS = (
    ("es_ret_1m", "nq_close", "es_lead_nq"),
    ("nq_ret_1m", "es_close", "nq_lead_es"),
    ("es_ret_sum5", "nq_close", "es5_lead_nq"),
    ("nq_ret_sum5", "es_close", "nq5_lead_es"),
)


def spearman(a: np.ndarray, b: np.ndarray) -> tuple[float, int]:
    ok = np.isfinite(a) & np.isfinite(b)
    n = int(ok.sum())
    if n < 50:
        return float("nan"), n
    return float(pd.Series(a[ok]).corr(pd.Series(b[ok]), method="spearman")), n


def signed_hit(leader: np.ndarray, fwd: np.ndarray) -> tuple[float, int]:
    side = np.sign(leader)
    ok = np.isfinite(leader) & np.isfinite(fwd) & (side != 0)
    n = int(ok.sum())
    if n < 50:
        return float("nan"), n
    return float(np.mean((side[ok] * fwd[ok]) > 0)), n


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    panel_path = ART / "synced_panel_1m.parquet"
    if not panel_path.exists():
        raise FileNotFoundError("Run phase0 first")
    panel = pd.read_parquet(panel_path)
    session = panel["session_date"].to_numpy()
    ny = panel["ny_min"].to_numpy(np.int16)

    # precompute forward rets
    fwd_cache: dict[tuple[str, int], np.ndarray] = {}
    for book in ("nq", "es"):
        close = panel[f"{book}_close"].to_numpy(np.float64)
        for h in HORIZONS:
            if h == 0:
                # contemporaneous % ret already on book
                fwd_cache[(book, 0)] = panel[f"{book}_ret_1m"].to_numpy(np.float64)
            else:
                fwd_cache[(book, h)] = forward_close_ret(close, session, h)

    rows = []
    for wname in WINDOWS:
        m_w = window_mask(ny, wname)
        for split in ("Discovery", "Validation", "OOS"):
            m = m_w & (panel["split"].to_numpy() == split)
            if m.sum() < 50:
                continue
            for lead_col, follow_close_col, pair_id in PAIRS:
                follower = "nq" if follow_close_col.startswith("nq") else "es"
                leader = panel[lead_col].to_numpy(np.float64)
                for h in HORIZONS:
                    fwd = fwd_cache[(follower, h)]
                    sp, n_sp = spearman(leader[m], fwd[m])
                    hit, n_hit = signed_hit(leader[m], fwd[m])
                    rows.append(
                        {
                            "window": wname,
                            "split": split,
                            "pair": pair_id,
                            "horizon": h,
                            "spearman": sp,
                            "n_spearman": n_sp,
                            "signed_hit": hit,
                            "n_hit": n_hit,
                        }
                    )

    res = pd.DataFrame(rows)
    res.to_csv(ART / "phase1_leadlag_spearman.csv", index=False)

    # focus table: lag>=1, open windows vs MID
    focus = res[(res["horizon"] >= 1) & (res["window"].isin(["OPEN5", "OPEN15", "OPEN30", "MID"]))]
    pivot_bits = []
    for pair in ("es_lead_nq", "nq_lead_es"):
        sub = focus[focus["pair"] == pair]
        if sub.empty:
            continue
        pivot_bits.append(f"### {pair}\n")
        wide = sub.pivot_table(
            index=["window", "horizon"],
            columns="split",
            values="spearman",
            aggfunc="first",
        )
        pivot_bits.append(wide.to_markdown())
        pivot_bits.append("")

    # open vs mid lift at H=1 for es_lead_nq
    def _sp(window: str, split: str, pair: str, h: int) -> float:
        r = res[
            (res["window"] == window)
            & (res["split"] == split)
            & (res["pair"] == pair)
            & (res["horizon"] == h)
        ]
        if r.empty:
            return float("nan")
        return float(r.iloc[0]["spearman"])

    lifts = []
    for split in ("Discovery", "Validation", "OOS"):
        for w in ("OPEN5", "OPEN15", "OPEN30"):
            for pair in ("es_lead_nq", "nq_lead_es"):
                o = _sp(w, split, pair, 1)
                mid = _sp("MID", split, pair, 1)
                lifts.append(
                    {
                        "split": split,
                        "window": w,
                        "pair": pair,
                        "spearman_h1": o,
                        "mid_h1": mid,
                        "lift_vs_mid": o - mid if np.isfinite(o) and np.isfinite(mid) else float("nan"),
                    }
                )
    lift_df = pd.DataFrame(lifts)
    lift_df.to_csv(ART / "phase1_open_vs_mid_h1.csv", index=False)

    # contemporaneous vs lag1 ratio
    contam = []
    for split in ("Discovery", "Validation", "OOS"):
        for w in ("OPEN15", "MID", "RTH"):
            for pair in ("es_lead_nq", "nq_lead_es"):
                c0 = _sp(w, split, pair, 0)
                c1 = _sp(w, split, pair, 1)
                contam.append(
                    {
                        "split": split,
                        "window": w,
                        "pair": pair,
                        "spearman_h0": c0,
                        "spearman_h1": c1,
                        "h1_over_h0": c1 / c0 if np.isfinite(c0) and c0 != 0 else float("nan"),
                    }
                )
    contam_df = pd.DataFrame(contam)
    contam_df.to_csv(ART / "phase1_contam_h0_vs_h1.csv", index=False)

    summary = {
        "n_rows": int(len(res)),
        "note": "h=0 is same-bar contamination; trading claims need h>=1",
        "open15_es_lead_nq_h1": {
            s: _sp("OPEN15", s, "es_lead_nq", 1) for s in ("Discovery", "Validation", "OOS")
        },
        "mid_es_lead_nq_h1": {
            s: _sp("MID", s, "es_lead_nq", 1) for s in ("Discovery", "Validation", "OOS")
        },
    }
    (ART / "phase1_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = [
        "# Strategy 28 — Phase 1 lead/lag",
        "",
        "Spearman(leader_ret_t, follower_fwd_h). **h=0 = same bar** (contamination).",
        "",
        "## OPEN15 vs MID — es_lead_nq H=1",
        "",
        f"- Discovery OPEN15={summary['open15_es_lead_nq_h1']['Discovery']:.4f} vs MID={summary['mid_es_lead_nq_h1']['Discovery']:.4f}",
        f"- Validation OPEN15={summary['open15_es_lead_nq_h1']['Validation']:.4f} vs MID={summary['mid_es_lead_nq_h1']['Validation']:.4f}",
        f"- OOS OPEN15={summary['open15_es_lead_nq_h1']['OOS']:.4f} vs MID={summary['mid_es_lead_nq_h1']['OOS']:.4f}",
        "",
        "## Open vs MID lift (H=1)",
        "",
        lift_df.to_markdown(index=False),
        "",
        "## Contam h0 vs h1",
        "",
        contam_df.to_markdown(index=False),
        "",
        *pivot_bits,
    ]
    (ART / "phase1_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Wrote", ART / "phase1_report.md")


if __name__ == "__main__":
    main()
