"""Strategy 28 Phase 2 — frozen 1:1 scalp probe (fully vectorized)."""
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

from _panel import ART, window_mask  # noqa: E402

SIGNAL_WINDOWS = ("OPEN5", "OPEN15", "OPEN30", "MID")
TIME_STOPS = (15, 30)

SIGNALS = (
    ("es_lead_nq", "es_ret_1m", "nq", (20.0, 25.0, 30.0), 1.0),
    ("nq_lead_es", "nq_ret_1m", "es", (8.0, 10.0, 12.0), 0.5),
    ("es5_lead_nq", "es_ret_sum5", "nq", (20.0, 25.0, 30.0), 1.0),
    ("nq5_lead_es", "nq_ret_sum5", "es", (8.0, 10.0, 12.0), 0.5),
)


def path_pnl_batch(
    sides: np.ndarray,
    entries: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    target: float,
    cost: float,
) -> tuple[np.ndarray, np.ndarray]:
    n, h = highs.shape
    pnl = np.full(n, np.nan, dtype=np.float64)
    kind = np.full(n, 3, dtype=np.int8)
    valid = np.isfinite(entries) & (entries > 0) & (sides != 0) & np.isfinite(sides)
    if not np.any(valid):
        return pnl, kind

    stop_lvl = entries - sides * target
    tgt_lvl = entries + sides * target
    decided = np.zeros(n, dtype=bool)

    for t in range(h):
        hi = highs[:, t]
        lo = lows[:, t]
        path_ok = valid & ~decided & np.isfinite(hi) & np.isfinite(lo)
        if not np.any(path_ok):
            continue
        long = path_ok & (sides > 0)
        short = path_ok & (sides < 0)
        hit_stop = np.zeros(n, dtype=bool)
        hit_tgt = np.zeros(n, dtype=bool)
        hit_stop[long] = lo[long] <= stop_lvl[long]
        hit_tgt[long] = hi[long] >= tgt_lvl[long]
        hit_stop[short] = hi[short] >= stop_lvl[short]
        hit_tgt[short] = lo[short] <= tgt_lvl[short]

        both = path_ok & hit_stop & hit_tgt
        only_stop = path_ok & hit_stop & ~hit_tgt
        only_tgt = path_ok & hit_tgt & ~hit_stop

        pnl[both | only_stop] = -target - cost
        kind[both | only_stop] = 1
        decided[both | only_stop] = True

        pnl[only_tgt] = target - cost
        kind[only_tgt] = 0
        decided[only_tgt] = True

    still = valid & ~decided
    if np.any(still):
        last = closes[:, -1]
        ok_last = still & np.isfinite(last)
        pnl[ok_last] = sides[ok_last] * (last[ok_last] - entries[ok_last]) - cost
        kind[ok_last] = 2
    return pnl, kind


def summarize(pnls: np.ndarray, kinds: np.ndarray, meta: dict) -> dict:
    ok = np.isfinite(pnls)
    x = pnls[ok]
    k = kinds[ok]
    if len(x) == 0:
        return {
            **meta,
            "n": 0,
            "win": np.nan,
            "E_net": np.nan,
            "target_hit": np.nan,
            "stop_hit": np.nan,
            "time_exit": np.nan,
        }
    return {
        **meta,
        "n": int(len(x)),
        "win": float(np.mean(x > 0)),
        "E_net": float(np.mean(x)),
        "median_net": float(np.median(x)),
        "target_hit": float(np.mean(k == 0)),
        "stop_hit": float(np.mean(k == 1)),
        "time_exit": float(np.mean(k == 2)),
    }


def collect_trades_fast(
    ny: np.ndarray,
    sess_codes: np.ndarray,
    leader: np.ndarray,
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    window: str,
    h: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """Vectorized eligibility; gather path with advanced indexing."""
    side = np.sign(leader)
    in_win = window_mask(ny, window)
    i = np.flatnonzero(in_win & np.isfinite(leader) & (side != 0))
    if len(i) == 0:
        return None
    j = i + 1
    k = j + h - 1
    n = len(ny)
    ok = k < n
    i, j, k = i[ok], j[ok], k[ok]
    ok = (sess_codes[j] == sess_codes[i]) & (sess_codes[k] == sess_codes[i])
    i, j, k = i[ok], j[ok], k[ok]
    ok = (ny[k].astype(np.int32) - ny[j].astype(np.int32)) == (h - 1)
    i, j, k = i[ok], j[ok], k[ok]
    if len(i) == 0:
        return None

    # path indices shape (n_trades, h)
    offs = np.arange(h, dtype=np.int32)
    idx = j[:, None] + offs[None, :]
    return (
        side[i].astype(np.float64),
        opens[j].astype(np.float64),
        highs[idx],
        lows[idx],
        closes[idx],
    )


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    panel_path = ART / "synced_panel_1m.parquet"
    if not panel_path.exists():
        raise FileNotFoundError("Run phase0 first")
    panel = pd.read_parquet(panel_path)

    # Encode session_date once
    sess_cat = pd.Categorical(panel["session_date"])
    panel = panel.assign(_sess=sess_cat.codes.astype(np.int32))

    rows = []
    cache: dict[tuple, object] = {}

    for split in ("Discovery", "Validation", "OOS"):
        sub = panel[panel["split"] == split].sort_values(["session_date", "ny_min"]).reset_index(drop=True)
        if sub.empty:
            continue
        ny = sub["ny_min"].to_numpy(np.int16)
        sess_codes = sub["_sess"].to_numpy(np.int32)
        print(f"split={split} bars={len(sub)}", flush=True)

        for signal_id, leader_col, follower, targets, cost in SIGNALS:
            leader = sub[leader_col].to_numpy(np.float64)
            opens = sub[f"{follower}_open"].to_numpy(np.float64)
            highs = sub[f"{follower}_high"].to_numpy(np.float64)
            lows = sub[f"{follower}_low"].to_numpy(np.float64)
            closes = sub[f"{follower}_close"].to_numpy(np.float64)

            for window in SIGNAL_WINDOWS:
                for h in TIME_STOPS:
                    key = (split, signal_id, window, h)
                    packed = collect_trades_fast(
                        ny, sess_codes, leader, opens, highs, lows, closes, window, h
                    )
                    cache[key] = packed
                    for target in targets:
                        meta = {
                            "signal": signal_id,
                            "window": window,
                            "follower": follower,
                            "target": target,
                            "H": h,
                            "split": split,
                        }
                        if packed is None:
                            rows.append(summarize(np.array([]), np.array([]), meta))
                        else:
                            sides, entries, hi, lo, cl = packed
                            pnl, kind = path_pnl_batch(sides, entries, hi, lo, cl, target, cost)
                            rows.append(summarize(pnl, kind, meta))
                        r = rows[-1]
                        print(
                            f"done {signal_id} {window} tgt={target} H={h} {split} n={r['n']} E={r['E_net']}",
                            flush=True,
                        )

    res = pd.DataFrame(rows)
    res.to_csv(ART / "phase2_scalp_grid.csv", index=False)

    piv = res.pivot_table(
        index=["signal", "window", "follower", "target", "H"],
        columns="split",
        values="E_net",
        aggfunc="first",
    )
    counts = res.pivot_table(
        index=["signal", "window", "follower", "target", "H"],
        columns="split",
        values="n",
        aggfunc="first",
    )
    survivors = []
    for idx in piv.index:
        e_d = piv.loc[idx].get("Discovery", np.nan)
        e_v = piv.loc[idx].get("Validation", np.nan)
        e_o = piv.loc[idx].get("OOS", np.nan)
        n_v = counts.loc[idx].get("Validation", 0) or 0
        n_o = counts.loc[idx].get("OOS", 0) or 0
        if np.isfinite(e_v) and np.isfinite(e_o) and e_v > 0 and e_o > 0 and n_v >= 30 and n_o >= 30:
            survivors.append(
                {
                    "signal": idx[0],
                    "window": idx[1],
                    "follower": idx[2],
                    "target": float(idx[3]),
                    "H": int(idx[4]),
                    "E_Discovery": float(e_d) if np.isfinite(e_d) else None,
                    "E_Validation": float(e_v),
                    "E_OOS": float(e_o),
                    "n_Validation": int(n_v),
                    "n_OOS": int(n_o),
                }
            )
    surv_df = pd.DataFrame(survivors)
    surv_df.to_csv(ART / "phase2_survivors.csv", index=False)

    open_res = res[res["window"].isin(["OPEN5", "OPEN15", "OPEN30"]) & (res["split"] == "OOS")]
    best = open_res.sort_values("E_net", ascending=False).head(20)

    freq = res[
        (res["signal"] == "es_lead_nq")
        & (res["window"] == "OPEN15")
        & (res["target"] == 25.0)
        & (res["H"] == 15)
    ][["split", "n", "E_net", "win", "target_hit", "stop_hit", "time_exit"]]

    if len(surv_df) == 0:
        klass, label = "C", "NO_SCALP_EDGE"
    else:
        strong = surv_df[surv_df["E_Discovery"].fillna(-1) > 0]
        klass, label = ("B", "WEAK_CANDIDATE_REVIEW") if len(strong) else ("B", "VAL_OOS_ONLY_SOFT")

    verdict = {
        "class": klass,
        "label": label,
        "n_grid_rows": int(len(res)),
        "n_survivors_val_oos_pos": int(len(surv_df)),
        "survivors": survivors,
        "open15_es_lead_nq_tgt25_H15": freq.to_dict(orient="records"),
        "best_oos_open_preview": best[
            ["signal", "window", "target", "H", "n", "win", "E_net", "target_hit", "stop_hit", "time_exit"]
        ].to_dict(orient="records"),
    }
    (ART / "phase2_verdict.json").write_text(json.dumps(verdict, indent=2, default=float), encoding="utf-8")

    md = [
        "# Strategy 28 — Phase 2 scalp probe",
        "",
        f"**Survivors (Val+OOS E_net>0, n≥30): {len(surv_df)}**",
        f"Verdict class: `{klass}` — {label}",
        "",
        "## Headline cell: es_lead_nq OPEN15 target=25 H=15",
        "",
        freq.to_markdown(index=False),
        "",
        "## Survivors",
        "",
        surv_df.to_markdown(index=False) if len(surv_df) else "_none_",
        "",
        "## Best OOS open cells (descriptive)",
        "",
        best.to_markdown(index=False),
        "",
        "Hostile path rule: same-bar stop before target. Costs deducted.",
    ]
    (ART / "phase2_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(verdict, indent=2, default=float))


if __name__ == "__main__":
    main()
